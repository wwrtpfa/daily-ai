# AGENTS.md — SIGNAL / daily-ai

> 给 AI 编码助手的项目规约。任何改动前先读 `docs/01-项目规约.md`（优先级更高）与 `docs/00-项目蓝图.md`。

## 新项目起点与执行顺序（2026-11-10）

- 当前已有文档与 v0.6 多页静态交互原型，没有生产工程、CI 或仓库内可复跑的 39 项测试；不能宣称已具备这些能力。
- 用户对 v0.3 产品功能和整体设计仍不满意。该原型是待评审候选，“功能都满意、只改呈现”不再是有效前提；不得自行宣布视觉定稿；用户已授权自主完成原型及必要功能取舍，见产品基线 v0.4 功能决策与 v0.6 玻璃磨砂。
- 开发前继续读 `docs/02-产品与原型基线.md`、`docs/03-开发规范.md`、`docs/04-技能与执行流程.md`。产品与视觉待确认项不靠回归通过自动变成已确认。
- 先定位并实际打开项目内原型，再做视觉与流程判断。可用本机 HTTP 预览；工具安全限制须遵守。不能仅看 HTML 源码就声称看过页面，也不让用户代找已有文件。
- 产品任务与范围 → 页面/交互/状态 → 候选原型 → 用户确认 → token 与契约 → 对应生产实现。现行硬约束在显式修订前仍有效。
- 技能按阶段选用，详见 `04`：产品与原型评审使用 Product Design；实现以已确认设计为依据；浏览器回归使用对应测试技能。不把不相关技能或其默认框架塞进项目。
- 本任务启动的浏览器、预览服务、REPL、watcher 和 helper 在结束前关闭并核查退出，保留用户原有进程。`agent-browser` 必须在任务会话内操作并执行 `agent-browser close`；Browser/CUA 执行文档中的标签收尾步骤。

## 当前原型执行入口

- 原型：`python3 scripts/build-prototype.py`；检查：`node --check prototype/app.js` 与 `python3 scripts/check-prototype.py`。
- v0.4 决策见 `docs/02-产品与原型基线.md` 开头：合并阅读模式，四信号改选条分享，日周项目与搜索闭环。生产约束继续有效，原型无需等待逐项确认才能实现。

## 当前实施状态（2026-11-10）

已按用户确认的 v0.6 玻璃磨砂方向继续，显式覆盖下方历史 v0.3 的无阴影/无渐变/无圆角视觉限制。真实数据在 content/，旧 demo-data.json 不用于发布。当前可执行链路为 Python 静态生成与校验；Astro/Zod/pnpm/Actions 尚未建立，不能宣称已通过其检查。每日数据任务先读 docs/05-每日数据生成与定时任务.md，使用其中当前命令；不在日常任务中改 UI。玻璃材质仍须来自 design-tokens。

## 项目是什么

每日 7:00 前上线的 AI / GitHub 日报静态站。**纯前端、GitHub 托管源码、Vercel 托管静态产物**。后端逻辑全部压进 GitHub Actions 每日构建期：`采集 → LLM 编纂 → 校验 → 生成图文与索引 → commit → Vercel 部署`。运行时只有 CDN 上的 HTML。

## 不可违反的约束

1. **不引入运行时后端**：禁止 Vercel Functions / SSR / ISR / 数据库 / 外部搜索服务 / 账号体系。**v0.2：不持久化任何用户数据** —— 信号标记、展开态、卡片内容一律页面内存，刷新即空；`localStorage` 唯一允许的键是 `signal:theme`。禁止导出/导入 JSON、兴趣指纹、集章、跨天重排（属 P3 可选，默认关闭）。唯一可能破例的是 P3 云同步，需先改蓝图并获确认。
1b. **不建 `/me` 路由**，不出现「我的 / 档案 / 连续天数」等暗示账户的文案；全站不得有向本站发起的写请求。
2. **首屏零 JS**：交互用 Astro Islands，默认 `client:visible` / `client:idle`；不引图表库、动画库、第三方脚本、追踪像素。
3. **Git 即 CMS**：内容写在 `content/days/<YYYY-MM-DD>.json`（+.md 镜像），由 Actions 生成，人工不手改；**已发布内容不可改写**，勘误只 append `amendments[]`。
4. **设计 token 单一来源**：`config/design-tokens.json`。禁止在组件或图文模板里硬编码颜色值。
5. **Schema 单一来源**：`src/content.config.ts` 的 Zod 定义。改数据结构必须同步改 schema、采集器、`scripts/validate.ts`、模板与文档。
6. **历史去重**：新条目必须与 `content/history.json` 比对，避免与既往推送重复。
7. **性能预算**：Lighthouse ≥ 95、CLS < 0.05、LCP < 1.2s、首屏 HTML < 30KB、首屏 JS < 15KB、单图 < 150KB。中文字体必须子集化。
8. **无障碍**：`aria-pressed`、键盘可达、对比度 AA、图片 alt、纯文字等价版本；动效必须包在 `@media (prefers-reduced-motion: no-preference)` 内。

