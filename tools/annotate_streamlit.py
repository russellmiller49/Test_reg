#!/usr/bin/env python3
"""Streamlit annotation interface for bronchoscopy notes (schema v2.1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.ui_helpers import tri_state  # noqa: E402
from tools.writer import save_annotation_v21  # noqa: E402

ANNOTATION_PATH = Path("eval/data/gold_corpus_v2_1.jsonl")
NOTES_DIR = Path("data/synthetic_notes")

SEDATION_OPTIONS = ["moderate", "deep", "general", "MAC", "local_topical"]
REVERSAL_OPTIONS = ["flumazenil", "naloxone"]
SEDATION_EVENT_OPTIONS = ["hypoxia", "prolonged sedation", "hypotension", "bradycardia", "reversal_given"]

ROSE_OPTIONS = [
    "positive_malignant",
    "benign",
    "atypical",
    "adequate_only",
    "insufficient",
    "granulomatous",
]
PET_OPTIONS = ["positive", "negative", "not_available"]
RADIAL_PATTERN_OPTIONS = ["concentric", "eccentric", "not_seen"]
PROCEDURE_TYPES = [
    "EBUS_TBNA",
    "EMN",
    "Robotic",
    "Cryobiopsy",
    "Endobronchial_biopsy",
    "BAL",
    "Fiducial",
    "Therapeutic",
    "Teaching",
    "Other",
]
DOCUMENT_TYPES = [
    "procedure_note",
    "progress_note",
    "telephone_note",
    "teaching_note",
    "safety_checklist",
    "registry_form",
]


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def record_status(
    store: Dict[str, str],
    detail_store: Dict[str, str],
    path: str,
    status: str,
    detail: str = "",
) -> None:
    store[path] = status
    if detail:
        detail_store[path] = detail
    else:
        detail_store.pop(path, None)


def compute_sedation_confidence(
    sedation_used: Optional[bool],
    sedation_mode: Optional[str],
    meds: List[Dict[str, Optional[str]]],
    ramsay: Optional[float],
) -> Optional[float]:
    if sedation_used is not True:
        return None
    score = 0.6
    if sedation_mode:
        score = 0.75
    if meds:
        score = max(score, 0.82)
    if ramsay is not None:
        score = max(score, 0.9)
    return round(score, 2)


def load_annotated_ids() -> set[str]:
    if not ANNOTATION_PATH.exists():
        return set()

    annotated: set[str] = set()
    with ANNOTATION_PATH.open(encoding="utf-8") as handle:
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
    return annotated


def capture_quality_flag(
    label: str,
    key: str,
    metric_key: str,
    field_status: Dict[str, str],
    field_status_detail: Dict[str, str],
) -> Tuple[Optional[bool], str]:
    value, status, detail = tri_state(label, key)
    record_status(field_status, field_status_detail, f"quality.{metric_key}", status, detail)
    return value, status


def collect_quality_metrics(
    key_prefix: str,
    ui: Dict[str, Any],
) -> Dict[str, Optional[bool]]:
    quality = ui["quality_metrics"]
    field_status = ui["field_status"]
    field_status_detail = ui["field_status_detail"]

    quality_flags: Dict[str, Optional[bool]] = {}

    quality_flags["staging_indication"], _ = capture_quality_flag(
        "Staging indication documented?", f"{key_prefix}_quality_staging", "staging_indication", field_status, field_status_detail
    )
    quality["staging_indication"] = quality_flags["staging_indication"]

    quality_flags["systematic"], _ = capture_quality_flag(
        "Systematic N3→N2→N1 sequence documented?",
        f"{key_prefix}_quality_systematic",
        "systematic_n3_n2_n1",
        field_status,
        field_status_detail,
    )
    quality["systematic_n3_n2_n1"] = quality_flags["systematic"]

    quality_flags["photodoc"], _ = capture_quality_flag(
        "Photodocumentation of all stations?",
        f"{key_prefix}_quality_photodoc",
        "photodocumentation_all_stations",
        field_status,
        field_status_detail,
    )
    quality["photodocumentation_all_stations"] = quality_flags["photodoc"]

    rose_value, _ = capture_quality_flag(
        "ROSE used?",
        f"{key_prefix}_quality_rose",
        "rose_available",
        field_status,
        field_status_detail,
    )
    quality["rose_available"] = rose_value
    quality_flags["rose"] = rose_value

    pet_value, _ = capture_quality_flag(
        "PET referenced for sampled nodes?",
        f"{key_prefix}_quality_pet",
        "pet_documented",
        field_status,
        field_status_detail,
    )
    quality["pet_documented"] = pet_value
    quality_flags["pet"] = pet_value

    radial_value, _ = capture_quality_flag(
        "Radial EBUS performed?",
        f"{key_prefix}_quality_radial",
        "radial_ebus_performed",
        field_status,
        field_status_detail,
    )
    quality["radial_ebus_performed"] = radial_value
    quality_flags["radial"] = radial_value

    tool_value, _ = capture_quality_flag(
        "Tool-in-lesion assessed?",
        f"{key_prefix}_quality_tool",
        "tool_in_lesion_assessed",
        field_status,
        field_status_detail,
    )
    quality["tool_in_lesion_assessed"] = tool_value
    quality_flags["tool_assessed"] = tool_value

    fluoro_value, _ = capture_quality_flag(
        "Fluoroscopy used?",
        f"{key_prefix}_quality_fluoro",
        "fluoroscopy_used",
        field_status,
        field_status_detail,
    )
    quality["fluoroscopy_used"] = fluoro_value
    quality_flags["fluoro"] = fluoro_value

    dap_value, _ = capture_quality_flag(
        "Dose area product recorded?",
        f"{key_prefix}_quality_dap",
        "dap_recorded",
        field_status,
        field_status_detail,
    )
    quality["dap_recorded"] = dap_value
    quality_flags["dap"] = dap_value

    cbct_value, _ = capture_quality_flag(
        "CBCT used?",
        f"{key_prefix}_quality_cbct",
        "cbct_used",
        field_status,
        field_status_detail,
    )
    quality["cbct_used"] = cbct_value
    quality_flags["cbct"] = cbct_value

    protocol_input = st.text_input("Protocol adherence (0-1)", key=f"{key_prefix}_quality_protocol")
    quality["protocol_adherence"] = parse_float(protocol_input)

    return quality_flags


def render_sedation_section(
    key_prefix: str,
    ui: Dict[str, Any],
) -> Dict[str, Any]:
    field_status = ui["field_status"]
    detail = ui["field_status_detail"]

    sedation_used, sedation_status, sedation_detail = tri_state(
        "Sedation administered?", key=f"{key_prefix}_sedation_used"
    )
    record_status(field_status, detail, "anesthesia_sedation.type", sedation_status, sedation_detail)
    ui["sedation_used_value"] = sedation_used

    sedation_mode: Optional[str] = None
    ramsay_value: Optional[float] = None
    monitoring_minutes: Optional[int] = None
    reversal_agents: List[str] = []
    spo2_value: Optional[bool] = None
    sedation_events: List[str] = []
    sedation_meds: List[Dict[str, Optional[str]]] = []

    if sedation_used is True:
        sedation_mode = st.selectbox(
            "Sedation type",
            SEDATION_OPTIONS,
            key=f"{key_prefix}_sedation_type",
        )
        record_status(field_status, detail, "anesthesia_sedation.type", "present")

        ramsay_input = st.text_input("Ramsay max", key=f"{key_prefix}_sedation_ramsay").strip()
        ramsay_value = parse_float(ramsay_input)
        status = "present" if ramsay_value is not None else "not_documented"
        record_status(field_status, detail, "anesthesia_sedation.ramsay_max", status)

        monitor_val, monitor_status, monitor_detail = tri_state(
            "BP monitoring interval documented?",
            key=f"{key_prefix}_sedation_monitoring",
        )
        if monitor_val is True:
            monitor_input = st.text_input(
                "BP monitoring interval (minutes)",
                key=f"{key_prefix}_sedation_monitor_value",
            ).strip()
            monitoring_minutes = parse_int(monitor_input)
            monitor_status = "present" if monitoring_minutes is not None else "not_documented"
            monitor_detail = ""
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.monitoring_bp_interval_min",
            monitor_status,
            monitor_detail,
        )

        reversal_val, reversal_status, reversal_detail = tri_state(
            "Reversal agents used?",
            key=f"{key_prefix}_sedation_reversal",
        )
        if reversal_val is True:
            reversal_agents = st.multiselect(
                "Reversal agents",
                REVERSAL_OPTIONS,
                key=f"{key_prefix}_sedation_reversal_agents",
            )
            reversal_status = "present" if reversal_agents else "not_documented"
            reversal_detail = "" if reversal_agents else "unspecified"
        record_status(field_status, detail, "anesthesia_sedation.reversal_agents", reversal_status, reversal_detail)

        spo2_val, spo2_status, spo2_detail = tri_state(
            "Continuous SpO₂ monitoring?",
            key=f"{key_prefix}_sedation_spo2",
        )
        spo2_value = spo2_val
        record_status(field_status, detail, "anesthesia_sedation.continuous_spo2", spo2_status, spo2_detail)

        sedation_events_common = st.multiselect(
            "Sedation events (select)",
            SEDATION_EVENT_OPTIONS,
            key=f"{key_prefix}_sedation_events",
        )
        sedation_events_extra = st.text_input(
            "Additional sedation events (comma separated)",
            key=f"{key_prefix}_sedation_events_extra",
        )
        sedation_events = sedation_events_common + [
            item.strip() for item in sedation_events_extra.split(",") if item.strip()
        ]

        meds_count = st.number_input(
            "Number of sedation medications",
            min_value=0,
            max_value=12,
            value=0,
            step=1,
            key=f"{key_prefix}_sedation_med_count",
        )
        for idx in range(int(meds_count)):
            st.markdown(f"**Medication {idx + 1}**")
            med_name = st.text_input("Name", key=f"{key_prefix}_sed_med_name_{idx}")
            med_dose = parse_float(st.text_input("Dose value", key=f"{key_prefix}_sed_med_dose_{idx}"))
            med_unit = st.text_input("Dose unit", key=f"{key_prefix}_sed_med_unit_{idx}")
            med_route = st.text_input("Route", key=f"{key_prefix}_sed_med_route_{idx}")
            med_timing = st.text_input("Timing note", key=f"{key_prefix}_sed_med_timing_{idx}")
            if med_name:
                sedation_meds.append(
                    {
                        "name": med_name,
                        "dose_value": med_dose,
                        "dose_unit": med_unit or None,
                        "route": med_route or None,
                        "timing_note": med_timing or None,
                    }
                )
    else:
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.ramsay_max",
            sedation_status,
            sedation_detail,
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.monitoring_bp_interval_min",
            sedation_status,
            sedation_detail,
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.reversal_agents",
            sedation_status,
            sedation_detail,
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.continuous_spo2",
            sedation_status,
            sedation_detail,
        )

    sedation_confidence = compute_sedation_confidence(sedation_used, sedation_mode, sedation_meds, ramsay_value)

    return {
        "sedation_mode": sedation_mode,
        "ramsay_max": ramsay_value,
        "monitoring_interval": monitoring_minutes,
        "reversal_agents": reversal_agents,
        "spo2_continuous": spo2_value,
        "sedation_events": sedation_events,
        "sedation_meds": sedation_meds,
        "sedation_confidence": sedation_confidence,
    }


def render_ebus_section(
    key_prefix: str,
    ui: Dict[str, Any],
    rose_value: Optional[bool],
    pet_value: Optional[bool],
) -> List[Dict[str, Any]]:
    field_status = ui["field_status"]
    detail = ui["field_status_detail"]

    nodes: List[Dict[str, Any]] = []
    count = st.number_input(
        "Number of EBUS stations",
        min_value=0,
        max_value=20,
        value=0,
        step=1,
        key=f"{key_prefix}_ebus_count",
    )

    for idx in range(int(count)):
        st.markdown(f"**Station {idx + 1}**")
        station = st.text_input("Station code", key=f"{key_prefix}_ebus_station_{idx}").strip()

        size_input = st.text_input("Short-axis size (mm)", key=f"{key_prefix}_ebus_size_{idx}").strip()
        size_value = parse_float(size_input)
        status = "present" if size_value is not None else "not_documented"
        record_status(field_status, detail, f"ebus.stations[{idx}].short_axis_mm", status)

        passes_input = st.text_input("Number of passes", key=f"{key_prefix}_ebus_passes_{idx}").strip()
        passes_value = parse_int(passes_input)
        status = "present" if passes_value is not None else "not_documented"
        record_status(field_status, detail, f"ebus.stations[{idx}].passes", status)

        if rose_value is True:
            rose_result = st.selectbox(
                "ROSE result",
                ROSE_OPTIONS,
                key=f"{key_prefix}_ebus_rose_{idx}",
            )
            record_status(field_status, detail, f"ebus.stations[{idx}].rose", "present")
        elif rose_value is False:
            rose_result = None
            record_status(field_status, detail, f"ebus.stations[{idx}].rose", "explicit_no")
        else:
            rose_result = None
            record_status(field_status, detail, f"ebus.stations[{idx}].rose", "not_documented", "unsure")

        if pet_value is True:
            pet_status = st.selectbox(
                "PET status",
                PET_OPTIONS,
                key=f"{key_prefix}_ebus_pet_{idx}",
            )
            record_status(field_status, detail, f"ebus.stations[{idx}].pet_status", "present")
        elif pet_value is False:
            pet_status = None
            record_status(field_status, detail, f"ebus.stations[{idx}].pet_status", "explicit_no")
        else:
            pet_status = None
            record_status(field_status, detail, f"ebus.stations[{idx}].pet_status", "not_documented", "unsure")

        elastography = st.text_input("Elastography (optional)", key=f"{key_prefix}_ebus_elasto_{idx}").strip() or None
        final_path = st.text_area(
            "Final pathology hint (optional)",
            key=f"{key_prefix}_ebus_path_{idx}",
            height=80,
        ).strip() or None

        if station:
            nodes.append(
                {
                    "station": station,
                    "short_axis_mm": size_value,
                    "passes": passes_value,
                    "pet_status": pet_status,
                    "rose": rose_result,
                    "elastography": elastography,
                    "final_path_hint": final_path,
                }
            )

    return nodes


def render_peripheral_section(
    key_prefix: str,
    ui: Dict[str, Any],
    quality_flags: Dict[str, Optional[bool]],
) -> List[Dict[str, Any]]:
    field_status = ui["field_status"]
    detail = ui["field_status_detail"]

    targets: List[Dict[str, Any]] = []
    count = st.number_input(
        "Number of peripheral targets",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
        key=f"{key_prefix}_peripheral_count",
    )

    for idx in range(int(count)):
        st.markdown(f"**Target {idx + 1}**")
        lobe_segment = st.text_input("Target lobe/segment", key=f"{key_prefix}_peripheral_lobe_{idx}").strip() or None
        size_value = parse_int(
            st.text_input("Lesion size (mm)", key=f"{key_prefix}_peripheral_size_{idx}").strip()
        )

        bronchus_sign_choice = st.selectbox(
            "Bronchus sign present?",
            ["", "Yes", "No"],
            key=f"{key_prefix}_peripheral_bronchus_{idx}",
        )
        bronchus_sign = {"Yes": True, "No": False}.get(bronchus_sign_choice)

        if quality_flags.get("radial") is True:
            radial_pattern = st.selectbox(
                "Radial EBUS pattern",
                RADIAL_PATTERN_OPTIONS,
                key=f"{key_prefix}_peripheral_radial_{idx}",
            )
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].radial_pattern",
                "present",
            )
        elif quality_flags.get("radial") is False:
            radial_pattern = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].radial_pattern",
                "explicit_no",
            )
        else:
            radial_pattern = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].radial_pattern",
                "not_documented",
                "unsure",
            )

        if quality_flags.get("tool_assessed") is True:
            tool_choice = st.radio(
                "Tool in lesion confirmed?",
                ["Yes", "No"],
                horizontal=True,
                key=f"{key_prefix}_peripheral_tool_{idx}",
            )
            tool_in_lesion = tool_choice == "Yes"
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].tool_in_lesion_confirmed",
                "present",
            )
        elif quality_flags.get("tool_assessed") is False:
            tool_in_lesion = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].tool_in_lesion_confirmed",
                "explicit_no",
            )
        else:
            tool_in_lesion = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].tool_in_lesion_confirmed",
                "not_documented",
                "unsure",
            )

        if quality_flags.get("fluoro") is True:
            fluoro_time = parse_float(
                st.text_input("Fluoroscopy time (min)", key=f"{key_prefix}_peripheral_fluoro_{idx}").strip()
            )
            status = "present" if fluoro_time is not None else "not_documented"
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].fluoro_time_min",
                status,
            )
        elif quality_flags.get("fluoro") is False:
            fluoro_time = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].fluoro_time_min",
                "explicit_no",
            )
        else:
            fluoro_time = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].fluoro_time_min",
                "not_documented",
                "unsure",
            )

        if quality_flags.get("dap") is True:
            dap_value = parse_float(
                st.text_input("Dose area product (cGy*cm²)", key=f"{key_prefix}_peripheral_dap_{idx}").strip()
            )
            status = "present" if dap_value is not None else "not_documented"
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].dap_cgy_cm2",
                status,
            )
        elif quality_flags.get("dap") is False:
            dap_value = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].dap_cgy_cm2",
                "explicit_no",
            )
        else:
            dap_value = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].dap_cgy_cm2",
                "not_documented",
                "unsure",
            )

        if quality_flags.get("cbct") is True:
            cbct_choice = st.radio(
                "CBCT used?",
                ["Yes", "No"],
                horizontal=True,
                key=f"{key_prefix}_peripheral_cbct_{idx}",
            )
            cbct_used = cbct_choice == "Yes"
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].cbct_used",
                "present",
            )
        elif quality_flags.get("cbct") is False:
            cbct_used = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].cbct_used",
                "explicit_no",
            )
        else:
            cbct_used = None
            record_status(
                field_status,
                detail,
                f"peripheral.targets[{idx}].cbct_used",
                "not_documented",
                "unsure",
            )

        samples: Dict[str, int] = {}
        st.markdown("**Sampling counts**")
        for sample_key in ["needle_aspirate", "forceps_biopsy", "brush", "cryo", "BAL"]:
            count_value = st.number_input(
                sample_key.replace("_", " ").title(),
                min_value=0,
                max_value=25,
                value=0,
                step=1,
                key=f"{key_prefix}_peripheral_sample_{sample_key}_{idx}",
            )
            if count_value:
                samples[sample_key] = int(count_value)

        final_path = st.text_area(
            "Final pathology hint (optional)",
            key=f"{key_prefix}_peripheral_path_{idx}",
            height=80,
        ).strip() or None

        if lobe_segment or samples or size_value is not None:
            targets.append(
                {
                    "lobe_segment": lobe_segment,
                    "size_mm": size_value,
                    "bronchus_sign": bronchus_sign,
                    "tool_in_lesion_confirmed": tool_in_lesion,
                    "radial_pattern": radial_pattern,
                    "cbct_used": cbct_used,
                    "fluoro_time_min": fluoro_time,
                    "dap_cgy_cm2": dap_value,
                    "samples": samples,
                    "final_path_hint": final_path,
                }
            )

    return targets


def render_specimen_section(key_prefix: str) -> Dict[str, bool]:
    st.markdown("**Specimen routing**")
    return {
        "cytology": st.checkbox("Cytology", key=f"{key_prefix}_specimen_cytology"),
        "cell_block": st.checkbox("Cell block", key=f"{key_prefix}_specimen_cell_block"),
        "histology": st.checkbox("Histology", key=f"{key_prefix}_specimen_histology"),
        "flow_cytometry": st.checkbox("Flow cytometry", key=f"{key_prefix}_specimen_flow"),
        "microbiology_afb_fungal_bacterial": st.checkbox(
            "Microbiology (AFB/Fungal/Bacterial)",
            key=f"{key_prefix}_specimen_micro",
        ),
        "molecular_ngs_pdl1_requested": st.checkbox(
            "Molecular / NGS / PD-L1",
            key=f"{key_prefix}_specimen_molecular",
        ),
    }


def render_complications_section(key_prefix: str) -> List[Dict[str, Optional[str]]]:
    complications: List[Dict[str, Optional[str]]] = []
    no_complications = st.checkbox("No complications", key=f"{key_prefix}_comp_none")
    if no_complications:
        return [{"type": "none", "severity": None, "details": None}]

    count = st.number_input(
        "Number of complications",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
        key=f"{key_prefix}_comp_count",
    )
    for idx in range(int(count)):
        st.markdown(f"**Complication {idx + 1}**")
        comp_type = st.selectbox(
            "Type",
            ["bleeding", "pneumothorax", "hypoxia", "other"],
            key=f"{key_prefix}_comp_type_{idx}",
        )
        severity_choice = st.selectbox(
            "Severity",
            ["", "mild", "moderate", "severe"],
            key=f"{key_prefix}_comp_severity_{idx}",
        )
        details = st.text_area("Details", key=f"{key_prefix}_comp_details_{idx}", height=80).strip() or None
        complications.append(
            {
                "type": comp_type,
                "severity": severity_choice or None,
                "details": details,
            }
        )
    return complications


def render_inferred_flags_section(key_prefix: str) -> Dict[str, Optional[Any]]:
    inferred: Dict[str, Optional[Any]] = {}
    inferred["n_category"] = st.selectbox(
        "N category",
        ["", "N0", "N1", "N2", "N3", "unknown"],
        key=f"{key_prefix}_inferred_n",
    ) or None
    inferred["bilateral_or_contralateral_nodes"] = {
        "Yes": True,
        "No": False,
    }.get(
        st.selectbox(
            "Bilateral / contralateral nodes?",
            ["", "Yes", "No"],
            key=f"{key_prefix}_inferred_bilateral",
        )
    )
    inferred["lymphoma_pattern_suspected"] = {
        "Yes": True,
        "No": False,
    }.get(
        st.selectbox(
            "Lymphoma pattern suspected?",
            ["", "Yes", "No"],
            key=f"{key_prefix}_inferred_lymphoma",
        )
    )
    inferred["sarcoid_pattern_suspected"] = {
        "Yes": True,
        "No": False,
    }.get(
        st.selectbox(
            "Sarcoid pattern suspected?",
            ["", "Yes", "No"],
            key=f"{key_prefix}_inferred_sarcoid",
        )
    )
    inferred["adequate_for_molecular"] = {
        "Yes": True,
        "No": False,
    }.get(
        st.selectbox(
            "Adequate for molecular testing?",
            ["", "Yes", "No"],
            key=f"{key_prefix}_inferred_molecular",
        )
    )
    return inferred


def validate_before_save(
    ui: Dict[str, Any],
    quality_flags: Dict[str, Optional[bool]],
) -> List[str]:
    errors: List[str] = []

    if ui.get("sedation_used_value") is True and not ui.get("sedation_mode"):
        errors.append("Sedation type is required when sedation is documented.")

    if ui.get("sedation_used_value") is True:
        monitoring_status = ui["field_status"].get("anesthesia_sedation.monitoring_bp_interval_min")
        if monitoring_status == "present" and ui.get("monitoring_interval") is None:
            errors.append("Monitoring interval is required when marked as documented.")

    if quality_flags.get("fluoro") is True:
        if not any(target.get("fluoro_time_min") is not None for target in ui.get("peripheral_targets", [])):
            errors.append("Fluoroscopy time is required when fluoroscopy is marked as used.")

    if quality_flags.get("dap") is True:
        if not any(target.get("dap_cgy_cm2") is not None for target in ui.get("peripheral_targets", [])):
            errors.append("DAP value is required when DAP is marked as recorded.")

    return errors


def main() -> None:
    st.set_page_config(page_title="Bronch Annotator v2.1", layout="wide")
    st.title("📝 Bronchoscopy Note Annotation (v2.1)")

    note_files = sorted(NOTES_DIR.glob("*.txt"))
    if not note_files:
        st.error("No notes found. Generate synthetic notes first.")
        return

    annotated_ids = load_annotated_ids()
    remaining_files = [path for path in note_files if path.stem not in annotated_ids]

    st.sidebar.header("📈 Progress")
    st.sidebar.metric("Total Notes", len(note_files))
    st.sidebar.metric("Annotated", len(annotated_ids))
    st.sidebar.metric("Remaining", len(remaining_files))

    if not remaining_files:
        st.success("🎉 All notes have been annotated!")
        return

    selected_file = st.sidebar.selectbox(
        "Select Note to Annotate",
        remaining_files,
        format_func=lambda path: f"{path.name} ({'✅' if path.stem in annotated_ids else '⏳'})",
    )

    note_text = selected_file.read_text(encoding="utf-8")
    key_prefix = selected_file.stem

    st.markdown(
        """
        <style>
            .annotation-columns > div[data-testid="stHorizontalBlock"] {
                align-items: flex-start;
            }
            .annotation-columns div[data-testid="column"] {
                overflow: visible !important;
            }
            .annotation-notes {
                position: sticky;
                top: 1.5rem;
                padding-right: 1rem;
            }
            .annotation-notes textarea {
                resize: none;
            }
            .annotation-notes-body {
                max-height: calc(100vh - 4rem);
                overflow-y: auto;
                padding-right: 0.5rem;
            }
            .annotation-form {
                max-height: calc(100vh - 4rem);
                overflow-y: auto;
                padding-right: 0.5rem;
                padding-bottom: 2rem;
            }
            .annotation-form .stButton > button {
                width: 100%;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='annotation-columns'>", unsafe_allow_html=True)
    note_col, form_col = st.columns([1, 2], gap="large")

    with note_col:
        st.markdown("<div class='annotation-notes'><div class='annotation-notes-body'>", unsafe_allow_html=True)
        st.subheader(f"Note: {selected_file.name}")
        st.text_area(
            "Procedure Note",
            note_text,
            height=720,
            key=f"{key_prefix}_note_view",
        )
        st.markdown("</div></div>", unsafe_allow_html=True)

    with form_col:
        st.markdown("<div class='annotation-form'>", unsafe_allow_html=True)
        st.header("📊 Annotate Fields")

        ui: Dict[str, Any] = {
            "quality_metrics": {},
            "field_status": {},
            "field_status_detail": {},
        }

        with st.expander("Patient & Procedure Info", expanded=True):
            ui["patient_name"] = st.text_input("Patient Name", key=f"{key_prefix}_patient_name") or None
            ui["mrn"] = st.text_input("MRN", key=f"{key_prefix}_mrn") or None
            ui["dob"] = st.text_input("Date of Birth (YYYY-MM-DD)", key=f"{key_prefix}_dob") or None
            ui["procedure_date"] = st.text_input("Procedure Date (YYYY-MM-DD)", key=f"{key_prefix}_proc_date") or None
            ui["indication_text"] = st.text_area(
                "Indication / History",
                key=f"{key_prefix}_indication",
                height=120,
            ) or None
            ui["procedure_components"] = st.multiselect(
                "Procedure Types",
                PROCEDURE_TYPES,
                key=f"{key_prefix}_procedure_types",
            )
            ui["document_type"] = st.selectbox(
                "Document Type",
                DOCUMENT_TYPES,
                key=f"{key_prefix}_document_type",
            )

        with st.expander("Quality & Workflow Flags", expanded=True):
            quality_flags = collect_quality_metrics(key_prefix, ui)

        with st.expander("Sedation", expanded=True):
            sedation_data = render_sedation_section(key_prefix, ui)
            ui.update(sedation_data)

        with st.expander("EBUS Node Sampling", expanded=True):
            ui["ebus_nodes"] = render_ebus_section(key_prefix, ui, quality_flags.get("rose"), quality_flags.get("pet"))

        with st.expander("Peripheral / Navigation", expanded=False):
            ui["peripheral_targets"] = render_peripheral_section(key_prefix, ui, quality_flags)

        with st.expander("Specimen Routing", expanded=False):
            ui["specimens"] = render_specimen_section(key_prefix)

        with st.expander("Complications", expanded=False):
            ui["complications"] = render_complications_section(key_prefix)

        with st.expander("Inferred Flags", expanded=False):
            ui["inferred_flags"] = render_inferred_flags_section(key_prefix)

        with st.expander("Disposition & Plan", expanded=False):
            ui["disposition"] = st.text_input("Disposition", key=f"{key_prefix}_disposition") or None
            ui["plan_summary"] = st.text_area(
                "Plan summary / next steps",
                key=f"{key_prefix}_plan",
                height=120,
            ) or None

        errors = validate_before_save(ui, quality_flags)

        if st.button("💾 Save Annotation", key=f"{key_prefix}_save"):
            if errors:
                for issue in errors:
                    st.error(issue)
            else:
                save_annotation_v21(selected_file.stem, note_text, ui)
                st.success(f"✅ Saved {selected_file.stem} (schema v2.1)")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
