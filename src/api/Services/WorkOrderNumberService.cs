using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;

namespace ToirProf.Api.Services;

// ===========================================================================
//  Генерация номера заявки вида Z-YYYY-XXXX
//
//  Номер выдаёт база, а не приложение. Счётчик лежит в отдельной
//  таблице work_order_counters по годам и обновляется одним оператором
//  UPDATE ... RETURNING — эта операция атомарна в PostgreSQL.
//
//  Почему не «SELECT, потом +1, потом UPDATE»: между чтением и записью
//  номер успевает выдать вторая транзакция, и две заявки получат один
//  и тот же номер. Ограничение уникальности поймает это, но пользователь
//  получит 409 вместо созданной заявки — при живом создании заявок на
//  демонстрации это выглядит как сбой.
// ===========================================================================

public interface IWorkOrderNumberService
{
    /// <summary>
    /// Забирает следующий номер заявки на текущий год.
    /// Вызывать внутри той же транзакции, что и вставку заявки.
    /// </summary>
    Task<string> NextAsync(CancellationToken ct);
}

public sealed class WorkOrderNumberService(AppDbContext db) : IWorkOrderNumberService
{
    public async Task<string> NextAsync(CancellationToken ct)
    {
        var year = DateTime.UtcNow.Year;

        // Строка счётчика может отсутствовать — например, если базу
        // собрали, а seed.sql не выполняли. Создаём её с нулевым
        // значением, чтобы первый же номер был Z-YEAR-0001.
        await db.Database.ExecuteSqlInterpolatedAsync(
            $"INSERT INTO work_order_counters (year, last_value) VALUES ({year}, 0) ON CONFLICT (year) DO NOTHING",
            ct);

        // Для скалярного запроса EF Core требует колонку с именем Value.
        var next = await db.Database.SqlQuery<int>(
                $"""
                 UPDATE work_order_counters
                    SET last_value = last_value + 1
                  WHERE year = {year}
                 RETURNING last_value AS "Value"
                 """)
            .FirstOrDefaultAsync(ct);

        if (next <= 0)
            throw new InvalidOperationException(
                $"Не удалось получить номер заявки: счётчик за {year} год не обновился.");

        return $"Z-{year}-{next:D4}";
    }
}