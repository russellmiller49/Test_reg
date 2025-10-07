# Bronchoscopy Registry

Privacy-preserving bronchoscopy procedure registry with on-device AI extraction using Apple's Foundation Models framework.

## 🎯 Project Overview

This project implements a comprehensive bronchoscopy registry system that:
- Captures clinical notes via iOS camera
- Performs on-device OCR and PHI redaction
- Extracts structured data using Apple's Foundation Models
- Submits de-identified data to a secure gateway
- Provides quality metrics and analytics

## 📊 Current Status

- ✅ **144 synthetic bronchoscopy notes** generated and ready for annotation
- ✅ **Annotation tool** built and ready to use
- ✅ **Schema definitions** for procedure data
- ✅ **iOS app foundation** (basic SwiftUI structure)
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
├── data/synthetic_notes/          # 144 clinical notes (note_001.txt - note_144.txt)
├── tools/                         # Annotation and processing tools
│   ├── annotate_streamlit.py      # Interactive annotation interface
│   ├── phi_synthesizer.py         # PHI replacement tool
│   └── README.md                  # Tool documentation
├── schemas/                       # Data schemas and codebooks
│   ├── bronchoscopy_procedure.schema.json
│   └── codebooks/
├── examples/                      # Example submissions
├── eval/data/                     # Annotated training data (generated)
├── Bronch_registryApp.swift       # iOS app entry point
├── ContentView.swift              # iOS app main view
└── REGISTRY_MASTER_PLAN.md        # Complete implementation plan
```

## 🎯 Next Steps

1. **Complete annotation** of 50-100 notes using the Streamlit tool
2. **Build iOS app** with document capture and redaction
3. **Implement Foundation Models** extraction
4. **Deploy gateway** for data collection
5. **Create metrics dashboard**

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
- [Tool Documentation](tools/README.md) - Annotation and processing tools
- [Schema Reference](schemas/bronchoscopy_procedure.schema.json) - Data structure

## 🤝 Contributing

This is a solo development project following the master plan. The annotation tool is ready for use with the 144-note corpus.

## 📄 License

Apache 2.0
