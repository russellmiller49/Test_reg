"""Backend interfaces for bronze annotation tooling (local + remote)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tools.writer import build_annotation_record_v22, save_annotation_v22, sha256


@dataclass(frozen=True)
class NoteEntry:
    """Lightweight descriptor for an annotatable note."""

    note_id: str
    display_label: str
    metadata: Dict[str, Any]


class AnnotationBackendError(RuntimeError):
    """Raised when a backend operation fails."""


class BaseAnnotationBackend:
    """Abstract base class for annotation storage backends."""

    def requires_annotator(self) -> bool:
        return False

    def list_notes(self) -> List[NoteEntry]:
        raise NotImplementedError

    def list_annotated_ids(self) -> Set[str]:
        raise NotImplementedError

    def load_note_text(self, note_id: str) -> str:
        raise NotImplementedError

    def save_annotation(
        self,
        note_id: str,
        note_text: str,
        ui_payload: Dict[str, Any],
        annotator: Optional[str],
    ) -> None:
        raise NotImplementedError

    def refresh(self) -> None:
        """Reset any internal caches."""


class LocalFilesystemBackend(BaseAnnotationBackend):
    """Existing local workflow (notes on disk, JSONL append)."""

    def __init__(
        self,
        notes_dir: Path,
        annotation_path: Path,
    ) -> None:
        self.notes_dir = notes_dir
        self.annotation_path = annotation_path
        self._notes_cache: Optional[List[NoteEntry]] = None
        self._annotated_cache: Optional[Set[str]] = None

    def requires_annotator(self) -> bool:
        return False

    def list_notes(self) -> List[NoteEntry]:
        if self._notes_cache is None:
            notes: List[NoteEntry] = []
            for path in sorted(self.notes_dir.glob("*.txt")):
                notes.append(
                    NoteEntry(
                        note_id=path.stem,
                        display_label=path.name,
                        metadata={"path": str(path)},
                    )
                )
            self._notes_cache = notes
        return self._notes_cache

    def list_annotated_ids(self) -> Set[str]:
        if self._annotated_cache is not None:
            return set(self._annotated_cache)
        annotated: Set[str] = set()
        if self.annotation_path.exists():
            with self.annotation_path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    record_id = record.get("id")
                    if record_id:
                        annotated.add(record_id)
        self._annotated_cache = annotated
        return set(annotated)

    def load_note_text(self, note_id: str) -> str:
        target = self.notes_dir / f"{note_id}.txt"
        if not target.exists():
            raise AnnotationBackendError(f"Note {note_id} not found at {target}")
        return target.read_text(encoding="utf-8")

    def save_annotation(
        self,
        note_id: str,
        note_text: str,
        ui_payload: Dict[str, Any],
        annotator: Optional[str],
    ) -> None:
        try:
            save_annotation_v22(note_id, note_text, ui_payload)
        except Exception as exc:  # pragma: no cover - surface in UI
            raise AnnotationBackendError(str(exc)) from exc
        self._annotated_cache = None

    def refresh(self) -> None:
        self._notes_cache = None
        self._annotated_cache = None


class SupabaseBackend(BaseAnnotationBackend):
    """Cloud backend that stores notes/annotations in Supabase."""

    def __init__(
        self,
        url: str,
        anon_key: str,
        *,
        notes_table: str = "bronch_notes",
        annotations_table: str = "bronch_annotations",
    ) -> None:
        try:
            from supabase import Client, create_client  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise AnnotationBackendError(
                "Supabase backend requires the `supabase` package. Install with `pip install supabase`."
            ) from exc
        if not url or not anon_key:
            raise AnnotationBackendError("Supabase URL and anon key are required.")
        self._client: Client = create_client(url, anon_key)
        self.notes_table = notes_table
        self.annotations_table = annotations_table
        self._notes_cache: Optional[List[NoteEntry]] = None
        self._annotated_cache: Optional[Set[str]] = None

    def requires_annotator(self) -> bool:
        return True

    def _execute(self, request: Any, error_message: str) -> Any:
        try:
            response = request.execute()
        except Exception as exc:  # pragma: no cover - network call
            raise AnnotationBackendError(f"{error_message}: {exc}") from exc
        data = getattr(response, "data", None)
        if data is None:
            raise AnnotationBackendError(f"{error_message}: empty response")
        return data

    def list_notes(self) -> List[NoteEntry]:
        if self._notes_cache is not None:
            return self._notes_cache
        request = (
            self._client.table(self.notes_table)
            .select("id, display_label, filename, tags")
            .order("created_at")
        )
        rows = self._execute(request, "Failed to fetch notes")
        notes: List[NoteEntry] = []
        for row in rows:
            note_id = row.get("id")
            if not note_id:
                continue
            label = row.get("display_label") or row.get("filename") or note_id
            notes.append(NoteEntry(note_id=note_id, display_label=label, metadata=row))
        self._notes_cache = notes
        return notes

    def list_annotated_ids(self) -> Set[str]:
        if self._annotated_cache is not None:
            return set(self._annotated_cache)
        request = self._client.table(self.annotations_table).select("note_id")
        rows = self._execute(request, "Failed to fetch annotations")
        ids = {row["note_id"] for row in rows if row.get("note_id")}
        self._annotated_cache = ids
        return set(ids)

    def load_note_text(self, note_id: str) -> str:
        request = (
            self._client.table(self.notes_table)
            .select("note_text")
            .eq("id", note_id)
            .limit(1)
        )
        rows = self._execute(request, f"Failed to load note {note_id}")
        if not rows:
            raise AnnotationBackendError(f"Note {note_id} not found.")
        note_text = rows[0].get("note_text")
        if note_text is None:
            raise AnnotationBackendError(f"Note {note_id} is missing note_text content.")
        return note_text

    def save_annotation(
        self,
        note_id: str,
        note_text: str,
        ui_payload: Dict[str, Any],
        annotator: Optional[str],
    ) -> None:
        if not annotator:
            raise AnnotationBackendError("Annotator ID is required for Supabase mode.")
        record = build_annotation_record_v22(note_id, note_text, ui_payload)
        payload = record.model_dump()
        data = {
            "note_id": note_id,
            "annotator": annotator,
            "record": payload,
            "raw_text_hash": sha256(note_text),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        request = (
            self._client.table(self.annotations_table)
            .upsert(data, on_conflict="note_id")
        )
        self._execute(request, f"Failed to save annotation for {note_id}")
        self._annotated_cache = None

    def refresh(self) -> None:
        self._notes_cache = None
        self._annotated_cache = None


def resolve_backend(
    *,
    backend_name: Optional[str],
    local_notes_dir: Path,
    annotation_path: Path,
    supabase_settings: Optional[Dict[str, Any]] = None,
) -> BaseAnnotationBackend:
    """Factory to create an appropriate backend based on configuration."""

    backend = (backend_name or "local").lower()
    if backend == "supabase":
        settings = supabase_settings or {}
        url = settings.get("url") or os.environ.get("SUPABASE_URL")
        anon_key = (
            settings.get("anon_key")
            or settings.get("api_key")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("SUPABASE_API_KEY")
        )
        notes_table = settings.get("notes_table") or os.environ.get("SUPABASE_NOTES_TABLE", "bronch_notes")
        annotations_table = (
            settings.get("annotations_table") or os.environ.get("SUPABASE_ANNOTATIONS_TABLE", "bronch_annotations")
        )
        return SupabaseBackend(
            url=url or "",
            anon_key=anon_key or "",
            notes_table=notes_table,
            annotations_table=annotations_table,
        )
    if backend != "local":
        raise AnnotationBackendError(f"Unsupported backend '{backend}'.")
    return LocalFilesystemBackend(local_notes_dir, annotation_path)
