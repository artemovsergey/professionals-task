using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.Common;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
///     Выгрузка отчётов в PDF по временной ссылке.
/// </summary>
[ApiController]
[Route("api/reports")]
[Produces("application/json")]
[Authorize]
public sealed class ReportsController(IReportService reports) : ControllerBase
{
    /// <summary>Запросить временную ссылку на PDF-отчёт.</summary>
    /// <remarks>
    ///     Ссылка живёт 15 секунд — ровно столько дано в задании. Второй запрос
    ///     по той же ссылке после истечения срока возвращает 404.
    /// </remarks>
    /// <param name="dto">Тип отчёта и период.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpPost]
    [RequireRole(RoleCodes.Admin, RoleCodes.Manager)]
    public async Task<ActionResult<ApiResponse<ReportLink>>> Create(
        [FromBody] CreateReportDto dto,
        CancellationToken ct = default)
    {
        return Ok(ApiResponse<ReportLink>.Ok(
            await reports.CreateLinkAsync(dto, ct), "Ссылка на отчёт готова."));
    }

    /// <summary>Скачать отчёт по временной ссылке.</summary>
    /// <remarks>
    ///     Внутри собирается PDF и сразу отдаётся файлом: класть его в файловую систему
    ///     не нужно, отчёт живёт ровно столько, сколько живёт ссылка.
    /// </remarks>
    /// <param name="token">Токен из ссылки, выданной предыдущим запросом.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet("download/{token}")]
    public async Task<IActionResult> Download([FromRoute] string token, CancellationToken ct = default)
    {
        // Сервис возвращает параметры запроса одной строкой:
        // "тип|начало|конец|цех". Пустая строка означает, что токен не найден или истёк.
        var request = reports.ResolveToken(token);
        if (string.IsNullOrEmpty(request))
            throw new ApiException(
                StatusCodes.Status404NotFound,
                "Ссылка истекла. Запросите отчёт заново.",
                ErrorCodes.NotFound);

        var parts = request.Split('|');
        var kind = parts[0];
        var from = DateOnly.Parse(parts[1]);
        var to = DateOnly.Parse(parts[2]);
        var workshopId = Guid.TryParse(parts[3], out var parsed) ? parsed : (Guid?)null;

        var bytes = await reports.BuildAsync(kind, new DateRange(from, to), workshopId, ct);

        // Имя файла собираем здесь, а не в сервисе: HTTP-заголовок — дело контроллера.
        var fileName = $"toirprof-{kind}-{DateTime.Now:yyyyMMdd-HHmm}.pdf";
        return File(bytes, "application/pdf", fileName);
    }
}