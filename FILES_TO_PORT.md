# Files to Port for Web UI Version

This document identifies which files from this Swift/iOS repository should be ported to create a web-based version for extracting registry information from procedural notes.

## ✅ **ESSENTIAL FILES TO PORT**

### 1. **Schema & Data Models** (Core Data Structure)
**Purpose:** Defines the structure of extracted registry data

- `schemas/bronchoscopy_procedure.schema.json` ✅ **MUST PORT**
  - JSON schema defining all registry fields
  - Used for validation and as reference for extraction

- `bronch_schema/models.py` ✅ **MUST PORT**
  - Pydantic models (Python) - canonical data structures
  - Includes: Sedation, NodeSampling, Therapeutic, QualityMetrics, Procedure, GoldRecord
  - Can be adapted to TypeScript interfaces for web frontend

### 2. **Backend API** (Python/FastAPI)
**Purpose:** Server-side API for storing and retrieving annotations

- `api/` directory ✅ **PORT ENTIRE DIRECTORY**
  - `api/app/main.py` - FastAPI application setup
  - `api/app/routers/annotations.py` - Annotation endpoints
  - `api/app/models/` - Database models
  - `api/app/schemas/` - API request/response schemas
  - `api/app/core/` - Core utilities
  - `api/app/database.py` - Database configuration
  - `api/requirements.txt` - Python dependencies
  - `api/alembic/` - Database migrations (if using)

### 3. **Extraction Logic & Prompts**
**Purpose:** Instructions for LLM extraction from notes

**Note:** The extraction prompts are described in `REGISTRY_MASTER_PLAN.md` but not yet implemented as separate files. You should create:

- `prompts/extract_ebus.txt` - EBUS extraction instructions (see REGISTRY_MASTER_PLAN.md lines 943-995)
- `prompts/extract_sedation.txt` - Sedation extraction instructions (see REGISTRY_MASTER_PLAN.md lines 997-1043)
- `prompts/extract_therapeutic.txt` - Therapeutic procedure extraction
- `prompts/extract_complications.txt` - Complications extraction
- `config/phi_rules.json` - PHI detection rules (see REGISTRY_MASTER_PLAN.md lines 907-940)

**Extraction Service (Python equivalent of Swift ExtractionService):**
- Create: `api/app/services/extraction_service.py`
  - Functions to call LLM APIs (OpenAI, Anthropic, etc.) with prompts
  - Parse structured JSON responses matching the schema
  - Handle errors and validation

### 4. **Annotation Tools** (Data Preparation)
**Purpose:** Tools for manually annotating notes to create training data

- `tools/annotate_streamlit.py` ✅ **PORT** (or adapt for web UI)
  - Interactive annotation interface
  - Can be adapted to work with your web frontend

- `tools/annotation_backend.py` ✅ **PORT**
  - Abstract backend for storing annotations
  - Supports both local filesystem and Supabase

- `tools/writer.py` ✅ **PORT**
  - Functions to build annotation records (`build_annotation_record_v22`)
  - Save annotations in JSONL format

- `tools/ui_helpers.py` ✅ **PORT**
  - UI helper functions (tri-state selection, etc.)

- `tools/validate_annotations.py` ✅ **PORT** (if exists)
  - Validation logic for annotations

### 5. **Frontend** (Next.js/React)
**Purpose:** User interface for web application

**Note:** A frontend already exists in this repo!

- `frontend/` directory ✅ **ENHANCE EXISTING**
  - `frontend/src/` - React components
  - `frontend/src/components/forms/ProcedureAnnotationForm.tsx` - Annotation form
  - `frontend/src/types/` - TypeScript type definitions
  - `frontend/src/lib/` - Utility functions
  - `frontend/package.json` - Dependencies

**Actions needed:**
1. Port Python models to TypeScript interfaces
2. Integrate extraction API calls into frontend
3. Add OCR/note upload functionality
4. Add extraction results display and editing

### 6. **Data & Examples**
**Purpose:** Test data and examples

- `data/synthetic_notes/` ✅ **PORT** (for testing)
  - Sample procedural notes for testing extraction

- `examples/` ✅ **PORT** (if exists)
  - Example submissions

- `bronchoscopy_notes.jsonl` ✅ **PORT** (if using)
  - Additional note data

