// Сервис заявок: жизненный цикл от «черновика» до «завершена».
//
// Два правила живут не здесь, а в базе — и потому продублированы проверками
// с понятным сообщением:
//   * простой (downtime_hours) считает триггер trg_work_order_dates_check;
//   * стоимость позиции (cost) — вычисляемая колонка quantity * unit_price.
// После SaveChangesAsync значения из базы перечитываются заново, иначе в
// ответе уедут нули.

using System.Linq.Expressions;
using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

public interface IWorkOrderService
{
    Task<PagedResult<WorkOrderShortDto>> GetListAsync(WorkOrderFilter filter, CancellationToken ct);
    Task<WorkOrderDto> GetByIdAsync(Guid id, CancellationToken ct);
    Task<WorkOrderDto> GetByNumberAsync(string number, CancellationToken ct);
    Task<WorkOrderDto> CreateAsync(CreateWorkOrderDto dto, Guid userId, CancellationToken ct);
    Task<WorkOrderDto> UpdateAsync(Guid id, UpdateWorkOrderDto dto, CancellationToken ct);
    Task<WorkOrderDto> AssignCrewAsync(Guid id, AssignCrewDto dto, CancellationToken ct);
    Task<WorkOrderDto> StartAsync(Guid id, StartWorkOrderDto dto, CancellationToken ct);
    Task<WorkOrderDto> CompleteAsync(Guid id, CompleteWorkOrderDto dto, CancellationToken ct);
    Task<WorkOrderDto> ChangeStatusAsync(Guid id, ChangeStatusDto dto, CancellationToken ct);
    Task<WorkOrderDto> AddMaterialAsync(Guid id, MaterialWriteOffDto dto, CancellationToken ct);
    Task<MaterialCostDto> GetCostAsync(Guid id, CancellationToken ct);
}

public sealed class WorkOrderService(AppDbContext db, IWorkOrderNumberService numbers) : IWorkOrderService
{
    // ---------------------------------------------------------------- чтение

