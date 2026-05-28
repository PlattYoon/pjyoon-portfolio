"""
pipelines/preannotate.py

Active-learning-assisted pre-annotation pipeline.

For each processed document:
  1. Send chunks to an LLM with a structured extraction prompt.
  2. Parse the LLM response into Span and Relation objects.
  3. Score confidence; flag low-confidence predictions for human review.
  4. Write pre-annotations to data/annotated/ as JSONL.

Usage:
    python -m pipelines.preannotate \
        --input data/processed/ \
        --output data/annotated/ \
        --model gpt-4o \
        --confidence-threshold 0.6
"""

import argparse
import json
import os
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from ontology.schema import (
    AnnotatedDocument, EntityType, RelationType, Relation, Span,
    validate_relation,
)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

ENTITY_LIST = "\n".join(f"  - {e.value}" for e in EntityType)
RELATION_LIST = "\n".join(f"  - {r.value}" for r in RelationType)

SYSTEM_PROMPT = f"""\
You are an expert annotator of Climate Action Plans (CAPs).
Extract all entities and relations from the given text passage.

Entity types:
{ENTITY_LIST}

Relation types (head → tail):
{RELATION_LIST}

Return ONLY a JSON object with this exact structure:
{{
  "spans": [
    {{"span_id": "s0", "start": <int>, "end": <int>, "text": "<str>",
      "entity_type": "<EntityType>", "confidence": <0.0-1.0>}}
  ],
  "relations": [
    {{"relation_id": "r0", "head_id": "<span_id>", "tail_id": "<span_id>",
      "relation_type": "<RelationType>", "confidence": <0.0-1.0>}}
  ]
}}
Return nothing else — no preamble, no explanation.
"""

def build_user_prompt(chunk_text: str, chunk_id: int, char_offset: int) -> str:
    return (
        f"[Passage chunk_id={chunk_id}, char_offset={char_offset}]\n\n"
        f"{chunk_text}\n\n"
        "Extract entities and relations as JSON."
    )


# ---------------------------------------------------------------------------
# LLM call (OpenAI-compatible)
# ---------------------------------------------------------------------------

