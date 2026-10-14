using FluentAssertions;
using ToirProf.Desktop.Services;

namespace ToirProf.Tests;

// ===========================================================================
//  Тест №3. Стоимость материалов: calculateTotalMaterialCost
//
//  Четыре проверки из задания: несколько материалов, пустой список,
//  количество ноль и отрицательные значения. Эталон взят из задания:
//      подшипник 6-205   4 шт × 850,00  = 3 400,00
//      ремень приводной  2 шт × 1 200,00 = 2 400,00
//      масло И-20       10 л  × 150,00 = 1 500,00
//      ИТОГО                            7 300,00
// ===========================================================================
public class MaterialCostTests
{
    private static readonly Guid Bearing = new("eeeeeeee-0000-0000-0000-000000000001");
    private static readonly Guid Belt = new("eeeeeeee-0000-0000-0000-000000000002");
    private static readonly Guid Oil = new("eeeeeeee-0000-0000-0000-000000000003");

    [Fact(DisplayName = "Стоимость нескольких материалов считается по эталону 7300,00")]
    public void CalculateTotalMaterialCost_SumsSeveralLines()
    {
        // Arrange
        var lines = new[]
        {
            new MaterialLine(Bearing, 4m, 850m),
            new MaterialLine(Belt, 2m, 1200m),
            new MaterialLine(Oil, 10m, 150m)
        };

        // Act
        var total = Calculators.CalculateTotalMaterialCost(lines);

        // Assert — сумма decimal, а не double: 0,1 + 0,2 в double не равны 0,3.
        total.Should().Be(7300.00m);
    }

    [Fact(DisplayName = "Пустой список даёт ноль")]
    public void CalculateTotalMaterialCost_ReturnsZeroForEmptyList()
    {
        // Arrange — заявка без списаний.
        var lines = Array.Empty<MaterialLine>();

        // Act
        var total = Calculators.CalculateTotalMaterialCost(lines);

        // Assert
        total.Should().Be(0m);
    }

    [Fact(DisplayName = "Нулевое количество не меняет итог")]
    public void CalculateTotalMaterialCost_ZeroQuantityContributesNothing()
    {
        // Arrange — одна позиция с нулевым количеством, вторая настоящая.
        var lines = new[]
        {
            new MaterialLine(Bearing, 0m, 850m),
            new MaterialLine(Oil, 10m, 150m)
        };

        // Act
        var total = Calculators.CalculateTotalMaterialCost(lines);

        // Assert
        total.Should().Be(1500.00m);
    }

    [Fact(DisplayName = "Отрицательные значения уменьшают итог и не роняют расчёт")]
    public void CalculateTotalMaterialCost_HandlesNegativeValues()
    {
        // Arrange — списание со знаком минус, как при возврате материала.
        var lines = new[]
        {
            new MaterialLine(Bearing, 4m, 850m),
            new MaterialLine(Oil, -2m, 150m)
        };

        // Act
        var total = Calculators.CalculateTotalMaterialCost(lines);

        // Assert — 3 400 минус 300.
        total.Should().Be(3100.00m);
    }
}