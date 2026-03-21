#!/usr/bin/env python3
"""
全量重建向量脚本

执行步骤：
1. 清空现有的向量集合
2. 从数据库读取所有文章
3. 重新构建向量并存储

使用方法：
python scripts/rebuild_all_vectors.py --tenant-id default
python scripts/rebuild_all_vectors.py --tenant-id default --limit 100
python scripts/rebuild_all_vectors.py --tenant-id default --no-clear
"""
import argparse
import time
from app.services.ingest_service import IngestService
from app.repositories.kb_article_repo import KbArticleRepository
from app.infra.embedding.openai_embedder import OpenAIEmbedder
from app.infra.vectorstore.chroma_store import ChromaVectorStore
from app.infra.db.sqlserver import SqlServer
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="全量重建向量脚本")
    parser.add_argument("--tenant-id", default="default", help="租户ID")
    parser.add_argument("--limit", type=int, help="限制处理的文章数量（用于测试）")
    parser.add_argument("--no-clear", action="store_true", help="不清空现有向量，追加模式")
    parser.add_argument("--batch-size", type=int, default=50, help="每批处理的文章数量")

    args = parser.parse_args()

    print("\n=== 全量重建向量脚本 ===")
    print(f"租户ID: {args.tenant_id}")
    print(f"限制数量: {args.limit or '无限制'}")
    print(f"清空现有向量: {'否' if args.no_clear else '是'}")
    print(f"批量大小: {args.batch_size}")
    print("=" * 50)

    try:
        # 初始化组件
        db = SqlServer()
        kb_repo = KbArticleRepository(db)
        vec_store = ChromaVectorStore()
        embedder = OpenAIEmbedder()
        ingest_service = IngestService(kb_repo, vec_store, embedder)

        # 步骤1：清空向量集合（如果需要）
        if not args.no_clear:
            print("\n[步骤1] 清空向量集合...")
            ingest_service.clear_vector_collection()
            print("向量集合已清空")

        # 统计信息
        total_articles = ingest_service.count_articles(args.tenant_id, "published")
        print(f"\n[信息] 租户 '{args.tenant_id}' 中共有 {total_articles} 篇已发布文章")

        if args.limit:
            total_articles = min(total_articles, args.limit)
            print(f"[信息] 限制处理 {total_articles} 篇文章")

        # 执行全量重建
        print(f"\n[步骤2] 开始全量重建向量...")
        start_time = time.time()

        result = ingest_service.rebuild_all(
            tenant_id=args.tenant_id,
            status="published",
            limit=args.limit,
            clear_first=False  # 已经手动清空过
        )

        # 计算耗时
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)

        # 打印结果
        print("\n" + "=" * 50)
        print("=== 重建完成 ===")
        print(f"总文章数: {result['total']}")
        print(f"成功处理: {result['success']}")
        print(f"失败处理: {result['failed']}")
        print(f"写入向量数: {result['upserted_total']}")
        if result['failed']:
            print("\n失败的文章:")
            for fail in result['failed']:
                print(f"  - ID {fail['article_id']}: {fail['error']}")

        print(f"\n耗时: {hours}小时 {minutes}分钟 {seconds}秒")
        if result['total'] > 0:
            avg_time = elapsed_time / result['total']
            print(f"平均每篇: {avg_time:.2f}秒")

        print("\n全量重建完成！")

    except Exception as e:
        logger.error("重建过程中出错: %s", e)
        print(f"\n错误: {e}")
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()