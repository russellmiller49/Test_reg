#!/usr/bin/env python3
"""
Cross-platform annotation sync utility
Helps sync annotations between WSL and macOS environments
"""
import json
import argparse
from pathlib import Path
import subprocess
import sys

def get_annotation_stats():
    """Get statistics about current annotations"""
    jsonl_path = Path("eval/data/gold_corpus_v1.jsonl")
    if not jsonl_path.exists():
        return {"total": 0, "annotated": 0, "remaining": 144}
    
    with open(jsonl_path) as f:
        annotated_count = len([line for line in f if line.strip()])
    
    return {
        "total": 144,
        "annotated": annotated_count,
        "remaining": 144 - annotated_count
    }

def check_git_status():
    """Check git status and uncommitted changes"""
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Error checking git status"

def sync_to_remote():
    """Sync annotations to remote repository"""
    try:
        # Add annotation files
        subprocess.run(["git", "add", "eval/data/gold_corpus_v1.jsonl"], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], 
                              capture_output=True)
        if result.returncode != 0:
            # There are changes to commit
            subprocess.run(["git", "commit", "-m", "Update annotations"], check=True)
            subprocess.run(["git", "push"], check=True)
            return "✅ Annotations synced to remote"
        else:
            return "ℹ️  No new annotations to sync"
    except subprocess.CalledProcessError as e:
        return f"❌ Error syncing: {e}"

def pull_from_remote():
    """Pull latest changes from remote"""
    try:
        subprocess.run(["git", "pull"], check=True)
        return "✅ Latest changes pulled from remote"
    except subprocess.CalledProcessError as e:
        return f"❌ Error pulling: {e}"

def main():
    parser = argparse.ArgumentParser(description="Sync annotations between platforms")
    parser.add_argument("--stats", action="store_true", help="Show annotation statistics")
    parser.add_argument("--sync", action="store_true", help="Sync annotations to remote")
    parser.add_argument("--pull", action="store_true", help="Pull latest from remote")
    parser.add_argument("--status", action="store_true", help="Show git status")
    
    args = parser.parse_args()
    
    if not any([args.stats, args.sync, args.pull, args.status]):
        # Default: show stats
        args.stats = True
    
    print("🔄 Bronchoscopy Registry Annotation Sync")
    print("=" * 50)
    
    if args.stats:
        stats = get_annotation_stats()
        print(f"📊 Annotation Statistics:")
        print(f"   Total notes: {stats['total']}")
        print(f"   Annotated: {stats['annotated']}")
        print(f"   Remaining: {stats['remaining']}")
        print(f"   Progress: {stats['annotated']/stats['total']*100:.1f}%")
        print()
    
    if args.status:
        git_status = check_git_status()
        if git_status:
            print(f"📋 Git Status:")
            print(f"   {git_status}")
        else:
            print("📋 Git Status: Clean")
        print()
    
    if args.pull:
        result = pull_from_remote()
        print(result)
        print()
    
    if args.sync:
        result = sync_to_remote()
        print(result)
        print()
    
    print("💡 Usage:")
    print("   python tools/sync_annotations.py --stats    # Show progress")
    print("   python tools/sync_annotations.py --sync     # Push annotations")
    print("   python tools/sync_annotations.py --pull     # Pull latest")
    print("   python tools/sync_annotations.py --status   # Check git status")

if __name__ == "__main__":
    main()
