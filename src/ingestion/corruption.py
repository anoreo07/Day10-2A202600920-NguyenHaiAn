from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    log: dict[str, Any] = {}
    corrupted = df.copy()

    n = len(corrupted)
    if n == 0:
        write_json(output_log_path, {"error": "Empty DataFrame, nothing to corrupt"})
        return corrupted

    n_drop = max(1, n // 4)
    drop_indices = corrupted.head(n_drop).index
    corrupted = corrupted.drop(drop_indices)
    log["dropped_latest_records"] = {
        "count": int(n_drop),
        "indices": [int(i) for i in drop_indices],
    }

    n_blank = max(1, n // 4)
    blank_indices = corrupted.sample(n=min(n_blank, len(corrupted))).index
    corrupted.loc[blank_indices, "summary"] = ""
    log["blank_summary"] = {"count": int(len(blank_indices)), "indices": [int(i) for i in blank_indices]}

    n_noise = max(1, n // 4)
    noise_indices = corrupted.sample(n=min(n_noise, len(corrupted))).index
    corrupted.loc[noise_indices, "summary"] = corrupted.loc[noise_indices, "summary"].apply(
        lambda x: str(x) + " NOISY_DATA_INJECTION_12345" if pd.notna(x) and str(x).strip() else x
    )
    log["noise_injection"] = {"count": int(len(noise_indices)), "indices": [int(i) for i in noise_indices]}

    n_truncate = max(1, n // 4)
    truncate_indices = corrupted.sample(n=min(n_truncate, len(corrupted))).index
    corrupted.loc[truncate_indices, "title"] = corrupted.loc[truncate_indices, "title"].apply(
        lambda x: str(x)[:10] + "..." if pd.notna(x) and len(str(x)) > 10 else x
    )
    log["truncated_title"] = {"count": int(len(truncate_indices)), "indices": [int(i) for i in truncate_indices]}

    n_stale = max(1, n // 4)
    stale_indices = corrupted.sample(n=min(n_stale, len(corrupted))).index
    corrupted.loc[stale_indices, "published"] = "1900-01-01"
    log["stale_date"] = {"count": int(len(stale_indices)), "indices": [int(i) for i in stale_indices]}

    n_dup = max(1, n // 4)
    dup_rows = corrupted.sample(n=min(n_dup, len(corrupted)))
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)
    log["duplicate_rows"] = {"count": int(len(dup_rows)), "indices_of_origin": [int(i) for i in dup_rows.index]}

    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        ),
        axis=1,
    )
    corrupted = corrupted.reset_index(drop=True)
    log["final_row_count"] = len(corrupted)
    write_json(output_log_path, log)
    return corrupted
