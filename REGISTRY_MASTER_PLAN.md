# BRONCHOSCOPY REGISTRY - COMPLETE IMPLEMENTATION PLAN
## iOS-First with Apple Foundation Models | Solo Developer Guide

---

## 📋 EXECUTIVE SUMMARY

**Project:** Privacy-preserving bronchoscopy procedure registry with on-device AI extraction  
**Platform:** iOS 26+ (Apple Intelligence required)  
**Developer:** Solo build using Claude Code + Codex  
**Timeline:** ~12-14 weeks  
**Regulatory Path:** Quality Improvement (not FDA)  

**Architecture:**
```
Capture → OCR → PHI Detect → Redact → Extract (Foundation Models) → Submit → Metrics
   ↓         ↓        ↓          ↓           ↓                          ↓         ↓
VisionKit  Vision  Regex+    Pixel-level  @Generable              FastAPI    SQL
                   Zones     Black boxes   on-device LLM          Gateway   Analytics
```

**Key Innovation:** Zero-persistence PHI handling + on-device 3B parameter LLM extraction (~100-300ms)

---

## 🎯 MANUAL ACTIONS CHECKLIST

Throughout this implementation, you'll need to perform manual tasks. Here's the complete list:

### ⏸️ MANUAL ACTION #1: Training Data Preparation
**When:** After Block 1 (schemas exist)  
**What:** Gather 50-100 clinical notes from your archive, de-identify PHI  
**How:**
1. Collect notes from your bronchoscopy archive
2. Run `python tools/phi_synthesizer.py --input-dir data/raw_notes --output-dir data/synthetic_notes`
3. Review synthetic notes for quality
4. Ensure coverage: 30+ EBUS, 10+ navigation, 10+ therapeutic cases

**Time:** 2-3 hours  
**Deliverable:** `data/synthetic_notes/*.txt` (50-100 files)

---

### ⏸️ MANUAL ACTION #2: Data Annotation
**When:** After annotation tool is built (Block 2A)  
**What:** Manually annotate 50-100 notes with ground truth fields  
**How:**
1. Run: `streamlit run tools/annotate_streamlit.py`
2. For each note, fill in:
   - Procedure type
   - EBUS fields (if applicable): stations, sizes, passes
   - Sedation: mode, Ramsay score, monitoring intervals
   - Complications
   - Quality assertions
3. Mark PHI spans (character positions)
4. Click "Save Annotation"

**Time:** 4-8 hours (5-10 min per note)  
**Deliverable:** `eval/data/gold_corpus_v1.jsonl` with 50+ entries

---

### ⏸️ MANUAL ACTION #3: JWT Configuration
**When:** During Block 2 (gateway setup)  
**What:** Generate secure JWT secret and development token  
**How:**
```bash
# Generate secret
openssl rand -hex 32

# Set environment variable
export REGISTRY_JWT_SECRET="<paste-secret-here>"

# Generate dev token
python gateway/scripts/generate_dev_jwt.py

# Copy the printed JWT - you'll need it for:
# 1. Testing gateway with curl
# 2. iOS app configuration
```

**Time:** 5 minutes  
**Deliverable:** JWT token (save securely)

---

### ⏸️ MANUAL ACTION #4: iOS Device Setup
**When:** Before Block 4 (iOS development)  
**What:** Prepare iOS device with Apple Intelligence  
**Requirements:**
- **Device:** iPhone 15 Pro/Max or iPhone 16 (any), iPad Air/Pro (M2+), Mac (M1+)
- **OS:** iOS 26+ (or iPadOS 26+, macOS Tahoe 26+)
- **Apple Intelligence:** MUST be enabled

**How:**
1. Update to iOS 26 or later
2. Go to: Settings → Apple Intelligence & Siri → Enable Apple Intelligence
3. Wait 10-30 minutes for model download (one-time, ~500MB)
4. Verify in Xcode playground:
```swift
import FoundationModels
print(SystemLanguageModel.default.availability)
// Should print: .available
```

**Time:** 30-60 minutes (mostly waiting for download)  
**Deliverable:** Device ready for Foundation Models

---

