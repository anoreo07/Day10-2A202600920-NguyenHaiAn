from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from evaluation.metrics import evaluate_pipeline
from retrieval.index import LocalEmbeddingIndex
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report


def main() -> None:
    settings = load_settings()
    run_date = now_utc()
    print("[Corruption] Loading settings...")

    print("[Corruption] Loading baseline clean data...")
    baseline_df = build_clean_dataframe(
        load_raw_records(settings.paths.raw_records_json),
        run_date,
    )
    print(f"[Corruption] Baseline rows: {len(baseline_df)}")

    print("[Corruption] Corrupting data...")
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    print(f"[Corruption] Corrupted rows: {len(corrupted_df)}")
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    corrupted_for_json = corrupted_df.copy()
    if "published_dt" in corrupted_for_json.columns:
        corrupted_for_json["published_dt"] = corrupted_for_json["published_dt"].astype(str)
    write_json(settings.paths.corrupted_clean_json, corrupted_for_json.to_dict(orient="records"))

    print("[Corruption] Building corrupted index...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)

    print("[Corruption] Evaluating corrupted pipeline...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"[Corruption] Corrupted metrics: {corrupted_bundle.summary}")

    print("[Corruption] Running quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")

    print("[Corruption] Building freshness report on corrupted data...")
    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.freshness_report)

    print("[Corruption] Repairing from raw source...")
    records = fetch_source_records(settings)
    repaired_df = build_clean_dataframe(records, run_date)
    print(f"[Corruption] Repaired rows: {len(repaired_df)}")
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    repaired_for_json = repaired_df.copy()
    if "published_dt" in repaired_for_json.columns:
        repaired_for_json["published_dt"] = repaired_for_json["published_dt"].astype(str)
    write_json(settings.paths.repaired_clean_json, repaired_for_json.to_dict(orient="records"))

    print("[Corruption] Building repaired index...")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)

    print("[Corruption] Evaluating repaired pipeline...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"[Corruption] Repaired metrics: {repaired_bundle.summary}")

    print("[Corruption] Running quality checks on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")

    print("[Corruption] Building freshness report on repaired data...")
    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.freshness_report)

    print("[Corruption] Generating comparison report...")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"[Corruption] Report saved to {settings.paths.comparison_report}")
    print("[Corruption] Done.")
