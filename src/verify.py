from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / "data" / "source_catalog.json").read_text(encoding="utf-8"))
generated = json.loads((ROOT / "dist" / "data" / "evidence.json").read_text(encoding="utf-8"))
problems = json.loads((ROOT / "dist" / "data" / "problems.json").read_text(encoding="utf-8"))

assert len(catalog) == len({item["id"] for item in catalog}), "source ids must be unique"
assert len(catalog) == len({item["url"] for item in catalog}), "source URLs must be unique"
assert all(item["claim"] and item["publisher"] and item["url"].startswith("http") for item in catalog)
assert all(item["strength"] in (1, 2, 3) for item in catalog)
assert all(item["content_sha256"] for item in generated if item["fetch_status"] in ("verified", "shell_only"))
assert all(item["excerpt"] is None or len(item["excerpt"]) <= 60 for item in generated)
assert all(0 <= item["index"] <= 100 for item in problems)

with sqlite3.connect(ROOT / "data" / "market_radar.sqlite3") as conn:
    source_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    tag_count = conn.execute("SELECT COUNT(*) FROM source_tags").fetchone()[0]
    latest_stats = conn.execute(
        "SELECT COUNT(*) FROM problem_stats WHERE run_id=(SELECT run_id FROM pipeline_runs ORDER BY ran_at DESC LIMIT 1)"
    ).fetchone()[0]

assert source_count == len(catalog)
assert tag_count == sum(len(item["tags"]) for item in catalog)
assert latest_stats == len(problems)

print(json.dumps({
    "status": "ok",
    "sources": source_count,
    "source_tags": tag_count,
    "problems": latest_stats,
    "verified": sum(item["fetch_status"] == "verified" for item in generated),
    "shell_only": sum(item["fetch_status"] == "shell_only" for item in generated),
    "blocked_or_failed": sum(item["fetch_status"] == "blocked_or_failed" for item in generated),
}, ensure_ascii=False))

