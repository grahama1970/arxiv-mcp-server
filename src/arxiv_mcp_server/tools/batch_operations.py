import asyncio
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings
from .download import handle_download
from .search import handle_search

settings = Settings()

batch_download_tool = types.Tool(
    name="batch_download",
    description="Download multiple ArXiv papers concurrently with resource-aware processing.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ArXiv paper IDs to download",
            },
            "search_query": {
                "type": "string",
                "description": "Alternative: Search query to find papers to download",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of papers to download from search",
                "default": 10,
            },
            "max_concurrent": {
                "type": "integer",
                "description": "Maximum concurrent downloads (auto-adjusts based on CPU)",
                "default": None,
            },
            "skip_existing": {
                "type": "boolean",
                "description": "Skip papers that are already downloaded",
                "default": True,
            },
            "convert_to": {
                "type": "string",
                "description": "Convert PDFs to this format after download",
                "enum": ["markdown", "json", "both", "none"],
                "default": "markdown",
            },
        },
        "oneOf": [
            {"required": ["paper_ids"]},
            {"required": ["search_query"]}
        ],
    },
)

async def download_with_progress(paper_id: str, convert_to: str, skip_existing: bool) -> Dict[str, Any]:
    """Download a single paper with error handling."""
    result = {
        "paper_id": paper_id,
        "status": "pending",
        "message": "",
        "file_path": None,
    }
    
    try:
        # Check if already exists
        if skip_existing:
            storage_path = settings.STORAGE_PATH
            pdf_path = storage_path / f"{paper_id}.pdf"
            md_path = storage_path / f"{paper_id}.md"
            
            if pdf_path.exists() and (convert_to == "none" or md_path.exists()):
                result["status"] = "skipped"
                result["message"] = "Already downloaded"
                result["file_path"] = str(pdf_path)
                return result
        
        # Download the paper
        download_result = await handle_download({
            "paper_id": paper_id,
            "converter": "pymupdf4llm" if convert_to != "none" else None,
            "output_format": convert_to if convert_to != "none" else "markdown"
        })
        result["status"] = "success"
        result["message"] = "Downloaded successfully"
        result["file_path"] = download_result[0].text if download_result else None
        
    except Exception as e:
        result["status"] = "failed"
        result["message"] = str(e)
    
    return result

async def handle_batch_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle batch download requests."""
    # Get paper IDs either directly or from search
    paper_ids = arguments.get("paper_ids", [])
    
    if not paper_ids and "search_query" in arguments:
        # Search for papers first
        search_results = await handle_search({
            "query": arguments["search_query"],
            "max_results": arguments.get("max_results", 10)
        })
        # Extract paper IDs from search results
        import json
        results_text = search_results[0].text if search_results else "[]"
        papers = json.loads(results_text)
        paper_ids = [paper["id"] for paper in papers]
    
    if not paper_ids:
        return [types.TextContent(type="text", text="No papers to download.")]
    
    # Determine concurrency limit
    max_concurrent = arguments.get("max_concurrent")
    if max_concurrent is None:
        # Auto-adjust based on CPU count
        cpu_count = os.cpu_count() or 2
        max_concurrent = min(cpu_count * 2, 8)  # Cap at 8
    
    convert_to = arguments.get("convert_to", "markdown")
    skip_existing = arguments.get("skip_existing", True)
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_with_semaphore(paper_id: str):
        async with semaphore:
            return await download_with_progress(paper_id, convert_to, skip_existing)
    
    # Download papers concurrently
    tasks = [download_with_semaphore(paper_id) for paper_id in paper_ids]
    results = await asyncio.gather(*tasks)
    
    # Prepare summary
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    }
    
    output = f"Batch Download Complete:\n"
    output += f"- Total: {summary['total']}\n"
    output += f"- Success: {summary['success']}\n"
    output += f"- Skipped: {summary['skipped']}\n"
    output += f"- Failed: {summary['failed']}\n\n"
    
    # Add details for failed downloads
    failures = [r for r in results if r["status"] == "failed"]
    if failures:
        output += "Failed downloads:\n"
        for result in failures:
            output += f"- {result['paper_id']}: {result['message']}\n"
    
    return [types.TextContent(type="text", text=output)]