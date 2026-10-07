Сессия 7. Desktop-клиент: каркас Avalonia · 0–70 мин

Стек: **C# / Avalonia 11**, паттерн MVVM. Раздел задания требует **нативный**
интерфейс: Electron, Tauri и PWA не подходят (см.
[21-Tauri-или-PWA-вместо-Avalonia](21-Tauri-или-PWA-вместо-Avalonia) —
этот вариант допустим только как дополнительный, на финальном этапе).

# Что делаем на этой странице

Собираем нативный проект: пакеты, точку входа, окно и модель представления,
которая ходит в уже готовый API. Ничего нового на сервере здесь не появляется —
десктопный клиент только читает и меняет задачи теми же запросами, что и веб.

В эталоне API поднят как сервис `api` в docker-compose, поэтому адрес клиента —
`http://api:8080`. Если API запущен локально, меняется одна константа:
`http://localhost:5000`.

# Шаг 1. Создаём проект

```bash
cd src/desktop
dotnet new install Avalonia.Templates
dotnet new avalonia.mvvm -n TaskPlanner.Desktop -o TaskPlanner.Desktop -f net9.0
```

Шаблон создаст лишнее — `ViewLocator.cs`, `Models/`, `Services/`, `Assets/` и
лишние окна. В эталоне HTTP-клиент живёт в модели представления, а окно одно,
поэтому лишнее удаляем:

```bash
cd TaskPlanner.Desktop
rm -rf Models Services Assets ViewLocator.cs
rm -f Views/LoginView.axaml Views/LoginView.axaml.cs Views/TasksView.axaml Views/TasksView.axaml.cs
```

Добавьте проект в solution:

```bash
cd ../../..
dotnet sln TaskPlanner.sln add desktop/TaskPlanner.Desktop/TaskPlanner.Desktop.csproj
```

![[images/desk19-s01-folder.png]]
*Explorer показывает ровно то, что осталось: два каталога, четыре файла и Dockerfile*

# Шаг 2. Пакеты и параметры сборки

`TaskPlanner.Desktop.csproj`:

```xml
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <AvaloniaUseCompiledBindingsByDefault>true</AvaloniaUseCompiledBindingsByDefault>
    <ApplicationManifest>app.manifest</ApplicationManifest>
  </PropertyGroup>
```

```xml
  <ItemGroup>
    <PackageReference Include="Avalonia" Version="11.2.3" />
    <PackageReference Include="Avalonia.Desktop" Version="11.2.3" />
    <PackageReference Include="Avalonia.Themes.Fluent" Version="11.2.3" />
    <PackageReference Include="Avalonia.Fonts.Inter" Version="11.2.3" />
  </ItemGroup>
```

Четыре пакета: движок, настольная платформа, тема Fluent и шрифт Inter.
Отдельная строка `AvaloniaUseCompiledBindingsByDefault` включает проверку
привязок на этапе сборки: опечатка в имени свойства станет ошибкой компиляции,
а не пустым элементом в рантайме.

![[images/desk19-s02-csproj.png]]
*Файл проекта: свойства сборки и четыре ссылки на пакеты Avalonia*

# Шаг 3. Точка входа

`Program.cs`:

```csharp
internal static class Program
{
    [STAThread]
    public static void Main(string[] args) => BuildAvaloniaApp()
        .StartWithClassicDesktopLifetime(args);

    public static AppBuilder BuildAvaloniaApp() => AppBuilder
        .Configure<App>()
        .UsePlatformDetect()
        .WithInterFont()
        .LogToTrace();
}
```

`UsePlatformDetect()` выбирает X11 на РедОС и Win32 на Windows, поэтому
код приложения одинаковый на обеих системах.

![[images/desk19-s03-program.png]]
*Program.cs собирает конфигурацию приложения и передаёт аргументы в Avalonia*

# Шаг 4. Приложение и главное окно

`App.axaml` — тема:

```xml
<Application xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             x:Class="TaskPlanner.Desktop.App">
  <Application.Styles>
    <FluentTheme />
  </Application.Styles>
</Application>
```

`App.axaml.cs` — единственное место, где создаётся окно:

```csharp
public override void OnFrameworkInitializationCompleted()
{
    if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        desktop.MainWindow = new Views.MainWindow();

    base.OnFrameworkInitializationCompleted();
}
```

Сервисы не нужны: у клиента одна модель представления, создать её проще, чем
прокидывать через контейнер. Модель получает `DataContext` в code-behind
окна — так видно, где живёт состояние.

![[images/desk19-s04-app.png]]
*App.axaml.cs назначает главное окно при старте приложения*

# Шаг 5. Модель представления

`ViewModels/MainWindowViewModel.cs`. Сначала — строка задачи и перевод
статусов и приоритетов на русский:

```csharp
public class TaskRow
{
    public long Id { get; init; }
    public string Title { get; init; } = "";
    public string? Description { get; init; }
    public string Status { get; init; } = "new";
    public string Priority { get; init; } = "medium";
    public string? DueDate { get; init; }

    public string StatusRu => Status switch
    {
        "in_progress" => "В работе",
        "done" => "Выполнена",
        "cancelled" => "Отменена",
        _ => "Новая",
    };

    public bool Done => Status == "done";
}
```

Дальше — сам клиент. Один `HttpClient` на модель, токен кладётся в заголовок
один раз при входе:

```csharp
private const string BaseUrl = "http://api:8080";

private readonly HttpClient _http = new() { BaseAddress = new Uri(BaseUrl) };
private string? _token;
```

