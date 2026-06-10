from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "report_name": report_name,
        "row_count": len(df),
        "checks": [],
    }
    if df.empty:
        checks["checks"].append({"check": "row_count > 0", "passed": False, "detail": "DataFrame is empty"})
        return checks

    checks["checks"].append({
        "check": "row_count > 0",
        "passed": True,
        "detail": f"Total rows: {len(df)}",
    })
    null_paper_ids = df["paper_id"].isna().sum()
    checks["checks"].append({
        "check": "paper_id not null",
        "passed": null_paper_ids == 0,
        "detail": f"Null paper_ids: {null_paper_ids}",
    })
    dup_paper_ids = df["paper_id"].duplicated().sum()
    checks["checks"].append({
        "check": "paper_id unique",
        "passed": dup_paper_ids == 0,
        "detail": f"Duplicate paper_ids: {dup_paper_ids}",
    })
    null_titles = df["title"].isna().sum()
    empty_titles = (df["title"].str.strip() == "").sum() if "title" in df else 0
    checks["checks"].append({
        "check": "title not null/empty",
        "passed": null_titles == 0 and empty_titles == 0,
        "detail": f"Null titles: {null_titles}, Empty titles: {empty_titles}",
    })
    short_summaries = (df["summary"].str.len() < 20).sum() if "summary" in df else 0
    checks["checks"].append({
        "check": "summary length >= 20 chars",
        "passed": short_summaries == 0,
        "detail": f"Summaries < 20 chars: {short_summaries}",
    })
    if "age_days" in df.columns:
        stale = (df["age_days"] > settings.freshness_threshold_days).sum()
        checks["checks"].append({
            "check": f"freshness (age_days <= {settings.freshness_threshold_days})",
            "passed": stale == 0,
            "detail": f"Stale rows (> {settings.freshness_threshold_days} days): {stale}",
        })
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(out_path, checks)
    return checks


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty or "published_dt" not in df.columns:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": len(df),
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload
    valid_dates = df["published_dt"].dropna()
    if valid_dates.empty:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": len(df),
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload
    latest = valid_dates.max().isoformat()
    oldest = valid_dates.min().isoformat()
    stale = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
    payload = {
        "latest_published": latest,
        "oldest_published": oldest,
        "stale_rows": stale,
        "total_rows": len(df),
        "is_fresh": stale == 0,
    }
    write_json(report_path, payload)
    return payload
