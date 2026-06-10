from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.utils import normalize_whitespace, compact_join
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    rows = []
    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        authors = r.authors
        categories = r.categories
        published = r.published.strip()
        if not title:
            continue
        rows.append({
            "paper_id": r.paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": r.primary_category,
            "published": published,
            "updated": r.updated.strip(),
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["authors_joined"] = df["authors"].apply(lambda x: compact_join(x, "; "))
    df["categories_joined"] = df["categories"].apply(lambda x: compact_join(x, "; "))
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = df.apply(
        lambda row: (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        ),
        axis=1,
    )
    def parse_date(val: str) -> datetime | pd.NaT:
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                dt = datetime.strptime(val, fmt)
                return dt.replace(tzinfo=UTC)
            except ValueError:
                continue
        return pd.NaT
    df["published_dt"] = df["published"].apply(parse_date)
    df["age_days"] = (run_date - df["published_dt"]).dt.days.where(df["published_dt"].notna(), -1)
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values("published_dt", ascending=False).reset_index(drop=True)
    return df
