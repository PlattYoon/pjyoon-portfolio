"""
qa/check_schema.py

Automated QA: validate every annotated JSONL record against the JSON Schema
and the ontology's relation-argument constraints.

Usage:
    python -m qa.check_schema --input data/annotated/
    python -m qa.check_schema --input data/annotated/preannotated.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

import jsonschema
from rich.console import Console
from rich.table import Table

from ontology.schema import (
    EntityType, RelationType, Span, Relation, validate_relation,
)

console = Console()

SCHEMA_PATH = Path(__file__).parent.parent / "annotation" / "schemas" / "annotated_doc.schema.json"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def load_json_schema() -> dict:
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def check_json_schema(record: dict, schema: dict) -> list[str]:
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for err in validator.iter_errors(record):
        errors.append(f"JSONSchema: {err.json_path} — {err.message}")
    return errors


def check_span_offsets(record: dict) -> list[str]:
    errors = []
    text = record.get("text", "")
    for span in record.get("spans", []):
        s, e = span.get("start", 0), span.get("end", 0)
        if s >= e:
            errors.append(f"Span {span.get('span_id')}: start ({s}) >= end ({e})")
        if e > len(text):
            errors.append(
                f"Span {span.get('span_id')}: end ({e}) beyond text length ({len(text)})"
            )
        expected = text[s:e]
        if expected and span.get("text") and expected != span["text"]:
            errors.append(
                f"Span {span.get('span_id')}: text mismatch — "
                f"expected '{expected[:40]}', got '{span['text'][:40]}'"
            )
    return errors


def check_relation_args(record: dict) -> list[str]:
    errors = []
    spans = [
        Span(
            span_id=s["span_id"],
            start=s["start"],
            end=s["end"],
            text=s.get("text", ""),
            entity_type=EntityType(s["entity_type"]),
            confidence=s.get("confidence", 1.0),
        )
        for s in record.get("spans", [])
        if "entity_type" in s and s["entity_type"] in EntityType._value2member_map_
    ]
    for r in record.get("relations", []):
        if "relation_type" not in r:
            errors.append(f"Relation {r.get('relation_id')}: missing relation_type")
            continue
        if r["relation_type"] not in RelationType._value2member_map_:
            errors.append(f"Relation {r.get('relation_id')}: unknown type {r['relation_type']}")
            continue
        rel = Relation(
            relation_id=r["relation_id"],
            head_id=r["head_id"],
            tail_id=r["tail_id"],
            relation_type=RelationType(r["relation_type"]),
        )
        arg_errors = validate_relation(rel, spans)
        errors.extend(
            f"Relation {r['relation_id']}: {e}" for e in arg_errors
        )
    return errors


def check_unique_ids(record: dict) -> list[str]:
    errors = []
    span_ids = [s.get("span_id") for s in record.get("spans", [])]
    rel_ids  = [r.get("relation_id") for r in record.get("relations", [])]
    for id_list, name in [(span_ids, "span_id"), (rel_ids, "relation_id")]:
        seen = set()
        for id_ in id_list:
            if id_ in seen:
                errors.append(f"Duplicate {name}: {id_}")
            seen.add(id_)
    return errors


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def check_record(record: dict, schema: dict) -> list[str]:
    errors = []
    errors.extend(check_json_schema(record, schema))
    errors.extend(check_span_offsets(record))
    errors.extend(check_relation_args(record))
    errors.extend(check_unique_ids(record))
    return errors


def run(input_path: Path) -> int:
    """Returns number of documents with errors."""
    schema = load_json_schema()
    files: list[Path] = []

    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = sorted(input_path.rglob("*.jsonl"))
    else:
        console.print(f"[red]Path not found:[/] {input_path}")
        return 1

    total_docs = 0
    total_errors = 0
    doc_errors = 0

    table = Table(title="QA Results", show_lines=True)
    table.add_column("doc_id", style="cyan", no_wrap=True)
    table.add_column("Errors", style="red")

    for file in files:
        with file.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                errors = check_record(record, schema)
                total_docs += 1
                if errors:
                    doc_errors += 1
                    total_errors += len(errors)
                    table.add_row(
                        record.get("doc_id", "???"),
                        "\n".join(errors[:10])
                        + (f"\n... and {len(errors)-10} more" if len(errors) > 10 else ""),
                    )

    console.print(table)
    console.print(
        f"\n[bold]Summary:[/] {total_docs} docs checked — "
        f"[{'green' if doc_errors == 0 else 'red'}]{doc_errors} with errors[/], "
        f"{total_errors} total error(s)"
    )
    return doc_errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QA schema compliance checker")
    parser.add_argument("--input", required=True, type=Path,
                        help="Path to JSONL file or directory")
    args = parser.parse_args()
    n_errors = run(args.input)
    sys.exit(0 if n_errors == 0 else 1)
