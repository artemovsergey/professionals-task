using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
/// Справочник видов планового обслуживания.
/// </summary>
[ApiController]
[Route("api/maintenance-types")]
[Produces("application/json")]
[Authorize]
public sealed class MaintenanceTypesController(IMaintenanceTypesService service) : ControllerBase
{
    /// <summary>Список видов обслуживания; по умолчанию только активные.</summary>
    [HttpGet]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<MaintenanceTypeDto>>>> List(
        [FromQuery] bool includeInactive = false,
        CancellationToken ct = default)
        => Ok(ApiResponse<IReadOnlyList<MaintenanceTypeDto>>.Ok(
            await service.GetListAsync(includeInactive, ct)));

    /// <summary>Карточка вида обслуживания.</summary>
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ApiResponse<MaintenanceTypeDto>>> GetById(Guid id, CancellationToken ct)
        => Ok(ApiResponse<MaintenanceTypeDto>.Ok(await service.GetByIdAsync(id, ct)));

    /// <summary>Добавить вид обслуживания.</summary>
    [HttpPost]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<MaintenanceTypeDto>>> Create(
        [FromBody] CreateMaintenanceTypeDto dto,
        CancellationToken ct)
        => Created("/api/maintenance-types",
            ApiResponse<MaintenanceTypeDto>.Ok(await service.CreateAsync(dto, ct), "Вид обслуживания добавлен."));

    /// <summary>Изменить вид обслуживания.</summary>
    [HttpPut("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse<MaintenanceTypeDto>>> Update(
        Guid id,
        [FromBody] UpdateMaintenanceTypeDto dto,
        CancellationToken ct)
        => Ok(ApiResponse<MaintenanceTypeDto>.Ok(await service.UpdateAsync(id, dto, ct), "Справочник сохранён."));

    /// <summary>
    /// Снять отметку «активен» вместо удаления.
    /// </summary>
    /// <remarks>
    /// Справочник, который уже использовали в графике или заявках,
    /// удалить нельзя: на него ссылаются прошлые периоды. Деактивация
    /// оставляет старые записи читаемыми и запрещает новые.
    /// </remarks>
    [HttpDelete("{id:guid}")]
    [RequireRole(RoleCodes.Admin)]
    public async Task<ActionResult<ApiResponse>> Deactivate(Guid id, CancellationToken ct)
    {
        await service.DeactivateAsync(id, ct);
        return Ok(ApiResponse.Ok("Вид обслуживания деактивирован."));
    }
}