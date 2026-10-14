using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
///     Ремонтные бригады и их состав.
/// </summary>
[ApiController]
[Route("api/crews")]
[Produces("application/json")]
[Authorize]
public sealed class CrewsController(ICrewService service) : ControllerBase
{
    /// <summary>Список бригад с поиском и постраничностью.</summary>
    /// <param name="includeInactive">Включать отключённые бригады.</param>
    /// <param name="search">Поиск по названию и коду.</param>
    /// <param name="page">Номер страницы, начиная с 1.</param>
    /// <param name="pageSize">Размер страницы, от 1 до 100.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet]
    public async Task<ActionResult<ApiResponse<PagedResult<CrewShortDto>>>> List(
        [FromQuery] bool includeInactive = false,
        [FromQuery] string? search = null,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<PagedResult<CrewShortDto>>.Ok(
            await service.GetListAsync(includeInactive, search, page, pageSize, ct)));
    }

    /// <summary>Бригады для выпадающего списка — без пагинации.</summary>
    [HttpGet("select")]
    public async Task<ActionResult<ApiResponse<List<CrewShortDto>>>> Select(CancellationToken ct = default)
    {
        return Ok(ApiResponse<List<CrewShortDto>>.Ok(await service.GetForSelectAsync(ct)));
    }

    /// <summary>Карточка бригады: состав, загрузка и рейтинг.</summary>
    /// <param name="id">Идентификатор бригады.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ApiResponse<CrewDto>>> GetById([FromRoute] Guid id, CancellationToken ct = default)
    {
        return Ok(ApiResponse<CrewDto>.Ok(await service.GetByIdAsync(id, ct)));
    }

    /// <summary>Создать бригаду.</summary>
    [HttpPost]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<CrewDto>>> Create(
        [FromBody] CreateCrewDto dto,
        CancellationToken ct = default)
    {
        var crew = await service.CreateAsync(dto, ct);
        return CreatedAtAction(nameof(GetById), new { id = crew.Id }, ApiResponse<CrewDto>.Ok(crew));
    }

    /// <summary>Изменить название, специализацию или активность бригады.</summary>
    [HttpPut("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<CrewDto>>> Update(
        [FromRoute] Guid id,
        [FromBody] UpdateCrewDto dto,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<CrewDto>.Ok(await service.UpdateAsync(id, dto, ct)));
    }

    /// <summary>Удалить бригаду, на которую не ссылается ни одна заявка.</summary>
    [HttpDelete("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse>> Delete([FromRoute] Guid id, CancellationToken ct = default)
    {
        await service.DeleteAsync(id, ct);
        return Ok(ApiResponse.Ok("Бригада удалена."));
    }

    /// <summary>Добавить сотрудника в состав бригады.</summary>
    [HttpPost("{id:guid}/members")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<CrewDto>>> AddMember(
        [FromRoute] Guid id,
        [FromBody] AddCrewMemberDto dto,
        CancellationToken ct = default)
    {
        await service.AddMemberAsync(id, dto, ct);
        return Ok(ApiResponse<CrewDto>.Ok(await service.GetByIdAsync(id, ct), "Сотрудник добавлен в бригаду."));
    }

    /// <summary>Убрать сотрудника из состава бригады.</summary>
    /// <remarks>
    ///     Пока бригада ведёт заявку «В работе», убрать сотрудника нельзя:
    ///     заявка осталась бы без исполнителя.
    /// </remarks>
    [HttpDelete("{id:guid}/members/{userId:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<CrewDto>>> RemoveMember(
        [FromRoute] Guid id,
        [FromRoute] Guid userId,
        CancellationToken ct = default)
    {
        await service.RemoveMemberAsync(id, userId, ct);
        return Ok(ApiResponse<CrewDto>.Ok(await service.GetByIdAsync(id, ct), "Сотрудник убран из бригады."));
    }
}