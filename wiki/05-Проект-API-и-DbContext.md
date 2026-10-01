Сессия 2. Backend: каркас · 0–75 мин

# 1. Solution и проекты (0–15 мин)

Перейдите в корень репозитория и создайте solution:

```bash
cd src
dotnet new sln -n TaskPlanner
dotnet sln TaskPlanner.sln add api/TaskPlanner.Core api/TaskPlanner.Api api/TaskPlanner.Tests
```

Три проекта:

```bash
dotnet new classlib -n TaskPlanner.Core  -o api/TaskPlanner.Core  -f net9.0
dotnet new webapi  -n TaskPlanner.Api   -o api/TaskPlanner.Api   -f net9.0 --use-controllers
dotnet new xunit   -n TaskPlanner.Tests -o api/TaskPlanner.Tests -f net9.0

dotnet sln TaskPlanner.sln add api/TaskPlanner.Core api/TaskPlanner.Api api/TaskPlanner.Tests
```

Ссылки: `Core` → используется в `Api` и `Tests`:

```bash
dotnet add api/TaskPlanner.Api   reference api/TaskPlanner.Core
dotnet add api/TaskPlanner.Tests reference api/TaskPlanner.Core
dotnet add api/TaskPlanner.Tests reference api/TaskPlanner.Api
```

> **Замечание:** доменный слой в `Core` — не украшение. Он позволяет писать
> юнит-тесты сервисов без запуска веб-сервера и без базы. На отборе это
> отдельные баллы за тест-кейсы.

# 2. Пакеты (15–25 мин)

```bash
cd api/TaskPlanner.Core
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL -v 9.0.4
dotnet add package FluentValidation -v 12.0.0

cd ../TaskPlanner.Api
dotnet add package Microsoft.EntityFrameworkCore.Design -v 9.0.4
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer -v 9.0.4
dotnet add package System.IdentityModel.Tokens.Jwt -v 8.3.0
dotnet add package BCrypt.Net-Next -v 4.0.3
dotnet add package Swashbuckle.AspNetCore -v 7.2.0
dotnet add package FluentValidation.AspNetCore -v 12.0.0
dotnet add package Serilog.AspNetCore -v 9.0.0
dotnet add package Serilog.Sinks.Console -v 6.0.0
dotnet add package Serilog.Sinks.File -v 6.0.0

cd ../TaskPlanner.Tests
dotnet add package Microsoft.EntityFrameworkCore.InMemory -v 9.0.4
dotnet add package Microsoft.AspNetCore.Mvc.Testing -v 9.0.4
dotnet add package FluentAssertions -v 7.0.0
```

Проверка сборки — она уже должна работать:

```bash
cd ../..
dotnet build
```

> **Замечание:** версии пакетов EF Core должны совпадать с версией .NET 9.
> Смешение 8.x и 9.x даёт `System.InvalidOperationException: The specified
> version of the Entity Framework Core is not compatible`.

# 3. Сущности (25–40 мин)

`src/api/TaskPlanner.Core/Entities/User.cs`:

```csharp
namespace TaskPlanner.Core.Entities;

public class User
{
    public long Id { get; set; }

    public string Email { get; set; } = string.Empty;

    /// <summary>Хеш пароля (BCrypt). Открытый пароль в базе не хранится.</summary>
    public string PasswordHash { get; set; } = string.Empty;

    public string FullName { get; set; } = string.Empty;

    public DateTimeOffset CreatedAt { get; set; }

    public ICollection<TaskItem> Tasks { get; set; } = new List<TaskItem>();

    public ICollection<Category> Categories { get; set; } = new List<Category>();
}
```

`src/api/TaskPlanner.Core/Entities/TaskItem.cs`:

```csharp
namespace TaskPlanner.Core.Entities;

public class TaskItem
{
    public long Id { get; set; }

    public long UserId { get; set; }
    public User? User { get; set; }

    public long? CategoryId { get; set; }
    public Category? Category { get; set; }

    public string Title { get; set; } = string.Empty;

    public string? Description { get; set; }

    public TaskStatus Status { get; set; } = TaskStatus.New;

    public TaskPriority Priority { get; set; } = TaskPriority.Medium;

    public DateOnly? DueDate { get; set; }

    /// <summary>Заполняется только когда <see cref="Status"/> = Done.</summary>
    public DateTimeOffset? CompletedAt { get; set; }

    public DateTimeOffset CreatedAt { get; set; }

    public DateTimeOffset UpdatedAt { get; set; }
}
```

> **Замечание:** класс называется `TaskItem`, а не `Task`. Имя `Task`
> совпадает с `System.Threading.Tasks.Task` — при `using System.Threading.Tasks`
> компилятор начнёт путать вашу сущность с делегатом. Это самая частая
> ошибка новичков в .NET-проектах.

