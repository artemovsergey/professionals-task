using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using CommunityToolkit.Mvvm.ComponentModel;

namespace ToirProf.Desktop.Services;

/// <summary>Экраны desktop-клиента. Порядок совпадает с боковым меню.</summary>
public enum ScreenKind
{
    Login,
    Dashboard,
    Equipment,
    Schedule,
    WorkOrders,
    Crews,
    Materials,
    Reports,
}

/// <summary>Пункт бокового меню: заголовок, экран и код роли для проверки прав.</summary>
public sealed record MenuItem(string Title, ScreenKind Screen, string Glyph, string[] AllowedRoles)
{
    public bool IsVisibleFor(string? role) =>
        role is null || AllowedRoles.Length == 0 || AllowedRoles.Contains(role, StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Имя экрана строкой. Команда меню принимает строку, а в разметке
    /// в <see cref="Screen" /> лежит перечисление — без этого свойства
    /// пришлось бы писать конвертер ради одного списка.
    /// </summary>
    public string Key => Screen.ToString();
}

/// <summary>
/// Навигация приложения: какой экран открыт и как выглядит хлебная крошка.
/// Вынесена отдельно от представления окна, чтобы и оболочка, и тесты
/// спрашивали у одного объекта, а не у двух разных.
/// </summary>
public sealed class NavigationService : ObservableObject
{
    /// <summary>
    /// Меню закрывает путь «Цех → экран», поэтому у каждого пункта
    /// есть родитель: без него крошка из одного слова ни о чём не говорит.
    /// </summary>
    private static readonly Dictionary<ScreenKind, string> Parents = new()
    {
        [ScreenKind.Dashboard] = "Цех",
        [ScreenKind.Equipment] = "Цех",
        [ScreenKind.Schedule] = "Цех",
        [ScreenKind.WorkOrders] = "Заявки",
        [ScreenKind.Crews] = "Справочники",
        [ScreenKind.Materials] = "Справочники",
        [ScreenKind.Reports] = "Аналитика",
    };

    public NavigationService()
    {
        Menu = new ReadOnlyObservableCollection<MenuItem>(new ObservableCollection<MenuItem>(All));
        Breadcrumbs = new ReadOnlyObservableCollection<string>(_crumbs);
    }

    public static IReadOnlyList<MenuItem> All { get; } =
    [
        new MenuItem("Дашборд мастера", ScreenKind.Dashboard, "D", []),
        new MenuItem("Оборудование цеха", ScreenKind.Equipment, "E", []),
        new MenuItem("График ТО", ScreenKind.Schedule, "G", []),
        new MenuItem("Заявки", ScreenKind.WorkOrders, "Z", []),
        new MenuItem("Бригады", ScreenKind.Crews, "B", ["ADMIN", "MANAGER"]),
        new MenuItem("Материалы и ЗИП", ScreenKind.Materials, "M", ["ADMIN", "MANAGER"]),
        new MenuItem("Отчёты", ScreenKind.Reports, "R", ["ADMIN", "MANAGER"]),
    ];

    public ReadOnlyObservableCollection<MenuItem> Menu { get; }

    /// <summary>
    /// Крошка — ReadOnly-обёртка над _crumbs: представление не должно
    /// дописывать в неё ничего, но перерисовываться обязано. Обёртка
    /// сама подписана на изменения коллекции, поэтому OnPropertyChanged
    /// для Breadcrumbs вызывать не нужно.
    /// </summary>
    public ReadOnlyObservableCollection<string> Breadcrumbs { get; }

    private readonly ObservableCollection<string> _crumbs = new();

    private ScreenKind _current = ScreenKind.Login;

    public ScreenKind Current
    {
        get => _current;
        private set
        {
            if (SetProperty(ref _current, value))
            {
                OnPropertyChanged(nameof(CurrentTitle));
                BuildBreadcrumbs(value);
            }
        }
    }

    public string CurrentTitle => TitleOf(_current);

    public bool IsLoggedIn => _current != ScreenKind.Login;

    public static string TitleOf(ScreenKind screen) =>
        screen == ScreenKind.Login
            ? "Авторизация"
            : All.FirstOrDefault(m => m.Screen == screen)?.Title ?? screen.ToString();

    /// <summary>
    /// Открыть экран. Возвращает false, если у роли нет прав: тогда
    /// вызывающий код показывает тост, а не молча меняет картинку.
    /// </summary>
    public bool GoTo(ScreenKind screen, string? role)
    {
        var item = All.FirstOrDefault(m => m.Screen == screen);
        if (item is not null && !item.IsVisibleFor(role))
        {
            return false;
        }

        Current = screen;
        return true;
    }

    /// <summary>
    /// Возврат к экрану входа. Вызывается при выходе из сеанса:
    /// навигация забывает, куда ходили, потому что после нового входа
    /// роль может быть другой и прежний экран оказаться недоступен.
    /// </summary>
    public void Reset()
    {
        Current = ScreenKind.Login;
    }

    /// <summary>
    /// Крошка всегда показывает родителя и текущий экран: «Цех /
    /// Оборудование цеха» читается быстрее, чем одно слово, а на
    /// экране «Заявки» второй уровень не нужен — там своя нумерация.
    /// </summary>
    private void BuildBreadcrumbs(ScreenKind screen)
    {
        _crumbs.Clear();
        if (screen == ScreenKind.Login)
        {
            _crumbs.Add(TitleOf(screen));
            return;
        }

        if (Parents.TryGetValue(screen, out var parent) && !string.Equals(parent, TitleOf(screen), StringComparison.Ordinal))
        {
            _crumbs.Add(parent);
        }

        _crumbs.Add(TitleOf(screen));
    }
}
