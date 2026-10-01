Сессия 7. Desktop-клиент: экраны · 70–150 мин

# 1. Экран входа (70–95 мин)

`ViewModels/LoginViewModel.cs`:

```csharp
using System.Net;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using TaskPlanner.Desktop.Services;

namespace TaskPlanner.Desktop.ViewModels;

public partial class LoginViewModel(
    ApiClient apiClient,
    TokenStorage tokenStorage) : ViewModelBase
{
    [ObservableProperty]
    private string _email = string.Empty;

    [ObservableProperty]
    private string _password = string.Empty;

    [ObservableProperty]
    private string _fullName = string.Empty;

    [ObservableProperty]
    private string _errorMessage = string.Empty;

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private bool _isAuthenticated;

    [ObservableProperty]
    private bool _isRegisterMode;

    public string SubmitTitle => IsRegisterMode ? "Зарегистрироваться" : "Войти";

    partial void OnIsRegisterModeChanged(bool value)
        => OnPropertyChanged(nameof(SubmitTitle));

    private bool Validate()
    {
        if (string.IsNullOrWhiteSpace(Email))
        {
            ErrorMessage = "Укажите email";
            return false;
        }

        if (string.IsNullOrEmpty(Password))
        {
            ErrorMessage = "Укажите пароль";
            return false;
        }

        if (Password.Length < 8)
        {
            ErrorMessage = "Пароль не короче 8 символов";
            return false;
        }

        if (IsRegisterMode && string.IsNullOrWhiteSpace(FullName))
        {
            ErrorMessage = "Укажите имя";
            return false;
        }

        ErrorMessage = string.Empty;
        return true;
    }

    [RelayCommand]
    private async Task SubmitAsync()
    {
        if (IsBusy || !Validate())
        {
            return;
        }

        IsBusy = true;
        ErrorMessage = string.Empty;

        try
        {
            if (IsRegisterMode)
            {
                var user = await apiClient.RegisterAsync(Email.Trim(), Password, FullName.Trim());

                // Регистрация токена не возвращает — сразу входим
                var session = await apiClient.LoginAsync(Email.Trim(), Password);

                apiClient.SetToken(session.Token);
                tokenStorage.Save(session.Token, session.User.FullName, session.User.Email);
            }
            else
            {
                var session = await apiClient.LoginAsync(Email.Trim(), Password);

                apiClient.SetToken(session.Token);
                tokenStorage.Save(session.Token, session.User.FullName, session.User.Email);
            }

            IsAuthenticated = true;
        }
        catch (ApiException e)
        {
            ErrorMessage = e.Message;
        }
        catch (TaskCanceledException)
        {
            ErrorMessage = "Сервер не отвечает. Проверьте, что API запущен.";
        }
        catch (HttpRequestException)
        {
            ErrorMessage = "Нет связи с сервером на http://localhost:5000";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private void ToggleMode()
        => IsRegisterMode = !IsRegisterMode;

    [RelayCommand]
    private void Logout()
    {
        apiClient.SetToken(null);
        tokenStorage.Clear();
        IsAuthenticated = false;
        Password = string.Empty;
    }
}
```

> **Замечание:** `ApiClient.RegisterAsync` возвращает `UserDto`, но в коде
> результат не используется — он нужен только для проверки, что запрос
> прошёл. Если компилятор предупредит о неиспользуемой переменной,
> замените строку на `_ = await apiClient.RegisterAsync(...)`.

`Views/LoginView.axaml`:

