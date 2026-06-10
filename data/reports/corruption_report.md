# Corruption Impact Report

## Metrics Comparison

- **judge_accuracy**: Baseline=0.6761 | Corrupted=0.3239 | Repaired=0.6761
- **mean_judge_score**: Baseline=3.7042 | Corrupted=2.2958 | Repaired=3.7042
- **mean_token_f1**: Baseline=0.7621 | Corrupted=0.3536 | Repaired=0.7621
- **ragas**:
    - skipped: Baseline=Set RUN_RAGAS=1 to enable the slower Ragas pass. | Corrupted=Set RUN_RAGAS=1 to enable the slower Ragas pass. | Repaired=Set RUN_RAGAS=1 to enable the slower Ragas pass.
- **retrieval_hit_rate**: Baseline=1.0000 | Corrupted=0.6197 | Repaired=1.0000
- **samples**: Baseline=71 | Corrupted=71 | Repaired=71

## Quality Comparison

### Corrupted

- **row_count > 0**: PASS — Total rows: 24
- **paper_id not null**: PASS — Null paper_ids: 0
- **paper_id unique**: FAIL — Duplicate paper_ids: 6
- **title not null/empty**: PASS — Null titles: 0, Empty titles: 0
- **summary length >= 20 chars**: FAIL — Summaries < 20 chars: 8
- **freshness (age_days <= 180)**: PASS — Stale rows (> 180 days): 0

### Repaired

- **row_count > 0**: PASS — Total rows: 24
- **paper_id not null**: PASS — Null paper_ids: 0
- **paper_id unique**: PASS — Duplicate paper_ids: 0
- **title not null/empty**: PASS — Null titles: 0, Empty titles: 0
- **summary length >= 20 chars**: FAIL — Summaries < 20 chars: 1
- **freshness (age_days <= 180)**: PASS — Stale rows (> 180 days): 0

## Freshness Comparison

### Corrupted

- Latest: 2026-04-06T00:00:00+00:00
- Oldest: 2025-12-19T00:00:00+00:00
- Stale: 0
- Fresh: Yes

### Repaired

- Latest: 2026-06-02T00:00:00+00:00
- Oldest: 2025-12-19T00:00:00+00:00
- Stale: 0
- Fresh: Yes