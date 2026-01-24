using Microsoft.EntityFrameworkCore;
using ai_hub_service.Models;

namespace ai_hub_service.Data;

/// <summary>
/// 应用程序数据库上下文
/// </summary>
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    /// <summary>
    /// 知识主表（kb_article）
    /// </summary>
    public DbSet<KnowledgeArticle> KnowledgeArticles { get; set; }

    /// <summary>
    /// 附件表（kb_asset）
    /// </summary>
    public DbSet<Asset> Assets { get; set; }

    /// <summary>
    /// 入库切片表（kb_chunk）
    /// </summary>
    public DbSet<KnowledgeChunk> KnowledgeChunks { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // 配置KnowledgeArticle实体（kb_article）
        modelBuilder.Entity<KnowledgeArticle>(entity =>
        {
            entity.ToTable("kb_article");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").HasMaxLength(50);
            entity.Property(e => e.Title).HasColumnName("title").HasMaxLength(500).IsRequired();
            entity.Property(e => e.QuestionText).HasColumnName("question_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.CauseText).HasColumnName("cause_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.SolutionText).HasColumnName("solution_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.ScopeJson).HasColumnName("scope_json").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.Tags).HasColumnName("tags").HasMaxLength(1000);
            entity.Property(e => e.Status).HasColumnName("status").HasMaxLength(20).IsRequired();
            entity.Property(e => e.Version).HasColumnName("version").HasDefaultValue(1);
            entity.Property(e => e.CreatedBy).HasColumnName("created_by").HasMaxLength(100);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at");
            entity.Property(e => e.PublishedAt).HasColumnName("published_at");
            entity.Property(e => e.DeletedAt).HasColumnName("deleted_at");

            // 索引
            entity.HasIndex(e => e.DeletedAt);
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.Status);
            entity.HasIndex(e => e.CreatedAt);
            entity.HasIndex(e => new { e.TenantId, e.Status });
        });

        // 配置Asset实体（kb_asset）
        modelBuilder.Entity<Asset>(entity =>
        {
            entity.ToTable("kb_asset");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").HasMaxLength(50);
            entity.Property(e => e.ArticleId).HasColumnName("article_id").IsRequired();
            entity.Property(e => e.AssetType).HasColumnName("asset_type").HasMaxLength(50).IsRequired();
            entity.Property(e => e.FileName).HasColumnName("file_name").HasMaxLength(500).IsRequired();
            entity.Property(e => e.Url).HasColumnName("url").HasMaxLength(1000).IsRequired();
            entity.Property(e => e.Size).HasColumnName("size");
            entity.Property(e => e.Duration).HasColumnName("duration");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();
            entity.Property(e => e.DeletedAt).HasColumnName("deleted_at");

            // 外键关系
            entity.HasOne(e => e.Article)
                  .WithMany(a => a.Assets)
                  .HasForeignKey(e => e.ArticleId)
                  .OnDelete(DeleteBehavior.Cascade);

            // 索引
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.ArticleId);
            entity.HasIndex(e => e.AssetType);
            entity.HasIndex(e => e.DeletedAt);
        });

        // 配置KnowledgeChunk实体（kb_chunk）
        modelBuilder.Entity<KnowledgeChunk>(entity =>
        {
            entity.ToTable("kb_chunk");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").HasMaxLength(50);
            entity.Property(e => e.ArticleId).HasColumnName("article_id").IsRequired();
            entity.Property(e => e.ChunkIndex).HasColumnName("chunk_index").IsRequired();
            entity.Property(e => e.ChunkText).HasColumnName("chunk_text").HasColumnType("NVARCHAR(MAX)").IsRequired();
            entity.Property(e => e.Hash).HasColumnName("hash").HasMaxLength(64);
            entity.Property(e => e.SourceFields).HasColumnName("source_fields").HasMaxLength(100);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            // 外键关系
            entity.HasOne(e => e.Article)
                  .WithMany(a => a.Chunks)
                  .HasForeignKey(e => e.ArticleId)
                  .OnDelete(DeleteBehavior.Cascade);

            // 索引
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.ArticleId);
            entity.HasIndex(e => e.Hash);
        });
    }
}
