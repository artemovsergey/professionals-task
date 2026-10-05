Сессия 2. Backend: каркас · 0–75 мин

# Как читать эту страницу

Каждый шаг — одна небольшая операция: сначала команда или кусок кода, затем
снимок того, как выглядит результат. Скриншоты снимайте в VS Code и в DBeaver
по ходу работы, а не в конце.

Проектов два: `TaskPlanner.Api` (сервис) и `TaskPlanner.Tests` (тесты). Схема
базы берётся из `db/schema.sql` со страницы [03](03-Скрипт-schema-sql) —
миграции для этого задания не обязательны.

# 1. Шаг 1. Solution (5 мин)

```bash
cd src
dotnet new sln -n TaskPlanner
```

![[images/api05-s1-sln.png]]
*Solution создан: `The template "Solution File" was created successfully`*

# 2. Шаг 2. Два проекта (5–20 мин)

```bash
dotnet new webapi -n TaskPlanner.Api   -o api/TaskPlanner.Api   -f net9.0 --use-controllers
dotnet new xunit   -n TaskPlanner.Tests -o api/TaskPlanner.Tests -f net9.0
```

Флаг `-f net9.0` обязателен: без него на машине с .NET 10 получится проект под
`net10.0`, а проверяющий собирает на .NET 9.

![[images/api05-s2-projects.png]]
*Шаблоны `webapi` и `xUnit` созданы, восстановление зависимостей прошло*

# 3. Шаг 3. Проекты в solution и ссылка на API (20–25 мин)

```bash
dotnet sln TaskPlanner.sln add api/TaskPlanner.Api api/TaskPlanner.Tests
dotnet add api/TaskPlanner.Tests reference api/TaskPlanner.Api
dotnet sln TaskPlanner.sln list
```

Тесты живут в отдельном проекте, но им нужен доступ к коду сервиса — поэтому
ссылка `Tests -> Api`. Без неё тесты не увидят `Program` и маршруты.

![[images/api05-s3-sln.png]]
*Оба проекта в solution, ссылка добавлена, `dotnet sln list` их показывает*

# 4. Шаг 4. Пакеты API (25–40 мин)

```bash
cd api/TaskPlanner.Api
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL -v 9.0.0
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer -v 9.0.0
dotnet add package BCrypt.Net-Next -v 4.0.3
dotnet add package Swashbuckle.AspNetCore -v 7.2.0
```

Четыре пакета закрывают всёBackend-приложение: драйвер PostgreSQL с EF Core,
JWT, хеширование паролей и Swagger UI.

> **Замечание:** версии EF Core держите на 9.0.x. Смешение 8.x и 9.x даёт
> `The specified version of the Entity Framework Core is not compatible`.

![[images/api05-s4-packages-api.png]]
*Пакеты добавлены: `PackageReference for package ... added to file`*

# 5. Шаг 5. Пакеты тестов (40–45 мин)

```bash
cd ../TaskPlanner.Tests
dotnet add package Microsoft.AspNetCore.Mvc.Testing -v 9.0.0
dotnet add package FluentAssertions -v 7.0.0
```

`Mvc.Testing` поднимает сервис целиком, `FluentAssertions` даёт читаемые
проверки вида `result.Should().BeUnauthorized()`.

![[images/api05-s5-packages-tests.png]]
*Пакеты тестов добавлены в `TaskPlanner.Tests.csproj`*

# 6. Шаг 6. Сборка (45–50 мин)

```bash
cd ../..
dotnet build
```

![[images/api05-s6-build.png]]
*`Build succeeded`: собраны обе DLL — API и тесты*

# 7. Шаг 7. Сущность пользователя (50–55 мин)

`api/TaskPlanner.Api/Models/Entities.cs`:

```csharp
public class User
{
    public long Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public DateTimeOffset CreatedAt { get; set; }
}
```

Колонка `password_hash` хранит хеш BCrypt. Открытый пароль в базе не
хранится, и в логах он тоже не должен появляться.

