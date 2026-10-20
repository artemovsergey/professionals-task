using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace ToirProf.Api.Data;

/// Контекст приложения. Схема не создаётся миграциями: на площадке
/// база собирается из db/schema.sql, db/functions.sql, db/triggers.sql
/// и db/seed.sql. Здесь только отображение таблиц на сущности.
public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Role> Roles => Set<Role>();
    public DbSet<User> Users => Set<User>();
    public DbSet<Workshop> Workshops => Set<Workshop>();
    public DbSet<Equipment> Equipment => Set<Equipment>();
    public DbSet<MaintenanceType> MaintenanceTypes => Set<MaintenanceType>();
    public DbSet<MaintenanceSchedule> MaintenanceSchedule => Set<MaintenanceSchedule>();
    public DbSet<Crew> Crews => Set<Crew>();
    public DbSet<CrewMember> CrewMembers => Set<CrewMember>();
    public DbSet<Material> Materials => Set<Material>();
    public DbSet<WorkOrder> WorkOrders => Set<WorkOrder>();
    public DbSet<WorkOrderMaterial> WorkOrderMaterials => Set<WorkOrderMaterial>();
    public DbSet<OperationLog> OperationLog => Set<OperationLog>();
    public DbSet<WorkOrderCounter> WorkOrderCounters => Set<WorkOrderCounter>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        // Наборы значений (статус оборудования, статус и приоритет заявки)
        // хранятся строками по-русски с пробелами — «В ремонте», «В работе».
        // Допустимые значения ограничены CHECK-ограничениями в db/schema.sql.
        //
        // Отдельный тип PostgreSQL (CREATE TYPE ... AS ENUM) не используется:
        // Npgsql отправляет строку как text, и PostgreSQL отвергает запись
        // в enum-колонку с ошибкой 42804 («колонка priority имеет тип
        // work_order_priority, а выражение - text»). С CHECK такой проблемы
        // нет, а гибкость — выше: добавить значение можно одним ALTER.
        //
        // В C# перечисление остаётся перечислением, а в базу уходит подпись
        // из атрибута [PgName] — см. PgEnumLabels.

        b.Entity<Role>(e =>
        {
            e.ToTable("roles");
            e.HasKey(x => x.Id).HasName("pk_roles");
            e.Property(x => x.Code).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(150).IsRequired();
            e.Property(x => x.Description).HasMaxLength(500);
            e.HasIndex(x => x.Code).IsUnique().HasDatabaseName("uq_roles_code");
        });

        b.Entity<User>(e =>
        {
            e.ToTable("users");
            e.HasKey(x => x.Id).HasName("pk_users");
            e.Property(x => x.Username).HasMaxLength(100).IsRequired();
            e.Property(x => x.PasswordHash).HasMaxLength(200).IsRequired();
            e.Property(x => x.FullName).HasMaxLength(200).IsRequired();
            e.HasIndex(x => x.Username).IsUnique().HasDatabaseName("uq_users_username");
            e.HasOne(x => x.Role)
                .WithMany(r => r.Users)
                .HasForeignKey(x => x.RoleId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_users_role");
        });

        b.Entity<Workshop>(e =>
        {
            e.ToTable("workshops");
            e.HasKey(x => x.Id).HasName("pk_workshops");
            e.Property(x => x.Code).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(150).IsRequired();
            e.HasIndex(x => x.Code).IsUnique().HasDatabaseName("uq_workshops_code");
        });

        b.Entity<MaintenanceType>(e =>
        {
            e.ToTable("maintenance_types");
            e.HasKey(x => x.Id).HasName("pk_maintenance_types");
            e.Property(x => x.Code).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(200).IsRequired();
            e.Property(x => x.IntervalDays).IsRequired();
            e.Property(x => x.Description).HasMaxLength(500);
            e.HasIndex(x => x.Code).IsUnique().HasDatabaseName("uq_maintenance_types_code");
        });

        b.Entity<Equipment>(e =>
        {
            e.ToTable("equipment");
            e.HasKey(x => x.Id).HasName("pk_equipment");
            e.Property(x => x.InventoryNumber).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(200).IsRequired();
            e.Property(x => x.Manufacturer).HasMaxLength(150);
            e.Property(x => x.Model).HasMaxLength(100);
            e.Property(x => x.SerialNumber).HasMaxLength(100);
            // Столбец status хранит русскую подпись статуса: в C# это
            // перечисление EquipmentStatus, в базе — varchar(50) с CHECK.
            e.Property(x => x.Status)
                .HasMaxLength(50)
                .IsRequired()
                .HasConversion(PgEnumLabels.Converter<EquipmentStatus>());
            e.Property(x => x.Location).HasMaxLength(200);
            e.Property(x => x.Notes).HasMaxLength(1000);

            // Даты приходят как DateOnly: в базе это date, а не timestamp.
            e.Property(x => x.CommissionDate).HasColumnType("date");
            e.Property(x => x.DecommissionDate).HasColumnType("date");

            e.HasIndex(x => x.InventoryNumber).IsUnique().HasDatabaseName("uq_equipment_inventory_number");
            e.HasIndex(x => x.WorkshopId).HasDatabaseName("ix_equipment_workshop");
            e.HasIndex(x => x.Status).HasDatabaseName("ix_equipment_status");

            e.HasOne(x => x.Workshop)
                .WithMany(w => w.Equipment)
                .HasForeignKey(x => x.WorkshopId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_equipment_workshop");
        });

        b.Entity<MaintenanceSchedule>(e =>
        {
            e.ToTable("maintenance_schedule");
            e.HasKey(x => x.Id).HasName("pk_maintenance_schedule");
            e.Property(x => x.PlannedDate).HasColumnType("date");
            e.Property(x => x.CompletedDate).HasColumnType("date");
            e.Property(x => x.NextPlannedDate).HasColumnType("date");
            e.Property(x => x.Status).HasMaxLength(50).IsRequired();
            e.Property(x => x.Notes).HasMaxLength(500);

            e.HasIndex(x => new { x.EquipmentId, x.MaintenanceTypeId, x.PlannedDate })
                .IsUnique()
                .HasDatabaseName("uq_maintenance_schedule_slot");
            e.HasIndex(x => x.EquipmentId).HasDatabaseName("ix_maintenance_schedule_equipment");
            e.HasIndex(x => x.PlannedDate).HasDatabaseName("ix_maintenance_schedule_planned");

            e.HasOne(x => x.Equipment)
                .WithMany(q => q.ScheduleEntries)
                .HasForeignKey(x => x.EquipmentId)
                .OnDelete(DeleteBehavior.Cascade)
                .HasConstraintName("fk_maintenance_schedule_equipment");

            e.HasOne(x => x.MaintenanceType)
                .WithMany(t => t.ScheduleEntries)
                .HasForeignKey(x => x.MaintenanceTypeId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_maintenance_schedule_type");
        });

        b.Entity<Crew>(e =>
        {
            e.ToTable("crews");
            e.HasKey(x => x.Id).HasName("pk_crews");
            e.Property(x => x.Code).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(200).IsRequired();
            e.Property(x => x.Specialty).HasMaxLength(300);
            e.HasIndex(x => x.Code).IsUnique().HasDatabaseName("uq_crews_code");
        });

        b.Entity<CrewMember>(e =>
        {
            e.ToTable("crew_members");
            e.HasKey(x => x.Id).HasName("pk_crew_members");
            e.Property(x => x.JoinedAt).HasColumnType("date");
            e.HasIndex(x => new { x.CrewId, x.UserId }).IsUnique().HasDatabaseName("uq_crew_members_crew_user");
            e.HasIndex(x => x.UserId).HasDatabaseName("ix_crew_members_user");

            e.HasOne(x => x.Crew)
                .WithMany(c => c.Members)
                .HasForeignKey(x => x.CrewId)
                .OnDelete(DeleteBehavior.Cascade)
                .HasConstraintName("fk_crew_members_crew");

            e.HasOne(x => x.User)
                .WithMany(u => u.CrewMemberships)
                .HasForeignKey(x => x.UserId)
                .OnDelete(DeleteBehavior.Cascade)
                .HasConstraintName("fk_crew_members_user");
        });

        b.Entity<Material>(e =>
        {
            e.ToTable("materials");
            e.HasKey(x => x.Id).HasName("pk_materials");
            e.Property(x => x.Sku).HasMaxLength(50).IsRequired();
            e.Property(x => x.Name).HasMaxLength(200).IsRequired();
            e.Property(x => x.Unit).HasMaxLength(10).IsRequired();
            e.Property(x => x.Price).HasPrecision(14, 2);
            e.Property(x => x.Stock).HasPrecision(14, 2);
            e.Property(x => x.MinStock).HasPrecision(14, 2);
            e.Property(x => x.Location).HasMaxLength(200);
            e.HasIndex(x => x.Sku).IsUnique().HasDatabaseName("uq_materials_sku");
        });

        b.Entity<WorkOrder>(e =>
        {
            e.ToTable("work_orders");
            e.HasKey(x => x.Id).HasName("pk_work_orders");
            e.Property(x => x.Number).HasMaxLength(20).IsRequired();
            e.Property(x => x.Title).HasMaxLength(200).IsRequired();
            e.Property(x => x.Description).HasMaxLength(2000);
            // Приоритет и статус — перечисления C# с русскими подписями
            // в базе (varchar(50) + CHECK из db/schema.sql).
            e.Property(x => x.Priority)
                .HasMaxLength(50)
                .IsRequired()
                .HasConversion(PgEnumLabels.Converter<WorkOrderPriority>());
            e.Property(x => x.Status)
                .HasMaxLength(50)
                .IsRequired()
                .HasConversion(PgEnumLabels.Converter<WorkOrderStatus>());
            e.Property(x => x.FailureReason).HasMaxLength(1000);

            e.Property(x => x.PlannedStart).HasColumnType("date");
            e.Property(x => x.PlannedEnd).HasColumnType("date");

            // Простой считает триггер. Помечаем поле генерируемым базой:
            // иначе EF отправил бы в UPDATE устаревшее значение и записал
            // бы его поверх того, что посчитал триггер.
            e.Property(x => x.DowntimeHours)
                .HasPrecision(10, 2)
                .ValueGeneratedOnAddOrUpdate();

            e.HasIndex(x => x.Number).IsUnique().HasDatabaseName("uq_work_orders_number");
            e.HasIndex(x => x.EquipmentId).HasDatabaseName("ix_work_orders_equipment");
            e.HasIndex(x => x.CrewId).HasDatabaseName("ix_work_orders_crew");
            e.HasIndex(x => x.Status).HasDatabaseName("ix_work_orders_status");
            e.HasIndex(x => x.Priority).HasDatabaseName("ix_work_orders_priority");
            e.HasIndex(x => x.CreatedAt).HasDatabaseName("ix_work_orders_created");

            e.HasOne(x => x.Equipment)
                .WithMany(q => q.WorkOrders)
                .HasForeignKey(x => x.EquipmentId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_work_orders_equipment");

            e.HasOne(x => x.MaintenanceType)
                .WithMany()
                .HasForeignKey(x => x.MaintenanceTypeId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_work_orders_maintenance_type");

            e.HasOne(x => x.Schedule)
                .WithMany(q => q.WorkOrders)
                .HasForeignKey(x => x.ScheduleId)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("fk_work_orders_schedule");

            e.HasOne(x => x.Crew)
                .WithMany(c => c.WorkOrders)
                .HasForeignKey(x => x.CrewId)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("fk_work_orders_crew");

            e.HasOne(x => x.Assignee)
                .WithMany()
                .HasForeignKey(x => x.AssignedTo)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("fk_work_orders_assigned_to");

            e.HasOne(x => x.Creator)
                .WithMany()
                .HasForeignKey(x => x.CreatedBy)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_work_orders_created_by");
        });

        b.Entity<WorkOrderMaterial>(e =>
        {
            e.ToTable("work_order_materials");
            e.HasKey(x => x.Id).HasName("pk_work_order_materials");
            e.Property(x => x.Quantity).HasPrecision(14, 3);
            e.Property(x => x.UnitPrice).HasPrecision(14, 2);

            // Колонка вычисляется на стороне PostgreSQL. EF помечает её
            // как магазинную и никогда не пишет: иначе приложение
            // отправило бы «цену» вместо количества × цены.
            e.Property(x => x.Cost)
                .HasPrecision(14, 2)
                .HasComputedColumnSql("quantity * unit_price", stored: true)
                .ValueGeneratedOnAddOrUpdate();

            e.HasIndex(x => new { x.WorkOrderId, x.MaterialId }).IsUnique().HasDatabaseName("uq_wom_order_material");
            e.HasIndex(x => x.WorkOrderId).HasDatabaseName("ix_wom_work_order");

            e.HasOne(x => x.WorkOrder)
                .WithMany(w => w.Materials)
                .HasForeignKey(x => x.WorkOrderId)
                .OnDelete(DeleteBehavior.Cascade)
                .HasConstraintName("fk_wom_work_order");

            e.HasOne(x => x.Material)
                .WithMany(m => m.Usages)
                .HasForeignKey(x => x.MaterialId)
                .OnDelete(DeleteBehavior.Restrict)
                .HasConstraintName("fk_wom_material");
        });

        b.Entity<OperationLog>(e =>
        {
            e.ToTable("operation_log");
            e.HasKey(x => x.Id).HasName("pk_operation_log");
            e.Property(x => x.TableName).HasMaxLength(50).IsRequired();
            e.Property(x => x.Operation).HasMaxLength(10).IsRequired();
            e.Property(x => x.OldValues).HasColumnType("jsonb");
            e.Property(x => x.NewValues).HasColumnType("jsonb");

            e.HasIndex(x => new { x.TableName, x.RecordId }).HasDatabaseName("ix_operation_log_record");
            e.HasIndex(x => x.CreatedAt).HasDatabaseName("ix_operation_log_created");

            e.HasOne(x => x.User)
                .WithMany()
                .HasForeignKey(x => x.UserId)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("fk_operation_log_user");
        });

        b.Entity<WorkOrderCounter>(e =>
        {
            e.ToTable("work_order_counters");
            e.HasKey(x => x.Year);
            e.Property(x => x.Year).HasColumnName("year");
        });

        ApplySnakeCaseColumnNames(b);
    }

    /// Приводит имена колонок к snake_case — ровно так их создаёт db/schema.sql.
    ///
    /// Таблицы, ключи, индексы и внешние ключи описаны выше поимённо, а имена
    /// колонок не заданы: без этого Entity Framework подставил бы в запрос
    /// имена свойств C# («Id», «CreatedAt») в кавычках, и первый же запрос
    /// к базе упал бы с «колонка u.id не существует».
    ///
    /// Пакет с готовыми соглашениями не подключаем: на площадке нет сети,
    /// а зависимость ради перевода регистра того не стоит.
    private static void ApplySnakeCaseColumnNames(ModelBuilder b)
    {
        foreach (var entity in b.Model.GetEntityTypes())
        {
            foreach (var property in entity.GetProperties())
            {
                property.SetColumnName(ToSnakeCase(property.Name));
            }
        }
    }

    /// <c>CreatedAt</c> → <c>created_at</c>, <c>RoleId</c> → <c>role_id</c>.
    ///
    /// Простая вставка подчёркивания перед каждой заглавной буквой, кроме
    /// первой: слова в именах C# пишутся с верблюжьим регистром, поэтому
    /// результат совпадает с соглашением базы.
    private static string ToSnakeCase(string name)
    {
        var builder = new StringBuilder(name.Length + 8);

        for (var i = 0; i < name.Length; i++)
        {
            var letter = name[i];

            if (char.IsUpper(letter) && i > 0)
            {
                builder.Append('_');
            }

            builder.Append(char.ToLowerInvariant(letter));
        }

        return builder.ToString();
    }

    public override int SaveChanges(bool acceptAllChangesOnSuccess)
    {
        Stamp();
        return base.SaveChanges(acceptAllChangesOnSuccess);
    }

    public override Task<int> SaveChangesAsync(
        bool acceptAllChangesOnSuccess,
        CancellationToken cancellationToken = default)
    {
        Stamp();
        return base.SaveChangesAsync(acceptAllChangesOnSuccess, cancellationToken);
    }

    /// Проставляет CreatedAt и UpdatedAt перед сохранением.
    ///
    /// Даты нужны не всем таблицам: у справочников вроде ролей и цехов
    /// их нет вовсе, поэтому обход идёт по набору изменений и проверяет
    /// наличие свойства перед записью.
    private void Stamp()
    {
        var now = DateTime.UtcNow;

        foreach (var entry in ChangeTracker.Entries())
        {
            if (entry.State is not (EntityState.Added or EntityState.Modified))
            {
                continue;
            }

            if (entry.State == EntityState.Added
                && entry.Metadata.FindProperty(nameof(User.CreatedAt)) is { } createdProperty)
            {
                var created = entry.Property(createdProperty.Name);
                if (created.CurrentValue is DateTime value && value == default)
                {
                    created.CurrentValue = now;
                }
            }

            if (entry.Metadata.FindProperty(nameof(User.UpdatedAt)) is { } updatedProperty)
            {
                entry.Property(updatedProperty.Name).CurrentValue = now;
            }
        }
    }
}