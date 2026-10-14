using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using ToirProf.Shared;

namespace ToirProf.Api.Common;

/// <summary>
/// Проверка роли прямо на контроллере или методе.
///
/// Пример:
///     [ApiController]
///     [Route("api/equipment")]
///     [Authorize]
///     [RequireRole("ADMIN", "MANAGER")]
///     public sealed class EquipmentController : ControllerBase
///
/// Зачем отдельный атрибут, если есть [Authorize(Roles = "...")]:
/// роли в базе хранятся кодом (ADMIN), а политики в ASP.NET Core
/// сравнивают claim role как есть — это работает, но не даёт 403
/// с понятным телом ответа. Здесь 403 возвращается в обёртке API,
/// как и все остальные ошибки.
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = false)]
public sealed class RequireRoleAttribute(params string[] roles) : Attribute, IAuthorizationFilter
{
    private readonly string[] _roles = roles.Length > 0
        ? roles
        : [RoleCodes.Admin, RoleCodes.Manager, RoleCodes.Master];

    public void OnAuthorization(AuthorizationFilterContext context)
    {
        if (context.HttpContext.User.Identity?.IsAuthenticated != true)
        {
            return; // Не авторизован — это обработает проверка [Authorize].
        }

        var hasRole = context.HttpContext.User.Claims
            .Where(c => c.Type == ClaimTypes.Role)
            .Select(c => c.Value)
            .Any(role => _roles.Contains(role, StringComparer.OrdinalIgnoreCase));

        if (!hasRole)
        {
            context.Result = new ObjectResult(
                ApiResponse<object>.Fail(
                    "Недостаточно прав для выполнения операции.",
                    ErrorCodes.Forbidden))
            {
                StatusCode = StatusCodes.Status403Forbidden
            };
        }
    }
}

/// <summary>
/// Коды ролей из справочника roles. Константы, а не строковые литералы:
/// опечатка в строке проявилась бы только в рантайме на площадке.
/// </summary>
public static class RoleCodes
{
    public const string Admin = "ADMIN";

    public const string Manager = "MANAGER";

    public const string Master = "MASTER";
}