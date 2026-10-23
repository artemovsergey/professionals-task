using FluentAssertions;
using ToirProf.Desktop.Services;

namespace ToirProf.Tests;

// ===========================================================================
//  Ровно пять юнит-тестов для Desktop-клиента по Приложению 5 тематического сценария.
//
//  Тест №1 — calculateDowntimeHours (два сценария).
//  Тест №2 — validateWorkOrder (два сценария).
//  Тест №3 — calculateTotalMaterialCost (один сценарий по эталону 7300,00).
// ===========================================================================
public class DesktopTests
{
    // =======================================================================
    //  Тест №1. Расчёт простоя: calculateDowntimeHours
    // =======================================================================
    [Fact(DisplayName = "Простой считается по рабочим часам между корректными датами")]
    public void calculateDowntimeHours_ValidDates_ReturnsCorrectHours()
    {
        // Arrange — 01.08.2026 (суббота) 10:00 → 03.08.2026 (понедельник) 16:00.
        // Выходные не считаются, только понедельник 8:00-16:00 = 8 часов.
        var start = new DateTimeOffset(2026, 8, 1, 10, 0, 0, TimeSpan.Zero);
        var end = new DateTimeOffset(2026, 8, 3, 16, 0, 0, TimeSpan.Zero);

        // Act
        var hours = Calculators.CalculateDowntimeHours(start, end);

        // Assert — 8 рабочих часов.
        hours.Should().Be(8m);
    }

    [Fact(DisplayName = "Окончание раньше начала даёт ноль")]
    public void calculateDowntimeHours_EndDateEarlierThanStartDate_ReturnsZero()
    {
        // Arrange — границы перепутаны местами.
        var start = new DateTimeOffset(2026, 3, 20, 20, 30, 0, TimeSpan.Zero);
        var end = new DateTimeOffset(2026, 3, 20, 8, 0, 0, TimeSpan.Zero);

        // Act
        var hours = Calculators.CalculateDowntimeHours(start, end);

        // Assert
        hours.Should().Be(0m);
    }

    // =======================================================================
    //  Тест №2. Валидация заявки: validateWorkOrder
    // =======================================================================
    private static readonly Guid EquipmentId = new("44444444-4444-4444-4444-444444444444");

    private static WorkOrderDraft ValidDraft() => new(
        EquipmentId,
        "Стучит подшипник главного шпинделя",
        "Критический",
        "Создана",
        new DateOnly(2026, 3, 24),
        new DateOnly(2026, 3, 26),
        "Износ подшипника 6-205 на шпинделе");

    [Fact(DisplayName = "Заполненная заявка проходит проверку")]
    public void validateWorkOrder_AllFieldsValid_ReturnsTrue()
    {
        // Arrange
        var draft = ValidDraft();

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert
        result.IsValid.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact(DisplayName = "Отсутствующее оборудование возвращает список ошибок")]
    public void validateWorkOrder_MissingEquipment_ReturnsFalseWithError()
    {
        // Arrange — оборудование не указано.
        var draft = ValidDraft() with { EquipmentId = Guid.Empty };

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().ContainSingle()
            .Which.Should().Contain("оборудование");
    }

    // =======================================================================
    //  Тест №3. Стоимость материалов: calculateTotalMaterialCost
    // =======================================================================
    private static readonly Guid Bearing = new("eeeeeeee-0000-0000-0000-000000000001");
    private static readonly Guid Belt = new("eeeeeeee-0000-0000-0000-000000000002");
    private static readonly Guid Oil = new("eeeeeeee-0000-0000-0000-000000000003");

    [Fact(DisplayName = "Стоимость нескольких материалов считается по эталону 7300,00")]
    public void calculateTotalMaterialCost_MultipleMaterials_ReturnsCorrectSum()
    {
        // Arrange — эталон из задания: 7300,00.
        var lines = new[]
        {
            new MaterialLine(Bearing, 4m, 850m),
            new MaterialLine(Belt, 2m, 1200m),
            new MaterialLine(Oil, 10m, 150m)
        };

        // Act
        var total = Calculators.CalculateTotalMaterialCost(lines);

        // Assert — сумма decimal, а не double.
        total.Should().Be(7300.00m);
    }
}
