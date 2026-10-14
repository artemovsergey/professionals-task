using System;
using System.Collections.Generic;

namespace ToirProf.Desktop.Models;

// Модели клиента — копия контрактов API в том виде, в каком их видит
// desktop. Проект api намеренно не подключён: если завтра сервер
// переедет на другой адрес или в другую сборку, клиент не должен
// пересобираться вместе с ним. Достаточно совпадения имён полей —
// JSON сериализуется в camelCase, а System.Text.Json читает так же.

public sealed class PagedResult<T>
{
    public List<T> Items { get; set; } = [];

    public int Total { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }

    public int TotalPages => PageSize <= 0 ? 0 : (int)Math.Ceiling(Total / (double)PageSize);
}

public sealed class EquipmentShort
{
    public Guid Id { get; set; }

    public string InventoryNumber { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public Guid WorkshopId { get; set; }

    public string WorkshopName { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public int Criticality { get; set; }
}

public sealed class EquipmentCard
{
    public Guid Id { get; set; }

    public string InventoryNumber { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public Guid WorkshopId { get; set; }

    public string WorkshopName { get; set; } = string.Empty;

    public string? Manufacturer { get; set; }

    public string? Model { get; set; }

    public string? SerialNumber { get; set; }

    public DateOnly CommissionDate { get; set; }

    public DateOnly? DecommissionDate { get; set; }

    public string Status { get; set; } = string.Empty;

    public int Criticality { get; set; }

    public string? Location { get; set; }

    public string? Notes { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }

    public bool IsDecommissioned { get; set; }

    /// <summary>
    /// Ключевой показатель для мастера: единица 5-й критичности
    /// встаёт дороже всего. Показываем его прямо в строке списка.
    /// </summary>
    public string CriticalityCaption => Criticality >= 5 ? "критическая" : $"критичность {Criticality}";
}

public sealed class MaintenanceTypeRow
{
    public Guid Id { get; set; }

    public string Code { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public int IntervalDays { get; set; }

    public string? Description { get; set; }

    public bool IsActive { get; set; }

    public int UsageCount { get; set; }
}

public sealed class ScheduleRow
{
    public Guid Id { get; set; }

    public Guid EquipmentId { get; set; }

    public string EquipmentName { get; set; } = string.Empty;

    public string InventoryNumber { get; set; } = string.Empty;

    public Guid MaintenanceTypeId { get; set; }

    public string MaintenanceTypeName { get; set; } = string.Empty;

    public int IntervalDays { get; set; }

    public DateOnly PlannedDate { get; set; }

    public DateOnly? CompletedDate { get; set; }

    public DateOnly? NextPlannedDate { get; set; }

    public string Status { get; set; } = string.Empty;

    public decimal? ActualCost { get; set; }

    public string? Notes { get; set; }

    /// <summary>
    /// Статус хранится в базе строкой, а не перечислением, и правится
    /// триггером при наступлении даты. Подсветка в клиенте — единственное
    /// место, где цвет различается, поэтому она собрана в одном методе.
    /// </summary>
    public string StatusBrush => Status switch
    {
        "Выполнено" => "ok",
        "Просрочено" => "bad",
        _ => "wait",
    };
}

public sealed class WorkOrderRow
{
    public Guid Id { get; set; }

    public string Number { get; set; } = string.Empty;

    public Guid EquipmentId { get; set; }

    public string EquipmentName { get; set; } = string.Empty;

    public string InventoryNumber { get; set; } = string.Empty;

    public string Priority { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public DateOnly? PlannedStart { get; set; }

    public DateOnly? PlannedEnd { get; set; }

    public decimal? DowntimeHours { get; set; }

    public string? CrewName { get; set; }

    public string PriorityBrush => Priority switch
    {
        "Аварийный" => "bad",
        "Высокий" => "warn",
        _ => "wait",
    };
}

public sealed class CrewRow
{
    public Guid Id { get; set; }

    public string Code { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public int MemberCount { get; set; }

    public int ActiveOrders { get; set; }

    public int CompletedOrders { get; set; }

    public decimal TotalDowntimeHours { get; set; }

    public decimal Rating { get; set; }
}

public sealed class CrewShort
{
    public Guid Id { get; set; }

    public string Code { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public int MemberCount { get; set; }
}

public sealed class MaterialRow
{
    public Guid Id { get; set; }

    public string Sku { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Unit { get; set; } = string.Empty;

    public decimal Price { get; set; }

    public decimal Stock { get; set; }

    public decimal MinStock { get; set; }

    public string? Location { get; set; }

    public bool IsActive { get; set; }

    public decimal TotalWrittenOff { get; set; }

    public bool IsShortage { get; set; }

    public string StockCaption => $"{Stock:0.##} {Unit}";
}

public sealed class WorkshopSlice
{
    public Guid WorkshopId { get; set; }

    public string Name { get; set; } = string.Empty;

    public int Total { get; set; }

    public int Completed { get; set; }

    public decimal DowntimeHours { get; set; }

    public decimal AverageDowntimeHours { get; set; }
}

public sealed class StatusSlice
{
    public string Status { get; set; } = string.Empty;

    public int Count { get; set; }
}

public sealed class MonthSlice
{
    public int Year { get; set; }

    public int Month { get; set; }

    public string Label { get; set; } = string.Empty;

    public int Count { get; set; }

    public decimal DowntimeHours { get; set; }
}

public sealed class DashboardSummary
{
    public int TotalOrders { get; set; }

    public int InProgress { get; set; }

    public int Completed { get; set; }

    public decimal AverageDowntimeHours { get; set; }

    public decimal EmergencyShare { get; set; }

    public decimal MaintenancePlanShare { get; set; }

    public decimal TotalMaterialCost { get; set; }

    public List<WorkshopSlice> ByWorkshop { get; set; } = [];

    public List<StatusSlice> ByStatus { get; set; } = [];

    public List<MonthSlice> ByMonth { get; set; } = [];

    public DateOnly PeriodFrom { get; set; }

    public DateOnly PeriodTo { get; set; }
}

public sealed class DowntimeSlice
{
    public Guid EquipmentId { get; set; }

    public string InventoryNumber { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string WorkshopName { get; set; } = string.Empty;

    public int OrdersCount { get; set; }

    public decimal TotalDowntimeHours { get; set; }

    public decimal SharePercent { get; set; }
}

public sealed class CrewEfficiency
{
    public Guid CrewId { get; set; }

    public string Code { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public int Assigned { get; set; }

    public int Completed { get; set; }

    public int InTime { get; set; }

    public decimal AverageDowntimeHours { get; set; }

    public decimal TotalMaterialCost { get; set; }

    public decimal Rating { get; set; }
}

public sealed class PlanExecutionSlice
{
    public string Status { get; set; } = string.Empty;

    public int Count { get; set; }

    public decimal Percent { get; set; }
}

public sealed class AnalyticsReport
{
    public DateOnly PeriodFrom { get; set; }

    public DateOnly PeriodTo { get; set; }

    public List<DowntimeSlice> Downtime { get; set; } = [];

    public List<CrewEfficiency> Crews { get; set; } = [];

    public List<MaterialUsage> Materials { get; set; } = [];

    public List<PlanExecutionSlice> Plan { get; set; } = [];

    public OrdersSummary Orders { get; set; } = new();
}

public sealed class MaterialUsage
{
    public Guid MaterialId { get; set; }

    public string Sku { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Unit { get; set; } = string.Empty;

    public decimal Quantity { get; set; }

    public decimal Cost { get; set; }

    public int OrdersCount { get; set; }
}

public sealed class OrdersSummary
{
    public int Total { get; set; }

    public int Completed { get; set; }

    public int InProgress { get; set; }

    public int Cancelled { get; set; }

    public decimal CompletionShare { get; set; }

    public decimal EmergencyShare { get; set; }

    public decimal AverageDowntimeHours { get; set; }
}

public sealed class ReportLink
{
    public string Token { get; set; } = string.Empty;

    public string Url { get; set; } = string.Empty;

    public DateTimeOffset ExpiresAt { get; set; }

    public int TtlSeconds { get; set; }
}
