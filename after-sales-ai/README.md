# 造型机售后 AI 客服 H5 演示版

## 项目简介

这是一个用于演示的「造型机售后 AI 客服」H5 应用，不接数据库、不接真实大模型，所有数据使用 mock JSON + localStorage 持久化。

## 技术栈

- Vue 3
- Vite
- TypeScript
- Vue Router
- NaiveUI（可选，本项目使用手写移动端样式）

## 功能特性

1. **手机端 H5 界面**：聊天问答页（结构化回答卡片）、历史记录页、工单列表/详情页、设备选择
2. **数据留痕**：每次对话都写入 localStorage（模拟数据库），并能在历史记录里查询
3. **一键转人工**：聊天页点击「生成工单」，自动生成工单并跳转工单详情
4. **知识依据展示**：AI 回答卡片底部显示"参考知识片段"（mock）
5. **演示模式**：内置 3 套演示问题按钮（如报警码E101、送料异常、压力不稳），一键出答案
6. **数据持久化**：所有数据用 mock JSON + localStorage 持久化；页面刷新仍保留

## 安装依赖

```bash
npm install
```

## 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 构建生产版本

```bash
npm run build
```

## 项目结构

```
/src
  /mock                    # Mock 数据
    customers.json         # 客户数据
    devices.json           # 设备数据
    kb_samples.json        # 知识库样本
    demo_questions.json    # 演示问题
  /models
    types.ts              # 数据结构类型定义
  /store
    storage.ts            # localStorage 封装
    repositories.ts       # 仓储层
  /ai
    mock_ai.ts            # Mock AI 服务
    prompt_rules.md       # 结构化输出规范
  /router
    index.ts              # 路由配置
  /views                  # 页面组件
    Home.vue              # 入口页
    Chat.vue              # 聊天页
    History.vue           # 历史会话列表
    SessionDetail.vue     # 会话详情回放
    Tickets.vue           # 工单列表
    TicketDetail.vue      # 工单详情
    Admin.vue             # 管理页面
  /components             # 公共组件
    DevicePicker.vue
    ChatMessageBubble.vue
    AiAnswerCard.vue
    QuickQuestions.vue
    TicketStatusTag.vue
    JsonExportButton.vue
  App.vue
  main.ts
```

## 使用说明

### 1. 选择设备
在首页选择客户（可选）和设备，点击「进入客服」开始对话。

### 2. 聊天问答
- 可以手动输入问题
- 也可以点击快捷问题按钮快速提问
- AI 会返回结构化的回答卡片，包含：
  - 问题归类、报警码（如有）
  - 可能原因 TOP3
  - 排查步骤
  - 解决方案（临时/根因）
  - 风险提示
  - 参考知识片段

### 3. 生成工单
在 AI 回答卡片上点击「生成工单」，会自动创建工单并跳转到工单详情页。

### 4. 反馈
在 AI 回答卡片上可以点击「已解决」或「未解决」进行反馈。

### 5. 历史记录
- 查看所有历史会话
- 支持按设备筛选
- 点击会话可查看详情回放

### 6. 工单管理
- 查看所有工单
- 支持按设备和状态筛选
- 在工单详情页可以「模拟工程师处理」

### 7. 管理页面
- 查看统计数据
- 导出所有数据为 JSON
- 清空演示数据（会重新初始化 mock 数据）

## 数据存储

所有数据存储在浏览器的 localStorage 中，key 前缀为 `after_ai_v1`。

首次进入应用时会自动初始化 mock 数据（客户、设备）。

## 演示问题

内置的演示问题包括：
- 设备报警码 E101，怎么处理？
- 送料系统不进料，一直卡住
- 压力值不稳定，一直在波动
- 报警码 E205 是什么意思？
- 设备温度过高，报警了
- 报警码 E308，压力系统异常

## 注意事项

- 这是一个演示版本，所有 AI 回答都是预设的 mock 数据
- 数据存储在 localStorage，清除浏览器数据会丢失
- 管理页面的「清空演示数据」会重置所有数据并重新初始化 mock 数据
