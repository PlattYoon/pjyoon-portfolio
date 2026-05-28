"""
utils/io.py

Shared helpers for reading/writing JSONL, iterating annotation records,
and pretty-printing documents.
"""

import json
from pathlib import Path
from typing import Iterator


def read_jsonl(path: Path) -> Iterator[dict]:
    """Yield records from a JSONL file, skipping blank lines."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(records: list[dict], path: Path, mode: str = "w"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def iter_all_jsonl(directory: Path) -> Iterator[dict]:
    """Recursively yield all records from all JSONL files in a directory."""
    for jf in sorted(directory.rglob("*.jsonl")):
        yield from read_jsonl(jf)


def summarize_record(record: dict) -> str:
    """One-line summary of an annotated document."""
    n_spans = len(record.get("spans", []))
    n_rels  = len(record.get("relations", []))
    return (
        f"{record.get('doc_id', '?')} | "
        f"{record.get('jurisdiction', '?')} | "
        f"year={record.get('year', '?')} | "
        f"{n_spans} spans, {n_rels} relations"
    )
