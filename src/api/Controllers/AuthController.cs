using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Api.Services;
using ToirProf.Shared;
using AppDbContext = ToirProf.Api.Data.AppDbContext;

namespace ToirProf.Api.Controllers;

/// <summary>
/// Регистрация, вход и собственный профиль.
/// Открытые методы отдают токен, поэтому класс намеренно без [Authorize]:
/// требовать токен, чтобы его получить, нельзя.
/// </summary>
[ApiController]
[Route("api/auth")]
[Produces("application/json")]
public sealed class AuthController(IAuthService auth, AppDbContext db) : ControllerBase
{
    /// <summary>Регистрирует нового пользователя и выдаёт токен.</summary>
    /// <response code="201">Пользователь создан, токен выдан.</response>
    /// <response code="400">Логин уже занят либо в системе нет роли ADMIN.</response>
    [HttpPost("register")]
    [ProducesResponseType(typeof(ApiResponse<TokenResponse>), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status409Conflict)]
    public async Task<ActionResult<ApiResponse<TokenResponse>>> Register(
        [FromBody] RegisterDto dto,
        CancellationToken ct)
    {
        var result = await auth.RegisterAsync(dto, ct);

        return StatusCode(
            StatusCodes.Status201Created,
            ApiResponse<TokenResponse>.Ok(result, "Регистрация выполнена"));
    }

    /// <summary>Проверяет пароль и выдаёт токен.</summary>
    /// <response code="200">Вход выполнен.</response>
    /// <response code="403">Учётная запись отключена.</response>
    /// <response code="404">Неверный логин или пароль.</response>
    [HttpPost("login")]
    [ProducesResponseType(typeof(ApiResponse<TokenResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status403Forbidden)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ApiResponse<TokenResponse>>> Login(
        [FromBody] LoginDto dto,
        CancellationToken ct)
    {
        var result = await auth.LoginAsync(dto, ct);

        return Ok(ApiResponse<TokenResponse>.Ok(result, "Вход выполнен"));
    }

    /// <summary>Профиль пользователя, которому принадлежит токен.</summary>
    /// <response code="200">Профиль текущего пользователя.</response>
    /// <response code="401">Токен не передан или истёк.</response>
    /// <response code="403">В токене нет идентификатора либо учётная запись отключена.</response>
    [HttpGet("me")]
    [Authorize]
    [ProducesResponseType(typeof(ApiResponse<UserDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(typeof(ApiResponse<object>), StatusCodes.Status403Forbidden)]
    public async Task<ActionResult<ApiResponse<UserDto>>> Me(CancellationToken ct)
    {
        var rawId = User.FindFirstValue(ClaimTypes.NameIdentifier);

        // Идентификатор кладём в токен сами, поэтому его отсутствие —
        // это либо подделка, либо токен, выпущенный другой версией
        // сервиса. Оба случая — отказ, а не пустой профиль.
        if (!Guid.TryParse(rawId, out var userId))
        {
            throw ApiException.Forbidden("Токен не содержит идентификатора пользователя.");
        }

        var profile = await ReadProfileAsync(userId, ct);

        return Ok(ApiResponse<UserDto>.Ok(profile, "Профиль текущего пользователя"));
    }

    /// <summary>
    /// Собирает профиль из базы, а не из claim'ов токена: в токене может
    /// остаться старая роль или «полное имя» сотрудника, которого уже
    /// отключили. База — единственный источник истины, а запрос лёгкий.
    /// </summary>
    private async Task<UserDto> ReadProfileAsync(Guid userId, CancellationToken ct)
    {
        var user = await db.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Id == userId, ct)
            ?? throw ApiException.Forbidden("Учётная запись не найдена.");

        if (!user.IsActive)
        {
            throw ApiException.Forbidden("Учётная запись отключена.");
        }

        var roleCode = await db.Roles
            .AsNoTracking()
            .Where(r => r.Id == user.RoleId)
            .Select(r => r.Code)
            .FirstOrDefaultAsync(ct) ?? string.Empty;

        var crews = await db.CrewMembers
            .AsNoTracking()
            .Where(m => m.UserId == userId)
            .Select(m => m.Crew.Name)
            .OrderBy(name => name)
            .ToListAsync(ct);

        return new UserDto(
            user.Id,
            user.Username,
            user.FullName,
            roleCode,
            user.IsActive,
            crews,
            user.CreatedAt);
    }
}