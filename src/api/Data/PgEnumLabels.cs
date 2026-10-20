using System.Reflection;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;
using NpgsqlTypes;

namespace ToirProf.Api.Data;

/// <summary>
/// Подписи значений перечислений так, как они записаны в базе.
///
/// Столбцы статусов и приоритета хранят «человеческие» подписи —
/// «В работе», «Выведено из эксплуатации». В C# пробел в имени члена
/// недопустим, поэтому имена слитные, а подпись для базы берётся
/// из атрибута <see cref="PgNameAttribute"/>: список значений остаётся
/// в одном месте — рядом с самим перечислением.
///
/// Преобразование включается на уровне свойства модели. Без него EF
/// вызывает <c>Enum.Parse</c> и падает на подписи с пробелом:
/// «Cannot convert string value 'В работе' from the database to any value
/// in the mapped 'WorkOrderStatus' enum».
/// </summary>
public static class PgEnumLabels
{
    /// <summary>Преобразователь «значение перечисления ↔ подпись в базе».</summary>
    public static ValueConverter<TEnum, string> Converter<TEnum>() where TEnum : struct, Enum =>
        new(value => ToLabel(value), label => FromLabel<TEnum>(label));

    /// <summary>Подпись для базы. Незаданная подпись — имя члена как есть.</summary>
    public static string ToLabel<TEnum>(TEnum value) where TEnum : struct, Enum =>
        Cache<TEnum>.To.TryGetValue(value, out var label) ? label : value.ToString();

    /// <summary>Значение по подписи из базы.</summary>
    public static TEnum FromLabel<TEnum>(string label) where TEnum : struct, Enum
    {
        if (Cache<TEnum>.From.TryGetValue(label, out var value))
        {
            return value;
        }

        // Подписи нет в атрибутах — пробуем имя члена: так прочитается
        // значение, добавленное в базу после сборки, и тестовые данные.
        return Enum.TryParse<TEnum>(label, out var parsed)
            ? parsed
            : throw new InvalidOperationException(
                $"В перечислении {typeof(TEnum).Name} нет значения «{label}».");
    }

    /// <summary>Словари для одного перечисления собираются один раз.</summary>
    private static class Cache<TEnum> where TEnum : struct, Enum
    {
        public static readonly Dictionary<TEnum, string> To = BuildTo();

        public static readonly Dictionary<string, TEnum> From =
            To.ToDictionary(pair => pair.Value, pair => pair.Key, StringComparer.Ordinal);

        private static Dictionary<TEnum, string> BuildTo()
        {
            var labels = new Dictionary<TEnum, string>();

            foreach (var field in typeof(TEnum).GetFields(BindingFlags.Public | BindingFlags.Static))
            {
                var label = field.GetCustomAttribute<PgNameAttribute>()?.PgName;
                if (label is not null && field.GetValue(null) is TEnum value)
                {
                    labels[value] = label;
                }
            }

            return labels;
        }
    }
}
