Сессия 4. Backend: логирование и Swagger · 135–150 мин

# 1. Serilog (135–142 мин)

Замените начало `Program.cs` (после строки `var builder = WebApplication.CreateBuilder(args);`):

```csharp
// ---------------------------------------------------------------------
// Логирование
// ---------------------------------------------------------------------
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "TaskPlanner.Api")
    .CreateLogger();

builder.Host.UseSerilog();
```

Добавьте в `appsettings.json` секцию:

```json
{
  "Serilog": {
    "Using": [ "Serilog.Sinks.Console", "Serilog.Sinks.File" ],
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft.AspNetCore": "Warning",
        "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
        "System.Net.Http.HttpClient": "Warning"
      }
    },
    "Enrich": [ "FromLogContext" ],
    "WriteTo": [
      {
        "Name": "Console",
        "Args": {
          "outputTemplate": "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}"
        }
      },
      {
        "Name": "File",
        "Args": {
          "path": "logs/taskplanner-.log",
          "rollingInterval": "Day",
          "retainedFileCountLimit": 7,
          "outputTemplate": "{Timestamp:o} [{Level:u3}] {Application} {Message:lj} {Properties:j}{NewLine}{Exception}"
        }
      }
    ]
  }
}
```

Добавьте `logs/` в `.gitignore`:

```gitignore
logs/
```

# 2. Логирование запросов (142–146 мин)

`src/api/TaskPlanner.Api/Infrastructure/RequestLoggingMiddleware.cs`:

```csharp
using System.Diagnostics;

namespace TaskPlanner.Api.Infrastructure;

/// <summary>
/// Пишет по строке на каждый запрос: метод, путь, код ответа, время.
/// Тела запросов НЕ пишутся — в них пароль и токены.
/// </summary>
public class RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            await next(context);
        }
        finally
        {
            stopwatch.Stop();

            logger.LogInformation(
                "{Method} {Path} -> {StatusCode} за {Elapsed}мс (user: {UserId})",
                context.Request.Method,
                context.Request.Path.Value,
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds,
                context.User?.FindFirst("sub")?.Value ?? "-");
        }
    }
}
```

Вставьте в `Program.cs` **до** `UseSwagger`:

```csharp
app.UseMiddleware<RequestLoggingMiddleware>();
```

Порядок в конвейере:

```csharp
app.UseMiddleware<ApiExceptionMiddleware>();
app.UseMiddleware<RequestLoggingMiddleware>();
app.UseCors(CorsPolicy);
app.UseAuthentication();
app.UseAuthorization();
app.UseSwagger();
app.UseSwaggerUI(...);
app.MapControllers();
```

> **Замечание:** `ApiExceptionMiddleware` стоит первым, чтобы поймать
> исключения из логирующего middleware. А логирование — вторым, чтобы в лог
> попали и 4xx, и 5xx: если логирование окажется ниже обработчика ошибок,
> ответ с кодом 500 будет записан как «200» в момент входа в middleware.

# 3. Маскирование секретов (146–148 мин)

Проверьте, что пароли не попадают в лог. `AuthService` логирует только email:

```csharp
logger.LogInformation("Регистрация отклонена: email {Email} уже занят", email);
```

Правила, которых стоит придерживаться:

| Нельзя логировать | Можно |
|---|---|
| `Password`, `PasswordHash` | email, `userId` |
| `Authorization: Bearer ...` | код ответа, длительность |
| тело запроса `/api/auth/login` | `userId`, результат операции |
| полный `user` из EF вместе с `PasswordHash` | проекцию без хеша |

Если всё же нужен разбор тела запроса — маскируйте:

```csharp
logger.LogInformation(
    "Запрос {Method} {Path}, тело: {Body}",
    context.Request.Method,
    context.Request.Path.Value,
    MaskPasswords(context.Request.Body));
```

где `MaskPasswords` читает тело, заменяет значение поля `password` на
`***` и возвращает строку. Тело при этом нужно перечитать
(`context.Request.EnableBuffering()`), иначе тело будет пустым.

# 4. XML-комментарии и Swagger (148–150 мин)

В `src/api/TaskPlanner.Api/TaskPlanner.Api.csproj` добавьте:

```xml
  <PropertyGroup>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <!-- 1591: не все публичные члены документированы — это ожидаемо -->
    <NoWarn>$(NoWarn);1591</NoWarn>
  </PropertyGroup>
```

И в `AddSwaggerGen` добавьте подключение XML-файла:

```csharp
var xmlPath = Path.Combine(AppContext.BaseDirectory, "TaskPlanner.Api.xml");

if (File.Exists(xmlPath))
{
    options.IncludeXmlComments(xmlPath);
}
```

Чтобы Swagger видел параметры запроса и диапазоны значений, добавьте в
`AddSwaggerGen`:

