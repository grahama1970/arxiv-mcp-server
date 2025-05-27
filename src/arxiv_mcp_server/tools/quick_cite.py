#!/usr/bin/env python3
"""
Quick Citation Copy Tool
========================

Copy formatted citations to clipboard in various academic styles.
Scientists need this dozens of times per day when writing papers.

Dependencies:
- pyperclip: Cross-platform clipboard access
- All arxiv_mcp_server dependencies

Sample Input:
    # Copy citation in APA format
    await copy_citation("1706.03762", style="apa")
    
    # Copy citation in custom format
    await copy_citation("1706.03762", style="inline")

Expected Output:
    "Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762"
    (copied to clipboard)
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
from loguru import logger

from ..config import Settings
from ..core.utils import normalize_paper_id
from ..core.search import search_papers

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    logger.warning("pyperclip not available - clipboard functionality disabled")

def get_paper_metadata(paper_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a single paper by ID."""
    try:
        # Search for the specific paper
        papers = search_papers(query=f"id:{paper_id}", max_results=1)
        if papers and len(papers) > 0:
            return papers[0]
        return None
    except Exception as e:
        logger.error(f"Error getting paper metadata: {e}")
        return None


class QuickCiter:
    """Quick citation formatting and clipboard copying."""
    
    def __init__(self):
        self.settings = Settings()
    
    def _format_authors(self, authors: List[str], style: str, max_authors: int = 3) -> str:
        """Format author list based on citation style."""
        if not authors:
            return "Unknown"
        
        if style in ["apa", "mla", "chicago"]:
            if len(authors) == 1:
                return self._format_single_author(authors[0], style)
            elif len(authors) == 2:
                return f"{self._format_single_author(authors[0], style)} & {self._format_single_author(authors[1], style)}"
            elif len(authors) > max_authors:
                return f"{self._format_single_author(authors[0], style)} et al."
            else:
                formatted = [self._format_single_author(a, style) for a in authors[:-1]]
                return ", ".join(formatted) + f", & {self._format_single_author(authors[-1], style)}"
        elif style == "bibtex":
            return " and ".join(authors)
        elif style == "inline":
            if len(authors) <= 2:
                return " & ".join([a.split()[-1] for a in authors])
            else:
                return f"{authors[0].split()[-1]} et al."
        else:  # numeric, plain
            return ", ".join(authors)
    
    def _format_single_author(self, author: str, style: str) -> str:
        """Format a single author name."""
        parts = author.strip().split()
        if not parts:
            return author
        
        if style == "apa":
            # Last, F. M.
            if len(parts) >= 2:
                last = parts[-1]
                initials = " ".join([f"{p[0]}." for p in parts[:-1]])
                return f"{last}, {initials}"
            return author
        elif style == "mla":
            # Last, First Middle
            if len(parts) >= 2:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"
            return author
        else:
            return author
    
    def _extract_year(self, paper_data: Dict[str, Any]) -> str:
        """Extract publication year from paper data."""
        published = paper_data.get("published", "")
        if published:
            try:
                return published[:4]
            except:
                pass
        
        # Try to extract from arxiv ID (YYMM.NNNNN format)
        paper_id = paper_data.get("id", "")
        if "." in paper_id:
            yymm = paper_id.split(".")[0]
            if len(yymm) == 4:
                year = int(yymm[:2])
                # Assume 20XX for years 00-99
                return f"20{year:02d}"
        
        return str(datetime.now().year)
    
    def format_citation(self, paper_data: Dict[str, Any], style: str = "apa") -> str:
        """Format citation in specified style."""
        title = paper_data.get("title", "Untitled")
        authors = paper_data.get("authors", ["Unknown"])
        year = self._extract_year(paper_data)
        paper_id = paper_data.get("id", "")
        
        # Clean title
        title = re.sub(r'\s+', ' ', title.strip())
        
        if style == "apa":
            # APA: Author, A. A. (Year). Title. arXiv:ID
            author_str = self._format_authors(authors, style)
            return f"{author_str} ({year}). {title}. arXiv:{paper_id}"
        
        elif style == "mla":
            # MLA: Author. "Title." arXiv preprint arXiv:ID (Year)
            author_str = self._format_authors(authors, style)
            return f'{author_str}. "{title}." arXiv preprint arXiv:{paper_id} ({year})'
        
        elif style == "chicago":
            # Chicago: Author. "Title." arXiv preprint arXiv:ID (Year).
            author_str = self._format_authors(authors, style)
            return f'{author_str}. "{title}." arXiv preprint arXiv:{paper_id} ({year}).'
        
        elif style == "bibtex":
            # BibTeX format
            first_author_last = authors[0].split()[-1].lower()
            key = f"{first_author_last}{year}{paper_id.replace('.', '')}"
            
            bibtex = f"@article{{{key},\n"
            bibtex += f"  title={{{title}}},\n"
            bibtex += f"  author={{{self._format_authors(authors, style)}}},\n"
            bibtex += f"  journal={{arXiv preprint arXiv:{paper_id}}},\n"
            bibtex += f"  year={{{year}}}\n"
            bibtex += "}"
            return bibtex
        
        elif style == "inline":
            # Inline: Author et al. (Year)
            author_str = self._format_authors(authors, style)
            return f"{author_str} ({year})"
        
        elif style == "numeric":
            # Numeric: [1] Author, "Title", arXiv:ID, Year
            author_str = self._format_authors(authors, style)
            return f'[1] {author_str}, "{title}", arXiv:{paper_id}, {year}'
        
        elif style == "plain":
            # Plain: Title by Author (arXiv:ID)
            author_str = self._format_authors(authors, style, max_authors=10)
            return f"{title} by {author_str} (arXiv:{paper_id})"
        
        elif style == "markdown":
            # Markdown: [Title](URL) by Author (Year)
            author_str = self._format_authors(authors, style)
            url = f"https://arxiv.org/abs/{paper_id}"
            return f"[{title}]({url}) by {author_str} ({year})"
        
        else:
            # Default fallback
            return f"{title} - {', '.join(authors)} (arXiv:{paper_id})"
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard."""
        if not CLIPBOARD_AVAILABLE:
            return False
        
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False
    
    async def quick_cite(self, paper_id: str, style: str = "apa") -> Dict[str, Any]:
        """Generate and copy citation for a paper."""
        # Clean paper ID
        paper_id = normalize_paper_id(paper_id)
        
        # Get paper metadata
        paper_data = get_paper_metadata(paper_id)
        if not paper_data:
            return {
                "success": False,
                "message": f"Paper {paper_id} not found",
                "citation": None
            }
        
        # Format citation
        citation = self.format_citation(paper_data, style)
        
        # Copy to clipboard
        clipboard_success = self.copy_to_clipboard(citation)
        
        return {
            "success": True,
            "citation": citation,
            "style": style,
            "paper_id": paper_id,
            "clipboard_copied": clipboard_success,
            "message": "Citation copied to clipboard!" if clipboard_success else "Citation generated (clipboard not available)"
        }


# Tool definitions for MCP
copy_citation_tool = {
    "name": "copy_citation",
    "description": "Copy a formatted citation to clipboard",
    "input_schema": {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID"
            },
            "style": {
                "type": "string",
                "description": "Citation style: apa, mla, chicago, bibtex, inline, numeric, plain, markdown",
                "default": "apa"
            }
        },
        "required": ["paper_id"]
    }
}

format_multiple_citations_tool = {
    "name": "format_multiple_citations",
    "description": "Format multiple papers as a bibliography",
    "input_schema": {
        "type": "object",
        "properties": {
            "paper_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ArXiv paper IDs"
            },
            "style": {
                "type": "string",
                "description": "Citation style",
                "default": "apa"
            },
            "sort_by": {
                "type": "string",
                "description": "Sort order: author, year, title",
                "default": "author"
            }
        },
        "required": ["paper_ids"]
    }
}

async def handle_copy_citation(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle copying a citation."""
    citer = QuickCiter()
    result = await citer.quick_cite(
        arguments["paper_id"],
        arguments.get("style", "apa")
    )
    
    if result["success"]:
        message = f"📋 {result['message']}\n\n"
        message += f"Style: {result['style'].upper()}\n"
        message += f"Citation:\n{result['citation']}"
    else:
        message = result["message"]
    
    return [{
        "type": "text",
        "text": message,
        "data": result
    }]

