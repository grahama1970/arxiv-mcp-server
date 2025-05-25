# Task 002: Refactor ArXiv MCP Server to 3-Layer Architecture

**Task ID**: 3layer_refactor_arxiv
**Goal**: Transform current structure into clean 3-layer architecture without breaking functionality
**Branch**: feature/3-layer-architecture

## Working Code Example - Core Layer Pattern

```python
# COPY THIS PATTERN FOR EACH CORE MODULE:
# File: src/arxiv_mcp_server/core/search.py

"""
ArXiv Search Core Functionality
==============================

Pure business logic for searching ArXiv papers.

Dependencies:
- arxiv: https://github.com/lukasschwab/arxiv.py
- python-dateutil: Date parsing

Sample Input:
    query = "quantum computing"
    max_results = 5
    date_from = "2023-01-01"

Expected Output:
    List of paper dictionaries with id, title, authors, etc.
"""

import arxiv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser


def search_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    categories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search ArXiv papers with filters."""
    # Build search client
    client = arxiv.Client()
    
    # Build query with date filters
    search_query = query
    if date_from or date_to:
        if date_from:
            search_query += f' AND submittedDate:[{date_from.replace("-", "")} TO '
        else:
            search_query += ' AND submittedDate:[19900101 TO '
            
        if date_to:
            search_query += f'{date_to.replace("-", "")}]'
        else:
            search_query += '30000101]'
    
    # Add category filters
    if categories:
        cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
        search_query = f'({search_query}) AND ({cat_query})'
    
    # Map sort options
    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted": arxiv.SortCriterion.SubmittedDate,
        "lastUpdated": arxiv.SortCriterion.LastUpdatedDate
    }
    sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
    
    # Create search
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=sort_criterion,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Execute search and format results
    papers = []
    for result in client.results(search):
        papers.append({
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary,
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "categories": result.categories,
            "primary_category": result.primary_category,
            "pdf_url": result.pdf_url,
            "entry_url": result.entry_id,
            "comment": result.comment,
            "journal_ref": result.journal_ref,
            "doi": result.doi
        })
    
    return papers


# Validation
if __name__ == "__main__":
    import sys
    
    all_validation_failures = []
    total_tests = 0
    
    print("=" * 80)
    print("VALIDATING ARXIV SEARCH CORE FUNCTIONALITY")
    print("=" * 80)
    
    # Test 1: Basic search
    total_tests += 1
    print("\nTest 1: Basic search")
    print("-" * 40)
    
    try:
        results = search_papers("quantum computing", max_results=3)
        if len(results) > 0:
            print(f"✓ Found {len(results)} papers")
            print(f"  First paper: {results[0]['title'][:60]}...")
        else:
            all_validation_failures.append("Test 1: No results returned")
    except Exception as e:
        all_validation_failures.append(f"Test 1: {str(e)}")
    
    # Test 2: Date filtered search
    total_tests += 1
    print("\nTest 2: Date filtered search")
    print("-" * 40)
    
    try:
        results = search_papers(
            "machine learning",
            max_results=5,
            date_from="2024-01-01",
            date_to="2024-12-31"
        )
        print(f"✓ Found {len(results)} papers from 2024")
    except Exception as e:
        all_validation_failures.append(f"Test 2: {str(e)}")
    
    # Final result
    print("\n" + "=" * 80)
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
```

## CLI Layer Pattern

```python
# COPY THIS PATTERN FOR CLI:
# File: src/arxiv_mcp_server/cli/app.py

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List

from ..core.search import search_papers
from .formatters import format_paper_table, print_error, print_success
from .validators import validate_date_format, validate_max_results

app = typer.Typer(help="ArXiv MCP Server CLI")
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(10, "--max", "-m", help="Maximum results"),
    sort_by: str = typer.Option("relevance", "--sort", "-s", help="Sort by: relevance, submitted, lastUpdated"),
    date_from: Optional[str] = typer.Option(None, "--from", "-f", help="From date (YYYY-MM-DD)"),
    date_to: Optional[str] = typer.Option(None, "--to", "-t", help="To date (YYYY-MM-DD)")
):
    """Search ArXiv papers."""
    try:
        # Validate inputs
        validate_max_results(max_results)
        if date_from:
            validate_date_format(date_from)
        if date_to:
            validate_date_format(date_to)
        
        # Call core function
        with console.status("Searching ArXiv..."):
            papers = search_papers(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
                date_from=date_from,
                date_to=date_to
            )
        
        # Display results
        if papers:
            console.print(format_paper_table(papers))
            print_success(f"Found {len(papers)} papers")
        else:
            print_error("No papers found")
            
    except Exception as e:
        print_error(f"Search failed: {str(e)}")
        raise typer.Exit(1)
```

## MCP Layer Pattern

