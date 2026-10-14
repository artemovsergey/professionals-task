using System;
using System.Collections.Generic;
using System.Linq;

namespace ToirProf.Desktop.Services;

/// <summary>
/// Позиция списания материалов в заявке.
/// Тот же набор полей, что и у сущности, но без привязки к базе:
/// тесты считают стоимость, не поднимая ни EF, ни PostgreSQL.
/// </summary>
/// <param name="MaterialId">Идентификатор материала.</param>
/// <param name="Quantity">Количество в единицах измерения справочника.</param>
/// <param name="UnitPrice">Цена за единицу на момент списания.</param>
public sealed record MaterialLine(Guid MaterialId, decimal Quantity, decimal UnitPrice)
{
    /// <summary>Стоимость позиции: количество умножается на цену.</summary>
    public decimal Cost => Quantity * UnitPrice;
}

/// <summary>
/// Результат проверки заявки перед сохранением.
/// </summary>
/// <param name="IsValid">True, если заявку можно сохранять.</param>
/// <param name="Errors">Список причин; пуст, когда <paramref name="IsValid"/> равно true.</param>
public sealed record ValidationResult(bool IsValid, IReadOnlyList<string> Errors)
{
    public static ValidationResult Ok() => new(true, Array.Empty<string>());

    public static ValidationResult Fail(params string[] errors) => new(false, errors);
}

/// <summary>
/// Проверяемые поля заявки. Только то, что нужно для проверки:
/// описание и приоритет в правилах задания не участвуют, поэтому
/// и не запрашиваются — лишние зависимости в тестах только мешают.
/// </summary>
/// <param name="EquipmentId">Оборудование, по которому открыта заявка.</param>
/// <param name="Description">Описание неисправности; обязательное поле.</param>
/// <param name="Priority">Приоритет: «Низкий», «Средний», «Высокий», «Аварийный».</param>
/// <param name="Status">Статус заявки: «Черновик», «Назначена», «В работе», «Завершена», «Отменена».</param>
/// <param name="PlannedStart">Запланированная дата начала работ.</param>
/// <param name="PlannedEnd">Запланированная дата окончания работ.</param>
/// <param name="FailureReason">Причина неисправности; обязательна для аварийной заявки.</param>
public sealed record WorkOrderDraft(
    Guid EquipmentId,
    string? Description,
    string Priority,
    string Status,
    DateOnly? PlannedStart,
    DateOnly? PlannedEnd,
    string? FailureReason);

/// <summary>
/// Бизнес-правила desktop-клиента, вынесенные в отдельный класс.
///
/// Класс не зависит ни от Avalonia, ни от Entity Framework: его можно
/// вызвать из юнит-теста, не создавая окно и не поднимая базу. Ровно
/// для этого в задании требуются модульные тесты desktop-клиента.
/// </summary>
public static class Calculators
{
    /// <summary>Приоритет, для которого обязательна причина неисправности.</summary>
    public const string EmergencyPriority = "Аварийный";

    /// <summary>Статус закрытой заявки.</summary>
    public const string CompletedStatus = "Завершена";

    /// <summary>
    /// Простой оборудования в часах между двумя моментами времени.
    ///
    /// Возвращает 0, если хотя бы одна граница не задана: заявка без
    /// фактических дат простоя не имеет, и ноль честнее, чем
    /// «неизвестно». Отрицательный результат тоже превращается в 0 —
    /// обратный порядок дат не должен давать отрицательный простой.
    /// </summary>
    /// <param name="start">Момент начала простоя.</param>
    /// <param name="end">Момент окончания простоя.</param>
    /// <returns>Длительность простоя в часах с точностью до сотых.</returns>
    public static decimal CalculateDowntimeHours(DateTimeOffset? start, DateTimeOffset? end)
    {
        if (start is null || end is null)
        {
            return 0m;
        }

        var hours = (end.Value - start.Value).TotalHours;
        return hours <= 0 ? 0m : Math.Round((decimal)hours, 2, MidpointRounding.AwayFromZero);
    }

    /// <summary>
    /// Проверка заявки перед сохранением.
    ///
    /// Проверяются четыре правила из задания: заполнено описание,
    /// заданы плановые даты в правильном порядке и у аварийной заявки
    /// есть причина неисправности. Ошибки собираются все сразу, а не
    /// по одной, — иначе пользователь правит форму пять раз подряд.
    /// </summary>
    /// <param name="draft">Проверяемая заявка.</param>
    /// <returns>Результат со списком причин.</returns>
    public static ValidationResult ValidateWorkOrder(WorkOrderDraft draft)
    {
        var errors = new List<string>();

        if (draft.EquipmentId == Guid.Empty)
        {
            errors.Add("Не указано оборудование.");
        }

        if (string.IsNullOrWhiteSpace(draft.Description))
        {
            errors.Add("Укажите описание неисправности.");
        }

        if (draft.PlannedStart is null)
        {
            errors.Add("Укажите плановую дату начала работ.");
        }

        if (draft.PlannedEnd is null)
        {
            errors.Add("Укажите плановую дату окончания работ.");
        }

        if (draft.PlannedStart is not null
            && draft.PlannedEnd is not null
            && draft.PlannedEnd < draft.PlannedStart)
        {
            errors.Add("Плановое окончание не может быть раньше планового начала.");
        }

        if (string.Equals(draft.Priority, EmergencyPriority, StringComparison.Ordinal)
            && string.IsNullOrWhiteSpace(draft.FailureReason))
        {
            errors.Add("Для аварийной заявки укажите причину неисправности.");
        }

        if (string.Equals(draft.Status, CompletedStatus, StringComparison.Ordinal)
            && string.IsNullOrWhiteSpace(draft.FailureReason))
        {
            errors.Add("Для завершённой заявки укажите причину неисправности.");
        }

        return errors.Count == 0 ? ValidationResult.Ok() : new ValidationResult(false, errors);
    }

    /// <summary>
    /// Суммарная стоимость списанных материалов.
    ///
    /// Пустой список даёт ноль, а не исключение: отчёт по заявке без
    /// списаний — обычный случай, и клиент не должен на нём падать.
    /// </summary>
    /// <param name="lines">Позиции списания.</param>
    /// <returns>Итоговая стоимость с точностью до сотых.</returns>
    public static decimal CalculateTotalMaterialCost(IEnumerable<MaterialLine> lines)
    {
        ArgumentNullException.ThrowIfNull(lines);

        var total = lines.Sum(line => line.Cost);
        return Math.Round(total, 2, MidpointRounding.AwayFromZero);
    }
}