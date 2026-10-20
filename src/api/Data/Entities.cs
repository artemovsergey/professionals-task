// Сущности EF Core, соответствующие таблицам db/schema.sql.
//
// Имена свойств совпадают с колонками. Для полей, которые считает сама
// база (простой, вычисляемая стоимость, даты аудита), свойство помечено
// комментарием: значение приходит из триггера или GENERATED-колонки,
// поэтому EF не должен ни читать его перед записью, ни считать главным.
using NpgsqlTypes;

namespace ToirProf.Api.Data;

public class Role
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }

    public List<User> Users { get; set; } = [];
}

public class User
{
    public Guid Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public Guid RoleId { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public Role Role { get; set; } = null!;
    public List<CrewMember> CrewMemberships { get; set; } = [];
}

public class Workshop
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;

    public List<Equipment> Equipment { get; set; } = [];
}

public class MaintenanceType
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int IntervalDays { get; set; }
    public string? Description { get; set; }
    public bool IsActive { get; set; } = true;

    public List<MaintenanceSchedule> ScheduleEntries { get; set; } = [];
}

public class Equipment
{
    public Guid Id { get; set; }
    public string InventoryNumber { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public Guid WorkshopId { get; set; }
    public string? Manufacturer { get; set; }
    public string? Model { get; set; }
    public string? SerialNumber { get; set; }
    public DateOnly CommissionDate { get; set; }
    public DateOnly? DecommissionDate { get; set; }
    public EquipmentStatus Status { get; set; }
    public int Criticality { get; set; }
    public string? Location { get; set; }
    public string? Notes { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public Workshop Workshop { get; set; } = null!;
    public List<MaintenanceSchedule> ScheduleEntries { get; set; } = [];
    public List<WorkOrder> WorkOrders { get; set; } = [];
}

/// Статус единицы оборудования. Менять статус у выведенной из
/// эксплуатации единицы запрещает триггер trg_equipment_status_guard.
public enum EquipmentStatus
{
    [PgName("Работает")]
    Работает = 0,

    [PgName("В ремонте")]
    ВРемонте = 1,

    [PgName("Выведено из эксплуатации")]
    ВыведеноИзЭксплуатации = 2,
}

/// Статус заявки. У завершённой заявки обязательны фактические даты
/// и причина неисправности — это проверяет trg_work_order_dates_check.
public enum WorkOrderStatus
{
    [PgName("Черновик")]
    Черновик = 0,

    [PgName("Назначена")]
    Назначена = 1,

    [PgName("В работе")]
    ВРаботе = 2,

    [PgName("Завершена")]
    Завершена = 3,

    [PgName("Отменена")]
    Отменена = 4,
}

public enum WorkOrderPriority
{
    [PgName("Низкий")]
    Низкий = 0,

    [PgName("Средний")]
    Средний = 1,

    [PgName("Высокий")]
    Высокий = 2,

    [PgName("Аварийный")]
    Аварийный = 3,
}

public class MaintenanceSchedule
{
    public Guid Id { get; set; }
    public Guid EquipmentId { get; set; }
    public Guid MaintenanceTypeId { get; set; }
    public DateOnly PlannedDate { get; set; }
    public DateOnly? CompletedDate { get; set; }
    public DateOnly? NextPlannedDate { get; set; }
    public string Status { get; set; } = "Запланировано";
    public decimal? ActualCost { get; set; }
    public string? Notes { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public Equipment Equipment { get; set; } = null!;
    public MaintenanceType MaintenanceType { get; set; } = null!;
    public List<WorkOrder> WorkOrders { get; set; } = [];
}

public class Crew
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Specialty { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public List<CrewMember> Members { get; set; } = [];
    public List<WorkOrder> WorkOrders { get; set; } = [];
}

public class CrewMember
{
    public Guid Id { get; set; }
    public Guid CrewId { get; set; }
    public Guid UserId { get; set; }
    public DateOnly JoinedAt { get; set; }

    public Crew Crew { get; set; } = null!;
    public User User { get; set; } = null!;
}

public class Material
{
    public Guid Id { get; set; }
    public string Sku { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Unit { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public decimal Stock { get; set; }
    public decimal MinStock { get; set; }
    public string? Location { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public List<WorkOrderMaterial> Usages { get; set; } = [];
}

public class WorkOrder
{
    public Guid Id { get; set; }
    public string Number { get; set; } = string.Empty;
    public Guid EquipmentId { get; set; }
    public Guid? MaintenanceTypeId { get; set; }
    public Guid? ScheduleId { get; set; }
    public Guid? CrewId { get; set; }
    public Guid CreatedBy { get; set; }
    public Guid? AssignedTo { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public WorkOrderPriority Priority { get; set; }
    public WorkOrderStatus Status { get; set; }

    public DateOnly? PlannedStart { get; set; }
    public DateOnly? PlannedEnd { get; set; }
    public DateTimeOffset? ActualStart { get; set; }
    public DateTimeOffset? ActualEnd { get; set; }

    // Простой в часах. Считает триггер fn_work_order_dates_check,
    // поэтому EF помечает поле как генерируемое базой и не пишет его.
    public decimal? DowntimeHours { get; set; }

    public string? FailureReason { get; set; }
    public DateTimeOffset? CompletedAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public Equipment Equipment { get; set; } = null!;
    public MaintenanceType? MaintenanceType { get; set; }
    public MaintenanceSchedule? Schedule { get; set; }
    public Crew? Crew { get; set; }
    public User? Assignee { get; set; }

    // Автор заявки. Связь с RESTRICT: удалить пользователя, который
    // когда-либо создавал заявку, нельзя — иначе в истории останутся
    // записи без автора.
    public User Creator { get; set; } = null!;

    public List<WorkOrderMaterial> Materials { get; set; } = [];
}

public class WorkOrderMaterial
{
    public Guid Id { get; set; }
    public Guid WorkOrderId { get; set; }
    public Guid MaterialId { get; set; }
    public decimal Quantity { get; set; }

    // Цена копируется из справочника на момент списания: если завтра
    // цена изменится, сумма закрытой заявки останется прежней.
    public decimal UnitPrice { get; set; }

    // Вычисляемая колонка GENERATED ALWAYS AS (quantity * unit_price).
    // EF только читает её, никогда не пишет.
    public decimal Cost { get; private set; }

    public WorkOrder WorkOrder { get; set; } = null!;
    public Material Material { get; set; } = null!;
}

public class OperationLog
{
    public Guid Id { get; set; }
    public Guid? UserId { get; set; }
    public string TableName { get; set; } = string.Empty;
    public Guid? RecordId { get; set; }
    public string Operation { get; set; } = string.Empty;
    public string? OldValues { get; set; }
    public string? NewValues { get; set; }
    public DateTime CreatedAt { get; set; }

    public User? User { get; set; }
}

public class WorkOrderCounter
{
    public short Year { get; set; }
    public int LastValue { get; set; }
}