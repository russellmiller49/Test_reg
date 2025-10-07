"""Canonical Pydantic models for bronchoscopy annotation schema v2.1."""

from datetime import date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SedationType = Literal["moderate", "deep", "general", "MAC", "local_topical"]


class MedicationDose(BaseModel):
    name: str
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None  # mg, mcg, mL, %, etc.
    route: Optional[str] = None  # IV, topical, nebulized
    timing_note: Optional[str] = None


class Sedation(BaseModel):
    sedation_type: Optional[SedationType] = None
    meds: List[MedicationDose] = Field(default_factory=list)
    ramsay_max: Optional[float] = None
    monitoring_bp_interval_min: Optional[int] = None
    continuous_spo2: Optional[bool] = None
    reversal_agents: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None  # optional block-level certainty


class NodeSampling(BaseModel):
    station: str  # e.g., 4R, 7, 10R
    short_axis_mm: Optional[float] = None
    passes: Optional[int] = None
    pet_status: Optional[Literal["positive", "negative", "not_available"]] = None
    rose: Optional[
        Literal[
            "positive_malignant",
            "benign",
            "atypical",
            "adequate_only",
            "insufficient",
            "granulomatous",
        ]
    ] = None
    elastography: Optional[str] = None
    final_path_hint: Optional[str] = None


class PeripheralTarget(BaseModel):
    lobe_segment: Optional[str] = None
    size_mm: Optional[int] = None
    bronchus_sign: Optional[bool] = None
    tool_in_lesion_confirmed: Optional[bool] = None
    radial_pattern: Optional[Literal["concentric", "eccentric", "not_seen"]] = None
    cbct_used: Optional[bool] = None
    fluoro_time_min: Optional[float] = None
    dap_cgy_cm2: Optional[float] = None
    samples: Dict[str, Optional[int]] = Field(default_factory=dict)
    rose: Optional[str] = None
    final_path_hint: Optional[str] = None


class SpecimenRouting(BaseModel):
    cytology: bool = False
    cell_block: bool = False
    histology: bool = False
    flow_cytometry: bool = False
    microbiology_afb_fungal_bacterial: bool = False
    molecular_ngs_pdl1_requested: bool = False


class Complication(BaseModel):
    type: Literal["none", "bleeding", "pneumothorax", "hypoxia", "other"]
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    details: Optional[str] = None


class QualityMetrics(BaseModel):
    staging_indication: Optional[bool] = None
    systematic_n3_n2_n1: Optional[bool] = None
    photodocumentation_all_stations: Optional[bool] = None
    rose_available: Optional[bool] = None
    protocol_adherence: Optional[float] = None

    # New high-level presence flags to mirror conditional UI prompts
    pet_documented: Optional[bool] = None
    radial_ebus_performed: Optional[bool] = None
    tool_in_lesion_assessed: Optional[bool] = None
    fluoroscopy_used: Optional[bool] = None
    dap_recorded: Optional[bool] = None
    cbct_used: Optional[bool] = None


class InferredFlags(BaseModel):
    n_category: Optional[Literal["N0", "N1", "N2", "N3", "unknown"]] = None
    bilateral_or_contralateral_nodes: Optional[bool] = None
    lymphoma_pattern_suspected: Optional[bool] = None
    sarcoid_pattern_suspected: Optional[bool] = None
    adequate_for_molecular: Optional[bool] = None


class Procedure(BaseModel):
    patient_name: Optional[str] = None
    mrn: Optional[str] = None
    dob: Optional[date] = None
    procedure_date: Optional[date] = None
    indication: Optional[str] = None
    procedure_types: List[str] = Field(default_factory=list)
    sedation: Sedation = Field(default_factory=Sedation)
    ebus_nodes: List[NodeSampling] = Field(default_factory=list)
    peripheral: Optional[Dict[str, List[PeripheralTarget]]] = None
    specimens: SpecimenRouting = Field(default_factory=SpecimenRouting)
    complications: List[Complication] = Field(default_factory=list)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    inferred: InferredFlags = Field(default_factory=InferredFlags)
    disposition: Optional[str] = None
    plan_summary: Optional[str] = None
    document_type: Optional[str] = "procedure_note"
    raw_text_hash: str


class GoldRecord(BaseModel):
    id: str
    schema_version: Literal["v2.1"] = "v2.1"
    note_text: str
    procedure: Procedure
    field_status: Dict[str, Literal["present", "explicit_no", "not_documented"]] = Field(
        default_factory=dict
    )
    field_status_detail: Dict[str, str] = Field(default_factory=dict)
