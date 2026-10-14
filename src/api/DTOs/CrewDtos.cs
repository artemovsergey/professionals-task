using System.ComponentModel.DataAnnotations;

namespace ToirProf.Api.DTOs;

// ===========================================================================
//  Бригады
// ===========================================================================

public sealed record CrewMemberDto(Guid UserId, string Username, string FullName, DateOnly JoinedAt);

public sealed record CrewShortDto(Guid Id, string Code, string Name, bool IsActive, int MemberCount);

public sealed record CrewDto(
    Guid Id,
    string Code,
    string Name,
    string? Specialty,
    bool IsActive,
    IReadOnlyList<CrewMemberDto> Members,
    int ActiveOrders,
    int CompletedOrders,
    decimal? TotalDowntimeHours,
    decimal? Rating)
{
    /// <summary>
    /// Рейтинг бригады по доле выполненных заявок в срок, умноженной на 100.
    /// Считается в SQL, здесь только округляется — иначе деление
    /// целочисленное отдаёт 0 вместо, например, 87,5.
    /// </summary>
    public decimal? EfficiencyPercent => Rating;
}

public sealed class CreateCrewDto
{
    [Required(ErrorMessage = "Укажите код бригады")]
    [StringLength(20, MinimumLength = 1)]
    public string Code { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите название бригады")]
    [StringLength(200, MinimumLength = 1)]
    public string Name { get; set; } = string.Empty;

    [StringLength(500)]
    public string? Specialty { get; set; }

    public bool IsActive { get; set; } = true;
}

public sealed class UpdateCrewDto
{
    [StringLength(200, MinimumLength = 1)]
    public string? Name { get; set; }

    [StringLength(500)]
    public string? Specialty { get; set; }