```xml
<UserControl xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:vm="using:TaskPlanner.Desktop.ViewModels"
             x:Class="TaskPlanner.Desktop.Views.LoginView"
             x:DataType="vm:LoginViewModel">

  <Border Background="#F1F6F2">
    <StackPanel Width="380" Margin="0,80,0,0" HorizontalAlignment="Center" Spacing="12">

      <TextBlock Text="Планировщик задач" FontSize="26" FontWeight="Bold"
                 Foreground="#364046" HorizontalAlignment="Center" />

      <TextBlock Classes="hint"
                 Text="Войдите, чтобы увидеть свои задачи"
                 HorizontalAlignment="Center" Foreground="#6D797F" />

      <TextBlock Text="{Binding ErrorMessage}"
                 Foreground="#D13C3C" TextWrapping="Wrap"
                 IsVisible="{Binding ErrorMessage, Converter={x:Static StringConverters.IsNotNullOrEmpty}}" />

      <TextBox Watermark="Email" Text="{Binding Email}" />

      <TextBox Watermark="Пароль" PasswordChar="•"
               Text="{Binding Password}" />

      <TextBox Watermark="Имя и фамилия" Text="{Binding FullName}"
               IsVisible="{Binding IsRegisterMode}" />

      <Button Content="{Binding SubmitTitle}"
              Command="{Binding SubmitCommand}"
              IsEnabled="{Binding !IsBusy}"
              HorizontalAlignment="Stretch"
              Background="#0F9346" Foreground="White" />

      <ProgressBar IsIndeterminate="True"
                   IsVisible="{Binding IsBusy}" Height="4" />

      <Button Content="Регистрация / Вход"
              Command="{Binding ToggleModeCommand}"
              HorizontalAlignment="Center" Background="Transparent" />

    </StackPanel>
  </Border>
</UserControl>
```

`Views/LoginView.axaml.cs`:

```csharp
using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace TaskPlanner.Desktop.Views;

public partial class LoginView : UserControl
{
    public LoginView()
    {
        InitializeComponent();
    }

    private void InitializeComponent() => AvaloniaXamlLoader.Load(this);
}
```

# 2. Экран задач (95–130 мин)

`ViewModels/TaskItemViewModel.cs`:

```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using TaskPlanner.Desktop.Services;

namespace TaskPlanner.Desktop.ViewModels;

/// <summary>
/// Одна задача в списке. Содержит только текущие значения —
/// после любой операции сервер возвращает новый объект, поэтому
/// строку пересоздаём, а не правим на месте.
/// </summary>
public partial class TaskItemViewModel(TaskDto dto) : ObservableObject
{
    public long Id => dto.Id;

    public string Title => dto.Title;

    public string? Description => dto.Description;

    public string StatusText => dto.Status switch
    {
        Core.Enums.TaskStatus.New => "Новая",
        Core.Enums.TaskStatus.InProgress => "В работе",
        Core.Enums.TaskStatus.Done => "Выполнена",
        Core.Enums.TaskStatus.Cancelled => "Отменена",
        _ => dto.Status.ToString(),
    };

    public string PriorityText => dto.Priority switch
    {
        Core.Enums.TaskPriority.Low => "Низкий",
        Core.Enums.TaskPriority.Medium => "Средний",
        Core.Enums.TaskPriority.High => "Высокий",
        _ => dto.Priority.ToString(),
    };

    public bool IsDone => dto.Status == Core.Enums.TaskStatus.Done;

    public string DueText => string.IsNullOrEmpty(dto.DueDate)
        ? "Без срока"
        : DateTime.Parse(dto.DueDate).ToString("dd.MM.yyyy");

    public bool IsOverdue => !IsDone
        && !string.IsNullOrEmpty(dto.DueDate)
        && DateTime.Parse(dto.DueDate).Date < DateTime.Today;
}
```

`ViewModels/TasksViewModel.cs`:

```csharp
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using TaskPlanner.Desktop.Services;

namespace TaskPlanner.Desktop.ViewModels;

public partial class TasksViewModel(ApiClient apiClient) : ViewModelBase
{
    [ObservableProperty]
    private string _statusFilter = "";

    [ObservableProperty]
    private string _errorMessage = string.Empty;

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private bool _isSummaryVisible;

    [ObservableProperty]
    private string _summaryText = string.Empty;

    public ObservableCollection<TaskItemViewModel> Items { get; } = new();

    [RelayCommand]
    private async Task LoadAsync()
    {
        if (IsBusy)
        {
            return;
        }

        IsBusy = true;
        ErrorMessage = string.Empty;

        try
        {
            var page = await apiClient.GetTasksAsync(
                page: 1,
                pageSize: 50,
                status: string.IsNullOrEmpty(StatusFilter) ? null : StatusFilter);

            Items.Clear();

            foreach (var dto in page.Items)
            {
                Items.Add(new TaskItemViewModel(dto));
            }

            SummaryText = $"Показано {Items.Count} из {page.Total}";
        }
        catch (ApiException e)
        {
            ErrorMessage = e.Message;
        }
        catch (HttpRequestException)
        {
            ErrorMessage = "Нет связи с сервером";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task ToggleCompletedAsync(TaskItemViewModel? item)
    {
        if (item is null)
        {
            return;
        }

        try
        {
            await apiClient.ToggleCompletedAsync(item.Id);
            await LoadAsync();
        }
        catch (ApiException e)
        {
            ErrorMessage = e.Message;
        }
    }

    [RelayCommand]
    private async Task DeleteAsync(TaskItemViewModel? item)
    {
        if (item is null)
        {
            return;
        }

        var confirmed = await ConfirmationService.AskAsync(
            this, $"Удалить задачу «{item.Title}»?");

        if (!confirmed)
        {
            return;
        }

        try
        {
            await apiClient.DeleteTaskAsync(item.Id);
            await LoadAsync();
        }
        catch (ApiException e)
        {
            ErrorMessage = e.Message;
        }
    }

    [RelayCommand]
    private async Task ShowSummaryAsync()
    {
        IsSummaryVisible = !IsSummaryVisible;

        if (!IsSummaryVisible)
        {
            return;
        }

        try
        {
            var summary = await apiClient.GetSummaryAsync();

            var low = summary.ByPriority.GetValueOrDefault("low");
            var medium = summary.ByPriority.GetValueOrDefault("medium");
            var high = summary.ByPriority.GetValueOrDefault("high");

            SummaryText =
                $"Всего: {summary.Total}\n" +
                $"Выполнено: {summary.Done}\n" +
                $"Не выполнено: {summary.NotDone}\n" +
                $"Просрочено: {summary.Overdue}\n" +
                $"Незавершённые: низкий {low}, средний {medium}, высокий {high}";
        }
        catch (ApiException e)
        {
            ErrorMessage = e.Message;
        }
    }

    [RelayCommand]
    private void HideSummary() => IsSummaryVisible = false;

    partial void OnStatusFilterChanged(string value) => _ = LoadAsync();
}
```

# 3. Подтверждение удаления (130–138 мин)

Диалог подтверждения в Avalonia делается отдельным окном. Простейший
вариант — окно с сообщением и двумя кнопками:

`Views/ConfirmWindow.axaml`:

```xml
<Window xmlns="https://github.com/avaloniaui"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        x:Class="TaskPlanner.Desktop.Views.ConfirmWindow"
        Title="Подтверждение" Width="380" SizeToContent="Height"
        WindowStartupLocation="CenterOwner" CanResize="False">

  <StackPanel Margin="20" Spacing="16">
    <TextBlock x:Name="MessageText" TextWrapping="Wrap" />
    <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" Spacing="8">
      <Button Content="Отмена" Click="OnCancel" />
      <Button Content="Удалить" Click="OnConfirm" Background="#D13C3C" Foreground="White" />
    </StackPanel>
  </StackPanel>
</Window>
```

`Views/ConfirmWindow.axaml.cs`:

```csharp
using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace TaskPlanner.Desktop.Views;

public partial class ConfirmWindow : Window
{
    public ConfirmWindow()
    {
        InitializeComponent();
    }

    private void InitializeComponent() => AvaloniaXamlLoader.Load(this);

    public static Task<bool> AskAsync(Window owner, string message)
    {
        var window = new ConfirmWindow();

        window.FindControl<TextBlock>("MessageText")!.Text = message;

        var tcs = new TaskCompletionSource<bool>();

        void Closed(object? sender, Avalonia.Controls.WindowClosingEventArgs e)
        {
            tcs.TrySetResult(window.Result);
        }

        window.Closed += Closed;
        window.ShowDialog(owner);

        return tcs.Task;
    }

    private bool Result { get; set; }

    private void OnConfirm(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        Result = true;
        Close();
    }

    private void OnCancel(object? sender, Avalonia.Interactivity.RoutedEventArgs e) => Close();
}
```

`Services/ConfirmationService.cs`:

```csharp
using Avalonia.Controls;
using TaskPlanner.Desktop.Views;

namespace TaskPlanner.Desktop.Services;

public static class ConfirmationService
{
    public static Task<bool> AskAsync(object owner, string message)
    {
        if (owner is not TopLevel topLevel)
        {
            return Task.FromResult(false);
        }

        var ownerWindow = topLevel as Window ?? topLevel.GetVisualRoot() as Window;

        return ownerWindow is null
            ? Task.FromResult(false)
            : ConfirmWindow.AskAsync(ownerWindow, message);
    }
}
```

