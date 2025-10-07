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
