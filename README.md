# SIGNAL · 每日 AI / 每日 GitHub

当前交付为用户确认方向的 **v0.6 玻璃磨砂静态原型**，已接入 2026-11-10 首期真实数据：4 条官方动态、3 个 GitHub 项目档案与 API 快照。自动采集调度、Astro 生产工程和部署尚未接入。

## 每日数据与 Agent 执行入口

后续 Agent 按 [每日数据生成与定时任务](docs/05-每日数据生成与定时任务.md) 执行；时间、预算配置在 `config/daily-task.json`，目前 `installed: false`，表示只完成规范，没有安装定时任务。

正式数据来自 `content/days/`、`content/projects/`，原文核验在 `content/sources/`，GitHub 快照在 `content/snapshots/`，去重历史在 `content/history.json`。首期为人工补刊，实际采集截止见数据 window；不是 07:00 自动出刊记录。旧 `prototype/demo-data.json` 仅作设计历史，不进入页面与归档。日周星标增量缺少对照快照时为 null，网页显示暂缺。

## 生成与预览

```sh
python3 scripts/validate-content.py
python3 scripts/build-prototype.py
python3 scripts/check-prototype.py
node --check prototype/app.js
python3 -m http.server 4173 --bind 127.0.0.1 --directory prototype
```

浏览器访问本机 4173 端口；完成后 Ctrl+C 关闭。入口为 `prototype/index.html`，不手改生成的 HTML。新增刊期先按规范写 JSON，通过审核后运行 `python3 scripts/validate-content.py --write-history` 更新去重历史，再生成页面。

## 已实现

- 今日与按日期独立刊期：结论与原因默认显示，原生 details 展开事实、场景、边界和真实来源。
- 项目介绍、用途、限制、日周切换、主题筛选与真实仓库链接；累计数字附采集时间。
- 一周观察仅归并近七天真实记录，覆盖不足不推断趋势；往期支持全文检索。
- 选条分享、图片预览/下载、文字复制与失败备用框；主题以外的用户选择只在内存。
- 同源 Markdown、RSS 和日历提醒；未配置 `config/site.json.publicBaseUrl` 时 RSS 指向仓库 Markdown，不冒充已上线站点。
- 银白磨砂材质、悬浮顶栏、原创玻璃叠层 SVG、手机布局、深色主题。设计 token 唯一来源为 `config/design-tokens.json`。

## 实施边界

页面由 Python 标准库生成，JS 只做阅读增强；无运行时后端、账号、追踪或用户数据上传。当前 Python 数据校验是原型过渡契约，未来迁移至 `src/content.config.ts` 的 Zod 唯一 schema。仓库尚无 pnpm/CI 工程，不能将本地链接与体积检查称为完整生产验收或 Lighthouse 测试。

产品、架构与开发规范见 docs/00–04；每日执行以 docs/05 为入口。尚未配置线上域名或部署，实际提交/推送状态以 Git 为准。