Добавьте в `Services/ConfirmationService.cs` первый `using`:

```csharp
using Avalonia.VisualTree;
```

# 4. Экран задач в XAML (138–145 мин)

`Views/TasksView.axaml`:

```xml
<UserControl xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:vm="using:TaskPlanner.Desktop.ViewModels"
             x:Class="TaskPlanner.Desktop.Views.TasksView"
             x:DataType="vm:TasksViewModel">

  <DockPanel LastChildFill="True">

    <Border DockPanel.Dock="Top" Background="#364046" Padding="16,12">
      <Grid ColumnDefinitions="Auto,*,Auto">
        <TextBlock Grid.Column="0" Text="Задачи" Foreground="White"
                   FontSize="20" FontWeight="Bold" VerticalAlignment="Center" />
        <StackPanel Grid.Column="2" Orientation="Horizontal" Spacing="8">
          <ComboBox Width="150" ItemsSource="{Binding StatusFilterOptions}"
                    SelectedItem="{Binding StatusFilter}" />
          <Button Content="Обновить" Command="{Binding LoadCommand}" />
          <Button Content="Сводка" Command="{Binding ShowSummaryCommand}" />
        </StackPanel>
      </Grid>
    </Border>

    <StackPanel DockPanel.Dock="Top" Margin="16,12" Spacing="8"
                IsVisible="{Binding ErrorMessage, Converter={x:Static StringConverters.IsNotNullOrEmpty}}">
      <TextBlock Text="{Binding ErrorMessage}" Foreground="#D13C3C" TextWrapping="Wrap" />
    </StackPanel>

    <Border DockPanel.Dock="Bottom" Background="White" Padding="16,10">
      <TextBlock Text="{Binding SummaryText}" Foreground="#6D797F" />
    </Border>

    <ScrollViewer>
      <ItemsControl ItemsSource="{Binding Items}" Margin="16">
        <ItemsControl.ItemTemplate>
          <DataTemplate x:DataType="vm:TaskItemViewModel">
            <Border Background="White" CornerRadius="10" Padding="14" Margin="0,0,0,10">
              <Grid ColumnDefinitions="Auto,*,Auto" RowDefinitions="Auto,Auto,Auto">
                <CheckBox Grid.Row="0" Grid.Column="0"
                          IsChecked="{Binding IsDone, Mode=OneWay}"
                          Command="{Binding $parent[ItemsControl].((vm:TasksViewModel)DataContext).ToggleCompletedCommand}"
                          CommandParameter="{Binding}" />

                <TextBlock Grid.Row="0" Grid.Column="1" Text="{Binding Title}"
                           FontWeight="SemiBold" VerticalAlignment="Center" Margin="8,0" />

                <StackPanel Grid.Row="0" Grid.Column="2" Orientation="Horizontal" Spacing="8">
                  <Button Content="Удалить"
                          Command="{Binding $parent[ItemsControl].((vm:TasksViewModel)DataContext).DeleteCommand}"
                          CommandParameter="{Binding}"
                          Background="#D13C3C" Foreground="White" />
                </StackPanel>

                <TextBlock Grid.Row="1" Grid.Column="1" Grid.ColumnSpan="2"
                           Text="{Binding Description}" Foreground="#6D797F"
                           TextWrapping="Wrap" IsVisible="{Binding Description, Converter={x:Static StringConverters.IsNotNull}}" />

                <StackPanel Grid.Row="2" Grid.Column="1" Grid.ColumnSpan="2"
                            Orientation="Horizontal" Spacing="12" Margin="8,8,0,0">
                  <TextBlock Text="{Binding StatusText}" FontSize="13" />
                  <TextBlock Text="{Binding PriorityText}" FontSize="13" />
                  <TextBlock Text="{Binding DueText}" FontSize="13" Foreground="#6D797F" />
                  <TextBlock Text="просрочена" FontSize="13" Foreground="#D13C3C"
                             IsVisible="{Binding IsOverdue}" />
                </StackPanel>
              </Grid>
            </Border>
          </DataTemplate>
        </ItemsControl.ItemTemplate>
      </ItemsControl>
    </ScrollViewer>

  </DockPanel>
</UserControl>
```

