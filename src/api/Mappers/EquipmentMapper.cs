using ToirProf.Api.Data;
using ToirProf.Api.DTOs;

namespace ToirProf.Api.Mappers;

/// <summary>
/// Ручной маппинг сущностей парковки в DTO.
///
/// Почему без AutoMapper: в DTO нет десятка полей подряд, зато есть
/// вычисляемый статус и подстановка названия цеха. Автоматический
/// маппер всё равно пришлось бы донастраиватьExclude-ами, а на
/// демонстрации выигрывает код, который читается целиком за минуту.
///
/// Статус передаётся параметром <c>workshopName</c>, а не берётся из
/// навигации: при чтении списка название цеха приходит одним
/// JOIN-ом, а при записи сущность ещё не сохранена и цеха у неё нет.
/// </summary>
public static class EquipmentMapper
{
    /// <summary>Полная карточка оборудования — для одного объекта.</summary>
    public static EquipmentDto ToDto(this Equipment entity, string workshopName) =>
        new(
            entity.Id,
            entity.InventoryNumber,
            entity.Name,
            entity.WorkshopId,
            workshopName,
            entity.Manufacturer,
            entity.Model,
            entity.SerialNumber,
            entity.CommissionDate,
            entity.DecommissionDate,
            StatusToString(entity.Status),
            entity.Criticality,
            entity.Location,
            entity.Notes,
            entity.CreatedAt,
            entity.UpdatedAt);

    /// <summary>
    /// Короткая строка списка: только то, что помещается в таблицу.
    /// Остальные поля грузить для сотни строк — лишняя нагрузка на БД.
    /// </summary>
    public static EquipmentShortDto ToShortDto(this Equipment entity, string workshopName) =>
        new(
            entity.Id,
            entity.InventoryNumber,
            entity.Name,
            entity.WorkshopId,
            workshopName,
            StatusToString(entity.Status),
            entity.Criticality);

    /// <summary>
    /// Вид обслуживания вместе с числом записей графика: клиенту
    /// показываем «используется 12 раз», чтобы администратор понимал,
    /// можно ли деактивировать справочник.
    /// </summary>
    public static MaintenanceTypeDto ToDto(this MaintenanceType entity, int usageCount) =>
        new(
            entity.Id,
            entity.Code,
            entity.Name,
            entity.IntervalDays,
            entity.Description,
            entity.IsActive,
            usageCount);

    /// <summary>
    /// Запись графика планового ТО. Названия оборудования и вида
    /// обслуживания приходят параметрами: они нужны клиенту для
    /// таблицы, а в самой записи хранятся только идентификаторы.
    /// </summary>
    public static MaintenanceScheduleDto ToDto(
        this MaintenanceSchedule entity,
        string equipmentName,
        string inventoryNumber,
        string typeName,
        int intervalDays) =>
        new(
            entity.Id,
            entity.EquipmentId,
            equipmentName,
            inventoryNumber,
            entity.MaintenanceTypeId,
            typeName,
            intervalDays,
            entity.PlannedDate,
            entity.CompletedDate,
            entity.NextPlannedDate,
            entity.Status,
            entity.ActualCost,
            entity.Notes);

    /// <summary>
    /// Перечисление <see cref="EquipmentStatus"/> переводится в строку
    /// из <see cref="EquipmentStatuses"/>.
    ///
    /// В базе статус лежит текстом — того же слова, что и в задании,
    /// — чтобы в DBeaver и в отчётах было видно «В ремонте», а не 1.
    /// В C# он остаётся enum: сравнения в коде должны искать
    /// <c>EquipmentStatus.ВРемонте</c>, а не строку, опечатка в которой
    /// проявилась бы только на демонстрации. Переписываем значения в
    /// одно место и возвращаем строку только на границе API.
    /// </summary>
    private static string StatusToString(EquipmentStatus status) =>
        status switch
        {
            EquipmentStatus.ВРаботе => EquipmentStatuses.Running,
            EquipmentStatus.ВРемонте => EquipmentStatuses.InRepair,
            EquipmentStatus.ВыведеноИзЭксплуатации => EquipmentStatuses.Retired,
            _ => EquipmentStatuses.Running,
        };
}