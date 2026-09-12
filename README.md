# 大模型求职与研究雷达

这是一个证据优先的求职与研究情报产品，用于发现大模型行业正在升温的工程难题，并把证据转化为程序员可执行的学习、研究和作品集建议。

当前阶段是前端优先 MVP：页面使用结构完整的模拟数据验证产品表达和操作逻辑，并显著标记“演示数据”。下一阶段将通过统一 Repository 接口接入真实 API，无需重写页面。

## 前端 MVP

```powershell
cd web
npm install
npm run dev
```

开发地址为 `http://127.0.0.1:5173/`。生产构建输出到项目根目录 `dist`：

```powershell
cd web
npm test
npm run test:e2e
npm run build
```

核心页面包括总览、动态难题、难题详情、求职快讯、证据库和数据方法。可使用 `?scenario=loading|empty|partial|stale|error` 验证异常与降级状态。

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

## 原有数据服务

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
