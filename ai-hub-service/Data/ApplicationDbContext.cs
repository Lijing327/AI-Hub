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
    /// 知识条目表
    /// </summary>
    public DbSet<KnowledgeItem> KnowledgeItems { get; set; }

    /// <summary>
    /// 知识附件表
    /// </summary>
    public DbSet<Attachment> Attachments { get; set; }

    /// <summary>
    /// 知识块表（用于向量化）
    /// </summary>
    public DbSet<KnowledgeChunk> KnowledgeChunks { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // 配置KnowledgeItem实体
        modelBuilder.Entity<KnowledgeItem>(entity =>
        {
            entity.ToTable("kb_item");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Title).HasColumnName("title").HasMaxLength(500).IsRequired();
            entity.Property(e => e.QuestionText).HasColumnName("question_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.CauseText).HasColumnName("cause_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.SolutionText).HasColumnName("solution_text").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.ScopeJson).HasColumnName("scope_json").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.Tags).HasColumnName("tags").HasMaxLength(1000);
            entity.Property(e => e.Status).HasColumnName("status").HasMaxLength(20).IsRequired();
            entity.Property(e => e.Version).HasColumnName("version").HasDefaultValue(1);
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").HasMaxLength(50);
            entity.Property(e => e.CreatedBy).HasColumnName("created_by").HasMaxLength(100);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at");
            entity.Property(e => e.PublishedAt).HasColumnName("published_at");

            // 索引
            entity.HasIndex(e => e.Status);
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.CreatedAt);
        });

        // 配置Attachment实体
        modelBuilder.Entity<Attachment>(entity =>
        {
            entity.ToTable("kb_attachment");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.KnowledgeItemId).HasColumnName("knowledge_item_id").IsRequired();
            entity.Property(e => e.FileName).HasColumnName("file_name").HasMaxLength(500).IsRequired();
            entity.Property(e => e.FilePath).HasColumnName("file_path").HasMaxLength(1000).IsRequired();
            entity.Property(e => e.FileUrl).HasColumnName("file_url").HasMaxLength(1000).IsRequired();
            entity.Property(e => e.FileType).HasColumnName("file_type").HasMaxLength(50).IsRequired();
            entity.Property(e => e.FileSize).HasColumnName("file_size");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            // 外键关系
            entity.HasOne(e => e.KnowledgeItem)
                  .WithMany(k => k.Attachments)
                  .HasForeignKey(e => e.KnowledgeItemId)
                  .OnDelete(DeleteBehavior.Cascade);
        });

        // 配置KnowledgeChunk实体
        modelBuilder.Entity<KnowledgeChunk>(entity =>
        {
            entity.ToTable("kb_chunk");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.KnowledgeItemId).HasColumnName("knowledge_item_id").IsRequired();
            entity.Property(e => e.ChunkText).HasColumnName("chunk_text").HasColumnType("NVARCHAR(MAX)").IsRequired();
            entity.Property(e => e.ChunkIndex).HasColumnName("chunk_index").IsRequired();
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            // 外键关系
            entity.HasOne(e => e.KnowledgeItem)
                  .WithMany(k => k.Chunks)
                  .HasForeignKey(e => e.KnowledgeItemId)
                  .OnDelete(DeleteBehavior.Cascade);

            // 索引
            entity.HasIndex(e => e.KnowledgeItemId);
        });
    }
}
