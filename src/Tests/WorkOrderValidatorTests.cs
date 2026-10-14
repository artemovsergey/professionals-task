using FluentAssertions;
using ToirProf.Desktop.Services;

namespace ToirProf.Tests;

// ===========================================================================
//  Тест №2. Проверка заявки: validateWorkOrder
//
//  Четыре проверки из задания: все поля верны, не заполнено обязательное,
//  аварийная заявка без причины и некорректные плановые даты.
// ===========================================================================
public class WorkOrderValidatorTests
{
    /// <summary>Оборудование из сида — пресс ПР-2.</summary>
    private static readonly Guid EquipmentId = new("44444444-4444-4444-4444-444444444444");

    private static WorkOrderDraft ValidDraft() => new(
        EquipmentId,
        "Стучит подшипник главного шпинделя",
        "Высокий",
        "Черновик",
        new DateOnly(2026, 3, 24),
        new DateOnly(2026, 3, 26),
        "Износ подшипника 6-205 на шпинделе");

    [Fact(DisplayName = "Заполненная заявка проходит проверку")]
    public void ValidateWorkOrder_AcceptsCorrectWorkOrder()
    {
        // Arrange
        var draft = ValidDraft();

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert
        result.IsValid.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact(DisplayName = "Пустое обязательное поле возвращает список ошибок")]
    public void ValidateWorkOrder_RejectsMissingRequiredField()
    {
        // Arrange — описание не заполнено.
        var draft = ValidDraft() with { Description = "   " };

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert — причина называется прямо, без «ошибка валидации».
        result.IsValid.Should().BeFalse();
        result.Errors.Should().ContainSingle()
            .Which.Should().Contain("описание");
    }

    [Fact(DisplayName = "Аварийная заявка без причины не проходит")]
    public void ValidateWorkOrder_RejectsEmergencyWithoutFailureReason()
    {
        // Arrange — приоритет аварийный, но причина не указана.
        var draft = ValidDraft() with
        {
            Priority = Calculators.EmergencyPriority,
            FailureReason = null
        };

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().ContainSingle()
            .Which.Should().Contain("аварийной");
    }

    [Fact(DisplayName = "Плановое окончание раньше начала не проходит")]
    public void ValidateWorkOrder_RejectsDatesOutOfOrder()
    {
        // Arrange — даты переставлены местами.
        var draft = ValidDraft() with
        {
            PlannedStart = new DateOnly(2026, 3, 26),
            PlannedEnd = new DateOnly(2026, 3, 24)
        };

        // Act
        var result = Calculators.ValidateWorkOrder(draft);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().ContainSingle()
            .Which.Should().Contain("раньше");
    }
}