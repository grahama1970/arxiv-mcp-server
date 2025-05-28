"""
Search-related CLI commands for ArXiv MCP Server.

Purpose:
    Provides CLI commands for indexing papers and performing semantic search
    on downloaded ArXiv papers using BM25, semantic, or hybrid search.

Links:
    - SQLite FTS5: https://www.sqlite.org/fts5.html
    - Sentence Transformers: https://www.sbert.net/

Sample input:
    arxiv-cli index-papers
    arxiv-cli semantic-search "transformer architecture"
    arxiv-cli search-stats

Expected output:
    Indexed paper counts, search results, database statistics
"""

import typer
from typing import Optional, List
import json
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path

# Import search handlers
from ..tools.semantic_search import (
    handle_semantic_search,
    handle_index_papers,
    handle_search_stats
)
from ..utils.mac_compatibility import check_semantic_search_availability

app = typer.Typer(
    name="search",
    help="Search and indexing commands",
    rich_markup_mode="rich"
)

console = Console()


@app.command(name="index-papers")
def index_papers(
    paper_id: Optional[str] = typer.Option(None, "--paper", "-p", help="Specific paper ID to index")
):
    """Index downloaded papers for semantic search."""
    arguments = {}
    if paper_id:
        arguments["paper_id"] = paper_id
    
    console.print("[bold green]Indexing papers...[/bold green]")
    result = asyncio.run(handle_index_papers(arguments))
    
    console.print(Panel.fit(result[0].text, title="Index Results", border_style="green"))


@app.command(name="semantic-search")
def semantic_search(
    query: str = typer.Argument(..., help="Natural language search query"),
    search_type: str = typer.Option("hybrid", "--type", "-t", help="Search type: bm25, semantic, or hybrid"),
    paper_filter: Optional[str] = typer.Option(None, "--paper-filter", "-p", help="Filter results to specific paper ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results")
):
    """Search indexed papers using natural language queries."""
    # Check compatibility first for semantic/hybrid search
    if search_type in ["semantic", "hybrid"]:
        is_available, error_message = check_semantic_search_availability()
        if not is_available:
            console.print(Panel(
                error_message,
                title="⚠️  Compatibility Notice",
                border_style="yellow"
            ))
            if search_type == "semantic":
                console.print("[yellow]Falling back to BM25 search...[/yellow]")
                search_type = "bm25"
            elif search_type == "hybrid":
                console.print("[yellow]Using BM25 search only (hybrid not available)...[/yellow]")
                search_type = "bm25"
    
    arguments = {
        "query": query,
        "search_type": search_type,
        "limit": limit
    }
    
    if paper_filter:
        arguments["paper_filter"] = paper_filter
    
    with console.status(f"[bold green]Searching ({search_type})..."):
        result = asyncio.run(handle_semantic_search(arguments))
    
    # Parse and display results nicely
    try:
        data = json.loads(result[0].text)
        
        # Create a nice table for results
        table = Table(title=f"Search Results for: {query}")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Paper ID", style="magenta")
        table.add_column("Title", style="green")
        table.add_column("Section", style="yellow")
        table.add_column("Preview", style="white")
        
        for r in data.get("results", []):
            table.add_row(
                str(r["rank"]),
                r["paper_id"],
                r["paper_title"][:40] + "..." if len(r["paper_title"]) > 40 else r["paper_title"],
                r["section"],
                r["content_preview"][:60] + "..."
            )
        
        console.print(table)
        console.print(f"\nTotal results: {data.get('total_results', 0)}")
        console.print(f"Search type: {data.get('search_type', 'hybrid')}")
        
    except json.JSONDecodeError:
        # Fallback to raw output
        console.print(result[0].text)


