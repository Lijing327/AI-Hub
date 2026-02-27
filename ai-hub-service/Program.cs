using ai_hub_service.Data;
using ai_hub_service.Services;
using ai_hub_service.Middleware;
using ai_hub_service.Modules.AiAudit.Services;
using AiHub.Services;
using AiHub.Middleware;
using AiHub.Utils;
using AiHub.Configurations;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);

// 环境开关：true=测试环境(ai_hub_test), false=生产环境(ai_hub)
const bool IS_TEST = true;

// 测试环境默认租户为 default_test（与 ai-hub-ai .env.test 一致，kb_article 数据多为该租户）
if (IS_TEST)
{
    builder.Configuration.AddInMemoryCollection(new Dictionary<string, string?>
    {
        ["Tenant:DefaultTenant"] = "default_test"
    });
}

Console.WriteLine($"============================================================");
Console.WriteLine($"============================================================");
Console.WriteLine($"AI-Hub .NET 服务启动 | 当前环境: {(IS_TEST ? "Test" : "Production")}");
Console.WriteLine($"使用数据库: {(IS_TEST ? "ai_hub_test" : "ai_hub")}");
Console.WriteLine($"============================================================");

// 添加服务
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// 配置数据库连接：根据 IS_TEST 开关强制使用对应数据库
var connectionString = IS_TEST
    ? "Server=172.16.15.9;Database=ai_hub_test;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;"
    : "Server=172.16.15.9;Database=ai_hub;User Id=sa;Password=pQdr2f@K3.Stp6Qs3hkP;TrustServerCertificate=true;";

Console.WriteLine($"[DEBUG] 连接字符串: {connectionString}");

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString)
           .EnableSensitiveDataLogging()  // 启用敏感数据日志
           .LogTo(Console.WriteLine, LogLevel.Information));  // 输出所有 SQL 查询到控制台

// 注册 HTTP 客户端工厂（用于调用 ai-hub-ai 服务）
builder.Services.AddHttpClient();

// 注册认证服务
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IDeviceManagerService, DeviceManagerService>();
builder.Services.AddScoped<PasswordHasher>();

// 注册知识库相关服务
builder.Services.AddScoped<IIndexService, IndexService>();
builder.Services.AddScoped<IKnowledgeArticleService, KnowledgeArticleService>();
builder.Services.AddScoped<IAssetService, AssetService>();
builder.Services.AddScoped<ITicketService, TicketService>();

// 配置JWT设置
var jwtSettings = builder.Configuration.GetSection(JwtSettings.SectionName).Get<JwtSettings>();
builder.Services.AddSingleton(jwtSettings!);
builder.Services.AddSingleton<JwtUtils>();

// 注册JWT认证
builder.Services.AddAuthentication("Bearer")
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new Microsoft.IdentityModel.Tokens.TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtSettings?.Issuer,
            ValidAudience = jwtSettings?.Audience,
            IssuerSigningKey = new Microsoft.IdentityModel.Tokens.SymmetricSecurityKey(
                System.Text.Encoding.UTF8.GetBytes(jwtSettings?.Secret ?? "")
            )
        };
    });

// 配置CORS
var allowedOrigins = builder.Configuration.GetSection("CORS:AllowedOrigins").Get<string[]>()
    ?? new[] { "http://localhost:5173", "http://localhost:3000" };

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowVueApp", policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// 配置Kestrel服务器端口（仅在开发环境或未配置反向代理时使用）
if (!IS_TEST)
{
    builder.WebHost.UseUrls("http://localhost:5000");
}

var app = builder.Build();

// 配置HTTP请求管道
// 添加异常处理中间件（必须在最前面）
app.UseDeveloperExceptionPage();

// 启用Swagger（测试环境也启用）
app.UseSwagger();
app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "知识库录入与管理系统 API V1");
        c.RoutePrefix = "swagger"; // Swagger UI 在 /swagger 路径下
    });

app.UseCors("AllowVueApp");

// 添加租户隔离中间件（必须在路由之前）
app.UseMiddleware<TenantMiddleware>();

