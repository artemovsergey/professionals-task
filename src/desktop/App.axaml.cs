using System;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core.Plugins;
using Avalonia.Markup.Xaml;
using ToirProf.Desktop.Services;
using ToirProf.Desktop.ViewModels;
using ToirProf.Desktop.Views;

namespace ToirProf.Desktop;

public partial class App : Application
{
    /// <summary>
    /// Точка сборки приложения. Сервисы создаются вручную, без контейнера
    /// внедрения: их пять, все с одним временем жизни, и лишняя
    /// зависимость в csproj на РедОС только мешала бы собираться.
    /// </summary>
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.ShutdownMode = ShutdownMode.OnMainWindowClose;
            desktop.MainWindow = BuildShell();
        }

        base.OnFrameworkInitializationCompleted();
    }

    private static Window BuildShell()
    {
        var logger = new FileLogger();
        var tokens = new TokenStorage();
        var queue = new OfflineQueue();
        var api = new ApiClient(tokens, queue, logger);
        var toasts = new ToastService();

        logger.Info("Клиент ТОиР-Проф запущен");

        var navigation = new NavigationService();
        var shell = new MainWindowViewModel(api, toasts, logger, navigation);

        return new MainWindow
        {
            DataContext = shell,
        };
    }
}
