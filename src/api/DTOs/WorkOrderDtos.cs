using System.ComponentModel.DataAnnotations;

namespace ToirProf.Api.DTOs;

// ===========================================================================
//  Заявки на ремонт и ТО
// ===========================================================================

public sealed record WorkOrderShortDto(
    Guid Id,
    string Number,
    Guid EquipmentId,
    string EquipmentName,
    string InventoryNumber,
    string Priority,
    string Status,
    DateOnly? PlannedStart,
    DateOnly? PlannedEnd,
    decimal? DowntimeHours,
    string? CrewName);

public sealed record WorkOrderMaterialDto(
    Guid MaterialId,
    string Sku,
    string Name,
    string Unit,
    decimal Quantity,
    decimal UnitPrice,
    decimal Cost);

public sealed record WorkOrderHistoryDto(
    DateTime ChangedAt,
    string? ChangedByName,
    string Action,
    string Summary);

public sealed record WorkOrderDto(
    Guid Id,
    string Number,
    Guid EquipmentId,
    string EquipmentName,
    string InventoryNumber,
    string WorkshopName,
    Guid? MaintenanceTypeId,
    string? MaintenanceTypeName,
    Guid? CrewId,
    string? CrewName,
    Guid? AssignedTo,
    string? AssignedToName,
    string Title,
    string Description,
    string Priority,
    string Status,
    DateOnly? PlannedStart,
    DateOnly? PlannedEnd,
    DateTimeOffset? ActualStart,
    DateTimeOffset? ActualEnd,
    decimal? DowntimeHours,
    string? FailureReason,
    DateTimeOffset? CompletedAt,
    DateOnly CreatedOn,
    decimal TotalMaterialCost,
    IReadOnlyList<WorkOrderMaterialDto> Materials,
    IReadOnlyList<WorkOrderHistoryDto> History)
{
    /// <summary>
    /// Простой считает триггер trg_work_order_dates_check. Пока работа
    /// не завершена, поле пустое — показывать в интерфейсе прочерк,
    /// а не ноль, иначе «0 ч» читается как «стоял и не работал».
    /// </summary>
    public bool HasDowntime => DowntimeHours.HasValue;
}

public static class WorkOrderStatuses
{
    public const string Draft = "Черновик";

    public const string Assigned = "Назначена";

    public const string InProgress = "В работе";

    public const string Completed = "Завершена";

    public const string Cancelled = "Отменена";

    /// <summary>
    /// Разрешённые переходы статусов. Завершённая и отменённая заявки
    /// закрываются навсегда — иначе простои и суммы в отчётах менялись бы
    /// задним числом.
    ///
    /// Ключ — текущий статус, значение — куда можно перейти.
    /// </summary>
    public static readonly IReadOnlyDictionary<string, IReadOnlyList<string>> Transitions =
        new Dictionary<string, IReadOnlyList<string>>
        {
            [Draft] = [Assigned, InProgress, Cancelled],
            [Assigned] = [InProgress, Draft, Cancelled],
            [InProgress] = [Completed, Assigned, Cancelled],
            [Completed] = [],
            [Cancelled] = []
        };

    public static bool CanTransition(string from, string to)
        => Transitions.TryGetValue(from, out var allowed) && allowed.Contains(to);

    /// <summary>
    /// Все статусы через запятую — подставляется в текст ошибки, когда
    /// пришло неизвестное значение. Список берётся отсюда же, поэтому
    /// новое значение нельзя забыть внести в текст.
    /// </summary>
    public const string AllText = $"{Draft}, {Assigned}, {InProgress}, {Completed}, {Cancelled}";
}

public static class WorkOrderPriorities
{
    public const string Low = "Низкий";

    public const string Medium = "Средний";

    public const string High = "Высокий";

    public const string Emergency = "Аварийный";

    /// <summary>
    /// Все приоритеты через запятую — для текста ошибки валидации.
    /// </summary>
    public const string AllText = $"{Low}, {Medium}, {High}, {Emergency}";
}

public sealed class CreateWorkOrderDto
{
    [Required(ErrorMessage = "Укажите оборудование")]
    public Guid EquipmentId { get; set; }

    public Guid? MaintenanceTypeId { get; set; }

    public Guid? ScheduleId { get; set; }

    [Required(ErrorMessage = "Укажите заголовок заявки")]
    [StringLength(200, MinimumLength = 1)]
    public string Title { get; set; } = string.Empty;

    [Required(ErrorMessage = "Опишите неисправность")]
    [StringLength(2000, MinimumLength = 1)]
    public string Description { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите приоритет")]
    public string Priority { get; set; } = WorkOrderPriorities.Medium;

    public DateOnly? PlannedStart { get; set; }

    public DateOnly? PlannedEnd { get; set; }

    public Guid? CrewId { get; set; }
}

public sealed class UpdateWorkOrderDto
{
    [StringLength(200, MinimumLength = 1)]
    public string? Title { get; set; }

    [StringLength(2000)]
    public string? Description { get; set; }

    public string? Priority { get; set; }

    public DateOnly? PlannedStart { get; set; }

    public DateOnly? PlannedEnd { get; set; }

    public string? FailureReason { get; set; }
}

public sealed class AssignCrewDto
{
    [Required(ErrorMessage = "Выберите бригаду")]
    public Guid CrewId { get; set; }

    public Guid? AssignedTo { get; set; }
}

public sealed class StartWorkOrderDto
{
    [Required(ErrorMessage = "Укажите фактическое время начала работ")]
    public DateTimeOffset ActualStart { get; set; }
}

public sealed class CompleteWorkOrderDto
{
    [Required(ErrorMessage = "Укажите фактическое время окончания работ")]
    public DateTimeOffset ActualEnd { get; set; }

    [Required(ErrorMessage = "Укажите причину неисправности")]
    [StringLength(1000, MinimumLength = 1)]
    public string FailureReason { get; set; } = string.Empty;

    [StringLength(1000)]
    public string? Comment { get; set; }
}

public sealed class ChangeStatusDto
{
    [Required(ErrorMessage = "Укажите новый статус")]
    public string Status { get; set; } = string.Empty;

    [StringLength(1000)]
    public string? Reason { get; set; }
}

public sealed class MaterialWriteOffDto
{
    [Required(ErrorMessage = "Выберите материал")]
    public Guid MaterialId { get; set; }

    [Range(0.001, double.MaxValue, ErrorMessage = "Количество должно быть больше нуля")]
    public decimal Quantity { get; set; }
}

public sealed record MaterialCostDto(Guid WorkOrderId, decimal TotalCost, int Positions);

public sealed record WorkOrderFilter(
    Guid? EquipmentId,
    Guid? CrewId,
    string? Status,
    string? Priority,
    DateOnly? From,
    DateOnly? To,
    string? Query,
    string Sort = "createdAt",
    string Order = "desc",
    int Page = 1,
    int PageSize = 20)
{
    public int NormalizedPage => Page < 1 ? 1 : Page;

    public int NormalizedPageSize => PageSize switch
    {
        < 1 => 20,
        > 100 => 100,
        _ => PageSize
    };
}