import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import mcp.types as types
from ..config import Settings

settings = Settings()

find_similar_papers_tool = types.Tool(
    name="find_similar_papers",
    description="Find papers similar to a given paper by abstract content, authors, or keywords.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID to find similar papers for",
            },
            "similarity_type": {
                "type": "string",
                "description": "Type of similarity to use",
                "enum": ["content", "authors", "keywords", "combined"],
                "default": "content",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of similar papers to return",
                "default": 5,
            },
            "min_similarity": {
                "type": "number",
                "description": "Minimum similarity score (0-1)",
                "default": 0.3,
            },
        },
        "required": ["paper_id"],
    },
)

def extract_abstract(content: str) -> str:
    """Extract abstract from paper content."""
    # Look for abstract section
    abstract_start = content.lower().find("abstract")
    if abstract_start == -1:
        # Use first 1000 chars as fallback
        return content[:1000]
    
    # Find end of abstract (usually Introduction or next section)
    abstract_end = content.lower().find("introduction", abstract_start)
    if abstract_end == -1:
        abstract_end = content.lower().find("\n## ", abstract_start)
    if abstract_end == -1:
        abstract_end = abstract_start + 2000  # Max 2000 chars
    
    return content[abstract_start:abstract_end].strip()

def compute_content_similarity(papers: List[Dict[str, Any]], target_idx: int) -> List[tuple]:
    """Compute content similarity using TF-IDF."""
    # Extract abstracts
    abstracts = [extract_abstract(p.get("content", "")) for p in papers]
    
    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(abstracts)
    
    # Compute similarities
    similarities = cosine_similarity(tfidf_matrix[target_idx:target_idx+1], tfidf_matrix).flatten()
    
    # Get top similar papers (excluding self)
    similar_indices = []
    for idx, score in enumerate(similarities):
        if idx != target_idx and score > 0:
            similar_indices.append((idx, score))
    
    return sorted(similar_indices, key=lambda x: x[1], reverse=True)

def compute_author_similarity(papers: List[Dict[str, Any]], target_idx: int) -> List[tuple]:
    """Compute similarity based on shared authors."""
    target_authors = set(papers[target_idx].get("authors", []))
    if not target_authors:
        return []
    
    similar_indices = []
    for idx, paper in enumerate(papers):
        if idx == target_idx:
            continue
        
        paper_authors = set(paper.get("authors", []))
        if paper_authors:
            # Jaccard similarity for authors
            intersection = target_authors.intersection(paper_authors)
            union = target_authors.union(paper_authors)
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity > 0:
                similar_indices.append((idx, similarity))
    
    return sorted(similar_indices, key=lambda x: x[1], reverse=True)

async def handle_find_similar_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper similarity requests."""
    paper_id = arguments["paper_id"]
    similarity_type = arguments.get("similarity_type", "content")
    top_k = arguments.get("top_k", 5)
    min_similarity = arguments.get("min_similarity", 0.3)
    
    # Load all papers in storage
    storage_path = settings.STORAGE_PATH
    papers = []
    target_idx = None
    
    # Scan storage directory
    for md_file in storage_path.glob("*.md"):
        try:
            file_paper_id = md_file.stem
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to load metadata if exists
            meta_file = storage_path / f"{file_paper_id}_metadata.json"
            metadata = {}
            if meta_file.exists():
                with open(meta_file, "r") as f:
                    metadata = json.load(f)
            
            paper_data = {
                "id": file_paper_id,
                "content": content,
                "authors": metadata.get("authors", []),
                "title": metadata.get("title", file_paper_id),
            }
            
            papers.append(paper_data)
            
            if file_paper_id == paper_id:
                target_idx = len(papers) - 1
                
        except Exception:
            continue
    
    if target_idx is None:
        return [types.TextContent(
            type="text",
            text=f"Error: Paper {paper_id} not found. Please download it first."
        )]
    
    if len(papers) < 2:
        return [types.TextContent(
            type="text",
            text="Not enough papers in storage to find similarities. Download more papers first."
        )]
    
    # Compute similarities based on type
    if similarity_type == "content":
        similar_papers = compute_content_similarity(papers, target_idx)
    elif similarity_type == "authors":
        similar_papers = compute_author_similarity(papers, target_idx)
    else:  # combined
        content_sim = compute_content_similarity(papers, target_idx)
        author_sim = compute_author_similarity(papers, target_idx)
        
        # Combine scores
        combined_scores = {}
        for idx, score in content_sim:
            combined_scores[idx] = score * 0.7  # 70% weight for content
        
        for idx, score in author_sim:
            if idx in combined_scores:
                combined_scores[idx] += score * 0.3  # 30% weight for authors
            else:
                combined_scores[idx] = score * 0.3
        
        similar_papers = [(idx, score) for idx, score in combined_scores.items()]
        similar_papers.sort(key=lambda x: x[1], reverse=True)
    
    # Filter by minimum similarity and top_k
    similar_papers = [(idx, score) for idx, score in similar_papers if score >= min_similarity][:top_k]
    
    # Format output
    if not similar_papers:
        output = f"No similar papers found with similarity >= {min_similarity}"
    else:
        output = f"Similar papers to {paper_id} ({similarity_type} similarity):\n\n"
        for idx, score in similar_papers:
            paper = papers[idx]
            output += f"• {paper['id']}: {paper['title']}\n"
            output += f"  Similarity: {score:.3f}\n"
            if paper['authors']:
                output += f"  Authors: {', '.join(paper['authors'][:3])}\n"
            output += "\n"
    
    return [types.TextContent(type="text", text=output)]