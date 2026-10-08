Сессия 4. Backend: логирование и Swagger · 135–150 мин

# Что делаем на этой странице

Доводим API до состояния, в котором его можно показать: каждый запрос
попадает в лог одной строкой, а контракт виден в Swagger UI и проверяется
кнопкой **Authorize** — без ручного копирования заголовков.

# Шаг 1. Логируем каждый запрос

В `api/TaskPlanner.Api/Program.cs` сразу после `builder.Build()`:

```csharp
app.Use(async (context, next) =>
{
    var started = DateTimeOffset.UtcNow;

    try
    {
        await next();
    }
    finally
    {
        var elapsed = DateTimeOffset.UtcNow - started;

        app.Logger.LogInformation(
            "{Method} {Path} -> {Status} за {Elapsed} мс",
            context.Request.Method,
            context.Request.Path,
            context.Response.StatusCode,
            (long)elapsed.TotalMilliseconds);
    }
});
```

Четыре решения, из-за которых строка лога полезна:

- `finally`, а не код после `await next()` — время считается и для запроса,
  который упал с исключением.
- Пишутся **код ответа**, а не «200»: по логу видно, откуда прилетели 401 и 404.
- Токен и тела запросов не пишутся: в заголовке `Authorization` пароль, и
  лог перестаёт быть безопасным.
- Время в миллисекундах — видно, какой маршрут медленный.

Уровни логов задаются в `appsettings.json`:

```json
"Logging": {
  "LogLevel": {
    "Default": "Information",
    "Microsoft.AspNetCore": "Warning",
    "Microsoft.EntityFrameworkCore.Database.Command": "Warning"
  }
}
```

`Microsoft.EntityFrameworkCore.Database.Command` на `Warning` — иначе каждая
выборка из базы пишется в лог целиком, и найти в нём что-либо невозможно.

![[images/api12-s1-logging.png]]
*Program.cs: логирование запроса и рядом — настройки сериализации и Swagger*

# Шаг 2. Смотрим лог вживую

Запустите API в терминале и сделайте два запроса — вход и список задач:

```bash
cd api/TaskPlanner.Api
dotnet run
```

```bash
TOKEN=$(curl -s -X POST http://localhost:5099/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ivanov@college.ru","password":"Password123"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["token"])')

curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:5099/api/tasks?pageSize=3"
```

![[images/api12-s2-logs.png]]
*В логе видно и вход, и список: POST /api/auth/login -> 200 за 1644 мс, GET /api/tasks -> 200 за 172 мс*

Вход медленнее списка неслучайно: он хеширует пароль и пишет пользователя в
базу. Такой разрыв в миллисекундах — самая дешёвая подсказка, где искать
проблему.

Если API запущен в Docker, лог смотрится той же командой:

```bash
docker compose logs -f api
```

# Шаг 3. Включаем Swagger

```csharp
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(o =>
{
    o.SwaggerDoc("v1", new() { Title = "Планировщик личных задач — API", Version = "v1" });
```

```csharp
app.UseSwagger();
app.UseSwaggerUI(o =>
{
    o.SwaggerEndpoint("/swagger/v1/swagger.json", "Планировщик личных задач v1");
    o.DocumentTitle = "Планировщик личных задач — API";
});
```

`AddEndpointsApiExplorer()` обязателен: без него Swagger не увидит маршруты,
объявленные через `MapGet`/`MapPost`, и страница будет пустой.

![[images/api12-swagger.png]]
*Swagger UI: все маршруты собраны в группы, схемы ответов подписаны*

# Шаг 4. Авторизация в Swagger

Чтобы кнопка **Authorize** появилась, в контракт добавляется схема
`bearerAuth`:

```csharp
o.AddSecurityDefinition("bearerAuth", new()
{
    Type = Microsoft.OpenApi.Models.SecuritySchemeType.Http,
    Scheme = "bearer",
    BearerFormat = "JWT",
    In = Microsoft.OpenApi.Models.ParameterLocation.Header,
    Description = "Вставьте токен из /api/auth/login",
});
```

И требование безопасности, которое применяет её ко всем маршрутам:

```csharp
o.AddSecurityRequirement(new()
{
    [new Microsoft.OpenApi.Models.OpenApiSecurityScheme
    {
        Reference = new Microsoft.OpenApi.Models.OpenApiReference
        {
            Type = Microsoft.OpenApi.Models.ReferenceType.SecurityScheme,
            Id = "bearerAuth",
        },
    }] = Array.Empty<string>(),
});
```

Открывайте `http://localhost:5099/swagger`, жмите **Authorize**, вставляйте
токен из `POST /api/auth/login` и выполняйте `GET /api/tasks` прямо из
браузера.

![[images/api12-swagger-authorize.png]]
*После Authorize защищённые маршруты отправляют запросы с токеном — 401 больше не появляется*

# Шаг 5. Русский текст в ответах

По умолчанию System.Text.Json превращает русские буквы в `\uXXXX` — в Swagger
такой ответ нечитаем:

```csharp
o.SerializerOptions.Encoder =
    System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping;
```

Плюс `PropertyNamingPolicy = JsonNamingPolicy.CamelCase`, чтобы имена полей
совпадали с теми, что ждёт клиент.

# Что добавить сверх эталона

В эталоге логи идут в stdout контейнера, а описания маршрутов — только
заголовком SwaggerDoc. Три вещи обычно добавляют на региональном этапе:

- **Файловые логи.** `builder.Host.UseSerilog()` с пакетами
  `Serilog.Sinks.Console` и `Serilog.Sinks.File`, чтобы лог переживал перезапуск
  контейнера. Обязательно проверьте, что в файле нет `password` и `Bearer`.
- **XML-комментарии.** `GenerateDocumentationFile` в `.csproj` плюс
  `IncludeXmlComments(...)` — тогда в Swagger видны описания методов и
  допустимые значения параметров (`status`, `priority`, `sort`).
- **Correlation ID.** В лог добавляется идентификатор запроса, а в ответ —
  заголовок `X-Request-Id`. Нагрузочный тест потом читается построчно.

# Проверка

```bash
# секретов в логе нет
docker compose logs api | grep -c "Password123\|Bearer eyJ"
# 0

# Swagger отдаёт контракт
curl -s http://localhost:5099/swagger/v1/swagger.json | head -c 120
```

Откройте `http://localhost:5099/swagger`: у каждого маршрута есть схема
ответа, кнопка **Authorize** работает, после авторизации `GET /api/tasks`
возвращает `200`, а без токена — `401` в общем формате из
[06-Единый-формат-ответа-и-ошибки](06-Единый-формат-ответа-и-ошибки).

# Коммит

```bash
git add api/TaskPlanner.Api/Program.cs api/TaskPlanner.Api/appsettings.json
git commit -m "Backend: логирование запросов и Swagger с авторизацией по токену"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| В логе пусто | `app.Use(...)` должен стоять после `builder.Build()` и до маршрутов; проверьте `LogLevel.Default` в `appsettings.json` |
| Лог на каждое обращение к БД | `Microsoft.EntityFrameworkCore.Database.Command` переведите в `Warning` |
| Swagger UI пустой | добавьте `AddEndpointsApiExplorer()` — без него маршруты `MapGet` не видны |
| Нет кнопки Authorize | в `AddSwaggerGen` нет `AddSecurityDefinition` или `AddSecurityRequirement` |
| Вместо задач приходит `401` | токен вставлен с пробелом или истёк: он живёт 2 часа, получите новый через `/api/auth/login` |
| Русский текст как `Ð°ÑƒÐ°Ð¹` | не задан `JavaScriptEncoder.UnsafeRelaxedJsonEscaping` |