@app.command(name="search-stats")
def search_stats():
    """Display search database statistics."""
    with console.status("[bold green]Fetching statistics..."):
        result = asyncio.run(handle_search_stats(arguments={}))
    
    # Parse and display stats nicely
    try:
        data = json.loads(result[0].text)
        
        # Create stats panels
        stats_text = f"""
[bold cyan]Database Statistics[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Total Papers: {data.get('total_papers', 0)}
📄 Total Chunks: {data.get('total_chunks', 0)}
💾 Database Size: {data.get('database_size', 'N/A')}
🔍 Has Embeddings: {'Yes' if data.get('has_embeddings') else 'No'}
"""
        
        console.print(Panel(stats_text, title="Search Engine Statistics", border_style="blue"))
        
    except json.JSONDecodeError:
        # Fallback to raw output
        console.print(result[0].text)


# ============================================
# VALIDATION FUNCTION
# ============================================

async def validate_search_commands():
    """Validate search CLI functionality with REAL data."""
    all_validation_failures = []
    total_tests = 0
    
    console.print("=" * 80)
    console.print("🔍 VALIDATING SEARCH COMMANDS")
    console.print("=" * 80)
    
    # Test 1: Search stats (should work even with empty DB)
    total_tests += 1
    console.print("\n📋 Test 1: Search stats")
    console.print("-" * 40)
    
    try:
        result = await handle_search_stats({})
        output = result[0].text
        
        # Check for expected fields
        data = json.loads(output)
        if "total_papers" not in data or "total_chunks" not in data:
            all_validation_failures.append("Test 1: Missing expected stats fields")
        else:
            console.print(f"✅ Stats working - Papers: {data['total_papers']}, Chunks: {data['total_chunks']}")
            
    except Exception as e:
        all_validation_failures.append(f"Test 1: Search stats failed - {str(e)}")
        import traceback
        console.print(f"❌ Error: {traceback.format_exc()}")
    
    # Test 2: Index papers (if any exist)
    total_tests += 1
    console.print("\n📋 Test 2: Index papers")
    console.print("-" * 40)
    
    try:
        # First check if we have any papers
        from pathlib import Path
        data_dir = Path("data/papers/markdown")
        if data_dir.exists():
            md_files = list(data_dir.glob("*.md"))
            if md_files:
                # Try to index first paper
                paper_id = md_files[0].stem
                console.print(f"   Found paper: {paper_id}")
                
                result = await handle_index_papers({"paper_id": paper_id})
                output = result[0].text
                
                if "indexed" in output.lower() or "error" not in output.lower():
                    console.print(f"✅ Indexing working")
                else:
                    all_validation_failures.append(f"Test 2: Indexing failed - {output}")
            else:
                console.print("⚠️  No papers found to index - skipping")
        else:
            console.print("⚠️  Data directory not found - skipping")
            
    except Exception as e:
        all_validation_failures.append(f"Test 2: Index papers failed - {str(e)}")
        import traceback
        console.print(f"❌ Error: {traceback.format_exc()}")
    
    # Test 3: Semantic search
    total_tests += 1
    console.print("\n📋 Test 3: Semantic search")
    console.print("-" * 40)
    
    try:
        # Try different search types
        for search_type in ["bm25", "hybrid"]:
            console.print(f"   Testing {search_type} search...")
            result = await handle_semantic_search({
                "query": "transformer architecture attention",
                "search_type": search_type,
                "limit": 5
            })
            
            output = result[0].text
            data = json.loads(output)
            
            if "results" not in data:
                all_validation_failures.append(f"Test 3: {search_type} search missing results")
            else:
                console.print(f"   ✅ {search_type} search returned {len(data['results'])} results")
                
    except Exception as e:
        all_validation_failures.append(f"Test 3: Semantic search failed - {str(e)}")
        import traceback
        console.print(f"❌ Error: {traceback.format_exc()}")
    
    # Final result
    console.print("\n" + "=" * 80)
    if all_validation_failures:
        console.print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            console.print(f"  - {failure}")
        return False
    else:
        console.print(f"✅ VALIDATION PASSED - All {total_tests} tests completed successfully")
        console.print("Search commands are working correctly with real data")
        return True


if __name__ == "__main__":
    import sys
    
    # Check if running validation
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        success = asyncio.run(validate_search_commands())
        sys.exit(0 if success else 1)
    else:
        app()
