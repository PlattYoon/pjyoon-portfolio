# Reviewer QA Checklist — CAP Annotation

Use this checklist when reviewing a completed annotation batch before it is merged into a release.

---

## Pre-Review Setup
- [ ] Pull the latest `annotation/schemas/annotated_doc.schema.json`
- [ ] Run `python -m qa.check_schema --input <batch_dir>` — zero errors required before manual review
- [ ] Confirm the annotator has completed the guidelines quiz (v1.0 or later)

---

## Per-Document Checks

### Coverage
- [ ] All entity mentions in the first three pages are annotated (spot check)
- [ ] No obvious entity type (EmissionsTarget, Jurisdiction) is missing from a document that clearly contains them
- [ ] Span boundaries are minimal — no surrounding prepositions or articles included

### Entity Quality
- [ ] EmissionsTarget spans contain either a quantified reduction or an explicit net-zero/carbon-neutral commitment
- [ ] AdaptationMeasure spans are concrete actions, not vague strategies
- [ ] Deadline spans anchor to a specific year or period, not open-ended language
- [ ] Metric spans specify a unit (e.g., MtCO2e, %, kWh) rather than generic words like "tons"

### Relation Quality
- [ ] Every EmissionsTarget has at least one `targets` relation pointing to a Jurisdiction
- [ ] Every `has_deadline` relation correctly links an EmissionsTarget/AdaptationMeasure to a Deadline
- [ ] No self-referential relations (head_id == tail_id)
- [ ] Relation argument types match `VALID_RELATION_ARGS` in `ontology/schema.py`

### Confidence & Flags
- [ ] All spans with confidence < 0.6 have a non-empty `notes` field
- [ ] Adjudication-needed items are copied to `data/adjudication/` with document ID

---

## Batch-Level Checks
- [ ] Inter-annotator agreement (IAA) ≥ 0.75 F1 on entity spans (run `qa/iaa.py`)
- [ ] No duplicate `span_id` or `relation_id` within any document
- [ ] All `doc_id` values are unique within the batch
- [ ] `source_path` values resolve to existing files in `data/raw/` or `data/processed/`

---

## Sign-Off

| Field | Value |
|---|---|
| Reviewer | |
| Batch ID | |
| Date | |
| QA Script Version | |
| Pass / Needs Revision | |

Notes:
