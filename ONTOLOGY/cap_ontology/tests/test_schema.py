"""
tests/test_schema.py

Unit tests for ontology schema validation logic.
"""

import pytest

from ontology.schema import (
    AnnotatedDocument, EntityType, RelationType, Relation, Span,
    validate_relation,
)


def make_span(span_id, start, end, entity_type, text="text"):
    return Span(
        span_id=span_id, start=start, end=end,
        text=text, entity_type=entity_type,
    )


# ---------------------------------------------------------------------------
# Span
# ---------------------------------------------------------------------------

def test_span_valid():
    s = make_span("s0", 0, 5, EntityType.JURISDICTION, "Paris")
    assert s.span_id == "s0"


def test_span_invalid_offsets():
    with pytest.raises(ValueError):
        make_span("s0", 10, 5, EntityType.JURISDICTION)


def test_span_invalid_confidence():
    with pytest.raises(ValueError):
        Span(span_id="s0", start=0, end=3, text="foo",
             entity_type=EntityType.SECTOR, confidence=1.5)


# ---------------------------------------------------------------------------
# Relation validation
# ---------------------------------------------------------------------------

def test_relation_valid_targets():
    spans = [
        make_span("s0", 0, 10, EntityType.JURISDICTION, "Pittsburgh"),
        make_span("s1", 20, 40, EntityType.EMISSIONS_TARGET, "net-zero by 2050"),
    ]
    rel = Relation(
        relation_id="r0", head_id="s0", tail_id="s1",
        relation_type=RelationType.TARGETS,
    )
    errors = validate_relation(rel, spans)
    assert errors == [], f"Unexpected errors: {errors}"


def test_relation_wrong_head_type():
    spans = [
        make_span("s0", 0, 10, EntityType.SECTOR, "buildings"),
        make_span("s1", 20, 40, EntityType.EMISSIONS_TARGET, "45% reduction"),
    ]
    rel = Relation(
        relation_id="r0", head_id="s0", tail_id="s1",
        relation_type=RelationType.TARGETS,
    )
    errors = validate_relation(rel, spans)
    assert any("head" in e.lower() for e in errors)


def test_relation_missing_span():
    spans = [make_span("s0", 0, 5, EntityType.JURISDICTION)]
    rel = Relation(
        relation_id="r0", head_id="s0", tail_id="MISSING",
        relation_type=RelationType.TARGETS,
    )
    errors = validate_relation(rel, spans)
    assert any("MISSING" in e for e in errors)


def test_relation_has_deadline_valid():
    spans = [
        make_span("s0", 0, 20, EntityType.EMISSIONS_TARGET, "net-zero"),
        make_span("s1", 25, 32, EntityType.DEADLINE, "by 2050"),
    ]
    rel = Relation(
        relation_id="r0", head_id="s0", tail_id="s1",
        relation_type=RelationType.HAS_DEADLINE,
    )
    assert validate_relation(rel, spans) == []


# ---------------------------------------------------------------------------
# AnnotatedDocument
# ---------------------------------------------------------------------------

def test_annotated_document_spans_by_type():
    doc = AnnotatedDocument(
        doc_id="doc1", source_path="foo.txt",
        jurisdiction="TestCity", year=2023,
        text="net-zero by 2050 in buildings",
    )
    doc.spans = [
        make_span("s0", 0, 16, EntityType.EMISSIONS_TARGET),
        make_span("s1", 20, 29, EntityType.SECTOR),
    ]
    assert len(doc.spans_by_type(EntityType.EMISSIONS_TARGET)) == 1
    assert len(doc.spans_by_type(EntityType.SECTOR)) == 1
    assert len(doc.spans_by_type(EntityType.DEADLINE)) == 0


def test_annotated_document_get_span():
    doc = AnnotatedDocument(
        doc_id="doc1", source_path="foo.txt",
        jurisdiction="TestCity", year=2023, text="x" * 50,
    )
    s = make_span("s5", 0, 5, EntityType.JURISDICTION)
    doc.spans = [s]
    assert doc.get_span("s5") is s
    assert doc.get_span("s99") is None
