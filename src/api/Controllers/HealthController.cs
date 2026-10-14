using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ToirProf.Shared;

namespace ToirProf.Api.Controllers;

/// <summary>Проверка живости сервиса.</summary>
[ApiController]
[Route("api/health")]
[Produces("application/json")]
[AllowAnonymous]
public sealed class HealthController : ControllerBase
{
    /// <summary>
    /// Отвечает без обращения к базе: проверяет, что процесс запущен и
    /// конвейер запросов работает.
    /// </summary>
    /// <remarks>
    /// Эндпоинт намеренно не ходит в базу. Проверять её доступность —
    /// задача мониторинга. Если связать её с этим же ответом, то при
    /// падении базы health-check начнёт отдавать ошибку, и по нему
    /// нельзя будет отличить «сервер лежит» от «база недоступна».
    /// </remarks>
    [HttpGet]
    public ActionResult<ApiResponse<HealthStatus>> Get()
        => Ok(ApiResponse<HealthStatus>.Ok(new(
            Status: "ok",
            Service: "toirprof-api",
            UtcNow: DateTimeOffset.UtcNow)));

    /// <summary>Состояние службы и время сервера.</summary>
    /// <param name="Status">Всегда «ok» — иначе сервис не ответил бы.</param>
    /// <param name="Service">Имя службы для мониторинга.</param>
    /// <param name="UtcNow">Время сервера, помогает заметить расхождение часов.</param>
    public sealed record HealthStatus(string Status, string Service, DateTimeOffset UtcNow);
}