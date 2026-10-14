using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
///     Справочник материалов и запасных частей.
/// </summary>
[ApiController]
[Route("api/materials")]
[Produces("application/json")]
[Authorize]
public sealed class MaterialsController(IMaterialService service) : ControllerBase
{
    /// <summary>Список материалов с поиском, фильтром дефицита и постраничностью.</summary>
    /// <param name="includeInactive">Включать отключённые материалы.</param>
    /// <param name="search">Поиск по артикулу и названию.</param>
    /// <param name="onlyShortage">Только позиции, у которых остаток ниже минимального.</param>
    /// <param name="page">Номер страницы, начиная с 1.</param>
    /// <param name="pageSize">Размер страницы, от 1 до 100.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet]
    public async Task<ActionResult<ApiResponse<PagedResult<MaterialDto>>>> List(
        [FromQuery] bool includeInactive = false,
        [FromQuery] string? search = null,
        [FromQuery] bool onlyShortage = false,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<PagedResult<MaterialDto>>.Ok(
            await service.GetListAsync(includeInactive, search, onlyShortage, page, pageSize, ct)));
    }

    /// <summary>Материалы для выпадающего списка при списании в заявку.</summary>
    [HttpGet("select")]
    public async Task<ActionResult<ApiResponse<List<MaterialDto>>>> Select(CancellationToken ct = default)
    {
        return Ok(ApiResponse<List<MaterialDto>>.Ok(await service.GetForSelectAsync(ct)));
    }

    /// <summary>Дефицитные позиции: остаток ниже минимального.</summary>
    [HttpGet("shortages")]
    public async Task<ActionResult<ApiResponse<List<MaterialShortageDto>>>> Shortages(CancellationToken ct = default)
    {
        return Ok(ApiResponse<List<MaterialShortageDto>>.Ok(await service.GetShortagesAsync(ct)));
    }

    /// <summary>Карточка материала.</summary>
    /// <param name="id">Идентификатор материала.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ApiResponse<MaterialDto>>> GetById(
        [FromRoute] Guid id,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<MaterialDto>.Ok(await service.GetByIdAsync(id, ct)));
    }

    /// <summary>Добавить материал в справочник.</summary>
    [HttpPost]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<MaterialDto>>> Create(
        [FromBody] CreateMaterialDto dto,
        CancellationToken ct = default)
    {
        var material = await service.CreateAsync(dto, ct);
        return CreatedAtAction(nameof(GetById), new { id = material.Id }, ApiResponse<MaterialDto>.Ok(material));
    }

    /// <summary>Изменить характеристики материала.</summary>
    /// <remarks>Остаток здесь не меняется: приход делает отдельный метод, а расход — списание в заявку.</remarks>
    [HttpPut("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<MaterialDto>>> Update(
        [FromRoute] Guid id,
        [FromBody] UpdateMaterialDto dto,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<MaterialDto>.Ok(await service.UpdateAsync(id, dto, ct)));
    }

    /// <summary>Удалить материал, который ещё не списывали в заявках.</summary>
    [HttpDelete("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse>> Delete([FromRoute] Guid id, CancellationToken ct = default)
    {
        await service.DeleteAsync(id, ct);
        return Ok(ApiResponse.Ok("Материал удалён из справочника."));
    }

    /// <summary>Приход на склад.</summary>
    /// <param name="id">Идентификатор материала.</param>
    /// <param name="dto">Количество поступления.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpPost("{id:guid}/receipt")]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<MaterialDto>>> ReceiveStock(
        [FromRoute] Guid id,
        [FromBody] StockReceiptDto dto,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<MaterialDto>.Ok(
            await service.ReceiveStockAsync(id, dto, ct), "Материал принят на склад."));
    }
}