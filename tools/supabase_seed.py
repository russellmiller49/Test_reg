#!/usr/bin/env python3
"""Upload bronchoscopy notes to Supabase for shared annotation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from tools.writer import sha256


def iter_notes(note_dir: Path) -> List[Dict[str, Any]]:
    if not note_dir.exists():
        raise FileNotFoundError(f"Note directory {note_dir} does not exist.")
    notes: List[Dict[str, Any]] = []
    for path in sorted(note_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        notes.append(
            {
                "id": path.stem,
                "display_label": path.name,
                "filename": path.name,
                "note_text": text,
                "raw_text_hash": sha256(text),
            }
        )
    return notes


def batched(items: List[Dict[str, Any]], batch_size: int) -> Iterable[List[Dict[str, Any]]]:
    for idx in range(0, len(items), batch_size):
        yield items[idx : idx + batch_size]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Supabase with annotation notes.")
    parser.add_argument(
        "--note-dir",
        type=Path,
        default=Path("data/synthetic_notes"),
        help="Directory containing *.txt notes (default: data/synthetic_notes)",
    )
    parser.add_argument(
        "--supabase-url",
        default=os.environ.get("SUPABASE_URL"),
        help="Supabase project URL (env SUPABASE_URL)",
    )
    parser.add_argument(
        "--supabase-service-key",
        default=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        help="Supabase service role key (env SUPABASE_SERVICE_ROLE_KEY)",
    )
    parser.add_argument(
        "--notes-table",
        default=os.environ.get("SUPABASE_NOTES_TABLE", "bronch_notes"),
        help="Target table name for notes (default: bronch_notes)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Rows per upsert batch (default: 50)",
    )
    args = parser.parse_args()

    if not args.supabase_url or not args.supabase_service_key:
        parser.error("Supabase URL and service role key are required (set env or pass flags).")

    try:
        from supabase import create_client  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit("Install supabase package first: pip install supabase") from exc

    notes = iter_notes(args.note_dir)
    if not notes:
        print("No notes found to upload.", file=sys.stderr)
        return

    client = create_client(args.supabase_url, args.supabase_service_key)
    uploaded = 0
    for batch in batched(notes, max(1, args.batch_size)):
        try:
            client.table(args.notes_table).upsert(batch, on_conflict="id").execute()
        except Exception as exc:  # pragma: no cover - network call
            raise SystemExit(f"Failed during Supabase upsert: {exc}") from exc
        uploaded += len(batch)

    print(f"Uploaded {uploaded} notes to '{args.notes_table}'.")


if __name__ == "__main__":
    main()
