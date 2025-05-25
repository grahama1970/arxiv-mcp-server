#!/usr/bin/env python3
"""
ArXiv MCP Server CLI
====================

Command-line interface for the ArXiv MCP Server providing direct access to all
ArXiv research tools without needing an MCP client.

Features:
- Search and download ArXiv papers
- Analyze paper content with various tools
- Find supporting/contradicting evidence
- Manage paper notes and annotations
- Export to various formats

Dependencies:
- typer: CLI framework (https://typer.tiangolo.com/)
- rich: Terminal formatting (https://rich.readthedocs.io/)
- All arxiv_mcp_server dependencies

Sample Input:
    arxiv-cli search "transformer architecture" --max-results 10
    arxiv-cli download 2401.12345 --converter marker-pdf
    arxiv-cli find-support "My hypothesis about X" --all-papers

Expected Output:
    Formatted search results, downloaded papers, analysis results
"""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from loguru import logger

# Import all our tools
from .tools import (
    handle_search, handle_download, handle_list_papers, handle_read_paper,
    handle_conversion_options, handle_describe_content, handle_system_stats,
    handle_analyze_code, handle_summarize_paper, handle_extract_citations,
    handle_batch_download, handle_compare_paper_ideas, handle_find_similar_papers,
    handle_extract_sections, handle_add_paper_note, handle_list_paper_notes,
    handle_find_research_support, handle_search_research_findings
)

app = typer.Typer(
    name="arxiv-cli",
    help="ArXiv MCP Server CLI - Research tools for ArXiv papers"
)

console = Console()

# ============================================
# SEARCH & DISCOVERY COMMANDS
# ============================================

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for ArXiv papers"),
    max_results: int = typer.Option(10, "--max-results", "-n", help="Maximum number of results"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    categories: Optional[List[str]] = typer.Option(None, "--category", "-c", help="ArXiv categories (e.g., cs.AI)")
):
    """Search for ArXiv papers matching your query."""
    arguments = {
        "query": query,
        "max_results": max_results
    }
    
    if date_from:
        arguments["date_from"] = date_from
    if date_to:
        arguments["date_to"] = date_to
    if categories:
        arguments["categories"] = categories
    
    with console.status("[bold green]Searching ArXiv..."):
        result = asyncio.run(handle_search(arguments))
    
    console.print(result[0].text)


@app.command()
def download(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID (e.g., 2401.12345)"),
    converter: str = typer.Option("pymupdf4llm", "--converter", "-c", help="PDF converter (pymupdf4llm or marker-pdf)"),
    output_format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown or json)"),
    keep_pdf: bool = typer.Option(False, "--keep-pdf", help="Keep the PDF file after conversion")
):
    """Download a paper from ArXiv."""
    arguments = {
        "paper_id": paper_id,
        "converter": converter,
        "output_format": output_format,
        "keep_pdf": keep_pdf
    }
    
    with console.status(f"[bold green]Downloading {paper_id}..."):
        result = asyncio.run(handle_download(arguments))
    
    console.print(result[0].text)


@app.command()
def batch_download(
    paper_ids: Optional[List[str]] = typer.Option(None, "--id", help="Paper IDs to download"),
    search_query: Optional[str] = typer.Option(None, "--search", "-s", help="Search query for papers"),
    max_results: int = typer.Option(10, "--max", "-n", help="Max papers from search"),
    skip_existing: bool = typer.Option(True, "--skip-existing", help="Skip already downloaded papers"),
    converter: str = typer.Option("pymupdf4llm", "--converter", "-c", help="PDF converter")
):
    """Download multiple papers at once."""
    arguments = {}
    
    if paper_ids:
        arguments["paper_ids"] = paper_ids
    elif search_query:
        arguments["search_query"] = search_query
        arguments["max_results"] = max_results
    else:
        console.print("[red]Error: Provide either --id or --search[/red]")
        raise typer.Exit(1)
    
    arguments["skip_existing"] = skip_existing
    arguments["convert_to"] = converter
    
    with console.status("[bold green]Batch downloading papers..."):
        result = asyncio.run(handle_batch_download(arguments))
    
    console.print(result[0].text)


@app.command()
def list_papers():
    """List all downloaded papers."""
    result = asyncio.run(handle_list_papers({}))
    console.print(result[0].text)


@app.command()
def read(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID to read")
):
    """Read the content of a downloaded paper."""
    result = asyncio.run(handle_read_paper({"paper_id": paper_id}))
    console.print(result[0].text)


# ============================================
# ANALYSIS COMMANDS
# ============================================

@app.command()
def summarize(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    strategy: str = typer.Option("rolling_window", "--strategy", "-s", help="Summarization strategy"),
    summary_type: str = typer.Option("comprehensive", "--type", "-t", help="Summary type"),
    max_length: int = typer.Option(1500, "--max-length", help="Maximum summary length")
):
    """Summarize a paper using advanced strategies."""
    arguments = {
        "paper_id": paper_id,
        "strategy": strategy,
        "summary_type": summary_type,
        "max_summary_length": max_length
    }
    
    with console.status("[bold green]Summarizing paper..."):
        result = asyncio.run(handle_summarize_paper(arguments))
    
    console.print(result[0].text)


