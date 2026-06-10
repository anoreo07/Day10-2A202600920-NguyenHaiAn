from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) < 3:
        raise ValueError(f"Need at least 3 documents, got {len(df)}")
    test_set: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        paper_id = row["paper_id"]
        if row["summary"] and len(str(row["summary"])) > 20:
            test_set.append({
                "id": f"q-summary-{idx}",
                "question_type": "summary",
                "question": f"What is the summary of the paper titled '{row['title']}'?",
                "ground_truth": str(row["summary"]),
                "ground_truth_doc_ids": [paper_id],
            })
        if row["authors_joined"]:
            test_set.append({
                "id": f"q-authors-{idx}",
                "question_type": "authors",
                "question": f"Who authored the paper '{row['title']}'?",
                "ground_truth": str(row["authors_joined"]),
                "ground_truth_doc_ids": [paper_id],
            })
        if row["published"]:
            test_set.append({
                "id": f"q-date-{idx}",
                "question_type": "date",
                "question": f"When was the paper '{row['title']}' published?",
                "ground_truth": str(row["published"]),
                "ground_truth_doc_ids": [paper_id],
            })
        if row["categories_joined"]:
            test_set.append({
                "id": f"q-categories-{idx}",
                "question_type": "categories",
                "question": f"What categories does the paper '{row['title']}' belong to?",
                "ground_truth": str(row["categories_joined"]),
                "ground_truth_doc_ids": [paper_id],
            })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, test_set)
    return test_set