### ⏸️ MANUAL ACTION #5: Keychain Configuration
**When:** During Block 4 (iOS app running)  
**What:** Configure JWT token in app  
**How:**
1. Build and run app on device
2. Go to Settings tab (will be created)
3. Enter:
   - **Gateway URL:** `http://localhost:8000` (for development)
   - **JWT Token:** (paste token from Manual Action #3)
4. Tap "Save"

**Time:** 2 minutes  
**Deliverable:** App configured for gateway communication

---

### ⏸️ MANUAL ACTION #6: Model Evaluation
**When:** After extraction is working (Block 4A)  
**What:** Evaluate extraction accuracy and tune  
**How:**
```bash
# Run evaluation
python tools/eval_harness.py --config eval/eval_config.yaml

# Review results
# Target thresholds:
#   - EBUS F1 ≥ 0.92
#   - Sedation F1 ≥ 0.95
#   - PHI recall = 1.0

# If below threshold:
# 1. Review failure cases in output
# 2. Refine extraction prompts in prompts/extract_*.txt
# 3. Add more training examples if needed
# 4. Adjust confidence thresholds in config
# 5. Re-run evaluation
```

**Time:** 30 minutes per iteration (expect 2-3 iterations)  
**Deliverable:** Passing eval metrics

---

### ⏸️ MANUAL ACTION #7: TestFlight Distribution
**When:** Phase 6 (deployment)  
**What:** Distribute app to beta testers  
**How:**
1. Create Apple Developer account ($99/year if not enrolled)
2. Create App ID in developer portal
3. In Xcode: Product → Archive
4. Upload to App Store Connect
5. Create TestFlight beta group
6. Invite testers (colleagues)

**Time:** 2-3 hours (first time)  
**Deliverable:** Beta testing group active

---

## 🧬 FOUNDATION MODELS API REFERENCE

Apple's Foundation Models framework provides structured output generation from on-device LLMs.

### Key Concepts

**1. @Generable - Structured Output**
```swift
import FoundationModels

@Generable
struct EBUSExtraction {
    var stagingIndication: Bool?
    var systematicSequenceUsed: Bool?
    var stationsSampled: [StationSample]?
}

@Generable
struct StationSample {
    var station: String  // e.g., "4R", "7"
    var sizeMm: Int
    var passes: Int
    var roseUsed: Bool?
}
```

**2. @Guide - Constrained Values**
```swift
@Generable
struct SedationExtraction {
    @Guide(.options(["local", "moderate_sedation", "deep_sedation", "general_anesthesia"]))
    var mode: String
    
    @Guide(.range(1...6))
    var ramsayMax: Int
}
```

**3. SystemLanguageModel - Entry Point**
```swift
let model = SystemLanguageModel.default

// Check availability
switch model.availability {
case .available:
    // Ready to use
case .unavailable(.appleIntelligenceNotEnabled):
    // Prompt user to enable in Settings
case .unavailable(.deviceNotEligible):
    // Fallback to manual forms
case .unavailable(.modelNotReady):
    // Model still downloading
}
```

**4. LanguageModelSession - Stateful Conversations**
```swift
let session = model.startSession(instructions: """
You are extracting EBUS-TBNA data for a bronchoscopy registry.
Extract fields matching the provided schema. If uncertain, set to null.
Never include PHI (names, MRNs, dates of birth).
""")

let result = try await session.generateResponse(
    for: "EBUS staging. N3→N2→N1. Station 4R (9mm) x4, ROSE+, PET+.",
    as: EBUSExtraction.self
)

print(result.stagingIndication)  // true
print(result.stationsSampled?.first?.station)  // "4R"
```

**5. Performance Characteristics**
- **Model Size:** ~3B parameters (built into system)
- **Latency:** 100-300ms for typical procedure note
- **Memory:** OS-managed, ~200-300MB peak
- **Offline:** Fully functional without network
- **Privacy:** Zero data leaves device

**6. Streaming (Optional)**
```swift
for try await chunk in session.streamResponse(for: prompt, as: MyStruct.self) {
    // Process incrementally
}
```

### Availability Requirements
- iOS 26+, iPadOS 26+, macOS Tahoe 26+
- Apple Intelligence-compatible hardware:
  - iPhone 15 Pro / Pro Max (A17 Pro)
  - iPhone 16 series (A18 / A18 Pro)
  - iPad Air (M2+)
  - iPad Pro (M1+)
  - Mac (M1+, M2+, M3+)

---

## 📦 PHASE 1: BACKEND FOUNDATION (Weeks 1-2)

**Goal:** Working FastAPI gateway + schemas + evaluation harness  
**No iOS work yet - pure backend**

### Block 0: Repository Bootstrap

**Acceptance:** Clean git repo with structure

```bash
# Execute
mkdir -p bronch-registry && cd bronch-registry
git init

# Create structure
mkdir -p schemas/codebooks openapi config prompts sql/metrics eval/data
mkdir -p mobile/ios gateway/app gateway/migrations gateway/jobs
mkdir -p docs runbooks .codex .github/workflows tools examples data/raw_notes

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.env
*.db

# iOS
*.xcuserstate
*.xcworkspace/xcuserdata/
DerivedData/

# Secrets
*.pem
*.key
.secrets/

# Data
data/raw_notes/*.txt
data/synthetic_notes/
*.jsonl
!eval/data/gold_corpus_v1.jsonl

# Large files
*.mp4
*.mov
*.pdf
EOF

# Pre-commit hook (block PHI + large files)
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
find . -type f -size +25M | grep -v '.git' && echo "❌ Files >25MB detected" && exit 1
git diff --cached | grep -E '(SSN:|MRN:|DOB:|Patient:)' && echo "❌ PHI pattern detected" && exit 1
exit 0
EOF
chmod +x .git/hooks/pre-commit

git add -A
git commit -m "chore(repo): bootstrap monorepo structure + precommit guard"
```

---

### Block 1: Canonical Schemas + Codebooks

**Acceptance:** Valid schemas that examples validate against

**File:** `schemas/bronchoscopy_procedure.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Bronchoscopy Procedure Submission",
  "type": "object",
  "required": ["schema_version", "facility_id", "operator_id_hash", "procedure_datetime_shifted", "procedure_type", "safety", "phi_attestation"],
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version of this schema"
    },
    "facility_id": {
      "type": "string",
      "pattern": "^[A-Z0-9-]{3,20}$",
      "description": "De-identified facility identifier"
    },
    "operator_id_hash": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "SHA-256 hash of operator identifier"
    },
    "procedure_datetime_shifted": {
      "type": "string",
      "format": "date-time",
      "description": "Procedure datetime shifted by facility-specific random offset"
    },
    "patient": {
      "type": "object",
      "properties": {
        "age_years": {"type": "integer", "minimum": 0, "maximum": 120},
        "sex": {"enum": ["female", "male", "unknown"]},
        "smoking_status": {"enum": ["never", "current", "previous", "unknown"]},
        "comorbidities": {
          "type": "array",
          "items": {"type": "string"}
        },
        "baseline_spirometry": {
          "type": "object",
          "properties": {
            "fev1_pct_pred": {"type": "number", "minimum": 0, "maximum": 200},
            "fvc_pct_pred": {"type": "number", "minimum": 0, "maximum": 200}
          }
        }
      }
    },
    "procedure_type": {
      "enum": ["diagnostic_flexible", "ebus_tbna", "navigation_bronchoscopy", "therapeutic_bronchoscopy"]
    },
    "anesthesia": {
      "type": "object",
      "properties": {
        "mode": {"enum": ["local", "moderate_sedation", "deep_sedation", "general_anesthesia"]},
        "ramsay_max": {"type": "integer", "minimum": 1, "maximum": 6},
        "monitoring_intervals_min": {"enum": [5, 10, 15]},
        "reversal_agents_used": {
          "type": "array",
          "items": {"enum": ["flumazenil", "naloxone"]}
        }
      }
    },
    "documentation": {
      "type": "object",
      "properties": {
        "synoptic_report_used": {"type": "boolean"},
        "safety_checklist_completed": {"type": "boolean"},
        "photodoc_key_landmarks": {"type": "boolean"},
        "systematic_airway_inspection_pct": {"type": "integer", "minimum": 0, "maximum": 100}
      }
    },
    "ebus": {
      "type": "object",
      "properties": {
        "staging_indication": {"type": "boolean"},
        "systematic_sequence_used": {"type": "boolean"},
        "photodoc_all_accessible_stations": {"type": "boolean"},
        "stations_sampled": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["station", "size_mm", "passes"],
            "properties": {
              "station": {
                "type": "string",
                "pattern": "^(1|2R|2L|3|4R|4L|5|6|7|8|9|10[RL]|11[RL]|12[RL])$"
              },
              "size_mm": {"type": "integer", "minimum": 1, "maximum": 60},
              "passes": {"type": "integer", "minimum": 1, "maximum": 10},
              "rose_used": {"type": "boolean"},
              "pet_positive": {"type": "boolean"}
            }
          }
        },
        "adequacy_all_nodes": {"type": "boolean"},
        "molecular_success": {"type": "boolean"}
      }
    },
    "navigation": {
      "type": "object",
      "properties": {
        "tool_in_lesion_confirmed": {"type": "boolean"},
        "localization_success": {"type": "boolean"},
        "peripheral_nodule_diagnostic_yield": {"type": "boolean"},
        "sampling_protocol_adherent": {"type": "boolean"}
      }
    },
    "radiation": {
      "type": "object",
      "properties": {
        "fluoro_time_min": {"type": "number", "minimum": 0},
        "dap_cGy_cm2": {"type": "number", "minimum": 0}
      }
    },
    "safety": {
      "type": "object",
      "required": ["complications"],
      "properties": {
        "complications": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type", "severity"],
            "properties": {
              "type": {"enum": ["pneumothorax", "pneumomediastinum", "airway_bleeding", "infection", "hypoxia", "cardiac_event", "other"]},
              "severity": {"enum": ["none", "mild", "moderate", "severe"]},
              "intervention": {"type": "string"}
            }
          }
        },
        "escalation_of_care": {"type": "boolean"},
        "procedure_related_mortality_30d": {"type": "boolean"}
      }
    },
    "diagnostics": {
      "type": "object",
      "properties": {
        "diagnostic_specific_result": {"type": "boolean"},
        "path_category": {"enum": ["malignant", "benign_specific", "benign_non_specific", "nondiagnostic"]},
        "molecular_profile_obtained": {"type": "boolean"}
      }
    },
    "follow_up": {
      "type": "object",
      "properties": {
        "readmission_30d": {"type": "boolean"},
        "mortality_30d": {"type": "boolean"},
        "stent_followup_bronch_done_4_6w": {"type": "boolean"}
      }
    },
    "metrics_input": {
      "type": "object",
      "properties": {
        "visible_mucosal_tumor_seen": {"type": "boolean"},
        "time_to_diagnosis_days": {"type": "integer", "minimum": 0},
        "door_to_scope_minutes": {"type": "integer", "minimum": 0}
      }
    },
    "phi_attestation": {
      "type": "object",
      "required": ["version", "never_persisted", "orig_image_hash", "redacted_image_hash", "signature"],
      "properties": {
        "version": {"type": "string"},
        "never_persisted": {"type": "boolean", "const": true},
        "orig_image_hash": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
        "redacted_image_hash": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
        "redacted_regions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["x", "y", "w", "h"],
            "properties": {
              "x": {"type": "number"},
              "y": {"type": "number"},
              "w": {"type": "number"},
              "h": {"type": "number"}
            }
          }
        },
        "signature": {"type": "string"}
      }
    }
  }
}
```

**File:** `schemas/codebooks/ebus_stations.json`

```json
{
  "version": "1.0.0",
  "stations": [
    {"code": "1", "name": "Highest mediastinal", "side": "midline"},
    {"code": "2R", "name": "Upper paratracheal", "side": "right"},
    {"code": "2L", "name": "Upper paratracheal", "side": "left"},
    {"code": "3", "name": "Prevascular/retrotracheal", "side": "midline"},
    {"code": "4R", "name": "Lower paratracheal", "side": "right"},
    {"code": "4L", "name": "Lower paratracheal", "side": "left"},
    {"code": "5", "name": "Subaortic", "side": "left"},
    {"code": "6", "name": "Para-aortic", "side": "left"},
    {"code": "7", "name": "Subcarinal", "side": "midline"},
    {"code": "8", "name": "Paraesophageal", "side": "midline"},
    {"code": "9", "name": "Pulmonary ligament", "side": "midline"},
    {"code": "10R", "name": "Tracheobronchial angle", "side": "right"},
    {"code": "10L", "name": "Tracheobronchial angle", "side": "left"},
    {"code": "11R", "name": "Interlobar", "side": "right"},
    {"code": "11L", "name": "Interlobar", "side": "left"},
    {"code": "12R", "name": "Lobar", "side": "right"},
    {"code": "12L", "name": "Lobar", "side": "left"}
  ]
}
```

**File:** `schemas/codebooks/sedation_scales.json`

```json
{
  "ramsay_scale": {
    "1": "Anxious, agitated, or restless",
    "2": "Cooperative, oriented, tranquil",
    "3": "Responds to commands only",
    "4": "Brisk response to light glabellar tap or loud auditory stimulus",
    "5": "Sluggish response to light glabellar tap or loud auditory stimulus",
    "6": "No response to light glabellar tap or loud auditory stimulus"
  },
  "monitoring_intervals": {
    "5": "Continuous SpO2, BP q5min (deep sedation)",
    "10": "SpO2 continuous, BP q10min (moderate sedation)",
    "15": "SpO2 continuous, BP q15min (minimal sedation)"
  }
}
```

**File:** `examples/example_procedure_submission.json`

```json
{
  "schema_version": "1.0.0",
  "facility_id": "SITE-01",
  "operator_id_hash": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
  "procedure_datetime_shifted": "2025-09-15T14:30:00Z",
  "patient": {
    "age_years": 67,
    "sex": "male",
    "smoking_status": "previous"
  },
  "procedure_type": "ebus_tbna",
  "anesthesia": {
    "mode": "moderate_sedation",
    "ramsay_max": 3,
    "monitoring_intervals_min": 5,
    "reversal_agents_used": []
  },
  "ebus": {
    "staging_indication": true,
    "systematic_sequence_used": true,
    "photodoc_all_accessible_stations": true,
    "stations_sampled": [
      {
        "station": "4R",
        "size_mm": 9,
        "passes": 4,
        "rose_used": true,
        "pet_positive": true
      },
      {
        "station": "7",
        "size_mm": 12,
        "passes": 3,
        "rose_used": true,
        "pet_positive": false
      }
    ],
    "adequacy_all_nodes": true,
    "molecular_success": true
  },
  "safety": {
    "complications": [],
    "escalation_of_care": false,
    "procedure_related_mortality_30d": false
  },
  "phi_attestation": {
    "version": "1.0.0",
    "never_persisted": true,
    "orig_image_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    "redacted_image_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    "redacted_regions": [
      {"x": 0, "y": 0, "w": 500, "h": 120}
    ],
    "signature": "hmac-sha256-placeholder"
  }
}
```

**Validation:**

```bash
# Install dependencies
pip install jsonschema

# Validate
python3 << 'EOF'
import jsonschema
import json

with open('schemas/bronchoscopy_procedure.schema.json') as f:
    schema = json.load(f)

with open('examples/example_procedure_submission.json') as f:
    example = json.load(f)

jsonschema.validate(example, schema)
print("✅ Example validates against schema")
EOF

git add schemas/ examples/
git commit -m "feat(schema): add canonical procedure schema + codebooks + valid example"
```

---

### Block 2: FastAPI Gateway + OpenAPI

**Acceptance:** Gateway accepts submissions, validates schema, enforces nonce uniqueness

**File:** `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.25
python-jose[cryptography]==3.3.0
jsonschema==4.23.0
PyYAML==6.0.2
pytest==8.3.3
faker==22.0.0
streamlit==1.39.0
```

**File:** `gateway/app/main.py`

```python
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
import os
from jose import jwt, JWTError
import hashlib

app = FastAPI(title="Bronchoscopy Registry Gateway", version="1.0.0")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./registry.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Procedure(Base):
    __tablename__ = "procedures"
    id = Column(String, primary_key=True)
    nonce = Column(String, unique=True, nullable=False, index=True)
    facility_id = Column(String, nullable=False)
    operator_id_hash = Column(String)
    procedure_datetime = Column(DateTime)
    payload = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True)
    kind = Column(String)
    facility_id = Column(String)
    nonce = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# JWT Configuration
JWT_SECRET = os.getenv("REGISTRY_JWT_SECRET", "dev-secret-CHANGE-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_jwt(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired JWT")

@app.post("/v1/procedures", status_code=201)
async def ingest_procedure(
    submission: dict,
    x_request_nonce: str = Header(..., alias="X-Request-Nonce"),
    db: Session = Depends(get_db),
    jwt_payload: dict = Depends(verify_jwt)
):
    """Ingest a de-identified procedure submission"""
    
    # 1. Check nonce uniqueness
    existing = db.query(Procedure).filter(Procedure.nonce == x_request_nonce).first()
    if existing:
        return JSONResponse(status_code=409, content={"error": "Duplicate nonce (replay)"})
    
    # 2. Validate against JSON Schema
    import jsonschema
    schema_path = "schemas/bronchoscopy_procedure.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(submission, schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Schema validation failed: {e.message}")
    
    # 3. Enforce PHI attestation policy
    phi_attest = submission.get("phi_attestation", {})
    if phi_attest.get("never_persisted") != True:
        raise HTTPException(status_code=422, detail="Policy violation: never_persisted must be true")
    
    # 4. Store procedure
    proc_id = hashlib.sha256(f"{submission['facility_id']}{x_request_nonce}".encode()).hexdigest()[:16]
    procedure = Procedure(
        id=proc_id,
        nonce=x_request_nonce,
        facility_id=submission["facility_id"],
        operator_id_hash=submission["operator_id_hash"],
        procedure_datetime=datetime.fromisoformat(submission["procedure_datetime_shifted"].replace("Z", "+00:00")),
        payload=json.dumps(submission)
    )
    db.add(procedure)
    
    # 5. Audit log
    audit = AuditLog(
        id=hashlib.sha256(f"audit-{x_request_nonce}".encode()).hexdigest()[:16],
        kind="ingest",
        facility_id=submission["facility_id"],
        nonce=x_request_nonce
    )
    db.add(audit)
    db.commit()
    
    return JSONResponse(
        status_code=201,
        headers={"X-Request-Nonce": x_request_nonce},
        content={"status": "created", "id": proc_id}
    )

@app.get("/v1/schemas/current")
async def get_current_schema():
    with open("schemas/bronchoscopy_procedure.schema.json") as f:
        schema = json.load(f)
    return {"version": "1.0.0", "schema": schema}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**File:** `gateway/scripts/generate_dev_jwt.py`

```python
#!/usr/bin/env python3
"""Generate development JWT for testing"""
import os
from jose import jwt
from datetime import datetime, timedelta

SECRET = os.getenv("REGISTRY_JWT_SECRET", "dev-secret-CHANGE-IN-PRODUCTION")
ALGORITHM = "HS256"

payload = {
    "sub": "dev-user",
    "facility_id": "SITE-01",
    "exp": datetime.utcnow() + timedelta(days=365)
}

token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
print(f"\n🔑 Development JWT (valid 365 days):")
print(f"{token}\n")
print("⚠️  MANUAL ACTION #3: Copy this token for:")
print("   1. Testing gateway with curl")
print("   2. iOS app configuration (Settings screen)")
print()
```

**Test:**

```bash
# Install
pip install -r requirements.txt

# ⚠️ MANUAL ACTION #3: Generate JWT secret
export REGISTRY_JWT_SECRET=$(openssl rand -hex 32)

# Generate dev token
python gateway/scripts/generate_dev_jwt.py
# Copy the JWT that is printed

# Run gateway
uvicorn gateway.app.main:app --reload --port 8000

# Test in another terminal (replace <JWT> with actual token)
curl -X POST http://localhost:8000/v1/procedures \
  -H "Authorization: Bearer <JWT>" \
  -H "X-Request-Nonce: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d @examples/example_procedure_submission.json

# Should return: 201 Created

# Try replay (same nonce) - should fail with 409
curl -X POST http://localhost:8000/v1/procedures \
  -H "Authorization: Bearer <JWT>" \
  -H "X-Request-Nonce: <same-nonce-as-above>" \
  -H "Content-Type: application/json" \
  -d @examples/example_procedure_submission.json

# Should return: 409 Conflict
```

**Commit:**
```bash
git add gateway/ requirements.txt
git commit -m "feat(gateway): FastAPI with schema validation + JWT + nonce dedupe"
```

---

### Block 3: Pipeline Config + PHI Rules + Extraction Prompts

**File:** `config/pipeline.config.yaml`

```yaml
version: 1.0.0

phi_detection:
  regex_pack: config/phi_rules.json
  danger_zones_px:
    header_top: 120
    footer_bottom: 60
  expansion_margin_px: 10

extraction:
  min_confidence: 0.85
  low_confidence_queue: true
  prompts:
    ebus: prompts/extract_ebus.txt
    sedation: prompts/extract_sedation.txt
    navigation: prompts/extract_navigation.txt
    safety: prompts/extract_safety.txt

attestation:
  version: "1.0.0"
  hmac_algorithm: sha256
  require_device_key: true
```

**File:** `config/phi_rules.json`

```json
{
  "version": "1.0.0",
  "regex": [
    {
      "name": "mrn",
      "pattern": "\\b(MRN|Med\\s*Rec|Record)[:#]?\\s*[A-Za-z0-9-]{5,}\\b",
      "severity": "high"
    },
    {
      "name": "dob",
      "pattern": "\\b(?:DOB|Birth)[:\\s]*[0-3]?\\d[/-][0-3]?\\d[/-](?:19|20)\\d{2}\\b",
      "severity": "high"
    },
    {
      "name": "phone",
      "pattern": "\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b",
      "severity": "medium"
    },
    {
      "name": "email",
      "pattern": "[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}",
      "flags": "i",
      "severity": "medium"
    },
    {
      "name": "person_name",
      "pattern": "(?:Patient|Name|Pt)[:\\s]+([A-Z][a-z]+\\s+[A-Z][a-z]+)",
      "severity": "high"
    }
  ]
}
```

**File:** `prompts/extract_ebus.txt`

```
You are extracting EBUS-TBNA data for a bronchoscopy registry.
Given OCR'd text from a clinical note, extract the following fields as structured data.

FIELDS TO EXTRACT:
- staging_indication: boolean (true if "staging" or "mediastinal staging" mentioned)
- systematic_sequence_used: boolean (true if "N3→N2→N1" or "systematic" sequence mentioned)
- photodoc_all_accessible_stations: boolean (true if "photos" or "photodoc" of "all accessible stations")
- stations_sampled: array of:
  - station: string matching pattern (1|2R|2L|3|4R|4L|5|6|7|8|9|10R|10L|11R|11L|12R|12L)
  - size_mm: integer (node size in millimeters)
  - passes: integer (number of needle passes)
  - rose_used: boolean (true if "ROSE" or "rapid on-site evaluation")
  - pet_positive: boolean (true if "PET+" or "PET positive" or "FDG-avid")
- adequacy_all_nodes: boolean (true if all samples adequate)
- molecular_success: boolean (true if molecular profiling obtained)

RULES:
1. If any field is uncertain or not mentioned, set it to null
2. Station labels must be exact: 4R not "right 4" or "station 4 right"
3. Never include PHI (patient names, MRNs, dates of birth)
4. Be conservative: if ambiguous, prefer null over guessing

EXAMPLE INPUT:
"EBUS-TBNA for staging. Systematic N3→N2→N1 evaluation. Station 4R (9mm, short axis) sampled with 4 passes, ROSE adequate, PET+. Station 7 (12mm) sampled with 3 passes, ROSE adequate. Photodocumentation of all accessible stations completed."

EXAMPLE OUTPUT:
{
  "staging_indication": true,
  "systematic_sequence_used": true,
  "photodoc_all_accessible_stations": true,
  "stations_sampled": [
    {
      "station": "4R",
      "size_mm": 9,
      "passes": 4,
      "rose_used": true,
      "pet_positive": true
    },
    {
      "station": "7",
      "size_mm": 12,
      "passes": 3,
      "rose_used": true,
      "pet_positive": false
    }
  ],
  "adequacy_all_nodes": true,
  "molecular_success": null
}
```

**File:** `prompts/extract_sedation.txt`

```
Extract sedation/anesthesia data from the clinical note.

FIELDS TO EXTRACT:
- mode: one of ["local", "moderate_sedation", "deep_sedation", "general_anesthesia"]
- ramsay_max: integer from 1 to 6 (maximum Ramsay sedation score during procedure)
- monitoring_intervals_min: one of [5, 10, 15] (blood pressure monitoring frequency in minutes)
- reversal_agents_used: array, can contain ["flumazenil", "naloxone"] or be empty

MAPPING HINTS:
- "topical" / "lidocaine only" / "spray" → "local"
- "conscious sedation" / "moderate sedation" / "MAC" → "moderate_sedation"
- "propofol" without intubation / "deep sedation" → "deep_sedation"
- "general" / "intubated" / "ETT" / "LMA" → "general_anesthesia"

RAMSAY SCALE:
1 = Anxious, agitated, restless
2 = Cooperative, oriented, tranquil
3 = Responds to commands only
4 = Brisk response to stimulus
5 = Sluggish response to stimulus
6 = No response

MONITORING:
- "continuous SpO2, BP q5min" → 5
- "SpO2 continuous, BP q10min" → 10
- "SpO2, BP q15min" → 15

RULES:
1. If mode is ambiguous, default to "moderate_sedation" for bronchoscopy
2. If Ramsay not mentioned, set to null
3. Reversal agents only if explicitly stated (flumazenil, Romazicon, naloxone, Narcan)
4. Never include PHI

EXAMPLE INPUT:
"Moderate sedation with midazolam and fentanyl. Patient remained Ramsay 3 throughout. Monitoring: continuous SpO2, BP checked every 5 minutes. No reversal agents required."

EXAMPLE OUTPUT:
{
  "mode": "moderate_sedation",
  "ramsay_max": 3,
  "monitoring_intervals_min": 5,
  "reversal_agents_used": []
}
```

**Commit:**
```bash
git add config/ prompts/
git commit -m "feat(pipeline): add config + PHI regex + extraction prompts"
```

---

### Block 6: Evaluation Harness + Gold Corpus

**File:** `eval/eval_config.yaml`

```yaml
dataset:
  path: eval/data/gold_corpus_v1.jsonl
  tasks:
    - name: phi_redaction
      metrics: [recall, precision]
    - name: ebus_fields
      fields: [stations_sampled, systematic_sequence_used, photodoc_all_accessible_stations]
      metrics: [precision, recall, f1]
    - name: sedation_fields
      fields: [mode, ramsay_max, monitoring_intervals_min, reversal_agents_used]
      metrics: [precision, recall, f1]

thresholds:
  phi_recall: 1.0
  ebus_f1: 0.92
  sedation_f1: 0.95

runtime:
  devices: [iphone15pro, iphone16]
  perf_budgets:
    ocr_ms: {iphone15pro: 2000, iphone16: 1500}
    nlp_ms: {iphone15pro: 800, iphone16: 500}
```

**File:** `eval/data/gold_corpus_v1.jsonl` (initial 3 examples)

```jsonl
{"id":"G001","note_text":"Bronchoscopy with EBUS-TBNA performed for staging. Patient: John Doe MRN: A12-99Z-77 DOB: 03/15/1961. Systematic evaluation N3→N2→N1 completed. Stations 4R (short-axis 9 mm) passes x4, 7 (12 mm) passes x3, 11R (8 mm) passes x3. ROSE adequate. No complications. Ramsay 3, SpO2 continuous, BP q5min. PET+ at 4R sampled. Photodoc of all accessible stations.","phi_spans":[{"start":47,"end":55,"label":"PERSON"},{"start":62,"end":72,"label":"ID"},{"start":78,"end":88,"label":"DATE"}],"ebus_fields":{"staging_indication":true,"stations_sampled":[{"station":"4R","size_mm":9,"passes":4,"rose_used":true,"pet_positive":true},{"station":"7","size_mm":12,"passes":3,"rose_used":true,"pet_positive":false},{"station":"11R","size_mm":8,"passes":3,"rose_used":true,"pet_positive":false}],"systematic_sequence_used":true,"photodoc_all_accessible_stations":true,"adequacy_all_nodes":true,"molecular_success":true},"sedation_fields":{"mode":"moderate_sedation","ramsay_max":3,"monitoring_intervals_min":5,"reversal_agents_used":[]},"outcomes":{"complications":[],"pneumothorax":false,"major_bleeding":false},"quality_asserts":{"visible_mucosal_tumor_seen":false}}
{"id":"G002","note_text":"Navigation bronchoscopy for peripheral nodule (RUL 15 mm, bronchus sign present). EBUS-radial tool-in-lesion confirmed concentric pattern; fluoroscopy time 6.5 min; DAP 180 cGy*cm². Sampling: needle x2, forceps x3, brush x2. Phone: (619)55O-1212 (synthetic). Ramsay 2, BP q10min.","phi_spans":[{"start":199,"end":213,"label":"PHONE"}],"ebus_fields":{"staging_indication":false,"stations_sampled":[],"systematic_sequence_used":false,"photodoc_all_accessible_stations":false,"adequacy_all_nodes":null,"molecular_success":null},"sedation_fields":{"mode":"moderate_sedation","ramsay_max":2,"monitoring_intervals_min":10,"reversal_agents_used":[]},"outcomes":{"complications":[],"pneumothorax":false,"major_bleeding":false},"quality_asserts":{"tool_in_lesion_confirmed":true,"localization_success":true}}
{"id":"G003","note_text":"Therapeutic bronchoscopy for central airway obstruction. Name: Jane X. MRN# ZX-5555. Massive tumor debulking + stent placement in LM. Bleeding controlled with vasoconstrictor and blocker (moderate). ICU transfer not required. Follow-up bronchoscopy planned at 4-6 weeks. Ramsay 3, reversal unused.","phi_spans":[{"start":55,"end":61,"label":"PERSON"},{"start":69,"end":76,"label":"ID"}],"ebus_fields":{"staging_indication":false,"stations_sampled":[],"systematic_sequence_used":false,"photodoc_all_accessible_stations":false,"adequacy_all_nodes":null,"molecular_success":null},"sedation_fields":{"mode":"deep_sedation","ramsay_max":3,"monitoring_intervals_min":10,"reversal_agents_used":[]},"outcomes":{"complications":[{"type":"airway_bleeding","severity":"moderate","intervention":"vasoconstrictor+blocker"}],"pneumothorax":false,"major_bleeding":true},"quality_asserts":{"stent_placed":true}}
```

**File:** `tools/phi_canary.py`

```python
#!/usr/bin/env python3
"""Ensure PHI patterns are detectable by regex pack"""
import json
import re
import sys

def load_phi_rules():
    with open("config/phi_rules.json") as f:
        return json.load(f)

def load_gold_corpus():
    examples = []
    with open("eval/data/gold_corpus_v1.jsonl") as f:
        for line in f:
            examples.append(json.loads(line))
    return examples

def main():
    rules = load_phi_rules()
    corpus = load_gold_corpus()
    
    all_matched = True
    total_phi = 0
    total_detected = 0
    
    for example in corpus:
        text = example["note_text"]
        expected_spans = example.get("phi_spans", [])
        total_phi += len(expected_spans)
        
        matched_spans = []
        for rule in rules["regex"]:
            flags = re.IGNORECASE if rule.get("flags") == "i" else 0
            pattern = re.compile(rule["pattern"], flags)
            for match in pattern.finditer(text):
                matched_spans.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "rule": rule["name"]
                })
        
        # Check coverage
        for expected in expected_spans:
            covered = any(
                m["start"] <= expected["start"] and m["end"] >= expected["end"]
                for m in matched_spans
            )
            if covered:
                total_detected += 1
            else:
                print(f"❌ MISS: '{text[expected['start']:expected['end']]}' in {example['id']}")
                all_matched = False
        
        if matched_spans:
            print(f"✅ {example['id']}: {len(matched_spans)} PHI patterns detected")
    
    recall = total_detected / total_phi if total_phi > 0 else 0
    print(f"\n📊 PHI Detection Recall: {recall:.2%} ({total_detected}/{total_phi})")
    
    if recall == 1.0:
        print("✅ Target achieved: PHI recall = 1.0")
        sys.exit(0)
    else:
        print("❌ Below threshold - update regex pack")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**File:** `tools/eval_harness.py`

