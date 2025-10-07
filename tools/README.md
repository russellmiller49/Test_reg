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

### 2. PHI Synthesizer (`phi_synthesizer.py`)

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
