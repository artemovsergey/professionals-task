using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Mappers;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

/// <summary>
/// CRUD единиц оборудования и смена статуса.
///
/// Статус меняется отдельным методом, а не через общий Update: у
/// выведенного из эксплуатации оборудования его менять запрещает
/// триггер trg_equipment_status_guard. Если разрешить это в общем
/// обновлении, клиент получит 400 из триггера и не поймёт, что именно
/// он сделал не так.
/// </summary>
public interface IEquipmentService
{
    Task<PagedResult<EquipmentShortDto>> GetListAsync(
        Guid? workshopId, string? search, string? status, int criticality,
        bool includeRetired, int page, int pageSize, CancellationToken ct);

    Task<EquipmentDto> GetByIdAsync(Guid id, CancellationToken ct);
    Task<EquipmentDto> CreateAsync(CreateEquipmentDto dto, CancellationToken ct);
    Task<EquipmentDto> UpdateAsync(Guid id, UpdateEquipmentDto dto, CancellationToken ct);
    Task<EquipmentDto> ChangeStatusAsync(Guid id, string status, CancellationToken ct);
    Task DeleteAsync(Guid id, CancellationToken ct);
    Task<List<EquipmentShortDto>> GetForSelectAsync(Guid? workshopId, CancellationToken ct);
}

public sealed class EquipmentService(AppDbContext db) : IEquipmentService
{
    public async Task<PagedResult<EquipmentShortDto>> GetListAsync(
        Guid? workshopId, string? search, string? status, int criticality,
        bool includeRetired, int page, int pageSize, CancellationToken ct)
    {
        page = page < 1 ? 1 : page;
        pageSize = pageSize is < 1 or > 100 ? 20 : pageSize;

        var query = BuildFilter(workshopId, search, status, criticality, includeRetired);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderBy(e => e.InventoryNumber)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(e => new EquipmentShortDto(
                e.Id, e.InventoryNumber, e.Name, e.WorkshopId, e.Workshop.Name,
                StatusToString(e.Status), e.Criticality))
            .ToListAsync(ct);

        return new PagedResult<EquipmentShortDto>(items, total, page, pageSize);
    }

    public async Task<EquipmentDto> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var equipment = await db.Equipment
            .AsNoTracking()
            .Include(e => e.Workshop)
            .FirstOrDefaultAsync(e => e.Id == id, ct)
            ?? throw ApiException.NotFound($"Оборудование с идентификатором {id} не найдено.");

