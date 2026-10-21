using CommunityToolkit.Mvvm.Input;
using System.Collections.Generic;
using System;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using ToirProf.Desktop.Models;
using ToirProf.Desktop.Services;

namespace ToirProf.Desktop.ViewModels.Screens;

/// <summary>
/// Заявки на ремонт и ТО — самый рабочий экран мастера.
///
/// Здесь виден весь жизненный цикл: создать, назначить бригаду, начать,
/// завершить, списать материал. Клиент не решает, можно ли завершить
/// заявку без причины неисправности или назначить занятую бригаду, —
/// это делает сервер, а клиент показывает его ответ.
/// </summary>
public sealed partial class WorkOrdersViewModel : PageViewModel
{
    public WorkOrdersViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        // Плановые даты новой заявки заполнены заранее: пустые поля
        // выбора даты показывают английские подсказки, а заявку всё
        // равно заводят «на завтра-послезавтра», не в прошлое.
        DraftPlannedStart = DateOnly.FromDateTime(DateTime.Today);
        DraftPlannedEnd = DraftPlannedStart.Value.AddDays(3);
    }

    public ObservableCollection<WorkOrderRow> Rows { get; } = [];

    public ObservableCollection<CrewShort> Crews { get; } = [];

    public ObservableCollection<EquipmentShort> Equipment { get; } = [];

    public IReadOnlyList<string> StatusOptions { get; } = ["Черновик", "Назначена", "В работе", "Завершена", "Отменена"];

    public IReadOnlyList<string> PriorityOptions { get; } = ["Низкий", "Средний", "Высокий", "Аварийный"];

    [ObservableProperty]
    private string? _statusFilter;

    [ObservableProperty]
    private string? _priorityFilter;

    [ObservableProperty]
    private Guid? _equipmentFilter;

    [ObservableProperty]
    private Guid? _crewFilter;

    // -------------------------------------------------------- новая заявка

    [ObservableProperty]
    private EquipmentShort? _draftEquipment;

    [ObservableProperty]
    private string _draftTitle = string.Empty;

    [ObservableProperty]
    private string _draftDescription = string.Empty;

    [ObservableProperty]
    private string _draftPriority = "Средний";

    [ObservableProperty]
    private DateOnly? _draftPlannedStart;

    [ObservableProperty]
    private DateOnly? _draftPlannedEnd;

    [ObservableProperty]
    private CrewShort? _draftCrew;

    // ------------------------------------------------------ текущая заявка

    [ObservableProperty]
    private WorkOrderRow? _selected;

    [ObservableProperty]
    private CrewShort? _assignCrew;

    [ObservableProperty]
    private string _failureReason = string.Empty;

    [ObservableProperty]
    private Guid? _writeOffMaterial;

    [ObservableProperty]
    private decimal _writeOffQuantity;

    public override async Task RefreshAsync()
    {
        await RunLoadAsync("Загружаем заявки…", async ct =>
        {
            var path =
                $"/api/work-orders?query={Uri.EscapeDataString(SearchTextOrEmpty)}" +
                $"&status={Uri.EscapeDataString(StatusFilter ?? string.Empty)}" +
                $"&priority={Uri.EscapeDataString(PriorityFilter ?? string.Empty)}" +
                $"&equipmentId={Fmt(EquipmentFilter)}&crewId={Fmt(CrewFilter)}" +
                $"&sort={Uri.EscapeDataString(SortField)}&order={SortOrder}" +
                $"&page={Page}&pageSize={PageSize}";

            var result = await Api!.GetAsync<PagedResult<WorkOrderRow>>(path, ct);

            if (!result.Success || result.Data is null)
            {
                ErrorText = result.Message;
                OnPropertyChanged(nameof(ErrorText));
                Toasts!.Warn(result.Message);
                return;
            }

            Rows.Clear();
            foreach (var row in result.Data.Items)
            {
                Rows.Add(row);
            }

            Total = result.Data.Total;
            OnPropertyChanged(nameof(TotalPages));
            OnPropertyChanged(nameof(CanGoNext));
            OnPropertyChanged(nameof(CanGoPrevious));
            OnPropertyChanged(nameof(PageCaption));

            await LoadLookupsAsync(ct);
        });
    }

    /// <summary>
    /// Справочники для выпадающих списков. Грузятся один раз при входе
    /// на экран: мастер выбирает бригаду и материал много раз подряд,
    /// и каждый раз дёргать сервер незачем.
    /// </summary>
    private async Task LoadLookupsAsync(CancellationToken ct)
    {
        var crews = await Api!.GetAsync<List<CrewShort>>("/api/crews/select", ct);
        if (crews.Success && crews.Data is not null)
        {
            Crews.Clear();
            foreach (var c in crews.Data)
            {
                Crews.Add(c);
            }
        }

        var equipment = await Api.GetAsync<List<EquipmentShort>>("/api/equipment/select", ct);
        if (equipment.Success && equipment.Data is not null)
        {
            Equipment.Clear();
            foreach (var e in equipment.Data)
            {
                Equipment.Add(e);
            }
        }
    }

    [RelayCommand]
    private void Select(WorkOrderRow? row)
    {
        Selected = row;
        if (row is not null)
        {
            AssignCrew = null;
            FailureReason = string.Empty;
            WriteOffQuantity = 0m;
        }
    }

    [RelayCommand]
    private async Task CreateAsync()
    {
        if (DraftEquipment is null)
        {
            Toasts!.Warn("Выберите оборудование.");
            return;
        }

        await RunLoadAsync("Создаём заявку…", async ct =>
        {
            var result = await Api!.PostAsync<WorkOrderRow>(
                "/api/work-orders",
                new
                {
                    equipmentId = DraftEquipment.Id,
                    title = DraftTitle,
                    description = DraftDescription,
                    priority = DraftPriority,
                    plannedStart = Fmt(DraftPlannedStart),
                    plannedEnd = Fmt(DraftPlannedEnd),
                    crewId = DraftCrew?.Id,
                },
                ct);

            if (!result.Success || result.Data is null)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success($"Создана заявка {result.Data.Number}.");
            DraftTitle = string.Empty;
            DraftDescription = string.Empty;
            await RefreshAsync();
        });
    }

    [RelayCommand]
    private async Task AssignCrewAsync()
    {
        if (Selected is null || AssignCrew is null)
        {
            Toasts!.Warn("Выберите заявку и бригаду.");
            return;
        }

        await RunLoadAsync("Назначаем бригаду…", async ct =>
        {
            var result = await Api!.PostAsync<object>(
                $"/api/work-orders/{Selected.Id}/crew",
                new { crewId = AssignCrew.Id },
                ct);

            if (!result.Success)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success($"Бригада {AssignCrew.Name} назначена.");
            await RefreshAsync();
        });
    }

    [RelayCommand]
    private async Task StartAsync()
    {
        if (Selected is null)
        {
            return;
        }

        await RunLoadAsync("Начинаем работу…", async ct =>
        {
            var result = await Api!.PostAsync<object>(
                $"/api/work-orders/{Selected.Id}/start",
                new { actualStart = DateTimeOffset.UtcNow },
                ct);

            if (!result.Success)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success("Заявка переведена в работу.");
            await RefreshAsync();
        });
    }

    /// <summary>
    /// Завершение требует причину неисправности: без неё сервер
    /// отвечает 400, и поле подсвечивается, чтобы мастер не искал
    /// причину ошибки в другом месте.
    /// </summary>
    [RelayCommand]
    private async Task CompleteAsync()
    {
        if (Selected is null)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(FailureReason))
        {
            Toasts!.Error("Укажите причину неисправности — без неё заявку завершить нельзя.");
            return;
        }

        await RunLoadAsync("Завершаем заявку…", async ct =>
        {
            var result = await Api!.PostAsync<object>(
                $"/api/work-orders/{Selected.Id}/complete",
                new
                {
                    actualEnd = DateTimeOffset.UtcNow,
                    failureReason = FailureReason,
                },
                ct);

            if (!result.Success)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success("Заявка завершена, простой посчитан сервером.");
            await RefreshAsync();
        });
    }

    /// <summary>Списание материала. Клиент шлёт количество, стоимость считает база.</summary>
    [RelayCommand]
    private async Task WriteOffAsync()
    {
        if (Selected is null || WriteOffMaterial is null)
        {
            Toasts!.Warn("Выберите заявку и материал.");
            return;
        }

        if (WriteOffQuantity <= 0m)
        {
            Toasts!.Warn("Количество должно быть больше нуля.");
            return;
        }

        await RunLoadAsync("Списываем материал…", async ct =>
        {
            var result = await Api!.PostAsync<object>(
                $"/api/work-orders/{Selected.Id}/materials",
                new { materialId = WriteOffMaterial.Value, quantity = WriteOffQuantity },
                ct);

            if (!result.Success)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success("Материал списан, остаток на складе уменьшен.");
            WriteOffQuantity = 0m;
            await RefreshAsync();
        });
    }

    private static string Fmt(Guid? value) => value?.ToString() ?? string.Empty;

    private static string Fmt(DateOnly? value) =>
        value is null ? string.Empty : value.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
}