## 内容硬要求（写进校验，不是风格建议）

- 结构：**先给结果 → 它是什么/能解决什么 → 效果 → 原理**。开头短、有当下感、不铺垫。
- **字段分层（v0.3 覆盖 v0.2 的「结论前置」）**：每条必有 `verdict / why / facts[3–4] / scenes[2–4]`；**只有 `verdict / why` 默认可见且不带字段标签**，其余字段必须在静态 HTML 的 DOM 里常驻、一键可展开。生产实现用原生 `<details>`，保证无 JS 可达。**不要把全部字段平铺在首屏** —— 信息不删，但要分层。
- **项目档案（v0.2）**：`oneline / problem / scenes / notFor / whyToday` 五个介绍字段必填，禁止只给项目名 + star 增量；`day` 与 `week` 两套数据都要有。数字永远排在介绍之后。
- 每条必有 ≥1 个**可达的**来源链接，以及 `caveat`（边界与存疑：厂商自选案例 / 未复跑数据 / 规划目标必须显式标注）。
- **高亮与配图分场景**：UI 阅读界面里，大标题以低饱和蓝灰突出关键词、正文用极淡双色底，信息图只在内页出现（**首屏不放图表**）；**OG / 分享卡 / 长图与文章正文仍按长期偏好保留 2–4 个多色高亮、配图给够**。不要用吉祥物插画凑数，也不要在同屏堆四色高亮破坏单一焦点。
- `why` 写结构性变化，不写「很厉害」；`brief[]` 必须与 `items[]` 一一对应。
- **当前 UI 依据为 `01-项目规约.md` 开头的 v0.6 玻璃磨砂说明**：用户明确要求玻璃磨砂与高级优雅感，允许受控渐变、柔和投影、9–27px 圆角和 backdrop-filter；覆盖旧视觉禁令。材质由 design-tokens.json 定义，无模糊支持时实色回退。架构与数据约束不变，不得自行宣布用户已定稿。
- 禁止：绝对化用语、无来源数字、全文转载、把传闻当发布。

## 定时任务（改 cron 前先读蓝图 §4）

- 用**非整点**分钟（`:17` / `:43`），避开整点高负载导致延迟或丢跑。
- cron 按 **UTC** 写，目标日用 `Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai'})` 计算。
- workflow 必须在默认分支 `main`；最小权限 `contents: write`；`timeout-minutes: 20`；concurrency group 不取消进行中任务。
- 必须有：幂等（无变化不 commit）、降级（失败标 `degraded` 并保留上一期，**禁止发空刊**）、死人开关 ping、三重触发（cron / repository_dispatch / workflow_dispatch）。
- 每日 LLM token 预算硬上限；小模型做抽取、旗舰模型做主编。

## 代码习惯

- pnpm + 提交 lockfile；TypeScript `strict`；ESLint/Prettier 通过后才提交。
- Conventional Commits；机器提交固定 `chore(daily): <date> [skip ci]`。
- 组件 PascalCase、文件 kebab-case；栏目枚举以 `config/taxonomy.yaml` 为准。
- 不新增运行时依赖，除非 PR 说明体积与理由；`prototype/` 不参与生产构建。
- 改动后跑：`pnpm typecheck && pnpm lint && pnpm daily:validate && pnpm build`。

## 不要做的事

不要加公开点赞计数、排行榜、评论、无限滚动、骨架屏、订阅弹窗、自动播放、粒子背景；不要把「纯前端」悄悄改成全栈；不要静默上传用户兴趣数据；**不要因为「别的产品都有」就补回一个「我的」页面** —— 无账号、无持久化、读完即走是本项目的主张，不是缺失。
