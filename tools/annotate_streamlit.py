#!/usr/bin/env python3
"""Streamlit annotation interface for bronchoscopy notes"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


def parse_int(value: str) -> Optional[int]:
    """Convert a string to int if possible."""
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_float(value: str) -> Optional[float]:
    """Convert a string to float if possible."""
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def tri_state_selectbox(label: str, key: str) -> Optional[bool]:
    """Render a tri-state selectbox returning True/False/None."""
    option = st.selectbox(label, ["Unknown", "Yes", "No"], key=key)
    if option == "Yes":
        return True
    if option == "No":
        return False
    return None


def save_annotation(note_id: str, note_text: str, procedure: Dict[str, Any]) -> None:
    """Append an annotation record to the JSONL dataset."""
    output_path = Path("eval/data/gold_corpus_v1.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "id": note_id,
        "note_text": note_text,
        "procedure": procedure
    }
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    st.success(f"✅ Saved {note_id}")


def load_annotated_ids() -> set[str]:
    """Return the set of note IDs that are already annotated."""
    jsonl_path = Path("eval/data/gold_corpus_v1.jsonl")
    if not jsonl_path.exists():
        return set()

    annotated_ids: set[str] = set()
    with open(jsonl_path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            annotated_ids.add(record.get("id"))
    return annotated_ids


def main() -> None:
    st.set_page_config(page_title="Bronch Annotator", layout="wide")
    st.title("📝 Bronchoscopy Note Annotation")

    notes_dir = Path("data/synthetic_notes")
    note_files = sorted(notes_dir.glob("*.txt"))

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
        format_func=lambda path: f"{path.name} ({'✅' if path.stem in annotated_ids else '⏳'})"
    )

    note_text = selected_file.read_text(encoding="utf-8")

    st.header(f"Note: {selected_file.name}")
    st.text_area("Clinical Note", note_text, height=320)

    st.header("📊 Annotate Fields")
    key_prefix = selected_file.stem

    # Patient & Procedure metadata
    with st.expander("Patient & Procedure Info", expanded=True):
        patient_name = st.text_input("Patient Name", key=f"{key_prefix}_patient_name")
        mrn = st.text_input("MRN", key=f"{key_prefix}_mrn")
        dob_input = st.text_input("Date of Birth (YYYY-MM-DD)", key=f"{key_prefix}_dob")
        procedure_date_input = st.text_input("Procedure Date (YYYY-MM-DD)", key=f"{key_prefix}_proc_date")
        indication = st.text_area("Indication / History", key=f"{key_prefix}_indication")
        procedure_types = st.multiselect(
            "Procedure Types",
            [
                "EBUS_TBNA",
                "EMN",
                "Robotic",
                "Cryobiopsy",
                "Endobronchial_biopsy",
                "BAL",
                "Fiducial",
                "Therapeutic",
                "Teaching",
                "Other"
            ],
            key=f"{key_prefix}_procedure_types"
        )
        document_type = st.selectbox(
            "Document Type",
            [
                "procedure_note",
                "progress_note",
                "telephone_note",
                "teaching_note",
                "safety_checklist",
                "registry_form"
            ],
            key=f"{key_prefix}_document_type"
        )

    # Sedation details
    with st.expander("Sedation", expanded=True):
        sedation_type = st.selectbox(
            "Sedation Type",
            ["", "moderate", "deep", "general", "MAC", "local_topical"],
            key=f"{key_prefix}_sedation_type"
        )
        sedation_ramsay = st.text_input("Ramsay max", key=f"{key_prefix}_ramsay")
        sedation_bp_interval = st.text_input("BP monitoring interval (min)", key=f"{key_prefix}_bp_interval")
        continuous_spo2 = tri_state_selectbox(
            "Continuous SpO₂ monitoring?",
            key=f"{key_prefix}_spo2"
        )
        sedation_reversal = st.multiselect(
            "Reversal agents used",
            ["flumazenil", "naloxone"],
            key=f"{key_prefix}_reversal"
        )
        sedation_events_common = st.multiselect(
            "Sedation events (select)",
            ["hypoxia", "prolonged sedation", "hypotension", "bradycardia", "reversal_given"],
            key=f"{key_prefix}_sedation_events"
        )
        sedation_events_extra = st.text_input(
            "Additional sedation events (comma separated)",
            key=f"{key_prefix}_sedation_events_extra"
        )
        sed_source_span = st.text_area("Sedation source span", key=f"{key_prefix}_sed_source")
        sed_confidence_input = st.text_input("Sedation confidence (0-1)", key=f"{key_prefix}_sed_confidence")

        sedation_meds_count = int(
            st.number_input(
                "Number of sedation medications", min_value=0, max_value=12, value=0, step=1,
                key=f"{key_prefix}_sed_med_count"
            )
        )
        sedation_meds: List[Dict[str, Any]] = []
        for idx in range(sedation_meds_count):
            st.markdown(f"**Medication {idx + 1}**")
            med_name = st.text_input("Name", key=f"{key_prefix}_sed_med_name_{idx}")
            med_dose_value = st.text_input("Dose value", key=f"{key_prefix}_sed_med_value_{idx}")
            med_dose_unit = st.text_input("Dose unit", key=f"{key_prefix}_sed_med_unit_{idx}")
            med_route = st.text_input("Route", key=f"{key_prefix}_sed_med_route_{idx}")
            med_timing = st.text_input("Timing note", key=f"{key_prefix}_sed_med_timing_{idx}")
            if med_name:
                sedation_meds.append({
                    "name": med_name,
                    "dose_value": parse_float(med_dose_value) if med_dose_value.strip() else None,
                    "dose_unit": med_dose_unit or None,
                    "route": med_route or None,
                    "timing_note": med_timing or None
                })

        sedation_events = list(dict.fromkeys(
            sedation_events_common +
            [evt.strip() for evt in sedation_events_extra.split(",") if evt.strip()]
        ))
        sedation_confidence = parse_float(sed_confidence_input) if sed_confidence_input.strip() else None
        sedation = {
            "sedation_type": sedation_type or None,
            "meds": sedation_meds,
            "ramsay_max": parse_float(sedation_ramsay) if sedation_ramsay.strip() else None,
            "monitoring_bp_interval_min": parse_int(sedation_bp_interval) if sedation_bp_interval.strip() else None,
            "continuous_spo2": continuous_spo2,
            "reversal_agents": sedation_reversal,
            "events": sedation_events,
            "source_span": sed_source_span or None,
            "confidence": sedation_confidence
        }

    # EBUS nodes
    with st.expander("EBUS Node Sampling", expanded=True):
        node_count = int(
            st.number_input(
                "Number of nodes sampled", min_value=0, max_value=40, value=0, step=1,
                key=f"{key_prefix}_node_count"
            )
        )
        ebus_nodes: List[Dict[str, Any]] = []
        for idx in range(node_count):
            st.markdown(f"**Node {idx + 1}**")
            station = st.text_input("Station", key=f"{key_prefix}_node_station_{idx}")
            size_input = st.text_input("Short-axis size (mm)", key=f"{key_prefix}_node_size_{idx}")
            passes_input = st.text_input("Passes", key=f"{key_prefix}_node_passes_{idx}")
            pet_status = st.selectbox(
                "PET status",
                ["", "positive", "negative", "not_available"],
                key=f"{key_prefix}_node_pet_status_{idx}"
            )
            pet_suv_input = st.text_input("PET SUV", key=f"{key_prefix}_node_pet_suv_{idx}")
            rose = st.selectbox(
                "ROSE result",
                [
                    "",
                    "positive_malignant",
                    "benign",
                    "atypical",
                    "adequate_only",
                    "insufficient",
                    "granulomatous"
                ],
                key=f"{key_prefix}_node_rose_{idx}"
            )
            ultrasound_shape = st.text_input("Ultrasound shape", key=f"{key_prefix}_node_shape_{idx}")
            ultrasound_hilum = st.text_input("Ultrasound hilum", key=f"{key_prefix}_node_hilum_{idx}")
            ultrasound_echo = st.text_input("Ultrasound echotexture", key=f"{key_prefix}_node_echo_{idx}")
            ultrasound_elasto = st.text_input("Ultrasound elastography score", key=f"{key_prefix}_node_elasto_{idx}")
            ultrasound_vascularity = st.text_input("Ultrasound vascularity", key=f"{key_prefix}_node_vasc_{idx}")
            adequacy = st.selectbox(
                "Adequacy",
                ["", "adequate", "inadequate", "unknown"],
                key=f"{key_prefix}_node_adequacy_{idx}"
            )
            molecular_sent = tri_state_selectbox(
                "Molecular tests sent?",
                key=f"{key_prefix}_node_molecular_{idx}"
            )
            final_path = st.text_input("Final pathology summary", key=f"{key_prefix}_node_path_{idx}")
            node_source_span = st.text_area("Node source span", key=f"{key_prefix}_node_source_{idx}")
            node_confidence_input = st.text_input("Node confidence (0-1)", key=f"{key_prefix}_node_conf_{idx}")

            if station:
                ultrasound_features = {
                    "shape": ultrasound_shape or None,
                    "hilum": ultrasound_hilum or None,
                    "echotexture": ultrasound_echo or None,
                    "elastography_score": ultrasound_elasto or None,
                    "vascularity": ultrasound_vascularity or None
                }
                ultrasound_features = {
                    key: value
                    for key, value in ultrasound_features.items()
                    if value is not None and value.strip()
                }
                ebus_nodes.append({
                    "station": station,
                    "size_mm_short_axis": parse_float(size_input) if size_input.strip() else None,
                    "passes": parse_int(passes_input) if passes_input.strip() else None,
                    "pet_status": pet_status or None,
                    "pet_suv": parse_float(pet_suv_input) if pet_suv_input.strip() else None,
                    "rose": rose or None,
                    "ultrasound_features": ultrasound_features,
                    "adequacy": adequacy or None,
                    "molecular_tests_sent": molecular_sent,
                    "final_path_summary": final_path or None,
                    "source_span": node_source_span or None,
                    "confidence": parse_float(node_confidence_input) if node_confidence_input.strip() else None
                })

    # Peripheral sampling
    with st.expander("Peripheral / Navigation", expanded=False):
        include_peripheral = st.checkbox("Include peripheral sampling", key=f"{key_prefix}_peripheral_include")
        peripheral: Optional[Dict[str, Any]] = None
        if include_peripheral:
            platform = st.selectbox(
                "Platform",
                ["", "EMN", "Robotic_Ion", "Robotic_Other", "None"],
                key=f"{key_prefix}_peripheral_platform"
            )
            radial_pattern = st.selectbox(
                "Radial EBUS pattern",
                ["", "concentric", "eccentric", "not_seen"],
                key=f"{key_prefix}_peripheral_pattern"
            )
            tool_in_lesion = tri_state_selectbox(
                "Tool in lesion confirmed?",
                key=f"{key_prefix}_peripheral_tool"
            )
            cbct_used = tri_state_selectbox(
                "CBCT used?",
                key=f"{key_prefix}_peripheral_cbct"
            )
            fluoro_time = st.text_input("Fluoroscopy time (min)", key=f"{key_prefix}_peripheral_fluoro")
            dap = st.text_input("Dose area product (cGy*cm²)", key=f"{key_prefix}_peripheral_dap")
            registration_error = st.text_input("Registration error (mm)", key=f"{key_prefix}_peripheral_regerr")
            target_segment = st.text_input("Target lobe/segment", key=f"{key_prefix}_peripheral_target")
            st.markdown("**Sampling counts**")
            sample_types = ["needle_aspirate", "forceps_biopsy", "brush", "cryo", "BAL"]
            sampling: Dict[str, int] = {}
            for sample in sample_types:
                count = st.number_input(
                    f"{sample.replace('_', ' ').title()} count",
                    min_value=0,
                    max_value=25,
                    value=0,
                    step=1,
                    key=f"{key_prefix}_peripheral_sampling_{sample}"
                )
                if count:
                    sampling[sample] = int(count)
            fiducial_placed = tri_state_selectbox(
                "Fiducial placed?",
                key=f"{key_prefix}_peripheral_fiducial"
            )
            blocker_used = tri_state_selectbox(
                "Blocker used?",
                key=f"{key_prefix}_peripheral_blocker"
            )
            peripheral_source_span = st.text_area("Peripheral source span", key=f"{key_prefix}_peripheral_source")
            peripheral_confidence_input = st.text_input(
                "Peripheral confidence (0-1)",
                key=f"{key_prefix}_peripheral_conf"
            )
            peripheral = {
                "platform": platform or None,
                "radial_ebus_pattern": radial_pattern or None,
                "tool_in_lesion_confirmed": tool_in_lesion,
                "cbct_used": cbct_used,
                "fluoro_time_min": parse_float(fluoro_time) if fluoro_time.strip() else None,
                "dose_area_product_cgy_cm2": parse_float(dap) if dap.strip() else None,
                "registration_error_mm": parse_float(registration_error) if registration_error.strip() else None,
                "target_lobe_segment": target_segment or None,
                "sampling": sampling,
                "fiducial_placed": fiducial_placed,
                "blocker_used": blocker_used,
                "source_span": peripheral_source_span or None,
                "confidence": parse_float(peripheral_confidence_input) if peripheral_confidence_input.strip() else None
            }

    # Specimen routing
    with st.expander("Specimen Routing", expanded=False):
        specimens = {
            "cytology": st.checkbox("Cytology", key=f"{key_prefix}_specimen_cytology"),
            "cell_block": st.checkbox("Cell block", key=f"{key_prefix}_specimen_cell_block"),
            "histology": st.checkbox("Histology", key=f"{key_prefix}_specimen_histology"),
            "flow_cytometry": st.checkbox("Flow cytometry", key=f"{key_prefix}_specimen_flow"),
            "microbiology_afb_fungal_bacterial": st.checkbox(
                "Microbiology (AFB/Fungal/Bacterial)",
                key=f"{key_prefix}_specimen_micro"
            ),
            "molecular_ngs_pdl1_requested": st.checkbox(
                "Molecular / NGS / PD-L1", key=f"{key_prefix}_specimen_molecular"
            )
        }

    # Complications
    with st.expander("Complications", expanded=False):
        complications: List[Dict[str, Any]] = []
        no_complications = st.checkbox("No complications", key=f"{key_prefix}_comp_none")
        if no_complications:
            complications = [{"type": "none", "severity": None, "details": None}]
        else:
            comp_count = int(
                st.number_input(
                    "Number of complications", min_value=0, max_value=10, value=0, step=1,
                    key=f"{key_prefix}_comp_count"
                )
            )
            for idx in range(comp_count):
                st.markdown(f"**Complication {idx + 1}**")
                comp_type = st.selectbox(
                    "Type",
                    ["bleeding", "pneumothorax", "hypoxia", "other"],
                    key=f"{key_prefix}_comp_type_{idx}"
                )
                severity = st.selectbox(
                    "Severity",
                    ["", "mild", "moderate", "severe"],
                    key=f"{key_prefix}_comp_severity_{idx}"
                )
                details = st.text_area("Details", key=f"{key_prefix}_comp_details_{idx}")
                complications.append({
                    "type": comp_type,
                    "severity": severity or None,
                    "details": details or None
                })

    # Quality metrics
    with st.expander("Quality Metrics", expanded=False):
        protocol_input = st.text_input("Protocol adherence (0-1)", key=f"{key_prefix}_quality_protocol")
        quality = {
            "staging_indication": st.checkbox("Staging indication documented", key=f"{key_prefix}_quality_staging"),
            "systematic_n3_n2_n1": st.checkbox("Systematic N3→N2→N1", key=f"{key_prefix}_quality_systematic"),
            "photodocumentation_all_stations": st.checkbox(
                "Photodocumentation of all stations",
                key=f"{key_prefix}_quality_photo"
            ),
            "rose_available": st.checkbox("ROSE available", key=f"{key_prefix}_quality_rose"),
            "protocol_adherence": parse_float(protocol_input) if protocol_input.strip() else None,
            "source_span": st.text_area("Quality source span", key=f"{key_prefix}_quality_source") or None
        }

    # Inferred flags
    with st.expander("Inferred Flags", expanded=False):
        n_category = st.selectbox(
            "N category",
            ["", "N0", "N1", "N2", "N3", "unknown"],
            key=f"{key_prefix}_inferred_n"
        )
        bilateral_nodes = tri_state_selectbox(
            "Bilateral / contralateral nodes involved?",
            key=f"{key_prefix}_inferred_bilateral"
        )
        lymphoma_pattern = tri_state_selectbox(
            "Lymphoma pattern suspected?",
            key=f"{key_prefix}_inferred_lymphoma"
        )
        sarcoid_pattern = tri_state_selectbox(
            "Sarcoid pattern suspected?",
            key=f"{key_prefix}_inferred_sarcoid"
        )
        adequate_molecular = tri_state_selectbox(
            "Adequate for molecular testing?",
            key=f"{key_prefix}_inferred_molecular"
        )
        inferred = {
            "n_category": n_category or None,
            "bilateral_or_contralateral_nodes": bilateral_nodes,
            "lymphoma_pattern_suspected": lymphoma_pattern,
            "sarcoid_pattern_suspected": sarcoid_pattern,
            "adequate_for_molecular": adequate_molecular
        }

    # Disposition / plan
    with st.expander("Disposition & Plan", expanded=False):
        disposition = st.text_input("Disposition", key=f"{key_prefix}_disposition")
        plan_summary = st.text_area("Plan summary / next steps", key=f"{key_prefix}_plan")

    raw_text_hash = hashlib.sha256(note_text.encode("utf-8")).hexdigest()

    procedure: Dict[str, Any] = {
        "patient_name": patient_name or None,
        "mrn": mrn or None,
        "dob": dob_input or None,
        "procedure_date": procedure_date_input or None,
        "indication": indication or None,
        "procedure_types": procedure_types,
        "sedation": sedation,
        "ebus_nodes": ebus_nodes,
        "peripheral": peripheral,
        "specimens": specimens,
        "complications": complications,
        "quality": quality,
        "inferred": inferred,
        "disposition": disposition or None,
        "plan_summary": plan_summary or None,
        "document_type": document_type,
        "raw_text_hash": raw_text_hash
    }

    if st.button("💾 Save Annotation"):
        save_annotation(selected_file.stem, note_text, procedure)
        st.rerun()


if __name__ == "__main__":
    main()
