Сессия 7. Desktop-клиент: каркас Avalonia · 0–70 мин

Стек: **C# / Avalonia 11**, паттерн MVVM. Раздел задания требует **нативный**
интерфейс: Electron, Tauri и PWA не подходят (см.
[21-Tauri-или-PWA-вместо-Avalonia](21-Tauri-или-PWA-вместо-Avalonia) —
этот вариант допустим только на финальном этапе).

# 1. Создание проекта (0–15 мин)

Сервис и шаблоны Avalonia для VS Code ставятся расширениями
(`Avalonia for VSCode`, `Avalonia Templates` — они есть в инфраструктурном
листе чемпионата). Командный вариант:

```bash
cd src/desktop
dotnet new install Avalonia.Templates
dotnet new avalonia.mvvm -n TaskPlanner.Desktop -o TaskPlanner.Desktop -f net9.0
cd TaskPlanner.Desktop
dotnet add reference ../../api/TaskPlanner.Core
dotnet add package Avalonia
dotnet add package Avalonia.Desktop
dotnet add package Avalonia.Themes.Fluent
dotnet add package Avalonia.Fonts.Inter
dotnet add package CommunityToolkit.Mvvm
dotnet add package System.Net.Http.Json
```

Структура, которая получится (её и правим):

```
TaskPlanner.Desktop/
├── Program.cs
├── App.axaml / App.axaml.cs
├── ViewLocator.cs
├── Assets/
├── Models/
├── Services/
├── ViewModels/
└── Views/
    ├── MainWindow.axaml
    ├── MainWindow.axaml.cs
    ├── LoginView.axaml
    └── TasksView.axaml
```

Добавьте проект в solution:

```bash
cd ../../..   # корень src
dotnet sln TaskPlanner.sln add desktop/TaskPlanner.Desktop/TaskPlanner.Desktop.csproj
```

Проверка — проект должен запуститься:

```bash
cd desktop/TaskPlanner.Desktop
dotnet run
```

# 2. Конфигурация и HTTP-клиент (15–35 мин)

`TaskPlanner.Desktop.csproj` — в `<PropertyGroup>`:

```xml
    <AvaloniaUseCompiledBindingsByDefault>true</AvaloniaUseCompiledBindingsByDefault>
```

`Services/ApiClient.cs`:

