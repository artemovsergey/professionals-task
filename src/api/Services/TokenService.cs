using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;
using ToirProf.Api.Data;

namespace ToirProf.Api.Services;

/// <summary>
/// Выпуск и проверка учётных данных: хеширование паролей
/// и подписание JWT. Вынесено в отдельный сервис, чтобы и контроллеры,
/// и фоновые задачи (сброс пароля, повторный выпуск токена) шифровали
/// и проверяли пароли одинаково.
/// </summary>
public interface ITokenService
{
    /// <summary>Выпускает подписанный JWT для пользователя с указанной ролью.</summary>
    /// <param name="user">Пользователь, от имени которого выдаётся токен.</param>
    /// <param name="roleCode">Код роли из справочника <c>roles</c>.</param>
    /// <returns>Строка JWT, готовая к отправке в заголовке Authorization.</returns>
    string CreateToken(User user, string roleCode);

    /// <summary>Хеширует пароль алгоритмом bcrypt.</summary>
    string HashPassword(string password);

    /// <summary>
    /// Проверяет пароль против значения из столбца <c>password_hash</c>.
    /// Поддерживает и bcrypt-хеш, и подставной формат из db/seed.sql.
    /// </summary>
    bool VerifyPassword(string password, string hash);
}

/// <inheritdoc />
public sealed class TokenService(IConfiguration configuration) : ITokenService
{
    // Префикс подставного значения из db/seed.sql: за ним лежит сам пароль.
    // См. пояснение в VerifyPassword.
    private const string SeedPasswordPrefix = "sha256$";

    // Настоящий bcrypt-хеш всегда начинается с версии алгоритма:
    // $2a$, $2b$ или $2y$. Проверка префикса заменяет перехват исключения.
    private const string BcryptPrefix = "$2";

    private const int DefaultLifetimeHours = 8;

    // HS256 подписывается симметричным ключом и требует не менее 256 бит.
    // Более короткий ключ библиотека примет молча, но подпись станет
    // подделываемой перебором, поэтому длину проверяем на старте.
    private const int MinimumKeyLengthBytes = 32;

    private readonly SymmetricSecurityKey _signingKey = ResolveSigningKey(configuration);

    private readonly int _lifetimeHours = ReadLifetimeHours(configuration);

    public string CreateToken(User user, string roleCode)
    {
        var now = DateTime.UtcNow;

        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new(ClaimTypes.Name, user.Username),
            new(ClaimTypes.Role, roleCode),

            // ФИО кладём отдельным claim: клиенту оно нужно в шапке и на
            // карточках, а искать пользователя ради одного поля — лишний запрос.
            new("full_name", user.FullName),
        };

        var token = new JwtSecurityToken(
            issuer: configuration["Jwt:Issuer"],
            audience: configuration["Jwt:Audience"],
            claims: claims,
            notBefore: now,
            expires: now.AddHours(_lifetimeHours),
            signingCredentials: new SigningCredentials(_signingKey, SecurityAlgorithms.HmacSha256));

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public string HashPassword(string password) => BCrypt.Net.BCrypt.HashPassword(password);

    /// <inheritdoc />
    public bool VerifyPassword(string password, string hash)
    {
        if (string.IsNullOrEmpty(hash))
        {
            return false;
        }

        // Формат db/seed.sql — «sha256$» и сам пароль открытым текстом.
        // Так сид запускается на «голом» PostgreSQL без расширений, и
        // демонстрационные учётки (admin/Admin123! и другие) работают сразу
        // после развёртывания. В рабочей системе такие значения заменяются
        // настоящими bcrypt-хешами, и ветка ниже просто перестаёт выбираться.
        if (hash.StartsWith(SeedPasswordPrefix, StringComparison.Ordinal))
        {
            var seedPassword = hash[SeedPasswordPrefix.Length..];

            return CryptographicOperations.FixedTimeEquals(
                Encoding.UTF8.GetBytes(seedPassword),
                Encoding.UTF8.GetBytes(password));
        }

        // Всё остальное считаем bcrypt-хешем. Префикс отсекаем заранее:
        // BCrypt.Verify бросает SaltParseException на мусоре, а try/catch
        // в сервисах запрещён — значит, негодный хеш должен отсеяться
        // до вызова, иначе клиент получил бы 500 вместо отказа во входе.
        return hash.StartsWith(BcryptPrefix, StringComparison.Ordinal)
            && BCrypt.Net.BCrypt.Verify(password, hash);
    }

    /// <summary>
    /// Параметры проверки токена на стороне API.
    ///
    /// Собираются здесь же рядом с выпуском токена: ключ и срок жизни
    /// должны читаться из одного места, иначе подпись и проверка
    /// со временем разъедутся.
    /// </summary>
    public TokenValidationParameters BuildValidationParameters() => new()
    {
        ValidateIssuer = true,
        ValidIssuer = configuration["Jwt:Issuer"],
        ValidateAudience = true,
        ValidAudience = configuration["Jwt:Audience"],
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = _signingKey,
        ValidateLifetime = true,

        // Штатные пять минут допуска слишком щедры: отключённый сотрудник
        // после смены пароля продолжал бы работать с уже выпущенным токеном.
        ClockSkew = TimeSpan.FromSeconds(30),
    };

    private static SymmetricSecurityKey ResolveSigningKey(IConfiguration configuration)
    {
        var key = configuration["Jwt:Key"];

        if (string.IsNullOrWhiteSpace(key))
        {
            throw new InvalidOperationException(
                "Не задан параметр Jwt:Key. Секрет подписи живёт в appsettings "
                + "или в переменной окружения Jwt__Key.");
        }

        var bytes = Encoding.UTF8.GetBytes(key);

        if (bytes.Length < MinimumKeyLengthBytes)
        {
            throw new InvalidOperationException(
                $"Ключ Jwt:Key короче {MinimumKeyLengthBytes} байт: алгоритм HS256 "
                + "подписывает им токен, и подделка станет перебором ключа.");
        }

        return new SymmetricSecurityKey(bytes);
    }

    private static int ReadLifetimeHours(IConfiguration configuration)
    {
        var raw = configuration["Jwt:LifetimeHours"];

        // При мусоре в конфигурации молча берём штатные восемь часов:
        // запрос входа не должен падать из-за опечатки в appsettings.
        return int.TryParse(raw, out var hours) && hours > 0
            ? hours
            : DefaultLifetimeHours;
    }
}