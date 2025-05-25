import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings

settings = Settings()

extract_sections_tool = types.Tool(
    name="extract_sections",
    description="Extract specific sections from ArXiv papers (e.g., abstract, introduction, methods).",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID",
            },
            "sections": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Sections to extract (e.g., ['abstract', 'introduction', 'methods'])",
            },
            "include_subsections": {
                "type": "boolean",
                "description": "Include subsections within requested sections",
                "default": True,
            },
        },
        "required": ["paper_id", "sections"],
    },
)

def normalize_section_name(section: str) -> List[str]:
    """Normalize section name and provide variants."""
    section_lower = section.lower().strip()
    
    # Common variations
    variants = {
        "abstract": ["abstract", "summary"],
        "introduction": ["introduction", "intro", "background"],
        "methods": ["methods", "methodology", "method", "approach", "materials and methods"],
        "results": ["results", "findings", "experiments", "experimental results"],
        "discussion": ["discussion", "analysis"],
        "conclusion": ["conclusion", "conclusions", "concluding remarks", "summary and conclusions"],
        "references": ["references", "bibliography", "works cited"],
    }
    
    # Return known variants or just the original
    return variants.get(section_lower, [section_lower])

def extract_section(content: str, section_name: str, include_subsections: bool) -> Optional[str]:
    """Extract a specific section from paper content."""
    section_variants = normalize_section_name(section_name)
    
    # Try each variant
    for variant in section_variants:
        # Pattern for markdown headers
        if include_subsections:
            # Match section and everything until next same-level or higher header
            pattern = rf'#+\s*{re.escape(variant)}\s*\n(.*?)(?=\n#{{1,2}}\s|\Z)'
        else:
            # Match section until any header
            pattern = rf'#+\s*{re.escape(variant)}\s*\n(.*?)(?=\n#+\s|\Z)'
        
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0).strip()
    
    # Try without markdown headers (plain text sections)
    for variant in section_variants:
        pattern = rf'{re.escape(variant)}\s*\n+([^#]*?)(?=\n[A-Z][^#]*?\n|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return f"{variant}\n\n{match.group(1).strip()}"
    
    return None

async def handle_extract_sections(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle section extraction requests."""
    paper_id = arguments["paper_id"]
    sections = arguments["sections"]
    include_subsections = arguments.get("include_subsections", True)
    
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
    
    # Extract requested sections
    extracted_sections = []
    not_found = []
    
    for section in sections:
        section_content = extract_section(content, section, include_subsections)
        if section_content:
            extracted_sections.append(section_content)
        else:
            not_found.append(section)
    
    # Format output
    output = f"Extracted sections from {paper_id}:\n\n"
    
    if extracted_sections:
        output += "\n\n---\n\n".join(extracted_sections)
    
    if not_found:
        output += f"\n\n---\n\nSections not found: {', '.join(not_found)}"
        output += "\n\nAvailable sections in this paper:\n"
        
        # Find all headers in the paper
        headers = re.findall(r'^#+\s*(.+)$', content, re.MULTILINE)
        unique_headers = []
        for h in headers[:20]:  # Limit to first 20
            if h.lower() not in [uh.lower() for uh in unique_headers]:
                unique_headers.append(h)
        
        output += "• " + "\n• ".join(unique_headers)
    
    return [types.TextContent(type="text", text=output)]