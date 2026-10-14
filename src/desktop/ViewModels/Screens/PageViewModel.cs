using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ToirProf.Desktop.Services;

namespace ToirProf.Desktop.ViewModels.Screens;

/// <summary>
/// Общая часть всех экранов со списком: поиск, сортировка, пагинация,
/// индикатор загрузки и состояние ошибки.
///
/// Зачем базовый класс. Восемь экранов повторяют один и тот же каркас,
/// и разница между ними только в том, какой запрос уходит на сервер.
/// Если разнести каркас по восьми файлам, через неделю в одном из них
/// забудется про состояние ошибки — и демонстрация это покажет.
///
/// Бизнес-логики здесь нет: клиент только спрашивает, показывает и
/// отдаёт назад выбранные фильтры.
/// </summary>
public abstract partial class PageViewModel : ObservableObject, IDisposable
{
    /// <summary>Строк на странице по умолчанию — столько влезает без прокрутки.</summary>
    public const int DefaultPageSize = 20;

    private CancellationTokenSource? _loadCts;

    protected PageViewModel(ApiClient api, ToastService toasts, FileLogger log)
    {
        Api = api;
        Toasts = toasts;
        Log = log;
    }

    /// <summary>
    /// Конструктор без сервисов — для экрана авторизации, который
    /// ничего не грузит: поля формы и кнопка входа принадлежат оболочке.
    /// </summary>
    protected PageViewModel()
    {
    }

    public ApiClient? Api { get; }

    public ToastService? Toasts { get; }

    public FileLogger? Log { get; }

    // ------------------------------------------------------------ состояние

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanGoNext))]
    [NotifyPropertyChangedFor(nameof(CanGoPrevious))]
    [NotifyPropertyChangedFor(nameof(PageCaption))]
    private int _page = 1;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(CanGoNext))]
    [NotifyPropertyChangedFor(nameof(CanGoPrevious))]
    [NotifyPropertyChangedFor(nameof(PageCaption))]
    private int _total;

    [ObservableProperty]
    private int _pageSize = DefaultPageSize;

    [ObservableProperty]
    private bool _isBusy;

    /// <summary>Подпись под индикатором: что именно сейчас грузится.</summary>
    [ObservableProperty]
    private string _statusText = string.Empty;

    /// <summary>
    /// Текст ошибки. Непустой — значит экран показывает красную
    /// плашку с кнопкой «Повторить». Пустой — обычный список.
    /// </summary>
    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(RetryCommand))]
    private string? _errorText;

    [ObservableProperty]
    private string? _searchText;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(SortCaption))]
    private string _sortField = "createdAt";

    [ObservableProperty]
    private string _sortOrder = "desc";

    // ------------------------------------------------------------ вычисляемое

    public int TotalPages => PageSize <= 0 ? 0 : (int)Math.Ceiling(Total / (double)PageSize);

    public bool CanGoNext => Page < TotalPages;

    public bool CanGoPrevious => Page > 1;

    public string PageCaption => Total == 0 ? "нет записей" : $"стр. {Page} из {TotalPages} · всего {Total}";

    public string SortCaption => $"{SortFieldLabel(SortField)} {(SortOrder == "asc" ? "↑" : "↓")}";

    public string SearchTextOrEmpty => string.IsNullOrWhiteSpace(SearchText) ? string.Empty : SearchText.Trim();

    // -------------------------------------------------------------- команды

    /// <summary>Команды экрана. Переопределяется наследниками.</summary>
    [RelayCommand]
    public virtual Task RefreshAsync()
    {
        ErrorText = null;
        return Task.CompletedTask;
    }

    /// <summary>Повтор после ошибки — та же загрузка, но без сброса фильтров.</summary>
    [RelayCommand(CanExecute = nameof(CanRetry))]
    private Task RetryAsync() => RefreshAsync();

    public bool CanRetry() => ErrorText is not null;

    [RelayCommand]
    private async Task NextPageAsync()
    {
        if (!CanGoNext)
        {
            return;
        }

        Page++;
        await RefreshAsync();
    }

    [RelayCommand]
    private async Task PreviousPageAsync()
    {
        if (!CanGoPrevious)
        {
            return;
        }

        Page--;
        await RefreshAsync();
    }

    [RelayCommand]
    private async Task FirstPageAsync()
    {
        Page = 1;
        await RefreshAsync();
    }

    /// <summary>
    /// Смена размера страницы сбрасывает номер на первый: иначе
    /// пользователь окажется на странице 7 из 2.
    /// </summary>
    [RelayCommand]
    private async Task ChangePageSizeAsync(string? size)
    {
        if (!int.TryParse(size, out var parsed) || parsed < 5 || parsed > 100)
        {
            return;
        }

        PageSize = parsed;
        Page = 1;
        await RefreshAsync();
    }

    /// <summary>Клик по заголовку столбца: тот же столбец переворачивает порядок.</summary>
    [RelayCommand]
    private async Task SortByAsync(string? field)
    {
        if (string.IsNullOrWhiteSpace(field))
        {
            return;
        }

        SortOrder = string.Equals(SortField, field, StringComparison.OrdinalIgnoreCase) && SortOrder == "desc"
            ? "asc"
            : "desc";
        SortField = field;
        Page = 1;
        await RefreshAsync();
    }

    /// <summary>
    /// Поиск по кнопке и по Enter. Кнопка нужна, потому что мастер
    /// вводит инвентарный номер и ждёт, а не отпускает клавишу.
    /// </summary>
    [RelayCommand]
    private async Task SearchAsync()
    {
        Page = 1;
        await RefreshAsync();
    }

    /// <summary>
    /// Обёртка загрузки: включает индикатор, гасит предыдущий запрос,
    /// ловит ошибку и превращает её в текст на экране. Наследники
    /// вызывают только её, а свой запрос пишут в LoadAsync.
    /// </summary>
    protected async Task RunLoadAsync(string caption, Func<CancellationToken, Task> load)
    {
        _loadCts?.Cancel();
        _loadCts = new CancellationTokenSource();
        var ct = _loadCts.Token;

        IsBusy = true;
        StatusText = caption;
        ErrorText = null;
        OnPropertyChanged(nameof(ErrorText));

        try
        {
            await load(ct);
        }
        catch (OperationCanceledException)
        {
            // Пользователь успел нажать «Обновить» ещё раз — это не сбой.
        }
        catch (Exception ex)
        {
            Log?.Error($"{GetType().Name}: загрузка не удалась", ex);
            ErrorText = ex.Message;
            OnPropertyChanged(nameof(ErrorText));
            Toasts?.Error(ex.Message);
        }
        finally
        {
            IsBusy = false;
            StatusText = string.Empty;
        }
    }

    /// <summary>Заголовок столбца по его техническому имени.</summary>
    protected static string SortFieldLabel(string field) => field switch
    {
        "inventoryNumber" => "Инв. номер",
        "name" => "Наименование",
        "plannedDate" => "Плановая дата",
        "createdAt" => "Создана",
        "number" => "Номер",
        "status" => "Статус",
        "priority" => "Приоритет",
        "plannedStart" => "Начало",
        "downtime" => "Простой",
        "sku" => "Артикул",
        "price" => "Цена",
        "stock" => "Остаток",
        _ => field,
    };

    /// <summary>Значение по умолчанию для размера страницы в выпадающем списке.</summary>
    public IReadOnlyList<int> PageSizeOptions { get; } = [10, 20, 50, 100];

    public void Dispose()
    {
        _loadCts?.Cancel();
        _loadCts?.Dispose();
        GC.SuppressFinalize(this);
    }
}
