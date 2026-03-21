"""Chunker 测试"""
import unittest
from unittest.mock import patch
from app.schemas.kb_article import KbArticle
from app.services.chunker import build_chunks


class TestChunker(unittest.TestCase):
    """Chunker 测试"""

    def setUp(self):
        """测试初始化"""
        self.article = KbArticle(
            id=1,
            tenant_id="default",
            title="造型机射砂问题",
            question_text="设备无法射砂怎么办？",
            cause_text="射砂管堵塞",
            solution_text="清理射砂管",
            tags="故障",
            scope_json='{"设备类型": "造型机", "设备型号": "YH500"}',
            status="published",
            version=1
        )

    @patch('app.services.chunker.json.loads')
    def test_build_chunks_with_device_type(self, mock_json):
        """测试带设备类型的 chunk 生成"""
        # 模拟 JSON 解析
        mock_json.return_value = {"设备类型": "造型机", "设备型号": "YH500"}

        # 执行 chunk 生成
        chunks = build_chunks(self.article)

        # 验证生成了正确的 chunk 数量（q、c、t）
        self.assertEqual(len(chunks), 3)

        # 验证每个 chunk 都包含设备类型信息
        for chunk in chunks:
            self.assertIn("device_type_code", chunk["metadata"])
            self.assertEqual(chunk["metadata"]["device_type_code"], "MOULDING_MACHINE")
            self.assertFalse(chunk["metadata"]["is_common"])
            self.assertIn("设备类型:造型机", chunk["doc"])
            self.assertIn("设备型号:YH500", chunk["doc"])

    def test_build_chunks_without_scope(self):
        """测试没有 scope_json 的情况"""
        article = KbArticle(
            id=1,
            tenant_id="default",
            title="设备问题",
            question_text="设备故障",
            cause_text="原因未知",
            solution_text="解决方案",
            tags="故障",
            scope_json=None,
            status="published",
            version=1
        )

        # 执行 chunk 生成
        chunks = build_chunks(article)

        # 验证为通用知识
        for chunk in chunks:
            self.assertEqual(chunk["metadata"]["device_type_code"], "COMMON")
            self.assertTrue(chunk["metadata"]["is_common"])

    def test_build_chunks_common_only(self):
        """测试通用知识"""
        article = KbArticle(
            id=1,
            tenant_id="default",
            title="通用问题",
            question_text="设备一般问题",
            cause_text="原因",
            solution_text="解决方案",
            tags="通用",
            scope_json='{"设备类型": "通用"}',
            status="published",
            version=1
        )

        # 执行 chunk 生成
        chunks = build_chunks(article)

        # 验证为通用知识
        for chunk in chunks:
            self.assertEqual(chunk["metadata"]["device_type_code"], "COMMON")
            self.assertTrue(chunk["metadata"]["is_common"])

    def test_build_chunks_multiple_device_types(self):
        """测试多设备类型"""
        article = KbArticle(
            id=1,
            tenant_id="default",
            title="多设备问题",
            question_text="设备故障",
            cause_text="原因",
            solution_text="解决方案",
            tags="多设备",
            scope_json='{"设备类型": "造型机,浇注机"}',
            status="published",
            version=1
        )

        # 执行 chunk 生成
        chunks = build_chunks(article)

        # 验证为每个设备类型生成了 chunk
        device_types = set()
        for chunk in chunks:
            device_types.add(chunk["metadata"]["device_type_code"])

        self.assertEqual(device_types, {"MOULDING_MACHINE", "POURING_MACHINE"})
        self.assertEqual(len(chunks), 6)  # 2设备类型 × 3chunk类型

    def test_build_chunks_inferred_type(self):
        """测试从标题推断设备类型"""
        article = KbArticle(
            id=1,
            tenant_id="default",
            title="YH600射砂故障",
            question_text="射砂不工作",
            cause_text="射砂管堵塞",
            solution_text="清理射砂管",
            tags="故障",
            scope_json=None,  # 没有 scope_json
            status="published",
            version=1
        )

        # 执行 chunk 生成
        chunks = build_chunks(article)

        # 验证推断出设备类型
        for chunk in chunks:
            self.assertEqual(chunk["metadata"]["device_type_code"], "MOULDING_MACHINE")
            self.assertFalse(chunk["metadata"]["is_common"])


if __name__ == "__main__":
    unittest.main()