# 🚀 Quick Start Guide

## For WSL Users (Windows)

### 1. One-time Setup
```bash
# Run this in WSL terminal
curl -sSL https://raw.githubusercontent.com/russellmiller49/Test_reg/main/tools/setup_wsl.sh | bash
```

### 2. Start Annotating
```bash
cd Test_reg
./tools/start_annotation.sh
```

### 3. Open Browser
- Go to: `http://localhost:8501`
- Start annotating the 144 notes!

## For macOS Users

### 1. Clone Repository
```bash
git clone https://github.com/russellmiller49/Test_reg.git
cd Test_reg
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Annotating
```bash
streamlit run tools/annotate_streamlit.py
```

## 🎯 What You'll See

The annotation tool will show:
- **Progress sidebar**: 144 total notes, annotated count, remaining
- **Note selector**: Choose which note to annotate
- **Annotation form**: Fill in clinical fields
- **Save button**: Commit your annotations

## 📊 Track Progress

```bash
# Check how many notes you've annotated
python tools/sync_annotations.py --stats

# Validate your annotations
python tools/validate_annotations.py

# Push to GitHub
python tools/sync_annotations.py --sync
```

## 🎯 Goal

**Annotate 50-100 notes** to create training data for the AI extraction models.

Each annotation should include:
- ✅ Procedure type
- ✅ EBUS fields (if applicable)
- ✅ Sedation details
- ✅ Complications
- ✅ PHI spans (if any)

## 💡 Tips

- **Work in batches**: 10-20 notes per session
- **Be consistent**: Follow the same format for similar cases
- **Validate regularly**: Check for errors after each batch
- **Save frequently**: Annotations auto-save to JSONL file

## 🆘 Need Help?

- Check the [Workflow Guide](workflow_guide.md) for detailed instructions
- Run validation tools to check for errors
- Ask for help with specific error messages

---

**Ready to start? Run the setup command above and begin annotating!** 🎉
