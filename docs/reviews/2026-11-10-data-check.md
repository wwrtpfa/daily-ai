# 2026-11-10 真实数据接入检查

用户确认按 v0.6 磨砂玻璃方向继续，本轮保留视觉。首期为人工补刊，正式刊号从 001 开始：4 条官方动态，3 个项目档案。新闻窗口与采集截止保存在 content/days/2026-11-10.json；不代表早间准点自动出刊。

## 数据与来源

- Anthropic Fable / Mythos 5.2：联网工具已读取官方全文；原文保留实际发布日期，未伪造精确时分。
- Adobe / Disney：读取官方公告全文，合作计划与商用安全表述明确标注为厂商声明。
- Claude Code v2.1.321、llama.cpp b12244：GitHub API 的正式 release 与发布时间，保留未复跑说明。
- Claude Code、llama.cpp、Microsoft Agent Framework：GitHub 仓库 API 快照和 README / LICENSE 核对；Claude Code 不再标 MIT。
- 无历史快照，日周增量为 null；不再展示模拟走势。旧演示刊期仍留在 demo-data.json，退出正式页面、归档、RSS 和周观察。
- `validate-content.py --check-links` 四个 URL 均返回 200；之后单独重复完整 HTTP 抓取时连接中断，未记录为全文抓取成功。完整事实核验依据上面列出的渠道，记录在 content/sources/。

## 已运行检查

- 内容校验：4 条，字段数量、brief 对齐、时间窗口、白名单来源、去重、项目快照通过。
- 隔离负例测试：正常数据、缺 facts、越界时间、brief 错序、重复来源事件、无基线增量，共 6 项符合预期。
- 静态页面：6 页、156 个站内链接/锚点、Markdown、RSS、日历、所有页面 HTML <30KB、JS <15KB，通过。
- `node --check prototype/app.js` 通过。生成器两次相同输入的资源哈希保持一致。
- 浏览器 1440×1000 首页及 390×844 手机截图已实际查看，无横向溢出；证据展开包含新闻原文链接。
- 项目页 `?period=week` 正确选中周视图且显示暂缺，inference 筛选只显示 llama.cpp。
- 往期搜索 OAuth，命中 1 期 1 条；周观察注明仅 1 期真实数据，不推断趋势。
- 分享弹层选择 4 条，1080px 画布正常，复制反馈“已复制 4 条摘要”。

截图在 `2026-11-10-data-assets/`。本轮未重新宣称生产 Lighthouse、完整无障碍或真实部署验收。没有安装定时任务；执行规范在 docs/05，参数在 config/daily-task.json。
