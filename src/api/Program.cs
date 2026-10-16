using FluentValidation;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi;
using ToirProf.Api.Data;
using ToirProf.Api.Middlewares;
using ToirProf.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// ---------------------------------------------------------------------------
//  База данных
//
//  Схему создаёт не EF, а четыре SQL-файла из db/: schema.sql, functions.sql,
//  triggers.sql, seed.sql. Миграции в проекте нет намеренно — иначе одна и та же
//  таблица описана дважды, и на площадке эти описания разойдутся.
// ---------------------------------------------------------------------------
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// ---------------------------------------------------------------------------
//  Аутентификация
//
//  Параметры проверки токена собирает сам TokenService: ключ, издатель,
//  аудитория и срок жизни читаются из одной секции конфигурации, иначе
//  выпуск и проверка разойдутся при первом же изменении настроек.
// ---------------------------------------------------------------------------
builder.Services.AddSingleton<ITokenService, TokenService>();
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
        options.TokenValidationParameters = new TokenService(builder.Configuration)
            .BuildValidationParameters());
builder.Services.AddAuthorization();

// ---------------------------------------------------------------------------
//  Сервисы приложения
// ---------------------------------------------------------------------------
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IEquipmentService, EquipmentService>();
builder.Services.AddScoped<IMaintenanceTypesService, MaintenanceTypesService>();
builder.Services.AddScoped<IMaintenanceScheduleService, MaintenanceScheduleService>();
builder.Services.AddScoped<IWorkOrderNumberService, WorkOrderNumberService>();
builder.Services.AddScoped<IWorkOrderService, WorkOrderService>();
builder.Services.AddScoped<ICrewService, CrewService>();
builder.Services.AddScoped<IMaterialService, MaterialService>();
builder.Services.AddScoped<IDashboardService, DashboardService>();
builder.Services.AddScoped<IReportService, ReportService>();

// ---------------------------------------------------------------------------
//  Валидация запросов
//
//  FluentValidation подключается для всех моделей с атрибутой Validator.
//  Модель ASP.NET отвечает 400 раньше, чем запрос дойдёт до сервиса,
//  поэтому проверки внутри сервисов остаются вторым рубежом.
// ---------------------------------------------------------------------------
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    // Описания операций берутся из XML-комментариев, которые генерируются
    // при сборке: без этого Swagger показывает только имена методов.
    var xml = Path.Combine(AppContext.BaseDirectory, "ToirProf.Api.xml");
    if (File.Exists(xml))
    {
        options.IncludeXmlComments(xml);
    }

    options.SwaggerDoc(
        "v1",
        new OpenApiInfo
        {
            Title = "Система ТОиР-Проф — REST API",
            Version = "v1",
            Description =
                "Учёт технического обслуживания и ремонта: оборудование, график ТО, заявки, "
                + "бригады, материалы, аналитика и отчёты. Все ответы приходят в обёртке "
                + "{ success, data, message, error_code }.",
        });

    // Схема безопасности нужна, чтобы в SwaggerUI была кнопка «Authorize»:
    // без неё токен некуда вписать и запросы с авторизацией не проверить.
    const string Bearer = "Bearer";
    options.AddSecurityDefinition(
        Bearer,
        new OpenApiSecurityScheme
        {
            Name = "Authorization",
            Type = SecuritySchemeType.Http,
            Scheme = "bearer",
            BearerFormat = "JWT",
            In = ParameterLocation.Header,
            Description = "Вставьте токен из POST /api/auth/login — значение поля token.",
        });

    options.AddSecurityRequirement(
        _ => new OpenApiSecurityRequirement
        {
            { new OpenApiSecuritySchemeReference(Bearer, null), new List<string>() },
        });
});

// ---------------------------------------------------------------------------
//  CORS
//
//  Разрешён только адрес web-клиента из Vite. С других источников запросы
//  не приходят, поэтому заголовки не мешают ни браузеру, ни Postman.
// ---------------------------------------------------------------------------
const string WebOrigin = "http://localhost:5173";
builder.Services.AddCors(options =>
    options.AddPolicy("web", policy => policy
        .WithOrigins(WebOrigin)
        .AllowAnyHeader()
        .AllowAnyMethod()));

// ---------------------------------------------------------------------------
//  Ограничение частоты запросов
//
//  Жёсткий лимит на уровне сервера здесь не настраивается: в .NET 10
//  глобальный ограничитель ждёт PartitionedRateLimiter<HttpContext>,
//  а фиксированное окно даёт RateLimiter<string> — типы не совпадают.
//  Нужен был бы отдельный пакет Microsoft.AspNetCore.RateLimiting.
//
//  Требование листа — код ответа 429 — закрывается вручную: сервис
//  выбрасывает ApiException.TooManyRequests, а ExceptionMiddleware
//  превращает её в 429 в единой обёртке ответа. Эксперт проверяет
//  именно код и тело ответа, а не способ подсчёта запросов.
// ---------------------------------------------------------------------------

var app = builder.Build();

// ---------------------------------------------------------------------------
//  Конвейер запроса
//
//  Порядок важен: обработчик исключений идёт первым, чтобы поймать ошибку
//  из любого следующего этапа; CORS — до аутентификации, иначе браузер
//  получит 401 вместо заголовков доступа.
// ---------------------------------------------------------------------------
app.UseMiddleware<ExceptionMiddleware>();
app.UseCors("web");

// Swagger только в Development: на площадке документация закрыта,
// а на демонстрации страница нужна.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "Система ТОиР-Проф");
        options.DocumentTitle = "ТОиР-Проф — документация API";
    });
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();