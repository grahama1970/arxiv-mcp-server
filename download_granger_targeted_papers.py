#!/usr/bin/env python3
"""Download highly targeted papers to support GRANGER project claims."""

import arxiv
from pathlib import Path
import sys
import os
import json
from datetime import datetime
import pymupdf4llm

print("Starting GRANGER targeted paper search...")
sys.stdout.flush()

# Highly targeted queries based on GRANGER's specific claims and needs
TARGETED_QUERIES = {
    # Cost impact and large-scale requirement failures
    "cost_impact": [
        "requirements defects cost billions software",
        "specification errors project overruns defense",
        "F-35 requirements engineering failures",
        "large scale requirements validation challenges"
    ],
    
    # Graph-based requirements analysis
    "graph_based": [
        "graph neural network requirements engineering",
        "knowledge graph requirements traceability",
        "graph-based specification analysis",
        "requirements dependency graph analysis"
    ],
    
    # LLM/AI for requirements contradiction
    "llm_requirements": [
        "LLM requirements engineering 2024",
        "GPT-4 specification validation",
        "transformer models requirements contradiction",
        "large language models formal verification",
        "BERT requirements inconsistency detection"
    ],
    
    # Multi-level security and classification
    "classification": [
        "multi-level security requirements engineering",
        "cross-domain requirements analysis",
        "classified specification management",
        "security classification requirements traceability"
    ],
    
    # Adversarial and supply chain
    "adversarial": [
        "adversarial requirements engineering",
        "supply chain specification attacks",
        "malicious requirements injection",
        "backdoor specifications detection"
    ],
    
    # Military/Defense specific
    "military": [
        "military systems requirements engineering",
        "defense acquisition requirements validation",
        "DO-178C DO-254 requirements verification",
        "weapon systems specification validation"
    ],
    
    # Formal methods + NLP combination
    "formal_nlp": [
        "combining formal methods natural language requirements",
        "SMT solver requirements engineering",
        "Z3 specification validation NLP",
        "formal verification natural language specifications"
    ],
    
    # Scale and performance
    "scale": [
        "100000 requirements scalability",
        "large-scale specification validation performance",
        "real-time requirements analysis",
        "distributed requirements verification"
    ]
}

def evaluate_paper_relevance(paper, category):
    """Evaluate paper relevance with detailed scoring."""
    title_lower = paper.title.lower()
    abstract_lower = paper.summary.lower()
    
    # Category-specific scoring
    scores = {
        "recency": 0,
        "category_match": 0,
        "granger_alignment": 0,
        "credibility": 0
    }
    
    # Recency score (papers from 2022-2024 preferred)
    year = paper.published.year
    if year >= 2024:
        scores["recency"] = 3
    elif year >= 2023:
        scores["recency"] = 2
    elif year >= 2022:
        scores["recency"] = 1
    
    # Category-specific keywords
    category_keywords = {
        "cost_impact": ["billion", "cost", "overrun", "defect", "failure", "expensive"],
        "graph_based": ["graph", "network", "node", "edge", "dependency", "traceability"],
        "llm_requirements": ["llm", "gpt", "bert", "transformer", "language model", "attention"],
        "classification": ["classification", "security", "clearance", "classified", "multi-level"],
        "adversarial": ["adversarial", "attack", "malicious", "backdoor", "supply chain"],
        "military": ["military", "defense", "weapon", "dod", "aerospace", "aviation"],
        "formal_nlp": ["formal", "smt", "z3", "sat solver", "natural language", "nlp"],
        "scale": ["scale", "large", "thousand", "performance", "distributed", "real-time"]
    }
    
    # GRANGER-specific keywords
    granger_keywords = ["requirement", "specification", "contradiction", "inconsistency", 
                       "conflict", "validation", "verification", "detection"]
    
    # Calculate category match
    if category in category_keywords:
        matches = sum(1 for kw in category_keywords[category] 
                     if kw in title_lower or kw in abstract_lower)
        scores["category_match"] = min(matches, 3)
    
    # Calculate GRANGER alignment
    granger_matches = sum(1 for kw in granger_keywords 
                         if kw in title_lower or kw in abstract_lower)
    scores["granger_alignment"] = min(granger_matches, 3)
    
    # Credibility indicators
    credibility_terms = ["ieee", "acm", "evaluation", "empirical", "case study", 
                        "industrial", "experiment", "benchmark"]
    cred_matches = sum(1 for term in credibility_terms 
                      if term in title_lower or term in abstract_lower)
    scores["credibility"] = min(cred_matches, 2)
    
    total_score = sum(scores.values())
    return total_score, scores

