from __future__ import annotations

import sys

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json, read_json
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from retrieval.index import LocalEmbeddingIndex
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report


def main() -> None:
    settings = load_settings()
    run_date = now_utc()
    print("[Phase 1] Loading settings...")

    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        print("[Phase 1] Loading existing raw records...")
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        print("[Phase 1] Fetching records from Crossref API...")
        records = fetch_source_records(settings)
    print(f"[Phase 1] Got {len(records)} raw records.")

    print("[Phase 1] Cleaning data...")
    df = build_clean_dataframe(records, run_date)
    print(f"[Phase 1] Cleaned dataset: {len(df)} rows.")
    write_csv(df, settings.paths.clean_csv)
    df_for_json = df.copy()
    if "published_dt" in df_for_json.columns:
        df_for_json["published_dt"] = df_for_json["published_dt"].astype(str)
    write_json(settings.paths.clean_json, df_for_json.to_dict(orient="records"))

    print("[Phase 1] Building embedding index...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    print(f"[Phase 1] Index built with collection '{index.collection_name}'.")

    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        print("[Phase 1] Loading existing test set...")
    else:
        print("[Phase 1] Building test set...")
        build_test_set(df, settings.paths.eval_testset)
    print(f"[Phase 1] Test set ready at {settings.paths.eval_testset}.")

    print("[Phase 1] Evaluating pipeline...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f"[Phase 1] Metrics: {bundle.summary}")

    print("[Phase 1] Running quality checks...")
    quality = run_data_quality_checks(df, settings, "baseline")

    print("[Phase 1] Building freshness report...")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    print("[Phase 1] Generating report...")
    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "max_results": settings.max_results,
        "records_fetched": len(records),
        "records_after_clean": len(df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"[Phase 1] Report saved to {settings.paths.baseline_report}")
    print("[Phase 1] Done.")