```csharp
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using TaskPlanner.Core.Common;
using TaskPlanner.Core.Enums;

namespace TaskPlanner.Desktop.Services;

/// <summary>
/// Обёртка ответа API. Совпадает с контрактом в api/openapi.yaml.
/// </summary>
public class ApiResponse<T>
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("data")]
    public T? Data { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = string.Empty;

    [JsonPropertyName("error_code")]
    public string? ErrorCode { get; set; }
}

public class UserDto
{
    [JsonPropertyName("id")]
    public long Id { get; set; }

    [JsonPropertyName("email")]
    public string Email { get; set; } = string.Empty;

    [JsonPropertyName("fullName")]
    public string FullName { get; set; } = string.Empty;
}

public class LoginResponse
{
    [JsonPropertyName("token")]
    public string Token { get; set; } = string.Empty;

    [JsonPropertyName("tokenType")]
    public string TokenType { get; set; } = "Bearer";

    [JsonPropertyName("expiresIn")]
    public int ExpiresIn { get; set; }

    [JsonPropertyName("user")]
    public UserDto User { get; set; } = new();
}

public class TaskDto
{
    [JsonPropertyName("id")]
    public long Id { get; set; }

    [JsonPropertyName("userId")]
    public long UserId { get; set; }

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("status")]
    public TaskStatus Status { get; set; }

    [JsonPropertyName("priority")]
    public TaskPriority Priority { get; set; }

    [JsonPropertyName("dueDate")]
    public string? DueDate { get; set; }

    [JsonPropertyName("completedAt")]
    public DateTimeOffset? CompletedAt { get; set; }

    [JsonPropertyName("createdAt")]
    public DateTimeOffset CreatedAt { get; set; }

    [JsonPropertyName("updatedAt")]
    public DateTimeOffset UpdatedAt { get; set; }
}

public class TaskSummaryDto
{
    [JsonPropertyName("total")]
    public long Total { get; set; }

    [JsonPropertyName("done")]
    public long Done { get; set; }

    [JsonPropertyName("notDone")]
    public long NotDone { get; set; }

    [JsonPropertyName("overdue")]
    public long Overdue { get; set; }

    [JsonPropertyName("byPriority")]
    public Dictionary<string, long> ByPriority { get; set; } = new();
}

public class PagedResult<T>
{
    [JsonPropertyName("items")]
    public List<T> Items { get; set; } = new();

    [JsonPropertyName("total")]
    public long Total { get; set; }

    [JsonPropertyName("page")]
    public int Page { get; set; }

    [JsonPropertyName("pageSize")]
    public int PageSize { get; set; }
}

/// <summary>
/// Тонкий клиент поверх общего API. Держит токен, разбирает обёртку
/// и превращает ошибки в ApiException.
/// </summary>
public class ApiClient
{
    private const string BaseUrl = "http://localhost:5000";

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true,
        Converters = { new TaskStatusConverter(), new TaskPriorityConverter() },
    };

    private readonly HttpClient _http;

    public string? Token { get; private set; }

    public ApiClient()
    {
        _http = new HttpClient
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(15),
        };
    }

    public void SetToken(string? token)
    {
        Token = token;

        _http.DefaultRequestHeaders.Authorization = token is null
            ? null
            : new AuthenticationHeaderValue("Bearer", token);
    }

    private async Task<T> SendAsync<T>(
        HttpMethod method,
        string path,
        object? body,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(method, path);

        if (body is not null)
        {
            request.Content = JsonContent.Create(body, options: JsonOptions);
        }

        using var response = await _http.SendAsync(request, cancellationToken);

        if (response.StatusCode == HttpStatusCode.NoContent)
        {
            return default!;
        }

        var payload = await response.Content.ReadFromJsonAsync<ApiResponse<T>>(JsonOptions, cancellationToken);

        if (payload is null)
        {
            throw new ApiException(
                HttpStatusCode.InternalServerError,
                "Сервер вернул пустой ответ");
        }

        if (!response.IsSuccessStatusCode || !payload.Success || payload.Data is null)
        {
            throw new ApiException(
                response.StatusCode,
                payload.Message ?? $"Ошибка {(int)response.StatusCode}",
                payload.ErrorCode ?? "UNKNOWN");
        }

        return payload.Data;
    }

    public Task<LoginResponse> LoginAsync(string email, string password, CancellationToken ct = default)
        => SendAsync<LoginResponse>(
            HttpMethod.Post, "/api/auth/login", new { email, password }, ct);

    public Task<UserDto> RegisterAsync(
        string email, string password, string fullName, CancellationToken ct = default)
        => SendAsync<UserDto>(
            HttpMethod.Post,
            "/api/auth/register",
            new { email, password, fullName },
            ct);

    public Task<PagedResult<TaskDto>> GetTasksAsync(
        int page = 1, int pageSize = 20, string? status = null, CancellationToken ct = default)
        => SendAsync<PagedResult<TaskDto>>(
            HttpMethod.Get,
            $"/api/tasks?page={page}&pageSize={pageSize}" +
            (string.IsNullOrEmpty(status) ? "" : $"&status={status}"),
            null,
            ct);

    public Task<TaskDto> CreateTaskAsync(object task, CancellationToken ct = default)
        => SendAsync<TaskDto>(HttpMethod.Post, "/api/tasks", task, ct);

    public Task<TaskDto> UpdateTaskAsync(long id, object task, CancellationToken ct = default)
        => SendAsync<TaskDto>(HttpMethod.Put, $"/api/tasks/{id}", task, ct);

    public Task<TaskDto> ToggleCompletedAsync(long id, CancellationToken ct = default)
        => SendAsync<TaskDto>(HttpMethod.Patch, $"/api/tasks/{id}/complete", null, ct);

    public Task DeleteTaskAsync(long id, CancellationToken ct = default)
        => SendAsync<object>(HttpMethod.Delete, $"/api/tasks/{id}", null, ct);

    public Task<TaskSummaryDto> GetSummaryAsync(CancellationToken ct = default)
        => SendAsync<TaskSummaryDto>(HttpMethod.Get, "/api/tasks/summary", null, ct);
}
```

