using System.ComponentModel.DataAnnotations;

namespace ToirProf.Api.DTOs;

// ===========================================================================
//  Общие части
// ===========================================================================

/// <summary>
/// Постраничная выдача. Клиент рисует таблицу и по этим полям
/// строит кнопки «вперёд» и «назад», поэтому total всегда нужна:
/// без неё неизвестно, сколько страниц осталось.
/// </summary>
public sealed record PagedResult<T>(IReadOnlyList<T> Items, int Total, int Page, int PageSize)
{
    public int TotalPages => PageSize <= 0 ? 0 : (int)Math.Ceiling(Total / (double)PageSize);
}

/// <summary>
/// Период отчёта. По умолчанию — последние 30 дней: пустой фильтр
/// не должен приводить к отчёту за все годы с нулевым простоем.
/// </summary>
public sealed record DateRange(DateOnly? From, DateOnly? To)
{
    public DateOnly Start => From ?? DateOnly.FromDateTime(DateTime.Today.AddDays(-30));

    public DateOnly End => To ?? DateOnly.FromDateTime(DateTime.Today);

    /// <summary>
    /// Начало периода в UTC. Колонки created_at описаны как timestamptz,
    /// а Npgsql принимает только DateTime с Kind = Utc: без явного вида
    /// он выбрасывает «Cannot write DateTime with Kind=Unspecified».
    /// </summary>
    public DateTime StartUtc => Start.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);

    /// <summary>Последний момент периода в UTC — конец дня включительно.</summary>
    public DateTime EndUtc => End.ToDateTime(TimeOnly.MaxValue, DateTimeKind.Utc);
}

// ===========================================================================
//  Оборудование
// ===========================================================================

public sealed record EquipmentShortDto(
    Guid Id,
    string InventoryNumber,
    string Name,
    Guid WorkshopId,
    string WorkshopName,
    string Status,
    int Criticality);

public sealed record EquipmentDto(
    Guid Id,
    string InventoryNumber,
    string Name,
    Guid WorkshopId,
    string WorkshopName,
    string? Manufacturer,
    string? Model,
    string? SerialNumber,
    DateOnly CommissionDate,
    DateOnly? DecommissionDate,
    string Status,
    int Criticality,
    string? Location,
    string? Notes,
    DateTime CreatedAt,
    DateTime UpdatedAt)
{
    public bool IsDecommissioned => Status == EquipmentStatuses.Retired;
}

/// <summary>
/// Значения статуса оборудования дублируют ENUM equipment_status из базы.
/// Здесь они в виде строк — клиенту не нужен числовой код.
/// </summary>
public static class EquipmentStatuses
{
    public const string Running = "Работает";

    public const string InRepair = "В ремонте";

    public const string Retired = "Выведено из эксплуатации";
}

public sealed class CreateEquipmentDto
{
    [Required(ErrorMessage = "Укажите инвентарный номер")]
    [StringLength(50, MinimumLength = 1)]
    public string InventoryNumber { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите название оборудования")]
    [StringLength(200, MinimumLength = 1)]
    public string Name { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите цех")]
    public Guid WorkshopId { get; set; }

    [StringLength(150)]
    public string? Manufacturer { get; set; }

    [StringLength(100)]
    public string? Model { get; set; }

    [StringLength(100)]
    public string? SerialNumber { get; set; }

    [Required(ErrorMessage = "Укажите дату ввода в эксплуатацию")]
    public DateOnly CommissionDate { get; set; }

    public DateOnly? DecommissionDate { get; set; }

    [Required(ErrorMessage = "Укажите статус оборудования")]
    public string Status { get; set; } = EquipmentStatuses.Running;

    [Range(1, 5, ErrorMessage = "Критичность — от 1 до 5")]
    public int Criticality { get; set; } = 3;

    [StringLength(200)]
    public string? Location { get; set; }

    [StringLength(1000)]
    public string? Notes { get; set; }
}

public sealed class UpdateEquipmentDto
{
    [StringLength(200, MinimumLength = 1)]
    public string? Name { get; set; }

    public Guid? WorkshopId { get; set; }

    [StringLength(150)]
    public string? Manufacturer { get; set; }

    [StringLength(100)]
    public string? Model { get; set; }

    [StringLength(100)]
    public string? SerialNumber { get; set; }

    [StringLength(200)]
    public string? Location { get; set; }

    [StringLength(1000)]
    public string? Notes { get; set; }

    /// <summary>
    /// Статус меняется отдельным эндпоинтом, а не через PATCH:
    /// у выведенного из эксплуатации оборудования статус менять
    /// запрещает триггер trg_equipment_status_guard, и клиенту
    /// нужно знать об этом заранее, до отправки формы.
    /// </summary>
    public string? Status { get; set; }

    [Range(1, 5)]
    public int? Criticality { get; set; }
}

// ===========================================================================
//  Справочник видов обслуживания
// ===========================================================================

public sealed record MaintenanceTypeDto(
    Guid Id,
    string Code,
    string Name,
    int IntervalDays,
    string? Description,
    bool IsActive,
    int UsageCount);

public sealed class CreateMaintenanceTypeDto
{
    [Required(ErrorMessage = "Укажите код вида обслуживания")]
    [StringLength(20, MinimumLength = 1)]
    public string Code { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите название")]
    [StringLength(200, MinimumLength = 1)]
    public string Name { get; set; } = string.Empty;

    [Range(1, 3650, ErrorMessage = "Периодичность — от 1 до 3650 дней")]
    public int IntervalDays { get; set; } = 30;

    [StringLength(500)]
    public string? Description { get; set; }
}

public sealed class UpdateMaintenanceTypeDto
{
    [StringLength(200, MinimumLength = 1)]
    public string? Name { get; set; }

    [Range(1, 3650)]
    public int? IntervalDays { get; set; }

    [StringLength(500)]
    public string? Description { get; set; }

    public bool? IsActive { get; set; }
}

// ===========================================================================
//  График планового ТО
// ===========================================================================

public sealed record MaintenanceScheduleDto(
    Guid Id,
    Guid EquipmentId,
    string EquipmentName,
    string InventoryNumber,
    Guid MaintenanceTypeId,
    string MaintenanceTypeName,
    int IntervalDays,
    DateOnly PlannedDate,
    DateOnly? CompletedDate,
    DateOnly? NextPlannedDate,
    string Status,
    decimal? ActualCost,
    string? Notes);

public sealed class CreateMaintenanceScheduleDto
{
    [Required]
    public Guid EquipmentId { get; set; }

    [Required]
    public Guid MaintenanceTypeId { get; set; }

    [Required(ErrorMessage = "Укажите плановую дату")]
    public DateOnly PlannedDate { get; set; }

    [StringLength(500)]
    public string? Notes { get; set; }
}

public sealed class CompleteMaintenanceScheduleDto
{
    [Required(ErrorMessage = "Укажите дату выполнения")]
    public DateOnly CompletedDate { get; set; }

    [Range(0, double.MaxValue, ErrorMessage = "Стоимость не может быть отрицательной")]
    public decimal? ActualCost { get; set; }
}