`src/api/TaskPlanner.Core/Entities/Category.cs`:

```csharp
namespace TaskPlanner.Core.Entities;

public class Category
{
    public long Id { get; set; }

    public long UserId { get; set; }
    public User? User { get; set; }

    public string Name { get; set; } = string.Empty;

    /// <summary>Цвет в формате #RRGGBB.</summary>
    public string? Color { get; set; }

    public ICollection<TaskItem> Tasks { get; set; } = new List<TaskItem>();
}
```

`src/api/TaskPlanner.Core/Enums/TaskStatus.cs`:

```csharp
namespace TaskPlanner.Core.Enums;

/// <summary>
/// Значения совпадают со списком из db/schema.sql и api/openapi.yaml.
/// Менять строки нельзя: они лежат в CHECK-ограничениях базы и в контракте API.
/// </summary>
public enum TaskStatus
{
    New = 0,
    InProgress = 1,
    Done = 2,
    Cancelled = 3,
}
```

`src/api/TaskPlanner.Core/Enums/TaskPriority.cs`:

```csharp
namespace TaskPlanner.Core.Enums;

public enum TaskPriority
{
    Low = 0,
    Medium = 1,
    High = 2,
}
```

# 4. Конвертация enum ⇄ строка (40–50 мин)

Enum хранится в базе как строка (`'new'`, `'high'`) и в JSON отдаётся строкой.
Значение `in_progress` пишется **с подчёркиванием**, а `camelCase`-сериализатор
даст `inProgress` — поэтому конвертер пишется явно.

`src/api/TaskPlanner.Core/Common/EnumJsonConverters.cs`:

```csharp
using System.Text.Json;
using System.Text.Json.Serialization;
using TaskPlanner.Core.Enums;

namespace TaskPlanner.Core.Common;

/// <summary>
/// Приводит enum к строке из контракта API: in_progress, а не inProgress.
/// Нужен потому, что в CHECK-ограничении базы записано 'in_progress'.
/// </summary>
public class TaskStatusConverter : JsonConverter<TaskStatus>
{
    private static readonly Dictionary<TaskStatus, string> ToText = new()
    {
        [TaskStatus.New] = "new",
        [TaskStatus.InProgress] = "in_progress",
        [TaskStatus.Done] = "done",
        [TaskStatus.Cancelled] = "cancelled",
    };

    private static readonly Dictionary<string, TaskStatus> FromText =
        ToText.ToDictionary(x => x.Value, x => x.Key);

    public override TaskStatus Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var value = reader.GetString() ?? string.Empty;
        if (FromText.TryGetValue(value, out var result))
        {
            return result;
        }

        throw new JsonException($"Неизвестный статус: {value}");
    }

    public override void Write(Utf8JsonWriter writer, TaskStatus value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(ToText[value]);
    }
}

public class TaskPriorityConverter : JsonConverter<TaskPriority>
{
    private static readonly Dictionary<TaskPriority, string> ToText = new()
    {
        [TaskPriority.Low] = "low",
        [TaskPriority.Medium] = "medium",
        [TaskPriority.High] = "high",
    };

    private static readonly Dictionary<string, TaskPriority> FromText =
        ToText.ToDictionary(x => x.Value, x => x.Key);

    public override TaskPriority Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var value = reader.GetString() ?? string.Empty;
        if (FromText.TryGetValue(value, out var result))
        {
            return result;
        }

        throw new JsonException($"Неизвестный приоритет: {value}");
    }

    public override void Write(Utf8JsonWriter writer, TaskPriority value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(ToText[value]);
    }
}
```

# 5. `AppDbContext` (50–65 мин)

`src/api/TaskPlanner.Api/Data/AppDbContext.cs`:

