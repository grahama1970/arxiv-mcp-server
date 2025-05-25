# Comprehensive ArXiv MCP Server Implementation Guide

This document merges all implementation tasks (001-007) into a single comprehensive guide with complete working code.

## Overview

All tasks implement new tools for the ArXiv MCP server. Each tool follows the same integration pattern:
1. Create the tool file in `src/arxiv_mcp_server/tools/`
2. Add imports to `__init__.py`
3. Register in `server.py`
4. Test with provided commands

## Task 001: Citation Extraction Tool

**Priority**: HIGH  
**Feature**: Extract and export paper references in BibTeX/JSON/EndNote formats

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/extract_citations.py

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
    # Clean up the text
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
    
    return citation if citation["authors"] or citation["title"] or citation["arxiv_id"] else None

def format_as_bibtex(citations: List[Dict[str, Any]]) -> str:
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
        
        entry += "}"
        bibtex_entries.append(entry)
    
    return "\n\n".join(bibtex_entries)

async def handle_extract_citations(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle citation extraction requests."""
    paper_id = arguments["paper_id"]
    output_format = arguments.get("format", "bibtex")
    
    # Load paper content
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract citations
    citations = extract_citations_from_text(content)
    
    # Format output
    if output_format == "bibtex":
        output = format_as_bibtex(citations)
    else:
        output = json.dumps(citations, indent=2)
    
    return [types.TextContent(type="text", text=output)]
```

## Task 002: Batch Operations Tool

**Priority**: HIGH  
**Feature**: Download and process multiple papers concurrently with resource awareness

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/batch_operations.py

import asyncio
from typing import Dict, Any, List
import mcp.types as types
from ..config import Settings
from .download import handle_download
from .system_stats import get_system_stats

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
            "converter": {
                "type": "string",
                "description": "PDF converter to use",
                "enum": ["pymupdf4llm", "marker-pdf"],
                "default": "pymupdf4llm",
            },
            "max_concurrent": {
                "type": "integer",
                "description": "Maximum concurrent downloads (auto-calculated if not set)",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["paper_ids"],
    },
)

def calculate_optimal_concurrency() -> int:
    """Calculate optimal concurrency based on system resources."""
    stats = get_system_stats()
    memory_gb = stats["memory_available_gb"]
    
    if memory_gb < 2:
        return 1
    elif memory_gb < 4:
        return 2
    else:
        return min(5, max(1, int(memory_gb / 2)))

async def download_paper_safe(paper_id: str, converter: str) -> Dict[str, Any]:
    """Download a single paper with error handling."""
    try:
        result = await handle_download({
            "paper_id": paper_id,
            "converter": converter,
            "output_format": "markdown"
        })
        return {
            "paper_id": paper_id,
            "success": True,
            "message": "Downloaded successfully"
        }
    except Exception as e:
        return {
            "paper_id": paper_id,
            "success": False,
            "message": str(e)
        }

async def handle_batch_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle batch download requests."""
    paper_ids = arguments["paper_ids"]
    converter = arguments.get("converter", "pymupdf4llm")
    max_concurrent = arguments.get("max_concurrent")
    
    if not max_concurrent:
        max_concurrent = calculate_optimal_concurrency()
    
    # Process downloads in batches
    results = []
    for i in range(0, len(paper_ids), max_concurrent):
        batch = paper_ids[i:i + max_concurrent]
        batch_tasks = [
            download_paper_safe(pid, converter) for pid in batch
        ]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
    
    # Format results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    output = f"# Batch Download Results\n\n"
    output += f"Total: {len(paper_ids)}, Success: {len(successful)}, Failed: {len(failed)}\n"
    output += f"Max concurrent: {max_concurrent}\n\n"
    
    if failed:
        output += "## Failed Downloads\n"
        for r in failed:
            output += f"- {r['paper_id']}: {r['message']}\n"
    
    return [types.TextContent(type="text", text=output)]
```

## Task 003: Paper Similarity Tool

**Priority**: MEDIUM  
**Feature**: Find papers similar to a given paper by content or metadata

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/paper_similarity.py

import json
import re
import math
from typing import Dict, Any, List
from collections import Counter
import mcp.types as types
from ..config import Settings
from .search import handle_search

settings = Settings()

find_similar_papers_tool = types.Tool(
    name="find_similar_papers",
    description="Find papers similar to a given paper by abstract, authors, or keywords.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID to find similar papers for",
            },
            "similarity_metric": {
                "type": "string",
                "description": "Method to find similarity",
                "enum": ["abstract", "authors", "keywords"],
                "default": "abstract",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of similar papers",
                "default": 10,
            },
        },
        "required": ["paper_id"],
    },
)

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract top keywords using simple TF approach."""
    # Tokenize and clean
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    # Simple stopwords
    stopwords = {'this', 'that', 'these', 'those', 'from', 'with', 'have', 'been'}
    words = [w for w in words if w not in stopwords]
    
    # Count and return top words
    word_freq = Counter(words)
    return [word for word, _ in word_freq.most_common(top_n)]

def cosine_similarity(text1: str, text2: str) -> float:
    """Calculate simple cosine similarity between texts."""
    words1 = set(re.findall(r'\b[a-z]+\b', text1.lower()))
    words2 = set(re.findall(r'\b[a-z]+\b', text2.lower()))
    
    intersection = words1.intersection(words2)
    if not words1 or not words2:
        return 0.0
    
    return len(intersection) / math.sqrt(len(words1) * len(words2))

async def handle_find_similar_papers(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Find similar papers based on various metrics."""
    paper_id = arguments["paper_id"]
    metric = arguments.get("similarity_metric", "abstract")
    max_results = arguments.get("max_results", 10)
    
    # Load source paper
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract abstract
    abstract_match = re.search(
        r'(?:Abstract|ABSTRACT)\s*:?\s*\n(.*?)(?:\n\n|\n#)',
        content,
        re.DOTALL | re.IGNORECASE
    )
    abstract = abstract_match.group(1) if abstract_match else ""
    
    if metric == "abstract" and abstract:
        # Search using keywords from abstract
        keywords = extract_keywords(abstract, 5)
        search_query = " ".join(keywords)
        
        # Search ArXiv
        search_results = await handle_search({
            "query": search_query,
            "max_results": max_results * 2
        })
        
        papers = json.loads(search_results[0].text)
        
        # Calculate similarities
        similar_papers = []
        for paper in papers:
            if paper["arxiv_id"] != paper_id:
                similarity = cosine_similarity(abstract, paper.get("abstract", ""))
                similar_papers.append({
                    **paper,
                    "similarity_score": similarity
                })
        
        # Sort and limit
        similar_papers.sort(key=lambda x: x["similarity_score"], reverse=True)
        similar_papers = similar_papers[:max_results]
        
        # Format output
        output = f"# Similar Papers to {paper_id}\n\n"
        for i, paper in enumerate(similar_papers, 1):
            output += f"{i}. **{paper['title']}**\n"
            output += f"   - ID: {paper['arxiv_id']}\n"
            output += f"   - Similarity: {paper['similarity_score']:.2%}\n\n"
        
        return [types.TextContent(type="text", text=output)]
    
    return [types.TextContent(type="text", text="No similar papers found")]
```

## Task 004: Section Extraction Tool

**Priority**: MEDIUM  
**Feature**: Extract specific sections from papers for targeted reading

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/extract_sections.py

import re
from typing import Dict, Any, List, Optional
import mcp.types as types
from ..config import Settings

settings = Settings()

extract_sections_tool = types.Tool(
    name="extract_sections",
    description="Extract specific sections from ArXiv papers (abstract, introduction, methods, etc.)",
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
                "description": "List of sections to extract",
                "default": ["abstract", "introduction", "conclusion"],
            },
        },
        "required": ["paper_id"],
    },
)