```csharp
options.AddSecurityRequirement(
    new Microsoft.OpenApi.Models.OpenApiSecurityRequirement
    {
        [scheme] = Array.Empty<string>(),
    });
```

Чтобы в Swagger было видно допустимые значения параметров, опишите их прямо
в XML-комментарии над методом контроллера:

```csharp
/// <summary>Список задач с фильтрами и пагинацией.</summary>
/// <param name="status">new | in_progress | done | cancelled</param>
/// <param name="priority">low | medium | high</param>
/// <param name="dueDate">Дата в формате ГГГГ-ММ-ДД</param>
/// <param name="q">Поиск по названию и описанию</param>
/// <param name="sort">createdAt | dueDate | priority | title</param>
/// <param name="order">asc | desc</param>
/// <param name="page">Номер страницы, от 1</param>
/// <param name="pageSize">Записей на странице, 1..100</param>
[HttpGet]
```

# Проверка

Запустите API, выполните несколько запросов, потом посмотрите лог:

```bash
cd src/api/TaskPlanner.Api
dotnet run
```

В консоли:

```
[inf] POST /api/auth/login -> 200 за 214мс (user: -)
[inf] POST /api/tasks -> 201 за 96мс (user: 4)
[inf] GET /api/tasks?status=done&pageSize=5 -> 200 за 31мс (user: 4)
[inf] GET /api/tasks/999999 -> 404 за 12мс (user: 4)
[inf] POST /api/auth/register -> 400 за 55мс (user: -)
```

Файл лога:

```bash
tail -f logs/taskplanner-*.log
```

Строка в файле:

```json
{"Timestamp":"2026-10-01T12:00:00.0000000+00:00","Level":"Information","Application":"TaskPlanner.Api","Message":"POST /api/tasks -> 201 за 96мс (user: 4)","Properties":{}}
```

Проверка, что секретов в логе нет:

```bash
grep -c "Passw0rd\|Bearer eyJ" logs/taskplanner-*.log
# 0
```

Swagger: `http://localhost:5000/swagger` — у каждого метода есть описание,
указаны коды ответов, кнопка **Authorize** работает, перечисление показывают
подсказки.

# Коммит

```bash
git add src .gitignore
git commit -m "Backend: Serilog, логирование запросов, XML-комментарии в Swagger"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `libs` нет в `Serilog` sinks | пакеты `Serilog.Sinks.Console` и `Serilog.Sinks.File` не добавлены |
| Логи не появляются | `builder.Host.UseSerilog()` не вызван или `MinimumLevel.Default` слишком высок |
| В логе 200 вместо 500 | `RequestLoggingMiddleware` стоит **после** `ApiExceptionMiddleware` |
| `SwaggerGeneratorException: Conflicting method/path` | два метода с одинаковым маршрутом — например, `GET /api/tasks/{id}` и `GET /api/tasks/summary` без ограничения типа |
| XML-комментарии не видны в Swagger | `IncludeXmlComments` не найден файл — проверьте `GenerateDocumentationFile` и имя `TaskPlanner.Api.xml` |
| Пароли в логе | проверьте, не логируется ли тело запроса целиком |
| `Serilog` не видит секцию из `appsettings.json` | опечатка в имени секции — должно быть `"Serilog"` с большой буквы |

# Что должно быть в репозитории к концу сессии 4

- [ ] Serilog: консоль + ежедневный файл, `logs/` в `.gitignore`
- [ ] логирование каждого запроса с кодом и временем
- [ ] логирование операций CRUD и входа/выхода
- [ ] пароли и токены не логируются
- [ ] Swagger с описаниями метода и параметров, XML-комментарии подключены
- [ ] все 9 методов API отвечают по контракту

# Итог сессий 2–4: backend готов

Проверьте чек-лист из [`criteria.md`](https://github.com/artemovsergey/professionals-task/blob/main/criteria.md), раздел «Backend и API —
25 баллов»:

- [x] регистрация и вход, пароль в хешированном виде (BCrypt, соль внутри)
- [x] токен выдаётся при входе и принимается в `Authorization: Bearer`
- [x] изоляция данных: пользователь видит и меняет только свои задачи
- [x] полный CRUD задач
- [x] отметка выполнения и сводка
- [x] фильтры, поиск, сортировка, постраничный вывод
- [x] единый формат ответа на всех методах
- [x] корректные HTTP-коды: 400 / 401 / 403 / 404 / 500
- [x] операции логируются

## Иллюстрации

![[images/api12-swagger.png]]
*Swagger UI с контрактом из `api/openapi.yaml`*

![[images/api12-swagger-authorize.png]]
*Кнопка Authorize: токен из `/api/auth/login` вставляется один раз*
