# Cross-Platform Workflow Guide

This guide explains how to work on the Bronchoscopy Registry project across macOS and WSL environments.

## 🖥️ Platform Overview

| Task | macOS | WSL (Windows) |
|------|-------|---------------|
| **Annotation** | ✅ | ✅ **Recommended** |
| **iOS Development** | ✅ **Required** | ❌ |
| **Data Processing** | ✅ | ✅ |
| **Git Operations** | ✅ | ✅ |

## 🚀 Quick Start

### WSL Setup (One-time)
```bash
# In WSL terminal
curl -sSL https://raw.githubusercontent.com/russellmiller49/Test_reg/main/tools/setup_wsl.sh | bash
```

### Start Annotating (WSL)
```bash
cd Test_reg
./tools/start_annotation.sh
```

## 📋 Detailed Workflow

### 1. Initial WSL Setup

```bash
# Clone repository
git clone https://github.com/russellmiller49/Test_reg.git
cd Test_reg

# Run setup script
chmod +x tools/setup_wsl.sh
./tools/setup_wsl.sh
```

### 2. Daily Annotation Work (WSL)

```bash
# Start annotation session
cd Test_reg
source venv/bin/activate
./tools/start_annotation.sh

# Or manually:
streamlit run tools/annotate_streamlit.py
```

**Annotation Process:**
1. Open browser to `http://localhost:8501`
2. Select notes from the 144-note corpus
3. Fill in clinical fields (EBUS, sedation, complications)
4. Save annotations (auto-saved to `eval/data/gold_corpus_v1.jsonl`)

### 3. Sync Annotations

```bash
# Check progress
python tools/sync_annotations.py --stats

# Push annotations to GitHub
python tools/sync_annotations.py --sync

# Pull latest changes
python tools/sync_annotations.py --pull
```

### 4. Validate Annotations

```bash
# Basic validation
python tools/validate_annotations.py

# Detailed analysis
python tools/validate_annotations.py --detailed

# Get fix suggestions
python tools/validate_annotations.py --fix
```

### 5. iOS Development (macOS)

```bash
# Pull latest annotations
cd /Users/russellmiller/Projects/Bronch_registry/Bronch_registry
git pull

# Open in Xcode
open Bronch_registry.xcodeproj

# Work on iOS app features
# - Document capture
# - PHI redaction
# - Foundation Models integration
```

## 🔄 Sync Workflow

### From WSL to macOS
```bash
# In WSL: Push annotations
python tools/sync_annotations.py --sync

# In macOS: Pull annotations
git pull
```

### From macOS to WSL
```bash
# In macOS: Push iOS changes
git add .
git commit -m "iOS app updates"
git push

# In WSL: Pull changes
git pull
```

## 📊 Progress Tracking

### Check Annotation Progress
```bash
# In WSL or macOS
python tools/sync_annotations.py --stats
```

**Output:**
```
📊 Annotation Statistics:
   Total notes: 144
   Annotated: 23
   Remaining: 121
   Progress: 16.0%
```

### Validate Quality
```bash
python tools/validate_annotations.py
```

**Output:**
```
📊 Annotation Summary:
   Total annotated: 23
   EBUS notes: 18
   Total stations: 45
   Complications: 2
   PHI spans: 0

✅ No validation issues found!
```

## 🛠️ Troubleshooting

### WSL Issues

**Streamlit won't start:**
```bash
# Check if port is in use
lsof -i :8501
# Kill process if needed
pkill -f streamlit

# Restart
./tools/start_annotation.sh
```

**Python dependencies missing:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**Git authentication issues:**
```bash
# Set up git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### macOS Issues

**Xcode project won't open:**
```bash
# Check if project is in right location
ls -la Bronch_registry.xcodeproj

# Open from correct directory
cd /Users/russellmiller/Projects/Bronch_registry/Bronch_registry
open Bronch_registry.xcodeproj
```

## 📁 File Organization

### WSL Workspace
```
~/Test_reg/
├── tools/                    # Python tools
├── data/synthetic_notes/     # 144 notes
├── eval/data/               # Annotations (generated)
├── venv/                    # Python environment
└── .git/                    # Git repository
```

### macOS Workspace
```
/Users/russellmiller/Projects/Bronch_registry/Bronch_registry/
├── tools/                    # Python tools
├── data/synthetic_notes/     # 144 notes
├── eval/data/               # Annotations (synced)
├── Bronch_registryApp.swift # iOS app
├── ContentView.swift        # iOS app
└── .git/                    # Git repository
```

## 🎯 Best Practices

### Annotation Work
- **Work in batches**: Annotate 10-20 notes at a time
- **Validate regularly**: Run validation after each batch
- **Sync frequently**: Push annotations after each session
- **Use consistent format**: Follow the schema guidelines

### Development Work
- **Pull before starting**: Always pull latest annotations
- **Test thoroughly**: Validate iOS app with real annotations
- **Commit often**: Small, focused commits
- **Document changes**: Clear commit messages

### Collaboration
- **Communicate progress**: Share annotation statistics
- **Review quality**: Validate annotations before using
- **Sync regularly**: Keep both environments up to date

## 🚀 Next Steps

1. **Complete annotation** (target: 50-100 notes)
2. **Build iOS app** with document capture
3. **Implement Foundation Models** extraction
4. **Deploy gateway** for data collection
5. **Create metrics dashboard**

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Run validation tools
3. Check git status
4. Review error messages
5. Ask for help with specific error messages