        return equipment.ToDto(equipment.Workshop.Name);
    }

    public async Task<EquipmentDto> CreateAsync(CreateEquipmentDto dto, CancellationToken ct)
    {
        await EnsureWorkshopExistsAsync(dto.WorkshopId, ct);
        EnsureStatusIsKnown(dto.Status);

        var duplicate = await db.Equipment
            .AnyAsync(e => e.InventoryNumber == dto.InventoryNumber, ct);
        if (duplicate)
            throw ApiException.Conflict(
                $"Оборудование с инвентарным номером «{dto.InventoryNumber}» уже заведено.",
                ErrorCodes.Conflict);

        if (dto.DecommissionDate is { } decommissioned && decommissioned < dto.CommissionDate)
            throw ApiException.BadRequest(
                "Дата вывода из эксплуатации не может быть раньше даты ввода.");

        var equipment = new Equipment
        {
            InventoryNumber = dto.InventoryNumber.Trim(),
            Name = dto.Name.Trim(),
            WorkshopId = dto.WorkshopId,
            Manufacturer = dto.Manufacturer?.Trim(),
            Model = dto.Model?.Trim(),
            SerialNumber = dto.SerialNumber?.Trim(),
            CommissionDate = dto.CommissionDate,
            DecommissionDate = dto.DecommissionDate,
            Status = StringToStatus(dto.Status),
            Criticality = dto.Criticality,
            Location = dto.Location?.Trim(),
            Notes = dto.Notes?.Trim(),
        };

        db.Equipment.Add(equipment);
        await db.SaveChangesAsync(ct);

        var workshop = await db.Workshops.AsNoTracking()
            .FirstAsync(w => w.Id == equipment.WorkshopId, ct);

        return equipment.ToDto(workshop.Name);
    }

    public async Task<EquipmentDto> UpdateAsync(Guid id, UpdateEquipmentDto dto, CancellationToken ct)
    {
        var equipment = await db.Equipment
            .Include(e => e.Workshop)
            .FirstOrDefaultAsync(e => e.Id == id, ct)
            ?? throw ApiException.NotFound($"Оборудование с идентификатором {id} не найдено.");

        if (equipment.Status == EquipmentStatus.ВыведеноИзЭксплуатации)
            throw ApiException.Conflict(
                "Оборудование выведено из эксплуатации: изменение данных недоступно.",
                ErrorCodes.StatusLocked);

        if (dto.WorkshopId is { } workshopId)
        {
            await EnsureWorkshopExistsAsync(workshopId, ct);
            equipment.WorkshopId = workshopId;
        }

        if (dto.Name is not null) equipment.Name = dto.Name.Trim();
        if (dto.Manufacturer is not null) equipment.Manufacturer = dto.Manufacturer.Trim();
        if (dto.Model is not null) equipment.Model = dto.Model.Trim();
        if (dto.SerialNumber is not null) equipment.SerialNumber = dto.SerialNumber.Trim();
        if (dto.Location is not null) equipment.Location = dto.Location.Trim();
        if (dto.Notes is not null) equipment.Notes = dto.Notes.Trim();
        if (dto.Criticality is { } criticality) equipment.Criticality = criticality;

        await db.SaveChangesAsync(ct);

        // Название цеха берём заново: при переносе оборудования в другой
        // цех уже загруженная навигация устарела и вернула бы старое имя.
        var workshopName = await db.Workshops.AsNoTracking()
            .Where(w => w.Id == equipment.WorkshopId)
            .Select(w => w.Name)
            .FirstAsync(ct);

        return equipment.ToDto(workshopName);
    }

    public async Task<EquipmentDto> ChangeStatusAsync(Guid id, string status, CancellationToken ct)
    {
        EnsureStatusIsKnown(status);

        var equipment = await db.Equipment
            .Include(e => e.Workshop)
            .FirstOrDefaultAsync(e => e.Id == id, ct)
            ?? throw ApiException.NotFound($"Оборудование с идентификатором {id} не найдено.");

        var target = StringToStatus(status);

        // Явная проверка повторяет правило триггера, но с понятным
        // сообщением. Пользователь видит «изменить статус нельзя», а не
        // текст из PostgreSQL с указанием на имя ограничения.
        if (equipment.Status == EquipmentStatus.ВыведеноИзЭксплуатации && target != equipment.Status)
            throw ApiException.Conflict(
                $"Оборудование «{equipment.InventoryNumber}» выведено из эксплуатации: изменить статус нельзя.",
                ErrorCodes.StatusLocked);

        equipment.Status = target;
        await db.SaveChangesAsync(ct);

        return equipment.ToDto(equipment.Workshop.Name);
    }

    public async Task DeleteAsync(Guid id, CancellationToken ct)
    {
        var equipment = await db.Equipment.FirstOrDefaultAsync(e => e.Id == id, ct)
            ?? throw ApiException.NotFound($"Оборудование с идентификатором {id} не найдено.");

        var hasOrders = await db.WorkOrders.AnyAsync(w => w.EquipmentId == id, ct);
        if (hasOrders)
            throw ApiException.Conflict(
                "По оборудованию есть заявки — удалить его нельзя. Выведите из эксплуатации.",
                ErrorCodes.Conflict);

        var hasSchedule = await db.MaintenanceSchedule.AnyAsync(m => m.EquipmentId == id, ct);
        if (hasSchedule)
            throw ApiException.Conflict(
                "По оборудованию есть записи графика ТО — удалите их или оставьте оборудование.",
                ErrorCodes.Conflict);

        db.Equipment.Remove(equipment);
        await db.SaveChangesAsync(ct);
    }

    public async Task<List<EquipmentShortDto>> GetForSelectAsync(Guid? workshopId, CancellationToken ct)
    {
        var query = db.Equipment
            .AsNoTracking()
            .Where(e => e.Status != EquipmentStatus.ВыведеноИзЭксплуатации);

        if (workshopId is { } id)
            query = query.Where(e => e.WorkshopId == id);

        return await query
            .OrderBy(e => e.InventoryNumber)
            .Select(e => new EquipmentShortDto(
                e.Id, e.InventoryNumber, e.Name, e.WorkshopId, e.Workshop.Name,
                StatusToString(e.Status), e.Criticality))
            .ToListAsync(ct);
    }

    private IQueryable<Equipment> BuildFilter(
        Guid? workshopId, string? search, string? status, int criticality, bool includeRetired)
    {
        var query = db.Equipment.AsNoTracking().Include(e => e.Workshop).AsQueryable();

        if (workshopId is { } id)
            query = query.Where(e => e.WorkshopId == id);

        if (!string.IsNullOrWhiteSpace(search))
        {
            var pattern = search.Trim();
            query = query.Where(e =>
                EF.Functions.ILike(e.InventoryNumber, $"%{pattern}%") ||
                EF.Functions.ILike(e.Name, $"%{pattern}%") ||
                (e.SerialNumber != null && EF.Functions.ILike(e.SerialNumber, $"%{pattern}%")));
        }

        if (!string.IsNullOrWhiteSpace(status))
        {
            var wanted = StringToStatus(status);
            query = query.Where(e => e.Status == wanted);
        }
        else if (!includeRetired)
        {
            query = query.Where(e => e.Status != EquipmentStatus.ВыведеноИзЭксплуатации);
        }

        if (criticality is >= 1 and <= 5)
            query = query.Where(e => e.Criticality == criticality);

        return query;
    }

    private async Task EnsureWorkshopExistsAsync(Guid workshopId, CancellationToken ct)
    {
        var exists = await db.Workshops.AnyAsync(w => w.Id == workshopId, ct);
        if (!exists)
            throw ApiException.BadRequest($"Цех с идентификатором {workshopId} не найден.");
    }

    private static void EnsureStatusIsKnown(string status) =>
        _ = StringToStatus(status);

    /// <summary>
    /// Строка из запроса в значение перечисления. Неизвестное значение —
    /// ошибка 400, а не молчаливое «В работе»: молчаливый откат
    /// выглядит на демонстрации как «приложение забыло данные».
    /// </summary>
    private static EquipmentStatus StringToStatus(string? status) =>
        status switch
        {
            EquipmentStatuses.Running => EquipmentStatus.ВРаботе,
            EquipmentStatuses.InRepair => EquipmentStatus.ВРемонте,
            EquipmentStatuses.Retired => EquipmentStatus.ВыведеноИзЭксплуатации,
            _ => throw ApiException.BadRequest(
                $"Недопустимый статус «{status}». Допустимы: {EquipmentStatuses.Running}, " +
                $"{EquipmentStatuses.InRepair}, {EquipmentStatuses.Retired}."),
        };

    private static string StatusToString(EquipmentStatus status) =>
        status switch
        {
            EquipmentStatus.ВРемонте => EquipmentStatuses.InRepair,
            EquipmentStatus.ВыведеноИзЭксплуатации => EquipmentStatuses.Retired,
            _ => EquipmentStatuses.Running,
        };
}