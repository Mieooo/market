from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "source_catalog.json"
PROBLEMS = ROOT / "data" / "problems.json"
DB = ROOT / "data" / "market_radar.sqlite3"
GENERATED = ROOT / "dist" / "data"
KEYWORDS = ("评测", "记忆", "工具", "权限", "RAG", "长期", "成本", "可靠", "生产", "轨迹")


def compact_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    positions = [text.find(k) for k in KEYWORDS if text.find(k) >= 0]
    start = max(0, min(positions) - 70) if positions else 0
    # Keep only a short verification fragment; the project links to originals
    # rather than republishing source text.
    excerpt = text[start : start + 60]
    return title[:240], excerpt


def fetch_source(client: httpx.Client, source: dict) -> dict:
    result = {
        "http_status": None,
        "fetch_status": "not_fetched",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_sha256": None,
        "page_title": None,
        "excerpt": None,
    }
    try:
        response = client.get(source["url"])
        result["http_status"] = response.status_code
        response.raise_for_status()
        body = response.content
        result["content_sha256"] = hashlib.sha256(body).hexdigest()
        result["page_title"], result["excerpt"] = compact_text(response.text)
        shell_markers = ("请稍候", "正在加载", "just a moment")
        shell_text = f'{result["page_title"]} {result["excerpt"]}'.lower()
        result["fetch_status"] = "shell_only" if any(marker in shell_text for marker in shell_markers) else "verified"
    except Exception as exc:
        result["fetch_status"] = "blocked_or_failed"
        result["fetch_error"] = type(exc).__name__
    return result


def evidence_index(rows: list[dict], tag: str) -> dict:
    tagged = [row for row in rows if tag in row["tags"]]
    publishers = {row["publisher"] for row in tagged}
    types = {row["type"] for row in tagged}
    direct = [row for row in tagged if row["strength"] == 3]
    recruitment = [row for row in tagged if row["type"] == "招聘"]
    verified = [row for row in tagged if row.get("fetch_status") == "verified"]
    # Denominators are intentionally above the first-version sample size so a
    # topic cannot reach 100 merely because this small corpus mentions it often.
    components = {
        "publisher_coverage": round(min(len(publishers) / 12, 1) * 30, 1),
        "direct_evidence": round(min(len(direct) / 12, 1) * 30, 1),
        "signal_diversity": round(min(len(types) / 6, 1) * 20, 1),
        "recruitment_signal": round(min(len(recruitment) / 8, 1) * 20, 1),
    }
    return {
        "evidence_count": len(tagged),
        "publisher_count": len(publishers),
        "source_type_count": len(types),
        "direct_evidence_count": len(direct),
        "recruitment_count": len(recruitment),
        "verified_url_count": len(verified),
        "index": round(sum(components.values())),
        "components": components,
    }


