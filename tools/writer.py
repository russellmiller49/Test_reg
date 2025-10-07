"""Persistence helpers for v2.1 gold corpus records."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List

from bronch_schema import (
    Complication,
    GoldRecord,
    MedicationDose,
    NodeSampling,
    PeripheralTarget,
    Procedure,
    Sedation,
    SpecimenRouting,
)

OUT_PATH = Path("eval/data/gold_corpus_v2_1.jsonl")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_medications(raw_meds: List[Dict[str, Any]]) -> List[MedicationDose]:
    meds: List[MedicationDose] = []
    for entry in raw_meds:
        if not entry.get("name"):
            continue
        meds.append(MedicationDose(**entry))
    return meds


def _build_complications(raw: List[Dict[str, Any]]) -> List[Complication]:
    if not raw:
        return []
    comps: List[Complication] = []
    for item in raw:
        comps.append(Complication(**item))
    return comps


def save_annotation_v21(note_id: str, note_text: str, ui: Dict[str, Any]) -> None:
    """
    Persist a v2.1 annotation record.

    The `ui` dict captures raw Streamlit inputs including field_status tracking.
    """

    sedation_block: Sedation
    if ui.get("sedation_used_value") is True:
        sedation_block = Sedation(
            sedation_type=ui.get("sedation_mode"),
            meds=_build_medications(ui.get("sedation_meds", [])),
            ramsay_max=ui.get("ramsay_max"),
            monitoring_bp_interval_min=ui.get("monitoring_interval"),
            continuous_spo2=ui.get("spo2_continuous"),
            reversal_agents=ui.get("reversal_agents", []),
            events=ui.get("sedation_events", []),
            confidence=ui.get("sedation_confidence"),
        )
    else:
        sedation_block = Sedation()

    ebus_nodes = [NodeSampling(**node) for node in ui.get("ebus_nodes", [])]
    peripheral_targets = [PeripheralTarget(**target) for target in ui.get("peripheral_targets", [])]
    peripheral = {"targets": peripheral_targets} if peripheral_targets else None

    procedure = Procedure(
        patient_name=ui.get("patient_name"),
        mrn=ui.get("mrn"),
        dob=ui.get("dob"),
        procedure_date=ui.get("procedure_date"),
        indication=ui.get("indication_text"),
        procedure_types=ui.get("procedure_components", []),
        sedation=sedation_block,
        ebus_nodes=ebus_nodes,
        peripheral=peripheral,
        specimens=SpecimenRouting(**ui.get("specimens", {})),
        complications=_build_complications(ui.get("complications", [])),
        quality=ui.get("quality_metrics", {}),
        inferred=ui.get("inferred_flags", {}),
        disposition=ui.get("disposition"),
        plan_summary=ui.get("plan_summary"),
        raw_text_hash=sha256(note_text),
        document_type=ui.get("document_type", "procedure_note"),
    )

    record = GoldRecord(
        id=note_id,
        note_text=note_text,
        procedure=procedure,
        field_status=ui.get("field_status", {}),
        field_status_detail=ui.get("field_status_detail", {}),
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json(ensure_ascii=False) + "\n")
