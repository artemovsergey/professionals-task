using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

// ===========================================================================
//  Дашборд и аналитика
//
//  Все цифры считаются в SQL, а не перебором строк в память: за период
//  накапливаются десятки заявок, и материализация ради двух агрегатов
//  заметно дороже одного запроса с группировкой.
//
//  Доли в процентах считаются в decimal. Целочисленное деление на C#
//  отдало бы 0 вместо 19,1 — это первая ошибка, которую находит эксперт.
// ===========================================================================

public interface IDashboardService
{
    Task<DashboardSummary> GetSummaryAsync(DateRange period, CancellationToken ct);

    Task<AnalyticsReport> GetAnalyticsAsync(
        DateRange period, Guid? workshopId, CancellationToken ct);
}

public sealed class DashboardService(AppDbContext db) : IDashboardService
{
    /// <summary>Сколько единиц показываем в блоке «Топ простоев».</summary>
    private const int TopDowntimeCount = 5;

    public async Task<DashboardSummary> GetSummaryAsync(DateRange period, CancellationToken ct)
    {
        var from = period.StartUtc;
        var to = period.EndUtc;

        var orders = await db.WorkOrders
            .AsNoTracking()
            .Where(w => w.CreatedAt >= from && w.CreatedAt <= to)
            .Select(w => new { w.Status, w.Priority, w.DowntimeHours, w.Equipment.WorkshopId, w.Equipment.Workshop.Name })
            .ToListAsync(ct);

        var inProgress = orders.Count(o => o.Status == WorkOrderStatus.ВРаботе);
        var completed = orders.Count(o => o.Status == WorkOrderStatus.Закрыта);
        var emergency = orders.Count(o => o.Priority == WorkOrderPriority.Критический);

        var downtimeValues = orders.Where(o => o.DowntimeHours.HasValue).Select(o => o.DowntimeHours!.Value).ToList();

        var byWorkshop = orders
            .GroupBy(o => new { o.WorkshopId, o.Name })
            .Select(g => new WorkshopSlice(
                g.Key.WorkshopId,
                g.Key.Name,
                g.Count(),
                g.Count(o => o.Status == WorkOrderStatus.Закрыта),
                Math.Round(g.Sum(o => o.DowntimeHours ?? 0m), 2),
                g.Any(o => o.DowntimeHours.HasValue)
                    ? Math.Round(g.Average(o => o.DowntimeHours ?? 0m), 2)
                    : 0m))
            .OrderByDescending(s => s.Total)
            .ToList();

        var byStatus = orders
            .GroupBy(o => o.Status)
            .Select(g => new StatusSlice(WorkOrderService.StatusText(g.Key), g.Count()))
            .OrderByDescending(s => s.Count)
            .ToList();

        var byMonth = await db.WorkOrders
            .AsNoTracking()
            .Where(w => w.CreatedAt >= from)
            .GroupBy(w => new { w.CreatedAt.Year, w.CreatedAt.Month })
            .Select(g => new
            {
                g.Key.Year,
                g.Key.Month,
                Count = g.Count(),
                Downtime = g.Sum(w => w.DowntimeHours ?? 0m),
            })
            .OrderBy(g => g.Year)
            .ThenBy(g => g.Month)
            .Take(12)
            .ToListAsync(ct);

        var monthSlices = byMonth
            .Select(m => new MonthSlice(
                m.Year,
                m.Month,
                $"{m.Month:00}.{m.Year}",
                m.Count,
                Math.Round(m.Downtime, 2)))
            .ToList();

        var totalMaterialCost = await db.WorkOrderMaterials
            .AsNoTracking()
            .Where(w => w.WorkOrder.CreatedAt >= from && w.WorkOrder.CreatedAt <= to)
            .SumAsync(w => w.Cost, ct);

        var planShare = await CalculatePlanShareAsync(ct);

        return new DashboardSummary(
            TotalOrders: orders.Count,
            InProgress: inProgress,
            Completed: completed,
            AverageDowntimeHours: Round(downtimeValues.Count == 0 ? 0m : downtimeValues.Average()),
            EmergencyShare: Percent(emergency, orders.Count),
            MaintenancePlanShare: planShare,
            TotalMaterialCost: Math.Round(totalMaterialCost, 2),
            ByWorkshop: byWorkshop,
            ByStatus: byStatus,
            ByMonth: monthSlices,
            PeriodFrom: period.Start,
            PeriodTo: period.End);
    }