def write_database(rows: list[dict], problems: list[dict], run_id: str) -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS pipeline_runs(
          run_id TEXT PRIMARY KEY, ran_at TEXT NOT NULL, source_count INTEGER NOT NULL,
          verified_count INTEGER NOT NULL, failed_count INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources(
          id TEXT PRIMARY KEY, type TEXT NOT NULL, region TEXT NOT NULL, source_date TEXT,
          publisher TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL, claim TEXT NOT NULL,
          strength INTEGER NOT NULL, fetch_status TEXT NOT NULL, http_status INTEGER,
          fetched_at TEXT, content_sha256 TEXT, page_title TEXT, excerpt TEXT, fetch_error TEXT
        );
        CREATE TABLE IF NOT EXISTS source_tags(
          source_id TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY(source_id, tag),
          FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        CREATE TABLE IF NOT EXISTS problem_stats(
          run_id TEXT NOT NULL, problem_key TEXT NOT NULL, evidence_index INTEGER NOT NULL,
          evidence_count INTEGER NOT NULL, publisher_count INTEGER NOT NULL,
          source_type_count INTEGER NOT NULL, direct_evidence_count INTEGER NOT NULL,
          recruitment_count INTEGER NOT NULL, verified_url_count INTEGER NOT NULL,
          components_json TEXT NOT NULL, PRIMARY KEY(run_id, problem_key)
        );
        """)
        conn.execute("DELETE FROM sources")
        conn.execute("DELETE FROM source_tags")
        for row in rows:
            conn.execute("""INSERT INTO sources VALUES(
              :id,:type,:region,:date,:publisher,:title,:url,:claim,:strength,
              :fetch_status,:http_status,:fetched_at,:content_sha256,:page_title,:excerpt,:fetch_error
            )""", {**row, "fetch_error": row.get("fetch_error")})
            conn.executemany("INSERT INTO source_tags(source_id,tag) VALUES(?,?)", [(row["id"], tag) for tag in row["tags"]])
        verified = sum(row["fetch_status"] == "verified" for row in rows)
        conn.execute("INSERT INTO pipeline_runs VALUES(?,?,?,?,?)", (run_id, datetime.now(timezone.utc).isoformat(), len(rows), verified, len(rows) - verified))
        for problem in problems:
            stat = evidence_index(rows, problem["key"])
            conn.execute("INSERT INTO problem_stats VALUES(?,?,?,?,?,?,?,?,?,?)", (
                run_id, problem["key"], stat["index"], stat["evidence_count"], stat["publisher_count"],
                stat["source_type_count"], stat["direct_evidence_count"], stat["recruitment_count"],
                stat["verified_url_count"], json.dumps(stat["components"], ensure_ascii=False)
            ))
        conn.commit()


def main(fetch: bool) -> None:
    rows = json.loads(CATALOG.read_text(encoding="utf-8"))
    problems = json.loads(PROBLEMS.read_text(encoding="utf-8"))
    if fetch:
        headers = {"User-Agent": "Mozilla/5.0 MarketProblemRadar/1.0 (research verification)"}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=18) as client:
            for source in rows:
                source.update(fetch_source(client, source))
    else:
        previous_path = GENERATED / "evidence.json"
        previous = {item["id"]: item for item in json.loads(previous_path.read_text(encoding="utf-8"))} if previous_path.exists() else {}
        for source in rows:
            old = previous.get(source["id"], {})
            old_title = old.get("page_title") or ""
            old_excerpt = old.get("excerpt") or ""
            old_status = old.get("fetch_status", "catalog_only")
            if any(marker in f"{old_title} {old_excerpt}".lower() for marker in ("请稍候", "正在加载", "just a moment")):
                old_status = "shell_only"
            source.update({
                "fetch_status": old_status,
                "http_status": old.get("http_status"),
                "fetched_at": old.get("fetched_at"),
                "content_sha256": old.get("content_sha256"),
                "page_title": old.get("page_title"),
                "excerpt": old_excerpt[:60] or None,
                "fetch_error": old.get("fetch_error"),
            })
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    stats = []
    for problem in problems:
        stat = evidence_index(rows, problem["key"])
        stats.append({**problem, **stat})
    stats.sort(key=lambda item: item["index"], reverse=True)
    write_database(rows, problems, run_id)
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "evidence.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (GENERATED / "problems.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    (GENERATED / "problem_definitions.json").write_text(
        json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    type_counts = Counter(row["type"] for row in rows)
    status_counts = Counter(row["fetch_status"] for row in rows)
    overview = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "定向证据抽样；指数衡量证据覆盖，不代表市场份额",
        "source_count": len(rows),
        "publisher_count": len({row["publisher"] for row in rows}),
        "verified_url_count": sum(row["fetch_status"] == "verified" for row in rows),
        "failed_url_count": sum(row["fetch_status"] == "blocked_or_failed" for row in rows),
        "shell_only_count": sum(row["fetch_status"] == "shell_only" for row in rows),
        "verification_status_counts": dict(status_counts),
        "source_type_counts": dict(type_counts),
    }
    (GENERATED / "overview.json").write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(overview, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch and verify public source pages")
    main(parser.parse_args().fetch)
