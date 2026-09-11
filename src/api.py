from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "market_radar.sqlite3"
DIST = ROOT / "dist"

app = FastAPI(title="大模型应用市场难题雷达 API", version="1.0.0")


def rows(query: str, params: tuple = ()) -> list[dict]:
    if not DB.exists():
        raise HTTPException(503, "数据库尚未生成，请先运行数据管线")
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params).fetchall()]


@app.get("/api/overview")
def overview():
    runs = rows("SELECT * FROM pipeline_runs ORDER BY ran_at DESC LIMIT 1")
    if not runs:
        raise HTTPException(404, "暂无数据")
    run = runs[0]
    run["source_types"] = rows("SELECT type, COUNT(*) AS count FROM sources GROUP BY type ORDER BY count DESC")
    run["verification_statuses"] = rows("SELECT fetch_status AS status, COUNT(*) AS count FROM sources GROUP BY fetch_status ORDER BY count DESC")
    status_counts = {item["status"]: item["count"] for item in run["verification_statuses"]}
    run["verified_count"] = status_counts.get("verified", 0)
    run["shell_only_count"] = status_counts.get("shell_only", 0)
    run["failed_count"] = status_counts.get("blocked_or_failed", 0)
    return run


@app.get("/api/problems")
def problems():
    stats = rows("""SELECT ps.* FROM problem_stats ps JOIN pipeline_runs pr ON pr.run_id=ps.run_id
                    WHERE pr.ran_at=(SELECT MAX(ran_at) FROM pipeline_runs) ORDER BY evidence_index DESC""")
    for stat in stats:
        stat["components"] = json.loads(stat.pop("components_json"))
    return stats


@app.get("/api/problem-definitions")
def problem_definitions():
    path = ROOT / "data" / "problems.json"
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/evidence")
def evidence(tag: str | None = None, source_type: str | None = Query(None, alias="type"), region: str | None = None):
    clauses, params = [], []
    if tag:
        clauses.append("EXISTS(SELECT 1 FROM source_tags st WHERE st.source_id=s.id AND st.tag=?)")
        params.append(tag)
    if source_type:
        clauses.append("s.type=?")
        params.append(source_type)
    if region:
        clauses.append("s.region=?")
        params.append(region)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    result = rows("SELECT s.* FROM sources s" + where + " ORDER BY strength DESC, source_date DESC", tuple(params))
    for item in result:
        item["tags"] = [r["tag"] for r in rows("SELECT tag FROM source_tags WHERE source_id=? ORDER BY tag", (item["id"],))]
    return {"count": len(result), "items": result}


@app.get("/api/evidence/{source_id}")
def evidence_detail(source_id: str):
    result = rows("SELECT * FROM sources WHERE id=?", (source_id,))
    if not result:
        raise HTTPException(404, "来源不存在")
    item = result[0]
    item["tags"] = [r["tag"] for r in rows("SELECT tag FROM source_tags WHERE source_id=?", (source_id,))]
    return item


@app.get("/")
def index():
    return FileResponse(DIST / "index.html")


app.mount("/data", StaticFiles(directory=DIST / "data"), name="data")
app.mount("/assets", StaticFiles(directory=DIST / "assets", check_dir=False), name="assets")
