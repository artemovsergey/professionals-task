using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Common;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;

namespace ToirProf.Api.Services;

/// <summary>
/// Регистрация и вход. Возвращает готовый <see cref="TokenResponse"/>:
/// клиенту не нужно делать второй запрос за профилем сразу после входа.
/// </summary>
public interface IAuthService
{
    /// <summary>Заводит нового пользователя и сразу выпускает для него токен.</summary>
    Task<TokenResponse> RegisterAsync(RegisterDto dto, CancellationToken ct);

    /// <summary>Проверяет пароль и выпускает токен для существующего пользователя.</summary>
    Task<TokenResponse> LoginAsync(LoginDto dto, CancellationToken ct);
}

/// <inheritdoc />
public sealed class AuthService(AppDbContext db, ITokenService tokenService) : IAuthService
{
    public async Task<TokenResponse> RegisterAsync(RegisterDto dto, CancellationToken ct)
    {
        var username = dto.Username.Trim();

        var usernameTaken = await db.Users
            .AsNoTracking()
            .AnyAsync(u => u.Username.ToLower() == username.ToLower(), ct);

        if (usernameTaken)
        {
            throw ApiException.Conflict("Пользователь с таким логином уже существует.");
        }

        // Роль назначается строго ADMIN, поле RegisterDto.Role намеренно
        // игнорируется: если разрешить выбирать роль при регистрации,
        // любой посетитель заведёт себе администратора одной формой.
        // Роль выдаёт уже авторизованный сотрудник.
        var role = await db.Roles
            .AsNoTracking()
            .FirstOrDefaultAsync(r => r.Code == RoleCodes.Admin, ct);

        if (role is null)
        {
            throw ApiException.BadRequest("В системе не заведена роль ADMIN.");
        }

        var user = new User
        {
            Id = Guid.NewGuid(),
            Username = username,
            PasswordHash = tokenService.HashPassword(dto.Password),
            FullName = dto.FullName.Trim(),
            RoleId = role.Id,
            IsActive = true,
        };

        db.Users.Add(user);
        await db.SaveChangesAsync(ct);

        // created_at проставляет AppDbContext при сохранении, поэтому
        // профиль собираем после SaveChangesAsync.
        return Issue(user, role.Code, []);
    }

    public async Task<TokenResponse> LoginAsync(LoginDto dto, CancellationToken ct)
    {
        var username = dto.Username.Trim();

        var user = await db.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Username.ToLower() == username.ToLower(), ct);

        // Несуществующий логин и неверный пароль дают один и тот же ответ.
        // Иначе форма входа превращается в готовый инструмент перебора
        // учётных записей: достаточно сравнить коды 403 и 404.
        // Пароль проверяем раньше IsActive, чтобы отключённая учётная запись
        // не выдавала себя отдельным сообщением.
        if (user is null || !tokenService.VerifyPassword(dto.Password, user.PasswordHash))
        {
            throw ApiException.NotFound("Неверный логин или пароль.");
        }

        if (!user.IsActive)
        {
            throw ApiException.Forbidden("Учётная запись отключена.");
        }

        var roleCode = await db.Roles
            .AsNoTracking()
            .Where(r => r.Id == user.RoleId)
            .Select(r => r.Code)
            .FirstOrDefaultAsync(ct) ?? string.Empty;

        var crews = await ReadCrewNamesAsync(user.Id, ct);

        return Issue(user, roleCode, crews);
    }

    /// <summary>
    /// Коды бригад пользователя. Нужны клиенту, чтобы сразу ограничить
    /// интерфейс его участком и не показывать чужое.
    /// </summary>
    private Task<List<string>> ReadCrewNamesAsync(Guid userId, CancellationToken ct)
        => db.CrewMembers
            .AsNoTracking()
            .Where(m => m.UserId == userId)
            .Select(m => m.Crew.Name)
            .OrderBy(name => name)
            .ToListAsync(ct);

    private TokenResponse Issue(User user, string roleCode, List<string> crews)
        => new(
            tokenService.CreateToken(user, roleCode),
            TokenResponse.Bearer,
            TokenResponse.LifetimeSeconds,
            new UserDto(
                user.Id,
                user.Username,
                user.FullName,
                roleCode,
                user.IsActive,
                crews,
                user.CreatedAt));
}