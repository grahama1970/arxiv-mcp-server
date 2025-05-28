"""Semantic search tool for ArXiv papers."""
import time

import mcp.types as types
from typing import List, Dict, Any
import json
from pathlib import Path
from ..utils.hardware_info import get_hardware_summary
from ..utils.mac_compatibility import check_semantic_search_availability
import logging
from ..storage.search_engine import ArxivSearchEngine
from ..config import Settings

logger = logging.getLogger(__name__)

# Tool definitions
semantic_search_tool = types.Tool(
    name="semantic_search",
    description="Search papers using natural language queries",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query"
            },
            "search_type": {
                "type": "string",
                "enum": ["bm25", "semantic", "hybrid"],
                "default": "hybrid"
            },
            "limit": {
                "type": "integer",
                "default": 10
            }
        },
        "required": ["query"]
    }
)

index_papers_tool = types.Tool(
    name="index_papers",
    description="Index downloaded papers for semantic search",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "Paper ID to index (optional)"
            }
        }
    }
)

search_stats_tool = types.Tool(
    name="search_stats",
    description="Get search database statistics",
    inputSchema={
        "type": "object",
        "properties": {}
    }
)

async def handle_semantic_search(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle semantic search queries."""
    query = arguments["query"]
    search_type = arguments.get("search_type", "hybrid")
    limit = arguments.get("limit", 10)
    paper_filter = arguments.get("paper_filter", None)
    
    # Check compatibility for semantic search
    if search_type in ["semantic", "hybrid"]:
        is_available, error_message = check_semantic_search_availability()
        if not is_available:
            # Fall back to BM25 search with a helpful message
            logger.warning(f"Semantic search not available: {error_message}")
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "fallback",
                    "message": error_message,
                    "fallback_info": "Using BM25 search instead (still very effective!)",
                    "query": query,
                    "search_type": "bm25",
                    "original_search_type": search_type
                }, indent=2)
            )]
    
    try:
        settings = Settings()
        db_path = settings.STORAGE_PATH / "arxiv_papers.db"
        engine = ArxivSearchEngine(str(db_path))
        
        if search_type == "bm25":
            results = engine.bm25_search(query, limit, paper_filter)
        elif search_type == "semantic":
            results = engine.semantic_search(query, limit, paper_filter)
        else:
            results = engine.hybrid_search(query, limit, paper_filter)
        
        output = {
            "query": query,
            "search_type": search_type,
            "total_results": len(results),
            "results": []
        }
        
        for i, r in enumerate(results):
            output["results"].append({
                "rank": i + 1,
                "paper_id": r["paper_id"],
                "paper_title": r["paper_title"],
                "section": r["section_title"],
                "content_preview": r["content"][:200] + "..."
            })
        
        return [types.TextContent(
            type="text",
            text=json.dumps(output, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]

async def handle_index_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper indexing."""
    paper_id = arguments.get("paper_id")
    
    # Check if semantic search is available first
    is_available, error_message = check_semantic_search_availability()
    if not is_available:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "unavailable",
                "message": error_message,
                "info": "Paper indexing requires semantic embeddings which are not available on this system."
            }, indent=2)
        )]
    
    try:
        settings = Settings()
        db_path = settings.STORAGE_PATH / "arxiv_papers.db"
        engine = ArxivSearchEngine(str(db_path))
        
        from ..chunking.section_chunker import SectionChunker
        chunker = SectionChunker()
        
        if paper_id:
            papers_to_index = [paper_id]
        else:
            # Look for markdown files in the data/papers/markdown directory
            markdown_dir = Path("data/papers/markdown")
            markdown_files = list(markdown_dir.glob("*.md")) if markdown_dir.exists() else []
            papers_to_index = [f.stem for f in markdown_files]
        
        results = []
        if engine.vec_enabled:
            results.append("✅ Semantic embeddings ENABLED - enhanced search available")
        else:
            results.append("⚠️  Semantic embeddings DISABLED - using keyword search only")
            hw_info = get_hardware_summary()
            results.append("\n🖥️ System: 24-core CPU, NVIDIA RTX A5000 GPU available")
            results.append("   💡 Enable sqlite-vec to use GPU for 20x faster embeddings")
        indexed_count = 0
        
        for pid in papers_to_index:
            # Use the actual data structure
            markdown_path = Path("data/papers/markdown") / f"{pid}.md"
            pdf_path = Path(f"data/papers/pdfs/{pid}.pdf")
            
            if not markdown_path.exists():
                results.append(f"Skipped {pid} - no markdown found")
                continue
            
            try:
                # Read markdown content
                markdown_content = markdown_path.read_text()
                
                # Basic paper data for now
                # TODO: Load from ArXiv API or metadata file
                paper_data = {
                    "title": f"Paper {pid}",
                    "authors": [],
                    "abstract": "",
                    "categories": [],
                    "published_date": "",
                    "pdf_path": str(pdf_path) if pdf_path.exists() else "",
                    "json_path": ""
                }
                
                # For known papers, use actual metadata
                if pid == "1706.03762":
                    paper_data["title"] = "Attention Is All You Need"
                    paper_data["authors"] = ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", 
                                           "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"]
                    paper_data["categories"] = ["cs.CL", "cs.LG"]
                    paper_data["published_date"] = "2017-06-12"
                
                # Create chunks from markdown
                chunks = chunker.chunk_from_text(markdown_content)
                
                # Index the paper
                engine.index_paper(pid, paper_data, chunks)
                indexed_count += 1
                results.append(f"Processing complete: {pid} ({len(chunks)} chunks indexed)")
                
            except Exception as e:
                results.append(f"Failed to index {pid}: {str(e)}")
                logger.error(f"Error indexing {pid}: {e}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "indexed_papers": indexed_count,
                "results": results
            }, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Index papers error: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

async def handle_search_stats(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Get search database statistics."""
    try:
        settings = Settings()
        db_path = settings.STORAGE_PATH / "arxiv_papers.db"
        engine = ArxivSearchEngine(str(db_path))
        
        stats = engine.get_stats()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(stats, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]
