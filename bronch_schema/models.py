"""Canonical Pydantic models for bronchoscopy annotation schema v2.2."""

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


class SupplementalO2(BaseModel):
    device: Optional[str] = None
    flow_l_min: Optional[float] = None
    fio2: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Sedation(BaseModel):
    sedation_type: Optional[SedationType] = None
    meds: List[MedicationDose] = Field(default_factory=list)
    ramsay_max: Optional[float] = None
    monitoring_bp_interval_min: Optional[int] = None
    continuous_spo2: Optional[bool] = None
    reversal_available: List[str] = Field(default_factory=list)
    reversal_given: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None  # optional block-level certainty
    paralytics_used: Optional[bool] = None
    asa_class: Optional[Literal["I", "II", "III", "IV"]] = None
    ecg_monitoring: Optional[bool] = None
    capnography: Optional[bool] = None
    supplemental_o2: Optional[SupplementalO2] = None
    lowest_spo2_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    sedation_start_time: Optional[str] = None
    sedation_end_time: Optional[str] = None
    sedation_duration_min: Optional[float] = Field(default=None, ge=0.0)


class NodeSampling(BaseModel):
    station: str  # e.g., 4R, 7, 10R
    short_axis_mm: Optional[float] = None
    passes: Optional[int] = None
    pet_status: Optional[Literal["positive", "negative", "not_available"]] = None
    pet_suv_max: Optional[float] = Field(default=None, ge=0.0)
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
    needle_gauge: Optional[Literal["22G", "25G", "other"]] = None
    passes_for_molecular: Optional[int] = None
    molecular_from_station: Optional[bool] = None


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
    molecular_source_nodes: List[str] = Field(default_factory=list)


class Complication(BaseModel):
    type: Literal["none", "bleeding", "pneumothorax", "hypoxia", "other"]
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    details: Optional[str] = None
    estimated_blood_loss_ml: Optional[float] = Field(default=None, ge=0.0)
    hemostasis: Optional[Hemostasis] = None


class PrimaryTumorLocation(BaseModel):
    side: Optional[Literal["right", "left", "bilateral"]] = None
    lobe: Optional[
        Literal[
            "RUL",
            "RML",
            "RLL",
            "LUL",
            "LLL",
            "lingula",
            "other",
        ]
    ] = None


class Hemostasis(BaseModel):
    epi_ml_1_10000: Optional[float] = None
    txa_topical_mg: Optional[float] = None
    iced_saline_ml: Optional[float] = None
    agents: List[str] = Field(default_factory=list)
    hemostasis_achieved: Optional[bool] = None
    time_to_hemostasis_min: Optional[float] = None


class EnergyModality(BaseModel):
    type: Literal["apc", "electrocautery", "laser", "cryo", "mechanical"]
    power_w: Optional[float] = None
    argon_flow_l_min: Optional[float] = None
    mode: Optional[str] = None
    active_time_min: Optional[float] = None
    cycles: Optional[int] = None
    freeze_time_s: Optional[float] = None
    thaw_time_s: Optional[float] = None
    fio2_at_therapy: Optional[float] = None


class AirwayObstructionRelief(BaseModel):
    site: str
    segment_length_cm: Optional[float] = None
    pre_patency_percent: Optional[float] = Field(default=None, ge=0, le=100)
    post_patency_percent: Optional[float] = Field(default=None, ge=0, le=100)
    modalities: List[EnergyModality] = Field(default_factory=list)
    hemostasis: Optional[Hemostasis] = None
    composite_flags: Dict[str, Optional[bool]] = Field(default_factory=dict)


class BalloonInflation(BaseModel):
    diameter_mm: Optional[float] = None
    duration_s: Optional[float] = None


class BalloonDilation(BaseModel):
    location: str
    length_cm: Optional[float] = None
    pre_narrowing_percent: Optional[float] = Field(default=None, ge=0, le=100)
    post_patency_percent: Optional[float] = Field(default=None, ge=0, le=100)
    inflations: List[BalloonInflation] = Field(default_factory=list)
    mucosal_tearing_grade: Optional[str] = None
    hemostasis: Optional[Hemostasis] = None


class HemoptysisTechnique(BaseModel):
    type: Literal[
        "iced_saline",
        "epinephrine",
        "tranexamic_acid",
        "tamponade",
        "blocker",
        "apc",
        "electrocautery",
        "cryo",
        "other",
    ]
    epi_ml_1_10000: Optional[float] = None
    txa_topical_mg: Optional[float] = None
    iced_saline_ml: Optional[float] = None


class HemoptysisControl(BaseModel):
    presentation_severity: Optional[Literal["minor", "moderate", "massive"]] = None
    estimated_blood_loss_ml: Optional[float] = None
    techniques: List[HemoptysisTechnique] = Field(default_factory=list)
    hemostasis_achieved: Optional[bool] = None
    rebleed_within_24h: Optional[bool] = None
    ventilation_strategy: Optional[str] = None


class StentPlacement(BaseModel):
    location: str
    type: Literal["silicone", "metal"]
    brand: Optional[str] = None
    diameter_mm: Optional[float] = None
    length_mm: Optional[float] = None
    deployment_success: Optional[bool] = None
    position_verification: Optional[Literal["bronchoscopic", "fluoro", "cbct"]] = None
    migration_preventive_measures: List[str] = Field(default_factory=list)
    immediate_complications: List[str] = Field(default_factory=list)


class PDT(BaseModel):
    photosensitizer: str
    dose_mg_per_kg: Optional[float] = None
    drug_light_interval_hr: Optional[float] = None
    wavelength_nm: Optional[float] = None
    fiber_length_cm: Optional[float] = None
    dosimetry_documented: Optional[bool] = None
    treated_segment: Optional[str] = None


class Therapeutic(BaseModel):
    airway_obstruction_relief: List[AirwayObstructionRelief] = Field(default_factory=list)
    balloon_dilation: List[BalloonDilation] = Field(default_factory=list)
    hemoptysis_control: List[HemoptysisControl] = Field(default_factory=list)
    stent: List[StentPlacement] = Field(default_factory=list)
    foreign_body: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    pdt: List[PDT] = Field(default_factory=list)


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
    fire_risk_mitigation_documented: Optional[bool] = None


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
    procedure_category: Optional[str] = None
    procedure_types: List[str] = Field(default_factory=list)
    procedure_duration_min: Optional[float] = Field(default=None, ge=0.0)
    primary_tumor_location: Optional[PrimaryTumorLocation] = None
    sedation: Sedation = Field(default_factory=Sedation)
    ebus_nodes: List[NodeSampling] = Field(default_factory=list)
    peripheral: Optional[Dict[str, List[PeripheralTarget]]] = None
    specimens: SpecimenRouting = Field(default_factory=SpecimenRouting)
    complications: List[Complication] = Field(default_factory=list)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    inferred: InferredFlags = Field(default_factory=InferredFlags)
    therapeutic: Optional[Therapeutic] = None
    disposition: Optional[str] = None
    plan_summary: Optional[str] = None
    document_type: Optional[str] = "procedure_note"
    raw_text_hash: str


class GoldRecord(BaseModel):
    id: str
    schema_version: Literal["v2.2"] = "v2.2"
    note_text: str
    procedure: Procedure
    field_status: Dict[str, Literal["present", "explicit_no", "not_documented"]] = Field(
        default_factory=dict
    )
    field_status_detail: Dict[str, str] = Field(default_factory=dict)
