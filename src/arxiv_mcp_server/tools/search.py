"""Search functionality for the arXiv MCP server."""

import arxiv
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dateutil import parser
import mcp.types as types
from ..config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

search_tool = types.Tool(
    name="search_papers",
    description="Search for papers on arXiv with advanced filtering",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer"},
            "date_from": {"type": "string"},
            "date_to": {"type": "string"},
            "categories": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["query"],
    },
)


def _is_within_date_range(
    date: datetime, start: Optional[datetime], end: Optional[datetime]
) -> bool:
    """Check if a date falls within the specified range."""
    if start and not start.tzinfo:
        start = start.replace(tzinfo=timezone.utc)
    if end and not end.tzinfo:
        end = end.replace(tzinfo=timezone.utc)

    if start and date < start:
        return False
    if end and date > end:
        return False
    return True


def _process_paper(paper: arxiv.Result) -> Dict[str, Any]:
    """Process paper information with resource URI."""
    try:
        return {
            "id": paper.get_short_id(),
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "abstract": paper.summary,
            "categories": paper.categories,
            "published": paper.published.isoformat() if paper.published else None,
            "url": paper.pdf_url,
            "resource_uri": f"arxiv://{paper.get_short_id()}",
        }
    except Exception as e:
        logger.error(f"Error processing paper: {e}")
        return {
            "id": "unknown",
            "title": "Error processing paper",
            "authors": [],
            "abstract": str(e),
            "categories": [],
            "published": None,
            "url": None,
            "resource_uri": None,
        }


async def handle_search(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper search requests with improved error handling."""
    logger.info(f"Search request received with arguments: {arguments}")
    
    try:
        # Validate required arguments
        query = arguments.get("query", "").strip()
        if not query:
            logger.warning("Empty query provided")
            return [
                types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "total_results": 0, 
                        "papers": [],
                        "message": "Empty query provided"
                    }, indent=2)
                )
            ]
        
        # Get max_results with validation
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)
        logger.debug(f"Max results set to: {max_results}")

        # Build search query with category filtering
        if categories := arguments.get("categories"):
            category_filter = " OR ".join(f"cat:{cat}" for cat in categories)
            query = f"({query}) AND ({category_filter})"
            logger.debug(f"Query with categories: {query}")

        # Parse date filters
        date_from = None
        date_to = None
        try:
            if "date_from" in arguments and arguments["date_from"]:
                date_from = parser.parse(arguments["date_from"]).replace(tzinfo=timezone.utc)
                logger.debug(f"Date from: {date_from}")
            if "date_to" in arguments and arguments["date_to"]:
                date_to = parser.parse(arguments["date_to"]).replace(tzinfo=timezone.utc)
                logger.debug(f"Date to: {date_to}")
        except (ValueError, TypeError) as e:
            logger.error(f"Date parsing error: {e}")
            return [
                types.TextContent(
                    type="text", 
                    text=json.dumps({
                        "error": f"Invalid date format: {str(e)}",
                        "total_results": 0,
                        "papers": []
                    }, indent=2)
                )
            ]

        # Create ArXiv client with custom settings
        client = arxiv.Client(
            page_size=100,
            delay_seconds=0.5,  # Be respectful to ArXiv servers
            num_retries=3
        )
        
        # Create search object - get extra results to account for date filtering
        search = arxiv.Search(
            query=query,
            max_results=max_results * 2 if (date_from or date_to) else max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        logger.info(f"Executing ArXiv search for query: {query}")
        
        # Process results
        results = []
        processed_count = 0
        
        try:
            for paper in client.results(search):
                processed_count += 1
                logger.debug(f"Processing paper {processed_count}: {paper.title[:50]}...")
                
                if _is_within_date_range(paper.published, date_from, date_to):
                    paper_data = _process_paper(paper)
                    results.append(paper_data)
                    logger.debug(f"Added paper: {paper_data['id']}")
                
                if len(results) >= max_results:
                    logger.info(f"Reached max results limit: {max_results}")
                    break
                    
        except Exception as e:
            logger.error(f"Error during search iteration: {e}", exc_info=True)
            # Return partial results if we have any
            if results:
                logger.warning(f"Returning {len(results)} partial results after error")
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Search error: {str(e)}",
                            "total_results": 0,
                            "papers": []
                        }, indent=2)
                    )
                ]

        logger.info(f"Search completed. Found {len(results)} papers (processed {processed_count} total)")
        
        # Prepare response
        response_data = {
            "total_results": len(results), 
            "papers": results,
            "query": arguments.get("query"),
            "processed_count": processed_count
        }

        return [
            types.TextContent(
                type="text", 
                text=json.dumps(response_data, indent=2)
            )
        ]

    except Exception as e:
        logger.error(f"Unexpected error in handle_search: {e}", exc_info=True)
        return [
            types.TextContent(
                type="text", 
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "total_results": 0,
                    "papers": []
                }, indent=2)
            )
        ]


# Add a diagnostics function
async def handle_diagnostics(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Return diagnostic information about the ArXiv MCP server."""
    import sys
    import os
    from pathlib import Path
    
    logger.info("Diagnostics requested")
    
    try:
        # Test ArXiv connectivity
        arxiv_status = "unknown"
        arxiv_error = None
        try:
            client = arxiv.Client(num_retries=1)
            search = arxiv.Search(query="test", max_results=1)
            papers = list(client.results(search))
            arxiv_status = "connected"
            logger.info(f"ArXiv API test successful, found {len(papers)} papers")
        except Exception as e:
            arxiv_status = "error"
            arxiv_error = str(e)
            logger.error(f"ArXiv API test failed: {e}")
        
        # Get storage info
        storage_path = Path(settings.STORAGE_DIR)
        paper_count = 0
        total_size = 0
        
        if storage_path.exists():
            pdf_count = len(list(storage_path.glob("pdfs/*.pdf")))
            md_count = len(list(storage_path.glob("markdown/*.md")))
            paper_count = max(pdf_count, md_count)
            
            for file in storage_path.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
        
        diagnostics = {
            "server_version": "1.0.0",
            "python_version": sys.version.split()[0],
            "storage_path": str(storage_path),
            "papers_stored": paper_count,
            "storage_size_mb": round(total_size / (1024 * 1024), 2),
            "arxiv_api_status": arxiv_status,
            "arxiv_api_error": arxiv_error,
            "max_results_limit": settings.MAX_RESULTS,
            "environment": {
                "os": os.name,
                "platform": sys.platform,
            }
        }
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(diagnostics, indent=2)
            )
        ]
        
    except Exception as e:
        logger.error(f"Error in diagnostics: {e}", exc_info=True)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"Diagnostics error: {str(e)}"}, indent=2)
            )
        ]


diagnostics_tool = types.Tool(
    name="get_diagnostics",
    description="Get diagnostic information about the ArXiv MCP server",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
