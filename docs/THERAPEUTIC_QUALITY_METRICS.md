# Therapeutic Bronchoscopy Quality Metrics (v2.2)

The v2.2 annotation schema expands therapeutic coverage so downstream models can score interventional quality. Each metric includes a numerator/denominator definition and intended data source within the procedure note.

## Global Flags
- **fire_risk_mitigation_documented** – evidence that FiO₂ ≤ 0.40 (or equivalent mitigation) was documented for energy delivery. *Denominator:* cases using APC/electrocautery/laser. *Numerator:* explicit FiO₂ or mitigation text.
- **fluoroscopy_used** – fluoroscopy mentioned for the therapeutic portion. If `True`, the UI requires `fluoro_time_min`.
- **dap_recorded** – dose area product charted. If `True`, `dap_cgy_cm2` must be supplied.
- **cbct_used** – cone-beam CT utilized for therapeutic navigation or verification.

## Airway Obstruction Relief
- **Patency delta** – (`post_patency_percent` − `pre_patency_percent`) captured per target.
- **Energy modality compliance** – requires `fio2_at_therapy` for APC/electrocautery/laser, allowing fire-risk scoring.
- **Hemostasis summary** – `Hemostasis` block documents topical agents, iced saline, and time to hemostasis for bleeding control KPI.

## Balloon Dilation
- **Inflation completeness** – `inflations[]` records diameter/duration per inflation. Guardrail ensures at least one entry.
- **Mucosal integrity** – optional `mucosal_tearing_grade` to stratify procedural trauma.

## Hemoptysis Control
- **Severity & response** – `presentation_severity`, `estimated_blood_loss_ml`, tactic list, hemostasis success, and 24 h rebleed markers enable efficacy and safety denominators.

## Stent Placement
- **Sizing & verification** – tracks diameter/length, deployment success, and verification modality (bronchoscopic / fluoro / CBCT). Migration mitigations and immediate complications feed post-placement dashboards.

## Foreign Body Retrieval
- **Retrieval documentation** – free-form list capturing object description, tool, and qualitative outcome for auditing retrieval workflow.

## Photodynamic Therapy (PDT)
- **Dosimetry confirmation** – `dosimetry_documented` flag plus dose, wavelength, fiber length, and drug-light interval for QA cycles.

These metrics are produced directly from the tri-state–gated Streamlit UI and stored in `eval/data/gold_corpus_v2_2.jsonl`. Use them to benchmark therapeutic adherence, safety, and documentation completeness.
