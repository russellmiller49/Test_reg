#!/usr/bin/env python3
"""
Annotation validation utility
Validates annotation quality and completeness
"""
import json
import argparse
from pathlib import Path
from collections import defaultdict

def load_annotations():
    """Load all annotations from JSONL file"""
    jsonl_path = Path("eval/data/gold_corpus_v1.jsonl")
    if not jsonl_path.exists():
        return []
    
    annotations = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))
    return annotations

def validate_annotation(annotation):
    """Validate a single annotation"""
    issues = []
    
    # Check required fields
    required_fields = ["id", "note_text"]
    for field in required_fields:
        if field not in annotation:
            issues.append(f"Missing required field: {field}")
    
    # Check EBUS fields if procedure type is EBUS
    if annotation.get("ebus_fields"):
        ebus_fields = annotation["ebus_fields"]
        
        # Check stations format
        if "stations_sampled" in ebus_fields:
            for i, station in enumerate(ebus_fields["stations_sampled"]):
                if "station" not in station:
                    issues.append(f"Station {i+1}: Missing station name")
                elif not station["station"].strip():
                    issues.append(f"Station {i+1}: Empty station name")
                
                if "size_mm" not in station:
                    issues.append(f"Station {i+1}: Missing size_mm")
                elif not isinstance(station["size_mm"], int) or station["size_mm"] <= 0:
                    issues.append(f"Station {i+1}: Invalid size_mm")
                
                if "passes" not in station:
                    issues.append(f"Station {i+1}: Missing passes")
                elif not isinstance(station["passes"], int) or station["passes"] <= 0:
                    issues.append(f"Station {i+1}: Invalid passes")
    
    # Check sedation fields
    if annotation.get("sedation_fields"):
        sedation = annotation["sedation_fields"]
        
        if "mode" not in sedation:
            issues.append("Missing sedation mode")
        elif sedation["mode"] not in ["local", "moderate_sedation", "deep_sedation", "general_anesthesia"]:
            issues.append(f"Invalid sedation mode: {sedation['mode']}")
        
        if "ramsay_max" not in sedation:
            issues.append("Missing Ramsay max score")
        elif not isinstance(sedation["ramsay_max"], int) or not (1 <= sedation["ramsay_max"] <= 6):
            issues.append(f"Invalid Ramsay max: {sedation['ramsay_max']}")
    
    # Check PHI spans
    if "phi_spans" in annotation:
        for i, span in enumerate(annotation["phi_spans"]):
            if "start" not in span or "end" not in span:
                issues.append(f"PHI span {i+1}: Missing start/end positions")
            elif span["start"] >= span["end"]:
                issues.append(f"PHI span {i+1}: Invalid start/end positions")
    
    return issues

def analyze_annotations(annotations):
    """Analyze annotation patterns and quality"""
    analysis = {
        "total": len(annotations),
        "procedure_types": defaultdict(int),
        "ebus_notes": 0,
        "stations_total": 0,
        "complications": 0,
        "phi_spans": 0,
        "issues": []
    }
    
    for annotation in annotations:
        # Count procedure types (infer from EBUS fields)
        if annotation.get("ebus_fields"):
            analysis["ebus_notes"] += 1
            analysis["procedure_types"]["ebus_tbna"] += 1
            
            # Count stations
            if "stations_sampled" in annotation["ebus_fields"]:
                analysis["stations_total"] += len(annotation["ebus_fields"]["stations_sampled"])
        else:
            analysis["procedure_types"]["other"] += 1
        
        # Count complications
        if annotation.get("outcomes", {}).get("complications"):
            analysis["complications"] += len(annotation["outcomes"]["complications"])
        
        # Count PHI spans
        if "phi_spans" in annotation:
            analysis["phi_spans"] += len(annotation["phi_spans"])
        
        # Validate annotation
        issues = validate_annotation(annotation)
        if issues:
            analysis["issues"].append({
                "id": annotation.get("id", "unknown"),
                "issues": issues
            })
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description="Validate annotation quality")
    parser.add_argument("--detailed", action="store_true", help="Show detailed validation results")
    parser.add_argument("--fix", action="store_true", help="Suggest fixes for common issues")
    
    args = parser.parse_args()
    
    print("🔍 Bronchoscopy Registry Annotation Validation")
    print("=" * 50)
    
    annotations = load_annotations()
    if not annotations:
        print("❌ No annotations found. Run the annotation tool first.")
        return
    
    analysis = analyze_annotations(annotations)
    
    print(f"📊 Annotation Summary:")
    print(f"   Total annotated: {analysis['total']}")
    print(f"   EBUS notes: {analysis['ebus_notes']}")
    print(f"   Total stations: {analysis['stations_total']}")
    print(f"   Complications: {analysis['complications']}")
    print(f"   PHI spans: {analysis['phi_spans']}")
    print()
    
    print(f"📋 Procedure Types:")
    for proc_type, count in analysis["procedure_types"].items():
        print(f"   {proc_type}: {count}")
    print()
    
    if analysis["issues"]:
        print(f"⚠️  Validation Issues ({len(analysis['issues'])} annotations):")
        for issue_set in analysis["issues"]:
            print(f"   {issue_set['id']}:")
            for issue in issue_set["issues"]:
                print(f"     - {issue}")
        print()
    else:
        print("✅ No validation issues found!")
        print()
    
    if args.detailed:
        print("📝 Detailed Analysis:")
        for annotation in annotations:
            print(f"   {annotation['id']}: {len(annotation.get('note_text', ''))} chars")
            if annotation.get("ebus_fields", {}).get("stations_sampled"):
                print(f"     Stations: {len(annotation['ebus_fields']['stations_sampled'])}")
        print()
    
    if args.fix:
        print("🔧 Common Fixes:")
        print("   - Ensure station names are in format: 4R, 7, 10L, etc.")
        print("   - Size should be positive integer (mm)")
        print("   - Passes should be positive integer")
        print("   - Ramsay score should be 1-6")
        print("   - Sedation mode should be one of: local, moderate_sedation, deep_sedation, general_anesthesia")
        print()
    
    print("💡 Usage:")
    print("   python tools/validate_annotations.py           # Basic validation")
    print("   python tools/validate_annotations.py --detailed # Detailed analysis")
    print("   python tools/validate_annotations.py --fix      # Show common fixes")

if __name__ == "__main__":
    main()
