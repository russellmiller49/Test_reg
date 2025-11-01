"""Persistence helpers for v2.2 gold corpus records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from bronch_schema import (
    Complication,
    GoldRecord,
    NodeSampling,
    PeripheralTarget,
    Procedure,
    QualityMetrics,
    Sedation,
    SpecimenRouting,
    Therapeutic,
)

OUT_PATH = Path("eval/data/gold_corpus_v2_2.jsonl")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_complications(raw: List[Dict[str, Any]]) -> List[Complication]:
    if not raw:
        return []
    comps: List[Complication] = []
    for item in raw:
        comps.append(Complication(**item))
    return comps


def build_annotation_record_v22(note_id: str, note_text: str, ui: Dict[str, Any]) -> GoldRecord:
    """Construct a GoldRecord instance from UI payload."""
    sedation_raw = ui.get("sedation") or {}
    sedation_block = Sedation(**sedation_raw)

    ebus_nodes = [NodeSampling(**node) for node in ui.get("ebus_nodes", [])]
    peripheral_targets = [PeripheralTarget(**target) for target in ui.get("peripheral_targets", [])]
    peripheral = {"targets": peripheral_targets} if peripheral_targets else None

    therapeutic_block = ui.get("therapeutic")
    therapeutic = Therapeutic(**therapeutic_block) if therapeutic_block else None

    procedure = Procedure(
        patient_name=ui.get("patient_name"),
        mrn=ui.get("mrn"),
        dob=ui.get("dob"),
        procedure_date=ui.get("procedure_date"),
        indication=ui.get("indication_text"),
        procedure_category=ui.get("procedure_category"),
        procedure_types=ui.get("procedure_components", []),
        procedure_duration_min=ui.get("procedure_duration_min"),
        primary_tumor_location=ui.get("primary_tumor_location"),
        sedation=sedation_block,
        ebus_nodes=ebus_nodes,
        peripheral=peripheral,
        specimens=SpecimenRouting(**ui.get("specimens", {})),
        complications=_build_complications(ui.get("complications", [])),
        quality=QualityMetrics(**ui.get("quality_metrics", {})) if ui.get("quality_metrics") else QualityMetrics(),
        inferred=ui.get("inferred_flags", {}),
        disposition=ui.get("disposition"),
        plan_summary=ui.get("plan_summary"),
        raw_text_hash=sha256(note_text),
        document_type=ui.get("document_type", "procedure_note"),
        therapeutic=therapeutic,
    )

    record = GoldRecord(
        id=note_id,
        note_text=note_text,
        procedure=procedure,
        field_status=ui.get("field_status", {}),
        field_status_detail=ui.get("field_status_detail", {}),
    )
    return record


def save_annotation_v22(note_id: str, note_text: str, ui: Dict[str, Any]) -> None:
    """
    Persist a v2.2 annotation record.

    The `ui` dict captures raw Streamlit inputs including field_status tracking.
    """

    record = build_annotation_record_v22(note_id, note_text, ui)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")