```python
# COPY THIS PATTERN FOR MCP:
# File: src/arxiv_mcp_server/mcp/handlers.py

from typing import Dict, Any, List
import mcp.types as types
from ..core.search import search_papers


async def search_papers_handler(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """MCP handler for search_papers tool."""
    # Extract arguments
    query = arguments["query"]
    max_results = arguments.get("max_results", 10)
    sort_by = arguments.get("sort_by", "relevance")
    date_from = arguments.get("date_from")
    date_to = arguments.get("date_to")
    categories = arguments.get("categories")
    
    # Call core function
    papers = search_papers(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
        date_from=date_from,
        date_to=date_to,
        categories=categories
    )
    
    # Format for MCP
    if not papers:
        return [types.TextContent(
            type="text",
            text="No papers found matching your search criteria."
        )]
    
    # Format results
    result_text = f"Found {len(papers)} papers:\n\n"
    for i, paper in enumerate(papers, 1):
        result_text += f"{i}. {paper['title']}\n"
        result_text += f"   Authors: {', '.join(paper['authors'][:3])}"
        if len(paper['authors']) > 3:
            result_text += f" and {len(paper['authors']) - 3} others"
        result_text += f"\n   Published: {paper['published'][:10]}\n"
        result_text += f"   arXiv ID: {paper['id']}\n"
        result_text += f"   PDF: {paper['pdf_url']}\n\n"
    
    return [types.TextContent(type="text", text=result_text)]
```

## Migration Steps

### Step 1: Create Core Modules

```bash
# Create all core modules
cd /home/graham/workspace/mcp-servers/arxiv-mcp-server

# Search functionality
cp src/arxiv_mcp_server/tools/search.py src/arxiv_mcp_server/core/search.py
# Extract just the search logic, remove MCP imports

# Download functionality  
cp src/arxiv_mcp_server/tools/download.py src/arxiv_mcp_server/core/download.py
# Extract download logic, remove handlers

# Continue for all tools...
```

### Step 2: Update Imports in Core

```python
# OLD IMPORTS (remove these):
import mcp.types as types
from ..server import app
from ..config import Settings

# NEW IMPORTS (use these):
from typing import Dict, Any, List, Optional
# Only standard library and direct dependencies
```

### Step 3: Create CLI Commands

```python
# For each tool, create a CLI command:
@app.command()
def download(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    converter: str = typer.Option("pymupdf4llm", help="PDF converter")
):
    """Download and convert an ArXiv paper."""
    # Call core.download.download_paper()
```

### Step 4: Create MCP Handlers

```python
# File: src/arxiv_mcp_server/mcp/handlers.py
# One handler per tool, all in one file initially

async def download_paper_handler(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handler for download_paper tool."""
    from ..core.download import download_paper
    # Implementation
```

## Common Issues & Solutions

### Issue 1: Circular imports
```python
# Solution: Use absolute imports in core
# Bad:  from ..config import settings
# Good: Pass settings as parameter

def search_papers(query: str, storage_path: Path = None):
    storage_path = storage_path or Path.home() / ".arxiv_papers"
```

### Issue 2: MCP types in core
```python
# Solution: Return plain Python types from core
# Bad:  return [types.TextContent(...)]
# Good: return {"text": "...", "type": "text"}

# Then convert in MCP layer:
return [types.TextContent(**result) for result in core_results]
```

### Issue 3: Async in core when not needed
```python
# Solution: Make core functions sync unless truly async
# Bad:  async def search_papers() -> List[Dict]:
# Good: def search_papers() -> List[Dict]:

# If needed, wrap in MCP layer:
async def handler(args):
    result = await asyncio.to_thread(core_function, args)
```

## Validation Requirements

```bash
# After each phase, run these tests:

# 1. Core layer tests (new)
python -m arxiv_mcp_server.core.search
python -m arxiv_mcp_server.core.download
# Each should exit with code 0

# 2. CLI tests
arxiv-cli search "quantum computing" --max 5
arxiv-cli download 2401.12345
# Should display formatted output

# 3. Existing tests must pass
cd /home/graham/workspace/mcp-servers/arxiv-mcp-server
export PYTHONPATH=/home/graham/workspace/mcp-servers/arxiv-mcp-server/src
uv run pytest tests/ -v

# 4. MCP server must start
arxiv-mcp-server
# Should show "Server running on stdio"
```

## File Mapping

| Current Location | New Core Location | New CLI Location | New MCP Location |
|-----------------|-------------------|------------------|------------------|
| tools/search.py | core/search.py | cli/app.py (search cmd) | mcp/handlers.py |
| tools/download.py | core/download.py | cli/app.py (download cmd) | mcp/handlers.py |
| tools/comparative_analysis.py | core/analysis.py | cli/app.py (compare cmd) | mcp/handlers.py |
| tools/paper_similarity.py | core/similarity.py | cli/app.py (similar cmd) | mcp/handlers.py |
| tools/research_support.py | core/research.py | cli/app.py (find-support cmd) | mcp/handlers.py |
| converters.py | core/converters.py | - | - |
| llm_providers.py | core/llm.py | - | - |

## Success Criteria

- [ ] All core modules have validation that passes
- [ ] CLI commands work with rich formatting
- [ ] MCP server starts and responds to queries
- [ ] All 71 tests still pass
- [ ] No circular imports
- [ ] Clean separation between layers

## Anti-Patterns to Avoid

❌ Importing MCP types in core layer
❌ Importing CLI stuff in core layer  
❌ Business logic in CLI or MCP layers
❌ Breaking existing functionality
❌ Changing external APIs

## Good Patterns to Follow

✅ Pure functions in core layer
✅ All I/O in CLI/MCP layers
✅ Validation at boundaries
✅ Type hints everywhere
✅ Each file < 500 lines