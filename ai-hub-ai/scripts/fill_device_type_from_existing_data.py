#!/usr/bin/env python3
"""
历史数据设备类型修复脚本

功能：
1. 扫描已有 kb_article 数据
2. 根据标题、tags、scope_json 推断设备类型
3. 更新 scope_json 字段
4. 输出修复统计报告

使用方法：
python scripts/fill_device_type_from_existing_data.py --tenant-id default --dry-run
python scripts/fill_device_type_from_existing_data.py --tenant-id default --batch-size 100
python scripts/fill_device_type_from_existing_data.py --tenant-id default --commit
"""
import argparse
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.infra.db.sqlserver import SqlServer, execute_query
from app.utils.device_type_utils import (
    parse_device_types_from_scope,
    normalize_device_type_name,
    extract_device_type_from_text,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 设备类型关键词映射
DEVICE_TYPE_KEYWORDS = {
    "MOULDING_MACHINE": ["造型", "射砂", "震实", "起模", "造型机", "YH", "混砂", "模板", "造型线"],
    "POURING_MACHINE": ["浇注", "保温", "熔炉", "液态", "浇注机", "JZ", "浇注线", "保温炉"],
    "SHOT_BLAST_MACHINE": ["抛丸", "清理", "喷砂", "打磨", "抛丸机", "PW", "清理线"],
}

# 反向映射：设备型号前缀
DEVICE_MODEL_PREFIX = {
    "MOULDING_MACHINE": ["YH"],
    "POURING_MACHINE": ["JZ"],
    "SHOT_BLAST_MACHINE": ["PW"],
}


def extract_device_type_from_content(title: str, question_text: str, tags: str) -> Optional[str]:
    """
    从内容中提取设备类型
    """
    if not title and not question_text:
        return None

    # 合并所有文本
    combined_text = f"{title or ''} {question_text or ''} {tags or ''}"
    combined_text = combined_text.lower()

    # 检查设备型号前缀
    for device_type, prefixes in DEVICE_MODEL_PREFIX.items():
        for prefix in prefixes:
            if combined_text.startswith(prefix.lower()) or f" {prefix.lower()}" in combined_text:
                logger.debug("通过设备型号前缀识别: %s -> %s", prefix, device_type)
                return device_type

    # 检查关键词
    for device_type, keywords in DEVICE_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in combined_text:
                logger.debug("通过关键词识别: %s -> %s", keyword, device_type)
                return device_type

    return None


def infer_device_type_from_existing_data(
    article_id: int,
    title: str,
    question_text: str,
    cause_text: str,
    solution_text: str,
    tags: str,
    existing_scope_json: str
) -> Tuple[str, str]:
    """
    推断设备的设备类型

    返回:
        device_type_code: 设备类型标准码
        updated_scope_json: 更新后的 scope_json
    """
    # 如果已有 scope_json 且包含设备类型，优先使用
    if existing_scope_json:
        try:
            existing_types = parse_device_types_from_scope(existing_scope_json)
            if existing_types and existing_types != ["COMMON"]:
                logger.debug("Article %s 已有设备类型: %s", article_id, existing_types)
                return existing_types[0], existing_scope_json
        except Exception as e:
            logger.warning("Article %s 解析 scope_json 失败: %s", article_id, e)

    # 尝试从内容中提取
    inferred_type = extract_device_type_from_content(title, question_text, tags)
    if inferred_type:
        # 构造新的 scope_json
        scope_data = {}
        if existing_scope_json:
            try:
                scope_data = json.loads(existing_scope_json)
            except:
                pass

        # 更新设备类型
        scope_data["设备类型"] = inferred_type

        # 构造设备型号（如果标题中有）
        if title:
            # 从标题中提取可能的型号
            for prefix, device_type in DEVICE_MODEL_PREFIX.items():
                if prefix in title:
                    scope_data["设备型号"] = title.split(prefix)[0] + prefix
                    break

        updated_scope_json = json.dumps(scope_data, ensure_ascii=False)
        logger.info("Article %s 推断设备类型: %s", article_id, inferred_type)
        return inferred_type, updated_scope_json

    # 无法推断，标记为通用
    return "COMMON", existing_scope_json or json.dumps({"设备类型": "通用"}, ensure_ascii=False)


def process_articles_batch(
    db: SqlServer,
    tenant_id: str,
    article_ids: List[int],
    dry_run: bool = True
) -> Dict[str, int]:
    """
    处理一批文章

    返回统计信息
    """
    stats = {
        "total": len(article_ids),
        "already_has_type": 0,
        "inferred_type": 0,
        "marked_common": 0,
        "no_change": 0,
        "failed": 0
    }

    # 查询文章数据
    placeholders = ",".join("?" * len(article_ids))
    sql = f"""
    SELECT
        id, title, question_text, cause_text, solution_text, tags, scope_json
    FROM dbo.kb_article
    WHERE id IN ({placeholders}) AND deleted_at IS NULL
    """
    rows = execute_query(sql, article_ids)

    # 准备更新语句
    update_sql = """
    UPDATE dbo.kb_article
    SET scope_json = ?, updated_at = GETDATE()
    WHERE id = ? AND deleted_at IS NULL
    """

    for row in rows:
        article_id = row["id"]
        title = row.get("title") or ""
        question_text = row.get("question_text") or ""
        cause_text = row.get("cause_text") or ""
        solution_text = row.get("solution_text") or ""
        tags = row.get("tags") or ""
        existing_scope_json = row.get("scope_json") or ""

        try:
            # 推断设备类型
            inferred_type, updated_scope_json = infer_device_type_from_existing_data(
                article_id,
                title,
                question_text,
                cause_text,
                solution_text,
                tags,
                existing_scope_json
            )

            # 检查是否需要更新
            if updated_scope_json != existing_scope_json:
                if inferred_type == "COMMON":
                    stats["marked_common"] += 1
                else:
                    stats["inferred_type"] += 1

                if not dry_run:
                    # 执行更新
                    execute_update = db.execute(
                        update_sql,
                        (updated_scope_json, article_id)
                    )
                    if execute_update:
                        logger.info("Article %s 更新成功: %s", article_id, inferred_type)
                    else:
                        stats["failed"] += 1
                        logger.error("Article %s 更新失败", article_id)
            else:
                stats["no_change"] += 1

            # 如果已有设备类型
            if parse_device_types_from_scope(existing_scope_json) != ["COMMON"]:
                stats["already_has_type"] += 1

        except Exception as e:
            stats["failed"] += 1
            logger.error("处理文章 %s 时出错: %s", article_id, e)

    return stats


def main():
    parser = argparse.ArgumentParser(description="历史数据设备类型修复脚本")
    parser.add_argument("--tenant-id", default="default", help="租户ID")
    parser.add_argument("--batch-size", type=int, default=50, help="每批处理数量")
    parser.add_argument("--dry-run", action="store_true", help="试运行模式，不实际更新数据库")
    parser.add_argument("--commit", action="store_true", help="提交更改到数据库")
    parser.add_argument("--start-id", type=int, default=0, help="开始处理的ID")
    parser.add_argument("--end-id", type=int, help="结束处理的ID（可选）")

    args = parser.parse_args()

    # 检查参数
    if args.dry_run and args.commit:
        print("错误：不能同时使用 --dry-run 和 --commit")
        return

    if not args.commit and not args.dry_run:
        print("警告：未指定 --commit，将使用试运行模式")
        args.dry_run = True

    print(f"\n=== 开始处理历史数据 ===")
    print(f"租户ID: {args.tenant_id}")
    print(f"批量大小: {args.batch_size}")
    print(f"试运行模式: {args.dry_run}")
    print(f"提交模式: {args.commit}")
    print(f"ID范围: {args.start_id} - {args.end_id or '无限制'}")
    print("=" * 50)

    # 连接数据库
    db = SqlServer()

    # 统计信息
    total_stats = {
        "total_processed": 0,
        "already_has_type": 0,
        "inferred_type": 0,
        "marked_common": 0,
        "no_change": 0,
        "failed": 0
    }

    try:
        # 获取需要处理的文章ID列表
        if args.end_id:
            sql = f"""
            SELECT id FROM dbo.kb_article
            WHERE tenant_id = ? AND id BETWEEN ? AND ? AND deleted_at IS NULL
            ORDER BY id
            """
            params = (args.tenant_id, args.start_id, args.end_id)
        else:
            sql = """
            SELECT id FROM dbo.kb_article
            WHERE tenant_id = ? AND id >= ? AND deleted_at IS NULL
            ORDER BY id
            """
            params = (args.tenant_id, args.start_id)

        all_ids = [r["id"] for r in execute_query(sql, params)]
        print(f"总共需要处理 {len(all_ids)} 条文章")

        # 分批处理
        for i in range(0, len(all_ids), args.batch_size):
            batch_ids = all_ids[i:i + args.batch_size]
            batch_num = i // args.batch_size + 1
            print(f"\n=== 处理第 {batch_num} 批 ({len(batch_ids)} 条) ===")

            # 处理这批文章
            batch_stats = process_articles_batch(
                db,
                args.tenant_id,
                batch_ids,
                args.dry_run
            )

            # 更新总统计
            for key in total_stats:
                total_stats[key] += batch_stats.get(key, 0)

            # 打印批次结果
            print(f"批次 {batch_num} 结果:")
            print(f"  总数: {batch_stats['total']}")
            print(f"  已有类型: {batch_stats['already_has_type']}")
            print(f"  推断出新类型: {batch_stats['inferred_type']}")
            print(f"  标记为通用: {batch_stats['marked_common']}")
            print(f"  无需修改: {batch_stats['no_change']}")
            print(f"  处理失败: {batch_stats['failed']}")

            if not args.dry_run and not args.commit:
                print("  注意：试运行模式，未实际更新数据库")

            # 模拟延迟
            import time
            time.sleep(0.1)

    except Exception as e:
        logger.error("处理过程中出错: %s", e)
    finally:
        db.close()

    # 打印最终统计
    print("\n" + "=" * 50)
    print("=== 最终统计 ===")
    print(f"总处理数: {total_stats['total_processed']}")
    print(f"已有设备类型: {total_stats['already_has_type']}")
    print(f"推断出新类型: {total_stats['inferred_type']}")
    print(f"标记为通用: {total_stats['marked_common']}")
    print(f"无需修改: {total_stats['no_change']}")
    print(f"处理失败: {total_stats['failed']}")

    if total_stats['total_processed'] > 0:
        success_rate = (total_stats['total_processed'] - total_stats['failed']) / total_stats['total_processed'] * 100
        print(f"成功率: {success_rate:.1f}%")

    # 生成报告文件
    report = {
        "timestamp": datetime.now().isoformat(),
        "tenant_id": args.tenant_id,
        "total_processed": total_stats['total_processed'],
        "statistics": total_stats,
        "note": "试运行模式" if args.dry_run else "实际执行模式"
    }

    report_file = f"device_type_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存到: {report_file}")
    print("=" * 50)


if __name__ == "__main__":
    main()