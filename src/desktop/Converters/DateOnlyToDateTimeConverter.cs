using System;
using System.Globalization;
using Avalonia.Data.Converters;

namespace ToirProf.Desktop.Converters;

/// <summary>
/// Связывает <see cref="DateOnly" /> из модели с выбором даты в интерфейсе.
///
/// Модели хранят дату без времени (<see cref="DateOnly" />) — её и ждут
/// запросы к API, — а <see cref="Avalonia.Controls.DatePicker" /> работает
/// с <see cref="DateTimeOffset" />. Перевод типов в каждой модели значил
/// бы таскать время по всей цепочке ради одного поля, поэтому он живёт
/// в конвертере.
///
/// Тип у контрола именно <c>DateTimeOffset?</c>: у <c>CalendarDatePicker</c>
/// он другой (<c>DateTime?</c>), и при замене контрола конвертер придётся
/// поправить — иначе выбор даты молча перестанет работать.
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

        // Смещение берём местное: календарь показывает дату как есть,
        // и при переходе на UTC число могло бы сдвинуться на сутки.
        return new DateTimeOffset(date.ToDateTime(TimeOnly.MinValue, DateTimeKind.Unspecified), TimeZoneInfo.Local.GetUtcOffset(DateTime.Today));
    }

    public object? ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        => value switch
        {
            DateTimeOffset offset => DateOnly.FromDateTime(offset.DateTime),
            DateTime dateTime => DateOnly.FromDateTime(dateTime),
            _ => null,
        };
}
