using System;
using System.Globalization;
using Avalonia.Data.Converters;

namespace ToirProf.Desktop.Converters;

/// <summary>
/// Связывает <see cref="DateOnly" /> из модели с выбором даты в интерфейсе.
///
/// Выбор даты в Avalonia работает с <see cref="DateTime" />, а запросы
/// к API принимают дату без времени. Приводить типы в каждой модели
/// значило бы таскать время по всей цепочке ради одного поля, поэтому
/// перевод живёт в конвертере.
/// </summary>
public sealed class DateOnlyToDateTimeConverter : IValueConverter
{
    public object? Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        if (value is not DateOnly date)
        {
            return null;
        }

        // Пустая дата в модели — это DateOnly.MinValue (01.01.0001), а не null:
        // поле объявлено значимым типом. Такой «ноль» нельзя отдавать календарю,
        // поэтому на его месте остаётся пустое поле.
        if (date == default)
        {
            return null;
        }

        return date.ToDateTime(TimeOnly.MinValue);
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value switch
        {
            DateTime dateTime => DateOnly.FromDateTime(dateTime),
            DateTimeOffset offset => DateOnly.FromDateTime(offset.DateTime),
            _ => null,
        };
}
