from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import write_json


CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _parse_date(date_parts: list[int] | None) -> str:
    if not date_parts:
        return ""
    parts = [str(p) for p in date_parts]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1].zfill(2)}"
    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"


def _parse_authors(authors: list[dict[str, Any]]) -> list[str]:
    result = []
    for author in authors:
        given = author.get("given", "")
        family = author.get("family", "")
        name = f"{given} {family}".strip()
        if name:
            result.append(name)
    return result


def _get_date(item: dict[str, Any], field: str) -> str:
    date_info = item.get(field) or item.get("published-print") or item.get("published-online") or item.get("issued")
    if date_info:
        return _parse_date(date_info.get("date-parts", [None])[0])
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        doi = item.get("DOI", "")
        if not doi:
            continue
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        if not title:
            continue
        abstract = item.get("abstract", "") or ""
        authors = _parse_authors(item.get("author", []))
        subjects = item.get("subject", [])
        primary = subjects[0] if subjects else ""
        published = _get_date(item, "published-print")
        if not published:
            published = _get_date(item, "published-online")
        if not published:
            published = _get_date(item, "issued")
        updated = _get_date(item, "updated")
        abs_url = f"https://doi.org/{doi}"
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
        records.append(PaperRecord(
            paper_id=doi,
            title=title,
            summary=abstract,
            authors=authors,
            categories=subjects,
            primary_category=primary,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment="",
        ))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": "Day10Lab/1.0 (mailto:student@example.com)"}
    max_retries = 3
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
            write_json(settings.paths.raw_api_response, payload)
            records = parse_crossref_payload(payload)
            write_json(settings.paths.raw_records_json, [r.__dict__ for r in records])
            return records
        except requests.RequestException as e:
            last_error = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch from Crossref after {max_retries} retries: {last_error}")


def load_raw_records(path: Path) -> list[PaperRecord]:
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    return [PaperRecord(**item) for item in data]
