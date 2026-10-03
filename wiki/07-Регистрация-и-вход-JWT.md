Сессия 3. Backend: авторизация · 0–95 мин

# 1. DTO авторизации (0–10 мин)

`src/api/TaskPlanner.Core/Dtos/AuthDtos.cs`:

```csharp
namespace TaskPlanner.Core.Dtos;

// ---------------------------------------------------------------------
// Запросы
// ---------------------------------------------------------------------
public class RegisterRequest
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
}

public class LoginRequest
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

// ---------------------------------------------------------------------
// Ответы
// ---------------------------------------------------------------------

/// <summary>
/// Пользователь для наружу. Пароля и хеша здесь нет и быть не должно:
/// если они появятся — их утечка станет возможной через любой endpoint.
/// </summary>
public class UserDto
{
    public long Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
}

public class LoginResponse
{
    public string Token { get; set; } = string.Empty;
    public string TokenType { get; set; } = "Bearer";
    public int ExpiresIn { get; set; }
    public UserDto User { get; set; } = new();
}
```

# 2. Валидаторы (10–20 мин)

`src/api/TaskPlanner.Core/Validators/AuthValidators.cs`:

```csharp
using FluentValidation;
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Core.Validators;

public class RegisterRequestValidator : AbstractValidator<RegisterRequest>
{
    public RegisterRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email обязателен")
            .MaximumLength(255).WithMessage("Email не длиннее 255 символов")
            .EmailAddress().WithMessage("Некорректный email");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Пароль обязателен")
            .MinimumLength(8).WithMessage("Пароль не короче 8 символов")
            .Matches("[A-Za-z]").WithMessage("Пароль должен содержать латинскую букву")
            .Matches("[0-9]").WithMessage("Пароль должен содержать цифру");

        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Имя обязательно")
            .MaximumLength(255).WithMessage("Имя не длиннее 255 символов")
            .Must(name => !string.IsNullOrWhiteSpace(name))
            .WithMessage("Имя не может состоять из пробелов");
    }
}

public class LoginRequestValidator : AbstractValidator<LoginRequest>
{
    public LoginRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email обязателен")
            .EmailAddress().WithMessage("Некорректный email");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Пароль обязателен");
    }
}
```

# 3. Хеширование паролей (20–30 мин)

Пароль **никогда** не хранится открытым. За критерии
«Пароли хранятся в открытом виде или хеш без соли» снимаются баллы.

`src/api/TaskPlanner.Core/Security/PasswordHasher.cs`:

```csharp
using BCrypt.Net;

namespace TaskPlanner.Core.Security;

/// <summary>
/// BCrypt: встроенная соль, настраиваемая стоимость, устойчив к
/// перебору на GPU. Все, что нужно помнить, — соль внутри хеша.
/// </summary>
public static class PasswordHasher
{
    /// <summary>Стоимость bcrypt. 11 — разумный компромисс для отбора.</summary>
    private const int WorkFactor = 11;

    public static string Hash(string password)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(password);

        // BCrypt работает с первыми 72 байтами — длинные пароли обрезаются.
        // Ограничиваем длину на входе, чтобы не было «молчаливого» усечения.
        if (password.Length > 72)
        {
            throw new ArgumentException("Пароль не длиннее 72 символов", nameof(password));
        }

        return BCrypt.Net.BCrypt.HashPassword(password, WorkFactor);
    }

    public static bool Verify(string password, string passwordHash)
    {
        if (string.IsNullOrEmpty(password) || string.IsNullOrEmpty(passwordHash))
        {
            return false;
        }

        try
        {
            return BCrypt.Net.BCrypt.Verify(password, passwordHash);
        }
        catch (BCrypt.Net.SaltParseException)
        {
            // В базе лежит не bcrypt-хеш (например, заглушка из seed.sql).
            return false;
        }
    }
}
```

# 4. Служба токенов (30–45 мин)

Опции JWT вынесите в отдельный класс, чтобы не размазывать `IConfiguration`
по коду:

`src/api/TaskPlanner.Core/Security/JwtOptions.cs`:

```csharp
namespace TaskPlanner.Core.Security;

public class JwtOptions
{
    public const string SectionName = "Jwt";

    public string Key { get; set; } = string.Empty;
    public string Issuer { get; set; } = string.Empty;
    public string Audience { get; set; } = string.Empty;
    public int ExpiresInMinutes { get; set; } = 60;
}
```

`src/api/TaskPlanner.Core/Security/IJwtTokenService.cs`:

```csharp
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Core.Security;

public interface IJwtTokenService
{
    LoginResponse CreateToken(Core.Entities.User user);
}
```