### 7. **Configuration & Documentation**
**Purpose:** Project setup and reference

- `requirements.txt` ✅ **PORT** (Python dependencies for tools)
- `README.md` ✅ **PORT** (update for web version)
- `REGISTRY_MASTER_PLAN.md` ✅ **REFERENCE ONLY**
  - Contains detailed specifications and prompts
  - Use as reference for implementation details

---

## ❌ **FILES TO SKIP (iOS/Swift Specific)**

**Note:** These files have been moved to the `ios/` subdirectory and preserved there.

- `ios/Bronch_registryApp.swift` - iOS app entry point (preserved in `ios/`)
- `ios/ContentView.swift` - iOS SwiftUI view (preserved in `ios/`)
- `ios/Assets.xcassets/` - iOS asset catalog (preserved in `ios/`)
- Any other `.swift` files (preserved in `ios/`)

See `ios/README.md` for details about the preserved iOS code.

---

## 🔧 **NEW FILES TO CREATE**

### Extraction Service (Python)
Create: `api/app/services/extraction_service.py`

```python
# Pseudo-code structure:
class ExtractionService:
    def extract_ebus(self, note_text: str) -> dict:
        # Use prompts/extract_ebus.txt
        # Call LLM API (OpenAI, Anthropic, etc.)
        # Return structured data matching schema
        
    def extract_sedation(self, note_text: str) -> dict:
        # Use prompts/extract_sedation.txt
        
    def extract_full_procedure(self, note_text: str) -> dict:
        # Extract all fields from bronchoscopy_procedure.schema.json
```

### OCR Service (if needed)
Create: `api/app/services/ocr_service.py`
- Use cloud OCR APIs (Google Cloud Vision, AWS Textract, etc.)
- Handle image upload and text extraction

### PHI Redaction Service
Create: `api/app/services/phi_redaction.py`
- Use config/phi_rules.json
- Redact PHI from extracted text before storing

### TypeScript Models
Create: `frontend/src/types/schema.ts`
- Port Pydantic models to TypeScript interfaces
- Ensure type safety in frontend

---

## 📋 **MIGRATION CHECKLIST**

- [ ] Port schema files (`schemas/`, `bronch_schema/`)
- [ ] Port backend API (`api/` directory)
- [ ] Create extraction service (Python) using prompts from master plan
- [ ] Port annotation tools (`tools/`) - adapt as needed
- [ ] Enhance frontend (`frontend/`) with extraction features
- [ ] Create PHI redaction service
- [ ] Create OCR service (if processing images)
- [ ] Port test data (`data/synthetic_notes/`)
- [ ] Update README for web version
- [ ] Set up environment variables and configuration

---

## 🎯 **RECOMMENDED ARCHITECTURE**

```
Web UI Version:
├── Frontend (Next.js/React)
│   ├── Note upload (OCR or text paste)
│   ├── Extraction trigger
│   ├── Display extracted fields
│   └── Manual editing/correction
│
├── Backend API (FastAPI)
│   ├── OCR endpoint (if processing images)
│   ├── Extraction endpoint (calls LLM)
│   ├── PHI redaction endpoint
│   ├── Annotation storage endpoint
│   └── Validation endpoint
│
└── Services
    ├── Extraction Service (LLM calls)
    ├── OCR Service (image → text)
    └── PHI Redaction Service
```

---

## 💡 **KEY DIFFERENCES FROM iOS VERSION**

1. **LLM Backend:** Use cloud LLM APIs (OpenAI, Anthropic) instead of Apple Foundation Models
2. **OCR:** Use cloud OCR services instead of VisionKit
3. **PHI Redaction:** Server-side instead of on-device
4. **Storage:** Database-driven instead of local iOS storage
5. **UI:** Web forms instead of SwiftUI

---

## 📝 **NOTES**

- The Swift extraction code in `REGISTRY_MASTER_PLAN.md` shows the intended structure using Apple Foundation Models. For web, adapt to use standard LLM APIs with structured output (JSON mode).
- The schema (`bronchoscopy_procedure.schema.json`) is the single source of truth for data structure.
- The existing `frontend/` directory suggests a Next.js app was already started - enhance it rather than starting from scratch.

