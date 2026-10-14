using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

/// <summary>
/// Материалы и ЗИП: справочник, остатки, дефицитные позиции.
/// Уход со склада делается только списанием в заявку —
/// иначе остатки расходятся с журналом операций.
/// </summary>
public interface IMaterialService
{
    Task<PagedResult<MaterialDto>> GetListAsync(bool includeInactive, string? search, bool onlyShortage, int page, int pageSize, CancellationToken ct);

    Task<MaterialDto> GetByIdAsync(Guid id, CancellationToken ct);

    Task<MaterialDto> CreateAsync(CreateMaterialDto dto, CancellationToken ct);

    Task<MaterialDto> UpdateAsync(Guid id, UpdateMaterialDto dto, CancellationToken ct);

    Task DeleteAsync(Guid id, CancellationToken ct);

    Task<MaterialDto> ReceiveStockAsync(Guid id, StockReceiptDto dto, CancellationToken ct);

    Task<List<MaterialShortageDto>> GetShortagesAsync(CancellationToken ct);

    Task<List<MaterialDto>> GetForSelectAsync(CancellationToken ct);
}

public sealed class MaterialService(AppDbContext db) : IMaterialService
{
    public async Task<PagedResult<MaterialDto>> GetListAsync(bool includeInactive, string? search, bool onlyShortage, int page, int pageSize, CancellationToken ct)
    {
        page = page < 1 ? 1 : page;
        pageSize = pageSize is < 1 or > 100 ? 20 : pageSize;

        var query = db.Materials.AsNoTracking();
        if (!includeInactive)
            query = query.Where(m => m.IsActive);
        if (!string.IsNullOrWhiteSpace(search))
        {
            var pattern = $"%{Escape(search.Trim())}%";
            query = query.Where(m => EF.Functions.ILike(m.Name, pattern, "\\")
                                     || EF.Functions.ILike(m.Sku, pattern, "\\"));
        }
        if (onlyShortage)
            query = query.Where(m => m.Stock < m.MinStock);

        var total = await query.CountAsync(ct);
        var items = await query
            .OrderBy(m => m.Name)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(m => new MaterialDto(
                m.Id, m.Sku, m.Name, m.Unit, m.Price, m.Stock, m.MinStock, m.Location, m.IsActive,
                m.Usages.Sum(u => u.Quantity)))
            .ToListAsync(ct);

        return new PagedResult<MaterialDto>(items, total, page, pageSize);
    }

    public async Task<MaterialDto> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var material = await db.Materials.AsNoTracking()
            .Where(m => m.Id == id)
            .Select(m => new MaterialDto(
                m.Id, m.Sku, m.Name, m.Unit, m.Price, m.Stock, m.MinStock, m.Location, m.IsActive,
                m.Usages.Sum(u => u.Quantity)))
            .FirstOrDefaultAsync(ct)
            ?? throw ApiException.NotFound("Материал не найден.");

        return material;
    }

    public async Task<MaterialDto> CreateAsync(CreateMaterialDto dto, CancellationToken ct)
    {
        var sku = dto.Sku.Trim();
        if (await db.Materials.AnyAsync(m => m.Sku == sku, ct))
            throw ApiException.Conflict($"Материал с артикулом {sku} уже есть в справочнике.");

        var material = new Material
        {
            Sku = sku,
            Name = dto.Name.Trim(),
            Unit = dto.Unit.Trim(),
            Price = dto.Price,
            Stock = dto.Stock,
            MinStock = dto.MinStock,
            Location = dto.Location?.Trim(),
            IsActive = true,
        };

        db.Materials.Add(material);
        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(material.Id, ct);
    }

    public async Task<MaterialDto> UpdateAsync(Guid id, UpdateMaterialDto dto, CancellationToken ct)
    {
        var material = await db.Materials.FirstOrDefaultAsync(m => m.Id == id, ct)
                       ?? throw ApiException.NotFound("Материал не найден.");

        if (dto.Name is not null) material.Name = dto.Name.Trim();
        if (dto.Unit is not null) material.Unit = dto.Unit.Trim();
        if (dto.Price.HasValue) material.Price = dto.Price.Value;
        if (dto.MinStock.HasValue) material.MinStock = dto.MinStock.Value;
        if (dto.Location is not null) material.Location = dto.Location.Trim();
        if (dto.IsActive.HasValue) material.IsActive = dto.IsActive.Value;

        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task DeleteAsync(Guid id, CancellationToken ct)
    {
        var material = await db.Materials.FirstOrDefaultAsync(m => m.Id == id, ct)
                       ?? throw ApiException.NotFound("Материал не найден.");

        var used = await db.WorkOrderMaterials.AnyAsync(u => u.MaterialId == id, ct);
        if (used)
            throw ApiException.Conflict("Материал удалён быть не может: он уже списан в заявку. Снимите отметку «активен».");

        db.Materials.Remove(material);
        await db.SaveChangesAsync(ct);
    }

    public async Task<MaterialDto> ReceiveStockAsync(Guid id, StockReceiptDto dto, CancellationToken ct)
    {
        var material = await db.Materials.FirstOrDefaultAsync(m => m.Id == id, ct)
                       ?? throw ApiException.NotFound("Материал не найден.");

        if (!material.IsActive)
            throw ApiException.Conflict("Принять приход по отключённому материалу нельзя.");

        material.Stock += dto.Quantity;
        await db.SaveChangesAsync(ct);
        return await GetByIdAsync(id, ct);
    }

    public async Task<List<MaterialShortageDto>> GetShortagesAsync(CancellationToken ct)
        => await db.Materials.AsNoTracking()
            .Where(m => m.IsActive && m.Stock < m.MinStock)
            .OrderBy(m => m.Stock - m.MinStock)
            .Select(m => new MaterialShortageDto(m.Id, m.Sku, m.Name, m.Stock, m.MinStock, m.Unit))
            .ToListAsync(ct);

    public async Task<List<MaterialDto>> GetForSelectAsync(CancellationToken ct)
        => await db.Materials.AsNoTracking()
            .Where(m => m.IsActive)
            .OrderBy(m => m.Name)
            .Select(m => new MaterialDto(
                m.Id, m.Sku, m.Name, m.Unit, m.Price, m.Stock, m.MinStock, m.Location, m.IsActive, null))
            .ToListAsync(ct);

    private static string Escape(string value)
        => value.Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_");
}