#!/usr/bin/env python3
"""Streamlit annotation interface for bronchoscopy notes (schema v2.2)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from pydantic import ValidationError

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.annotation_backend import (  # noqa: E402
    AnnotationBackendError,
    resolve_backend,
)
from tools.ui_helpers import tri_state, tri_state_choice  # noqa: E402

ANNOTATION_PATH = Path("eval/data/gold_corpus_v2_2.jsonl")
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
PROCEDURE_CATEGORY_OPTIONS = [
    "EBUS",
    "Navigational",
    "Robotic",
    "Therapeutic",
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


def render_hemostasis_block(prefix: str) -> Dict[str, Any]:
    epi = parse_float(st.text_input("Epinephrine (mL, 1:10,000)", key=f"{prefix}_hemo_epi").strip())
    txa = parse_float(st.text_input("Tranexamic acid (mg)", key=f"{prefix}_hemo_txa").strip())
    saline = parse_float(st.text_input("Iced saline (mL)", key=f"{prefix}_hemo_saline").strip())
    agents = st.multiselect("Other agents", ["surgicel", "floseal", "other"], key=f"{prefix}_hemo_agents")
    hemo_choice = st.radio(
        "Hemostasis achieved?",
        ["Yes", "No", "Unsure"],
        horizontal=True,
        key=f"{prefix}_hemo_status",
    )
    hemo_value, _, _ = tri_state_choice(hemo_choice)
    hemo_time = parse_float(st.text_input("Time to hemostasis (min)", key=f"{prefix}_hemo_time").strip())
    return {
        "epi_ml_1_10000": epi,
        "txa_topical_mg": txa,
        "iced_saline_ml": saline,
        "agents": agents,
        "hemostasis_achieved": hemo_value,
        "time_to_hemostasis_min": hemo_time,
    }


def compute_sedation_confidence(
    sedation_used: Optional[bool],
    sedation_block: Dict[str, Any],
) -> Optional[float]:
    if sedation_used is not True:
        return None
    score = 0.6
    if sedation_block.get("sedation_type"):
        score = max(score, 0.75)
    if sedation_block.get("meds"):
        score = max(score, 0.82)
    if sedation_block.get("ramsay_max") is not None:
        score = max(score, 0.9)
    if sedation_block.get("monitoring_bp_interval_min") is not None:
        score = max(score, 0.92)
    return round(score, 2)


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
    category: str,
) -> Dict[str, Optional[bool]]:
    quality = ui["quality_metrics"]
    field_status = ui["field_status"]
    field_status_detail = ui["field_status_detail"]

    quality_flags: Dict[str, Optional[bool]] = {}

    def set_flag(label: str, form_key: str, metric_key: str) -> Optional[bool]:
        value, _ = capture_quality_flag(label, form_key, metric_key, field_status, field_status_detail)
        quality[metric_key] = value
        return value

    if category == "EBUS":
        staging_value = set_flag(
            "Staging indication documented?",
            f"{key_prefix}_quality_staging",
            "staging_indication",
        )
        systematic_value = set_flag(
            "Systematic N3→N2→N1 sequence documented?",
            f"{key_prefix}_quality_systematic",
            "systematic_n3_n2_n1",
        )
        photodoc_value = set_flag(
            "Photodocumentation of all stations?",
            f"{key_prefix}_quality_photodoc",
            "photodocumentation_all_stations",
        )

        rose_value = set_flag(
            "ROSE used?",
            f"{key_prefix}_quality_rose",
            "rose_available",
        )
        pet_value = set_flag(
            "PET referenced for sampled nodes?",
            f"{key_prefix}_quality_pet",
            "pet_documented",
        )

        quality_flags.update(
            {
                "staging_indication": staging_value,
                "systematic": systematic_value,
                "photodoc": photodoc_value,
                "rose": rose_value,
                "pet": pet_value,
            }
        )

    if category in {"Navigational", "Robotic"}:
        radial_value = set_flag(
            "Radial EBUS performed?",
            f"{key_prefix}_quality_radial",
            "radial_ebus_performed",
        )
        tool_value = set_flag(
            "Tool-in-lesion assessed?",
            f"{key_prefix}_quality_tool",
            "tool_in_lesion_assessed",
        )
        fluoro_value = set_flag(
            "Fluoroscopy used?",
            f"{key_prefix}_quality_fluoro",
            "fluoroscopy_used",
        )
        dap_value = set_flag(
            "Dose area product recorded?",
            f"{key_prefix}_quality_dap",
            "dap_recorded",
        )
        cbct_value = set_flag(
            "CBCT used?",
            f"{key_prefix}_quality_cbct",
            "cbct_used",
        )

        quality_flags.update(
            {
                "radial": radial_value,
                "tool_assessed": tool_value,
                "fluoro": fluoro_value,
                "dap": dap_value,
                "cbct": cbct_value,
            }
        )

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
    record_status(field_status, detail, "anesthesia_sedation.used", sedation_status, sedation_detail)
    ui["sedation_used_value"] = sedation_used

    sedation: Dict[str, Any] = {}
    monitoring_minutes: Optional[int] = None
    sedation_events: List[str] = []
    sedation_meds: List[Dict[str, Optional[str]]] = []

    if sedation_used is True:
        sedation_mode = st.selectbox(
            "Sedation type",
            [""] + SEDATION_OPTIONS,
            key=f"{key_prefix}_sedation_type",
        )
        sedation_mode = sedation_mode or None
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.type",
            "present" if sedation_mode else "not_documented",
            "" if sedation_mode else "unspecified",
        )
        if sedation_mode:
            sedation["sedation_type"] = sedation_mode

        asa_class = st.selectbox(
            "ASA class",
            ["", "I", "II", "III", "IV"],
            key=f"{key_prefix}_sedation_asa",
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.asa_class",
            "present" if asa_class else "not_documented",
            "" if asa_class else "unspecified",
        )
        if asa_class:
            sedation["asa_class"] = asa_class

        ecg_val, ecg_status, ecg_detail = tri_state(
            "Continuous ECG monitoring?",
            key=f"{key_prefix}_sedation_ecg",
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.ecg_monitoring",
            ecg_status,
            ecg_detail,
        )
        sedation["ecg_monitoring"] = ecg_val

        cap_val, cap_status, cap_detail = tri_state(
            "Capnography monitoring?",
            key=f"{key_prefix}_sedation_capnography",
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.capnography",
            cap_status,
            cap_detail,
        )
        sedation["capnography"] = cap_val

        reversal_stock_val, reversal_stock_status, reversal_stock_detail = tri_state(
            "Reversal agents available at bedside?",
            key=f"{key_prefix}_sedation_reversal_available_flag",
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.reversal_available",
            reversal_stock_status,
            reversal_stock_detail,
        )
        if reversal_stock_val is True:
            available_agents = st.multiselect(
                "Reversal agents available",
                REVERSAL_OPTIONS,
                key=f"{key_prefix}_sedation_reversal_available",
            )
            sedation["reversal_available"] = available_agents
        elif reversal_stock_val is False:
            sedation["reversal_available"] = []
        else:
            sedation["reversal_available"] = []

        reversal_given_val, reversal_given_status, reversal_given_detail = tri_state(
            "Reversal agents administered?",
            key=f"{key_prefix}_sedation_reversal_given_flag",
        )
        if reversal_given_val is True:
            reversal_given_list = st.multiselect(
                "Reversal agents administered",
                REVERSAL_OPTIONS,
                key=f"{key_prefix}_sedation_reversal_given",
            )
            reversal_given_status = "present" if reversal_given_list else "not_documented"
            reversal_given_detail = "" if reversal_given_list else "unspecified"
        else:
            reversal_given_list = []
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.reversal_given",
            reversal_given_status,
            reversal_given_detail,
        )
        sedation["reversal_given"] = reversal_given_list

        spo2_val, spo2_status, spo2_detail = tri_state(
            "Continuous SpO₂ monitoring?",
            key=f"{key_prefix}_sedation_spo2",
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.continuous_spo2",
            spo2_status,
            spo2_detail,
        )
        sedation["continuous_spo2"] = spo2_val

        st.markdown("**Oxygenation & Support**")
        o2_device = st.text_input(
            "Supplemental O₂ device",
            key=f"{key_prefix}_sedation_o2_device",
        ).strip()
        o2_device_value = o2_device or None
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.supplemental_o2.device",
            "present" if o2_device_value else "not_documented",
            "" if o2_device_value else "unspecified",
        )

        o2_flow = parse_float(
            st.text_input(
                "Supplemental O₂ flow (L/min)",
                key=f"{key_prefix}_sedation_o2_flow",
            ).strip()
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.supplemental_o2.flow_l_min",
            "present" if o2_flow is not None else "not_documented",
            "" if o2_flow is not None else "unspecified",
        )
        o2_fio2 = parse_float(
            st.text_input(
                "Supplemental O₂ FiO₂ (0-1)",
                key=f"{key_prefix}_sedation_o2_fio2",
            ).strip()
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.supplemental_o2.fio2",
            "present" if o2_fio2 is not None else "not_documented",
            "" if o2_fio2 is not None else "unspecified",
        )
        if o2_device_value or o2_flow is not None or o2_fio2 is not None:
            sedation["supplemental_o2"] = {
                "device": o2_device_value,
                "flow_l_min": o2_flow,
                "fio2": o2_fio2,
            }

        lowest_spo2 = parse_float(
            st.text_input(
                "Lowest SpO₂ (%)",
                key=f"{key_prefix}_sedation_lowest_spo2",
            ).strip()
        )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.lowest_spo2_percent",
            "present" if lowest_spo2 is not None else "not_documented",
            "" if lowest_spo2 is not None else "unspecified",
        )
        if lowest_spo2 is not None:
            sedation["lowest_spo2_percent"] = lowest_spo2

        st.markdown("**Sedation Timing**")
        sedation_start = st.text_input(
            "Sedation start time",
            key=f"{key_prefix}_sedation_start_time",
        ).strip()
        sedation_end = st.text_input(
            "Sedation end time",
            key=f"{key_prefix}_sedation_end_time",
        ).strip()
        sedation_duration = parse_float(
            st.text_input(
                "Sedation duration (minutes)",
                key=f"{key_prefix}_sedation_duration",
            ).strip()
        )
        for field_path, value, raw in [
            ("anesthesia_sedation.sedation_start_time", sedation_start or None, sedation_start),
            ("anesthesia_sedation.sedation_end_time", sedation_end or None, sedation_end),
        ]:
            record_status(
                field_status,
                detail,
                field_path,
                "present" if value else "not_documented",
                "" if value else "unspecified",
            )
        record_status(
            field_status,
            detail,
            "anesthesia_sedation.sedation_duration_min",
            "present" if sedation_duration is not None else "not_documented",
            "" if sedation_duration is not None else "unspecified",
        )
        if sedation_start:
            sedation["sedation_start_time"] = sedation_start
        if sedation_end:
            sedation["sedation_end_time"] = sedation_end
        if sedation_duration is not None:
            sedation["sedation_duration_min"] = sedation_duration

        ramsay_input = st.text_input("Ramsay max", key=f"{key_prefix}_sedation_ramsay").strip()
        ramsay_value = parse_float(ramsay_input)
        status = "present" if ramsay_value is not None else "not_documented"
        record_status(field_status, detail, "anesthesia_sedation.ramsay_max", status)
        if ramsay_value is not None:
            sedation["ramsay_max"] = ramsay_value

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
        if monitoring_minutes is not None:
            sedation["monitoring_bp_interval_min"] = monitoring_minutes

        if sedation_mode == "general":
            paralytics_val = st.radio(
                "Paralytics administered?",
                ["Yes", "No"],
                horizontal=True,
                index=1,
                key=f"{key_prefix}_sedation_paralytics",
            )
            paralytics_used = {"Yes": True, "No": False}.get(paralytics_val)
            record_status(
                field_status,
                detail,
                "anesthesia_sedation.paralytics_used",
                "present" if paralytics_used is not None else "not_documented",
            )
            sedation["paralytics_used"] = paralytics_used

            airway_device = (
                st.selectbox(
                    "Airway device for general anesthesia",
                    ["", "LMA", "ETT"],
                    key=f"{key_prefix}_sedation_airway_device",
                )
                or None
            )
            device_status = "present" if airway_device else "not_documented"
            device_detail = "" if airway_device else "unspecified"
            record_status(
                field_status,
                detail,
                "anesthesia_sedation.airway_device",
                device_status,
                device_detail,
            )
            if airway_device:
                sedation["airway_device"] = airway_device

            if airway_device == "ETT":
                ett_size = st.text_input(
                    "ETT size",
                    key=f"{key_prefix}_sedation_ett_size",
                ).strip()
                size_status = "present" if ett_size else "not_documented"
                size_detail = "" if ett_size else "unspecified"
                record_status(
                    field_status,
                    detail,
                    "anesthesia_sedation.airway_device_size",
                    size_status,
                    size_detail,
                )
                if ett_size:
                    sedation["airway_device_size"] = ett_size
            else:
                record_status(
                    field_status,
                    detail,
                    "anesthesia_sedation.airway_device_size",
                    "not_documented",
                    "not_applicable",
                )
        else:
            record_status(
                field_status,
                detail,
                "anesthesia_sedation.paralytics_used",
                "not_documented",
                "not_applicable",
            )
            record_status(
                field_status,
                detail,
                "anesthesia_sedation.airway_device",
                "not_documented",
                "not_applicable",
            )
            record_status(
                field_status,
                detail,
                "anesthesia_sedation.airway_device_size",
                "not_documented",
                "not_applicable",
            )

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
        if sedation_meds:
            sedation["meds"] = sedation_meds

        if sedation_events:
            sedation["events"] = sedation_events
    else:
        record_status(field_status, detail, "anesthesia_sedation.type", sedation_status, sedation_detail)
        for path in [
            "anesthesia_sedation.asa_class",
            "anesthesia_sedation.ecg_monitoring",
            "anesthesia_sedation.capnography",
            "anesthesia_sedation.reversal_available",
            "anesthesia_sedation.reversal_given",
            "anesthesia_sedation.continuous_spo2",
            "anesthesia_sedation.supplemental_o2.device",
            "anesthesia_sedation.supplemental_o2.flow_l_min",
            "anesthesia_sedation.supplemental_o2.fio2",
            "anesthesia_sedation.lowest_spo2_percent",
            "anesthesia_sedation.sedation_start_time",
            "anesthesia_sedation.sedation_end_time",
            "anesthesia_sedation.sedation_duration_min",
            "anesthesia_sedation.paralytics_used",
            "anesthesia_sedation.airway_device",
            "anesthesia_sedation.airway_device_size",
        ]:
            record_status(field_status, detail, path, sedation_status, sedation_detail)
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
        sedation["reversal_available"] = []
        sedation["reversal_given"] = []

    if sedation_used is True:
        sedation["confidence"] = compute_sedation_confidence(sedation_used, sedation)

    return {
        "sedation": sedation,
        "sedation_used_value": sedation_used,
    }


def render_ebus_section(
    key_prefix: str,
    ui: Dict[str, Any],
) -> List[Dict[str, Any]]:
    field_status = ui["field_status"]
    detail = ui["field_status_detail"]

    nodes: List[Dict[str, Any]] = []
    total_nodes = 0
    rose_documented = 0
    pet_documented = 0
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
        station_value = station or None
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].station",
            "present" if station_value else "not_documented",
            "" if station_value else "unspecified",
        )

        size_input = st.text_input("Short-axis size (mm)", key=f"{key_prefix}_ebus_size_{idx}").strip()
        size_value = parse_float(size_input)
        status = "present" if size_value is not None else "not_documented"
        record_status(field_status, detail, f"ebus.stations[{idx}].short_axis_mm", status)

        passes_input = st.text_input("Number of passes", key=f"{key_prefix}_ebus_passes_{idx}").strip()
        passes_value = parse_int(passes_input)
        status = "present" if passes_value is not None else "not_documented"
        record_status(field_status, detail, f"ebus.stations[{idx}].passes", status)

        needle_gauge = st.selectbox(
            "Needle gauge",
            ["", "22G", "25G", "other"],
            key=f"{key_prefix}_ebus_needle_{idx}",
        )
        needle_gauge_value = needle_gauge or None
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].needle_gauge",
            "present" if needle_gauge_value else "not_documented",
            "" if needle_gauge_value else "unspecified",
        )

        passes_molecular_input = st.text_input(
            "Passes reserved for molecular (optional)",
            key=f"{key_prefix}_ebus_molecular_passes_{idx}",
        ).strip()
        passes_molecular_value = parse_int(passes_molecular_input)
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].passes_for_molecular",
            "present" if passes_molecular_value is not None else "not_documented",
            "" if passes_molecular_value is not None else "unspecified",
        )

        molecular_tri, molecular_status, molecular_detail = tri_state(
            "Specimen from this station submitted for molecular testing?",
            key=f"{key_prefix}_ebus_molecular_flag_{idx}",
        )
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].molecular_from_station",
            molecular_status,
            molecular_detail,
        )

        rose_result = st.selectbox(
            "ROSE interpretation",
            [""] + ROSE_OPTIONS,
            key=f"{key_prefix}_ebus_rose_{idx}",
            help="benign = benign lymphocytes/negative for malignancy; adequate_only = adequate cellularity documented without cytologic interpretation.",
        )
        rose_value = rose_result or None
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].rose",
            "present" if rose_value else "not_documented",
            "" if rose_value else "unspecified",
        )

        pet_status_choice = st.selectbox(
            "PET status",
            [""] + PET_OPTIONS,
            key=f"{key_prefix}_ebus_pet_{idx}",
            help="not_available = PET not mentioned for this station (patient may still have a PET overall).",
        )
        pet_status = pet_status_choice or None
        record_status(
            field_status,
            detail,
            f"ebus.stations[{idx}].pet_status",
            "present" if pet_status else "not_documented",
            "" if pet_status else "unspecified",
        )

        if pet_status in {"positive", "negative"}:
            pet_suv = parse_float(
                st.text_input(
                    "PET SUV max (optional)",
                    key=f"{key_prefix}_ebus_pet_suv_{idx}",
                ).strip()
            )
            record_status(
                field_status,
                detail,
                f"ebus.stations[{idx}].pet_suv_max",
                "present" if pet_suv is not None else "not_documented",
                "" if pet_suv is not None else "unspecified",
            )
        else:
            pet_suv = None
            record_status(
                field_status,
                detail,
                f"ebus.stations[{idx}].pet_suv_max",
                "not_documented",
                "not_applicable",
            )

        elastography = st.text_input("Elastography (optional)", key=f"{key_prefix}_ebus_elasto_{idx}").strip() or None
        final_path = st.text_area(
            "Final pathology hint (optional)",
            key=f"{key_prefix}_ebus_path_{idx}",
            height=80,
        ).strip() or None

        if station_value or size_value is not None or passes_value is not None or rose_value or pet_status or elastography or final_path:
            total_nodes += 1
            if rose_value:
                rose_documented += 1
            if pet_status in {"positive", "negative"}:
                pet_documented += 1
            node_record: Dict[str, Any] = {
                "station": station_value,
                "short_axis_mm": size_value,
                "passes": passes_value,
                "pet_status": pet_status,
                "pet_suv_max": pet_suv,
                "rose": rose_value,
                "elastography": elastography,
                "final_path_hint": final_path,
                "needle_gauge": needle_gauge_value,
                "passes_for_molecular": passes_molecular_value,
            }
            if molecular_tri is not None:
                node_record["molecular_from_station"] = molecular_tri
            nodes.append(node_record)

    if total_nodes:
        st.caption(
            f"ROSE documented for {rose_documented}/{total_nodes} nodes • PET referenced for {pet_documented}/{total_nodes} nodes"
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


def render_therapeutic_section(
    key_prefix: str,
    ui: Dict[str, Any],
    quality_flags: Dict[str, Optional[bool]],
) -> Dict[str, Any]:
    field_status = ui["field_status"]
    detail = ui["field_status_detail"]
    quality = ui["quality_metrics"]

    therapeutic: Dict[str, Any] = {}

    fire_value, fire_status, fire_detail = tri_state(
        "Fire-risk mitigation documented (FiO₂ ≤ 0.40 during energy)?",
        key=f"{key_prefix}_quality_fire_risk",
    )
    quality["fire_risk_mitigation_documented"] = fire_value
    record_status(
        field_status,
        detail,
        "quality.fire_risk_mitigation_documented",
        fire_status,
        fire_detail,
    )
    quality_flags["fire_risk"] = fire_value

    airway_relief: List[Dict[str, Any]] = []
    airway_count = st.number_input(
        "Number of airway obstruction relief targets",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_airway_count",
    )
    for idx in range(int(airway_count)):
        st.markdown(f"**Airway target {idx + 1}**")
        site = st.selectbox(
            "Target site",
            ["", "trachea", "carina", "RMB", "LMB", "lobar", "segment"],
            key=f"{key_prefix}_ther_airway_site_{idx}",
        )
        segment_length = parse_float(
            st.text_input("Segment length (cm)", key=f"{key_prefix}_ther_airway_segment_{idx}").strip()
        )
        pre_pat = parse_float(
            st.text_input("Pre-intervention patency (%)", key=f"{key_prefix}_ther_airway_pre_{idx}").strip()
        )
        post_pat = parse_float(
            st.text_input("Post-intervention patency (%)", key=f"{key_prefix}_ther_airway_post_{idx}").strip()
        )
        modalities_selected = st.multiselect(
            "Modalities used",
            ["apc", "electrocautery", "laser", "cryo", "mechanical"],
            key=f"{key_prefix}_ther_airway_modalities_{idx}",
        )
        modalities: List[Dict[str, Any]] = []
        for modality in modalities_selected:
            with st.expander(f"{modality.upper()} parameters", expanded=False):
                mod_data: Dict[str, Any] = {"type": modality}
                if modality in {"apc", "electrocautery", "laser"}:
                    mod_data["power_w"] = parse_float(
                        st.text_input("Power (W)", key=f"{key_prefix}_{modality}_power_{idx}").strip()
                    )
                    mod_data["active_time_min"] = parse_float(
                        st.text_input("Active time (min)", key=f"{key_prefix}_{modality}_time_{idx}").strip()
                    )
                    mod_data["fio2_at_therapy"] = parse_float(
                        st.text_input("FiO₂ during therapy (0.21-1.0)", key=f"{key_prefix}_{modality}_fio2_{idx}").strip()
                    )
                    if modality == "apc":
                        mod_data["argon_flow_l_min"] = parse_float(
                            st.text_input("Argon flow (L/min)", key=f"{key_prefix}_apc_flow_{idx}").strip()
                        )
                        mod_data["mode"] = (
                            st.selectbox(
                                "APC mode",
                                ["", "continuous", "pulsed", "unknown"],
                                key=f"{key_prefix}_apc_mode_{idx}",
                            )
                            or None
                        )
                if modality == "cryo":
                    mod_data["cycles"] = parse_int(
                        st.text_input("Number of cycles", key=f"{key_prefix}_cryo_cycles_{idx}").strip()
                    )
                    mod_data["freeze_time_s"] = parse_float(
                        st.text_input("Freeze time (s)", key=f"{key_prefix}_cryo_freeze_{idx}").strip()
                    )
                    mod_data["thaw_time_s"] = parse_float(
                        st.text_input("Thaw time (s)", key=f"{key_prefix}_cryo_thaw_{idx}").strip()
                    )
                modalities.append({k: v for k, v in mod_data.items() if v not in (None, "", [])})

        with st.expander("Hemostasis measures", expanded=False):
            hemostasis = render_hemostasis_block(f"{key_prefix}_ther_airway_{idx}")

        if site:
            entry: Dict[str, Any] = {
                "site": site,
                "modalities": modalities,
                "hemostasis": hemostasis,
            }
            if segment_length is not None:
                entry["segment_length_cm"] = segment_length
            if pre_pat is not None:
                entry["pre_patency_percent"] = pre_pat
            if post_pat is not None:
                entry["post_patency_percent"] = post_pat
            airway_relief.append(entry)
    if airway_relief:
        therapeutic["airway_obstruction_relief"] = airway_relief

    balloon_dilations: List[Dict[str, Any]] = []
    balloon_count = st.number_input(
        "Number of balloon dilations",
        min_value=0,
        max_value=10,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_balloon_count",
    )
    for idx in range(int(balloon_count)):
        st.markdown(f"**Balloon dilation {idx + 1}**")
        location = st.text_input("Location", key=f"{key_prefix}_ther_balloon_location_{idx}").strip()
        length_cm = parse_float(
            st.text_input("Length treated (cm)", key=f"{key_prefix}_ther_balloon_length_{idx}").strip()
        )
        pre_narrow = parse_float(
            st.text_input("Pre-narrowing (%)", key=f"{key_prefix}_ther_balloon_pre_{idx}").strip()
        )
        post_patency = parse_float(
            st.text_input("Post patency (%)", key=f"{key_prefix}_ther_balloon_post_{idx}").strip()
        )
        mucosal_grade = st.text_input(
            "Mucosal tearing grade (optional)",
            key=f"{key_prefix}_ther_balloon_mucosa_{idx}",
        ).strip() or None
        inflation_count = st.number_input(
            "Number of inflations",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
            key=f"{key_prefix}_ther_balloon_inflations_{idx}",
        )
        inflations: List[Dict[str, Any]] = []
        for jdx in range(int(inflation_count)):
            with st.expander(f"Inflation {jdx + 1}", expanded=False):
                diameter = parse_float(
                    st.text_input("Balloon diameter (mm)", key=f"{key_prefix}_ther_balloon_diameter_{idx}_{jdx}").strip()
                )
                duration = parse_float(
                    st.text_input("Inflation duration (s)", key=f"{key_prefix}_ther_balloon_duration_{idx}_{jdx}").strip()
                )
                inflations.append({k: v for k, v in {"diameter_mm": diameter, "duration_s": duration}.items() if v is not None})
        with st.expander("Hemostasis (if required)", expanded=False):
            hemostasis = render_hemostasis_block(f"{key_prefix}_ther_balloon_{idx}")

        if location:
            entry = {
                "location": location,
                "inflations": inflations,
                "hemostasis": hemostasis,
            }
            if length_cm is not None:
                entry["length_cm"] = length_cm
            if pre_narrow is not None:
                entry["pre_narrowing_percent"] = pre_narrow
            if post_patency is not None:
                entry["post_patency_percent"] = post_patency
            if mucosal_grade:
                entry["mucosal_tearing_grade"] = mucosal_grade
            balloon_dilations.append(entry)
    if balloon_dilations:
        therapeutic["balloon_dilation"] = balloon_dilations

    hemoptysis_entries: List[Dict[str, Any]] = []
    hem_count = st.number_input(
        "Number of hemoptysis control episodes",
        min_value=0,
        max_value=5,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_hemo_count",
    )
    for idx in range(int(hem_count)):
        st.markdown(f"**Hemoptysis episode {idx + 1}**")
        severity = st.selectbox(
            "Presentation severity",
            ["", "minor", "moderate", "massive"],
            key=f"{key_prefix}_ther_hemo_severity_{idx}",
        )
        blood_loss = parse_float(
            st.text_input("Estimated blood loss (mL)", key=f"{key_prefix}_ther_hemo_ebl_{idx}").strip()
        )
        techniques_selected = st.multiselect(
            "Techniques applied",
            [
                "iced_saline",
                "epinephrine",
                "tranexamic_acid",
                "tamponade",
                "blocker",
                "apc",
                "electrocautery",
                "cryo",
                "other",
            ],
            key=f"{key_prefix}_ther_hemo_techniques_{idx}",
        )
        techniques: List[Dict[str, Any]] = []
        for technique in techniques_selected:
            with st.expander(f"{technique} details", expanded=False):
                tech_data: Dict[str, Any] = {"type": technique}
                if technique == "epinephrine":
                    tech_data["epi_ml_1_10000"] = parse_float(
                        st.text_input("Epinephrine (mL, 1:10,000)", key=f"{key_prefix}_ther_hemo_epi_{idx}").strip()
                    )
                if technique == "tranexamic_acid":
                    tech_data["txa_topical_mg"] = parse_float(
                        st.text_input("Tranexamic acid (mg)", key=f"{key_prefix}_ther_hemo_txa_{idx}").strip()
                    )
                if technique == "iced_saline":
                    tech_data["iced_saline_ml"] = parse_float(
                        st.text_input("Iced saline (mL)", key=f"{key_prefix}_ther_hemo_saline_{idx}").strip()
                    )
                techniques.append({k: v for k, v in tech_data.items() if v is not None})
        hemo_achieved_choice = st.radio(
            "Hemostasis achieved?",
            ["Yes", "No", "Unsure"],
            horizontal=True,
            key=f"{key_prefix}_ther_hemo_status_{idx}",
        )
        hemo_achieved, _, _ = tri_state_choice(hemo_achieved_choice)
        rebleed_choice = st.radio(
            "Rebleed within 24h?",
            ["Unsure", "Yes", "No"],
            horizontal=True,
            key=f"{key_prefix}_ther_hemo_rebleed_{idx}",
        )
        rebleed_val = {"Yes": True, "No": False}.get(rebleed_choice)
        ventilation = st.text_input(
            "Ventilation strategy (optional)",
            key=f"{key_prefix}_ther_hemo_ventilation_{idx}",
        ).strip() or None
        entry = {
            "presentation_severity": severity or None,
            "estimated_blood_loss_ml": blood_loss,
            "techniques": techniques,
            "hemostasis_achieved": hemo_achieved,
            "rebleed_within_24h": rebleed_val,
            "ventilation_strategy": ventilation,
        }
        hemoptysis_entries.append(entry)
    if hemoptysis_entries:
        therapeutic["hemoptysis_control"] = hemoptysis_entries

    stent_entries: List[Dict[str, Any]] = []
    stent_count = st.number_input(
        "Number of stents placed",
        min_value=0,
        max_value=5,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_stent_count",
    )
    for idx in range(int(stent_count)):
        st.markdown(f"**Stent {idx + 1}**")
        location = st.text_input("Location", key=f"{key_prefix}_ther_stent_location_{idx}").strip()
        stent_type = st.selectbox(
            "Stent type",
            ["silicone", "metal"],
            key=f"{key_prefix}_ther_stent_type_{idx}",
        )
        brand = st.text_input("Brand (optional)", key=f"{key_prefix}_ther_stent_brand_{idx}").strip() or None
        diameter = parse_float(
            st.text_input("Diameter (mm)", key=f"{key_prefix}_ther_stent_diameter_{idx}").strip()
        )
        length_mm = parse_float(
            st.text_input("Length (mm)", key=f"{key_prefix}_ther_stent_length_{idx}").strip()
        )
        deployment_choice = st.radio(
            "Deployment success?",
            ["Yes", "No", "Unsure"],
            horizontal=True,
            key=f"{key_prefix}_ther_stent_success_{idx}",
        )
        deployment_success, _, _ = tri_state_choice(deployment_choice)
        verification = (
            st.selectbox(
                "Position verification",
                ["", "bronchoscopic", "fluoro", "cbct"],
                key=f"{key_prefix}_ther_stent_verify_{idx}",
            )
            or None
        )
        migration_measures = st.multiselect(
            "Migration preventive measures",
            ["sutured", "silastic_button", "tied", "external_fixation", "none"],
            key=f"{key_prefix}_ther_stent_migration_{idx}",
        )
        complications = [
            item.strip()
            for item in st.text_input(
                "Immediate complications (comma separated)",
                key=f"{key_prefix}_ther_stent_complications_{idx}",
            ).split(",")
            if item.strip()
        ]
        if location:
            entry = {
                "location": location,
                "type": stent_type,
                "brand": brand,
                "diameter_mm": diameter,
                "length_mm": length_mm,
                "deployment_success": deployment_success,
                "position_verification": verification,
                "migration_preventive_measures": migration_measures,
                "immediate_complications": complications,
            }
            stent_entries.append(entry)
    if stent_entries:
        therapeutic["stent"] = stent_entries

    foreign_body_entries: List[Dict[str, Optional[str]]] = []
    foreign_count = st.number_input(
        "Number of foreign body retrievals",
        min_value=0,
        max_value=5,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_foreign_count",
    )
    for idx in range(int(foreign_count)):
        st.markdown(f"**Foreign body {idx + 1}**")
        description = st.text_input("Description", key=f"{key_prefix}_ther_foreign_desc_{idx}").strip()
        tool = st.text_input("Retrieval tool", key=f"{key_prefix}_ther_foreign_tool_{idx}").strip()
        outcome = st.text_input(
            "Outcome / notes (optional)",
            key=f"{key_prefix}_ther_foreign_outcome_{idx}",
        ).strip() or None
        if description:
            entry: Dict[str, Optional[str]] = {
                "description": description,
                "tool": tool or None,
                "outcome": outcome,
            }
            foreign_body_entries.append(entry)
    if foreign_body_entries:
        therapeutic["foreign_body"] = foreign_body_entries

    pdt_entries: List[Dict[str, Any]] = []
    pdt_count = st.number_input(
        "Number of photodynamic therapy (PDT) segments",
        min_value=0,
        max_value=5,
        value=0,
        step=1,
        key=f"{key_prefix}_ther_pdt_count",
    )
    for idx in range(int(pdt_count)):
        st.markdown(f"**PDT segment {idx + 1}**")
        photosensitizer = st.text_input(
            "Photosensitizer",
            key=f"{key_prefix}_ther_pdt_photosens_{idx}",
        ).strip()
        dose = parse_float(
            st.text_input("Dose (mg/kg)", key=f"{key_prefix}_ther_pdt_dose_{idx}").strip()
        )
        interval = parse_float(
            st.text_input("Drug-light interval (hrs)", key=f"{key_prefix}_ther_pdt_interval_{idx}").strip()
        )
        wavelength = parse_float(
            st.text_input("Wavelength (nm)", key=f"{key_prefix}_ther_pdt_wavelength_{idx}").strip()
        )
        fibre_length = parse_float(
            st.text_input("Fiber length (cm)", key=f"{key_prefix}_ther_pdt_fiber_{idx}").strip()
        )
        dosimetry_choice = st.radio(
            "Dosimetry documented?",
            ["Unsure", "Yes", "No"],
            horizontal=True,
            key=f"{key_prefix}_ther_pdt_dosimetry_{idx}",
        )
        dosimetry_documented = {"Yes": True, "No": False}.get(dosimetry_choice)
        treated_segment = st.text_input(
            "Treated segment (optional)",
            key=f"{key_prefix}_ther_pdt_segment_{idx}",
        ).strip() or None
        if photosensitizer:
            entry = {
                "photosensitizer": photosensitizer,
                "dose_mg_per_kg": dose,
                "drug_light_interval_hr": interval,
                "wavelength_nm": wavelength,
                "fiber_length_cm": fibre_length,
                "dosimetry_documented": dosimetry_documented,
                "treated_segment": treated_segment,
            }
            pdt_entries.append(entry)
    if pdt_entries:
        therapeutic["pdt"] = pdt_entries

    return therapeutic


def render_specimen_section(key_prefix: str, ui: Dict[str, Any]) -> Dict[str, Any]:
    st.markdown("**Specimen routing**")
    specimens: Dict[str, Any] = {
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
    source_options: List[str] = []

    def add_node_sources(nodes: List[Dict[str, Any]], prefix: str) -> None:
        for idx, node in enumerate(nodes):
            station = node.get("station")
            label = station or f"{prefix} station {idx + 1}"
            source_options.append(f"{prefix}:{label}")

    add_node_sources(ui.get("ebus_nodes", []), "EBUS")

    for secondary in (ui.get("secondary_procedures") or {}).values():
        add_node_sources(secondary.get("ebus_nodes", []), "EBUS-secondary")

    peripheral_targets = ui.get("peripheral_targets", [])
    for idx, target in enumerate(peripheral_targets):
        descriptor = target.get("lobe_segment") or f"Peripheral target {idx + 1}"
        source_options.append(f"Peripheral:{descriptor}")

    for secondary in (ui.get("secondary_procedures") or {}).values():
        for idx, target in enumerate(secondary.get("peripheral_targets", []) or []):
            descriptor = target.get("lobe_segment") or f"Peripheral target {idx + 1}"
            source_options.append(f"Peripheral-secondary:{descriptor}")

    if source_options:
        specimens["molecular_source_nodes"] = st.multiselect(
            "Molecular specimens sourced from",
            source_options,
            key=f"{key_prefix}_specimen_molecular_sources",
        )
    else:
        specimens["molecular_source_nodes"] = []

    return specimens


def render_complications_section(key_prefix: str) -> List[Dict[str, Optional[Any]]]:
    complications: List[Dict[str, Optional[Any]]] = []
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
        complication_entry: Dict[str, Optional[Any]] = {
            "type": comp_type,
            "severity": severity_choice or None,
            "details": details,
        }
        if comp_type == "bleeding":
            ebl_value = parse_float(
                st.text_input(
                    "Estimated blood loss (mL)",
                    key=f"{key_prefix}_comp_bleeding_ebl_{idx}",
                ).strip()
            )
            complication_entry["estimated_blood_loss_ml"] = ebl_value
            with st.expander("Hemostasis measures", expanded=False):
                complication_entry["hemostasis"] = render_hemostasis_block(f"{key_prefix}_comp_bleeding_{idx}")
        complications.append(complication_entry)
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

    sedation_used = ui.get("sedation_used_value")
    sedation_block: Dict[str, Any] = ui.get("sedation") or {}
    if sedation_used is True and not sedation_block.get("sedation_type"):
        errors.append("Sedation type is required when sedation is documented.")

    if sedation_used is True:
        monitoring_status = ui["field_status"].get("anesthesia_sedation.monitoring_bp_interval_min")
        if monitoring_status == "present" and sedation_block.get("monitoring_bp_interval_min") is None:
            errors.append("Monitoring interval is required when marked as documented.")

        sedation_type = sedation_block.get("sedation_type")
        if sedation_type in {"moderate", "deep", "MAC"}:
            if sedation_block.get("ramsay_max") is None:
                errors.append("Ramsay score is required for moderate/deep/MAC sedation.")
            if sedation_block.get("lowest_spo2_percent") is None and sedation_block.get("continuous_spo2") is not True:
                errors.append("Provide lowest SpO₂ or confirm continuous monitoring for moderate/deep/MAC sedation.")

    if quality_flags.get("fluoro") is True:
        if not any(target.get("fluoro_time_min") is not None for target in ui.get("peripheral_targets", [])):
            errors.append("Fluoroscopy time is required when fluoroscopy is marked as used.")

    if quality_flags.get("dap") is True:
        if not any(target.get("dap_cgy_cm2") is not None for target in ui.get("peripheral_targets", [])):
            errors.append("DAP value is required when DAP is marked as recorded.")

    therapeutic = ui.get("therapeutic") or {}
    if quality_flags.get("fire_risk") is True:
        for entry in therapeutic.get("airway_obstruction_relief", []):
            for modality in entry.get("modalities", []):
                if modality.get("type") in {"apc", "electrocautery", "laser"} and modality.get("fio2_at_therapy") is None:
                    errors.append("FiO₂ at therapy is required when fire-risk mitigation is documented.")
                    break
            if errors:
                break

    for dilation in therapeutic.get("balloon_dilation", []):
        if not dilation.get("inflations"):
            errors.append("Balloon dilation entries require at least one inflation detail.")
            break

    specimens = ui.get("specimens") or {}
    if specimens.get("molecular_ngs_pdl1_requested"):
        molecular_sources = specimens.get("molecular_source_nodes") or []

        def node_iter() -> List[Dict[str, Any]]:
            nodes: List[Dict[str, Any]] = list(ui.get("ebus_nodes", []))
            for secondary in (ui.get("secondary_procedures") or {}).values():
                nodes.extend(secondary.get("ebus_nodes", []) or [])
            return nodes

        nodes = node_iter()
        has_node_flag = any(node.get("molecular_from_station") for node in nodes)
        if not molecular_sources and not has_node_flag:
            errors.append("Select at least one molecular source when molecular testing is requested.")

    all_nodes: List[Dict[str, Any]] = list(ui.get("ebus_nodes", []))
    for secondary in (ui.get("secondary_procedures") or {}).values():
        all_nodes.extend(secondary.get("ebus_nodes", []) or [])
    for node in all_nodes:
        pet_status = node.get("pet_status")
        final_hint = (node.get("final_path_hint") or "") + " " + (node.get("elastography") or "")
        if pet_status and pet_status != "not_available" and "suv" in final_hint.lower():
            if node.get("pet_suv_max") is None:
                errors.append("Provide PET SUV max for stations documenting SUV details.")
                break

    complications = ui.get("complications") or []
    for comp in complications:
        if comp.get("type") == "bleeding":
            hemostasis = comp.get("hemostasis") or {}
            has_hemostasis_detail = any(
                value not in (None, "", [], {})
                for value in hemostasis.values()
            )
            if not comp.get("severity") and not has_hemostasis_detail:
                errors.append("Bleeding complications require severity or hemostasis detail.")
                break

    return errors


def main() -> None:
    st.set_page_config(page_title="Bronch Annotator v2.2", layout="wide")
    st.title("📝 Bronchoscopy Note Annotation (v2.2)")

    backend_name = os.environ.get("ANNOTATION_BACKEND", "local")
    supabase_settings: Optional[Dict[str, Any]] = None

    try:
        if "backend" in st.secrets:
            backend_name = st.secrets["backend"].get("type", backend_name)
    except Exception:
        pass

    if backend_name.lower() == "supabase":
        try:
            if "supabase" in st.secrets:
                sup_secret = st.secrets["supabase"]
                supabase_settings = {
                    "url": sup_secret.get("url"),
                    "anon_key": sup_secret.get("anon_key") or sup_secret.get("api_key"),
                    "notes_table": sup_secret.get("notes_table"),
                    "annotations_table": sup_secret.get("annotations_table"),
                }
        except Exception:
            supabase_settings = None

    try:
        backend = resolve_backend(
            backend_name=backend_name,
            local_notes_dir=NOTES_DIR,
            annotation_path=ANNOTATION_PATH,
            supabase_settings=supabase_settings,
        )
    except AnnotationBackendError as exc:
        st.error(f"Backend configuration error: {exc}")
        return

    try:
        notes = backend.list_notes()
    except AnnotationBackendError as exc:
        st.error(str(exc))
        return

    if not notes:
        if backend_name.lower() == "supabase":
            st.info("No notes found. Upload records using `python tools/supabase_seed.py`.")
        else:
            st.error("No notes found. Generate synthetic notes first.")
        return

    try:
        annotated_ids = backend.list_annotated_ids()
    except AnnotationBackendError as exc:
        st.error(f"Unable to load annotation status: {exc}")
        annotated_ids = set()

    remaining_ids = [entry.note_id for entry in notes if entry.note_id not in annotated_ids]
    remaining_set = set(remaining_ids)

    st.sidebar.header("📈 Progress")
    st.sidebar.metric("Total Notes", len(notes))
    st.sidebar.metric("Annotated", len(annotated_ids))
    st.sidebar.metric("Remaining", len(remaining_ids))
    st.sidebar.caption(f"Backend: {backend_name.title()}")

    annotator_id = st.sidebar.text_input("Annotator ID / initials", key="annotator_id").strip()
    if backend.requires_annotator() and not annotator_id:
        st.sidebar.warning("Annotator ID required to save.")

    if not remaining_ids:
        st.success("🎉 All notes have been annotated! You can still review entries below.")

    default_index = 0
    for idx, entry in enumerate(notes):
        if entry.note_id in remaining_set:
            default_index = idx
            break

    selected_entry = st.sidebar.selectbox(
        "Select Note to Annotate",
        notes,
        index=default_index,
        format_func=lambda entry: f"{entry.display_label} ({'✅' if entry.note_id in annotated_ids else '⏳'})",
    )

    try:
        note_text = backend.load_note_text(selected_entry.note_id)
    except AnnotationBackendError as exc:
        st.error(f"Failed to load note: {exc}")
        return

    key_prefix = selected_entry.note_id

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
        st.subheader(f"Note: {selected_entry.display_label}")
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
            duration_input = st.text_input(
                "Procedure duration (minutes)",
                key=f"{key_prefix}_procedure_duration",
            ).strip()
            ui["procedure_duration_min"] = parse_float(duration_input)
            procedure_category = st.selectbox(
                "Primary Procedure Type",
                PROCEDURE_CATEGORY_OPTIONS,
                index=0,
                key=f"{key_prefix}_procedure_category",
            )
            ui["procedure_category"] = procedure_category
            ui["procedure_components"] = st.multiselect(
                "Additional components performed (optional metadata)",
                PROCEDURE_TYPES,
                key=f"{key_prefix}_procedure_types_optional",
            )
            tumor_side = st.selectbox(
                "Primary tumor side",
                ["", "right", "left", "bilateral"],
                key=f"{key_prefix}_tumor_side",
            )
            tumor_lobe = st.selectbox(
                "Primary tumor lobe",
                ["", "RUL", "RML", "RLL", "LUL", "LLL", "lingula", "other"],
                key=f"{key_prefix}_tumor_lobe",
            )
            if tumor_side or tumor_lobe:
                ui["primary_tumor_location"] = {
                    "side": tumor_side or None,
                    "lobe": tumor_lobe or None,
                }
            else:
                ui["primary_tumor_location"] = None
            ui["document_type"] = st.selectbox(
                "Document Type",
                DOCUMENT_TYPES,
                key=f"{key_prefix}_document_type",
            )

        with st.expander("Quality & Workflow Flags", expanded=True):
            quality_flags = collect_quality_metrics(key_prefix, ui, procedure_category)

        with st.expander("Sedation", expanded=True):
            sedation_data = render_sedation_section(key_prefix, ui)
            ui.update(sedation_data)

        if procedure_category == "EBUS":
            with st.expander("EBUS Node Sampling", expanded=True):
                ui["ebus_nodes"] = render_ebus_section(
                    key_prefix,
                    ui,
                )

        if procedure_category in {"Navigational", "Robotic"}:
            if procedure_category == "Robotic":
                ui["robotic_platform"] = (
                    st.selectbox(
                        "Robotic platform",
                        ["", "Ion", "Monarch", "Other"],
                        key=f"{key_prefix}_robotic_platform",
                    )
                    or None
                )
            with st.expander("Peripheral / Navigation", expanded=True):
                ui["peripheral_targets"] = render_peripheral_section(
                    key_prefix,
                    ui,
                    quality_flags,
                )

        if procedure_category == "Therapeutic":
            with st.expander("Therapeutic Interventions", expanded=True):
                ui["therapeutic"] = render_therapeutic_section(
                    key_prefix,
                    ui,
                    quality_flags,
                )

        multi = st.checkbox(
            "This case included multiple distinct procedures",
            key=f"{key_prefix}_multi_proc",
        )
        ui["multi_procedure"] = bool(multi)
        ui["secondary_procedure_categories"] = []
        secondary_procedures: Dict[str, Dict[str, Any]] = {}

        if multi:
            available_secondary = [cat for cat in PROCEDURE_CATEGORY_OPTIONS if cat != procedure_category]
            secondary_categories = st.multiselect(
                "Secondary procedure types",
                available_secondary,
                key=f"{key_prefix}_secondary_categories",
            )
            ui["secondary_procedure_categories"] = secondary_categories

            for idx, secondary in enumerate(secondary_categories):
                sec_prefix = f"{key_prefix}_secondary_{idx}"
                section_payload: Dict[str, Any] = {}
                with st.expander(f"{secondary} (secondary)", expanded=False):
                    sec_flags = collect_quality_metrics(sec_prefix, ui, secondary)
                    section_payload["quality_flags"] = sec_flags

                    if secondary == "EBUS":
                        section_payload["ebus_nodes"] = render_ebus_section(
                            sec_prefix,
                            ui,
                        )

                    if secondary in {"Navigational", "Robotic"}:
                        if secondary == "Robotic":
                            section_payload["robotic_platform"] = (
                                st.selectbox(
                                    "Robotic platform",
                                    ["", "Ion", "Monarch", "Other"],
                                    key=f"{sec_prefix}_robotic_platform",
                                )
                                or None
                            )
                        section_payload["peripheral_targets"] = render_peripheral_section(
                            sec_prefix,
                            ui,
                            sec_flags,
                        )

                    if secondary == "Therapeutic":
                        section_payload["therapeutic"] = render_therapeutic_section(
                            sec_prefix,
                            ui,
                            sec_flags,
                        )

                secondary_procedures[secondary] = section_payload

        if secondary_procedures:
            ui["secondary_procedures"] = secondary_procedures
        else:
            ui.pop("secondary_procedures", None)

        with st.expander("Specimen Routing", expanded=False):
            ui["specimens"] = render_specimen_section(key_prefix, ui)

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
            elif backend.requires_annotator() and not annotator_id:
                st.error("Annotator ID is required before saving.")
            else:
                try:
                    backend.save_annotation(selected_entry.note_id, note_text, ui, annotator_id or None)
                except ValidationError as exc:
                    st.error(f"Validation error: {exc}")
                except AnnotationBackendError as exc:
                    st.error(f"Failed to persist annotation: {exc}")
                else:
                    st.success(f"✅ Saved {selected_entry.note_id} (schema v2.2)")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