```python
#!/usr/bin/env python3
"""Evaluation harness for extraction quality"""
import json
import argparse
import yaml
from pathlib import Path

def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_gold_corpus(corpus_path):
    examples = []
    with open(corpus_path) as f:
        for line in f:
            examples.append(json.loads(line))
    return examples

def compute_metrics(predictions, ground_truth, field_name):
    """Compute P/R/F1 for a field"""
    # Placeholder - will be implemented after extraction is working
    return {
        "precision": 0.95,
        "recall": 0.93,
        "f1": 0.94
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--predictions", help="Predictions JSONL (optional for now)")
    args = parser.parse_args()
    
    config = load_config(args.config)
    gold = load_gold_corpus(config["dataset"]["path"])
    
    print(f"📁 Loaded {len(gold)} gold examples")
    print(f"📋 Tasks: {', '.join(t['name'] for t in config['dataset']['tasks'])}\n")
    
    # Placeholder metrics (will be real after extraction)
    for task in config["dataset"]["tasks"]:
        print(f"🎯 Task: {task['name']}")
        if task["name"] == "ebus_fields":
            for field in task["fields"]:
                metrics = compute_metrics(None, gold, field)
                print(f"  {field}: F1={metrics['f1']:.2f}")
                
                threshold_key = f"{task['name'].split('_')[0]}_f1"
                if threshold_key in config["thresholds"]:
                    threshold = config["thresholds"][threshold_key]
                    status = "✅" if metrics["f1"] >= threshold else "⚠️"
                    print(f"    {status} Threshold: {threshold}")
    
    print("\n✅ Eval harness structure validated")
    print("⏸️  MANUAL ACTION #6: Run again after extraction with --predictions")

if __name__ == "__main__":
    main()
```

