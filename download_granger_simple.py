#!/usr/bin/env python3
"""Download papers relevant to the Granger project - simplified version."""

import asyncio
import arxiv
from pathlib import Path
import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from arxiv_mcp_server.converters import ConverterFactory
from arxiv_mcp_server.config import Settings

# Key queries for Granger project
SEARCH_QUERIES = [
    "requirements contradiction detection",
    "specification inconsistency formal methods",
    "requirements conflict detection"
]

async def search_and_download_papers():
    """Search for and download papers relevant to Granger."""
    
    print("=== Downloading Papers for GRANGER Project (Simplified) ===\n")
    
    # Setup
    settings = Settings()
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Create a subdirectory for Granger papers
    granger_path = storage_path / "granger_project"
    granger_path.mkdir(exist_ok=True)
    
    all_papers = []
    paper_ids_seen = set()
    
    # Search for papers using each query
    for query in SEARCH_QUERIES:
        print(f"\n📚 Searching: {query}")
        print("-" * 50)
        
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=3,  # Only 3 per query
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = list(client.results(search))
            print(f"  Found {len(papers)} papers")
            
            for paper in papers:
                paper_id = paper.entry_id.split('/')[-1]
                
                if paper_id in paper_ids_seen:
                    continue
                    
                paper_ids_seen.add(paper_id)
                
                paper_info = {
                    "id": paper_id,
                    "title": paper.title.replace('\n', ' '),
                    "published": paper.published.isoformat(),
                    "pdf_url": paper.pdf_url,
                    "query": query
                }
                
                all_papers.append(paper_info)
                print(f"  ✓ {paper.title[:60]}...")
                
        except Exception as e:
            print(f"  ❌ Error searching: {e}")
            continue
    
    print(f"\n\n🎯 Total papers found: {len(all_papers)}")
    
    # Download papers
    max_downloads = min(5, len(all_papers))  # Limit to 5
    downloaded_papers = []
    
    print(f"\n📥 Downloading {max_downloads} papers...\n")
    
    for i, paper_info in enumerate(all_papers[:max_downloads], 1):
        paper_id = paper_info["id"]
        print(f"[{i}/{max_downloads}] {paper_info['title'][:60]}...")
        
        try:
            # Download PDF
            pdf_path = granger_path / f"{paper_id}.pdf"
            
            if not pdf_path.exists():
                print(f"  ⬇️  Downloading PDF...")
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
                paper.download_pdf(dirpath=str(granger_path), filename=f"{paper_id}.pdf")
                print(f"  ✓ Downloaded")
            else:
                print(f"  ✓ PDF exists")
            
            # Convert to markdown
            print(f"  📄 Converting to markdown...")
            converter = ConverterFactory.create("pymupdf4llm", granger_path)
            md_result = await converter.convert(paper_id, pdf_path)
            
            if md_result:
                paper_info["converted"] = True
                downloaded_papers.append(paper_info)
                print(f"  ✓ Converted")
            else:
                print(f"  ❌ Conversion failed")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            continue
    
    # Save metadata
    metadata_path = granger_path / "granger_papers_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            "download_date": datetime.now().isoformat(),
            "papers": downloaded_papers
        }, f, indent=2)
    
    print(f"\n✅ Complete! Downloaded {len(downloaded_papers)} papers")
    print(f"📁 Saved to: {granger_path}")

if __name__ == "__main__":
    asyncio.run(search_and_download_papers())
