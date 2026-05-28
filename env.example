# Climate Action Plan Ontology

A research toolkit for building fine-grained ontologies of Climate Action Plans (CAPs) across jurisdictions, enabling large-scale policy analysis for climate adaptation and emissions reduction targets.

## Project Structure

```
cap_ontology/
├── data/
│   ├── raw/          # Original CAP documents (PDFs, HTMLs)
│   ├── processed/    # Cleaned, chunked text
│   ├── annotated/    # Labeled spans + relations (JSONL)
│   └── releases/     # Versioned dataset snapshots
├── ontology/         # Entity/relation schema definitions
├── annotation/
│   ├── schemas/      # JSON Schema for annotation format
│   ├── guidelines/   # Annotator instruction docs
│   └── checklists/   # Reviewer QA checklists
├── pipelines/        # Active learning + LLM annotation pipelines
├── qa/               # Automated QA and schema compliance scripts
├── models/           # Model wrappers (LLM prompting, fine-tuning)
├── utils/            # Shared helpers (I/O, text, versioning)
├── notebooks/        # Exploratory analysis
├── tests/            # Unit tests
└── docs/             # Extended documentation
```

## Quickstart

```bash
pip install -r requirements.txt

# 1. Ingest raw CAP documents
python -m pipelines.ingest --input data/raw/ --output data/processed/

# 2. Run LLM-assisted pre-annotation
python -m pipelines.preannotate --input data/processed/ --output data/annotated/

# 3. Run QA checks on annotations
python -m qa.check_schema --input data/annotated/

# 4. Cut a versioned release
python -m utils.release --version 1.0.0
```

## Key Concepts

- **Entity types**: `EmissionsTarget`, `AdaptationMeasure`, `Jurisdiction`, `Sector`, `Deadline`, `Stakeholder`
- **Relation types**: `targets`, `implements`, `governs`, `reports_to`, `supersedes`
- **Active learning**: uncertainty sampling over LLM confidence scores to prioritize human review
