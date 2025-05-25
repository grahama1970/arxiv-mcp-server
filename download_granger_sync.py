#!/usr/bin/env python3
"""Download papers relevant to the Granger project - synchronous version."""

import arxiv
from pathlib import Path
import sys
import os
import json
from datetime import datetime
import pymupdf4llm

print("Starting GRANGER paper download script...")
sys.stdout.flush()

# Keywords for Granger project research
SEARCH_QUERIES = [
    "requirements contradiction detection formal methods",
    "specification inconsistency detection", 
    "requirements conflict detection engineering",
    "formal verification contradiction",
    "model checking specification consistency"
]

def download_papers():
    """Search for and download papers relevant to Granger."""
    
    print("\n=== Downloading Papers for GRANGER Project ===\n")
    
    # Setup
    storage_path = Path.home() / ".arxiv-mcp-server" / "papers"
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Create a subdirectory for Granger papers
    granger_path = storage_path / "granger_project"
    granger_path.mkdir(exist_ok=True)
    
    all_papers = []
    paper_ids_seen = set()
    
    # Search for papers using each query
    for query in SEARCH_QUERIES:
        print(f"\n📚 Searching: {query}")
        print("-" * 60)
        sys.stdout.flush()
        
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = list(client.results(search))
            print(f"  Found {len(papers)} papers")
            
            for paper in papers:
                paper_id = paper.entry_id.split('/')[-1]
                
                if paper_id in paper_ids_seen:
                    continue
                    
                paper_ids_seen.add(paper_id)
                
                # Check relevance
                title_lower = paper.title.lower()
                abstract_lower = paper.summary.lower()
                
                relevant_terms = [
                    "requirement", "specification", "contradiction", 
                    "inconsisten", "conflict", "formal", "verification",
                    "detection", "analysis"
                ]
                
                relevance_score = sum(
                    1 for term in relevant_terms 
                    if term in title_lower or term in abstract_lower
                )
                
                if relevance_score >= 2:  # At least 2 relevant terms
                    paper_info = {
                        "id": paper_id,
                        "title": paper.title.replace('\n', ' '),
                        "authors": [author.name for author in paper.authors],
                        "published": paper.published.isoformat(),
                        "relevance_score": relevance_score,
                        "pdf_url": paper.pdf_url,
                        "categories": list(paper.categories),
                        "query": query,
                        "abstract": paper.summary[:500] + "..."
                    }
                    
                    all_papers.append(paper_info)
                    print(f"  ✓ {paper.title[:70]}...")
                    print(f"    Relevance: {relevance_score}/9")
                
        except Exception as e:
            print(f"  ❌ Error searching: {e}")
            continue
    
    # Sort by relevance
    all_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"\n\n🎯 Total relevant papers found: {len(all_papers)}")
    
    # Download top papers
    max_downloads = min(10, len(all_papers))
    downloaded_papers = []
    
    print(f"\n📥 Downloading top {max_downloads} papers...\n")
    sys.stdout.flush()
    
    for i, paper_info in enumerate(all_papers[:max_downloads], 1):
        paper_id = paper_info["id"]
        print(f"[{i}/{max_downloads}] {paper_info['title'][:70]}...")
        print(f"  Relevance: {paper_info['relevance_score']}/9")
        sys.stdout.flush()
        
        try:
            # Download PDF
            pdf_path = granger_path / f"{paper_id}.pdf"
            
            if not pdf_path.exists():
                print(f"  ⬇️  Downloading PDF...")
                sys.stdout.flush()
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
                paper.download_pdf(dirpath=str(granger_path), filename=f"{paper_id}.pdf")
                print(f"  ✓ Downloaded: {pdf_path.name}")
            else:
                print(f"  ✓ PDF already exists")
            
            # Convert to markdown
            print(f"  📄 Converting to markdown...")
            sys.stdout.flush()
            
            try:
                md_text = pymupdf4llm.to_markdown(str(pdf_path))
                md_path = granger_path / f"{paper_id}.md"
                
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {paper_info['title']}\n\n")
                    f.write(f"**Authors:** " + ", ".join(paper_info['authors']) + "\n\n")
                    f.write(f"**Published:** {paper_info['published']}\n\n")
                    f.write(f"**Categories:** " + ", ".join(paper_info['categories']) + "\n\n")
                    f.write(f"**Relevance Score:** {paper_info['relevance_score']}/9\n\n")
                    f.write("---\n\n")
                    f.write(md_text)
                
                paper_info["converted"] = True
                paper_info["markdown_path"] = f"{paper_id}.md"
                downloaded_papers.append(paper_info)
                print(f"  ✓ Converted to markdown: {md_path.name}")
                
            except Exception as e:
                print(f"  ❌ Conversion error: {e}")
                paper_info["converted"] = False
                downloaded_papers.append(paper_info)
                
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            continue
        
        print()  # Empty line between papers
    
    # Save metadata
    metadata_path = granger_path / "granger_papers_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump({
            "download_date": datetime.now().isoformat(),
            "total_found": len(all_papers),
            "downloaded": len(downloaded_papers),
            "papers": downloaded_papers
        }, f, indent=2)
    
    print(f"\n✅ Download complete!")
    print(f"📁 Papers saved to: {granger_path}")
    print(f"📊 Metadata saved to: {metadata_path.name}")
    print(f"\nSummary:")
    print(f"  - Papers found: {len(all_papers)}")
    print(f"  - Papers downloaded: {len(downloaded_papers)}")
    print(f"  - Papers converted: {sum(1 for p in downloaded_papers if p.get('converted'))}")
    
    # Print top papers
    print(f"\n🏆 Top papers by relevance:")
    for i, paper in enumerate(downloaded_papers[:5], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Relevance: {paper['relevance_score']}/9")
        if paper.get('converted'):
            print(f"   📄 File: {paper['id']}.md")
        else:
            print(f"   📄 File: {paper['id']}.pdf (not converted)")

if __name__ == "__main__":
    download_papers()