// 添加内部 API 鉴权中间件（必须在路由之前，租户中间件之后）
app.UseMiddleware<InternalApiAuthMiddleware>();

// 添加JWT中间件（必须在认证之后，路由之前）
app.UseJwtMiddleware();

// 配置静态文件服务（用于提供上传的文件访问）
var uploadsPath = Path.Combine(app.Environment.ContentRootPath, "wwwroot", "uploads");
if (!Directory.Exists(uploadsPath))
{
    Directory.CreateDirectory(uploadsPath);
}

// 配置附件静态文件服务（支持从两个位置查找文件：优先附件目录，然后 wwwroot/uploads）
var attachmentBasePath = app.Configuration["AttachmentStorage:BasePath"];

// 如果配置了附件目录，优先使用附件目录的静态文件服务
if (!string.IsNullOrEmpty(attachmentBasePath) && Directory.Exists(attachmentBasePath))
{
    app.UseStaticFiles(new StaticFileOptions
    {
        FileProvider = new PhysicalFileProvider(attachmentBasePath),
        RequestPath = "/uploads",
        OnPrepareResponse = ctx =>
        {
            // 允许跨域访问静态文件
            ctx.Context.Response.Headers.Append("Access-Control-Allow-Origin", "*");
            ctx.Context.Response.Headers.Append("Access-Control-Allow-Methods", "GET, OPTIONS");
            ctx.Context.Response.Headers.Append("Access-Control-Allow-Headers", "*");

            // 设置缓存策略
            var fileName = ctx.File.Name.ToLower();
            if (fileName.EndsWith(".jpg") || fileName.EndsWith(".jpeg") ||
                fileName.EndsWith(".png") || fileName.EndsWith(".gif") ||
                fileName.EndsWith(".webp") || fileName.EndsWith(".mp4") ||
                fileName.EndsWith(".avi") || fileName.EndsWith(".mov") ||
                fileName.EndsWith(".wmv"))
            {
                ctx.Context.Response.Headers.Append("Cache-Control", "public, max-age=31536000");
            }
        }
    });
}

// 然后配置 wwwroot/uploads 的静态文件服务（作为回退）
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(app.Environment.ContentRootPath, "wwwroot")),
    RequestPath = "/uploads",
    OnPrepareResponse = ctx =>
    {
        // 允许跨域访问静态文件（图片等）
        ctx.Context.Response.Headers.Append("Access-Control-Allow-Origin", "*");
        ctx.Context.Response.Headers.Append("Access-Control-Allow-Methods", "GET, OPTIONS");
        ctx.Context.Response.Headers.Append("Access-Control-Allow-Headers", "*");

        // 设置缓存策略
        var fileName = ctx.File.Name.ToLower();
        if (fileName.EndsWith(".jpg") || fileName.EndsWith(".jpeg") ||
                fileName.EndsWith(".png") || fileName.EndsWith(".gif") ||
                fileName.EndsWith(".webp") || fileName.EndsWith(".mp4") ||
                fileName.EndsWith(".avi") || fileName.EndsWith(".mov") ||
                fileName.EndsWith(".wmv"))
        {
            ctx.Context.Response.Headers.Append("Cache-Control", "public, max-age=31536000");
        }
    }
});

app.UseAuthorization();
app.MapControllers();

// 配置根路径，重定向到Swagger
app.MapGet("/", () => Results.Redirect("/swagger")).ExcludeFromDescription();

// 初始化数据库并创建测试用户
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    var logger = services.GetRequiredService<ILogger<Program>>();

    try
    {
        var context = services.GetRequiredService<ApplicationDbContext>();

        // 应用待执行的迁移
        var pendingMigrations = await context.Database.GetPendingMigrationsAsync();
        if (pendingMigrations.Any())
        {
            logger.LogInformation("正在应用 {Count} 个数据库迁移...", pendingMigrations.Count());
            await context.Database.MigrateAsync();
            logger.LogInformation("数据库迁移应用完成");
        }
        else
        {
            logger.LogInformation("数据库已是最新状态");
        }
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "数据库初始化时发生错误");
    }
}

app.Run();