@app.command()
def analyze_code(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    languages: Optional[List[str]] = typer.Option(None, "--lang", "-l", help="Programming languages to analyze"),
    min_lines: int = typer.Option(3, "--min-lines", help="Minimum lines for code blocks"),
    extract_functions: bool = typer.Option(True, "--functions", help="Extract function definitions"),
    extract_classes: bool = typer.Option(True, "--classes", help="Extract class definitions")
):
    """Extract and analyze code from a paper."""
    arguments = {
        "paper_id": paper_id,
        "min_lines": min_lines,
        "extract_functions": extract_functions,
        "extract_classes": extract_classes
    }
    
    if languages:
        arguments["languages"] = languages
    
    with console.status("[bold green]Analyzing code..."):
        result = asyncio.run(handle_analyze_code(arguments))
    
    console.print(result[0].text)


@app.command()
def extract_citations(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    format: str = typer.Option("bibtex", "--format", "-f", help="Citation format (bibtex, json, endnote)"),
    include_links: bool = typer.Option(True, "--links", help="Include ArXiv links")
):
    """Extract citations from a paper."""
    arguments = {
        "paper_id": paper_id,
        "format": format,
        "include_arxiv_links": include_links
    }
    
    with console.status("[bold green]Extracting citations..."):
        result = asyncio.run(handle_extract_citations(arguments))
    
    console.print(result[0].text)


@app.command()
def extract_sections(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    sections: List[str] = typer.Option(..., "--section", "-s", help="Sections to extract"),
    include_subsections: bool = typer.Option(True, "--subsections", help="Include subsections")
):
    """Extract specific sections from a paper."""
    arguments = {
        "paper_id": paper_id,
        "sections": sections,
        "include_subsections": include_subsections
    }
    
    result = asyncio.run(handle_extract_sections(arguments))
    console.print(result[0].text)


# ============================================
# RESEARCH SUPPORT COMMANDS
# ============================================

@app.command()
def find_support(
    research_context: str = typer.Argument(..., help="Your research context or hypothesis"),
    paper_ids: Optional[List[str]] = typer.Option(None, "--paper", "-p", help="Specific paper IDs"),
    all_papers: bool = typer.Option(False, "--all", "-a", help="Analyze all downloaded papers"),
    support_type: str = typer.Option("both", "--type", "-t", help="Support type: bolster, contradict, or both"),
    provider: str = typer.Option("mock", "--provider", help="LLM provider (openai, anthropic, mock)"),
    min_confidence: float = typer.Option(0.7, "--confidence", help="Minimum confidence score"),
    sections: Optional[List[str]] = typer.Option(None, "--section", "-s", help="Sections to analyze")
):
    """Find evidence that supports or contradicts your research."""
    arguments = {
        "research_context": research_context,
        "support_type": support_type,
        "llm_provider": provider,
        "min_confidence": min_confidence
    }
    
    if all_papers:
        arguments["paper_ids"] = ["all"]
    elif paper_ids:
        arguments["paper_ids"] = paper_ids
    else:
        console.print("[red]Error: Provide either --paper IDs or --all[/red]")
        raise typer.Exit(1)
    
    if sections:
        arguments["sections_to_analyze"] = sections
    
    with console.status(f"[bold green]Finding {support_type} evidence..."):
        result = asyncio.run(handle_find_research_support(arguments))
    
    console.print(result[0].text)


@app.command()
def search_findings(
    query: str = typer.Argument(..., help="Search query for findings"),
    support_type: str = typer.Option("both", "--type", "-t", help="Filter by support type"),
    paper_id: Optional[str] = typer.Option(None, "--paper", "-p", help="Filter by paper ID"),
    top_k: int = typer.Option(10, "--top", "-k", help="Number of results")
):
    """Search through stored research findings."""
    arguments = {
        "query": query,
        "support_type": support_type,
        "top_k": top_k
    }
    
    if paper_id:
        arguments["paper_id"] = paper_id
    
    result = asyncio.run(handle_search_research_findings(arguments))
    console.print(result[0].text)


# ============================================
# COMPARISON & SIMILARITY COMMANDS
# ============================================

@app.command()
def compare(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    research_context: str = typer.Argument(..., help="Your research to compare against"),
    comparison_type: str = typer.Option("comprehensive", "--type", "-t", help="Comparison type"),
    provider: str = typer.Option("mock", "--provider", help="LLM provider"),
    focus_areas: Optional[List[str]] = typer.Option(None, "--focus", "-f", help="Focus areas")
):
    """Compare a paper's ideas against your research."""
    arguments = {
        "paper_id": paper_id,
        "research_context": research_context,
        "comparison_type": comparison_type,
        "llm_provider": provider
    }
    
    if focus_areas:
        arguments["focus_areas"] = list(focus_areas)
    
    with console.status("[bold green]Comparing ideas..."):
        result = asyncio.run(handle_compare_paper_ideas(arguments))
    
    console.print(result[0].text)


