using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

/// <summary>
/// Ремонтные бригады: справочник, состав и сводка по заявкам.
/// </summary>
public interface ICrewService
{
    Task<PagedResult<CrewShortDto>> GetListAsync(bool includeInactive, string? search, int page, int pageSize, CancellationToken ct);

    Task<CrewDto> GetByIdAsync(Guid id, CancellationToken ct);

    Task<CrewDto> CreateAsync(CreateCrewDto dto, CancellationToken ct);

    Task<CrewDto> UpdateAsync(Guid id, UpdateCrewDto dto, CancellationToken ct);

    Task DeleteAsync(Guid id, CancellationToken ct);

    Task<CrewDto> AddMemberAsync(Guid id, AddCrewMemberDto dto, CancellationToken ct);

    Task RemoveMemberAsync(Guid id, Guid userId, CancellationToken ct);

    Task<List<CrewShortDto>> GetForSelectAsync(CancellationToken ct);
}

public sealed class CrewService(AppDbContext db) : ICrewService
{
    public async Task<PagedResult<CrewShortDto>> GetListAsync(bool includeInactive, string? search, int page, int pageSize, CancellationToken ct)
    {
        page = page < 1 ? 1 : page;
        pageSize = pageSize is < 1 or > 100 ? 20 : pageSize;

        var query = db.Crews.AsNoTracking();
        if (!includeInactive)
            query = query.Where(c => c.IsActive);
        if (!string.IsNullOrWhiteSpace(search))
        {
            var pattern = $"%{Escape(search.Trim())}%";
            query = query.Where(c => EF.Functions.ILike(c.Name, pattern, "\\")
                                     || EF.Functions.ILike(c.Code, pattern, "\\"));
        }

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderBy(c => c.Code)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(c => new CrewShortDto(c.Id, c.Code, c.Name, c.IsActive, c.Members.Count))
            .ToListAsync(ct);

        return new PagedResult<CrewShortDto>(items, total, page, pageSize);
    }

    public async Task<CrewDto> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var crew = await db.Crews.AsNoTracking()
            .Include(c => c.Members).ThenInclude(m => m.User)
            .FirstOrDefaultAsync(c => c.Id == id, ct)
            ?? throw ApiException.NotFound("Бригада не найдена.");

        var orders = await db.WorkOrders.AsNoTracking()
            .Where(w => w.CrewId == id)
            .Select(w => new { w.Status, w.DowntimeHours })
            .ToListAsync(ct);

        var active = orders.Count(o => o.Status == WorkOrderStatus.ВРаботе);
        var completed = orders.Count(o => o.Status == WorkOrderStatus.Закрыта);
        var downtime = orders.Where(o => o.DowntimeHours.HasValue).Sum(o => o.DowntimeHours!.Value);

        // Рейтинг — доля завершённых заявок в процентах. Считается
        // в decimal: целочисленное деление 2/3 дало бы 0 вместо 66,7.
        var rating = orders.Count == 0 ? (decimal?)null
            : Math.Round(completed * 100m / orders.Count, 1);

        return new CrewDto(
            crew.Id,
            crew.Code,
            crew.Name,
            crew.Specialty,
            crew.IsActive,
            crew.Members
                .OrderBy(m => m.JoinedAt)
                .Select(m => new CrewMemberDto(m.UserId, m.User.Username, m.User.FullName, m.JoinedAt))
                .ToList(),
            active,
            completed,
            orders.Any(o => o.DowntimeHours.HasValue) ? Math.Round(downtime, 2) : null,
            rating);
    }

    public async Task<CrewDto> CreateAsync(CreateCrewDto dto, CancellationToken ct)
    {
        var code = dto.Code.Trim();
        if (await db.Crews.AnyAsync(c => c.Code == code, ct))
            throw ApiException.Conflict($"Бригада с кодом {code} уже существует.");

        var crew = new Crew
        {
            Code = code,
            Name = dto.Name.Trim(),
            Specialty = dto.Specialty?.Trim(),
            IsActive = dto.IsActive,
        };

        db.Crews.Add(crew);
        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(crew.Id, ct);
    }

    public async Task<CrewDto> UpdateAsync(Guid id, UpdateCrewDto dto, CancellationToken ct)
    {
        var crew = await db.Crews.FirstOrDefaultAsync(c => c.Id == id, ct)
                   ?? throw ApiException.NotFound("Бригада не найдена.");

        if (dto.Name is not null) crew.Name = dto.Name.Trim();
        if (dto.Specialty is not null) crew.Specialty = dto.Specialty.Trim();
        if (dto.IsActive.HasValue) crew.IsActive = dto.IsActive.Value;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task DeleteAsync(Guid id, CancellationToken ct)
    {
        var crew = await db.Crews.FirstOrDefaultAsync(c => c.Id == id, ct)
                   ?? throw ApiException.NotFound("Бригада не найдена.");

        var busy = await db.WorkOrders.AnyAsync(w => w.CrewId == id, ct);
        if (busy)
            throw ApiException.Conflict("Бригада удалена быть не может: на неё ссылаются заявки.");

        db.Crews.Remove(crew);
        await db.SaveChangesAsync(ct);
    }

    public async Task<CrewDto> AddMemberAsync(Guid id, AddCrewMemberDto dto, CancellationToken ct)
    {
        var crew = await db.Crews.FirstOrDefaultAsync(c => c.Id == id, ct)
                   ?? throw ApiException.NotFound("Бригада не найдена.");

        var user = await db.Users.AsNoTracking().FirstOrDefaultAsync(u => u.Id == dto.UserId, ct)
                   ?? throw ApiException.BadRequest("Пользователь не найден.");

        if (!user.IsActive)
            throw ApiException.BadRequest("В бригаду нельзя добавить отключённого пользователя.");

        var already = await db.CrewMembers.AnyAsync(m => m.CrewId == id && m.UserId == dto.UserId, ct);
        if (already)
            throw ApiException.Conflict($"{user.FullName} уже состоит в бригаде {crew.Name}.");

        db.CrewMembers.Add(new CrewMember
        {
            CrewId = id,
            UserId = dto.UserId,
            JoinedAt = DateOnly.FromDateTime(DateTime.Today),
        });

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task RemoveMemberAsync(Guid id, Guid userId, CancellationToken ct)
    {
        var member = await db.CrewMembers
            .Include(m => m.Crew)
            .FirstOrDefaultAsync(m => m.CrewId == id && m.UserId == userId, ct)
            ?? throw ApiException.NotFound("Пользователь не состоит в этой бригаде.");

        var inProgress = await db.WorkOrders.AnyAsync(
            w => w.CrewId == id && w.Status == WorkOrderStatus.ВРаботе, ct);
        if (inProgress)
            throw ApiException.Conflict(
                $"{member.Crew.Name} ведёт заявку в работе: сначала назначьте другую бригаду.");

        db.CrewMembers.Remove(member);
        await db.SaveChangesAsync(ct);
    }

    public async Task<List<CrewShortDto>> GetForSelectAsync(CancellationToken ct)
        => await db.Crews.AsNoTracking()
            .Where(c => c.IsActive)
            .OrderBy(c => c.Name)
            .Select(c => new CrewShortDto(c.Id, c.Code, c.Name, c.IsActive, c.Members.Count))
            .ToListAsync(ct);

    /// <summary>
    /// Экранирует спецсимволы LIKE, иначе «100%» в поиске превращается
    /// в «совпадает со всем» и список реестра оказывается пустым.
    /// </summary>
    private static string Escape(string value)
        => value.Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_");
}