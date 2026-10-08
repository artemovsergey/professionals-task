Сессия 2. Backend: регистрация и вход, JWT · 0–95 мин

# Что делаем на этой странице

Два маршрута — `POST /api/auth/register` и `POST /api/auth/login` — и настройка
JWT так, чтобы защищённые маршруты из [08-Изоляция-данных](08-Изоляция-данных)
и [09-CRUD-задач](09-CRUD-задач) вообще не открывались без токена.

Здесь же появляется первый настоящий пароль в системе: BCrypt-хеш в базе и
проверка пароля при входе.

# Шаг 1. Контракт запросов и ответа

`api/TaskPlanner.Api/Contracts/Contracts.cs`:

```csharp
public record RegisterRequest(string? Email, string? Password, string? FullName);
public record RegisterResponse(UserDto User);
public record LoginRequest(string? Email, string? Password);
public record LoginResponse(string Token, string TokenType, int ExpiresIn, UserDto User);

public record UserDto(long Id, string Email, string FullName);
```

Все поля входных записей — `string?`: nullable позволяет принять запрос с
неполным телом и ответить `400` с понятным кодом, а не `500` при разборе
JSON. Профиль возвращается отдельным `UserDto` без пароля и хеша — пароль не
покидает сервер ни при каких условиях.

![[images/api07-s1-contracts.png]]
*Contracts.cs: запросы, ответы и профиль пользователя без пароля*

# Шаг 2. Регистрация: валидация

`app.MapPost("/api/auth/register", ...)` в `Program.cs`:

```csharp
var errors = new List<string>();
if (string.IsNullOrWhiteSpace(req.Email) || !req.Email.Contains('@')) errors.Add("email");
if (string.IsNullOrWhiteSpace(req.FullName)) errors.Add("fullName");
if (string.IsNullOrWhiteSpace(req.Password) || req.Password.Length < 8) errors.Add("password");
if (errors.Count > 0)
    return Api.Fail(400, "Проверьте поля: " + string.Join(", ", errors), "VALIDATION_ERROR");
```

Все ошибки собираются **сразу**, а не по одной: пользователь не должен
делать пять попыток, чтобы узнать про все проблемы. Длина пароля — 8
символов, это же требование проверяется в тестах на
[25-Тест-кейсы-и-автотесты](25-Тест-кейсы-и-автотесты).

# Шаг 3. Регистрация: уникальность почты

```csharp
var email = req.Email!.Trim().ToLowerInvariant();
if (await db.Users.AnyAsync(u => u.Email == email))
    return Api.Fail(409, "Пользователь с такой почтой уже есть", "EMAIL_TAKEN");
```

`Trim()` и `ToLowerInvariant()` обязательны: иначе `Ivanov@college.ru` и
`ivanov@college.ru` станут двумя разными людьми, а ограничение
`uq_users_email` не сработает. Проверка идёт **до** вставки — иначе пришлось
бы ловить исключение уникальности.

# Шаг 4. Регистрация: пароль

```csharp
var user = new TaskPlanner.Api.Models.User
{
    Email = email,
    PasswordHash = BCrypt.Net.BCrypt.HashPassword(req.Password!),
    FullName = req.FullName!.Trim(),
};
db.Users.Add(user);
await db.SaveChangesAsync();
return Results.Json(Api.Envelope(user.ToDto()), statusCode: 201);
```

`HashPassword` даёт соль внутри хеша, поэтому два одинаковых пароля дают
разные строки в базе — это и нужно для защиты от радужных таблиц. В
`users.password_hash` попадает только результат хеширования; проверить
можно так:

```sql
SELECT email, left(password_hash, 7) FROM users;
-- 2b$10$…
```

![[images/api07-s2-register.png]]
*Program.cs: валидация, проверка уникальности и хеширование пароля*

# Шаг 5. Проверяем ответы регистрации

```bash
python3 tools/api-auth-demo.py | head -12
```

![[images/api07-s4-register-errors.png]]
*Три ответа подряд: 201 с профилем, 409 с EMAIL_TAKEN и 400 с VALIDATION_ERROR*

Три кода ответа означают разные вещи, и клиент обязан различать их:

| Ответ | Что произошло | Что делает клиент |
|---|---|---|
| `201` | пользователь создан | переходит к входу |
| `409` `EMAIL_TAKEN` | почта занята | предлагает вход, а не регистрацию |
| `400` `VALIDATION_ERROR` | плохие поля | подсвечивает конкретное поле |

Ошибка приходит в общем формате из
[06-Единый-формат-ответа-и-ошибки](06-Единый-формат-ответа-и-ошибки): `success`,
`data`, `message`, `error_code`. Клиенту не нужно разбирать текст сообщения —
достаточно `error_code`.

# Шаг 6. Вход и выпуск токена

