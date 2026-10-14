using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ToirProf.Desktop.Services;
using ToirProf.Desktop.ViewModels.Screens;

namespace ToirProf.Desktop.ViewModels;

/// <summary>
/// Оболочка desktop-клиента: боковое меню, верхняя панель, хлебные
/// крошки и всплывающие сообщения живут здесь, а наполняет их активный
/// экран. Один объект на всё окно — проще держать состояние в одном
/// месте, чем раздавать его по восьми представлениям.
///
/// Сам экран входа тоже создаётся здесь, но его поля живут в
/// <see cref="LoginViewModel" />: оболочка не должна знать, что такое
/// пароль. Единственное, что она делает, — ловит событие «вход удался»
/// и открывает дашборд.
/// </summary>
public sealed partial class MainWindowViewModel : ObservableObject, IDisposable
{
    private readonly ApiClient _api;
    private readonly ToastService _toasts;
    private readonly FileLogger _log;
    private readonly NavigationService _nav;

    private PageViewModel? _page;

    public MainWindowViewModel(ApiClient api, ToastService toasts, FileLogger log, NavigationService nav)
    {
        _api = api;
        _toasts = toasts;
        _log = log;
        _nav = nav;

        VisibleMenu = new ReadOnlyObservableCollection<MenuItem>(
            new ObservableCollection<MenuItem>(NavigationService.All));

        ShowLogin();
    }

    /// <summary>
    /// Сервисы, доступные экранам. Оболочка владеет ими, но экрану нужны
    /// те же самые экземпляры — иначе журнал писался бы в один файл,
    /// а токен хранился бы в другом.
    /// </summary>
    public ApiClient Api => _api;

    public FileLogger Log => _log;

    public ReadOnlyObservableCollection<MenuItem> VisibleMenu { get; }

    public ReadOnlyObservableCollection<string> Breadcrumbs => _nav.Breadcrumbs;

    public ReadOnlyObservableCollection<Toast> Toasts => _toasts.Items;

    /// <summary>Активный экран. При смене экрана старый освобождает подписки.</summary>
    public PageViewModel? Page
    {
        get => _page;
        private set
        {
            if (SetProperty(ref _page, value))
            {
                OnPropertyChanged(nameof(IsLoggedIn));
                OnPropertyChanged(nameof(StatusText));
                OnPropertyChanged(nameof(WindowTitle));
            }
        }
    }

    public bool IsLoggedIn => _nav.Current != ScreenKind.Login;

    /// <summary>
    /// Правая часть верхней панели. Собирается из того, что клиент знает
    /// наверняка: кто вошёл, есть ли связь, сколько операций ждёт отправки.
    /// </summary>
    public string StatusText
    {
        get
        {
            if (!IsLoggedIn)
            {
                return "Не авторизован";
            }

            var link = _api.IsOffline ? "Нет связи" : "Связь есть";
            var queue = _api.PendingQueueCount > 0 ? $", в очереди {_api.PendingQueueCount}" : string.Empty;
            return $"{_api.Username} · {_api.Role} · {link}{queue}";
        }
    }

    public string WindowTitle => IsLoggedIn
        ? $"ТОиР-Проф — {_api.Username} ({_api.Role})"
        : "ТОиР-Проф — вход";

    public bool CanGoBack => _nav.Current != ScreenKind.Login && _nav.Current != ScreenKind.Dashboard;

    public string CurrentScreenTitle => _nav.CurrentTitle;

    // ------------------------------------------------------------ состояние

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string _busyCaption = string.Empty;

    // ------------------------------------------------------------ навигация

    [RelayCommand]
    private Task OpenDashboardAsync() => OpenAsync(ScreenKind.Dashboard);

    [RelayCommand]
    private Task OpenEquipmentAsync() => OpenAsync(ScreenKind.Equipment);

    [RelayCommand]
    private Task OpenScheduleAsync() => OpenAsync(ScreenKind.Schedule);

    [RelayCommand]
    private Task OpenWorkOrdersAsync() => OpenAsync(ScreenKind.WorkOrders);

    [RelayCommand]
    private Task OpenCrewsAsync() => OpenAsync(ScreenKind.Crews);

    [RelayCommand]
    private Task OpenMaterialsAsync() => OpenAsync(ScreenKind.Materials);

    [RelayCommand]
    private Task OpenReportsAsync() => OpenAsync(ScreenKind.Reports);

