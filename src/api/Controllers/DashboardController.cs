using System.Text.Json;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Api.DTOs;
using ToirProf.Api.Services;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>
///     Дашборд руководителя: сводные показатели и поток обновлений.
/// </summary>
[ApiController]
[Route("api/dashboard")]
[Produces("application/json")]
[Authorize]
public sealed class DashboardController(IDashboardService dashboard) : ControllerBase
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    /// <summary>Сводные показатели за период: карточки, срезы по цехам, статусам и месяцам.</summary>
    /// <param name="from">Начало периода; по умолчанию — 30 дней назад.</param>
    /// <param name="to">Конец периода; по умолчанию — сегодня.</param>
    /// <param name="ct">Токен отмены запроса.</param>
    [HttpGet("summary")]
    public async Task<ActionResult<ApiResponse<DashboardSummary>>> Summary(
        [FromQuery] DateOnly? from = null,
        [FromQuery] DateOnly? to = null,
        CancellationToken ct = default)
    {
        var summary = await dashboard.GetSummaryAsync(new DateRange(from, to), ct);
        return Ok(ApiResponse<DashboardSummary>.Ok(summary));
    }

    /// <summary>
    ///     Поток обновлений дашборда (Server-Sent Events).
    /// </summary>
    /// <remarks>
    ///     Клиент подписывается один раз и дальше получает новые цифры без перезапроса.
    ///     Если события долго нет, сервер шлёт <c>dashboard.ping</c> — по нему клиент понимает,
    ///     что соединение живо. Тот же механизм служит индикатором статуса соединения.
    /// </remarks>
    [HttpGet("events")]
    [Produces("text/event-stream")]
    public async Task Events(
        [FromQuery] DateOnly? from = null,
        [FromQuery] DateOnly? to = null,
        CancellationToken ct = default)
    {
        Response.Headers.CacheControl = "no-cache";
        Response.Headers.Connection = "keep-alive";

        // Nginx и IIS любят буферизовать ответ: события до клиента доходят пачкой
        // раз в несколько секунд. Эта строка отключает буферизацию.
        Response.Headers["X-Accel-Buffering"] = "no";

        Response.ContentType = "text/event-stream";
        Response.StatusCode = StatusCodes.Status200OK;

        var period = new DateRange(from, to);
        var ping = TimeSpan.FromSeconds(25);

        await Response.WriteAsync(
            $"event: {DashboardEvent.UpdatedType}\ndata: {JsonSerializer.Serialize(await dashboard.GetSummaryAsync(period, ct), JsonOptions)}\n\n",
            ct);

        await Response.Body.FlushAsync(ct);

        var lastSent = DateTimeOffset.UtcNow;

        try
        {
            while (!ct.IsCancellationRequested)
            {
                await Task.Delay(TimeSpan.FromSeconds(10), ct);

                if (DateTimeOffset.UtcNow - lastSent < ping)
                    continue;

                var summary = await dashboard.GetSummaryAsync(period, ct);
                await Response.WriteAsync(
                    $"event: {DashboardEvent.UpdatedType}\ndata: {JsonSerializer.Serialize(summary, JsonOptions)}\n\n",
                    ct);
                await Response.Body.FlushAsync(ct);
                lastSent = DateTimeOffset.UtcNow;
            }
        }
        catch (OperationCanceledException)
        {
            // Клиент закрыл вкладку или потерял связь — это нормальное завершение,
            // а не ошибка: отмену пробрасывать не нужно.
        }
    }
}