```csharp
var email = (req.Email ?? string.Empty).Trim().ToLowerInvariant();
var user = await db.Users.FirstOrDefaultAsync(u => u.Email == email);
if (user is null || !BCrypt.Net.BCrypt.Verify(req.Password ?? string.Empty, user.PasswordHash))
    return Api.Fail(401, "Неверная почта или пароль", "INVALID_CREDENTIALS");
```

Одна проверка на два случая: несуществующая почта и неверный пароль дают
**одинаковый** ответ. Иначе по коду ответа можно перебрать, какие почты
зарегистрированы.

```csharp
var key = new SymmetricSecurityKey(
    System.Text.Encoding.UTF8.GetBytes(cfg["Jwt:Key"] ?? "dev-secret-key-…"));
var claims = new[]
{
    new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
    new Claim(ClaimTypes.Email, user.Email),
};
var token = new JwtSecurityToken(
    issuer: "taskplanner",
    audience: "taskplanner",
    claims: claims,
    expires: DateTime.UtcNow.AddHours(2),
    signingCredentials: new SigningCredentials(key, SecurityAlgorithms.HmacSha256));
```

В токен кладётся **только идентификатор** и почта. Все права определяются по
`userId`, который сервер берёт из токена, — клиент не может «повысить» свои
права, потому что подписать токен без ключа невозможно.

![[images/api07-s3-login.png]]
*Program.cs: проверка пароля BCrypt и выпуск токена на два часа*

# Шаг 7. Проверяем вход

```bash
python3 tools/api-auth-demo.py | sed -n '12,22p'
```

![[images/api07-s5-login.png]]
*Вход вернул токен и профиль, неверный пароль — 401 с INVALID_CREDENTIALS*

Токен живёт два часа. Когда он истечёт, API вернёт `401` даже с верными
данными — клиенту нужно уметь распознать это и отправить пользователя на
вход, а не показывать «что-то пошло не так».

# Шаг 8. Единый формат для 401 и 403

Kestrel сам отдаёт пустой ответ без тела, если не переопределить
`JwtBearerEvents`. Поэтому события заменяются:

```csharp
o.Events = new JwtBearerEvents
{
    OnChallenge = async ctx =>
    {
        ctx.HandleResponse();
        ctx.Response.StatusCode = 401;
        ctx.Response.ContentType = "application/json; charset=utf-8";
        await ctx.Response.WriteAsync(
            "{\"success\":false,\"data\":null,\"message\":\"Нужен Authorization: Bearer <токен>\",\"error_code\":\"UNAUTHORIZED\"}");
    },
    OnForbidden = async ctx =>
    {
        ctx.Response.StatusCode = 403;
        ctx.Response.ContentType = "application/json; charset=utf-8";
        await ctx.Response.WriteAsync(
            "{\"success\":false,\"data\":null,\"message\":\"Недостаточно прав\",\"error_code\":\"FORBIDDEN\"}");
    },
};
```

`ctx.HandleResponse()` обязателен: без него платформа допишет своё тело
поверх нашего. Теперь даже «запрет» приходит в том же формате, что и ошибки
валидации.

# Шаг 9. Кто я

```csharp
public static long CurrentUserId(ClaimsPrincipal user) =>
    long.Parse(user.FindFirst(ClaimTypes.NameIdentifier)!.Value);
```

Одна функция на весь проект. Все маршруты берут владельца только отсюда —
другого способа узнать, кто спрашивает, у обработчика нет. Подробнее на
[08-Изоляция-данных](08-Изоляция-данных).

# Сценарий целиком

Регистрация, вход и защищённый маршрут в Swagger UI — от вставки тела до
ответа с токеном:

![[gifs/api-scenario.gif]]
*Swagger: POST /api/auth/register → 201, затем вход и защищённый запрос с токеном*

# Коммит

```bash
git add api/TaskPlanner.Api
git commit -m "Backend: регистрация, вход, BCrypt и JWT с единым форматом 401/403"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `401` возвращается пустым телом | не переопределены `JwtBearerEvents` либо забыт `ctx.HandleResponse()` |
| `409` не ловится, вместо него `500` | проверка `AnyAsync` идёт после вставки; перенесите её выше |
| Один пароль хешируется одинаково дважды | используйте `BCrypt.HashPassword`, а не `ComputeHash` — соль обязательна |
| Токен не принимается на защищённом маршруте | проверьте `issuer`, `audience` и `ValidateLifetime`: все три значения должны совпадать с выданными |
| Токен проходит, но `userId` пустой | в claims нет `ClaimTypes.NameIdentifier` либо он назван иначе, чем ищет `CurrentUserId` |
| `403` вместо `401` при пустом токене | маршрут без `RequireAuthorization()` — добавьте его |