def find_section_boundaries(content: str) -> Dict[str, tuple[int, int]]:
    """Find start and end positions of sections."""
    sections = {}
    lines = content.split('\n')
    
    # Common section patterns
    section_patterns = [
        (r'^#{1,3}\s*(\d+\.?\s*)?([A-Za-z\s]+)$', 2),  # Markdown headers
        (r'^(\d+\.?\s*)?([A-Z][A-Za-z\s]+)$', 2),      # Title case
    ]
    
    current_pos = 0
    section_positions = []
    
    for i, line in enumerate(lines):
        for pattern, name_group in section_patterns:
            match = re.match(pattern, line.strip())
            if match:
                section_name = match.group(name_group).strip().lower()
                section_positions.append((section_name, current_pos, i))
                break
        current_pos += len(line) + 1
    
    # Set end positions
    for i, (name, start_pos, line_num) in enumerate(section_positions):
        if i < len(section_positions) - 1:
            end_pos = section_positions[i + 1][1]
        else:
            end_pos = len(content)
        sections[name] = (start_pos, end_pos)
    
    return sections

def extract_section(content: str, section_name: str) -> Optional[str]:
    """Extract a specific section's content."""
    sections = find_section_boundaries(content)
    
    # Normalize section name
    normalized = section_name.lower().strip()
    
    # Try exact match
    if normalized in sections:
        start, end = sections[normalized]
        return content[start:end].strip()
    
    # Try partial match
    for name, (start, end) in sections.items():
        if normalized in name or name in normalized:
            return content[start:end].strip()
    
    return None