```csharp
public async Task SignInAsync()
{
    Error = "";
    var payload = await _http.PostAsJsonAsync(
        "/api/auth/login",
        new { email = Email, password = Password });

    var json = await payload.Content.ReadFromJsonAsync<JsonElement>();
    if (!payload.IsSuccessStatusCode)
    {
        Error = json.GetProperty("message").GetString() ?? "Не удалось войти";
        return;
    }

    var data = json.GetProperty("data");
    _token = data.GetProperty("token").GetString();
    _http.DefaultRequestHeaders.Authorization =
        new AuthenticationHeaderValue("Bearer", _token);
    IsLoggedIn = true;
    await RefreshAsync();
}
```

Ошибку входа показываем текстом с сервера, а не своей строкой: сообщение
приходит тем же контрактом `message`, что и в веб-клиенте, и студент видит
ровно то, что вернул бэкенд.

Список задач и сводка приходят двумя запросами — так же, как в веб-клиенте:

```csharp
var query = new List<string> { "sort=dueDate", "order=asc", "pageSize=50" };
if (!string.IsNullOrWhiteSpace(StatusFilter))
    query.Add($"status={StatusFilter}");

var json = await _http.GetFromJsonAsync<JsonElement>($"/api/tasks?{string.Join('&', query)}");
Tasks.Clear();
foreach (var item in json.GetProperty("data").GetProperty("items").EnumerateArray())
{
    Tasks.Add(new TaskRow { Id = item.GetProperty("id").GetInt64(), /* остальные поля */ });
}
```

Каждую строку JSON собираем в `TaskRow` вручную: у полей `description`
и `dueDate` значение может быть `null`, поэтому читаем их через
`TryGetProperty`. Сводку берём вторым запросом, чтобы не пересчитывать
счётчики на клиенте:

```csharp
var summary = await _http.GetFromJsonAsync<JsonElement>("/api/tasks/summary");
Total = summary.GetProperty("data").GetProperty("total").GetInt32();
Done = summary.GetProperty("data").GetProperty("done").GetInt32();
Overdue = summary.GetProperty("data").GetProperty("overdue").GetInt32();
```

Свойства объявлены через `INotifyPropertyChanged` — привязки Avalonia
подписаны на него сами:

```csharp
public event PropertyChangedEventHandler? PropertyChanged;

private void Set<T>(ref T field, T value, [CallerMemberName] string? name = null)
{
    if (EqualityComparer<T>.Default.Equals(field, value)) return;
    field = value;
    PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
```

![[images/desk19-s05-viewmodel.png]]
*Модель представления: строка задачи, переводы статусов, HTTP-клиент и вход*

# Шаг 6. Разметка окна и обработчики

`Views/MainWindow.axaml` объявляет тип данных — с ним привязки проверяются
при сборке:

```xml
<Window xmlns="https://github.com/avaloniaui"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:vm="using:TaskPlanner.Desktop.ViewModels"
        x:Class="TaskPlanner.Desktop.Views.MainWindow"
        x:DataType="vm:MainWindowViewModel"
        Title="Планировщик личных задач — десктоп"
        Width="1180" Height="760" MinWidth="960" MinHeight="620">
```

Внутри три блока с комментариями в разметке: шапка с именем пользователя,
форма входа и список с панелью сводки. Каждая кнопка вызывает обработчик
code-behind:

```xml
<Button Content="Войти" Classes="primary" Click="OnSignIn" />
<Button Content="Все" Classes="chip" Click="OnFilterAll" />
<Button Content="Удалить" Classes="ghost" Tag="{Binding}" Click="OnDelete" />
```

`Views/MainWindow.axaml.cs` переводит события в вызовы модели:

```csharp
private async void OnSignIn(object? sender, RoutedEventArgs e) => await _vm.SignInAsync();

private async void OnFilterDone(object? sender, RoutedEventArgs e) => await FilterAsync("done");

private async Task FilterAsync(string status)
{
    _vm.StatusFilter = status;
    await _vm.RefreshAsync();
}

private async void OnToggleDone(object? sender, RoutedEventArgs e)
{
    if (sender is CheckBox { Tag: TaskRow task }) await _vm.ToggleAsync(task);
}
```

Тег на чекбоксе и на кнопке удаления — та самая строка задачи, о которой
известно событие. Без него обработчик не поймёт, какую строку менять.

![[images/desk19-s06-mainwindow.png]]
*MainWindow.axaml: x:DataType объявлен у окна, кнопки ссылаются на обработчики code-behind*

# Шаг 7. Собираем

```bash
cd src/desktop/TaskPlanner.Desktop
dotnet build
```

![[images/desk19-s07-build.png]]
*Сборка проходит без ошибок: 0 Warning(s), 0 Error(s)*

Ошибок быть не должно, потому что compiled bindings уже проверили имена
свойств. Если сборка прошла — половина страницы закрыта: осталось открыть
окно и нарисовать экраны, это [20-Desktop-Avalonia-экраны](20-Desktop-Avalonia-экраны).

# Коммит

```bash
git add src/desktop
git commit -m "Desktop-клиент: проект Avalonia, модель представления, окно"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Шаблон `avalonia.mvvm` не найден | `dotnet new install Avalonia.Templates`, затем `dotnet new list \| grep avalonia` |
| Привязки пустые, а ошибок нет | не объявлен `x:DataType` или выключен `AvaloniaUseCompiledBindingsByDefault` |
| `XOpenDisplay failed` на РедОС | не установлены X11-библиотеки: `libx11-6`, `libice6`, `libsm6`, `libxext6`, `libxrandr2`, `libxi6`, `libxcursor1`, `libxrender1`, `libgl1` |
| Шрифты в окне квадратами | нужен пакет `Avalonia.Fonts.Inter` и `WithInterFont()` в `Program.cs` |
| `404` на все запросы | в путях нужен префикс `/api`: `/api/tasks`, а не `/tasks` |
| `No such host` или таймаут | API не поднят; в эталоне имя сервиса — `api`, локально адрес `http://localhost:5000` |