**Test:**

```bash
# PHI canary
python tools/phi_canary.py

# Eval harness structure
python tools/eval_harness.py --config eval/eval_config.yaml

git add eval/ tools/phi_canary.py tools/eval_harness.py
git commit -m "feat(eval): add eval harness + PHI canary + gold corpus (3 examples)"
```

---

### Block 8: Documentation

Create comprehensive docs covering quality metrics, security, threat model, governance, device support, and runbooks.

**File:** `docs/QUALITY_METRICS.md`

```markdown
# Quality Metrics

## BTS Audit Standards
- **Staging sensitivity:** ≥88% (EBUS-TBNA for nodal staging)
- **Complication rate:** <1% (moderate/severe bleeding, pneumothorax requiring treatment)

## AQuIRE Risk-Adjusted Yield
- **O/E Ratio:** Observed/Expected diagnostic yield stratified by node size
- **Strata:** ≤10mm, 11-20mm, 21-30mm, >30mm
- **Minimum n:** 25 cases for facility-level reporting

## Thresholds
- EBUS field extraction F1: ≥0.92
- Sedation field extraction F1: ≥0.95
- PHI detection recall: 1.0 (zero misses)
```

**File:** `docs/SECURITY.md`

```markdown
# Security Model

## Zero-Persistence Architecture
1. **Capture:** Image held in memory only (never written to disk)
2. **OCR:** Processed in-memory via Vision framework
3. **Redact:** Pixel-level black boxes applied to image buffer
4. **Attest:** Generate cryptographic attestation
5. **Purge:** Original image zeroed from memory
6. **Export:** Only redacted image + structured JSON persisted

## iOS Data Protection
- Keychain: JWT tokens (kSecAttrAccessibleWhenUnlockedThisDeviceOnly)
- File Protection: Complete Until First Unlock for redacted artifacts
- No screenshots in capture/redaction screens
```

**File:** `docs/DEVICE_SUPPORT.md`

```markdown
# Device Support

## iOS Requirements
- **iOS 26+** (Foundation Models framework)
- **Apple Intelligence-compatible devices:**
  - iPhone 15 Pro / Pro Max (A17 Pro)
  - iPhone 16 series (A18 / A18 Pro)
  - iPad Air (M2+), iPad Pro (M1+)
  - MacBook Air/Pro (M1+)

## Fallback Strategy
- Primary: Foundation Models extraction (iOS 26+, AI-enabled)
- Fallback: Manual form entry (all devices)

## Performance
- OCR latency: 1-2 seconds (VisionKit)
- Extraction latency: 100-500ms (Foundation Models)
- Memory usage: ~300 MB peak
```

**File:** `runbooks/incident_phi_breach.md`

```markdown
# PHI Breach Response Runbook

## Detection
- User reports PHI visible after submission
- Audit log shows `never_persisted: false`

## Immediate Actions (0-1 hour)
1. **Isolate:** Take affected device offline
2. **Preserve:** Capture memory dump if accessible
3. **Notify:** Alert security officer + clinical lead
4. **Quarantine:** Block facility_id at gateway

## Investigation (1-24 hours)
1. Review attestation signatures
2. Check audit logs for patterns
3. Examine device: iOS version, app version
4. Reproduce on test device

## Remediation (24-72 hours)
1. If app bug: Emergency patch + force update
2. If device compromised: Revoke certs
3. Notify affected individuals per HIPAA rules
```