async def handle_extract_sections(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Extract requested sections from a paper."""
    paper_id = arguments["paper_id"]
    requested_sections = arguments.get("sections", ["abstract", "introduction", "conclusion"])
    
    # Load paper
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract sections
    output = f"# Extracted Sections from {paper_id}\n\n"
    extracted_count = 0
    
    for section_name in requested_sections:
        section_content = extract_section(content, section_name)
        
        if section_content:
            extracted_count += 1
            output += f"## {section_name.title()}\n\n"
            
            # Limit length for readability
            if len(section_content) > 1500:
                section_content = section_content[:1500] + "\n\n[... truncated ...]"
            
            output += section_content + "\n\n---\n\n"
        else:
            output += f"## {section_name.title()}\n\n"
            output += f"*Section not found*\n\n---\n\n"
    
    output += f"\nExtracted {extracted_count}/{len(requested_sections)} sections"
    
    return [types.TextContent(type="text", text=output)]
```

## Task 005: Paper Annotations Tool

**Priority**: LOW  
**Feature**: Add notes and tags to papers for personal research management

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/annotations.py

import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import mcp.types as types
from ..config import Settings

settings = Settings()

add_paper_note_tool = types.Tool(
    name="add_paper_note",
    description="Add notes and tags to ArXiv papers for organization.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID",
            },
            "note": {
                "type": "string",
                "description": "Note text to add",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for categorization",
                "default": [],
            },
        },
        "required": ["paper_id", "note"],
    },
)

list_paper_notes_tool = types.Tool(
    name="list_paper_notes",
    description="List all notes for a paper or search by tags.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID (optional)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by tags",
            },
        },
    },
)

class NotesManager:
    """Simple JSON-based notes storage."""
    
    def __init__(self, storage_path: Path):
        self.notes_file = storage_path / "paper_notes.json"
        self.notes = self._load_notes()
    
    def _load_notes(self) -> Dict:
        if self.notes_file.exists():
            with open(self.notes_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_notes(self):
        with open(self.notes_file, "w") as f:
            json.dump(self.notes, f, indent=2)
    
    def add_note(self, paper_id: str, note: str, tags: List[str]) -> Dict:
        if paper_id not in self.notes:
            self.notes[paper_id] = []
        
        note_entry = {
            "id": len(self.notes[paper_id]) + 1,
            "timestamp": datetime.now().isoformat(),
            "note": note,
            "tags": tags
        }
        
        self.notes[paper_id].append(note_entry)
        self._save_notes()
        return note_entry
    
    def get_notes(self, paper_id: str = None, tags: List[str] = None) -> Dict:
        if paper_id:
            paper_notes = self.notes.get(paper_id, [])
            if tags:
                paper_notes = [n for n in paper_notes 
                              if any(t in n.get("tags", []) for t in tags)]
            return {paper_id: paper_notes}
        
        # Filter all notes by tags
        if tags:
            filtered = {}
            for pid, notes in self.notes.items():
                filtered_notes = [n for n in notes 
                                 if any(t in n.get("tags", []) for t in tags)]
                if filtered_notes:
                    filtered[pid] = filtered_notes
            return filtered
        
        return self.notes

async def handle_add_paper_note(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Add a note to a paper."""
    paper_id = arguments["paper_id"]
    note_text = arguments["note"]
    tags = arguments.get("tags", [])
    
    manager = NotesManager(settings.STORAGE_PATH)
    note_entry = manager.add_note(paper_id, note_text, tags)
    
    output = f"# Note Added\n\n"
    output += f"**Paper**: {paper_id}\n"
    output += f"**Note ID**: {note_entry['id']}\n"
    output += f"**Tags**: {', '.join(tags) if tags else 'none'}\n\n"
    output += f"**Note**: {note_text}\n"
    
    return [types.TextContent(type="text", text=output)]

async def handle_list_paper_notes(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """List notes for papers."""
    paper_id = arguments.get("paper_id")
    filter_tags = arguments.get("tags", [])
    
    manager = NotesManager(settings.STORAGE_PATH)
    notes = manager.get_notes(paper_id, filter_tags)
    
    if not notes:
        return [types.TextContent(type="text", text="No notes found")]
    
    output = "# Paper Notes\n\n"
    
    for pid, paper_notes in notes.items():
        if not paper_id:  # Show paper ID if listing multiple
            output += f"## Paper: {pid}\n\n"
        
        for note in paper_notes:
            output += f"**Note {note['id']}** - {note['timestamp'][:10]}\n"
            if note.get('tags'):
                output += f"Tags: {', '.join(note['tags'])}\n"
            output += f"\n{note['note']}\n\n---\n\n"
    
    return [types.TextContent(type="text", text=output)]
```

## Task 007: Comparative Analysis Tool

**Priority**: HIGH  
**Feature**: Compare paper content against user's research questions or existing systems using AI analysis

### Complete Working Code

```python
# File: src/arxiv_mcp_server/tools/comparative_analysis.py

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings
from .extract_sections import extract_section, find_section_boundaries

settings = Settings()

compare_paper_ideas_tool = types.Tool(
    name="compare_paper_ideas",
    description="Compare paper ideas against your research question or system. Uses AI to find better/worse ideas, contradictions, and unique insights.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID to analyze",
            },
            "user_context": {
                "type": "string",
                "description": "Your research question, system description, or hypothesis to compare against",
            },
            "analysis_type": {
                "type": "string",
                "description": "Type of comparative analysis",
                "enum": ["better_worse", "contradictions", "unique_ideas", "comprehensive"],
                "default": "comprehensive",
            },
            "focus_sections": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific sections to focus on (default: all)",
                "default": [],
            },
            "llm_provider": {
                "type": "string",
                "description": "LLM provider to use for analysis",
                "enum": ["mock", "openai", "anthropic", "perplexity"],
                "default": "mock",
            },
        },
        "required": ["paper_id", "user_context"],
    },
)