`src/api/TaskPlanner.Core/Security/JwtTokenService.cs`:

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using TaskPlanner.Core.Dtos;
using TaskPlanner.Core.Entities;

namespace TaskPlanner.Core.Security;

public class JwtTokenService(IOptions<JwtOptions> options) : IJwtTokenService
{
    private readonly JwtOptions _options = options.Value;

    public LoginResponse CreateToken(User user)
    {
        // Ключ короче 32 байт не подходит для HMAC-SHA256:
        // будет IDX10703 при старте.
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.Key));

        var expires = DateTime.UtcNow.AddMinutes(_options.ExpiresInMinutes);

        var claims = new List<Claim>
        {
            // Идентификатор пользователя. Именно он используется для
            // фильтрации задач, поэтому должен быть в токене.
            new(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new(JwtRegisteredClaimNames.Email, user.Email),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new(ClaimTypes.NameIdentifier, user.Id.ToString()),
        };

        var token = new JwtSecurityToken(
            issuer: _options.Issuer,
            audience: _options.Audience,
            claims: claims,
            notBefore: DateTime.UtcNow,
            expires: expires,
            signingCredentials: new SigningCredentials(key, SecurityAlgorithms.HmacSha256));

        return new LoginResponse
        {
            Token = new JwtSecurityTokenHandler().WriteToken(token),
            TokenType = "Bearer",
            ExpiresIn = _options.ExpiresInMinutes * 60,
            User = new UserDto
            {
                Id = user.Id,
                Email = user.Email,
                FullName = user.FullName,
            },
        };
    }
}
```

# 5. Регистрация в DI и аутентификация (45–65 мин)

Добавьте в `src/api/TaskPlanner.Api/Program.cs` **после** `builder.Services.AddControllers()`
и **до** `var app = builder.Build();`:

```csharp
// ---------------------------------------------------------------------
// Аутентификация и авторизация
// ---------------------------------------------------------------------
builder.Services.Configure<JwtOptions>(
    builder.Configuration.GetSection(JwtOptions.SectionName));

builder.Services.AddScoped<IJwtTokenService, JwtTokenService>();

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        var jwt = builder.Configuration
            .GetSection(JwtOptions.SectionName)
            .Get<JwtOptions>() ?? new JwtOptions();

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwt.Key));

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = key,

            ValidateIssuer = true,
            ValidIssuer = jwt.Issuer,

            ValidateAudience = true,
            ValidAudience = jwt.Audience,

            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30),

            // Не подставлять имя пользователя из токена по умолчанию:
            // нам нужен только идентификатор.
            NameClaimType = JwtRegisteredClaimNames.Sub,
        };

        options.Events = new JwtBearerEvents
        {
            // Ответ 401 должен быть в нашей обёртке, а не стандартный пустой
            OnChallenge = async context =>
            {
                context.HandleResponse();

                context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                context.Response.ContentType = "application/json; charset=utf-8";

                var response = ApiResponse<object?>.Fail(
                    "Требуется авторизация", ErrorCodes.Unauthorized);

                await context.Response.WriteAsync(
                    JsonSerializer.Serialize(response, new JsonSerializerOptions(JsonSerializerDefaults.Web)));
            },
        };
    });

builder.Services.AddAuthorization();
```

И добавьте два `using` в начало `Program.cs`:

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using TaskPlanner.Core.Security;
```

Затем в `Program.cs` вставьте две строки **после** `UseCors` и **до** Swagger:

```csharp
app.UseAuthentication();
app.UseAuthorization();
```

Порядок в конвейере теперь такой:

```csharp
app.UseMiddleware<ApiExceptionMiddleware>();
app.UseCors(CorsPolicy);
app.UseAuthentication();
app.UseAuthorization();
app.UseSwagger();
app.UseSwaggerUI(...);
app.MapControllers();
```

> **Замечание:** `UseAuthentication` должен идти раньше `UseAuthorization`,
> иначе `[Authorize]` не увидит principal. И оба — раньше `MapControllers`.

# 6. Сервис авторизации (65–80 мин)

Интерфейс живёт в `Core` — он не зависит ни от EF, ни от контекста:

`src/api/TaskPlanner.Core/Services/IAuthService.cs`:

```csharp
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Core.Services;

public interface IAuthService
{
    Task<UserDto> RegisterAsync(RegisterRequest request, CancellationToken cancellationToken);

    Task<LoginResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken);
}
```

> **Замечание:** `AppDbContext` лежит в проекте `Api`, поэтому реализация
> сервиса, которая ходит в базу, тоже должна быть в `Api`. Если написать её
> в `Core`, проект перестанет собираться: `Core` не ссылается на EF и не знает
> про `AppDbContext`. Интерфейс — в `Core`, реализация — в `Api`.