```csharp
using Microsoft.EntityFrameworkCore;
using TaskPlanner.Core.Entities;

namespace TaskPlanner.Api.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();

    public DbSet<TaskItem> Tasks => Set<TaskItem>();

    public DbSet<Category> Categories => Set<Category>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // ---------------------------------------------------------------
        // users
        // ---------------------------------------------------------------
        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("users", table => table.HasCheckConstraint("ck_users_email_format",
                "email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'"));
            entity.HasCheckConstraint("ck_users_full_name",
                "length(btrim(full_name)) > 0");

            entity.HasKey(x => x.Id);

            entity.Property(x => x.Id)
                .HasColumnName("id")
                .ValueGeneratedOnAdd();

            entity.Property(x => x.Email)
                .HasColumnName("email")
                .HasMaxLength(255)
                .IsRequired();

            entity.Property(x => x.PasswordHash)
                .HasColumnName("password_hash")
                .HasMaxLength(255)
                .IsRequired();

            entity.Property(x => x.FullName)
                .HasColumnName("full_name")
                .HasMaxLength(255)
                .IsRequired();

            entity.Property(x => x.CreatedAt)
                .HasColumnName("created_at")
                .HasColumnType("timestamptz")
                .IsRequired();

            entity.HasIndex(x => x.Email)
                .IsUnique()
                .HasDatabaseName("uq_users_email");
        });

        // ---------------------------------------------------------------
        // categories
        // ---------------------------------------------------------------
        modelBuilder.Entity<Category>(entity =>
        {
            entity.ToTable("categories");
            entity.HasCheckConstraint("ck_categories_name", "length(btrim(name)) > 0");
            entity.HasCheckConstraint("ck_categories_color",
                "color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$'");

            entity.HasKey(x => x.Id);

            entity.Property(x => x.Id)
                .HasColumnName("id")
                .ValueGeneratedOnAdd();

            entity.Property(x => x.UserId)
                .HasColumnName("user_id")
                .IsRequired();

            entity.Property(x => x.Name)
                .HasColumnName("name")
                .HasMaxLength(100)
                .IsRequired();

            entity.Property(x => x.Color)
                .HasColumnName("color")
                .HasMaxLength(7);

            entity.HasIndex(x => new { x.UserId, x.Name })
                .IsUnique()
                .HasDatabaseName("uq_categories_user_name");

            entity.HasOne(x => x.User)
                .WithMany(u => u.Categories)
                .HasForeignKey(x => x.UserId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // ---------------------------------------------------------------
        // tasks
        // ---------------------------------------------------------------
        modelBuilder.Entity<TaskItem>(entity =>
        {
            entity.ToTable("tasks");
            entity.HasCheckConstraint("ck_tasks_title_not_empty", "length(btrim(title)) > 0");
            entity.HasCheckConstraint("ck_tasks_status",
                "status IN ('new','in_progress','done','cancelled')");
            entity.HasCheckConstraint("ck_tasks_priority",
                "priority IN ('low','medium','high')");
            entity.HasCheckConstraint("ck_tasks_completed_at",
                "(status = 'done' AND completed_at IS NOT NULL) OR (status <> 'done' AND completed_at IS NULL)");

            entity.HasKey(x => x.Id);

            entity.Property(x => x.Id)
                .HasColumnName("id")
                .ValueGeneratedOnAdd();

            entity.Property(x => x.UserId)
                .HasColumnName("user_id")
                .IsRequired();

            entity.Property(x => x.CategoryId)
                .HasColumnName("category_id");

            entity.Property(x => x.Title)
                .HasColumnName("title")
                .HasMaxLength(200)
                .IsRequired();

            entity.Property(x => x.Description)
                .HasColumnName("description");

            // enum хранится строкой — так же, как в CHECK-ограничении
            entity.Property(x => x.Status)
                .HasColumnName("status")
                .HasColumnType("varchar(16)")
                .HasConversion<string>()
                .IsRequired();

            entity.Property(x => x.Priority)
                .HasColumnName("priority")
                .HasColumnType("varchar(16)")
                .HasConversion<string>()
                .IsRequired();

            entity.Property(x => x.DueDate)
                .HasColumnName("due_date")
                .HasColumnType("date");

            entity.Property(x => x.CompletedAt)
                .HasColumnName("completed_at")
                .HasColumnType("timestamptz");

            entity.Property(x => x.CreatedAt)
                .HasColumnName("created_at")
                .HasColumnType("timestamptz")
                .IsRequired();

            entity.Property(x => x.UpdatedAt)
                .HasColumnName("updated_at")
                .HasColumnType("timestamptz")
                .IsRequired();

            entity.HasIndex(x => x.UserId)
                .HasDatabaseName("ix_tasks_user_id");

            entity.HasIndex(x => x.Status)
                .HasDatabaseName("ix_tasks_status");

            entity.HasIndex(x => x.DueDate)
                .HasDatabaseName("ix_tasks_due_date");

            entity.HasIndex(x => new { x.UserId, x.Status, x.DueDate })
                .HasDatabaseName("ix_tasks_user_status_due");

            entity.HasIndex(x => x.CreatedAt)
                .HasDatabaseName("ix_tasks_created_at");

            entity.HasOne(x => x.User)
                .WithMany(u => u.Tasks)
                .HasForeignKey(x => x.UserId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(x => x.Category)
                .WithMany(c => c.Tasks)
                .HasForeignKey(x => x.CategoryId)
                .OnDelete(DeleteBehavior.SetNull);
        });
    }
}
```

