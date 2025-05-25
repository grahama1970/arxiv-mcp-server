#!/usr/bin/env python3
"""Download papers relevant to the Granger project."""

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

# Keywords for Granger project research
SEARCH_QUERIES = [
    "requirements contradiction detection formal methods",
    "specification inconsistency detection software engineering", 
    "automated requirements analysis verification",
    "natural language processing formal verification",
    "model based systems engineering contradiction",
    "requirements engineering conflict detection",
    "formal methods military systems",
    "cross domain requirements analysis",
    "specification validation formal methods",
    "requirements traceability graph analysis"
]

async def search_and_download_papers():
    """Search for and download papers relevant to Granger."""
    
    print("=== Downloading Papers for GRANGER Project ===\n")
    
    # Setup
    settings = Settings()
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(exist_ok=True)
    
    # Create a subdirectory for Granger papers
    granger_path = storage_path / "granger_project"
    granger_path.mkdir(exist_ok=True)
    
    all_papers = []
    paper_ids_seen = set()
    
    # Search for papers using each query
    for query in SEARCH_QUERIES:
        print(f"\n📚 Searching: {query}")
        print("-" * 80)
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=5,  # Top 5 per query
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = list(client.results(search))
        
        for paper in papers:
            paper_id = paper.entry_id.split('/')[-1]
            
            # Skip if we've already seen this paper
            if paper_id in paper_ids_seen:
                continue
                
            paper_ids_seen.add(paper_id)
            
            # Filter by relevance - check if title/abstract contains key terms
            relevant_terms = [
                "requirement", "specification", "contradiction", "inconsisten",
                "conflict", "formal", "verification", "validation", "detection",
                "analysis", "model", "engineer"
            ]
            
            title_lower = paper.title.lower()
            abstract_lower = paper.summary.lower()
            
            relevance_score = sum(
                1 for term in relevant_terms 
                if term in title_lower or term in abstract_lower
            )
            
            if relevance_score < 3:  # Skip if not relevant enough
                continue
            
            paper_info = {
                "id": paper_id,
                "title": paper.title.replace('\n', ' '),
                "authors": [author.name for author in paper.authors],
                "published": paper.published.isoformat(),
                "relevance_score": relevance_score,
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
                "query": query
            }
            
            all_papers.append(paper_info)
            
            print(f"\n✓ Found: {paper.title}")
            print(f"  ID: {paper_id}")
            print(f"  Published: {paper.published.date()}")
            print(f"  Relevance Score: {relevance_score}")
            categories_str = ", ".join(paper.categories)
            print(f"  Categories: {categories_str}")
    
    # Sort by relevance score
    all_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"\n\n🎯 Total relevant papers found: {len(all_papers)}")
    print("\n" + "=" * 80)
    
    # Download top papers
    max_downloads = min(15, len(all_papers))  # Limit to top 15
    downloaded_papers = []
    
    print(f"\n📥 Downloading top {max_downloads} papers...\n")
    
    # Check available converters
    available_converters = ConverterFactory.get_available_converters()
    use_marker = available_converters.get("marker-pdf", False)
    
    if use_marker:
        print("✓ marker-pdf is available for high-quality conversion")
    else:
        print("ℹ️  Using pymupdf4llm for conversion (install marker-pdf for better quality)")
    
    for i, paper_info in enumerate(all_papers[:max_downloads], 1):
        paper_id = paper_info["id"]
        print(f"\n[{i}/{max_downloads}] Processing: {paper_info['title'][:80]}...")
        
        try:
            # Download PDF
            pdf_path = granger_path / f"{paper_id}.pdf"
            
            if not pdf_path.exists():
                print(f"  ⬇️  Downloading PDF...")
                # Re-fetch the paper object to download
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
                paper.download_pdf(dirpath=str(granger_path), filename=f"{paper_id}.pdf")
                print(f"  ✓ Downloaded to: {pdf_path.name}")
            else:
                print(f"  ✓ PDF already exists")
            
            # Convert to markdown
            print(f"  📄 Converting to markdown...")
            converter_type = "marker-pdf" if use_marker else "pymupdf4llm"
            converter = ConverterFactory.create(converter_type, granger_path)
            
            # Convert to markdown
            md_result = await converter.convert(paper_id, pdf_path)
            
            if md_result:
                # Save metadata
                paper_info["converted"] = True
                paper_info["converter"] = converter_type
                paper_info["markdown_path"] = f"{paper_id}.md"
                downloaded_papers.append(paper_info)
                print(f"  ✓ Converted successfully")
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
            "total_found": len(all_papers),
            "downloaded": len(downloaded_papers),
            "papers": downloaded_papers
        }, f, indent=2)
    
    print(f"\n\n✅ Download complete!")
    print(f"📁 Papers saved to: {granger_path}")
    print(f"📊 Metadata saved to: {metadata_path.name}")
    print(f"\nSummary:")
    print(f"  - Papers found: {len(all_papers)}")
    print(f"  - Papers downloaded: {len(downloaded_papers)}")
    
    # Print top papers for reference
    print(f"\n🏆 Top 5 most relevant papers:")
    for i, paper in enumerate(downloaded_papers[:5], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Relevance: {paper['relevance_score']}")
        print(f"   File: {paper['id']}.md")

if __name__ == "__main__":
    asyncio.run(search_and_download_papers())
