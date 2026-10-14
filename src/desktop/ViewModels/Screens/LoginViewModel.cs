using System;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ToirProf.Desktop.Services;

namespace ToirProf.Desktop.ViewModels.Screens;

/// <summary>
/// Экран авторизации. Отдельный экран, а не часть оболочки: пока
/// пользователь не вошёл, у него нет роли, а без роли нельзя построить
/// меню — значит, экран входа обязан жить сам по себе.
/// </summary>
public sealed partial class LoginViewModel : PageViewModel
{
    private readonly ApiClient _api;
    private readonly ToastService _toasts;
    private readonly DispatcherTimer _blockTimer;

    public LoginViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        _api = api;
        _toasts = toasts;

        // Логин мастера подставлен заранее: на демонстрации вводить
        // его руками каждый раз неудобно. Пароль стирается после входа.
        Login = "master";

        _blockTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        _blockTimer.Tick += (_, _) => RaiseBlockChanged();
    }

    /// <summary>
    /// Вход состоялся. Оболочка подписывается на событие и открывает
    /// дашборд: сам экран о навигации не знает — это не его дело.
    /// </summary>
    public event Action? Authenticated;

    [ObservableProperty]
    private string _login = "master";

    [ObservableProperty]
    private string _password = "Master123!";

    [ObservableProperty]
    private string? _loginError;

    public bool IsLoginBlocked => _api.BlockSecondsRemaining > 0;

    public int BlockSeconds => _api.BlockSecondsRemaining;

    /// <summary>
    /// Вход. Три неудачи подряд — и клиент закрывает форму на 15 секунд,
    /// чтобы перебор паролей не шёл непрерывным потоком.
    /// </summary>
    [RelayCommand]
    private async Task LoginAsync()
    {
        if (IsBusy || IsLoginBlocked)
        {
            return;
        }

        LoginError = null;
        IsBusy = true;
        StatusText = "Проверяем учётные данные…";
        try
        {
            var result = await _api.LoginAsync(Login, Password);

            if (!result.Success)
            {
                LoginError = result.Message;
                RaiseBlockChanged();
                _toasts.Error(result.Message);
                return;
            }

            _toasts.Success($"Здравствуйте, {_api.Username}!");
            Password = string.Empty;
            _blockTimer.Stop();
            Authenticated?.Invoke();
        }
        finally
        {
            IsBusy = false;
            StatusText = string.Empty;
        }
    }

    /// <summary>
    /// Форма входа ничего не загружает, поэтому общий <c>RefreshAsync</c>
    /// базового экрана тут лишний: F5 на экране входа не должен
    /// перезапрашивать данные сервера.
    /// </summary>
    public override Task RefreshAsync() => Task.CompletedTask;

    /// <summary>
    /// Обратный отсчёт блокировки. Таймер крутится только пока идёт
    /// блокировка, иначе он зря будит UI-нить раз в секунду всё время
    /// работы программы.
    /// </summary>
    private void RaiseBlockChanged()
    {
        OnPropertyChanged(nameof(IsLoginBlocked));
        OnPropertyChanged(nameof(BlockSeconds));

        if (IsLoginBlocked)
        {
            if (!_blockTimer.IsEnabled)
            {
                _blockTimer.Start();
            }
        }
        else
        {
            _blockTimer.Stop();
        }
    }
}
