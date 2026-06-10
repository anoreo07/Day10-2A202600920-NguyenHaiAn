from __future__ import annotations

from typing import Any

from core.utils import write_text


def _fmt_quality(quality: dict[str, Any]) -> str:
    lines = ["## Data Quality\n"]
    for check in quality.get("checks", []):
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- **{check['check']}**: {status} — {check['detail']}")
    return "\n".join(lines)


def _fmt_freshness(freshness: dict[str, Any]) -> str:
    lines = ["## Freshness\n"]
    lines.append(f"- Latest published: {freshness.get('latest_published', 'N/A')}")
    lines.append(f"- Oldest published: {freshness.get('oldest_published', 'N/A')}")
    lines.append(f"- Stale rows: {freshness.get('stale_rows', 0)}")
    lines.append(f"- Total rows: {freshness.get('total_rows', 0)}")
    lines.append(f"- Fresh: {'Yes' if freshness.get('is_fresh') else 'No'}")
    return "\n".join(lines)


def _fmt_metrics(metrics: dict[str, Any]) -> str:
    lines = ["## Evaluation Metrics\n"]
    for key, value in metrics.items():
        if key == "ragas" and isinstance(value, dict):
            lines.append(f"- **ragas**:")
            for rk, rv in value.items():
                if isinstance(rv, float):
                    lines.append(f"    - {rk}: {rv:.4f}")
                else:
                    lines.append(f"    - {rk}: {rv}")
        elif isinstance(value, float):
            lines.append(f"- **{key}**: {value:.4f}")
        else:
            lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def _fmt_source(source_summary: dict[str, Any]) -> str:
    lines = ["## Source Summary\n"]
    for key, value in source_summary.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    sections = [
        "# Phase 1 — Baseline Pipeline Report\n",
        _fmt_source(source_summary),
        _fmt_metrics(metrics),
        _fmt_quality(quality),
        _fmt_freshness(freshness),
    ]
    write_text(report_path, "\n\n".join(sections))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    sections = ["# Corruption Impact Report\n"]
    sections.append("## Metrics Comparison\n")
    all_keys = set(baseline_metrics.keys()) | set(corrupted_metrics.keys()) | set(repaired_metrics.keys())
    for key in sorted(all_keys):
        b = baseline_metrics.get(key, "N/A")
        c = corrupted_metrics.get(key, "N/A")
        r = repaired_metrics.get(key, "N/A")
        if isinstance(b, float):
            sections.append(f"- **{key}**: Baseline={b:.4f} | Corrupted={c:.4f} | Repaired={r:.4f}")
        elif isinstance(b, dict) and key == "ragas":
            sections.append(f"- **ragas**:")
            for rk in set(b.keys()) | set(c.keys()) if isinstance(c, dict) else set(b.keys()):
                bv = b.get(rk, "N/A") if isinstance(b, dict) else "N/A"
                cv_ = c.get(rk, "N/A") if isinstance(c, dict) else "N/A"
                rv = r.get(rk, "N/A") if isinstance(r, dict) else "N/A"
                if isinstance(bv, float):
                    sections.append(f"    - {rk}: Baseline={bv:.4f} | Corrupted={cv_:.4f} | Repaired={rv:.4f}")
                else:
                    sections.append(f"    - {rk}: Baseline={bv} | Corrupted={cv_} | Repaired={rv}")
        else:
            sections.append(f"- **{key}**: Baseline={b} | Corrupted={c} | Repaired={r}")
    sections.append("")
    sections.append("## Quality Comparison\n")
    sections.append("### Corrupted\n")
    for check in corrupted_quality.get("checks", []):
        status = "PASS" if check["passed"] else "FAIL"
        sections.append(f"- **{check['check']}**: {status} — {check['detail']}")
    sections.append("\n### Repaired\n")
    for check in repaired_quality.get("checks", []):
        status = "PASS" if check["passed"] else "FAIL"
        sections.append(f"- **{check['check']}**: {status} — {check['detail']}")
    sections.append("")
    sections.append("## Freshness Comparison\n")
    sections.append("### Corrupted\n")
    sections.append(f"- Latest: {corrupted_freshness.get('latest_published', 'N/A')}")
    sections.append(f"- Oldest: {corrupted_freshness.get('oldest_published', 'N/A')}")
    sections.append(f"- Stale: {corrupted_freshness.get('stale_rows', 0)}")
    sections.append(f"- Fresh: {'Yes' if corrupted_freshness.get('is_fresh') else 'No'}")
    sections.append("\n### Repaired\n")
    sections.append(f"- Latest: {repaired_freshness.get('latest_published', 'N/A')}")
    sections.append(f"- Oldest: {repaired_freshness.get('oldest_published', 'N/A')}")
    sections.append(f"- Stale: {repaired_freshness.get('stale_rows', 0)}")
    sections.append(f"- Fresh: {'Yes' if repaired_freshness.get('is_fresh') else 'No'}")
    write_text(report_path, "\n".join(sections))
