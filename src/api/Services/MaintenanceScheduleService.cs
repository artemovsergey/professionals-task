using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Mappers;
using ToirProf.Api.Middlewares;

namespace ToirProf.Api.Services;

/// <summary>
/// График планового технического обслуживания.
///
/// Следующая плановая дата не считается в коде: её вычисляет функция
/// базы fn_next_maintenance_date(date, integer). Правило «через месяц»,
/// заданное в задании, живёт в одном месте — в базе, и меняется там же.
/// </summary>
public interface IMaintenanceScheduleService
{
    Task<List<MaintenanceScheduleDto>> GetListAsync(Guid? equipmentId, DateRange period, string? status, CancellationToken ct);
    Task<MaintenanceScheduleDto> GetByIdAsync(Guid id, CancellationToken ct);
    Task<MaintenanceScheduleDto> CreateAsync(CreateMaintenanceScheduleDto dto, CancellationToken ct);
    Task<MaintenanceScheduleDto> CompleteAsync(Guid id, CompleteMaintenanceScheduleDto dto, CancellationToken ct);
    Task MarkPlannedAsync(Guid id, CancellationToken ct);
    Task DeleteAsync(Guid id, CancellationToken ct);
}

public sealed class MaintenanceScheduleService(AppDbContext db) : IMaintenanceScheduleService
{
    private const string StatusPlanned = "Запланировано";
    private const string StatusCompleted = "Выполнено";
    private const string StatusOverdue = "Просрочено";

    public async Task<List<MaintenanceScheduleDto>> GetListAsync(
        Guid? equipmentId, DateRange period, string? status, CancellationToken ct)
    {
        await RefreshOverdueAsync(ct);

        // Сортировку ставим до проекции: EF Core не умеет протаскивать
        // OrderBy через вызов конструктора ScheduleRow и падает с
        // «The LINQ expression ... could not be translated».
        var query = db.MaintenanceSchedule.AsNoTracking();

        if (equipmentId is not null)
            query = query.Where(s => s.EquipmentId == equipmentId.Value);

        if (period.From is not null)
            query = query.Where(s => s.PlannedDate >= period.Start);

        if (period.To is not null)
            query = query.Where(s => s.PlannedDate <= period.End);

        if (!string.IsNullOrWhiteSpace(status))
            query = query.Where(s => s.Status == status);

        var rows = await query
            .OrderBy(s => s.PlannedDate)
            .ThenBy(s => s.Equipment.InventoryNumber)
            .Select(s => new ScheduleRow(
                s.Id, s.EquipmentId, s.Equipment.Name, s.Equipment.InventoryNumber,
                s.MaintenanceTypeId, s.MaintenanceType.Name, s.MaintenanceType.IntervalDays,
                s.PlannedDate, s.CompletedDate, s.NextPlannedDate,
                s.Status, s.ActualCost, s.Notes))
            .ToListAsync(ct);

        return rows.Select(row => new MaintenanceScheduleDto(
                row.Id, row.EquipmentId, row.EquipmentName, row.InventoryNumber,
                row.MaintenanceTypeId, row.MaintenanceTypeName, row.IntervalDays,
                row.PlannedDate, row.CompletedDate, row.NextPlannedDate,
                row.Status, row.ActualCost, row.Notes))
            .ToList();
    }

    public async Task<MaintenanceScheduleDto> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var row = await BuildProjection().FirstOrDefaultAsync(s => s.Id == id, ct);

