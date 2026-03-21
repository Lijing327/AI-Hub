"""QueryService 测试"""
import unittest
from unittest.mock import Mock, MagicMock
from app.services.query_service import QueryService
from app.repositories.vector_repo import VectorRepository
from app.infra.embedding.base import IEmbedder


class TestQueryService(unittest.TestCase):
    """QueryService 测试"""

    def setUp(self):
        """测试初始化"""
        self.mock_vec_repo = Mock(spec=VectorRepository)
        self.mock_embedder = Mock(spec=IEmbedder)
        self.query_service = QueryService(self.mock_vec_repo, self.mock_embedder)

    def test_query_without_device_type(self):
        """测试不带设备类型的查询（保持原有逻辑）"""
        # 模拟嵌入
        self.mock_embedder.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        # 模拟向量检索结果
        mock_results = [
            {
                "id": "default:kb:1:q",
                "score": 0.1,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 1,
                    "type": "q",
                    "status": "published",
                    "version": 1,
                    "tags": "故障",
                }
            },
            {
                "id": "default:kb:2:q",
                "score": 0.2,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 2,
                    "type": "q",
                    "status": "published",
                    "version": 1,
                    "tags": "报警",
                }
            }
        ]
        self.mock_vec_repo.query.return_value = mock_results

        # 执行查询
        result = self.query_service.query(
            tenant_id="default",
            query_text="设备故障",
            top_k=5,
            device_type_code=None
        )

        # 验证调用
        self.mock_embedder.embed_texts.assert_called_once_with(["设备故障"])
        self.mock_vec_repo.query.assert_called_once_with(
            embedding=[0.1, 0.2, 0.3],
            top_k=15,  # max(5*3, 10)
            where={"tenant_id": "default"}
        )

        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["article_id"], 2)  # 分数最高的在前
        self.assertEqual(result[0]["score"], 0.95)  # 1/(1+0.05) after weighting
        self.assertEqual(result[0]["hit_type"], "q")

    def test_query_with_device_type(self):
        """测试带设备类型的查询"""
        # 模拟嵌入
        self.mock_embedder.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        # 模拟向量检索结果
        mock_results = [
            {
                "id": "default:kb:1:q:MOULDING_MACHINE",
                "score": 0.1,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 1,
                    "type": "q",
                    "device_type_code": "MOULDING_MACHINE",
                    "is_common": False,
                }
            },
            {
                "id": "default:kb:2:q:COMMON",
                "score": 0.2,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 2,
                    "type": "q",
                    "device_type_code": "COMMON",
                    "is_common": True,
                }
            }
        ]
        self.mock_vec_repo.query.return_value = mock_results

        # 执行查询
        result = self.query_service.query(
            tenant_id="default",
            query_text="造型机故障",
            top_k=5,
            device_type_code="MOULDING_MACHINE"
        )

        # 验证调用 - 应该查询设备类型和通用知识
        expected_where = {
            "$or": [
                {"device_type_code": "MOULDING_MACHINE"},
                {"device_type_code": "COMMON"}
            ],
            "$and": [{"tenant_id": "default"}]
        }
        self.mock_vec_repo.query.assert_called_with(
            embedding=[0.1, 0.2, 0.3],
            top_k=15,
            where=expected_where
        )

        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["article_id"], 2)  # 通用知识分数更高
        self.assertEqual(result[0]["device_type_code"], "COMMON")

    def test_query_with_device_type_fallback(self):
        """测试带设备类型的查询和兜底机制"""
        # 模拟嵌入
        self.mock_embedder.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        # 第一阶段结果很少（触发兜底）
        mock_primary_results = [
            {
                "id": "default:kb:1:q:MOULDING_MACHINE",
                "score": 0.1,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 1,
                    "type": "q",
                    "device_type_code": "MOULDING_MACHINE",
                    "is_common": False,
                }
            }
        ]
        self.mock_vec_repo.query.return_value = mock_primary_results

        # 第二阶段结果
        mock_fallback_results = [
            {
                "id": "default:kb:3:q:POURING_MACHINE",
                "score": 0.3,
                "metadata": {
                    "tenant_id": "default",
                    "article_id": 3,
                    "type": "q",
                    "device_type_code": "POURING_MACHINE",
                    "is_common": False,
                }
            }
        ]
        self.mock_vec_repo.query.return_value = mock_fallback_results

        # 执行查询
        result = self.query_service.query(
            tenant_id="default",
            query_text="设备故障",
            top_k=5,
            device_type_code="MOULDING_MACHINE",
            enable_fallback=True
        )

        # 验证结果包含两个阶段的内容
        self.assertEqual(len(result), 2)
        # 第一阶段的结果
        primary_result = next(r for r in result if r["article_id"] == 1)
        self.assertEqual(primary_result["source"], None)  # 不是兜底结果
        # 第二阶段的结果
        fallback_result = next(r for r in result if r["article_id"] == 3)
        self.assertEqual(fallback_result["source"], "fallback")

    def test_need_fallback_insufficient_results(self):
        """测试需要兜底 - 结果不足"""
        # 只有1个结果，需要top_k=5
        hits = [{"article_id": 1, "score": 0.8}]
        self.assertTrue(self.query_service._need_fallback(hits, 5))

        # 有足够结果，但分数很低
        hits = [{"article_id": 1, "score": 0.3}]
        self.assertTrue(self.query_service._need_fallback(hits, 1))

        # 足够的结果和分数
        hits = [{"article_id": 1, "score": 0.8}, {"article_id": 2, "score": 0.7}]
        self.assertFalse(self.query_service._need_fallback(hits, 2))


if __name__ == "__main__":
    unittest.main()