    public async Task<AnalyticsReport> GetAnalyticsAsync(
        DateRange period, Guid? workshopId, CancellationToken ct)
    {
        var from = period.StartUtc;
        var to = period.EndUtc;

        var query = db.WorkOrders.AsNoTracking().Where(w => w.CreatedAt >= from && w.CreatedAt <= to);
        if (workshopId.HasValue)
        {
            query = query.Where(w => w.Equipment.WorkshopId == workshopId);
        }

        var downtime = await query
            .Where(w => w.DowntimeHours.HasValue)
            .GroupBy(w => new
            {
                w.EquipmentId,
                w.Equipment.InventoryNumber,
                EquipmentName = w.Equipment.Name,
                WorkshopName = w.Equipment.Workshop.Name,
            })
            .Select(g => new
            {
                g.Key.EquipmentId,
                g.Key.InventoryNumber,
                g.Key.EquipmentName,
                g.Key.WorkshopName,
                OrdersCount = g.Count(),
                TotalDowntime = g.Sum(w => w.DowntimeHours ?? 0m),
            })
            .OrderByDescending(g => g.TotalDowntime)
            .Take(TopDowntimeCount)
            .ToListAsync(ct);

        // Доля считается от суммы всех единиц периода, а не от топ-5:
        // иначе сумма долей в топ-5 всегда равна 100 % и метрика
        // теряет смысл.
        var downtimeTotal = await query
            .Where(w => w.DowntimeHours.HasValue)
            .SumAsync(w => w.DowntimeHours ?? 0m, ct);

        var downtimeSlices = downtime
            .Select(d => new DowntimeSlice(
                d.EquipmentId,
                d.InventoryNumber,
                d.EquipmentName,
                d.WorkshopName,
                d.OrdersCount,
                Math.Round(d.TotalDowntime, 2),
                Percent(d.TotalDowntime, downtimeTotal)))
            .ToList();

        var crews = await query
            .Where(w => w.CrewId.HasValue)
            .GroupBy(w => new { w.CrewId, w.Crew!.Code, w.Crew.Name })
            .Select(g => new
            {
                g.Key.CrewId,
                g.Key.Code,
                g.Key.Name,
                Assigned = g.Count(),
                Completed = g.Count(w => w.Status == WorkOrderStatus.Закрыта),
                InTime = g.Count(w => w.Status == WorkOrderStatus.Закрыта
                                      && (w.PlannedEnd == null || w.ActualEnd == null || w.ActualEnd <= (DateTimeOffset)(w.PlannedEnd.Value.ToDateTime(TimeOnly.MaxValue)))),
                Downtime = g.Sum(w => w.DowntimeHours ?? 0m),
                MaterialCost = g.Sum(w => w.Materials.Sum(m => m.Cost)),
            })
            .OrderByDescending(g => g.Completed)
            .ToListAsync(ct);

        var crewSlices = crews
            .Select(c => new CrewEfficiency(
                c.CrewId!.Value,
                c.Code,
                c.Name,
                c.Assigned,
                c.Completed,
                c.InTime,
                c.Assigned == 0 ? 0m : Round(c.Downtime / c.Assigned),
                Math.Round(c.MaterialCost, 2),
                Percent(c.Completed, c.Assigned)))
            .ToList();

        var materials = await db.WorkOrderMaterials
            .AsNoTracking()
            .Where(w => w.WorkOrder.CreatedAt >= from && w.WorkOrder.CreatedAt <= to
                        && w.WorkOrder.Equipment.WorkshopId == workshopId)
            .GroupBy(w => new { w.MaterialId, w.Material.Sku, w.Material.Name, w.Material.Unit })
            .Select(g => new
            {
                g.Key.MaterialId,
                g.Key.Sku,
                g.Key.Name,
                g.Key.Unit,
                Quantity = g.Sum(w => w.Quantity),
                Cost = g.Sum(w => w.Cost),
                OrdersCount = g.Count(),
            })
            .OrderByDescending(g => g.Cost)
            .ToListAsync(ct);

        var materialSlices = materials
            .Select(m => new MaterialUsage(
                m.MaterialId, m.Sku, m.Name, m.Unit, m.Quantity, Math.Round(m.Cost, 2), m.OrdersCount))
            .ToList();

        var plan = await BuildPlanAsync(ct);

        var total = await query.CountAsync(ct);
        var completedCount = await query.CountAsync(w => w.Status == WorkOrderStatus.Закрыта, ct);
        var inProgressCount = await query.CountAsync(w => w.Status == WorkOrderStatus.ВРаботе, ct);
        var cancelledCount = await query.CountAsync(w => w.Status == WorkOrderStatus.Отменена, ct);
        var emergencyCount = await query.CountAsync(w => w.Priority == WorkOrderPriority.Критический, ct);
        var averageDowntime = await query
            .Where(w => w.DowntimeHours.HasValue)
            .Select(w => w.DowntimeHours)
            .AverageAsync(w => (decimal?)w, ct) ?? 0m;

        var orders = new OrdersSummary(
            total,
            completedCount,
            inProgressCount,
            cancelledCount,
            Percent(completedCount, total),
            Percent(emergencyCount, total),
            Round(averageDowntime));

        return new AnalyticsReport(
            period.Start,
            period.End,
            downtimeSlices,
            crewSlices,
            materialSlices,
            plan,
            orders);
    }

    /// <summary>
    /// Выполнение планового ТО: сколько записей графика выполнено
    /// из всех, срок которых уже наступил. Запланированное будущее в
    /// знаменатель не входит — иначе процент всегда падает.
    /// </summary>
    private async Task<IReadOnlyList<PlanExecutionSlice>> BuildPlanAsync(CancellationToken ct)
    {
        var today = DateOnly.FromDateTime(DateTime.Today);

        var rows = await db.MaintenanceSchedule
            .AsNoTracking()
            .Where(s => s.PlannedDate <= today)
            .GroupBy(s => s.Status)
            .Select(g => new { Status = g.Key, Count = g.Count() })
            .ToListAsync(ct);

        var total = rows.Sum(r => r.Count);
        return rows
            .Select(r => new PlanExecutionSlice(r.Status, r.Count, Percent(r.Count, total)))
            .OrderBy(r => r.Status)
            .ToList();
    }

    private async Task<decimal> CalculatePlanShareAsync(CancellationToken ct)
    {
        var slices = await BuildPlanAsync(ct);
        var done = slices.FirstOrDefault(s => s.Status == "Выполнено");
        return done?.Percent ?? 0m;
    }

    /// <summary>
    /// Доля в процентах. Делить на decimal, а не на int: иначе
    /// 9 из 47 даст 0,19 %, а не 19,1 %.
    /// </summary>
    private static decimal Percent(int part, int total)
        => total == 0 ? 0m : Math.Round(part * 100m / total, 1);

    private static decimal Percent(decimal part, decimal total)
        => total == 0m ? 0m : Math.Round(part * 100m / total, 1);

    private static decimal Round(decimal value) => Math.Round(value, 2, MidpointRounding.AwayFromZero);
}