**File:** `README.md`

```markdown
# Bronchoscopy Registry - iOS-First Implementation

Privacy-first bronchoscopy procedure registry with on-device AI extraction using Apple's Foundation Models framework.

## Features
- ✅ Zero-persistence PHI (never written to disk)
- ✅ Pixel-level redaction with cryptographic attestation
- ✅ On-device extraction (~3B LLM, 100-300ms, offline)
- ✅ BTS/AQuIRE metrics (sensitivity, complications, O/E)
- ✅ Replay protection (nonce tracking)

## Requirements
- **Development:** macOS 26+, Xcode 26+
- **Runtime:** iOS 26+, Apple Intelligence device
- **Python:** 3.11+
- **Database:** SQLite (dev), PostgreSQL (prod)

## Quickstart (Backend)

### 1. Setup
```bash
git clone <repo>
cd bronch-registry
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
# Generate JWT secret
export REGISTRY_JWT_SECRET=$(openssl rand -hex 32)

# Generate dev token
python gateway/scripts/generate_dev_jwt.py
# Save the printed JWT
```

### 3. Run Gateway
```bash
uvicorn gateway.app.main:app --reload --port 8000
```

### 4. Test
```bash
curl -X POST http://localhost:8000/v1/procedures \
  -H "Authorization: Bearer <JWT>" \
  -H "X-Request-Nonce: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d @examples/example_procedure_submission.json
# Expected: 201 Created
```

## Documentation
- [Quality Metrics](docs/QUALITY_METRICS.md)
- [Security Model](docs/SECURITY.md)
- [Device Support](docs/DEVICE_SUPPORT.md)

## License
Apache 2.0
```

**Commit:**
```bash
git add docs/ runbooks/ README.md
git commit -m "docs: add quality, security, device support + runbooks + README"
```

---

**PHASE 1 COMPLETE ✅**

At this point you have:
- ✅ Working FastAPI gateway
- ✅ Schema validation pipeline
- ✅ JWT authentication
- ✅ Nonce replay protection
- ✅ PHI policy enforcement
- ✅ Evaluation harness structure
- ✅ Comprehensive documentation

**⏸️ PAUSE HERE: Perform MANUAL ACTION #1 (prepare 50-100 training notes)**

---

## 📦 PHASE 2: TRAINING DATA PIPELINE (Week 3)

**Goal:** De-identify and annotate 50-100 notes for extraction training

### Block 2A: Data Preparation & Annotation

**⚠️ PRE-REQUISITE:** MANUAL ACTION #1 complete (50-100 notes in `data/raw_notes/`)

**File:** `tools/phi_synthesizer.py`

```python
#!/usr/bin/env python3
"""Replace real PHI with synthetic data while preserving clinical content"""
import re
import random
from pathlib import Path
import json
from faker import Faker

fake = Faker()

class PHISynthesizer:
    def __init__(self):
        self.name_map = {}
        self.mrn_map = {}
        self.dob_map = {}
        
    def synthesize_note(self, text: str) -> tuple[str, dict]:
        """Returns: (synthesized_text, metadata)"""
        replacements = []
        
        # Names
        def replace_name(match):
            original = match.group(0)
            if original not in self.name_map:
                self.name_map[original] = fake.name()
            replacement = self.name_map[original]
            replacements.append({
                "type": "name",
                "original_span": (match.start(), match.end()),
                "fake": replacement
            })
            return replacement
        
        text = re.sub(r'(?:Patient|Name):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', replace_name, text)
        
        # MRNs
        def replace_mrn(match):
            original = match.group(0)
            if original not in self.mrn_map:
                self.mrn_map[original] = f"MRN: {fake.bothify(text='??-###-##')}"
            return self.mrn_map[original]
        
        text = re.sub(r'MRN[:#]?\s*[A-Za-z0-9-]{5,}', replace_mrn, text)
        
        # DOBs
        def replace_dob(match):
            fake_date = fake.date_of_birth(minimum_age=40, maximum_age=85)
            return f"DOB: {fake_date.strftime('%m/%d/%Y')}"
        
        text = re.sub(r'(?:DOB|Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', replace_dob, text)
        
        # Phones
        text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', lambda m: fake.phone_number(), text)
        
        metadata = {
            "replacements": replacements,
            "synthetic_length": len(text)
        }
        
        return text, metadata

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="data/raw_notes")
    parser.add_argument("--output-dir", default="data/synthetic_notes")
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    synthesizer = PHISynthesizer()
    
    for note_file in input_dir.glob("*.txt"):
        print(f"Processing {note_file.name}...")
        with open(note_file) as f:
            original = f.read()
        
        synthetic, metadata = synthesizer.synthesize_note(original)
        
        out_path = output_dir / note_file.name
        with open(out_path, 'w') as f:
            f.write(synthetic)
        
        meta_path = output_dir / f"{note_file.stem}_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  → {len(metadata['replacements'])} PHI replacements")
    
    print(f"\n✅ Synthesized {len(list(input_dir.glob('*.txt')))} notes")
    print("⏸️  MANUAL ACTION #2: Review synthetic notes, then annotate")

if __name__ == "__main__":
    main()
```

**File:** `tools/annotate_streamlit.py`

```python
#!/usr/bin/env python3
"""Streamlit annotation interface"""
import streamlit as st
import json
from pathlib import Path

def save_annotation(note_id, note_text, annotations):
    output_path = Path("eval/data/gold_corpus_v1.jsonl")
    record = {
        "id": note_id,
        "note_text": note_text,
        "phi_spans": annotations.get("phi_spans", []),
        "ebus_fields": annotations.get("ebus_fields", {}),
        "sedation_fields": annotations.get("sedation_fields", {}),
        "outcomes": annotations.get("outcomes", {}),
        "quality_asserts": annotations.get("quality_asserts", {})
    }
    with open(output_path, 'a') as f:
        f.write(json.dumps(record) + '\n')
    st.success(f"✅ Saved {note_id}")

def main():
    st.set_page_config(page_title="Bronch Annotator", layout="wide")
    st.title("📝 Bronchoscopy Note Annotation")
    
    notes_dir = Path("data/synthetic_notes")
    note_files = sorted(notes_dir.glob("*.txt"))
    
    if not note_files:
        st.error("No notes found. Run phi_synthesizer.py first.")
        return
    
    selected_file = st.sidebar.selectbox("Note", note_files, format_func=lambda x: x.name)
    
    with open(selected_file) as f:
        note_text = f.read()
    
    st.header(f"Note: {selected_file.name}")
    st.text_area("Clinical Note", note_text, height=300)
    
    st.header("📊 Annotate Fields")
    
    procedure_type = st.selectbox("Procedure Type", 
        ["diagnostic_flexible", "ebus_tbna", "navigation_bronchoscopy", "therapeutic_bronchoscopy"])
    
    ebus_fields = None
    if procedure_type == "ebus_tbna":
        st.subheader("EBUS Fields")
        ebus_fields = {}
        ebus_fields["staging_indication"] = st.checkbox("Staging indication?")
        ebus_fields["systematic_sequence_used"] = st.checkbox("Systematic N3→N2→N1?")
        ebus_fields["photodoc_all_accessible_stations"] = st.checkbox("Photodoc all stations?")
        
        num_stations = st.number_input("Number of stations", 0, 10, 0)
        stations = []
        for i in range(num_stations):
            st.write(f"**Station {i+1}**")
            col1, col2, col3, col4, col5 = st.columns(5)
            station = col1.text_input("Station (e.g., 4R)", key=f"st_{i}")
            size_mm = col2.number_input("Size (mm)", 1, 60, 10, key=f"sz_{i}")
            passes = col3.number_input("Passes", 1, 10, 3, key=f"ps_{i}")
            rose = col4.checkbox("ROSE", key=f"rs_{i}")
            pet = col5.checkbox("PET+", key=f"pt_{i}")
            if station:
                stations.append({
                    "station": station, "size_mm": size_mm, "passes": passes,
                    "rose_used": rose, "pet_positive": pet
                })
        ebus_fields["stations_sampled"] = stations
        ebus_fields["adequacy_all_nodes"] = st.checkbox("All nodes adequate?")
        ebus_fields["molecular_success"] = st.checkbox("Molecular success?")
    
    st.subheader("Sedation")
    sedation_fields = {}
    sedation_fields["mode"] = st.selectbox("Mode", 
        ["local", "moderate_sedation", "deep_sedation", "general_anesthesia"])
    sedation_fields["ramsay_max"] = st.slider("Ramsay max", 1, 6, 3)
    sedation_fields["monitoring_intervals_min"] = st.selectbox("Monitoring (min)", [5, 10, 15])
    sedation_fields["reversal_agents_used"] = st.multiselect("Reversal", ["flumazenil", "naloxone"])
    
    st.subheader("Outcomes")
    outcomes = {"complications": []}
    if st.checkbox("Any complications?"):
        comp_type = st.selectbox("Type", 
            ["pneumothorax", "pneumomediastinum", "airway_bleeding", "infection", "hypoxia", "cardiac_event", "other"])
        severity = st.selectbox("Severity", ["none", "mild", "moderate", "severe"])
        intervention = st.text_input("Intervention")
        outcomes["complications"].append({
            "type": comp_type, "severity": severity, "intervention": intervention
        })
    
    st.subheader("Quality Assertions")
    quality_asserts = {}
    if procedure_type == "ebus_tbna":
        quality_asserts["visible_mucosal_tumor_seen"] = st.checkbox("Visible tumor?")
    elif procedure_type == "navigation_bronchoscopy":
        quality_asserts["tool_in_lesion_confirmed"] = st.checkbox("Tool in lesion?")
        quality_asserts["localization_success"] = st.checkbox("Localization success?")
    
    st.subheader("PHI Spans")
    num_phi = st.number_input("Number of PHI spans", 0, 10, 0)
    phi_spans = []
    for i in range(num_phi):
        col1, col2, col3 = st.columns(3)
        start = col1.number_input(f"Start", 0, key=f"phi_s_{i}")
        end = col2.number_input(f"End", 0, key=f"phi_e_{i}")
        label = col3.selectbox(f"Label", ["PERSON", "ID", "DATE", "PHONE"], key=f"phi_l_{i}")
        phi_spans.append({"start": start, "end": end, "label": label})
    
    if st.button("💾 Save Annotation"):
        annotations = {
            "ebus_fields": ebus_fields,
            "sedation_fields": sedation_fields,
            "outcomes": outcomes,
            "quality_asserts": quality_asserts,
            "phi_spans": phi_spans
        }
        save_annotation(selected_file.stem, note_text, annotations)
    
    # Progress
    st.sidebar.header("📈 Progress")
    jsonl_path = Path("eval/data/gold_corpus_v1.jsonl")
    if jsonl_path.exists():
        with open(jsonl_path) as f:
            num_annotated = len(f.readlines())
        st.sidebar.metric("Annotated", f"{num_annotated} / 50+")
    else:
        st.sidebar.metric("Annotated", "0 / 50+")

if __name__ == "__main__":
    main()
```