    public bool? IsActive { get; set; }
}

public sealed class AddCrewMemberDto
{
    [Required(ErrorMessage = "Выберите пользователя")]
    public Guid UserId { get; set; }
}

// ===========================================================================
//  Материалы и ЗИП
// ===========================================================================

public sealed record MaterialDto(
    Guid Id,
    string Sku,
    string Name,
    string Unit,
    decimal Price,
    decimal Stock,
    decimal MinStock,
    string? Location,
    bool IsActive,
    decimal? TotalWrittenOff)
{
    /// <summary>
    /// Дефицитный материал: остаток ниже минимального.
    /// На экране справочника такие строки подсвечиваются красным.
    /// </summary>
    public bool IsShortage => Stock < MinStock;
}

public sealed class CreateMaterialDto
{
    [Required(ErrorMessage = "Укажите артикул")]
    [StringLength(50, MinimumLength = 1)]
    public string Sku { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите название материала")]
    [StringLength(200, MinimumLength = 1)]
    public string Name { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите единицу измерения")]
    [StringLength(10, MinimumLength = 1)]
    public string Unit { get; set; } = string.Empty;

    [Range(0, double.MaxValue, ErrorMessage = "Цена не может быть отрицательной")]
    public decimal Price { get; set; }

    [Range(0, double.MaxValue, ErrorMessage = "Остаток не может быть отрицательным")]
    public decimal Stock { get; set; }

    [Range(0, double.MaxValue, ErrorMessage = "Минимальный остаток не может быть отрицательным")]
    public decimal MinStock { get; set; }

    [StringLength(200)]
    public string? Location { get; set; }
}

public sealed class UpdateMaterialDto
{
    [StringLength(200, MinimumLength = 1)]
    public string? Name { get; set; }

    [StringLength(10)]
    public string? Unit { get; set; }

    [Range(0, double.MaxValue)]
    public decimal? Price { get; set; }

    [Range(0, double.MaxValue)]
    public decimal? MinStock { get; set; }

    [StringLength(200)]
    public string? Location { get; set; }

    public bool? IsActive { get; set; }
}

public sealed record MaterialShortageDto(Guid Id, string Sku, string Name, decimal Stock, decimal MinStock, string Unit);

/// <summary>
/// Приход на склад. Остаток меняется только положительным числом:
/// уход со склада делается списанием в заявку, иначе остатки
/// расходятся с журналом операций.
/// </summary>
public sealed class StockReceiptDto
{
    [Range(0.001, double.MaxValue, ErrorMessage = "Количество должно быть больше нуля")]
    public decimal Quantity { get; set; }
}

// ===========================================================================
//  Дашборд и аналитика
// ===========================================================================

public sealed record DashboardSummary(
    int TotalOrders,
    int InProgress,
    int Completed,
    decimal AverageDowntimeHours,
    decimal EmergencyShare,
    decimal MaintenancePlanShare,
    decimal TotalMaterialCost,
    IReadOnlyList<WorkshopSlice> ByWorkshop,
    IReadOnlyList<StatusSlice> ByStatus,
    IReadOnlyList<MonthSlice> ByMonth,
    DateOnly PeriodFrom,
    DateOnly PeriodTo);

public sealed record WorkshopSlice(
    Guid WorkshopId,
    string Name,
    int Total,
    int Completed,
    decimal DowntimeHours,
    decimal AverageDowntimeHours);

public sealed record StatusSlice(string Status, int Count);

public sealed record MonthSlice(int Year, int Month, string Label, int Count, decimal DowntimeHours);

public sealed record DowntimeSlice(
    Guid EquipmentId,
    string InventoryNumber,
    string Name,
    string WorkshopName,
    int OrdersCount,
    decimal TotalDowntimeHours,
    decimal SharePercent);

public sealed record CrewEfficiency(
    Guid CrewId,
    string Code,
    string Name,
    int Assigned,
    int Completed,
    int InTime,
    decimal AverageDowntimeHours,
    decimal TotalMaterialCost,
    decimal Rating);

public sealed record MaterialUsage(
    Guid MaterialId,
    string Sku,
    string Name,
    string Unit,
    decimal Quantity,
    decimal Cost,
    int OrdersCount);

public sealed record PlanExecutionSlice(
    string Status,
    int Count,
    decimal Percent);

public sealed record AnalyticsReport(
    DateOnly PeriodFrom,
    DateOnly PeriodTo,
    IReadOnlyList<DowntimeSlice> Downtime,
    IReadOnlyList<CrewEfficiency> Crews,
    IReadOnlyList<MaterialUsage> Materials,
    IReadOnlyList<PlanExecutionSlice> Plan,
    OrdersSummary Orders);

public sealed record OrdersSummary(
    int Total,
    int Completed,
    int InProgress,
    int Cancelled,
    decimal CompletionShare,
    decimal EmergencyShare,
    decimal AverageDowntimeHours);

/// <summary>
/// Событие дашборда для Server-Sent Events.
/// Payload — тот же DashboardSummary, что отдаёт GET, поэтому клиент
/// обновляет экран без пересчётов на своей стороне.
/// </summary>
public sealed record DashboardEvent(string Type, DateTimeOffset At, DashboardSummary Data)
{
    public const string UpdatedType = "dashboard.updated";

    public const string PingType = "dashboard.ping";
}

// ===========================================================================
//  Отчёты и пользователи
// ===========================================================================

public static class ReportKinds
{
    public const string Downtime = "downtime";

    public const string Crews = "crews";

    public const string Materials = "materials";

    public const string Plan = "plan";
}

public sealed class CreateReportDto
{
    [Required(ErrorMessage = "Укажите тип отчёта")]
    public string Kind { get; set; } = ReportKinds.Downtime;

    public DateOnly? From { get; set; }

    public DateOnly? To { get; set; }

    public Guid? WorkshopId { get; set; }
}

/// <summary>
/// Временная ссылка на отчёт. Токен живёт 15 секунд — это требование
/// задания: за это время эксперт успевает открыть файл, но ссылка
/// не остаётся в истории браузера рабочей надолго.
/// </summary>
public sealed record ReportLink(string Token, string Url, DateTimeOffset ExpiresAt, int TtlSeconds)
{
    public const int TtlSecondsValue = 15;
}

public sealed record UserDto(
    Guid Id,
    string Username,
    string FullName,
    string Role,
    bool IsActive,
    IReadOnlyList<string> Crews,
    DateTime CreatedAt);

public sealed class RegisterDto
{
    [Required(ErrorMessage = "Укажите имя пользователя")]
    [StringLength(50, MinimumLength = 3)]
    [RegularExpression("^[a-zA-Z0-9_.-]+$",
        ErrorMessage = "Логин: латиница, цифры и символы _ . -")]
    public string Username { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите пароль")]
    [StringLength(100, MinimumLength = 8, ErrorMessage = "Пароль — минимум 8 символов")]
    public string Password { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите ФИО")]
    [StringLength(200, MinimumLength = 3)]
    public string FullName { get; set; } = string.Empty;

    [StringLength(10)]
    public string? Role { get; set; }
}

public sealed class LoginDto
{
    [Required(ErrorMessage = "Укажите имя пользователя")]
    public string Username { get; set; } = string.Empty;

    [Required(ErrorMessage = "Укажите пароль")]
    public string Password { get; set; } = string.Empty;
}

public sealed record TokenResponse(
    string Token,
    string TokenType,
    int ExpiresIn,
    UserDto User)
{
    public const string Bearer = "Bearer";

    /// <summary>Срок жизни токена — 8 часов, как в листе требований.</summary>
    public const int LifetimeSeconds = 8 * 60 * 60;
}