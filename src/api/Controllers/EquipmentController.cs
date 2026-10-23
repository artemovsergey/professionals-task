using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
/// Оборудование участка: справочник, карточка единицы, смена статуса.
/// </summary>
[ApiController]
[Route("api/equipment")]
[Produces("application/json")]
[Authorize]
public sealed class EquipmentController(IEquipmentService service) : ControllerBase
{
    /// <summary>
    /// Список оборудования с фильтрами, поиском и пагинацией.
    /// </summary>
    /// <remarks>
    /// По умолчанию выведенное из эксплуатации оборудование скрыто: оно
    /// занимало бы первые строки списка и мешало работать. Флаг
    /// <paramref name="includeRetired"/> возвращает его обратно.
    /// </remarks>
    [HttpGet]
    public async Task<ActionResult<ApiResponse<PagedResult<EquipmentShortDto>>>> List(
        [FromQuery] Guid? workshopId,
        [FromQuery] string? search,
        [FromQuery] string? status,
        [FromQuery] int criticality = 0,
        [FromQuery] bool includeRetired = false,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
        => Ok(ApiResponse<PagedResult<EquipmentShortDto>>.Ok(
            await service.GetListAsync(workshopId, search, status, criticality, includeRetired, page, pageSize, ct)));

    /// <summary>Краткий список для выпадающих списков, без пагинации.</summary>
    [HttpGet("select")]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<EquipmentShortDto>>>> Select(
        [FromQuery] Guid? workshopId,
        CancellationToken ct = default)
        => Ok(ApiResponse<IReadOnlyList<EquipmentShortDto>>.Ok(
            await service.GetForSelectAsync(workshopId, ct)));

    /// <summary>Карточка единицы оборудования.</summary>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ApiResponse<EquipmentDto>>> GetById(Guid id, CancellationToken ct)
        => Ok(ApiResponse<EquipmentDto>.Ok(await service.GetByIdAsync(id, ct)));

    /// <summary>Добавить единицу оборудования.</summary>
    [HttpPost]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<EquipmentDto>>> Create(
        [FromBody] CreateEquipmentDto dto,
        CancellationToken ct)
        => Created("/api/equipment",
            ApiResponse<EquipmentDto>.Ok(await service.CreateAsync(dto, ct), "Оборудование добавлено."));

    /// <summary>Изменить карточку оборудования.</summary>
    [HttpPut("{id:guid}")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<EquipmentDto>>> Update(
        Guid id,
        [FromBody] UpdateEquipmentDto dto,
        CancellationToken ct)
        => Ok(ApiResponse<EquipmentDto>.Ok(await service.UpdateAsync(id, dto, ct), "Карточка сохранена."));

    /// <summary>
    /// Сменить статус отдельно от остальных полей карточки.
    /// </summary>
    /// <remarks>
    /// Отдельный эндпоинт, а не поле в <c>UpdateEquipmentDto</c>. Правило
    /// «выведенное из эксплуатации оборудование нельзя вернуть в работу»
    /// проверяется триггером в базе; если смешать статус с остальными
    /// полями, пользователь получит ошибку 400 без указания, что именно
    /// не так, и решит, что форма сломана.
    /// </remarks>
    [HttpPatch("{id:guid}/status")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<EquipmentDto>>> ChangeStatus(
        Guid id,
        [FromBody] ChangeStatusRequest request,
        CancellationToken ct)
        => Ok(ApiResponse<EquipmentDto>.Ok(
            await service.ChangeStatusAsync(id, request.Status, ct), "Статус обновлён."));

    /// <summary>Удалить единицу оборудования, если она ещё не используется.</summary>
    [HttpDelete("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse>> Delete(Guid id, CancellationToken ct)
    {
        await service.DeleteAsync(id, ct);
        return Ok(ApiResponse.Ok("Оборудование удалено."));
    }
}

/// <summary>Тело запроса смены статуса оборудования.</summary>
/// <param name="Status">Одно из значений: В работе, В ремонте, В простое, Выведено из эксплуатации.</param>
public sealed record ChangeStatusRequest(string Status);