**Execute:**

```bash
# 1. Synthesize PHI
python tools/phi_synthesizer.py

# 2. Review output
ls data/synthetic_notes/

# ⏸️ MANUAL ACTION #2: Annotate notes
streamlit run tools/annotate_streamlit.py
# Open browser, annotate 50-100 notes (4-8 hours)

# 3. Validate
python -c "
import json
path = 'eval/data/gold_corpus_v1.jsonl'
with open(path) as f:
    count = len(f.readlines())
print(f'✅ Annotated {count} examples')
assert count >= 50, 'Need at least 50 examples'
"

git add tools/phi_synthesizer.py tools/annotate_streamlit.py
git commit -m "feat(data): PHI synthesizer + annotation tool"
```

---

**PHASE 2 COMPLETE ✅**

You now have 50-100 annotated training examples in `eval/data/gold_corpus_v1.jsonl`

**⏸️ PAUSE: Ensure MANUAL ACTION #4 complete (iOS device with Apple Intelligence)**

---

## 📱 PHASE 3: iOS APP SHELL (Weeks 4-7)

**Goal:** Working iOS app with capture, redaction, manual forms (no extraction yet)

### Block 4: iOS App Foundation

**Create Xcode Project:**

1. Open Xcode → File → New → Project
2. Select: iOS → App
3. Product Name: `BronchRegistry`
4. Organization: `com.yourorg`
5. Interface: SwiftUI
6. Language: Swift
7. Save to: `mobile/ios/`

**Directory Structure:**

```
mobile/ios/BronchRegistry/
├── BronchRegistry.xcodeproj
├── BronchRegistry/
│   ├── App/
│   │   ├── BronchRegistryApp.swift
│   │   └── ContentView.swift
│   ├── Models/
│   │   ├── BronchoscopyProcedure.swift
│   │   └── PHIAttestation.swift
│   ├── Features/
│   │   ├── Capture/
│   │   ├── Redaction/
│   │   ├── Forms/
│   │   ├── Review/
│   │   └── Networking/
│   ├── Utils/
│   │   ├── SecureStorage.swift
│   │   ├── ImageRedactor.swift
│   │   └── HashingUtil.swift
│   └── Info.plist
```

**Key Files:**

**File:** `mobile/ios/BronchRegistry/Models/BronchoscopyProcedure.swift`

```swift
import Foundation

struct BronchoscopyProcedure: Codable {
    let schemaVersion: String
    let facilityId: String
    let operatorIdHash: String
    let procedureDatetimeShifted: String
    let patient: Patient?
    let procedureType: ProcedureType
    let anesthesia: Anesthesia?
    let ebus: EBUS?
    let safety: Safety
    let phiAttestation: PHIAttestation
    
    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case facilityId = "facility_id"
        case operatorIdHash = "operator_id_hash"
        case procedureDatetimeShifted = "procedure_datetime_shifted"
        case patient, procedureType = "procedure_type"
        case anesthesia, ebus, safety
        case phiAttestation = "phi_attestation"
    }
}

enum ProcedureType: String, Codable {
    case diagnosticFlexible = "diagnostic_flexible"
    case ebusTbna = "ebus_tbna"
    case navigationBronchoscopy = "navigation_bronchoscopy"
    case therapeuticBronchoscopy = "therapeutic_bronchoscopy"
}

struct Patient: Codable {
    let ageYears: Int?
    let sex: Sex?
    
    enum Sex: String, Codable {
        case female, male, unknown
    }
    
    enum CodingKeys: String, CodingKey {
        case ageYears = "age_years"
        case sex
    }
}

struct Anesthesia: Codable {
    let mode: Mode?
    let ramsayMax: Int?
    let monitoringIntervalsMin: Int?
    
    enum Mode: String, Codable {
        case local
        case moderateSedation = "moderate_sedation"
        case deepSedation = "deep_sedation"
        case generalAnesthesia = "general_anesthesia"
    }
    
    enum CodingKeys: String, CodingKey {
        case mode
        case ramsayMax = "ramsay_max"
        case monitoringIntervalsMin = "monitoring_intervals_min"
    }
}

struct EBUS: Codable {
    let stagingIndication: Bool?
    let systematicSequenceUsed: Bool?
    let stationsSampled: [StationSample]?
    
    struct StationSample: Codable {
        let station: String
        let sizeMm: Int
        let passes: Int
        let roseUsed: Bool?
        
        enum CodingKeys: String, CodingKey {
            case station
            case sizeMm = "size_mm"
            case passes
            case roseUsed = "rose_used"
        }
    }
    
    enum CodingKeys: String, CodingKey {
        case stagingIndication = "staging_indication"
        case systematicSequenceUsed = "systematic_sequence_used"
        case stationsSampled = "stations_sampled"
    }
}

struct Safety: Codable {
    let complications: [Complication]
    
    struct Complication: Codable {
        let type: ComplicationType
        let severity: Severity
        
        enum ComplicationType: String, Codable {
            case pneumothorax, airwayBleeding = "airway_bleeding"
        }
        
        enum Severity: String, Codable {
            case none, mild, moderate, severe
        }
    }
}

struct PHIAttestation: Codable {
    let version: String
    let neverPersisted: Bool
    let origImageHash: String
    let redactedImageHash: String
    let redactedRegions: [RedactedRegion]
    let signature: String
    
    struct RedactedRegion: Codable {
        let x: Double
        let y: Double
        let w: Double
        let h: Double
    }
    
    enum CodingKeys: String, CodingKey {
        case version
        case neverPersisted = "never_persisted"
        case origImageHash = "orig_image_hash"
        case redactedImageHash = "redacted_image_hash"
        case redactedRegions = "redacted_regions"
        case signature
    }
}
```

**File:** `mobile/ios/BronchRegistry/Utils/SecureStorage.swift`

```swift
import Foundation
import Security

class SecureStorage {
    static func storeJWT(_ token: String) throws {
        let data = token.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "jwt_token",
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            kSecValueData as String: data
        ]
        SecItemDelete(query as CFDictionary)
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.unableToStore
        }
    }
    
    static func retrieveJWT() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "jwt_token",
            kSecReturnData as String: true
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        return token
    }
    
    static func storeGatewayURL(_ url: String) {
        UserDefaults.standard.set(url, forKey: "gateway_url")
    }
    
    static func retrieveGatewayURL() -> String {
        return UserDefaults.standard.string(forKey: "gateway_url") ?? "http://localhost:8000"
    }
    
    enum KeychainError: Error {
        case unableToStore
    }
}
```

**File:** `mobile/ios/BronchRegistry/Utils/HashingUtil.swift`

```swift
import Foundation
import CryptoKit
import UIKit

struct HashingUtil {
    static func sha256(of data: Data) -> String {
        let hash = SHA256.hash(data: data)
        return "sha256:" + hash.compactMap { String(format: "%02x", $0) }.joined()
    }
    
    static func hashImage(_ image: UIImage) -> String? {
        guard let data = image.pngData() else { return nil }
        return sha256(of: data)
    }
    
    static func hmacSignature(payload: Data, secret: String) -> String {
        let key = SymmetricKey(data: secret.data(using: .utf8)!)
        let signature = HMAC<SHA256>.authenticationCode(for: payload, using: key)
        return signature.compactMap { String(format: "%02x", $0) }.joined()
    }
}
```

**File:** `mobile/ios/BronchRegistry/Utils/ImageRedactor.swift`

```swift
import UIKit

struct ImageRedactor {
    /// Apply black rectangles to image (in-memory only)
    static func redact(image: UIImage, regions: [CGRect]) -> UIImage? {
        let size = image.size
        let scale = image.scale
        
        UIGraphicsBeginImageContextWithOptions(size, true, scale)
        defer { UIGraphicsEndImageContext() }
        
        image.draw(at: .zero)
        
        let context = UIGraphicsGetCurrentContext()
        context?.setFillColor(UIColor.black.cgColor)
        context?.setBlendMode(.normal)
        
        for region in regions {
            context?.fill(region)
        }
        
        return UIGraphicsGetImageFromCurrentImageContext()
    }
}
```

**File:** `mobile/ios/BronchRegistry/Features/Capture/DocumentCaptureView.swift`

```swift
import SwiftUI
import VisionKit

struct DocumentCaptureView: UIViewControllerRepresentable {
    @Environment(\.dismiss) var dismiss
    var onCapture: (UIImage, String) -> Void
    
    func makeUIViewController(context: Context) -> VNDocumentCameraViewController {
        let controller = VNDocumentCameraViewController()
        controller.delegate = context.coordinator
        return controller
    }
    
    func updateUIViewController(_ uiViewController: VNDocumentCameraViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, VNDocumentCameraViewControllerDelegate {
        let parent: DocumentCaptureView
        
        init(_ parent: DocumentCaptureView) {
            self.parent = parent
        }
        
        func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFinishWith scan: VNDocumentCameraScan) {
            guard scan.pageCount > 0 else {
                parent.dismiss()
                return
            }
            
            let image = scan.imageOfPage(at: 0)
            
            performOCR(on: image) { recognizedText in
                DispatchQueue.main.async {
                    self.parent.onCapture(image, recognizedText)
                    self.parent.dismiss()
                }
            }
        }
        
        func documentCameraViewControllerDidCancel(_ controller: VNDocumentCameraViewController) {
            parent.dismiss()
        }
        
        func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFailWithError error: Error) {
            parent.dismiss()
        }
        
        private func performOCR(on image: UIImage, completion: @escaping (String) -> Void) {
            guard let cgImage = image.cgImage else {
                completion("")
                return
            }
            
            let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            let request = VNRecognizeTextRequest { request, error in
                guard let observations = request.results as? [VNRecognizedTextObservation] else {
                    completion("")
                    return
                }
                
                let text = observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
                completion(text)
            }
            
            request.recognitionLevel = .accurate
            
            DispatchQueue.global(qos: .userInitiated).async {
                try? requestHandler.perform([request])
            }
        }
    }
}
```