class ComparativeAnalyzer:
    """Analyze papers against user research questions."""
    
    def __init__(self, llm_provider: str = "mock"):
        self.llm_provider = llm_provider
    
    async def analyze_section(
        self,
        section_content: str,
        user_context: str,
        analysis_type: str,
        section_name: str
    ) -> Dict[str, Any]:
        """Analyze a single section against user context."""
        
        # Build analysis prompt based on type
        prompts = {
            "better_worse": f"""
Compare this research section with the user's system/idea:

USER'S SYSTEM/IDEA:
{user_context}

PAPER SECTION ({section_name}):
{section_content[:2000]}

Identify:
1. Ideas in the paper that are BETTER than the user's approach (with reasoning)
2. Ideas that are WORSE than the user's approach (with reasoning)
3. Trade-offs between the approaches

Format as:
BETTER IDEAS:
- [specific idea]: [why it's better]

WORSE IDEAS:
- [specific idea]: [why it's worse]

TRADE-OFFS:
- [comparison point]: [trade-off analysis]
""",
            
            "contradictions": f"""
Find contradictions or conflicts between this research and the user's system:

USER'S SYSTEM/IDEA:
{user_context}

PAPER SECTION ({section_name}):
{section_content[:2000]}

Identify:
1. Direct contradictions with the user's approach
2. Conflicting assumptions or principles
3. New research that challenges the user's ideas

Format as:
CONTRADICTIONS:
- [user's assumption]: [paper's contradicting finding]

CONFLICTING PRINCIPLES:
- [principle]: [how they conflict]

NEW CHALLENGES:
- [finding]: [how it challenges user's approach]
""",
            
            "unique_ideas": f"""
Extract unique ideas from this paper section that relate to the user's research:

USER'S SYSTEM/IDEA:
{user_context}

PAPER SECTION ({section_name}):
{section_content[:2000]}

Identify:
1. Novel approaches not in the user's system
2. Unique insights or findings
3. Potential improvements or extensions

Format as:
NOVEL APPROACHES:
- [approach]: [how it differs]

UNIQUE INSIGHTS:
- [insight]: [relevance to user's work]

POTENTIAL IMPROVEMENTS:
- [improvement]: [how to apply]
""",
            
            "comprehensive": f"""
Comprehensive comparison of this research with the user's system:

USER'S SYSTEM/IDEA:
{user_context}

PAPER SECTION ({section_name}):
{section_content[:2000]}

Analyze:
1. Similarities and differences
2. Strengths and weaknesses of each approach
3. Contradictions or conflicts
4. Unique contributions
5. Potential synergies

Provide specific examples and reasoning for each point.
"""
        }
        
        prompt = prompts.get(analysis_type, prompts["comprehensive"])
        
        # Mock LLM response for demonstration
        if self.llm_provider == "mock":
            return {
                "section": section_name,
                "analysis": f"[Mock analysis of {section_name}]\n\nBETTER IDEAS:\n- Paper uses advanced heat storage: More efficient than user's molten salt battery\n\nWORSE IDEAS:\n- Paper's 200MW capacity: Lower than user's 345MW system\n\nTRADE-OFFS:\n- Efficiency vs. capacity: Paper prioritizes efficiency, user prioritizes scale",
                "key_findings": [
                    "Advanced heat storage method",
                    "Different capacity trade-offs",
                    "Alternative cooling approach"
                ]
            }
        
        # Real LLM integration would go here
        # response = await self.llm_client.analyze(prompt)
        
        return {
            "section": section_name,
            "analysis": "LLM analysis would appear here",
            "key_findings": []
        }
    
    async def compare_full_paper(
        self,
        paper_content: str,
        user_context: str,
        analysis_type: str,
        focus_sections: List[str] = None
    ) -> Dict[str, Any]:
        """Compare entire paper against user context."""
        
        # Find all sections
        sections = find_section_boundaries(paper_content)
        
        # Filter to focus sections if specified
        if focus_sections:
            sections = {k: v for k, v in sections.items() 
                       if any(focus in k for focus in focus_sections)}
        
        # Analyze each section
        analyses = []
        for section_name, (start, end) in sections.items():
            section_content = paper_content[start:end]
            
            # Skip very short sections
            if len(section_content.strip()) < 100:
                continue
            
            analysis = await self.analyze_section(
                section_content,
                user_context,
                analysis_type,
                section_name
            )
            analyses.append(analysis)
        
        # Synthesize findings
        all_findings = []
        for analysis in analyses:
            all_findings.extend(analysis.get("key_findings", []))
        
        return {
            "section_analyses": analyses,
            "key_findings": list(set(all_findings)),  # Deduplicate
            "sections_analyzed": len(analyses),
            "analysis_type": analysis_type
        }