        return row is null
            ? throw ApiException.NotFound("Запись графика не найдена.")
            : new MaintenanceScheduleDto(
                row.Id, row.EquipmentId, row.EquipmentName, row.InventoryNumber,
                row.MaintenanceTypeId, row.MaintenanceTypeName, row.IntervalDays,
                row.PlannedDate, row.CompletedDate, row.NextPlannedDate,
                row.Status, row.ActualCost, row.Notes);
    }

    public async Task<MaintenanceScheduleDto> CreateAsync(CreateMaintenanceScheduleDto dto, CancellationToken ct)
    {
        var equipment = await db.Equipment.FindAsync([dto.EquipmentId], ct)
            ?? throw ApiException.BadRequest("Оборудование не найдено.");

        var type = await db.MaintenanceTypes.FindAsync([dto.MaintenanceTypeId], ct)
            ?? throw ApiException.BadRequest("Вид обслуживания не найден.");

        var duplicate = await db.MaintenanceSchedule.AnyAsync(
            s => s.EquipmentId == dto.EquipmentId
                 && s.MaintenanceTypeId == dto.MaintenanceTypeId
                 && s.PlannedDate == dto.PlannedDate, ct);

        if (duplicate)
            throw ApiException.Conflict(
                $"Запись графика для оборудования {equipment.InventoryNumber} " +
                $"и вида обслуживания {type.Code} на {dto.PlannedDate:dd.MM.yyyy} уже существует.");

        var entity = new MaintenanceSchedule
        {
            Id = Guid.NewGuid(),
            EquipmentId = dto.EquipmentId,
            MaintenanceTypeId = dto.MaintenanceTypeId,
            PlannedDate = dto.PlannedDate,
            Status = StatusPlanned,
            Notes = dto.Notes?.Trim()
        };

        db.MaintenanceSchedule.Add(entity);
        await db.SaveChangesAsync(ct);

        return new MaintenanceScheduleDto(
            entity.Id, equipment.Id, equipment.Name, equipment.InventoryNumber,
            type.Id, type.Name, type.IntervalDays, entity.PlannedDate,
            null, null, entity.Status, null, entity.Notes);
    }

    public async Task<MaintenanceScheduleDto> CompleteAsync(
        Guid id, CompleteMaintenanceScheduleDto dto, CancellationToken ct)
    {
        var entity = await db.MaintenanceSchedule.FindAsync([id], ct)
            ?? throw ApiException.NotFound("Запись графика не найдена.");

        if (entity.Status == StatusCompleted)
            throw ApiException.Conflict("Запись графика уже отмечена как выполненная.");

        // Дата выполнения позже плановой — обычная ситуация, а не ошибка.
        // Но раньше даты ввода оборудования в эксплуатацию выполнить ТО нельзя.
        var equipment = await db.Equipment.FindAsync([entity.EquipmentId], ct);
        if (equipment is not null && dto.CompletedDate < equipment.CommissionDate)
            throw ApiException.BadRequest(
                $"Дата выполнения {dto.CompletedDate:dd.MM.yyyy} раньше даты ввода оборудования " +
                $"{equipment.InventoryNumber} в эксплуатацию.");

        var type = await db.MaintenanceTypes.FindAsync([entity.MaintenanceTypeId], ct);
        var interval = type?.IntervalDays ?? 30;

        entity.CompletedDate = dto.CompletedDate;
        entity.ActualCost = dto.ActualCost;
        entity.Status = StatusCompleted;
        entity.NextPlannedDate = await NextPlannedDateAsync(dto.CompletedDate, interval, ct);

        await db.SaveChangesAsync(ct);

        return new MaintenanceScheduleDto(
            entity.Id, entity.EquipmentId, equipment?.Name ?? string.Empty,
            equipment?.InventoryNumber ?? string.Empty, entity.MaintenanceTypeId,
            type?.Name ?? string.Empty, interval, entity.PlannedDate,
            entity.CompletedDate, entity.NextPlannedDate, entity.Status,
            entity.ActualCost, entity.Notes);
    }

    public async Task MarkPlannedAsync(Guid id, CancellationToken ct)
    {
        var entity = await db.MaintenanceSchedule.FindAsync([id], ct)
            ?? throw ApiException.NotFound("Запись графика не найдена.");

        if (entity.Status == StatusCompleted)
            throw ApiException.Conflict("Выполненную запись графика вернуть в план нельзя.");

        entity.Status = StatusPlanned;
        entity.CompletedDate = null;
        entity.NextPlannedDate = null;

        await db.SaveChangesAsync(ct);
    }

    public async Task DeleteAsync(Guid id, CancellationToken ct)
    {
        var entity = await db.MaintenanceSchedule.FindAsync([id], ct)
            ?? throw ApiException.NotFound("Запись графика не найдена.");

        if (entity.Status == StatusCompleted)
            throw ApiException.Conflict(
                "Выполненную запись графика удалить нельзя: по ней считается выполнение плана ТО.");

        var linked = await db.WorkOrders.AnyAsync(w => w.ScheduleId == id, ct);
        if (linked)
            throw ApiException.Conflict("Запись графика связана с заявками — удалить её нельзя.");

        db.MaintenanceSchedule.Remove(entity);
        await db.SaveChangesAsync(ct);
    }

    /// <summary>
    /// Просроченные записи пересчитываются перед каждым чтением графика:
    /// иначе запись, которую не выполнили в срок, навсегда осталась бы
    /// «Запланировано» и не попала в отчёт по просрочкам.
    /// </summary>
    private async Task RefreshOverdueAsync(CancellationToken ct)
    {
        var today = DateOnly.FromDateTime(DateTime.Today);

        var planned = await db.MaintenanceSchedule
            .Where(s => s.Status == StatusPlanned && s.PlannedDate < today)
            .ToListAsync(ct);

        if (planned.Count == 0)
            return;

        foreach (var entry in planned)
            entry.Status = StatusOverdue;

        await db.SaveChangesAsync(ct);
    }

    private async Task<DateOnly?> NextPlannedDateAsync(
        DateOnly completedDate, int intervalDays, CancellationToken ct)
    {
        var dates = await db.Database
            .SqlQuery<DateOnly?>($"""
                SELECT fn_next_maintenance_date({completedDate}::date, {intervalDays}) AS "Value"
                """)
            .ToListAsync(ct);

        return dates.FirstOrDefault();
    }

    private IQueryable<ScheduleRow> BuildProjection()
    {
        return db.MaintenanceSchedule.AsNoTracking()
            .Select(s => new ScheduleRow(
                s.Id, s.EquipmentId, s.Equipment.Name, s.Equipment.InventoryNumber,
                s.MaintenanceTypeId, s.MaintenanceType.Name, s.MaintenanceType.IntervalDays,
                s.PlannedDate, s.CompletedDate, s.NextPlannedDate,
                s.Status, s.ActualCost, s.Notes));
    }

    private sealed record ScheduleRow(
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
}