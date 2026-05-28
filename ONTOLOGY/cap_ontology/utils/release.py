"""
utils/release.py

Cut a versioned, reproducible dataset release snapshot.

Steps:
  1. Validate all annotated JSONL files (calls qa.check_schema).
  2. Compute dataset statistics.
  3. Copy data to data/releases/<version>/.
  4. Write a manifest.json with hashes, stats, and schema version.

Usage:
    python -m utils.release --version 1.0.0
    python -m utils.release --version 1.1.0 --input data/annotated/
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

console = Console()

ANNOTATED_DIR = Path("data/annotated")
RELEASES_DIR  = Path("data/releases")
SCHEMA_FILE   = Path("annotation/schemas/annotated_doc.schema.json")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(records: list[dict]) -> dict:
    n_spans     = sum(len(r.get("spans", []))     for r in records)
    n_relations = sum(len(r.get("relations", [])) for r in records)

    entity_counts: dict[str, int] = {}
    relation_counts: dict[str, int] = {}
    jurisdictions: set[str] = set()

    for rec in records:
        jurisdictions.add(rec.get("jurisdiction", "unknown"))
        for s in rec.get("spans", []):
            et = s.get("entity_type", "Unknown")
            entity_counts[et] = entity_counts.get(et, 0) + 1
        for r in rec.get("relations", []):
            rt = r.get("relation_type", "unknown")
            relation_counts[rt] = relation_counts.get(rt, 0) + 1

    return {
        "n_documents":       len(records),
        "n_jurisdictions":   len(jurisdictions),
        "n_spans":           n_spans,
        "n_relations":       n_relations,
        "entity_counts":     dict(sorted(entity_counts.items())),
        "relation_counts":   dict(sorted(relation_counts.items())),
    }


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------

def run(version: str, input_dir: Path, dry_run: bool = False):
    # Validate first
    console.print(f"[bold cyan]Running QA validation before release...[/]")
    from qa.check_schema import run as qa_run
    n_errors = qa_run(input_dir)
    if n_errors > 0:
        console.print(
            f"\n[red bold]Release aborted:[/] {n_errors} document(s) failed QA. "
            "Fix errors before cutting a release."
        )
        return False

    console.print(f"[green]QA passed. Preparing release v{version}...[/]\n")

    # Load all records for stats
    records = []
    jsonl_files = sorted(input_dir.rglob("*.jsonl"))
    for jf in jsonl_files:
        with jf.open(encoding="utf-8") as f:
            records.extend(json.loads(line) for line in f if line.strip())

    stats = compute_stats(records)

    # Build manifest
    manifest = {
        "version":          version,
        "created_at":       datetime.now(timezone.utc).isoformat(),
        "schema_version":   "1.0",
        "stats":            stats,
        "files":            {},
    }

    release_dir = RELEASES_DIR / f"v{version}"

    if not dry_run:
        release_dir.mkdir(parents=True, exist_ok=True)

        # Copy annotated files
        for jf in jsonl_files:
            dest = release_dir / jf.name
            shutil.copy2(jf, dest)
            manifest["files"][jf.name] = sha256_file(dest)

        # Copy schema
        if SCHEMA_FILE.exists():
            dest_schema = release_dir / SCHEMA_FILE.name
            shutil.copy2(SCHEMA_FILE, dest_schema)
            manifest["files"][SCHEMA_FILE.name] = sha256_file(dest_schema)

        # Write manifest
        manifest_path = release_dir / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        console.print(f"[green bold]Release v{version} written to {release_dir}[/]")
    else:
        console.print("[yellow]Dry run — no files written.[/]")

    # Print summary
    console.print("\n[bold]Dataset Statistics:[/]")
    for k, v in stats.items():
        if isinstance(v, dict):
            console.print(f"  {k}:")
            for kk, vv in v.items():
                console.print(f"    {kk}: {vv}")
        else:
            console.print(f"  {k}: {v}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cut a versioned CAP dataset release")
    parser.add_argument("--version",   required=True,          help="Semantic version, e.g. 1.0.0")
    parser.add_argument("--input",     default=str(ANNOTATED_DIR), type=Path)
    parser.add_argument("--dry-run",   action="store_true")
    args = parser.parse_args()
    run(args.version, args.input, args.dry_run)