`src/api/TaskPlanner.Api/Services/AuthService.cs`:

```csharp
using Microsoft.EntityFrameworkCore;
using TaskPlanner.Api.Data;
using TaskPlanner.Core.Common;
using TaskPlanner.Core.Dtos;
using TaskPlanner.Core.Entities;
using TaskPlanner.Core.Exceptions;
using TaskPlanner.Core.Security;
using TaskPlanner.Core.Services;

namespace TaskPlanner.Api.Services;

public class AuthService(
    AppDbContext db,
    IJwtTokenService tokenService,
    ILogger<AuthService> logger) : IAuthService
{
    public async Task<UserDto> RegisterAsync(
        RegisterRequest request,
        CancellationToken cancellationToken)
    {
        var email = request.Email.Trim().ToLowerInvariant();

        var exists = await db.Users.AnyAsync(x => x.Email == email, cancellationToken);

        if (exists)
        {
            logger.LogInformation("Регистрация отклонена: email {Email} уже занят", email);

            throw ApiException.Conflict(
                ErrorCodes.EmailTaken,
                "Пользователь с таким email уже существует");
        }

        var user = new User
        {
            Email = email,
            PasswordHash = PasswordHasher.Hash(request.Password),
            FullName = request.FullName.Trim(),
            CreatedAt = DateTimeOffset.UtcNow,
        };

        db.Users.Add(user);
        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation("Зарегистрирован пользователь {UserId} ({Email})", user.Id, email);

        return new UserDto
        {
            Id = user.Id,
            Email = user.Email,
            FullName = user.FullName,
        };
    }

    public async Task<LoginResponse> LoginAsync(
        LoginRequest request,
        CancellationToken cancellationToken)
    {
        var email = request.Email.Trim().ToLowerInvariant();

        var user = await db.Users.FirstOrDefaultAsync(x => x.Email == email, cancellationToken);

        // Хеш считаем всегда, даже если пользователя нет: иначе по времени
        // ответа можно отличить «email не существует» от «неверный пароль».
        var hashToCheck = user?.PasswordHash
            ?? "$2a$11$0000000000000000000000000000000000000000000000000000";

        var passwordOk = PasswordHasher.Verify(request.Password, hashToCheck);

        if (user is null || !passwordOk)
        {
            logger.LogInformation("Неудачная попытка входа для {Email}", email);

            // Сообщение одинаковое в обоих случаях: не подсказываем,
            // существует ли такой email.
            throw ApiException.Unauthorized("Неверный email или пароль");
        }

        var response = tokenService.CreateToken(user);

        logger.LogInformation("Выполнен вход пользователя {UserId}", user.Id);

        return response;
    }
}
```

`PasswordHasher` — статический класс в `Core`. Если хотите внедрить его через
DI, сделайте из него интерфейс `IPasswordHasher` и зарегистрируйте
`services.AddSingleton<IPasswordHasher, BcryptPasswordHasher>()`; на отботе
статического класса достаточно.

Зарегистрируйте сервис в `Program.cs`:

```csharp
builder.Services.AddScoped<IAuthService, AuthService>();
```

# 7. Контроллер (80–95 мин)

`src/api/TaskPlanner.Api/Controllers/AuthController.cs`:

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Swashbuckle.AspNetCore.Annotations;
using TaskPlanner.Core.Services;
using TaskPlanner.Core.Common;
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Api.Controllers;