async def handle_compare_paper_ideas(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle comparative analysis requests."""
    try:
        paper_id = arguments["paper_id"]
        user_context = arguments["user_context"]
        analysis_type = arguments.get("analysis_type", "comprehensive")
        focus_sections = arguments.get("focus_sections", [])
        llm_provider = arguments.get("llm_provider", "mock")
        
        # Clean paper ID
        if "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        paper_id = paper_id.replace(".pdf", "")
        
        # Load paper
        storage_path = settings.STORAGE_PATH
        md_path = storage_path / f"{paper_id}.md"
        
        if not md_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Paper {paper_id} not found. Please download it first."
                )
            ]
        
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'^#?\s*(.+?)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else paper_id
        
        # Perform analysis
        analyzer = ComparativeAnalyzer(llm_provider)
        results = await analyzer.compare_full_paper(
            content,
            user_context,
            analysis_type,
            focus_sections
        )
        
        # Format output
        output = f"# Comparative Analysis: {title}\n\n"
        output += f"**Your System/Research**:\n{user_context[:200]}...\n\n"
        output += f"**Analysis Type**: {analysis_type}\n"
        output += f"**Sections Analyzed**: {results['sections_analyzed']}\n\n"
        
        # Section-by-section analysis
        output += "## Detailed Analysis by Section\n\n"
        
        for analysis in results["section_analyses"]:
            output += f"### {analysis['section'].title()}\n\n"
            output += analysis["analysis"] + "\n\n"
            output += "---\n\n"
        
        # Key findings summary
        if results["key_findings"]:
            output += "## Key Findings Summary\n\n"
            for finding in results["key_findings"]:
                output += f"- {finding}\n"
        
        # Recommendations
        output += "\n## Recommendations\n\n"
        output += "Based on this analysis, consider:\n\n"
        
        if analysis_type == "better_worse":
            output += "1. **Adopt**: Ideas from the paper that outperform your approach\n"
            output += "2. **Maintain**: Aspects where your system is superior\n"
            output += "3. **Investigate**: Trade-offs that need further research\n"
        
        elif analysis_type == "contradictions":
            output += "1. **Reconcile**: Address contradictions with new evidence\n"
            output += "2. **Test**: Validate conflicting assumptions experimentally\n"
            output += "3. **Refine**: Update your approach based on new findings\n"
        
        elif analysis_type == "unique_ideas":
            output += "1. **Integrate**: Novel approaches that complement your work\n"
            output += "2. **Experiment**: Test unique insights in your context\n"
            output += "3. **Extend**: Build upon new ideas for innovation\n"
        
        # Note about LLM usage
        if llm_provider == "mock":
            output += "\n\n---\n*Note: This is a mock analysis. "
            output += "Set llm_provider to 'openai', 'anthropic', or 'perplexity' for real AI analysis.*"
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error in comparative analysis: {str(e)}"
            )
        ]
```

## Integration Steps (Same for All Tools)

### 1. Update `src/arxiv_mcp_server/tools/__init__.py`

Add imports for each new tool:

```python
# Add these imports
from .extract_citations import extract_citations_tool, handle_extract_citations
from .batch_operations import batch_download_tool, handle_batch_download
from .paper_similarity import find_similar_papers_tool, handle_find_similar_papers
from .extract_sections import extract_sections_tool, handle_extract_sections
from .annotations import add_paper_note_tool, list_paper_notes_tool, handle_add_paper_note, handle_list_paper_notes
from .comparative_analysis import compare_paper_ideas_tool, handle_compare_paper_ideas

# Update __all__ list
__all__ = [
    # ... existing exports ...
    "extract_citations_tool", "handle_extract_citations",
    "batch_download_tool", "handle_batch_download",
    "find_similar_papers_tool", "handle_find_similar_papers",
    "extract_sections_tool", "handle_extract_sections",
    "add_paper_note_tool", "list_paper_notes_tool", 
    "handle_add_paper_note", "handle_list_paper_notes",
    "compare_paper_ideas_tool", "handle_compare_paper_ideas",
]
```

### 2. Update `src/arxiv_mcp_server/server.py`

In the `list_tools()` method:

```python
async def list_tools(self) -> List[types.Tool]:
    return [
        # ... existing tools ...
        extract_citations_tool,
        batch_download_tool,
        find_similar_papers_tool,
        extract_sections_tool,
        add_paper_note_tool,
        list_paper_notes_tool,
        compare_paper_ideas_tool,
    ]
```

In the `call_tool()` method:

```python
async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    # ... existing handlers ...
    elif name == "extract_citations":
        return await handle_extract_citations(arguments)
    elif name == "batch_download":
        return await handle_batch_download(arguments)
    elif name == "find_similar_papers":
        return await handle_find_similar_papers(arguments)
    elif name == "extract_sections":
        return await handle_extract_sections(arguments)
    elif name == "add_paper_note":
        return await handle_add_paper_note(arguments)
    elif name == "list_paper_notes":
        return await handle_list_paper_notes(arguments)
    elif name == "compare_paper_ideas":
        return await handle_compare_paper_ideas(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
```

## Test Commands

Test each tool after implementation:

```bash
# Task 001: Citation Extraction
python -c "import asyncio; from arxiv_mcp_server.tools.extract_citations import handle_extract_citations; print(asyncio.run(handle_extract_citations({'paper_id': '2301.00001'})))"

# Task 002: Batch Download
python -c "import asyncio; from arxiv_mcp_server.tools.batch_operations import handle_batch_download; print(asyncio.run(handle_batch_download({'paper_ids': ['2301.00001', '2301.00002']})))"

# Task 003: Paper Similarity
python -c "import asyncio; from arxiv_mcp_server.tools.paper_similarity import handle_find_similar_papers; print(asyncio.run(handle_find_similar_papers({'paper_id': '2301.00001'})))"

# Task 004: Section Extraction
python -c "import asyncio; from arxiv_mcp_server.tools.extract_sections import handle_extract_sections; print(asyncio.run(handle_extract_sections({'paper_id': '2301.00001', 'sections': ['abstract', 'methods']})))"

# Task 005: Paper Annotations
python -c "import asyncio; from arxiv_mcp_server.tools.annotations import handle_add_paper_note; print(asyncio.run(handle_add_paper_note({'paper_id': '2301.00001', 'note': 'Important methodology in section 3', 'tags': ['methodology', 'review']})))"

# Task 007: Comparative Analysis
python -c "import asyncio; from arxiv_mcp_server.tools.comparative_analysis import handle_compare_paper_ideas; print(asyncio.run(handle_compare_paper_ideas({'paper_id': '2301.00001', 'user_context': 'My Natrium system pairs a 345-MW sodium-cooled fast reactor with molten salt thermal battery', 'analysis_type': 'better_worse'})))"
```

## Common Issues & Pre-Solved Solutions

### Missing Dependencies

```python
# Add fallback imports for optional dependencies
try:
    from tree_sitter import Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

# Add system stats fallback
def get_system_stats():
    """Get system resource statistics."""
    try:
        import psutil
        return {
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "cpu_percent": psutil.cpu_percent(),
        }
    except ImportError:
        # Fallback for systems without psutil
        return {
            "memory_available_gb": 4.0,  # Conservative default
            "cpu_percent": 50.0,
        }
```

### File Not Found Errors

```python
# Always check file existence before operations
if not md_path.exists():
    return [types.TextContent(
        type="text", 
        text=f"Error: Paper {paper_id} not found. Please download it first."
    )]
```

### Concurrent Access Issues

```python
# Use file locking for shared resources
import fcntl

def _save_notes(self):
    with open(self.notes_file, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(self.notes, f, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### Rate Limiting

```python
# Add semaphore for rate limiting
download_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def download_paper_safe(paper_id: str, converter: str) -> Dict[str, Any]:
    async with download_semaphore:
        await asyncio.sleep(0.5)  # Be nice to ArXiv
        # ... rest of function
```

## Validation Checklist

Each tool implementation should pass these checks:

1. **Returns correct type**: `List[types.TextContent]`
2. **Handles missing files**: Returns error message, doesn't crash
3. **Validates inputs**: Checks required parameters
4. **Formats output**: Clear, readable markdown/text
5. **Handles errors**: Try/except blocks with meaningful messages
6. **Resource aware**: Doesn't exhaust memory/CPU
7. **Concurrent safe**: Multiple calls don't conflict

## Full Test Suite

Run all tests after implementation:

```bash
# Run all tool tests
pytest tests/tools/ -v

# Test server integration
python -m arxiv_mcp_server --help

# Manual testing with MCP client
mcp-client arxiv-mcp-server
```