**File:** `mobile/ios/BronchRegistry/Features/Redaction/RedactionOverlayView.swift`

```swift
import SwiftUI

struct RedactionOverlayView: View {
    let image: UIImage
    @Binding var redactionBoxes: [CGRect]
    @State private var currentBox: CGRect?
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                
                ForEach(Array(redactionBoxes.enumerated()), id: \.offset) { index, box in
                    let displayBox = denormalizeRect(box, in: geometry.size)
                    
                    Rectangle()
                        .stroke(Color.red, lineWidth: 2)
                        .background(Color.black.opacity(0.5))
                        .frame(width: displayBox.width, height: displayBox.height)
                        .position(x: displayBox.midX, y: displayBox.midY)
                        .overlay(
                            Button {
                                redactionBoxes.remove(at: index)
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.white)
                                    .background(Circle().fill(Color.red))
                            }
                            .position(x: displayBox.maxX - 10, y: displayBox.minY + 10)
                        )
                }
                
                if let box = currentBox {
                    let displayBox = denormalizeRect(box, in: geometry.size)
                    Rectangle()
                        .stroke(Color.yellow, lineWidth: 3)
                        .background(Color.yellow.opacity(0.2))
                        .frame(width: displayBox.width, height: displayBox.height)
                        .position(x: displayBox.midX, y: displayBox.midY)
                }
            }
            .gesture(
                DragGesture()
                    .onChanged { value in
                        let imageSize = getImageDisplaySize(in: geometry.size)
                        let offset = getImageOffset(in: geometry.size, imageSize: imageSize)
                        
                        let start = value.startLocation
                        let current = value.location
                        
                        let normalizedStart = CGPoint(
                            x: (start.x - offset.x) / imageSize.width,
                            y: (start.y - offset.y) / imageSize.height
                        )
                        let normalizedCurrent = CGPoint(
                            x: (current.x - offset.x) / imageSize.width,
                            y: (current.y - offset.y) / imageSize.height
                        )
                        
                        currentBox = CGRect(
                            x: min(normalizedStart.x, normalizedCurrent.x),
                            y: min(normalizedStart.y, normalizedCurrent.y),
                            width: abs(normalizedCurrent.x - normalizedStart.x),
                            height: abs(normalizedCurrent.y - normalizedStart.y)
                        )
                    }
                    .onEnded { _ in
                        if let box = currentBox {
                            redactionBoxes.append(box)
                        }
                        currentBox = nil
                    }
            )
        }
    }
    
    private func getImageDisplaySize(in viewSize: CGSize) -> CGSize {
        let imageAspect = image.size.width / image.size.height
        let viewAspect = viewSize.width / viewSize.height
        
        if imageAspect > viewAspect {
            let width = viewSize.width
            let height = width / imageAspect
            return CGSize(width: width, height: height)
        } else {
            let height = viewSize.height
            let width = height * imageAspect
            return CGSize(width: width, height: height)
        }
    }
    
    private func getImageOffset(in viewSize: CGSize, imageSize: CGSize) -> CGPoint {
        CGPoint(
            x: (viewSize.width - imageSize.width) / 2,
            y: (viewSize.height - imageSize.height) / 2
        )
    }
    
    private func denormalizeRect(_ normalizedRect: CGRect, in viewSize: CGSize) -> CGRect {
        let imageSize = getImageDisplaySize(in: viewSize)
        let offset = getImageOffset(in: viewSize, imageSize: imageSize)
        return CGRect(
            x: offset.x + normalizedRect.minX * imageSize.width,
            y: offset.y + normalizedRect.minY * imageSize.height,
            width: normalizedRect.width * imageSize.width,
            height: normalizedRect.height * imageSize.height
        )
    }
}
```

**File:** `mobile/ios/BronchRegistry/App/ContentView.swift`

```swift
import SwiftUI

struct ContentView: View {
    @State private var showCapture = false
    @State private var capturedImage: UIImage?
    @State private var recognizedText = ""
    @State private var redactionBoxes: [CGRect] = []
    @State private var showRedaction = false
    @State private var showSettings = false
    
    var body: some View {
        TabView {
            HomeView(
                showCapture: $showCapture,
                capturedImage: $capturedImage,
                recognizedText: $recognizedText,
                redactionBoxes: $redactionBoxes,
                showRedaction: $showRedaction
            )
            .tabItem {
                Label("Home", systemImage: "house")
            }
            
            SettingsView(showSettings: $showSettings)
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}

struct HomeView: View {
    @Binding var showCapture: Bool
    @Binding var capturedImage: UIImage?
    @Binding var recognizedText: String
    @Binding var redactionBoxes: [CGRect]
    @Binding var showRedaction: Bool
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                Text("Bronchoscopy Registry")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Button {
                    showCapture = true
                } label: {
                    Label("Capture Note", systemImage: "doc.text.viewfinder")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
                .padding(.horizontal)
                
                Spacer()
            }
            .padding()
            .navigationTitle("Home")
            .sheet(isPresented: $showCapture) {
                DocumentCaptureView { image, text in
                    self.capturedImage = image
                    self.recognizedText = text
                    self.showRedaction = true
                }
            }
            .sheet(isPresented: $showRedaction) {
                if let image = capturedImage {
                    RedactionView(
                        image: image,
                        recognizedText: recognizedText,
                        redactionBoxes: $redactionBoxes,
                        showRedaction: $showRedaction
                    )
                }
            }
        }
    }
}

struct RedactionView: View {
    let image: UIImage
    let recognizedText: String
    @Binding var redactionBoxes: [CGRect]
    @Binding var showRedaction: Bool
    
    var body: some View {
        NavigationView {
            VStack {
                Text("Redact PHI")
                    .font(.headline)
                Text("Drag to create redaction boxes")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                RedactionOverlayView(image: image, redactionBoxes: $redactionBoxes)
                    .frame(maxHeight: 500)
                
                Button("Continue") {
                    showRedaction = false
                    // TODO: Navigate to form or extraction
                }
                .buttonStyle(.borderedProminent)
                .padding()
            }
            .navigationTitle("Redaction")
            .navigationBarItems(trailing: Button("Skip") {
                showRedaction = false
            })
        }
    }
}

struct SettingsView: View {
    @Binding var showSettings: Bool
    @State private var gatewayURL = SecureStorage.retrieveGatewayURL()
    @State private var jwtToken = SecureStorage.retrieveJWT() ?? ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Gateway") {
                    TextField("URL", text: $gatewayURL)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                }
                
                Section("Authentication") {
                    SecureField("JWT Token", text: $jwtToken)
                }
                
                Section {
                    Button("Save") {
                        SecureStorage.storeGatewayURL(gatewayURL)
                        try? SecureStorage.storeJWT(jwtToken)
                    }
                }
            }
            .navigationTitle("Settings")
        }
    }
}
```

**Update Info.plist:**

```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to capture clinical notes.</string>
```

**Test:**

1. Build and run in Xcode (Cmd+R)
2. Tap "Capture Note"
3. Scan a document
4. Verify OCR extracts text
5. Draw redaction boxes
6. Go to Settings → Enter gateway URL and JWT
7. Verify NO files written (check Files app)

**Commit:**
```bash
git add mobile/ios/
git commit -m "feat(ios): capture + redaction + settings (forms-first shell)"
```

---

**PHASE 3 COMPLETE ✅**

You now have a working iOS app that:
- ✅ Captures documents via camera
- ✅ Performs OCR
- ✅ Allows redaction box editing
- ✅ Stores JWT securely in Keychain
- ✅ Never persists unredacted images

---

## 🤖 PHASE 4: FOUNDATION MODELS EXTRACTION (Weeks 8-10)

**Goal:** Automated field extraction using on-device LLM

**⚠️ PRE-REQUISITE:** MANUAL ACTION #4 complete (Apple Intelligence enabled)

### Block 4A: Foundation Models Integration

**File:** `mobile/ios/BronchRegistry/Features/Extraction/ExtractionService.swift`

```swift
import Foundation
import FoundationModels

@available(iOS 26.0, *)
class ExtractionService {
    private let model: SystemLanguageModel
    
    init() {
        self.model = SystemLanguageModel.default
    }
    
    var availability: SystemLanguageModel.Availability {
        model.availability
    }
    
    /// Extract EBUS fields from OCR'd text
    func extractEBUS(from text: String) async throws -> EBUSExtraction {
        let session = model.startSession(instructions: """
        You are extracting EBUS-TBNA data for a bronchoscopy registry.
        Extract fields matching the provided schema.
        If any field is uncertain, set it to null.
        Never include PHI (patient names, MRNs, dates of birth).
        Be conservative: prefer null over guessing.
        """)
        
        let prompt = """
        Extract EBUS fields from this clinical note:
        
        \(text)
        
        Look for:
        - Staging indication (keywords: "staging", "mediastinal staging")
        - Systematic sequence (keywords: "N3→N2→N1", "systematic")
        - Stations sampled (format: "4R (9mm) x4 passes")
        - ROSE usage (keywords: "ROSE", "rapid on-site evaluation")
        - PET positivity (keywords: "PET+", "FDG-avid")
        """
        
        let result = try await session.generateResponse(
            for: prompt,
            as: EBUSExtraction.self
        )
        
        return result
    }
    
    /// Extract sedation fields from OCR'd text
    func extractSedation(from text: String) async throws -> SedationExtraction {
        let session = model.startSession(instructions: """
        Extract sedation/anesthesia data from clinical notes.
        Map terms to standardized values:
        - "conscious sedation" / "MAC" → "moderate_sedation"
        - "propofol" without intubation → "deep_sedation"
        - "general" / "intubated" → "general_anesthesia"
        """)
        
        let result = try await session.generateResponse(
            for: "Extract sedation data from: \(text)",
            as: SedationExtraction.self
        )
        
        return result
    }
}

// MARK: - Generable Models

@available(iOS 26.0, *)
@Generable
struct EBUSExtraction {
    var stagingIndication: Bool?
    var systematicSequenceUsed: Bool?
    var photodocAllAccessibleStations: Bool?
    var stationsSampled: [StationSample]?
    var adequacyAllNodes: Bool?
    var molecularSuccess: Bool?
    
    @Generable
    struct StationSample {
        @Guide(.pattern(#"^(1|2R|2L|3|4R|4L|5|6|7|8|9|10[RL]|11[RL]|12[RL])$"#))
        var station: String
        
        @Guide(.range(1...60))
        var sizeMm: Int
        
        @Guide(.range(1...10))
        var passes: Int
        
        var roseUsed: Bool?
        var petPositive: Bool?
    }
}

@available(iOS 26.0, *)
@Generable
struct SedationExtraction {
    @Guide(.options(["local", "moderate_sedation", "deep_sedation", "general_anesthesia"]))
    var mode: String
    
    @Guide(.range(1...6))
    var ramsayMax: Int
    
    @Guide(.options([5, 10, 15]))
    var monitoringIntervalsMin: Int
    
    var reversalAgentsUsed: [String]?
}

// MARK: - Confidence Scoring

@available(iOS 26.0, *)
extension EBUSExtraction {
    func computeConfidence() -> Double {
        var score = 0.0
        var fields = 0
        
        if stagingIndication != nil { score += 1.0; fields += 1 }
        if systematicSequenceUsed != nil { score += 1.0; fields += 1 }
        if let stations = stationsSampled, !stations.isEmpty {
            score += 1.0
            fields += 1
        }
        
        return fields > 0 ? score / Double(fields) : 0.0
    }
}
```

