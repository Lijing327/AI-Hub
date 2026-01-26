#!/bin/bash
# Python 服务 Excel 导入测试脚本

BASE_URL="http://localhost:8000"
EXCEL_FILE="test.xlsx"  # 替换为实际的 Excel 文件路径

echo "=== 测试 Excel 导入 ==="

if [ ! -f "$EXCEL_FILE" ]; then
    echo "错误: Excel 文件不存在: $EXCEL_FILE"
    echo "请创建一个测试 Excel 文件，包含以下列："
    echo "  设备型号 | 故障现象 | 报警信息 | 原因分析 | 处理方法"
    exit 1
fi

curl -X POST "$BASE_URL/import/excel" \
  -F "file=@$EXCEL_FILE" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "测试完成！"
