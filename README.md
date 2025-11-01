# Bronchoscopy Registry

Privacy-preserving bronchoscopy procedure registry with web-based extraction and annotation tools.

## 🎯 Project Overview

This project implements a comprehensive bronchoscopy registry system that:
- Captures clinical notes via web upload or text input
- Performs OCR and PHI redaction (server-side or client-side)
- Extracts structured data using LLM APIs
- Submits de-identified data to a secure gateway
- Provides quality metrics and analytics

## 📊 Current Status

- ✅ **144 synthetic bronchoscopy notes** generated and ready for annotation
- ✅ **Annotation tool** built and ready to use
- ✅ **Schema definitions** for procedure data
- ✅ **Web frontend** (Next.js/React) in development
- ✅ **Backend API** (FastAPI) structure in place
- 📦 **iOS app files** preserved in `ios/` directory for future development
- 🔄 **Annotation in progress** (target: 50-100 annotated notes)

## 🚀 Quick Start

### 1. Set Up Environment
```bash
pip install -r requirements.txt
```

### 2. Start Annotation Tool
```bash
streamlit run tools/annotate_streamlit.py
```
Open browser to `http://localhost:8501`

### 3. Annotate Notes
- Select notes from the 144-note corpus
- Fill in clinical fields (EBUS, sedation, complications)
- Save annotations to build training dataset

## 📁 Project Structure

```
Bronch_registry/
├── api/                           # Backend API (FastAPI)
│   ├── app/                       # Application code
│   └── requirements.txt           # Python dependencies
├── frontend/                      # Web frontend (Next.js/React)
│   ├── src/                       # Source code
│   └── package.json               # Node dependencies
├── ios/                           # iOS app (preserved for future)
│   ├── Bronch_registryApp.swift   # iOS app entry point
│   ├── ContentView.swift          # iOS app main view
│   ├── Assets.xcassets/           # iOS assets
│   └── README.md                  # iOS development notes
├── data/synthetic_notes/          # 144 clinical notes (note_001.txt - note_144.txt)
├── tools/                         # Annotation and processing tools
│   ├── annotate_streamlit.py      # Interactive annotation interface
│   ├── phi_synthesizer.py         # PHI replacement tool
│   └── README.md                  # Tool documentation
├── schemas/                       # Data schemas and codebooks
│   ├── bronchoscopy_procedure.schema.json
│   └── codebooks/
├── bronch_schema/                 # Python data models (Pydantic)
├── examples/                      # Example submissions
├── eval/data/                     # Annotated training data (generated)
├── REGISTRY_MASTER_PLAN.md        # Complete implementation plan
└── FILES_TO_PORT.md              # Guide for porting to web version
```

## 🎯 Next Steps

1. **Complete annotation** of 50-100 notes using the Streamlit tool
2. **Implement extraction service** (Python) using LLM APIs
3. **Enhance web frontend** with extraction and editing capabilities
4. **Deploy gateway** for data collection
5. **Create metrics dashboard**

## 📱 iOS Development

iOS app files are preserved in the `ios/` directory for potential future development. See [ios/README.md](ios/README.md) for details.

## 📋 Data Schema

The registry captures structured data including:
- **Procedure details**: Type, indication, operator
- **EBUS fields**: Stations sampled, ROSE results, PET status
- **Sedation**: Mode, Ramsay score, monitoring
- **Outcomes**: Complications, diagnostic results
- **Quality metrics**: BTS compliance, safety measures

## 🔒 Privacy & Security

- **Zero-persistence PHI**: Original images never written to disk
- **On-device processing**: All AI extraction happens locally
- **Cryptographic attestation**: Tamper-proof PHI redaction records
- **De-identified submission**: Only structured, non-PHI data transmitted

## 📚 Documentation

- [Master Implementation Plan](REGISTRY_MASTER_PLAN.md) - Complete 12-14 week roadmap
- [Files to Port Guide](FILES_TO_PORT.md) - Guide for web version migration
- [iOS Development Notes](ios/README.md) - iOS app preservation notes
- [Tool Documentation](tools/README.md) - Annotation and processing tools
- [Schema Reference](schemas/bronchoscopy_procedure.schema.json) - Data structure

## 🤝 Contributing

This is a solo development project following the master plan. The annotation tool is ready for use with the 144-note corpus.

## 📄 License

Apache 2.0