`Services/ApiException.cs`:

```csharp
using System.Net;

namespace TaskPlanner.Desktop.Services;

public class ApiException(HttpStatusCode statusCode, string message, string errorCode = "UNKNOWN")
    : Exception(message)
{
    public HttpStatusCode StatusCode { get; } = statusCode;

    public string ErrorCode { get; } = errorCode;
}
```

# 3. Хранение токена (35–50 мин)

`Services/TokenStorage.cs`:

```csharp
using System.Text.Json;

namespace TaskPlanner.Desktop.Services;

/// <summary>
/// Токен лежит в файле рядом с приложением, чтобы переживал перезапуск.
/// В рабочей версии файл нужно шифровать или хранить в системном
/// хранилище секретов; на отборе достаточно файла в каталоге данных.
/// </summary>
public class TokenStorage
{
    private readonly string _path;

    public TokenStorage()
    {
        var directory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "TaskPlanner");

        Directory.CreateDirectory(directory);
        _path = Path.Combine(directory, "session.json");
    }

    private sealed record Session(string Token, string FullName, string Email);

    public void Save(string token, string fullName, string email)
    {
        var session = new Session(token, fullName, email);

        File.WriteAllText(_path, JsonSerializer.Serialize(session));
    }

    public Session? Load()
    {
        if (!File.Exists(_path))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<Session>(File.ReadAllText(_path));
        }
        catch (JsonException)
        {
            // Файл повреждён — считаем сессию недействительной
            File.Delete(_path);
            return null;
        }
    }

    public void Clear()
    {
        if (File.Exists(_path))
        {
            File.Delete(_path);
        }
    }
}
```

> **Замечание:** `session.json` не попадает в репозиторий: он создаётся в
> `%APPDATA%` на Windows и в `~/.local/share/TaskPlanner` на РедОС. На РедОС
> `Environment.SpecialFolder.ApplicationData` возвращает путь внутри
> `~/.local/share`, поэтому каталог создаётся автоматически.

# 4. Регистрация в DI (50–60 мин)

`Program.cs`:

```csharp
using Avalonia;
using TaskPlanner.Desktop.Services;
using TaskPlanner.Desktop.ViewModels;
using TaskPlanner.Desktop.Views;

namespace TaskPlanner.Desktop;

internal static class Program
{
    [STAThread]
    public static void Main(string[] args) => BuildAvaloniaApp()
        .StartWithClassicDesktopLifetime(args);

    public static AppBuilder BuildAvaloniaApp()
        => AppBuilder
            .Configure<App>()
            .UsePlatformDetect()
            .WithInterFont()
            .LogToTrace();
}
```

`App.axaml.cs`:

```csharp
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using TaskPlanner.Desktop.Services;
using TaskPlanner.Desktop.ViewModels;
using TaskPlanner.Desktop.Views;

namespace TaskPlanner.Desktop;

public partial class App : Application
{
    public override void Initialize() => AvaloniaXamlLoader.Load(this);

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            // Простые сервисы — один на всё приложение
            var apiClient = new ApiClient();
            var tokenStorage = new TokenStorage();

            var session = tokenStorage.Load();

            if (session is not null)
            {
                apiClient.SetToken(session.Token);
            }

            var shell = new MainWindow
            {
                DataContext = new MainWindowViewModel(apiClient, tokenStorage, session),
            };

            desktop.MainWindow = shell;
        }

        base.OnFrameworkInitializationCompleted();
    }
}
```

`App.axaml` — тема и общий словарь:

```xml
<Application xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             x:Class="TaskPlanner.Desktop.App"
             RequestedThemeVariant="Light">

  <Application.Styles>
    <FluentTheme />
  </Application.Styles>

</Application>
```

