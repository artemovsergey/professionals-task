using System.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using ToirProf.Api.Data;

namespace ToirProf.Api.Services;

// ===========================================================================
//  Генерация номера заявки вида Z-YYYY-XXXX
//
//  Номер выдаёт база, а не приложение. Счётчик лежит в отдельной
//  таблице work_order_counters по годам и обновляется одним оператором
//  INSERT ... ON CONFLICT DO UPDATE ... RETURNING — эта операция атомарна
//  в PostgreSQL.
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

        // Запрос идёт мимо Entity Framework. Причина: EF оборачивает
        // текст SqlQuery в подзапрос, а UPDATE ... RETURNING внутри
        // подзапроса PostgreSQL не принимает — запрос падает ещё на
        // сборке SQL с «'FromSql' or 'SqlQuery' was called with
        // non-composable SQL». Один оператор через ADO.NET решает
        // задачу без обходных путей.
        var connection = db.Database.GetDbConnection();
        if (connection.State != ConnectionState.Open)
        {
            await connection.OpenAsync(ct);
        }

        await using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO work_order_counters (year, last_value)
            VALUES (@year, 1)
            ON CONFLICT (year) DO UPDATE
               SET last_value = work_order_counters.last_value + 1
            RETURNING last_value
            """;

        var parameter = command.CreateParameter();
        parameter.ParameterName = "year";
        parameter.Value = year;
        command.Parameters.Add(parameter);

        // Если вызывающий код уже открыл транзакцию, счётчик обязан
        // увеличиться в ней же: иначе номер «сгорит» при откате.
        if (db.Database.CurrentTransaction is { } transaction)
        {
            command.Transaction = transaction.GetDbTransaction();
        }

        var next = Convert.ToInt32(await command.ExecuteScalarAsync(ct));

        if (next <= 0)
        {
            throw new InvalidOperationException(
                $"Не удалось получить номер заявки: счётчик за {year} год не обновился.");
        }

        return $"Z-{year}-{next:D4}";
    }
}