> **Замечание:** ограничения из `db/schema.sql` перенесены в `OnModelCreating`,
> чтобы миграции создавали ту же схему. Иначе база из миграций разойдётся со
> скриптом, который сдаётся проверяющему, и ограничения пропадут.
>
> Внимание к экранированию: внутри C#-строки регулярное выражение
> `'^[^@\s]+@[^@\s]+\.[^@\s]+$'` записывается как
> `"email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'"` — два обратных слэша.

# 6. Фабрика для миграций (65–70 мин)

`src/api/TaskPlanner.Api/Data/DesignTimeDbContextFactory.cs`:

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Microsoft.Extensions.Configuration;

namespace TaskPlanner.Api.Data;

/// <summary>
/// Нужна, чтобы команда dotnet ef работала без запуска приложения.
/// </summary>
public class DesignTimeDbContextFactory : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .AddEnvironmentVariables()
            .Build();

        var connectionString = configuration.GetConnectionString("DefaultConnection");

        var optionsBuilder = new DbContextOptionsBuilder<AppDbContext>();
        optionsBuilder.UseNpgsql(connectionString);

        return new AppDbContext(optionsBuilder.Options);
    }
}
```

# 7. Первая миграция (70–75 мин)

Установите инструмент миграций (один раз, локально для репозитория):

```bash
cd src
dotnet new tool-manifest
dotnet tool install dotnet-ef --version 9.0.4
```

Создайте миграцию и примените её:

```bash
cd api/TaskPlanner.Api
dotnet ef migrations add InitialCreate
dotnet ef database update
```

Проверьте, что миграция создала ограничения:

```bash
psql -h 127.0.0.1 -U taskplanner -d taskplanner -c "\d tasks"
```

> **Замечание:** `dotnet ef database update` упадёт с
> `42P01: relation "tasks" does not exist`, если таблицы уже созданы
> `schema.sql` — миграция не умеет «пересоздать» существующую таблицу. Если
> вы применяли `schema.sql` вручную, сначала пересоздайте базу:
>
> ```bash
> dropdb -h 127.0.0.1 -U taskplanner taskplanner
> createdb -h 127.0.0.1 -U taskplanner taskplanner
> dotnet ef database update
> psql -h 127.0.0.1 -U taskplanner -d taskplanner -f ../db/seed.sql
> ```

# Проверка

```bash
cd src
dotnet build
```

Должно быть `Build succeeded`, без предупреждений о nullable.

Запустите API — на этой странице он ещё не отвечает на `/health`, но должен
подняться:

```bash
cd api/TaskPlanner.Api
dotnet run
```

В консоли: `Now listening on: http://localhost:5000`, и в Swagger — список
методов WeatherForecast. Пока это нормально: маршруты будут на следующей
странице.

Проверка в базе — ограничения на месте:

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'tasks'::regclass
ORDER BY conname;
```

В результате должны быть `ck_tasks_completed_at`, `ck_tasks_priority`,
`ck_tasks_status`, `ck_tasks_title_not_empty`, `fk_tasks_user`,
`fk_tasks_category`, `pk_tasks`.

# Коммит

```bash
git add src
git commit -m "Backend: solution, проекты, сущности, DbContext, первая миграция"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `dotnet: command not found` | см. [00-Подготовка-окружения](00-Подготовка-окружения) |
| `The specified version of the Entity Framework Core is not compatible` | выровнять версии всех `EntityFrameworkCore`-пакетов на 9.0.x |
| `Unable to create an object of type 'DesignTimeDbContextFactory'` | не найден `appsettings.json`: запускать `dotnet ef` из каталога `TaskPlanner.Api` |
| `Npgsql.NpgsqlException: Failed to connect` | не запущен PostgreSQL или неверна строка подключения |
| `relation "tasks" does not exist` | пересоздать базу, см. замечание выше |
| Компилятор не находит `TaskStatus` в сущности | забыт `using TaskPlanner.Core.Enums;` |
| `.HasConversion<string>()` ругается | EF 9 переименовал в `HasConversion<string>()` → строка; проверьте, что тип колонки указан как `varchar(16)` |

# Что должно быть в репозитории к концу сессии 2, блок 1

- [ ] `src/TaskPlanner.sln` с тремя проектами
- [ ] `TaskPlanner.Core`: сущности `User`, `TaskItem`, `Category`, enum-ы, конвертеры
- [ ] `TaskPlanner.Api`: `AppDbContext` со всеми CHECK-ограничениями и индексами
- [ ] `DesignTimeDbContextFactory`
- [ ] миграция `InitialCreate` и файл `db/schema.sql` в репозитории
- [ ] `dotnet build` проходит

---

Дальше: [06-Единый-формат-ответа-и-ошибки](06-Единый-формат-ответа-и-ошибки)