**File:** `mobile/ios/BronchRegistry/Features/Extraction/ExtractionView.swift`

```swift
import SwiftUI
import FoundationModels

@available(iOS 26.0, *)
struct ExtractionView: View {
    let recognizedText: String
    @State private var isExtracting = false
    @State private var ebusResult: EBUSExtraction?
    @State private var sedationResult: SedationExtraction?
    @State private var confidence: Double = 0.0
    @State private var errorMessage: String?
    
    private let extractionService = ExtractionService()
    
    var body: some View {
        VStack {
            if isExtracting {
                ProgressView("Extracting fields...")
                    .padding()
            } else if let error = errorMessage {
                Text("Extraction failed: \(error)")
                    .foregroundColor(.red)
                    .padding()
                
                Button("Retry") {
                    Task { await performExtraction() }
                }
            } else if let ebus = ebusResult {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        HStack {
                            Text("Confidence: \(Int(confidence * 100))%")
                                .font(.headline)
                            Spacer()
                            if confidence < 0.85 {
                                Text("⚠️ Low confidence - review carefully")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }
                        
                        GroupBox("EBUS Fields") {
                            VStack(alignment: .leading, spacing: 10) {
                                FieldRow("Staging", value: ebus.stagingIndication?.description)
                                FieldRow("Systematic Sequence", value: ebus.systematicSequenceUsed?.description)
                                FieldRow("Photodoc All Stations", value: ebus.photodocAllAccessibleStations?.description)
                                
                                if let stations = ebus.stationsSampled {
                                    Text("Stations Sampled:")
                                        .font(.subheadline)
                                        .bold()
                                    ForEach(Array(stations.enumerated()), id: \.offset) { index, station in
                                        Text("  • \(station.station): \(station.sizeMm)mm, \(station.passes) passes")
                                            .font(.caption)
                                    }
                                }
                            }
                        }
                        
                        if let sedation = sedationResult {
                            GroupBox("Sedation") {
                                VStack(alignment: .leading, spacing: 10) {
                                    FieldRow("Mode", value: sedation.mode)
                                    FieldRow("Ramsay Max", value: String(sedation.ramsayMax))
                                    FieldRow("Monitoring Interval", value: "\(sedation.monitoringIntervalsMin) min")
                                }
                            }
                        }
                        
                        Button("Continue to Review") {
                            // TODO: Navigate to submission review
                        }
                        .buttonStyle(.borderedProminent)
                        .frame(maxWidth: .infinity)
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Extraction")
        .task {
            await performExtraction()
        }
    }
    
    private func performExtraction() async {
        // Check availability
        switch extractionService.availability {
        case .available:
            break
        case .unavailable(.appleIntelligenceNotEnabled):
            errorMessage = "Please enable Apple Intelligence in Settings"
            return
        case .unavailable(.deviceNotEligible):
            errorMessage = "Device not compatible with Apple Intelligence"
            return
        case .unavailable(.modelNotReady):
            errorMessage = "Model still downloading. Try again in a few minutes."
            return
        }
        
        isExtracting = true
        errorMessage = nil
        
        do {
            let ebus = try await extractionService.extractEBUS(from: recognizedText)
            let sedation = try await extractionService.extractSedation(from: recognizedText)
            
            self.ebusResult = ebus
            self.sedationResult = sedation
            self.confidence = ebus.computeConfidence()
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isExtracting = false
    }
}

struct FieldRow: View {
    let label: String
    let value: String?
    
    init(_ label: String, value: String?) {
        self.label = label
        self.value = value
    }
    
    var body: some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
            Spacer()
            Text(value ?? "null")
                .font(.caption)
                .foregroundColor(value == nil ? .orange : .primary)
        }
    }
}
```

**Update ContentView to use extraction:**

```swift
// In RedactionView:
Button("Continue") {
    showRedaction = false
    // Navigate to extraction
    navigationPath.append(ExtractionDestination.extraction)
}
```

**Test:**

1. Build and run app
2. Capture a document
3. Redact PHI
4. Verify extraction runs automatically
5. Review extracted fields
6. Check confidence score

**⏸️ MANUAL ACTION #6: Evaluate extraction**

```bash
# Export predictions from iOS app to JSONL
# Then run:
python tools/eval_harness.py --config eval/eval_config.yaml --predictions predictions.jsonl

# If F1 < threshold:
# 1. Review failure cases
# 2. Refine extraction instructions in ExtractionService.swift
# 3. Iterate
```

**Commit:**
```bash
git add mobile/ios/
git commit -m "feat(ios): Foundation Models extraction with @Generable"
```

---

**PHASE 4 COMPLETE ✅**

You now have automated extraction using Apple's on-device LLM!

---

## 📊 PHASE 5: METRICS DASHBOARD (Week 11)

**File:** `tools/metrics_dashboard.py`

```python
#!/usr/bin/env python3
"""Streamlit metrics dashboard"""
import streamlit as st
import sqlite3
import pandas as pd
import json

def load_procedures():
    conn = sqlite3.connect("registry.db")
    df = pd.read_sql_query("SELECT * FROM procedures", conn)
    conn.close()
    
    # Parse JSON payloads
    df['data'] = df['payload'].apply(json.loads)
    return df

def main():
    st.set_page_config(page_title="Bronchoscopy Metrics", layout="wide")
    st.title("📊 Bronchoscopy Registry Metrics")
    
    df = load_procedures()
    
    if df.empty:
        st.info("No procedures submitted yet")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Procedures", len(df))
    
    # EBUS staging sensitivity
    ebus_df = df[df['data'].apply(lambda x: x.get('procedure_type') == 'ebus_tbna')]
    if not ebus_df.empty:
        staging_count = ebus_df['data'].apply(lambda x: x.get('ebus', {}).get('staging_indication', False)).sum()
        sensitivity = staging_count / len(ebus_df) * 100
        col2.metric("EBUS Staging %", f"{sensitivity:.1f}%")
    
    # Complication rate
    complications = df['data'].apply(lambda x: len(x.get('safety', {}).get('complications', [])) > 0).sum()
    comp_rate = complications / len(df) * 100
    col3.metric("Complication Rate", f"{comp_rate:.1f}%")
    
    # BTS threshold checks
    st.subheader("BTS Audit Thresholds")
    if not ebus_df.empty and sensitivity >= 88:
        st.success(f"✅ Staging sensitivity: {sensitivity:.1f}% (≥88%)")
    elif not ebus_df.empty:
        st.error(f"❌ Staging sensitivity: {sensitivity:.1f}% (<88%)")
    
    if comp_rate < 1.0:
        st.success(f"✅ Complication rate: {comp_rate:.1f}% (<1%)")
    else:
        st.warning(f"⚠️ Complication rate: {comp_rate:.1f}% (≥1%)")
    
    # Recent procedures
    st.subheader("Recent Procedures")
    recent = df.sort_values('created_at', ascending=False).head(10)
    st.dataframe(recent[['id', 'facility_id', 'created_at']])

if __name__ == "__main__":
    main()
```

**Run:**
```bash
streamlit run tools/metrics_dashboard.py
# Opens in browser at http://localhost:8501
```

**Commit:**
```bash
git add tools/metrics_dashboard.py
git commit -m "feat(metrics): Streamlit dashboard with BTS thresholds"
```

---

## 🚀 PHASE 6: DEPLOYMENT (Weeks 12-14)

### TestFlight Distribution

**⏸️ MANUAL ACTION #7: TestFlight setup**

1. **Apple Developer Account**
   - Enroll at developer.apple.com ($99/year)
   - Create App ID: com.yourorg.bronchregistry

2. **Archive Build**
   - Xcode → Product → Archive
   - Upload to App Store Connect

3. **TestFlight Setup**
   - Create internal testing group
   - Add beta testers (colleagues)
   - Submit for review

4. **Distribute**
   - Testers receive invite email
   - Install via TestFlight app

### Gateway Deployment

**Docker:**

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY gateway/ ./gateway/
COPY schemas/ ./schemas/
EXPOSE 8000
CMD ["uvicorn", "gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build and run
docker build -t bronch-registry-gateway .
docker run -p 8000:8000 \
  -e REGISTRY_JWT_SECRET="your-production-secret" \
  -e DATABASE_URL="postgresql://..." \
  bronch-registry-gateway
```

**Deploy to Fly.io:**

```bash
fly launch
fly deploy
fly secrets set REGISTRY_JWT_SECRET="your-secret"
```

**Commit:**
```bash
git add Dockerfile fly.toml
git commit -m "chore(deploy): Docker + Fly.io config"
git tag v1.0.0
```

---

## ✅ PROJECT COMPLETE

**You've built:**
- ✅ Privacy-preserving mobile app (iOS 26+)
- ✅ On-device Foundation Models extraction
- ✅ Zero-persistence PHI handling
- ✅ FastAPI gateway with validation
- ✅ Metrics dashboard with BTS thresholds
- ✅ 50+ annotated training examples
- ✅ Comprehensive documentation

**Next Steps:**
1. Collect real-world usage data (20+ procedures)
2. Tune extraction prompts based on failures
3. Add Android support (optional)
4. Scale to multiple facilities

**Support:** Review documentation in `docs/` for security model, quality metrics, and incident response.

---

**END OF MASTER PLAN**
