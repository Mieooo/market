# 大模型应用市场难题雷达

这是一个证据优先的数据与应用项目，用于识别大模型应用市场真正希望解决的问题，并把问题转化为应届生可验证的作品集项目。前端不保存手填统计，所有数字来自 SQLite 与可重跑的数据管线。

## 数据口径

- 观察窗口：2024–2026 年，数据截至 2026-09-12。
- 第一版采用定向抽样，包含招聘、生产实践、公开评测、行业调查和一线公开分享。
- 证据覆盖指数用于比较当前语料对问题的支持强弱，不表示市场份额或岗位占比。
- 来源登记位于 `data/source_catalog.json`。
- 管线保存 HTTP 状态、抓取时间、内容 SHA-256 和短验证片段。
- SQLite 数据库位于 `data/market_radar.sqlite3`。

## API

- `GET /api/overview`
- `GET /api/problems`
- `GET /api/problem-definitions`
- `GET /api/evidence`
- `GET /api/evidence?tag=长期记忆`
- `GET /api/evidence/{source_id}`

## 运行

项目已经包含独立虚拟环境。执行：

```powershell
.\run.ps1
```

页面地址为 `http://127.0.0.1:4174/`，API 文档为 `http://127.0.0.1:4174/docs`。

只重新生成统计而不联网抓取：

```powershell
.\.venv\Scripts\python.exe src\pipeline.py
.\.venv\Scripts\python.exe src\verify.py
```