    public async Task<PagedResult<WorkOrderShortDto>> GetListAsync(WorkOrderFilter filter, CancellationToken ct)
    {
        var query = BaseQuery();

        if (filter.EquipmentId is { } equipmentId)
            query = query.Where(w => w.EquipmentId == equipmentId);
        if (filter.CrewId is { } crewId)
            query = query.Where(w => w.CrewId == crewId);
        if (!string.IsNullOrWhiteSpace(filter.Status))
        {
            var status = ToStatus(filter.Status);
            query = query.Where(w => w.Status == status);
        }
        if (!string.IsNullOrWhiteSpace(filter.Priority))
        {
            var priority = ToPriority(filter.Priority);
            query = query.Where(w => w.Priority == priority);
        }
        if (filter.From is { } from)
            query = query.Where(w => w.CreatedAt >= from.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc));
        if (filter.To is { } to)
            query = query.Where(w => w.CreatedAt < to.AddDays(1).ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc));
        if (!string.IsNullOrWhiteSpace(filter.Query))
        {
            var pattern = $"%{Escape(filter.Query)}%";
            query = query.Where(w => EF.Functions.ILike(w.Number, pattern)
                                     || EF.Functions.ILike(w.Title, pattern)
                                     || EF.Functions.ILike(w.Equipment.Name, pattern)
                                     || EF.Functions.ILike(w.Equipment.InventoryNumber, pattern));
        }

        query = ApplySort(query, filter.Sort, filter.Order);

        var total = await query.CountAsync(ct);
        var page = filter.NormalizedPage;
        var size = filter.NormalizedPageSize;

        var items = await query
            .Skip((page - 1) * size)
            .Take(size)
            .Select(w => new WorkOrderShortDto(
                w.Id,
                w.Number,
                w.EquipmentId,
                w.Equipment.Name,
                w.Equipment.InventoryNumber,
                StatusText(w.Priority),
                StatusText(w.Status),
                w.PlannedStart,
                w.PlannedEnd,
                w.DowntimeHours,
                w.Crew != null ? w.Crew.Name : null))
            .ToListAsync(ct);

        return new PagedResult<WorkOrderShortDto>(items, total, page, size);
    }

    public Task<WorkOrderDto> GetByIdAsync(Guid id, CancellationToken ct)
        => Load(w => w.Id == id, ct);

    public Task<WorkOrderDto> GetByNumberAsync(string number, CancellationToken ct)
        => Load(w => w.Number == number, ct);

    // -------------------------------------------------------------- создание

    public async Task<WorkOrderDto> CreateAsync(CreateWorkOrderDto dto, Guid userId, CancellationToken ct)
    {
        var equipment = await db.Equipment
            .AsNoTracking()
            .FirstOrDefaultAsync(e => e.Id == dto.EquipmentId, ct);
        if (equipment is null)
            throw ApiException.NotFound("Оборудование не найдено.");

        // Выведенное из эксплуатации оборудование ремонтировать нельзя:
        // заявка на него — ошибка пользователя, а не системы.
        if (equipment.Status == EquipmentStatus.ВыведеноИзЭксплуатации)
            throw ApiException.BadRequest(
                $"Оборудование {equipment.InventoryNumber} выведено из эксплуатации — заявку на него создать нельзя.");

        if (dto.PlannedStart is { } ps && dto.PlannedEnd is { } pe && pe < ps)
            throw ApiException.BadRequest("Плановое окончание раньше планового начала.");

        Guid? crewId = null;
        if (dto.CrewId is { } requestedCrew)
        {
            crewId = await EnsureCrewExistsAsync(requestedCrew, ct);
        }

        var order = new WorkOrder
        {
            Id = Guid.NewGuid(),
            Number = await numbers.NextAsync(ct),
            EquipmentId = dto.EquipmentId,
            MaintenanceTypeId = dto.MaintenanceTypeId,
            ScheduleId = dto.ScheduleId,
            CrewId = crewId,
            CreatedBy = userId,
            Title = dto.Title.Trim(),
            Description = dto.Description.Trim(),
            Priority = ToPriority(dto.Priority),
            Status = WorkOrderStatus.Создана,
            PlannedStart = dto.PlannedStart,
            PlannedEnd = dto.PlannedEnd,
        };

        db.WorkOrders.Add(order);
        await db.SaveChangesAsync(ct);

        return await GetByIdAsync(order.Id, ct);
    }

    public async Task<WorkOrderDto> UpdateAsync(Guid id, UpdateWorkOrderDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        if (dto.Title is { } title)
            order.Title = title.Trim();
        if (dto.Description is { } description)
            order.Description = description.Trim();
        if (dto.Priority is { } priority)
            order.Priority = ToPriority(priority);
        if (dto.PlannedStart is not null)
            order.PlannedStart = dto.PlannedStart;
        if (dto.PlannedEnd is not null)
            order.PlannedEnd = dto.PlannedEnd;
        if (dto.FailureReason is { } reason)
            order.FailureReason = reason.Trim();

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    // ---------------------------------------------------------- жизненный цикл

    public async Task<WorkOrderDto> AssignCrewAsync(Guid id, AssignCrewDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        await EnsureCrewExistsAsync(dto.CrewId, ct);

        if (dto.AssignedTo is { } assignee)
        {
            var inCrew = await db.CrewMembers
                .AsNoTracking()
                .AnyAsync(m => m.CrewId == dto.CrewId && m.UserId == assignee, ct);
            if (!inCrew)
                throw ApiException.BadRequest("Исполнитель не состоит в выбранной бригаде.");
        }

        // Бригада не может вести две заявки одновременно: иначе простой и
        // загрузка в рейтинге бригад считаются неверно.
        var busy = await db.WorkOrders
            .AsNoTracking()
            .AnyAsync(w => w.CrewId == dto.CrewId
                           && w.Id != id
                           && w.Status == WorkOrderStatus.ВРаботе, ct);
        if (busy)
            throw new ApiException(409, "Бригада уже ведёт другую заявку в работе.", ErrorCodes.CrewBusy);

        order.CrewId = dto.CrewId;
        order.AssignedTo = dto.AssignedTo;
        if (order.Status == WorkOrderStatus.Создана)
            order.Status = WorkOrderStatus.Назначена;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task<WorkOrderDto> StartAsync(Guid id, StartWorkOrderDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        if (!WorkOrderStatuses.CanTransition(StatusText(order.Status), WorkOrderStatuses.InProgress))
            throw TransitionError(order, WorkOrderStatuses.InProgress);

        order.ActualStart = dto.ActualStart.ToUniversalTime();
        order.Status = WorkOrderStatus.ВРаботе;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task<WorkOrderDto> CompleteAsync(Guid id, CompleteWorkOrderDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        if (!WorkOrderStatuses.CanTransition(StatusText(order.Status), WorkOrderStatuses.Completed))
            throw TransitionError(order, WorkOrderStatuses.Completed);

        // Триггер требует обе фактические даты, поэтому начало подставляем,
        // если мастер его не указал: иначе заявку невозможно закрыть.
        order.ActualStart ??= DateTimeOffset.UtcNow;
        order.ActualEnd = dto.ActualEnd.ToUniversalTime();
        order.FailureReason = dto.FailureReason.Trim();
        order.CompletedAt = dto.ActualEnd.ToUniversalTime();
        order.Status = WorkOrderStatus.Закрыта;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task<WorkOrderDto> ChangeStatusAsync(Guid id, ChangeStatusDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        var target = ToStatus(dto.Status);
        var targetText = StatusText(target);

        if (!WorkOrderStatuses.CanTransition(StatusText(order.Status), targetText))
            throw TransitionError(order, targetText);

        if (target == WorkOrderStatus.Закрыта)
        {
            // Через смену статуса закрыть заявку тоже можно, но только если
            // фактические даты и причина уже проставлены.
            if (order.ActualStart is null || order.ActualEnd is null)
                throw ApiException.BadRequest(
                    "Для завершения укажите фактические даты начала и окончания работ.");
            if (string.IsNullOrWhiteSpace(order.FailureReason))
                throw ApiException.BadRequest(
                    "Для завершения укажите причину неисправности.");
            order.CompletedAt = order.ActualEnd;
        }

        if (target != WorkOrderStatus.Закрыта && order.Status == WorkOrderStatus.Закрыта)
            order.CompletedAt = null;

        order.Status = target;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    // ---------------------------------------------------------------- списание

    public async Task<WorkOrderDto> AddMaterialAsync(Guid id, MaterialWriteOffDto dto, CancellationToken ct)
    {
        var order = await FindAsync(id, ct);
        EnsureEditable(order);

        var material = await db.Materials.FirstOrDefaultAsync(m => m.Id == dto.MaterialId, ct);
        if (material is null)
            throw ApiException.NotFound("Материал не найден.");
        if (!material.IsActive)
            throw ApiException.BadRequest($"Материал {material.Name} отключён и не может быть списан.");

        var line = await db.WorkOrderMaterials
            .FirstOrDefaultAsync(w => w.WorkOrderId == id && w.MaterialId == dto.MaterialId, ct);

        // Уже списанное количество прибавляем: повторная правка — это
        // докупление, а не новая позиция.
        var already = line?.Quantity ?? 0m;
        var required = already + dto.Quantity;

        if (material.Stock < required)
            throw new ApiException(
                409,
                $"Недостаточно материала «{material.Name}»: на складе {material.Stock} {material.Unit}, требуется {required}.",
                ErrorCodes.NotEnoughStock);

        if (line is null)
        {
            line = new WorkOrderMaterial
            {
                Id = Guid.NewGuid(),
                WorkOrderId = id,
                MaterialId = dto.MaterialId,
                Quantity = dto.Quantity,
                UnitPrice = material.Price,
            };
            db.WorkOrderMaterials.Add(line);
        }
        else
        {
            line.Quantity = required;
            // Цену фиксируем на момент последнего списания: historic
            // стоимость заявки не должна «плыть» при изменении прайса.
            line.UnitPrice = material.Price;
        }

        material.Stock -= dto.Quantity;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task<MaterialCostDto> GetCostAsync(Guid id, CancellationToken ct)
    {
        var exists = await db.WorkOrders.AsNoTracking().AnyAsync(w => w.Id == id, ct);
        if (!exists)
            throw ApiException.NotFound("Заявка не найдена.");

        var lines = await db.WorkOrderMaterials
            .AsNoTracking()
            .Where(w => w.WorkOrderId == id)
            .ToListAsync(ct);

        // SUM в SQL вернул бы null на пустом наборе — нули удобнее клиенту.
        var total = lines.Sum(l => l.Cost);
        return new MaterialCostDto(id, total, lines.Count);
    }

    // ----------------------------------------------------------------- помощь

    private IQueryable<WorkOrder> BaseQuery() => db.WorkOrders.AsNoTracking().Include(w => w.Equipment);

    private static IQueryable<WorkOrder> ApplySort(IQueryable<WorkOrder> query, string? sort, string? order)
    {
        var descending = !string.Equals(order, "asc", StringComparison.OrdinalIgnoreCase);

        return (sort?.ToLowerInvariant()) switch
        {
            "number" => descending ? query.OrderByDescending(w => w.Number) : query.OrderBy(w => w.Number),
            "status" => descending ? query.OrderByDescending(w => w.Status) : query.OrderBy(w => w.Status),
            "priority" => descending ? query.OrderByDescending(w => w.Priority) : query.OrderBy(w => w.Priority),
            "plannedstart" => descending
                ? query.OrderByDescending(w => w.PlannedStart)
                : query.OrderBy(w => w.PlannedStart),
            "downtime" => descending
                ? query.OrderByDescending(w => w.DowntimeHours)
                : query.OrderBy(w => w.DowntimeHours),
            _ => descending ? query.OrderByDescending(w => w.CreatedAt) : query.OrderBy(w => w.CreatedAt),
        };
    }

    private async Task<WorkOrder> FindAsync(Guid id, CancellationToken ct)
    {
        var order = await db.WorkOrders.FirstOrDefaultAsync(w => w.Id == id, ct);
        return order ?? throw ApiException.NotFound("Заявка не найдена.");
    }

    private async Task<Guid> EnsureCrewExistsAsync(Guid crewId, CancellationToken ct)
    {
        var crew = await db.Crews.AsNoTracking().FirstOrDefaultAsync(c => c.Id == crewId, ct);
        if (crew is null)
            throw ApiException.NotFound("Бригада не найдена.");
        if (!crew.IsActive)
            throw ApiException.BadRequest($"Бригада {crew.Name} отключена.");
        return crew.Id;
    }

    private async Task<WorkOrderDto> Load(Expression<Func<WorkOrder, bool>> predicate, CancellationToken ct)
    {
        var row = await db.WorkOrders
            .AsNoTracking()
            .Include(w => w.Equipment)
            .ThenInclude(e => e.Workshop)
            .Include(w => w.MaintenanceType)
            .Include(w => w.Crew)
            .Include(w => w.Assignee)
            .Include(w => w.Materials)
            .ThenInclude(m => m.Material)
            .FirstOrDefaultAsync(predicate, ct);

        if (row is null)
            throw ApiException.NotFound("Заявка не найдена.");

        var history = await db.OperationLog
            .AsNoTracking()
            .Where(l => l.TableName == "work_orders" && l.RecordId == row.Id)
            .OrderByDescending(l => l.CreatedAt)
            .Take(20)
            .Select(l => new WorkOrderHistoryDto(
                l.CreatedAt,
                l.User != null ? l.User.FullName : null,
                l.Operation,
                DescribeAction(l.Operation, l.NewValues)))
            .ToListAsync(ct);

        return new WorkOrderDto(
            row.Id,
            row.Number,
            row.EquipmentId,
            row.Equipment.Name,
            row.Equipment.InventoryNumber,
            row.Equipment.Workshop.Name,
            row.MaintenanceTypeId,
            row.MaintenanceType?.Name,
            row.CrewId,
            row.Crew?.Name,
            row.AssignedTo,
            row.Assignee?.FullName,
            row.Title,
            row.Description ?? string.Empty,
            StatusText(row.Priority),
            StatusText(row.Status),
            row.PlannedStart,
            row.PlannedEnd,
            row.ActualStart,
            row.ActualEnd,
            row.DowntimeHours,
            row.FailureReason,
            row.CompletedAt,
            DateOnly.FromDateTime(row.CreatedAt),
            row.Materials.Sum(m => m.Cost),
            row.Materials
                .OrderBy(m => m.Material.Name)
                .Select(m => new WorkOrderMaterialDto(
                    m.MaterialId,
                    m.Material.Sku,
                    m.Material.Name,
                    m.Material.Unit,
                    m.Quantity,
                    m.UnitPrice,
                    m.Cost))
                .ToList(),
            history);
    }

    private static string DescribeAction(string operation, string? newValues) => operation switch
    {
        "INSERT" => "Заявка создана",
        "UPDATE" => "Данные заявки изменены",
        "DELETE" => "Заявка удалена",
        _ => newValues is null ? "Изменение" : $"Изменение ({newValues.Length} байт)",
    };

    private static void EnsureEditable(WorkOrder order)
    {
        if (order.Status is WorkOrderStatus.Закрыта or WorkOrderStatus.Отменена)
            throw new ApiException(
                409,
                $"Заявка {order.Number} имеет статус «{StatusText(order.Status)}» и больше не изменяется.",
                ErrorCodes.StatusLocked);
    }

    private static ApiException TransitionError(WorkOrder order, string target) => new(
        409,
        $"Недопустимый переход статуса: «{StatusText(order.Status)}» → «{target}».",
        ErrorCodes.StatusLocked);

    // Перевод строк DTO в enum. Неизвестное значение — ошибка пользователя,
    // а не молчаливый откат к значению по умолчанию.
    public static WorkOrderStatus ToStatus(string value) => value switch
    {
        WorkOrderStatuses.Draft => WorkOrderStatus.Создана,
        WorkOrderStatuses.Assigned => WorkOrderStatus.Назначена,
        WorkOrderStatuses.InProgress => WorkOrderStatus.ВРаботе,
        WorkOrderStatuses.Completed => WorkOrderStatus.Закрыта,
        WorkOrderStatuses.Cancelled => WorkOrderStatus.Отменена,
        _ => throw ApiException.BadRequest(
            $"Неизвестный статус «{value}». Допустимо: {WorkOrderStatuses.AllText}."),
    };

    public static WorkOrderPriority ToPriority(string value) => value switch
    {
        WorkOrderPriorities.Low => WorkOrderPriority.Низкий,
        WorkOrderPriorities.Medium => WorkOrderPriority.Средний,
        WorkOrderPriorities.High => WorkOrderPriority.Высокий,
        WorkOrderPriorities.Emergency => WorkOrderPriority.Критический,
        _ => throw ApiException.BadRequest(
            $"Неизвестный приоритет «{value}». Допустимо: {WorkOrderPriorities.AllText}."),
    };

    // Статусы в базе — русские значения enum, их же отдаём клиенту:
    // контракт один и тот же для БД и для JSON.
    public static string StatusText(WorkOrderStatus status) => status switch
    {
        WorkOrderStatus.Создана => WorkOrderStatuses.Draft,
        WorkOrderStatus.Назначена => WorkOrderStatuses.Assigned,
        WorkOrderStatus.ВРаботе => WorkOrderStatuses.InProgress,
        WorkOrderStatus.ОжидаетМатериалов => WorkOrderStatuses.AwaitingMaterials,
        WorkOrderStatus.Выполнена => WorkOrderStatuses.Completed,
        WorkOrderStatus.Закрыта => WorkOrderStatuses.Closed,
        WorkOrderStatus.Отменена => WorkOrderStatuses.Cancelled,
        _ => WorkOrderStatuses.Draft,
    };

    public static string StatusText(WorkOrderPriority priority) => priority switch
    {
        WorkOrderPriority.Низкий => WorkOrderPriorities.Low,
        WorkOrderPriority.Средний => WorkOrderPriorities.Medium,
        WorkOrderPriority.Высокий => WorkOrderPriorities.High,
        WorkOrderPriority.Критический => WorkOrderPriorities.Emergency,
        _ => WorkOrderPriorities.Medium,
    };

    private static string Escape(string value) => value.Replace("%", string.Empty).Replace("_", string.Empty);
}