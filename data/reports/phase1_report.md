# Phase 1 — Baseline Pipeline Report


## Source Summary

- **source**: Crossref REST API
- **query**: agentic retrieval augmented generation large language model
- **filter**: from-pub-date:2025-12-12,has-abstract:true
- **max_results**: 24
- **records_fetched**: 24
- **records_after_clean**: 24

## Evaluation Metrics

- **samples**: 71
- **retrieval_hit_rate**: 1.0000
- **mean_token_f1**: 0.7621
- **judge_accuracy**: 0.6761
- **mean_judge_score**: 3.7042
- **ragas**:
    - skipped: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## Data Quality

- **row_count > 0**: PASS — Total rows: 24
- **paper_id not null**: PASS — Null paper_ids: 0
- **paper_id unique**: PASS — Duplicate paper_ids: 0
- **title not null/empty**: PASS — Null titles: 0, Empty titles: 0
- **summary length >= 20 chars**: FAIL — Summaries < 20 chars: 1
- **freshness (age_days <= 180)**: PASS — Stale rows (> 180 days): 0

## Freshness

- Latest published: 2026-06-02T00:00:00+00:00
- Oldest published: 2025-12-19T00:00:00+00:00
- Stale rows: 0
- Total rows: 24
- Fresh: Yes