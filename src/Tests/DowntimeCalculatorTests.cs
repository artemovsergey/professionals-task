using FluentAssertions;
using ToirProf.Desktop.Services;

namespace ToirProf.Tests;

// ===========================================================================
//  Тест №1. Расчёт простоя: calculateDowntimeHours
//
//  Три проверки из задания: корректные даты, окончание раньше начала
//  и незаполненные (null) границы. Метод статический и не имеет
//  состояния, поэтому все проверки живут в одном классе.
// ===========================================================================
public class DowntimeCalculatorTests
{
    [Fact(DisplayName = "Простой считается по двум корректным датам")]
    public void CalculateDowntimeHours_ReturnsHoursBetweenDates()
    {
        // Arrange — заявка простояла с 8:00 до 20:30, то есть 12,5 часа.
        var start = new DateTimeOffset(2026, 3, 20, 8, 0, 0, TimeSpan.Zero);
        var end = new DateTimeOffset(2026, 3, 20, 20, 30, 0, TimeSpan.Zero);

        // Act
        var hours = Calculators.CalculateDowntimeHours(start, end);

        // Assert — 12,5 часа, а не 12 или 13.
        hours.Should().Be(12.5m);
    }

    [Fact(DisplayName = "Окончание раньше начала даёт ноль, а не отрицательное значение")]
    public void CalculateDowntimeHours_ReturnsZeroWhenEndBeforeStart()
    {
        // Arrange — границы перепутаны местами.
        var start = new DateTimeOffset(2026, 3, 20, 20, 30, 0, TimeSpan.Zero);
        var end = new DateTimeOffset(2026, 3, 20, 8, 0, 0, TimeSpan.Zero);

        // Act
        var hours = Calculators.CalculateDowntimeHours(start, end);

        // Assert — простой не может быть отрицательным.
        hours.Should().Be(0m);
    }

    [Theory(DisplayName = "Незаполненная граница даёт ноль вместо ошибки")]
    [InlineData(null, "2026-03-20T20:30:00+00:00")]
    [InlineData("2026-03-20T08:00:00+00:00", null)]
    [InlineData(null, null)]
    public void CalculateDowntimeHours_ReturnsZeroWhenDatesMissing(
        string? startText,
        string? endText)
    {
        // Arrange — одна или обе границы не заполнены.
        var start = startText is null ? (DateTimeOffset?)null : DateTimeOffset.Parse(startText);
        var end = endText is null ? (DateTimeOffset?)null : DateTimeOffset.Parse(endText);

        // Act
        var hours = Calculators.CalculateDowntimeHours(start, end);

        // Assert
        hours.Should().Be(0m);
    }
}