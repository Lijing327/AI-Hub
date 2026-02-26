# Vue DevTools 不显示 - 排查报告

## 一、环境确认

### 1.1 项目与启动命令

| 项目 | 启动命令 | 端口 | base 路径 | 路由示例 |
|------|----------|------|-----------|----------|
| **after-sales-ai** | `npm run dev` | 3000 | `/cs/` | localhost:3000/cs/#/chat |
| **knowledgebase-frontend** | `npm run dev` | 5173 | `/` (dev) | localhost:5173/#/knowledge |

- **必须使用 `npm run dev`**，不能使用 `npm run preview`（preview 是生产构建，DevTools 会被剥离）
- 若使用 `npm run build` + `npm run preview`，Vue 会走 production 模式，DevTools 无法注入

### 1.2 Vue 与 DevTools 版本

- **Vue**: 3.4.x（两个项目一致）
- **Vue DevTools**: 需 v6+ 才能识别 Vue 3
- 兼容性：✅ 满足

### 1.3 路径说明

- 你提到的 `localhost:4000/cs/#/knowledge`：
  - **after-sales-ai** 有 `/cs/` 但**无** `/knowledge` 路由（有 /chat、/home、/history 等）
  - **knowledgebase-frontend** 有 `/knowledge` 路由，dev 时 base 为 `/`，访问 `localhost:5173/#/knowledge`
  - 若通过 Nginx/网关在 4000 端口代理，需确认实际代理到哪个前端及 base 路径

## 二、代码层排查结果

### 2.1 未发现显式关闭 DevTools

- 未发现 `app.config.devtools = false`
- 未发现 `__VUE_PROD_DEVTOOLS__`、`__VUE_OPTIONS_API__` 等 define
- 未发现“生产/预览模式禁用 devtools”的逻辑

### 2.2 已做修复

在 `main.ts` 中**显式启用** DevTools（仅开发环境）：

```ts
if (import.meta.env.DEV) {
  app.config.devtools = true
}
```

- **after-sales-ai/src/main.ts**：已添加
- **knowledgebase-frontend/src/main.ts**：已添加

作用：避免子路径（如 `/cs/`）、构建配置等导致 DevTools 未被正确识别。

## 三、根因与修复摘要

### 根因（最可能）

1. **运行模式错误**：使用了 `npm run preview` 或 `npm run build` 后的静态服务，而非 `npm run dev`，导致 production 构建，DevTools 被剥离。
2. **未显式启用 devtools**：在子路径、多应用等场景下，DevTools 可能未自动检测到，需显式设置 `app.config.devtools = true`。

### 修复内容

| 文件 | 改动 |
|------|------|
| `after-sales-ai/src/main.ts` | 在 `import.meta.env.DEV` 时设置 `app.config.devtools = true` |
| `knowledgebase-frontend/src/main.ts` | 同上 |

## 四、验证步骤

1. **确认使用 dev 模式**
   ```bash
   cd after-sales-ai   # 或 knowledgebase-frontend
   npm run dev
   ```

2. **访问对应地址**
   - after-sales-ai: `http://localhost:3000/cs/#/chat`
   - knowledgebase-frontend: `http://localhost:5173/#/knowledge`

3. **在 Console 中检查**
   ```js
   // 应能看到 Vue 相关对象
   window.__VUE__
   window.__VUE_DEVTOOLS_GLOBAL_HOOK__
   ```

4. **检查 Chrome 扩展**
   - Vue DevTools 图标应显示“已检测到”或类似状态
   - 打开 DevTools → Vue 面板应可正常使用

5. **若仍不显示**
   - 确认 Vue DevTools 为 v6+
   - 扩展设置中勾选“允许访问文件 URL”
   - 关闭可能冲突的扩展（如 React DevTools）
   - 刷新页面或重启浏览器

## 五、关键文件片段

### after-sales-ai/src/main.ts

```ts
const app = createApp(App)
if (import.meta.env.DEV) {
  app.config.devtools = true
}
app.use(router)
app.mount('#app')
```

### knowledgebase-frontend/src/main.ts

```ts
const app = createApp(App)
if (import.meta.env.DEV) {
  app.config.devtools = true
}
// 注册Element Plus图标
// ...
```

### vite.config 相关（无 define 覆盖）

两个项目的 `vite.config.ts` 均未使用 `define` 覆盖 `__VUE_PROD_DEVTOOLS__`，dev 模式下由 Vite 默认提供开发构建，DevTools 应可用。