![[images/api05-s7-user.png]]
*`User`: пять свойств, названия совпадают с колонками из `schema.sql`*

# 8. Шаг 8. Сущность задачи (55–60 мин)

```csharp
public class TaskItem
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string Status { get; set; } = "new";
    public string Priority { get; set; } = "medium";
    public DateOnly? DueDate { get; set; }
    public DateTimeOffset? CompletedAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }
    public long? CategoryId { get; set; }
}
```

Два решения, которые стоит принять сразу:

- класс называется `TaskItem`, а не `Task`: имя `Task` совпадает с
  `System.Threading.Tasks.Task`, и при `using System.Threading.Tasks`
  компилятор начинает путать сущность с делегатом;
- `Status` и `Priority` — строки, а не enum: в базе они лежат строками
  (`'in_progress'`, а не `inProgress`), и такой же формат требует
  `api/openapi.yaml`.

![[images/api05-s8-taskitem.png]]
*`TaskItem`: двенадцать свойств, `Status` и `Priority` — строки*

# 9. Шаг 9. Контекст и наборы сущностей (60–62 мин)

`api/TaskPlanner.Api/Data/TaskPlannerContext.cs`:

```csharp
public class TaskPlannerContext(DbContextOptions<TaskPlannerContext> options)
    : DbContext(options)
{
    public DbSet<Models.User> Users => Set<Models.User>();
    public DbSet<Models.TaskItem> Tasks => Set<Models.TaskItem>();
    public DbSet<Models.Category> Categories => Set<Models.Category>();
}
```

Три `DbSet` — это три таблицы, с которыми работает сервис.

![[images/api05-s9-dbsets.png]]
*Контекст объявляет `Users`, `Tasks`, `Categories`*

# 10. Шаг 10. Отображение users (62–65 мин)

```csharp
b.Entity<Models.User>(e =>
{
    e.ToTable("users");
    e.HasKey(x => x.Id);
    // EF оборачивает имена в кавычки, поэтому «Id» и «id» — разные колонки
    e.Property(x => x.Id).HasColumnName("id");
    e.Property(x => x.Email).HasColumnName("email");
    e.Property(x => x.PasswordHash).HasColumnName("password_hash");
    e.Property(x => x.FullName).HasColumnName("full_name");
    e.Property(x => x.CreatedAt).HasColumnName("created_at");
});
```

Без `HasColumnName` EF создаст колонки `Id`, `EmailHash`, `PasswordHash` —
и `SELECT` из приложения перестанет совпадать с таблицей из `schema.sql`.

![[images/api05-s10-users-mapping.png]]
*Каждое свойство связано с колонкой своей таблицы*

# 11. Шаг 11. Отображение tasks (65–68 мин)

```csharp
b.Entity<Models.TaskItem>(e =>
{
    e.ToTable("tasks");
    e.HasKey(x => x.Id);
    e.Property(x => x.Id).HasColumnName("id");
    e.Property(x => x.UserId).HasColumnName("user_id");
    e.Property(x => x.Title).HasColumnName("title");
    e.Property(x => x.Description).HasColumnName("description");
    e.Property(x => x.Status).HasColumnName("status");
    e.Property(x => x.Priority).HasColumnName("priority");
    e.Property(x => x.DueDate).HasColumnName("due_date");
    e.Property(x => x.CompletedAt).HasColumnName("completed_at");
    e.Property(x => x.CreatedAt).HasColumnName("created_at");
    e.Property(x => x.UpdatedAt).HasColumnName("updated_at");
    e.Property(x => x.CategoryId).HasColumnName("category_id");
});
```

CHECK-ограничения из `schema.sql` переносить в `OnModelCreating` не нужно:
схему создаёт скрипт, а не миграции. Дублировать правила в двух местах — значит
со временем получить расхождение.