[ApiController]
[Route("api/auth")]
[AllowAnonymous]
public class AuthController(IAuthService authService) : ControllerBase
{
    /// <summary>Регистрация нового пользователя.</summary>
    [HttpPost("register")]
    [ProducesResponseType(typeof(ApiResponse<UserDto>), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Register(
        [FromBody] RegisterRequest request,
        CancellationToken cancellationToken)
    {
        var user = await authService.RegisterAsync(request, cancellationToken);

        var response = ApiResponse<UserDto>.Ok(user, "Пользователь создан");

        return Created($"/api/users/{user.Id}", response);
    }

    /// <summary>Вход и получение JWT-токена.</summary>
    [HttpPost("login")]
    [ProducesResponseType(typeof(ApiResponse<LoginResponse>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Login(
        [FromBody] LoginRequest request,
        CancellationToken cancellationToken)
    {
        var token = await authService.LoginAsync(request, cancellationToken);

        return Ok(ApiResponse<LoginResponse>.Ok(token, "Вход выполнен"));
    }
}
```

> **Замечание:** `[AllowAnonymous]` на контроллере обязателен — иначе
> глобальная политика авторизации закроет вход. В этом проекте глобальной
> политики нет, `[Authorize]` ставится на конкретные контроллеры, поэтому
> атрибут можно убрать. Оставьте его: на реальном проекте вход не должен
> требовать токен.

# Проверка

Запустите API: `dotnet run` в `src/api/TaskPlanner.Api`.

### 1. Регистрация

```bash
curl -i -X POST http://localhost:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@college.ru","password":"Passw0rd123","fullName":"Иван Петров"}'
```

```json
{
  "success": true,
  "data": { "id": 4, "email": "student1@college.ru", "fullName": "Иван Петров" },
  "message": "Пользователь создан",
  "error_code": null
}
```

Обратите внимание: в ответе нет `password` и `passwordHash`.

### 2. Повторная регистрация — 409

```bash
curl -i -X POST http://localhost:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@college.ru","password":"Passw0rd123","fullName":"Иван Петров"}'
```

```json
{
  "success": false,
  "data": null,
  "message": "Пользователь с таким email уже существует (traceId: 0HN...)",
  "error_code": "EMAIL_TAKEN"
}
```

### 3. Слабый пароль — 400

```bash
curl -i -X POST http://localhost:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"x@college.ru","password":"123","fullName":"Тест"}'
```

```json
{
  "success": false,
  "data": null,
  "message": "Пароль не короче 8 символов; Пароль должен содержать латинскую букву; Пароль должен содержать цифру (traceId: 0HN...)",
  "error_code": "VALIDATION_ERROR"
}
```

### 4. Вход — получаем токен

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@college.ru","password":"Passw0rd123"}'
```

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0IiwiZW1haWwiOiJzdHVk...",
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "user": { "id": 4, "email": "student1@college.ru", "fullName": "Иван Петров" }
  },
  "message": "Вход выполнен",
  "error_code": null
}
```

Сохраните токен в переменную — она понадобится дальше:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@college.ru","password":"Passw0rd123"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['token'])")
echo "$TOKEN"
```

### 5. Неверный пароль — 401

```bash
curl -i -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student1@college.ru","password":"WrongPassw0rd"}'
```

```json
{
  "success": false,
  "data": null,
  "message": "Неверный email или пароль (traceId: 0HN...)",
  "error_code": "UNAUTHORIZED"
}
```

### 6. Пароль в базе — только хеш

```sql
SELECT email, left(password_hash, 20) AS hash_prefix, length(password_hash) AS hash_len
FROM users WHERE email = 'student1@college.ru';
-- hash_prefix = $2a$11$xxxxx…   hash_len = 60
```

Хеш BCrypt начинается с `$2a$`, содержит соль и стоимость — 60 символов.
Открытого пароля в базе нет.

### 7. Swagger

Откройте `http://localhost:5000/swagger`, выполните `POST /api/auth/login`,
скопируйте `token`, нажмите **Authorize** и вставьте токен. Затем можно
вызывать защищённые методы.

# Коммит

```bash
git add src
git commit -m "Backend: регистрация, вход, хеш пароля BCrypt, JWT"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `IDX10703: Unable to create keyed hash` | `Jwt:Key` короче 32 символов. Сгенерируйте: `openssl rand -base64 48` |
| `IDX10501: Signature validation failed` | ключ в `JwtTokenService` и в `AddJwtBearer` разошлись; проверьте, что оба читают одну секцию `Jwt` |
| `System.Text.Json.JsonException: inProgress` | не зарегистрирован `TaskStatusConverter` в `AddJsonOptions` |
| Ответ 401 без обёртки | не сработал `OnChallenge` в `JwtBearerEvents`; проверьте `context.HandleResponse()` |
| Все ответы 401 даже с токеном | `UseAuthentication()` вызывается после `MapControllers()` или отсутствует |
| `BCrypt` не найден | пакет `BCrypt.Net-Next` добавлен в `Core`, а не в `Api` |
| `SaltParseException` при входе | в базе заглушка из `seed.sql` вместо bcrypt-хеша; заведите пользователя через API |
| 500 вместо 409 на дубликат email | добавьте `case DbUpdateException` для `UniqueViolation` в middleware (страница 06) |

# Что должно быть в репозитории к концу сессии 3, блок 1

- [ ] `RegisterRequest`, `LoginRequest`, `UserDto`, `LoginResponse`
- [ ] валидаторы с сообщениями на русском
- [ ] `PasswordHasher` на BCrypt с `WorkFactor = 11`
- [ ] `JwtOptions`, `JwtTokenService` с claim `sub`
- [ ] `AddAuthentication().AddJwtBearer()` + `UseAuthentication()`
- [ ] `AuthController` с `register` и `login`
- [ ] пароль не возвращается и не хранится открытым

## Иллюстрации

![[gifs/api-scenario.gif]]
*Полный сценарий в Swagger: регистрация, вход, токен, задача, сводка*
