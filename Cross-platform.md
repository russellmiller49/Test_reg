# Cross-Platform Development Guide

This project supports development across **macOS** and **WSL (Windows)** environments.

## 🎯 Platform Roles

| Task | macOS | WSL (Windows) |
|------|-------|---------------|
| **Annotation** | ✅ | ✅ **Recommended** |
| **iOS Development** | ✅ **Required** | ❌ |
| **Data Processing** | ✅ | ✅ |
| **Git Operations** | ✅ | ✅ |

## 🚀 Quick Start

### WSL Users (Windows)
```bash
# One-time setup
curl -sSL https://raw.githubusercontent.com/russellmiller49/Test_reg/main/tools/setup_wsl.sh | bash

# Start annotating
cd Test_reg
./tools/start_annotation.sh
```

### macOS Users
```bash
# Clone and setup
git clone https://github.com/russellmiller49/Test_reg.git
cd Test_reg
pip install -r requirements.txt

# Start annotating
streamlit run tools/annotate_streamlit.py
```

## 🔄 Workflow

1. **Annotate** in WSL (Windows) using web interface
2. **Sync** annotations to GitHub
3. **Pull** on macOS for iOS development
4. **Develop** iOS app with latest annotations
5. **Repeat** - continuous sync between platforms

## 📊 Progress Tracking

```bash
# Check annotation progress
python tools/sync_annotations.py --stats

# Validate annotations
python tools/validate_annotations.py

# Sync to GitHub
python tools/sync_annotations.py --sync
```

## 📚 Documentation

- **[Workflow Guide](tools/workflow_guide.md)** - Detailed cross-platform instructions
- **[Quick Start](tools/quick_start.md)** - Fast setup guide
- **[Tools README](tools/README.md)** - Complete tool documentation

## 🎯 Goal

**Annotate 50-100 notes** to create training data for AI extraction models.

---

**Ready to start?** Follow the quick start commands above! 🎉