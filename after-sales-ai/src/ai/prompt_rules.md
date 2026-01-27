# AI 结构化输出规范

## 输出字段要求

1. **issueCategory** (string): 问题分类
   - 可选值：报警码、送料异常、压力异常、温度异常、其他

2. **alarmCode** (string?, 可选): 报警码（如 E101、E205、E308）

3. **confidence** (number, 0-1): 置信度

4. **topCauses** (string[]): 可能原因 TOP3

5. **steps** (array): 排查步骤
   - title: 步骤标题
   - action: 具体操作
   - expect: 预期现象
   - next: 下一步建议

6. **solution** (object): 解决方案
   - temporary: 临时处理方案
   - final: 根本解决方案

7. **safetyTip** (string): 安全提示

8. **citedDocs** (array): 参考知识片段（2-3条）

9. **shouldEscalate** (boolean): 是否需要转人工

10. **shortAnswerText** (string): 简短回答文本（用于消息气泡）
