using Microsoft.EntityFrameworkCore;
using ai_hub_service.Models;
using ai_hub_service.Modules.AiAudit.Entities;
using AiHub.Models;

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

    // ========== AI 审计表 ==========
    public DbSet<AiConversation> AiConversations { get; set; }
    public DbSet<AiMessage> AiMessages { get; set; }
    public DbSet<AiDecisionLog> AiDecisionLogs { get; set; }
    public DbSet<AiRetrievalLog> AiRetrievalLogs { get; set; }
    public DbSet<AiResponse> AiResponses { get; set; }

    /// <summary>
    /// 用户表
    /// </summary>
    public DbSet<User> Users { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // 配置 KnowledgeArticle 实体（kb_article）
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

        // 配置 Asset 实体（kb_asset）
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

        // 配置 KnowledgeChunk 实体（kb_chunk）
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

        // ========== AI 审计表配置 ==========

        // ai_conversation
        modelBuilder.Entity<AiConversation>(entity =>
        {
            entity.ToTable("ai_conversation");
            entity.HasKey(e => e.ConversationId);
            entity.Property(e => e.ConversationId).HasColumnName("conversation_id");
            entity.Property(e => e.TenantId).HasColumnName("tenant_id").HasMaxLength(64).IsRequired();
            entity.Property(e => e.UserId).HasColumnName("user_id").HasMaxLength(64);
            entity.Property(e => e.Channel).HasColumnName("channel").HasMaxLength(32).IsRequired();
            entity.Property(e => e.StartedAt).HasColumnName("started_at").IsRequired();
            entity.Property(e => e.EndedAt).HasColumnName("ended_at");
            entity.Property(e => e.MetaJson).HasColumnName("meta_json").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasIndex(e => new { e.TenantId, e.StartedAt }).IsDescending(false, true);
            entity.HasIndex(e => new { e.UserId, e.StartedAt }).IsDescending(false, true);
        });

        // ai_message
        modelBuilder.Entity<AiMessage>(entity =>
        {
            entity.ToTable("ai_message");
            entity.HasKey(e => e.MessageId);
            entity.Property(e => e.MessageId).HasColumnName("message_id");
            entity.Property(e => e.ConversationId).HasColumnName("conversation_id").IsRequired();
            entity.Property(e => e.Role).HasColumnName("role").HasMaxLength(16).IsRequired();
            entity.Property(e => e.Content).HasColumnName("content").HasColumnType("NVARCHAR(MAX)").IsRequired();
            entity.Property(e => e.ContentLen).HasColumnName("content_len");
            entity.Property(e => e.IsMasked).HasColumnName("is_masked");
            entity.Property(e => e.MaskedContent).HasColumnName("masked_content").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasOne(e => e.Conversation)
                  .WithMany(c => c.Messages)
                  .HasForeignKey(e => e.ConversationId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(e => new { e.ConversationId, e.CreatedAt });
            entity.HasIndex(e => new { e.Role, e.CreatedAt });
        });

        // ai_decision_log
        modelBuilder.Entity<AiDecisionLog>(entity =>
        {
            entity.ToTable("ai_decision_log");
            entity.HasKey(e => e.MessageId);
            entity.Property(e => e.MessageId).HasColumnName("message_id");
            entity.Property(e => e.IntentType).HasColumnName("intent_type").HasMaxLength(64).IsRequired();
            entity.Property(e => e.Confidence).HasColumnName("confidence").HasColumnType("DECIMAL(5,4)");
            entity.Property(e => e.ModelName).HasColumnName("model_name").HasMaxLength(128);
            entity.Property(e => e.PromptVersion).HasColumnName("prompt_version").HasMaxLength(32);
            entity.Property(e => e.UseKnowledge).HasColumnName("use_knowledge");
            entity.Property(e => e.FallbackReason).HasColumnName("fallback_reason").HasMaxLength(128);
            entity.Property(e => e.TokensIn).HasColumnName("tokens_in");
            entity.Property(e => e.TokensOut).HasColumnName("tokens_out");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasOne(e => e.Message)
                  .WithOne(m => m.DecisionLog)
                  .HasForeignKey<AiDecisionLog>(e => e.MessageId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(e => new { e.IntentType, e.CreatedAt });
            entity.HasIndex(e => e.ModelName);
        });

        // ai_retrieval_log
        modelBuilder.Entity<AiRetrievalLog>(entity =>
        {
            entity.ToTable("ai_retrieval_log");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id").UseIdentityColumn();
            entity.Property(e => e.MessageId).HasColumnName("message_id").IsRequired();
            entity.Property(e => e.DocId).HasColumnName("doc_id").HasMaxLength(64).IsRequired();
            entity.Property(e => e.DocTitle).HasColumnName("doc_title").HasMaxLength(256);
            entity.Property(e => e.Score).HasColumnName("score").HasColumnType("DECIMAL(8,6)");
            entity.Property(e => e.Rank).HasColumnName("rank");
            entity.Property(e => e.ChunkId).HasColumnName("chunk_id").HasMaxLength(64);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasOne(e => e.Message)
                  .WithMany(m => m.RetrievalLogs)
                  .HasForeignKey(e => e.MessageId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(e => e.MessageId);
            entity.HasIndex(e => e.DocId);
        });

        // ai_response
        modelBuilder.Entity<AiResponse>(entity =>
        {
            entity.ToTable("ai_response");
            entity.HasKey(e => e.MessageId);
            entity.Property(e => e.MessageId).HasColumnName("message_id");
            entity.Property(e => e.FinalAnswer).HasColumnName("final_answer").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.ResponseTimeMs).HasColumnName("response_time_ms");
            entity.Property(e => e.IsSuccess).HasColumnName("is_success");
            entity.Property(e => e.ErrorType).HasColumnName("error_type").HasMaxLength(64);
            entity.Property(e => e.ErrorDetail).HasColumnName("error_detail").HasColumnType("NVARCHAR(MAX)");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasOne(e => e.Message)
                  .WithOne(m => m.Response)
                  .HasForeignKey<AiResponse>(e => e.MessageId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(e => e.ResponseTimeMs);
            entity.HasIndex(e => e.IsSuccess);
        });

        // 配置 User 实体
        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("users");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id)
                  .HasColumnName("id")
                  .HasMaxLength(64)
                  .HasDefaultValueSql("NEWID()");
            entity.Property(e => e.Account).HasColumnName("account").HasMaxLength(100).IsRequired();
            entity.Property(e => e.PasswordHash).HasColumnName("password_hash").HasMaxLength(256).IsRequired();
            entity.Property(e => e.Status).HasColumnName("status").HasMaxLength(16).IsRequired();
            entity.Property(e => e.DeviceMN).HasColumnName("device_mn").HasMaxLength(50);
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();
            entity.Property(e => e.UpdatedAt).HasColumnName("updated_at").IsRequired();

            // 索引
            entity.HasIndex(e => e.Account).IsUnique();
            entity.HasIndex(e => e.Status);
            entity.HasIndex(e => e.CreatedAt);
        });
    }
}