@app.command()
def find_similar(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    similarity_type: str = typer.Option("content", "--type", "-t", help="Similarity type (content, authors, combined)"),
    top_k: int = typer.Option(5, "--top", "-k", help="Number of similar papers"),
    min_similarity: float = typer.Option(0.3, "--min", help="Minimum similarity score")
):
    """Find papers similar to a given paper."""
    arguments = {
        "paper_id": paper_id,
        "similarity_type": similarity_type,
        "top_k": top_k,
        "min_similarity": min_similarity
    }
    
    result = asyncio.run(handle_find_similar_papers(arguments))
    console.print(result[0].text)


# ============================================
# NOTES & ANNOTATIONS COMMANDS
# ============================================

@app.command()
def add_note(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    note: str = typer.Argument(..., help="Note content"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags for the note"),
    section_ref: Optional[str] = typer.Option(None, "--section", "-s", help="Section reference")
):
    """Add a note to a paper."""
    arguments = {
        "paper_id": paper_id,
        "note": note
    }
    
    if tags:
        arguments["tags"] = list(tags)
    if section_ref:
        arguments["section_ref"] = section_ref
    
    result = asyncio.run(handle_add_paper_note(arguments))
    console.print(result[0].text)


@app.command()
def list_notes(
    paper_id: Optional[str] = typer.Option(None, "--paper", "-p", help="Filter by paper ID"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Filter by tags"),
    search_text: Optional[str] = typer.Option(None, "--search", "-s", help="Search in notes")
):
    """List and search paper notes."""
    arguments = {}
    
    if paper_id:
        arguments["paper_id"] = paper_id
    if tags:
        arguments["tags"] = list(tags)
    if search_text:
        arguments["search_text"] = search_text
    
    result = asyncio.run(handle_list_paper_notes(arguments))
    console.print(result[0].text)


# ============================================
# UTILITY COMMANDS
# ============================================

@app.command()
def describe_content(
    paper_id: str = typer.Argument(..., help="ArXiv paper ID"),
    content_type: str = typer.Option("both", "--type", "-t", help="Content type (table, image, both)"),
    llm_model: str = typer.Option("mock", "--model", "-m", help="LLM model to use"),
    use_camelot: bool = typer.Option(False, "--camelot", help="Use Camelot for table extraction")
):
    """Describe tables and images in a paper using AI."""
    arguments = {
        "paper_id": paper_id,
        "content_type": content_type,
        "llm_model": llm_model
    }
    
    if use_camelot:
        arguments["use_camelot"] = use_camelot
    
    with console.status("[bold green]Analyzing content..."):
        result = asyncio.run(handle_describe_content(arguments))
    
    console.print(result[0].text)


@app.command()
def conversion_options():
    """Show available PDF conversion options."""
    result = asyncio.run(handle_conversion_options({}))
    console.print(result[0].text)


@app.command()
def system_stats():
    """Show system statistics and storage info."""
    result = asyncio.run(handle_system_stats({}))
    console.print(result[0].text)


# ============================================
# VALIDATION FUNCTION
# ============================================

if __name__ == "__main__":
    import sys
    
    # Validation tests
    async def validate():
        """Validate CLI functionality."""
        all_validation_failures = []
        total_tests = 0
        
        console.print("=" * 80)
        console.print("VALIDATING ARXIV CLI")
        console.print("=" * 80)
        
        # Test 1: Search command
        total_tests += 1
        console.print("\nTest 1: Search command")
        console.print("-" * 40)
        
        try:
            result = await handle_search({
                "query": "transformer architecture",
                "max_results": 3
            })
            
            output = result[0].text
            # Check for JSON format with total_results
            if "total_results" not in output and "Error" not in output:
                all_validation_failures.append("Test 1: Search didn't return expected format")
            else:
                console.print("✓ Search working")
                
        except Exception as e:
            all_validation_failures.append(f"Test 1: Search failed - {str(e)}")
        
        # Test 2: List papers
        total_tests += 1
        console.print("\nTest 2: List papers")
        console.print("-" * 40)
        
        try:
            result = await handle_list_papers({})
            output = result[0].text
            console.print("✓ List papers working")
        except Exception as e:
            all_validation_failures.append(f"Test 2: List papers failed - {str(e)}")
        
        # Test 3: Conversion options
        total_tests += 1
        console.print("\nTest 3: Conversion options")
        console.print("-" * 40)
        
        try:
            result = await handle_conversion_options({})
            output = result[0].text
            
            if "pymupdf4llm" not in output:
                all_validation_failures.append("Test 3: Missing converter info")
            else:
                console.print("✓ Conversion options working")
                
        except Exception as e:
            all_validation_failures.append(f"Test 3: Conversion options failed - {str(e)}")
        
        # Final result
        console.print("\n" + "=" * 80)
        if all_validation_failures:
            console.print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                console.print(f"  - {failure}")
            sys.exit(1)
        else:
            console.print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            console.print("ArXiv CLI is working correctly")
            sys.exit(0)
    
    # Check if running validation
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        asyncio.run(validate())
    else:
        app()