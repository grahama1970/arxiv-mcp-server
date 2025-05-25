#!/usr/bin/env python3
"""Migrate papers from old storage location to new project-based storage."""

import os
import shutil
from pathlib import Path
import json


def migrate_papers():
    """Migrate papers from ~/.arxiv-mcp-server/papers to project data directory."""
    
    # Old location
    old_path = Path.home() / ".arxiv-mcp-server" / "papers"
    
    # New location (relative to this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    new_path = project_root / "data" / "papers"
    
    if not old_path.exists():
        print(f"No papers found at {old_path}")
        return
    
    print(f"Migrating papers from {old_path} to {new_path}")
    
    # Count files
    pdf_files = list(old_path.glob("*.pdf"))
    md_files = list(old_path.glob("*.md"))
    json_files = list(old_path.glob("*.json"))
    
    print(f"Found: {len(pdf_files)} PDFs, {len(md_files)} Markdown files, {len(json_files)} JSON files")
    
    # Migrate PDFs
    for pdf in pdf_files:
        dest = new_path / "pdfs" / pdf.name
        if not dest.exists():
            print(f"  Moving {pdf.name} to pdfs/")
            shutil.copy2(pdf, dest)
        else:
            print(f"  Skipping {pdf.name} (already exists)")
    
    # Migrate Markdown files
    for md in md_files:
        dest = new_path / "markdown" / md.name
        if not dest.exists():
            print(f"  Moving {md.name} to markdown/")
            shutil.copy2(md, dest)
        else:
            print(f"  Skipping {md.name} (already exists)")
    
    # Migrate JSON files
    for json_file in json_files:
        # Check if it's metadata
        if "_metadata" in json_file.name or "_meta" in json_file.name:
            dest = new_path / "metadata" / json_file.name
        else:
            dest = new_path / "json" / json_file.name
        
        if not dest.exists():
            print(f"  Moving {json_file.name} to {dest.parent.name}/")
            shutil.copy2(json_file, dest)
        else:
            print(f"  Skipping {json_file.name} (already exists)")
    
    # Migrate annotations
    old_annotations = old_path / "annotations"
    if old_annotations.exists():
        new_annotations = project_root / "data" / "annotations"
        for ann_file in old_annotations.glob("*.json"):
            dest = new_annotations / ann_file.name
            if not dest.exists():
                print(f"  Moving annotation {ann_file.name}")
                shutil.copy2(ann_file, dest)
    
    print("\nMigration complete!")
    print("\nTo use the new location, update your MCP client config:")
    print(f'  "args": ["--storage-path", "{new_path}"]')
    print("\nOr set the environment variable:")
    print(f'  export ARXIV_STORAGE_PATH="{new_path}"')


if __name__ == "__main__":
    migrate_papers()