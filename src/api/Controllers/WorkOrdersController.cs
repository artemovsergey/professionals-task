// Контроллер заявок на ремонт и техническое обслуживание.
//
// Маршруты повторяют структуру спринтов 8–10 из плана:
//   GET    /api/work-orders              список с фильтрами, сортировкой и пагинацией
//   GET    /api/work-orders/select       краткие строки для выпадающих списков
//   GET    /api/work-orders/{id}         карточка заявки
//   GET    /api/work-orders/by-number/{number}
//   POST   /api/work-orders              создание, номер выдаёт сервис нумерации
//   PUT    /api/work-orders/{id}         правка незакрытой заявки
//   POST   /api/work-orders/{id}/crew    назначение бригады
//   POST   /api/work-orders/{id}/start   перевод в «В работе»
//   POST   /api/work-orders/{id}/complete завершение
//   POST   /api/work-orders/{id}/status  смена статуса по графу переходов
//   POST   /api/work-orders/{id}/materials списание материала
//   GET    /api/work-orders/{id}/cost    итоговая стоимость по списанию

using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

[ApiController]
[Route("api/work-orders")]
[Produces("application/json")]
[Authorize]
public sealed class WorkOrdersController(IWorkOrderService service) : ControllerBase
{
    /// <summary>Список заявок с фильтрами, сортировкой и пагинацией.</summary>
    /// <param name="equipmentId">Ограничить по единице оборудования.</param>
    /// <param name="crewId">Ограничить по бригаде.</param>
    /// <param name="status">Статус: Черновик, Назначена, В работе, Завершена, Отменена.</param>
    /// <param name="priority">Приоритет: Низкий, Средний, Высокий, Аварийный.</param>
    /// <param name="from">Начало периода по дате создания.</param>
    /// <param name="to">Конец периода по дате создания.</param>
    /// <param name="query">Поиск по номеру, названию и инвентарному номеру.</param>
    /// <param name="sort">Поле сортировки: createdAt, number, status, priority, plannedStart, downtime.</param>
    /// <param name="order">asc или desc.</param>
    /// <param name="page">Номер страницы, начиная с 1.</param>
    /// <param name="pageSize">Размер страницы, от 1 до 100.</param>
    [HttpGet]
    public async Task<ActionResult<ApiResponse<PagedResult<WorkOrderShortDto>>>> List(
        [FromQuery] Guid? equipmentId,
        [FromQuery] Guid? crewId,
        [FromQuery] string? status,
        [FromQuery] string? priority,
        [FromQuery] DateOnly? from,
        [FromQuery] DateOnly? to,
        [FromQuery] string? query,
        [FromQuery] string sort = "createdAt",
        [FromQuery] string order = "desc",
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
    {
        var result = await service.GetListAsync(
            new WorkOrderFilter(equipmentId, crewId, status, priority, from, to, query, sort, order, page, pageSize),
            ct);

        return Ok(ApiResponse<PagedResult<WorkOrderShortDto>>.Ok(result));
    }

    /// <summary>Краткие строки заявок для выпадающих списков клиентов.</summary>
    [HttpGet("select")]
    public async Task<ActionResult<ApiResponse<List<WorkOrderShortDto>>>> Select(
        [FromQuery] int limit = 50,
        CancellationToken ct = default)
    {
        var page = await service.GetListAsync(
            new WorkOrderFilter(null, null, null, null, null, null, null, "createdAt", "desc", 1, limit),
            ct);

        return Ok(ApiResponse<List<WorkOrderShortDto>>.Ok(page.Items.ToList()));
    }

    /// <summary>Карточка заявки: оборудование, бригада, материалы и история изменений.</summary>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> GetById(Guid id, CancellationToken ct)
    {
        var order = await service.GetByIdAsync(id, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order));
    }

    /// <summary>Карточка заявки по её номеру, например Z-2026-0047.</summary>
    [HttpGet("by-number/{number}")]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> GetByNumber(string number, CancellationToken ct)
    {
        var order = await service.GetByNumberAsync(number, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order));
    }

    /// <summary>Создать заявку. Номер вида Z-YYYY-XXXX выдаёт сервис нумерации.</summary>
    /// <param name="dto">Оборудование, тема, описание неисправности и приоритет.</param>
    /// <param name="userId">Автор заявки, берётся из профиля.</param>
    [HttpPost]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> Create(
        [FromBody] CreateWorkOrderDto dto,
        [FromQuery] Guid userId,
        CancellationToken ct)
    {
        var order = await service.CreateAsync(dto, userId, ct);
        return CreatedAtAction(nameof(GetById), new { id = order.Id }, ApiResponse<WorkOrderDto>.Ok(order, "Заявка создана."));
    }

    /// <summary>Изменить незакрытую заявку: тема, описание, приоритет, плановые даты.</summary>
    [HttpPut("{id:guid}")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> Update(
        Guid id,
        [FromBody] UpdateWorkOrderDto dto,
        CancellationToken ct)
    {
        var order = await service.UpdateAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Заявка обновлена."));
    }

    /// <summary>Назначить бригаду и исполнителя. Бригада не может вести две заявки «В работе».</summary>
    [HttpPost("{id:guid}/crew")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> AssignCrew(
        Guid id,
        [FromBody] AssignCrewDto dto,
        CancellationToken ct)
    {
        var order = await service.AssignCrewAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Бригада назначена."));
    }

    /// <summary>Перевести заявку в статус «В работе» с фактическим временем начала.</summary>
    [HttpPost("{id:guid}/start")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> Start(
        Guid id,
        [FromBody] StartWorkOrderDto dto,
        CancellationToken ct)
    {
        var order = await service.StartAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Работы начаты."));
    }

    /// <summary>Завершить заявку: фактическое время окончания и причина неисправности обязательны.</summary>
    [HttpPost("{id:guid}/complete")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> Complete(
        Guid id,
        [FromBody] CompleteWorkOrderDto dto,
        CancellationToken ct)
    {
        var order = await service.CompleteAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Заявка закрыта."));
    }

    /// <summary>Сменить статус по графу переходов. Неразрешённый переход даёт 409.</summary>
    [HttpPost("{id:guid}/status")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> ChangeStatus(
        Guid id,
        [FromBody] ChangeStatusDto dto,
        CancellationToken ct)
    {
        var order = await service.ChangeStatusAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Статус изменён."));
    }

    /// <summary>Списать материал на заявку. Остаток уменьшается, стоимость считает база.</summary>
    [HttpPost("{id:guid}/materials")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master)]
    public async Task<ActionResult<ApiResponse<WorkOrderDto>>> AddMaterial(
        Guid id,
        [FromBody] MaterialWriteOffDto dto,
        CancellationToken ct)
    {
        var order = await service.AddMaterialAsync(id, dto, ct);
        return Ok(ApiResponse<WorkOrderDto>.Ok(order, "Материал списан."));
    }

    /// <summary>Итоговая стоимость по заявке: сумма списанных позиций.</summary>
    [HttpGet("{id:guid}/cost")]
    public async Task<ActionResult<ApiResponse<MaterialCostDto>>> GetCost(Guid id, CancellationToken ct)
    {
        var cost = await service.GetCostAsync(id, ct);
        return Ok(ApiResponse<MaterialCostDto>.Ok(cost));
    }
}