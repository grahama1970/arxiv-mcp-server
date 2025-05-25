import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings

settings = Settings()

extract_citations_tool = types.Tool(
    name="extract_citations",
    description="Extract citations and references from ArXiv papers. Outputs BibTeX, JSON, or EndNote formats.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID (e.g., '2301.00001')",
            },
            "format": {
                "type": "string",
                "description": "Output format for citations",
                "enum": ["bibtex", "json", "endnote"],
                "default": "bibtex",
            },
            "include_arxiv_links": {
                "type": "boolean",
                "description": "Add clickable links for ArXiv papers in citations",
                "default": True,
            },
        },
        "required": ["paper_id"],
    },
)

def extract_citations_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract citations from paper text using regex patterns."""
    citations = []
    
    # Pattern for References/Bibliography section
    ref_section_pattern = r'(?:References|Bibliography|REFERENCES|BIBLIOGRAPHY)\s*\n(.*?)(?:\n\n|\Z)'
    ref_match = re.search(ref_section_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not ref_match:
        return citations
    
    references_text = ref_match.group(1)
    
    # Split into individual references (numbered or bulleted)
    ref_patterns = [
        r'\[\d+\]\s*(.*?)(?=\[\d+\]|\Z)',  # [1] Author et al...
        r'\d+\.\s*(.*?)(?=\d+\.|\Z)',       # 1. Author et al...
        r'•\s*(.*?)(?=•|\Z)',               # • Author et al...
    ]
    
    for pattern in ref_patterns:
        matches = re.findall(pattern, references_text, re.DOTALL)
        if matches:
            for i, match in enumerate(matches):
                citation = parse_citation(match.strip(), i + 1)
                if citation:
                    citations.append(citation)
            break
    
    return citations

def parse_citation(text: str, index: int) -> Optional[Dict[str, Any]]:
    """Parse a single citation into structured format."""
    text = ' '.join(text.split())
    
    citation = {
        "index": index,
        "raw_text": text,
        "authors": [],
        "title": "",
        "year": None,
        "arxiv_id": None,
        "doi": None,
    }
    
    # Extract ArXiv ID
    arxiv_pattern = r'arXiv:(\d{4}\.\d{4,5})'
    arxiv_match = re.search(arxiv_pattern, text)
    if arxiv_match:
        citation["arxiv_id"] = arxiv_match.group(1)
    
    # Extract year
    year_pattern = r'\((\d{4})\)'
    year_match = re.search(year_pattern, text)
    if year_match:
        citation["year"] = int(year_match.group(1))
    
    # Extract DOI
    doi_pattern = r'doi:\s*([^\s]+)'
    doi_match = re.search(doi_pattern, text, re.IGNORECASE)
    if doi_match:
        citation["doi"] = doi_match.group(1)
    
    # Try to extract title (text in quotes or after year)
    title_pattern = r'"([^"]+)"'
    title_match = re.search(title_pattern, text)
    if title_match:
        citation["title"] = title_match.group(1)
    
    # Extract authors (text before year or title)
    if year_match:
        authors_text = text[:year_match.start()].strip()
        # Split by "and" or commas
        authors = re.split(r',\s*|\s+and\s+', authors_text)
        citation["authors"] = [a.strip() for a in authors if a.strip()]
    
    return citation

def format_as_bibtex(citations: List[Dict[str, Any]], include_links: bool = True) -> str:
    """Convert citations to BibTeX format."""
    bibtex_entries = []
    
    for cite in citations:
        # Generate citation key
        first_author = cite["authors"][0].split()[-1] if cite["authors"] else "Unknown"
        year = cite["year"] or "XXXX"
        key = f"{first_author}{year}_{cite['index']}"
        
        entry = f"@article{{{key},\n"
        
        if cite["authors"]:
            entry += f'  author = "{" and ".join(cite["authors"])}",\n'
        
        if cite["title"]:
            entry += f'  title = "{{{cite["title"]}}}",\n'
        
        if cite["year"]:
            entry += f'  year = {{{cite["year"]}}},\n'
        
        if cite["arxiv_id"]:
            entry += f'  eprint = "{{{cite["arxiv_id"]}}}",\n'
            entry += f'  archivePrefix = "arXiv",\n'
            if include_links:
                entry += f'  url = "https://arxiv.org/abs/{cite["arxiv_id"]}",\n'
        
        if cite["doi"]:
            entry += f'  doi = "{{{cite["doi"]}}}",\n'
        
        entry += "}"
        bibtex_entries.append(entry)
    
    return "\n\n".join(bibtex_entries)

def format_as_endnote(citations: List[Dict[str, Any]]) -> str:
    """Convert citations to EndNote format."""
    endnote_entries = []
    
    for cite in citations:
        entry = "%0 Journal Article\n"
        
        if cite["authors"]:
            for author in cite["authors"]:
                entry += f"%A {author}\n"
        
        if cite["title"]:
            entry += f"%T {cite['title']}\n"
        
        if cite["year"]:
            entry += f"%D {cite['year']}\n"
        
        if cite["arxiv_id"]:
            entry += f"%U https://arxiv.org/abs/{cite['arxiv_id']}\n"
        
        if cite["doi"]:
            entry += f"%R {cite['doi']}\n"
        
        endnote_entries.append(entry)
    
    return "\n".join(endnote_entries)

async def handle_extract_citations(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle citation extraction requests."""
    paper_id = arguments["paper_id"]
    output_format = arguments.get("format", "bibtex")
    include_links = arguments.get("include_arxiv_links", True)
    
    # Load paper content
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    if not md_path.exists():
        return [types.TextContent(
            type="text", 
            text=f"Error: Paper {paper_id} not found. Please download it first."
        )]
    
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading paper: {str(e)}")]
    
    # Extract citations
    citations = extract_citations_from_text(content)
    
    if not citations:
        return [types.TextContent(
            type="text", 
            text="No citations found. The paper may not have a standard References section."
        )]
    
    # Format output
    if output_format == "bibtex":
        output = format_as_bibtex(citations, include_links)
    elif output_format == "endnote":
        output = format_as_endnote(citations)
    else:  # json
        output = json.dumps(citations, indent=2)
    
    return [types.TextContent(type="text", text=output)]