# 5. Главное окно и навигация (60–70 мин)

`Views/MainWindow.axaml`:

```xml
<Window xmlns="https://github.com/avaloniaui"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:vm="using:TaskPlanner.Desktop.ViewModels"
        x:Class="TaskPlanner.Desktop.Views.MainWindow"
        xmlns:local="using:TaskPlanner.Desktop.Views"
        x:DataType="vm:MainWindowViewModel"
        Title="Планировщик задач"
        Width="1000" Height="680"
        MinWidth="900" MinHeight="600">

  <Design.DataContext>
    <vm:MainWindowViewModel />
  </Design.DataContext>

  <Grid>
    <local:LoginView DataContext="{Binding Login}" />

    <Grid IsVisible="{Binding !IsAuthenticated}">
      <local:TasksView DataContext="{Binding Tasks}" />
    </Grid>
  </Grid>
</Window>
```

`Views/MainWindow.axaml.cs`:

```csharp
using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace TaskPlanner.Desktop.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private void InitializeComponent() => AvaloniaXamlLoader.Load(this);
}
```

> **Замечание:** `{Binding !IsAuthenticated}` — оператор отрицания в
> compiled bindings Avalonia. При `x:DataType` и
> `AvaloniaUseCompiledBindingsByDefault` привязки проверяются на этапе сборки
> — опечатка в имени свойства станет ошибкой компиляции, а не «пустым
> экраном в рантайме».

`ViewModels/MainWindowViewModel.cs`:

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using TaskPlanner.Desktop.Services;

namespace TaskPlanner.Desktop.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private readonly ApiClient _apiClient;
    private readonly TokenStorage _tokenStorage;

    [ObservableProperty]
    private bool _isAuthenticated;

    public LoginViewModel Login { get; }

    public TasksViewModel Tasks { get; }

    public MainWindowViewModel(
        ApiClient apiClient,
        TokenStorage tokenStorage,
        object? session)
    {
        _apiClient = apiClient;
        _tokenStorage = tokenStorage;

        Login = new LoginViewModel(apiClient, tokenStorage);
        Tasks = new TasksViewModel(apiClient);

        IsAuthenticated = session is not null;

        Login.PropertyChanged += (_, e) =>
        {
            if (e.PropertyName == nameof(LoginViewModel.IsAuthenticated))
            {
                IsAuthenticated = Login.IsAuthenticated;
            }
        };
    }
}
```

`ViewModels/ViewModelBase.cs`:

```csharp
using CommunityToolkit.Mvvm.ComponentModel;

namespace TaskPlanner.Desktop.ViewModels;

public abstract partial class ViewModelBase : ObservableObject
{
}
```

# Проверка

```bash
cd src/desktop/TaskPlanner.Desktop
dotnet build
dotnet run
```

- Окно «Планировщик задач» 1000×680, в нём форма входа.
- Заголовок окна и минимальный размер 900×600 заданы в XAML.
- Приложение запускается без ошибок в консоли.

# Коммит

```bash
git add src/desktop
git commit -m "Desktop-клиент: проект Avalonia, API-клиент, хранение токена, навигация"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Шаблон `avalonia.mvvm` не найден | `dotnet new install Avalonia.Templates`, затем `dotnet new list \| grep avalonia` |
| Привязки не работают, элементы пустые | не включён `x:DataType` или `AvaloniaUseCompiledBindingsByDefault` |
| `CommunityToolkit.Mvvm` не генерирует `Login` | используйте `[ObservableProperty]` и частичные классы: `public partial class … : ObservableObject` |
| `404` на все запросы | в путях нужен префикс `/api`: `"/api/tasks"`, а не `"/tasks"` |
| `No such host` / таймаут | API не запущен на порту 5000 |
| Не собирается на РедОС | проверьте, что нет Windows-специфичных пакетов; Avalonia кроссплатформенна |

---

Дальше: [20-Desktop-Avalonia-экраны](20-Desktop-Avalonia-экраны)