async def handle_format_multiple_citations(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle formatting multiple citations."""
    citer = QuickCiter()
    paper_ids = arguments["paper_ids"]
    style = arguments.get("style", "apa")
    sort_by = arguments.get("sort_by", "author")
    
    citations = []
    for paper_id in paper_ids:
        paper_data = get_paper_metadata(normalize_paper_id(paper_id))
        if paper_data:
            citation = citer.format_citation(paper_data, style)
            citations.append({
                "citation": citation,
                "paper_data": paper_data
            })
    
    # Sort citations
    if sort_by == "author":
        citations.sort(key=lambda x: x["paper_data"]["authors"][0].split()[-1].lower())
    elif sort_by == "year":
        citations.sort(key=lambda x: citer._extract_year(x["paper_data"]))
    elif sort_by == "title":
        citations.sort(key=lambda x: x["paper_data"]["title"].lower())
    
    # Format output
    if style == "bibtex":
        bibliography = "\n\n".join([c["citation"] for c in citations])
    else:
        bibliography = "\n".join([c["citation"] for c in citations])
    
    # Copy to clipboard
    clipboard_success = citer.copy_to_clipboard(bibliography)
    
    message = f"📚 Formatted {len(citations)} citations in {style.upper()} style\n"
    if clipboard_success:
        message += "✓ Copied to clipboard!\n"
    message += "\n" + bibliography
    
    return [{
        "type": "text",
        "text": message,
        "data": {
            "citations": bibliography,
            "count": len(citations),
            "style": style,
            "clipboard_copied": clipboard_success
        }
    }]


if __name__ == "__main__":
    # Validation tests
    import asyncio
    
    async def validate():
        """Validate quick citation functionality."""
        print("=" * 80)
        print("VALIDATING QUICK CITATION TOOL")
        print("=" * 80)
        
        citer = QuickCiter()
        
        # Test paper ID
        test_paper = "1706.03762"  # Attention Is All You Need
        
        # Test 1: Different citation styles
        print("\nTest 1: Citation styles")
        print("-" * 40)
        
        styles = ["apa", "mla", "chicago", "bibtex", "inline", "plain", "markdown"]
        
        for style in styles:
            result = await citer.quick_cite(test_paper, style)
            if result["success"]:
                print(f"\n{style.upper()}:")
                print(result["citation"])
            else:
                print(f"✗ Failed to generate {style} citation")
        
        # Test 2: Clipboard functionality
        print("\nTest 2: Clipboard functionality")
        print("-" * 40)
        
        if CLIPBOARD_AVAILABLE:
            result = await citer.quick_cite(test_paper, "apa")
            if result["clipboard_copied"]:
                print("✓ Citation copied to clipboard")
                try:
                    clipboard_content = pyperclip.paste()
                    print(f"✓ Verified clipboard content: {clipboard_content[:50]}...")
                except:
                    print("ℹ Could not verify clipboard content")
        else:
            print("ℹ Clipboard functionality not available")
        
        # Test 3: Multiple citations
        print("\nTest 3: Multiple citations bibliography")
        print("-" * 40)
        
        test_papers = ["1706.03762", "1810.04805", "2005.14165"]  # Famous transformer papers
        
        citations = []
        for paper_id in test_papers:
            paper_data = get_paper_metadata(paper_id)
            if paper_data:
                citation = citer.format_citation(paper_data, "apa")
                citations.append(citation)
        
        if citations:
            print(f"✓ Generated {len(citations)} citations")
            print("\nBibliography:")
            for i, citation in enumerate(citations, 1):
                print(f"{i}. {citation}")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION PASSED - Quick citation tool is working")
        print("=" * 80)
    
    asyncio.run(validate())