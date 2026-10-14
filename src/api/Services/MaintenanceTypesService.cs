using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Mappers;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

/// <summary>
/// Справочник видов планового технического обслуживания.
/// Справочник не удаляется, а деактивируется: иначе записи графика за
/// прошлые периоды потеряли бы ссылку на смысл своей работы.
/// </summary>
public interface IMaintenanceTypesService
{
    Task<List<MaintenanceTypeDto>> GetListAsync(bool includeInactive, CancellationToken ct);
    Task<MaintenanceTypeDto> GetByIdAsync(Guid id, CancellationToken ct);
    Task<MaintenanceTypeDto> CreateAsync(CreateMaintenanceTypeDto dto, CancellationToken ct);
    Task<MaintenanceTypeDto> UpdateAsync(Guid id, UpdateMaintenanceTypeDto dto, CancellationToken ct);
    Task DeactivateAsync(Guid id, CancellationToken ct);
}

public sealed class MaintenanceTypesService(AppDbContext db) : IMaintenanceTypesService
{
    public async Task<List<MaintenanceTypeDto>> GetListAsync(bool includeInactive, CancellationToken ct)
    {
        var query = db.MaintenanceTypes.AsNoTracking();

        if (!includeInactive)
            query = query.Where(t => t.IsActive);

        var rows = await query
            .Select(t => new { Type = t, UsageCount = t.ScheduleEntries.Count })
            .ToListAsync(ct);

        return rows
            .Select(r => r.Type.ToDto(r.UsageCount))
            .OrderBy(dto => dto.Code)
            .ToList();
    }

    public async Task<MaintenanceTypeDto> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var row = await db.MaintenanceTypes.AsNoTracking()
            .Where(t => t.Id == id)
            .Select(t => new { Type = t, UsageCount = t.ScheduleEntries.Count })
            .FirstOrDefaultAsync(ct);

        return row is null
            ? throw ApiException.NotFound("Вид обслуживания не найден.")
            : row.Type.ToDto(row.UsageCount);
    }

    public async Task<MaintenanceTypeDto> CreateAsync(CreateMaintenanceTypeDto dto, CancellationToken ct)
    {
        var code = dto.Code.Trim();

        var taken = await db.MaintenanceTypes.AnyAsync(t => t.Code == code, ct);
        if (taken)
            throw ApiException.Conflict($"Вид обслуживания с кодом {code} уже существует.");

        var entity = new MaintenanceType
        {
            Id = Guid.NewGuid(),
            Code = code,
            Name = dto.Name.Trim(),
            IntervalDays = dto.IntervalDays,
            Description = dto.Description?.Trim(),
            IsActive = true
        };

        db.MaintenanceTypes.Add(entity);
        await db.SaveChangesAsync(ct);

        return entity.ToDto(0);
    }

    public async Task<MaintenanceTypeDto> UpdateAsync(Guid id, UpdateMaintenanceTypeDto dto, CancellationToken ct)
    {
        var entity = await db.MaintenanceTypes.FindAsync([id], ct)
            ?? throw ApiException.NotFound("Вид обслуживания не найден.");

        if (dto.Name is not null)
            entity.Name = dto.Name.Trim();

        if (dto.IntervalDays is not null)
            entity.IntervalDays = dto.IntervalDays.Value;

        if (dto.Description is not null)
            entity.Description = dto.Description.Trim();

        if (dto.IsActive is not null)
            entity.IsActive = dto.IsActive.Value;

        await db.SaveChangesAsync(ct);

        var usageCount = await db.MaintenanceSchedule.CountAsync(s => s.MaintenanceTypeId == id, ct);
        return entity.ToDto(usageCount);
    }

    public async Task DeactivateAsync(Guid id, CancellationToken ct)
    {
        var entity = await db.MaintenanceTypes.FindAsync([id], ct)
            ?? throw ApiException.NotFound("Вид обслуживания не найден.");

        entity.IsActive = false;
        await db.SaveChangesAsync(ct);
    }
}