def call_llm(
    user_prompt: str,
    model: str = "gpt-4o",
    max_tokens: int = 2048,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """Call OpenAI chat completions. Returns raw response text or None on error."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package required: pip install openai")

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError("Set OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  LLM error: {e}")
        return None


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """Remove ```json ... ``` fences if present."""
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def parse_llm_response(
    raw: str,
    chunk_id: int,
    char_offset: int,
) -> tuple[list[Span], list[Relation]]:
    """Parse LLM JSON output into Span and Relation objects."""
    spans: list[Span] = []
    relations: list[Relation] = []

    try:
        data = json.loads(_strip_markdown(raw))
    except json.JSONDecodeError as e:
        print(f"  JSON parse error (chunk {chunk_id}): {e}")
        return spans, relations

    for i, s in enumerate(data.get("spans", [])):
        try:
            # Adjust character offsets to document-level
            abs_start = char_offset + s["start"]
            abs_end   = char_offset + s["end"]
            span = Span(
                span_id=f"c{chunk_id}_s{i}",
                start=abs_start,
                end=abs_end,
                text=s.get("text", ""),
                entity_type=EntityType(s["entity_type"]),
                confidence=float(s.get("confidence", 1.0)),
                annotator="llm",
            )
            spans.append(span)
        except (KeyError, ValueError) as e:
            print(f"  Skipping malformed span {s}: {e}")

    span_id_remap = {
        s_raw["span_id"]: f"c{chunk_id}_s{i}"
        for i, s_raw in enumerate(data.get("spans", []))
    }

    for j, r in enumerate(data.get("relations", [])):
        try:
            head = span_id_remap.get(r["head_id"], r["head_id"])
            tail = span_id_remap.get(r["tail_id"], r["tail_id"])
            relation = Relation(
                relation_id=f"c{chunk_id}_r{j}",
                head_id=head,
                tail_id=tail,
                relation_type=RelationType(r["relation_type"]),
                confidence=float(r.get("confidence", 1.0)),
                annotator="llm",
            )
            relations.append(relation)
        except (KeyError, ValueError) as e:
            print(f"  Skipping malformed relation {r}: {e}")

    return spans, relations


# ---------------------------------------------------------------------------
# Active learning: uncertainty sampling
# ---------------------------------------------------------------------------

def flag_uncertain(
    spans: list[Span],
    relations: list[Relation],
    threshold: float,
) -> tuple[list[Span], list[Relation]]:
    """
    Mark low-confidence predictions for human review by setting a note.
    Returns the same lists mutated in place for convenience.
    """
    for span in spans:
        if span.confidence < threshold:
            span.notes = f"[REVIEW_NEEDED] confidence={span.confidence:.2f}"
    for rel in relations:
        if rel.confidence < threshold:
            rel.notes = f"[REVIEW_NEEDED] confidence={rel.confidence:.2f}"
    return spans, relations


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def annotate_document(
    record: dict,
    model: str,
    confidence_threshold: float,
    api_key: Optional[str],
    sleep_between: float = 0.5,
) -> AnnotatedDocument:
    all_spans: list[Span] = []
    all_relations: list[Relation] = []

    for chunk in record.get("chunks", []):
        user_prompt = build_user_prompt(
            chunk["text"], chunk["chunk_id"], chunk["start"]
        )
        raw = call_llm(user_prompt, model=model, api_key=api_key)
        if raw is None:
            continue

        spans, relations = parse_llm_response(raw, chunk["chunk_id"], chunk["start"])

        # Validate relations against known spans
        for rel in relations:
            errors = validate_relation(rel, spans)
            if errors:
                rel.notes = f"[SCHEMA_ERROR] {'; '.join(errors)}"

        flag_uncertain(spans, relations, confidence_threshold)
        all_spans.extend(spans)
        all_relations.extend(relations)

        time.sleep(sleep_between)

    return AnnotatedDocument(
        doc_id=record["doc_id"],
        source_path=record["source_path"],
        jurisdiction=record["jurisdiction"],
        year=record.get("year"),
        text=record["text"],
        spans=all_spans,
        relations=all_relations,
        metadata={**record.get("metadata", {}), "annotator": "llm", "model": model},
    )


def run(
    input_dir: Path,
    output_dir: Path,
    model: str,
    confidence_threshold: float,
    api_key: Optional[str],
):
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "preannotated.jsonl"

    processed_files = sorted(input_dir.glob("*.jsonl"))
    if not processed_files:
        print(f"No JSONL files found in {input_dir}")
        return

    total = 0
    with out_path.open("w", encoding="utf-8") as f_out:
        for jsonl_file in processed_files:
            with jsonl_file.open(encoding="utf-8") as f_in:
                records = [json.loads(line) for line in f_in if line.strip()]

            for record in tqdm(records, desc=jsonl_file.name):
                doc = annotate_document(
                    record, model, confidence_threshold, api_key
                )
                # Convert dataclasses to plain dicts for JSON serialisation
                out_record = {
                    "doc_id":       doc.doc_id,
                    "source_path":  doc.source_path,
                    "jurisdiction": doc.jurisdiction,
                    "year":         doc.year,
                    "text":         doc.text,
                    "spans":        [asdict(s) for s in doc.spans],
                    "relations":    [asdict(r) for r in doc.relations],
                    "metadata":     doc.metadata,
                }
                f_out.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                total += 1

    print(f"Pre-annotated {total} documents → {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-assisted CAP pre-annotation")
    parser.add_argument("--input",                required=True, type=Path)
    parser.add_argument("--output",               required=True, type=Path)
    parser.add_argument("--model",                default="gpt-4o")
    parser.add_argument("--confidence-threshold", default=0.6, type=float)
    parser.add_argument("--api-key",              default=None)
    args = parser.parse_args()

    run(args.input, args.output, args.model, args.confidence_threshold, args.api_key)