![[images/api05-s11-tasks-mapping.png]]
*`tasks`: двенадцать колонок, имена совпадают со скриптом*

# 12. Шаг 12. Подключение контекста (68–70 мин)

`api/TaskPlanner.Api/Program.cs`:

```csharp
builder.Services.AddDbContext<TaskPlanner.Api.Data.TaskPlannerContext>(o =>
    o.UseNpgsql(builder.Configuration.GetConnectionString("Default")));
```

Строка подключения лежит в `appsettings.json`, а не в коде: адрес БД у
проверяющего может отличаться от вашего.

![[images/api05-s12-program-db.png]]
*Контекст зарегистрирован в DI через `AddDbContext`*

# 13. Шаг 13. Swagger (70–73 мин)

```csharp
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(o =>
{
    o.SwaggerDoc("v1", new() {
        Title = "Планировщик личных задач — API",
        Version = "v1"
    });
});
```

Swagger нужен не для красоты: без него нельзя показать проверяющему контракт
методов, а это отдельные баллы.

![[images/api05-s13-program-swagger.png]]
*Документация API включена в сборку*

# 14. Шаг 14. Конверт ответа (73–75 мин)

`api/TaskPlanner.Api/Contracts/Contracts.cs`:

```csharp
public class Envelope<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string Message { get; set; } = "OK";

    [System.Text.Json.Serialization.JsonPropertyName("error_code")]
    public string? ErrorCode { get; set; }
}
```

Одна обёртка на весь API: успех и ошибка отличаются только `success` и
`error_code`. Формат разбирается на странице
[06](06-Единый-формат-ответа-и-ошибки).

![[images/api05-s14-envelope.png]]
*`Envelope<T>`: `success`, `data`, `message`, `error_code`*

# Проверка

```bash
cd src
dotnet build
```

В выводе должно быть `Build succeeded` без предупреждений о nullable.

Запустите API — на этой странице маршрутов ещё нет, но процесс должен подняться
и показать пустой Swagger:

```bash
cd api/TaskPlanner.Api
dotnet run
```

Проверка в базе — ограничения на месте после `schema.sql`:

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'tasks'::regclass
ORDER BY conname;
```

В результате должны быть `ck_tasks_completed_at`, `ck_tasks_priority`,
`ck_tasks_status`, `ck_tasks_title_not_empty`, `fk_tasks_user`,
`fk_tasks_category`.

# Коммит

```bash
git add src
git commit -m "Backend: solution, проекты, пакеты, сущности и контекст данных"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `dotnet: command not found` | см. [00-Подготовка-окружения](00-Подготовка-окружения) |
| `'net9.0' is not a valid value for -f` | на машине стоит .NET 10 SDK: поставьте .NET 9 или укажите свою версию |
| `The specified version of the Entity Framework Core is not compatible` | выровнять все пакеты `EntityFrameworkCore` на 9.0.x |
| `Npgsql.NpgsqlException: Failed to connect` | не запущен PostgreSQL или неверна строка подключения |
| `relation "users" does not exist` | не выполнен `db/schema.sql` со страницы [03](03-Скрипт-schema-sql) |
| В базе появились колонки `Id`, `Email` вместо `id`, `email` | забыли `HasColumnName` в `OnModelCreating` |

# Что должно быть в репозитории к концу сессии 2, блок 1

- [ ] `TaskPlanner.sln` с проектами `TaskPlanner.Api` и `TaskPlanner.Tests`
- [ ] `Models/Entities.cs`: `User`, `TaskItem`, `Category`
- [ ] `Data/TaskPlannerContext.cs` с отображением на таблицы из `schema.sql`
- [ ] `Contracts/Contracts.cs` с общим конвертом ответа
- [ ] `Program.cs` с `AddDbContext`, Swagger и строкой подключения из настроек
- [ ] `dotnet build` проходит

---

Дальше: [06-Единый-формат-ответа-и-ошибки](06-Единый-формат-ответа-и-ошибки)