Добавьте в `TasksViewModel` список значений фильтра:

```csharp
public IReadOnlyList<string> StatusFilterOptions { get; } =
    ["", "new", "in_progress", "done", "cancelled"];
```

# 5. Открытие списка при входе (145–150 мин)

В `MainWindowViewModel` подпишитесь на вход и загружайте список:

```csharp
Login.PropertyChanged += (_, e) =>
{
    if (e.PropertyName != nameof(LoginViewModel.IsAuthenticated))
    {
        return;
    }

    IsAuthenticated = Login.IsAuthenticated;

    if (IsAuthenticated)
    {
        _ = Tasks.LoadAsync();
    }
};
```

# Проверка

```bash
cd src/desktop/TaskPlanner.Desktop
dotnet run
```

1. Появится форма входа. Введите неверный пароль → «Неверный email или пароль».
2. Нажмите «Регистрация / Вход» → появляется поле имени, кнопка меняет текст.
3. Зарегистрируйтесь и войдите → открывается список задач.
4. Список не пуст: 10–50 задач из `seed.sql`.
5. Поставьте галочку у задачи → статус меняется на «Выполнена», строка
   обновляется, счётчик «Показано N из M» пересчитан.
6. Фильтр по статусу: выберите `done` → список обновился без кнопки
   «Обновить» (срабатывает `OnStatusFilterChanged`).
7. Нажмите «Удалить» → диалог подтверждения; «Отмена» ничего не удаляет,
   «Удалить» убирает строку.
8. Нажмите «Сводка» → панель с числами совпадает с `GET /api/tasks/summary`.
9. Закройте приложение и откройте снова → вы уже внутри, список загружен:
   токен сохранён в `%APPDATA%/TaskPlanner/session.json`
   (на РедОС — `~/.local/share/TaskPlanner/session.json`).
10. Остановите API, нажмите «Обновить» → понятное сообщение о недоступности
    сервера, приложение не падает.

```bash
# проверить, что desktop ходит в тот же API одной базой
curl -s -X POST http://localhost:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"desktop-check@college.ru","password":"Passw0rd123","fullName":"Проверка"}'
# зарегистрируйте этого же пользователя из приложения — должен быть 409
```

# Коммит

```bash
git add src/desktop
git commit -m "Desktop-клиент: вход, список задач, сводка, подтверждение удаления"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Свойство из ViewModel не обновляется | класс не `partial` либо нет `[ObservableProperty]` |
| Команда не вызывается, `Command` пустой | имя команды генерируется из метода: `LoadAsync` → `LoadCommand` |
| `ToggleCompletedCommand` не находится в DataTemplate | команда лежит в родительском ViewModel; нужен `$parent[ItemsControl].DataContext` |
| `StringConverters` не найден | добавьте `xmlns` или используйте `IsVisible="{Binding ErrorMessage.Length}"` — нет, `Text` пустой даст `NullReference`; правильно — конвертер `x:Static StringConverters.IsNotNullOrEmpty` |
| Диалог подтверждения не появляется | `AskAsync` вернул `false`: передан не `Window`; передавайте `this` из ViewModel нельзя — используйте `TopLevel` |
| Показан пустой список | не вызвали `Tasks.LoadAsync()` после входа |
| Не собирается на РедОС | проверьте `Environment.SpecialFolder.ApplicationData` и отсутствие `System.Drawing` |

# Итог сессии 7

Раздел «Desktop-клиент — 15 баллов»:

- [x] настоящее настольное приложение на Avalonia, **не WebView**
- [x] 3–4 экрана: вход, список задач, карточка/детали, сводка
- [x] авторизация и хранение токена между запусками
- [x] создание, изменение, отметка выполнения, удаление
- [x] приложение запускается по инструкции из README (сессия 9)

Скриншоты Avalonia-клиента — в `docs/screenshots/`:

```bash
# на РедОС и Linux удобно снимать окно командой
gnome-screenshot -w -f docs/screenshots/desktop-tasks.png
```

---

Дальше: [21-Tauri-или-PWA-вместо-Avalonia](21-Tauri-или-PWA-вместо-Avalonia)
