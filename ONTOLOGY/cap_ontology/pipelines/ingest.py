"""
pipelines/ingest.py

Ingest raw CAP documents (PDF or plain text), extract and clean text,
chunk into passages, and write to data/processed/ as JSONL.

Usage:
    python -m pipelines.ingest --input data/raw/ --output data/processed/
"""

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterator

from tqdm import tqdm


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Unicode normalization, collapse whitespace, strip boilerplate artifacts."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\n{3,}", "\n\n", text)          # collapse blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)           # collapse spaces/tabs
    text = re.sub(r"\f", "\n", text)                 # form feeds → newlines
    text = re.sub(r"\x00", "", text)                 # null bytes
    return text.strip()


def remove_boilerplate(text: str) -> str:
    """
    Heuristically strip page headers, footers, and table-of-contents lines.
    Extend this with document-specific patterns as needed.
    """
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip page numbers
        if re.fullmatch(r"(page\s*)?\d+(\s*of\s*\d+)?", stripped, re.IGNORECASE):
            continue
        # Skip very short lines that are likely headers/footers
        if len(stripped) < 4 and not stripped.isalpha():
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> list[dict]:
    """
    Split text into overlapping chunks suitable for LLM context windows.
    Returns list of {'chunk_id': int, 'start': int, 'end': int, 'text': str}.
    """
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # Try to break at a sentence boundary
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + max_chars // 2:
                end = boundary + 1
        chunks.append({
            "chunk_id": chunk_id,
            "start": start,
            "end": end,
            "text": text[start:end],
        })
        chunk_id += 1
        start = end - overlap  # overlap
    return chunks


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_pdf(path: Path) -> str:
    """Extract text from PDF using pdfminer.six if available, else raise."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path))
    except ImportError:
        raise ImportError(
            "pdfminer.six is required for PDF ingestion. "
            "Run: pip install pdfminer.six"
        )


LOADERS = {
    ".txt": load_txt,
    ".md":  load_txt,
    ".pdf": load_pdf,
}


def load_document(path: Path) -> str:
    suffix = path.suffix.lower()
    loader = LOADERS.get(suffix)
    if loader is None:
        raise ValueError(f"Unsupported file type: {suffix}")
    return loader(path)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_metadata(path: Path, text: str) -> dict:
    """Best-effort metadata from filename and text heuristics."""
    year_match = re.search(r"\b(19|20)\d{2}\b", path.stem)
    year = int(year_match.group()) if year_match else None

    # Simple jurisdiction guess from filename
    jurisdiction = re.sub(r"[_\-]+", " ", path.stem.split("_")[0]).title()

    return {
        "filename": path.name,
        "char_count": len(text),
        "year_guess": year,
        "jurisdiction_guess": jurisdiction,
    }


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def doc_id_from_path(path: Path) -> str:
    h = hashlib.md5(str(path.resolve()).encode()).hexdigest()[:8]
    return f"{path.stem}_{h}"


def ingest_file(path: Path, max_chars: int, overlap: int) -> dict:
    raw_text = load_document(path)
    text = remove_boilerplate(normalize_text(raw_text))
    metadata = extract_metadata(path, text)
    chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)

    return {
        "doc_id": doc_id_from_path(path),
        "source_path": str(path),
        "jurisdiction": metadata["jurisdiction_guess"],
        "year": metadata["year_guess"],
        "text": text,
        "chunks": chunks,
        "metadata": metadata,
    }


def iter_input_files(input_dir: Path) -> Iterator[Path]:
    for ext in LOADERS:
        yield from sorted(input_dir.rglob(f"*{ext}"))


def run(input_dir: Path, output_dir: Path, max_chars: int, overlap: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "processed.jsonl"

    files = list(iter_input_files(input_dir))
    print(f"Found {len(files)} document(s) in {input_dir}")

    errors = []
    with out_path.open("w", encoding="utf-8") as f:
        for path in tqdm(files, desc="Ingesting"):
            try:
                record = ingest_file(path, max_chars=max_chars, overlap=overlap)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                errors.append((path, str(e)))

    print(f"Wrote {len(files) - len(errors)} records to {out_path}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for p, msg in errors:
            print(f"  {p}: {msg}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest raw CAP documents")
    parser.add_argument("--input",     required=True, type=Path)
    parser.add_argument("--output",    required=True, type=Path)
    parser.add_argument("--max-chars", default=2000,  type=int)
    parser.add_argument("--overlap",   default=200,   type=int)
    args = parser.parse_args()
    run(args.input, args.output, args.max_chars, args.overlap)
