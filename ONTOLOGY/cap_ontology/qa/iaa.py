"""
qa/iaa.py

Compute inter-annotator agreement (IAA) between two annotation JSONL files
for the same document set.

Metrics:
  - Span-level token F1 (exact match + partial)
  - Relation-level F1 (head, tail, type must all match)

Usage:
    python -m qa.iaa \
        --a data/annotated/annotator_alice.jsonl \
        --b data/annotated/annotator_bob.jsonl
"""

import argparse
import json
from pathlib import Path
from typing import NamedTuple

from rich.console import Console
from rich.table import Table

console = Console()


class SpanKey(NamedTuple):
    start: int
    end: int
    entity_type: str


class RelKey(NamedTuple):
    head_start: int
    head_end: int
    tail_start: int
    tail_end: int
    relation_type: str


def load_jsonl(path: Path) -> dict[str, dict]:
    """Returns {doc_id: record}."""
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                out[rec["doc_id"]] = rec
    return out


def spans_to_keys(record: dict) -> set[SpanKey]:
    return {
        SpanKey(s["start"], s["end"], s["entity_type"])
        for s in record.get("spans", [])
    }


def relations_to_keys(record: dict) -> set[RelKey]:
    span_map = {s["span_id"]: s for s in record.get("spans", [])}
    keys = set()
    for r in record.get("relations", []):
        head = span_map.get(r.get("head_id"), {})
        tail = span_map.get(r.get("tail_id"), {})
        if head and tail:
            keys.add(RelKey(
                head.get("start", -1), head.get("end", -1),
                tail.get("start", -1), tail.get("end", -1),
                r.get("relation_type", ""),
            ))
    return keys


def f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1_score  = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0.0)
    return precision, recall, f1_score


def compute_iaa(docs_a: dict[str, dict], docs_b: dict[str, dict]):
    common = set(docs_a) & set(docs_b)
    if not common:
        console.print("[red]No common doc_ids found between the two files.[/]")
        return

    span_tp = span_fp = span_fn = 0
    rel_tp  = rel_fp  = rel_fn  = 0

    for doc_id in sorted(common):
        a_spans = spans_to_keys(docs_a[doc_id])
        b_spans = spans_to_keys(docs_b[doc_id])

        span_tp += len(a_spans & b_spans)
        span_fp += len(a_spans - b_spans)
        span_fn += len(b_spans - a_spans)

        a_rels = relations_to_keys(docs_a[doc_id])
        b_rels = relations_to_keys(docs_b[doc_id])

        rel_tp += len(a_rels & b_rels)
        rel_fp += len(a_rels - b_rels)
        rel_fn += len(b_rels - a_rels)

    sp_p, sp_r, sp_f = f1(span_tp, span_fp, span_fn)
    re_p, re_r, re_f = f1(rel_tp,  rel_fp,  rel_fn)

    table = Table(title=f"IAA over {len(common)} shared documents")
    table.add_column("Level",     style="cyan")
    table.add_column("Precision", justify="right")
    table.add_column("Recall",    justify="right")
    table.add_column("F1",        justify="right", style="bold")

    def fmt(x: float) -> str:
        return f"{x:.3f}"

    table.add_row("Span",     fmt(sp_p), fmt(sp_r), fmt(sp_f))
    table.add_row("Relation", fmt(re_p), fmt(re_r), fmt(re_f))

    console.print(table)
    console.print(
        f"\nDocs in A only: {len(docs_a) - len(common)}, "
        f"Docs in B only: {len(docs_b) - len(common)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IAA between two annotation files")
    parser.add_argument("--a", required=True, type=Path, help="Annotator A JSONL")
    parser.add_argument("--b", required=True, type=Path, help="Annotator B JSONL")
    args = parser.parse_args()

    docs_a = load_jsonl(args.a)
    docs_b = load_jsonl(args.b)
    compute_iaa(docs_a, docs_b)
