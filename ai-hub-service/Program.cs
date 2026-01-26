using ai_hub_service.Data;
using ai_hub_service.Services;
using ai_hub_service.Middleware;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.FileProviders;

var builder = WebApplication.CreateBuilder(args);

// 添加服务
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// 配置数据库连接
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString));

// 注册服务
builder.Services.AddScoped<IKnowledgeArticleService, KnowledgeArticleService>();
builder.Services.AddScoped<IAssetService, AssetService>();
builder.Services.AddScoped<IIndexService, IndexService>();

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
if (builder.Environment.IsDevelopment())
{
    builder.WebHost.UseUrls("http://localhost:5000");
}

var app = builder.Build();

// 配置HTTP请求管道
// 添加异常处理中间件（必须在最前面）
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler("/Error");
}

// 启用Swagger（生产环境建议禁用或限制访问）
var enableSwagger = app.Configuration.GetValue<bool>("EnableSwagger", false);
if (app.Environment.IsDevelopment() || enableSwagger)
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "知识库录入与管理系统 API V1");
        c.RoutePrefix = "swagger"; // Swagger UI 在 /swagger 路径下
    });
}

app.UseCors("AllowVueApp");

// 添加租户隔离中间件（必须在路由之前）
app.UseMiddleware<TenantMiddleware>();

// 添加内部 API 鉴权中间件（必须在路由之前，租户中间件之后）
app.UseMiddleware<InternalApiAuthMiddleware>();

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

app.Run();
