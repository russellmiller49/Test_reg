# Bronchoscopy Registry Tools

This directory contains tools for processing and annotating bronchoscopy notes.

## Setup

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Tools

### 1. Annotation Tool (`annotate_streamlit.py`)

Interactive web interface for annotating bronchoscopy notes with ground truth fields.

**Usage:**
```bash
streamlit run tools/annotate_streamlit.py
```

**Features:**
- Loads all 144 synthetic notes from `data/synthetic_notes/`
- Tracks annotation progress (shows annotated vs remaining)
- Saves annotations to `eval/data/gold_corpus_v1.jsonl`
- Supports EBUS, sedation, complications, and PHI span annotation

**Annotation Fields:**
- **Procedure Type**: diagnostic_flexible, ebus_tbna, navigation_bronchoscopy, therapeutic_bronchoscopy
- **EBUS Fields**: staging indication, systematic sequence, stations sampled, ROSE usage, PET positivity
- **Sedation**: mode, Ramsay score, monitoring intervals, reversal agents
- **Outcomes**: complications with type, severity, and intervention
- **PHI Spans**: character positions of PHI elements

### 2. Cross-Platform Setup (`setup_wsl.sh`)

One-time setup script for WSL environment.

**Usage:**
```bash
# In WSL terminal
curl -sSL https://raw.githubusercontent.com/russellmiller49/Test_reg/main/tools/setup_wsl.sh | bash
```

**Features:**
- Installs Python, pip, and git
- Creates virtual environment
- Installs all dependencies
- Clones repository if needed
- Verifies installation

### 3. Quick Start (`start_annotation.sh`)

Quick start script for annotation tool.

**Usage:**
```bash
cd Test_reg
./tools/start_annotation.sh
```

**Features:**
- Activates virtual environment
- Checks dependencies
- Starts Streamlit annotation tool
- Shows access URL

### 4. Annotation Sync (`sync_annotations.py`)

Cross-platform annotation synchronization utility.

**Usage:**
```bash
python tools/sync_annotations.py --stats    # Show progress
python tools/sync_annotations.py --sync     # Push annotations
python tools/sync_annotations.py --pull     # Pull latest
python tools/sync_annotations.py --status   # Check git status
```

**Features:**
- Shows annotation progress statistics
- Syncs annotations to/from GitHub
- Checks git status
- Handles cross-platform workflow

### 5. Annotation Validation (`validate_annotations.py`)

Validates annotation quality and completeness.

**Usage:**
```bash
python tools/validate_annotations.py           # Basic validation
python tools/validate_annotations.py --detailed # Detailed analysis
python tools/validate_annotations.py --fix      # Show common fixes
```

**Features:**
- Validates annotation format and content
- Checks for missing or invalid fields
- Analyzes annotation patterns
- Suggests fixes for common issues

### 6. PHI Synthesizer (`phi_synthesizer.py`)

Replaces real PHI with synthetic data while preserving clinical content.

**Usage:**
```bash
python tools/phi_synthesizer.py --input-dir data/raw_notes --output-dir data/synthetic_notes
```

**Features:**
- Replaces names, MRNs, DOBs, and phone numbers with synthetic equivalents
- Maintains consistent replacements within each note
- Generates metadata about replacements made

## Data Structure

### Input Notes
- Location: `data/synthetic_notes/note_001.txt` through `note_144.txt`
- Format: Plain text clinical notes
- Content: De-identified bronchoscopy procedure notes

### Output Annotations
- Location: `eval/data/gold_corpus_v1.jsonl`
- Format: JSON Lines (one JSON object per line)
- Schema: Each annotation contains note text, PHI spans, and extracted fields

## Next Steps

1. **Run the annotation tool** to begin annotating the 144-note corpus
2. **Annotate 50+ notes** for training data (target: 50-100 notes)
3. **Review annotations** for quality and consistency
4. **Use annotated data** for model training and evaluation

## Notes

- The annotation tool automatically tracks progress and skips already annotated notes
- All 144 notes are available for annotation
- The tool is designed to work with the current data structure and doesn't require updates for the expanded corpus