    /// <summary>
    /// Открыть экран по имени пункта меню. Вызывается из разметки, где
    /// параметр команды приходит строкой, а не перечислением.
    /// </summary>
    [RelayCommand]
    private Task OpenByNameAsync(string? screen)
    {
        if (!Enum.TryParse<ScreenKind>(screen, out var kind))
        {
            return Task.CompletedTask;
        }

        return OpenAsync(kind);
    }

    /// <summary>
    /// Переход на экран. Права проверяет NavigationService: если роль не
    /// подходит, показываем тост и остаёмся на текущем экране — так
    /// эксперту проще понять, что произошло.
    /// </summary>
    private async Task OpenAsync(ScreenKind screen)
    {
        if (screen == ScreenKind.Login)
        {
            ShowLogin();
            return;
        }

        if (!_nav.GoTo(screen, _api.Role))
        {
            _toasts.Warn($"У роли {_api.Role} нет доступа к экрану «{NavigationService.TitleOf(screen)}».");
            return;
        }

        var page = BuildPage(screen);
        AttachAuthenticated(page);
        Page = page;

        IsBusy = true;
        BusyCaption = $"Загружаем «{NavigationService.TitleOf(screen)}»…";
        try
        {
            await page.RefreshAsync();
            _log.Info($"Открыт экран {screen}");
        }
        finally
        {
            IsBusy = false;
            BusyCaption = string.Empty;
            OnPropertyChanged(nameof(StatusText));
        }
    }

    [RelayCommand]
    private void Logout()
    {
        _api.Logout();
        _toasts.Info("Сеанс завершён");
        ShowLogin();
    }

    /// <summary>
    /// Экран входа. Создаётся заново при каждом выходе из сеанса, чтобы
    /// поле «пароль» и счётчик неудачных попыток начинали с нуля.
    /// </summary>
    private void ShowLogin()
    {
        _nav.Reset();
        var login = new LoginViewModel(_api, _toasts, _log);
        login.Authenticated += OnAuthenticated;
        Page?.Dispose();
        Page = login;
        OnPropertyChanged(nameof(CanGoBack));
    }

    /// <summary>
    /// Создаёт представление экрана. Один раз в одном месте — чтобы не
    /// разъехалось: экран добавлен в меню, но забыт здесь.
    /// </summary>
    private PageViewModel BuildPage(ScreenKind screen) => screen switch
    {
        ScreenKind.Dashboard => new DashboardViewModel(_api, _toasts, _log),
        ScreenKind.Equipment => new EquipmentViewModel(_api, _toasts, _log),
        ScreenKind.Schedule => new ScheduleViewModel(_api, _toasts, _log),
        ScreenKind.WorkOrders => new WorkOrdersViewModel(_api, _toasts, _log),
        ScreenKind.Crews => new CrewsViewModel(_api, _toasts, _log),
        ScreenKind.Materials => new MaterialsViewModel(_api, _toasts, _log),
        ScreenKind.Reports => new ReportsViewModel(_api, _toasts, _log),
        _ => new LoginViewModel(_api, _toasts, _log),
    };

    private void AttachAuthenticated(PageViewModel page)
    {
        if (page is LoginViewModel login)
        {
            login.Authenticated += OnAuthenticated;
        }
    }

    private async void OnAuthenticated()
    {
        // Событие приходит из команды входа, поэтому обработчик обязан
        // быть async void: подписчик не ждёт результата. Исключения
        // внутри перехватываются оболочкой и превращаются в тост.
        try
        {
            await OpenAsync(ScreenKind.Dashboard);
        }
        catch (Exception ex)
        {
            _log.Error("Не удалось открыть дашборд после входа", ex);
            _toasts.Error(ex.Message);
        }
    }

    // ------------------------------------------------------------- прочее

    [RelayCommand]
    private void Refresh()
    {
        if (Page is not null)
        {
            _ = RefreshPageAsync();
        }
    }

    private async Task RefreshPageAsync()
    {
        IsBusy = true;
        BusyCaption = "Обновляем данные…";
        try
        {
            await Page!.RefreshAsync();
        }
        finally
        {
            IsBusy = false;
            BusyCaption = string.Empty;
            OnPropertyChanged(nameof(StatusText));
        }
    }

    public void Dispose()
    {
        _toasts.Dispose();
        _api.Dispose();
        GC.SuppressFinalize(this);
    }
}
