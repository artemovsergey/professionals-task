using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
///     Аналитика: простои, эффективность бригад, расход материалов и выполнение плана ТО.
/// </summary>
[ApiController]
[Route("api/analytics")]
[Produces("application/json")]
[Authorize]
public sealed class AnalyticsController(IDashboardService dashboard) : ControllerBase
{
    /// <summary>Полный отчёт за период — пять блоков аналитики в одном ответе.</summary>
    /// <remarks>
    ///     Клиент запрашивает его один раз и раскладывает по вкладкам: пять отдельных
    ///     запросов означали бы пять одинаковых выборок из одних и тех же таблиц.
    /// </remarks>
    /// <param name="from">Начало периода; по умолчанию — 30 дней назад.</param>
    /// <param name="to">Конец периода; по умолчанию — сегодня.</param>
    /// <param name="workshopId">Ограничить отчёт одним цехом.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<AnalyticsReport>>> Report(
        [FromQuery] DateOnly? from = null,
        [FromQuery] DateOnly? to = null,
        [FromQuery] Guid? workshopId = null,
        CancellationToken ct = default)
    {
        var report = await dashboard.GetAnalyticsAsync(new DateRange(from, to), workshopId, ct);
        return Ok(ApiResponse<AnalyticsReport>.Ok(report));
    }
}