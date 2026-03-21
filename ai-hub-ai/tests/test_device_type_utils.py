"""设备类型解析工具测试"""
import unittest
from app.utils.device_type_utils import (
    parse_device_types_from_scope,
    normalize_device_type_name,
    is_common_device_type,
    format_device_types_for_display,
    extract_device_type_from_text,
    infer_device_type_from_model_or_label,
    resolve_device_type_for_query,
    scope_label_for_excel_import,
)


class TestDeviceTypeUtils(unittest.TestCase):
    """设备类型工具类测试"""

    def test_parse_device_types_from_scope_empty(self):
        """测试空 scope_json"""
        result = parse_device_types_from_scope(None)
        self.assertEqual(result, ["COMMON"])

        result = parse_device_types_from_scope("")
        self.assertEqual(result, ["COMMON"])

        result = parse_device_types_from_scope("   ")
        self.assertEqual(result, ["COMMON"])

    def test_parse_device_types_from_scope_valid_json(self):
        """测试有效的 JSON"""
        scope_json = '{"设备类型": "造型机"}'
        result = parse_device_types_from_scope(scope_json)
        self.assertEqual(result, ["MOULDING_MACHINE"])

    def test_parse_device_types_from_scope_multiple_types(self):
        """测试多设备类型"""
        scope_json = '{"设备类型": "造型机,浇注机"}'
        result = parse_device_types_from_scope(scope_json)
        self.assertEqual(set(result), {"MOULDING_MACHINE", "POURING_MACHINE"})

    def test_parse_device_types_from_scope_with_spaces(self):
        """测试带空格的设备类型"""
        scope_json = '{"设备类型": "造型机, 浇注机"}'
        result = parse_device_types_from_scope(scope_json)
        self.assertEqual(set(result), {"MOULDING_MACHINE", "POURING_MACHINE"})

    def test_parse_device_types_from_scope_invalid_json(self):
        """测试无效的 JSON"""
        result = parse_device_types_from_scope("invalid json")
        self.assertEqual(result, ["COMMON"])

    def test_parse_device_types_from_scope_with_device_model(self):
        """测试设备型号映射"""
        scope_json = '{"设备类型": "YH500"}'
        result = parse_device_types_from_scope(scope_json)
        self.assertEqual(result, ["MOULDING_MACHINE"])

    def test_normalize_typo_paowaji(self):
        self.assertEqual(normalize_device_type_name("抛瓦机"), "SHOT_BLAST_MACHINE")

    def test_normalize_device_type_name(self):
        """测试设备类型名称标准化"""
        # 中文映射
        self.assertEqual(normalize_device_type_name("造型机"), "MOULDING_MACHINE")
        self.assertEqual(normalize_device_type_name("浇注机"), "POURING_MACHINE")
        self.assertEqual(normalize_device_type_name("抛丸机"), "SHOT_BLAST_MACHINE")
        self.assertEqual(normalize_device_type_name("通用"), "COMMON")

        # 标准码映射
        self.assertEqual(normalize_device_type_name("MOULDING_MACHINE"), "MOULDING_MACHINE")

        # 设备型号映射
        self.assertEqual(normalize_device_type_name("YH500"), "MOULDING_MACHINE")

        # 无效输入
        self.assertIsNone(normalize_device_type_name(""))
        self.assertIsNone(normalize_device_type_name(None))

    def test_is_common_device_type(self):
        """测试通用知识判断"""
        # 通用知识
        self.assertTrue(is_common_device_type(["COMMON"]))
        self.assertTrue(is_common_device_type([]))

        # 非通用知识
        self.assertFalse(is_common_device_type(["MOULDING_MACHINE"]))
        self.assertFalse(is_common_device_type(["MOULDING_MACHINE", "COMMON"]))

    def test_format_device_types_for_display(self):
        """测试设备类型显示格式化"""
        # 单个设备类型
        self.assertEqual(format_device_types_for_display(["MOULDING_MACHINE"]), "造型机")

        # 多个设备类型
        result = format_device_types_for_display(["MOULDING_MACHINE", "POURING_MACHINE"])
        self.assertTrue("造型机" in result and "浇注机" in result)

        # 通用
        self.assertEqual(format_device_types_for_display(["COMMON"]), "通用")

    def test_extract_device_type_from_text(self):
        """测试从文本提取设备类型"""
        # 造型机相关
        self.assertEqual(extract_device_type_from_text("YH500造型机故障"), "MOULDING_MACHINE")
        self.assertEqual(extract_device_type_from_text("射砂系统问题"), "MOULDING_MACHINE")

        # 浇注机相关
        self.assertEqual(extract_device_type_from_text("JZ-200浇注机报警"), "POURING_MACHINE")
        self.assertEqual(extract_device_type_from_text("保温炉温度异常"), "POURING_MACHINE")

        # 抛丸机相关
        self.assertEqual(extract_device_type_from_text("PW-150抛丸机清理"), "SHOT_BLAST_MACHINE")
        self.assertEqual(extract_device_type_from_text("喷砂嘴磨损"), "SHOT_BLAST_MACHINE")

        # 无匹配
        self.assertIsNone(extract_device_type_from_text("普通文档"))

    def test_infer_device_type_from_model_or_label(self):
        self.assertEqual(infer_device_type_from_model_or_label("YH500"), "MOULDING_MACHINE")
        self.assertEqual(infer_device_type_from_model_or_label("yh-600"), "MOULDING_MACHINE")
        self.assertEqual(infer_device_type_from_model_or_label("JZ-200"), "POURING_MACHINE")
        self.assertEqual(infer_device_type_from_model_or_label("造型机"), "MOULDING_MACHINE")

    def test_resolve_device_type_for_query(self):
        self.assertEqual(
            resolve_device_type_for_query("MOULDING_MACHINE", "JZ-200"),
            "MOULDING_MACHINE",
        )
        self.assertEqual(resolve_device_type_for_query(None, "YH500"), "MOULDING_MACHINE")
        self.assertEqual(resolve_device_type_for_query("", "PW-250"), "SHOT_BLAST_MACHINE")
        self.assertIsNone(resolve_device_type_for_query(None, None))
        self.assertIsNone(resolve_device_type_for_query(None, "未知型号XYZ"))

    def test_scope_label_for_excel_import(self):
        self.assertIsNone(scope_label_for_excel_import(None))
        self.assertIsNone(scope_label_for_excel_import(""))
        self.assertIsNone(scope_label_for_excel_import("  "))
        self.assertEqual(scope_label_for_excel_import("造型机"), "造型机")
        self.assertEqual(scope_label_for_excel_import("MOULDING_MACHINE"), "造型机")
        self.assertEqual(scope_label_for_excel_import("通用"), "通用")
        with self.assertRaises(ValueError):
            scope_label_for_excel_import("火星机")


if __name__ == "__main__":
    unittest.main()