def download_targeted_papers():
    """Search and download papers supporting GRANGER claims."""
    
    print("\n=== Downloading Targeted Papers for GRANGER Project ===\n")
    
    # Setup
    storage_path = Path.home() / ".arxiv-mcp-server" / "papers"
    granger_path = storage_path / "granger_project" / "targeted_papers"
    granger_path.mkdir(parents=True, exist_ok=True)
    
    all_papers = []
    paper_ids_seen = set()
    
    # Search each category
    for category, queries in TARGETED_QUERIES.items():
        print(f"\n📂 Category: {category.upper()}")
        print("=" * 60)
        
        for query in queries:
            print(f"\n🔍 Searching: {query}")
            sys.stdout.flush()
            
            try:
                client = arxiv.Client()
                search = arxiv.Search(
                    query=query,
                    max_results=5,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                papers = list(client.results(search))
                print(f"  Found {len(papers)} papers")
                
                for paper in papers:
                    paper_id = paper.entry_id.split('/')[-1]
                    
                    if paper_id in paper_ids_seen:
                        continue
                    
                    paper_ids_seen.add(paper_id)
                    
                    # Evaluate relevance
                    total_score, scores = evaluate_paper_relevance(paper, category)
                    
                    # Only keep highly relevant papers (score >= 5)
                    if total_score >= 5:
                        paper_info = {
                            "id": paper_id,
                            "title": paper.title.replace('\n', ' '),
                            "authors": [author.name for author in paper.authors],
                            "published": paper.published.isoformat(),
                            "year": paper.published.year,
                            "category": category,
                            "query": query,
                            "total_score": total_score,
                            "scores": scores,
                            "pdf_url": paper.pdf_url,
                            "categories": list(paper.categories),
                            "abstract": paper.summary[:300] + "..."
                        }
                        
                        all_papers.append(paper_info)
                        print(f"  ✅ {paper.title[:60]}...")
                        print(f"     Year: {paper.published.year}, Score: {total_score}")
                        print(f"     Details: Recency={scores['recency']}, " + 
                              f"Category={scores['category_match']}, " +
                              f"GRANGER={scores['granger_alignment']}, " +
                              f"Credibility={scores['credibility']}")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
    
    # Sort by total score, then by year
    all_papers.sort(key=lambda x: (x["total_score"], x["year"]), reverse=True)
    
    print(f"\n\n🎯 Total highly relevant papers found: {len(all_papers)}")
    
    # Group by category for analysis
    by_category = {}
    for paper in all_papers:
        cat = paper["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(paper)
    
    print("\n📊 Papers by category:")
    for cat, papers in by_category.items():
        print(f"  {cat}: {len(papers)} papers")
    
    # Download top papers
    max_downloads = min(20, len(all_papers))
    downloaded_papers = []
    
    print(f"\n📥 Downloading top {max_downloads} papers...\n")
    sys.stdout.flush()
    
    for i, paper_info in enumerate(all_papers[:max_downloads], 1):
        paper_id = paper_info["id"]
        print(f"[{i}/{max_downloads}] {paper_info['title'][:70]}...")
        print(f"  Category: {paper_info['category']}, Score: {paper_info['total_score']}")
        sys.stdout.flush()
        
        try:
            # Download PDF
            pdf_path = granger_path / f"{paper_id}.pdf"
            
            if not pdf_path.exists():
                print(f"  ⬇️  Downloading PDF...")
                sys.stdout.flush()
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
                paper.download_pdf(dirpath=str(granger_path), filename=f"{paper_id}.pdf")
                print(f"  ✓ Downloaded")
            else:
                print(f"  ✓ PDF exists")
            
            # Convert to markdown
            print(f"  📄 Converting to markdown...")
            sys.stdout.flush()
            
            try:
                md_text = pymupdf4llm.to_markdown(str(pdf_path))
                md_path = granger_path / f"{paper_id}.md"
                
                # Add metadata header
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {paper_info['title']}\n\n")
                    f.write(f"**Category:** {paper_info['category']}\n")
                    f.write(f"**Score:** {paper_info['total_score']}\n")
                    f.write(f"**Year:** {paper_info['year']}\n")
                    f.write(f"**Authors:** " + ", ".join(paper_info['authors']) + "\n\n")
                    f.write(f"**Relevance Scores:**\n")
                    for k, v in paper_info['scores'].items():
                        f.write(f"- {k}: {v}\n")
                    f.write("\n---\n\n")
                    f.write(md_text)
                
                paper_info["converted"] = True
                downloaded_papers.append(paper_info)
                print(f"  ✓ Converted")
                
            except Exception as e:
                print(f"  ❌ Conversion error: {e}")
                paper_info["converted"] = False
                downloaded_papers.append(paper_info)
                
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            continue
        
        print()  # Empty line between papers
    
    # Save detailed metadata
    metadata_path = granger_path / "targeted_papers_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump({
            "search_date": datetime.now().isoformat(),
            "total_found": len(all_papers),
            "downloaded": len(downloaded_papers),
            "by_category": {cat: len(papers) for cat, papers in by_category.items()},
            "papers": downloaded_papers
        }, f, indent=2)
    
    print(f"\n✅ Download complete!")
    print(f"📁 Papers saved to: {granger_path}")
    print(f"📊 Metadata: {metadata_path.name}")
    
    # Print summary by category
    print(f"\n📈 Summary by Category:")
    for cat in TARGETED_QUERIES.keys():
        cat_papers = [p for p in downloaded_papers if p["category"] == cat]
        if cat_papers:
            print(f"\n{cat.upper()}:")
            for p in cat_papers[:3]:  # Top 3 per category
                print(f"  - {p['title'][:70]}...")
                print(f"    Score: {p['total_score']}, Year: {p['year']}")

if __name__ == "__main__":
    download_targeted_papers()
