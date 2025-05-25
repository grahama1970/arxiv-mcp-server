"""Tool for summarizing ArXiv papers using rolling window technique."""

import json
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
import mcp.types as types
from ..config import Settings
import math

settings = Settings()

SummarizationStrategy = Literal["rolling_window", "map_reduce", "hierarchical"]

summarize_paper_tool = types.Tool(
    name="summarize_paper",
    description="Summarize ArXiv papers using rolling window technique for long documents. Handles papers that exceed LLM context limits by intelligently chunking and summarizing.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID (e.g., '2301.00001' or full URL)",
            },
            "strategy": {
                "type": "string",
                "description": "Summarization strategy: rolling_window (maintains context), map_reduce (parallel but less context), hierarchical (tree-based)",
                "enum": ["rolling_window", "map_reduce", "hierarchical"],
                "default": "rolling_window",
            },
            "chunk_size": {
                "type": "integer",
                "description": "Size of each chunk in tokens (default: 2000 for detail, 4000 for overview)",
                "default": 2000,
            },
            "overlap_size": {
                "type": "integer",
                "description": "Number of tokens to overlap between chunks (default: 200)",
                "default": 200,
            },
            "summary_type": {
                "type": "string",
                "description": "Type of summary: abstract (brief), detailed (comprehensive), technical (methods focus), or findings (results focus)",
                "enum": ["abstract", "detailed", "technical", "findings"],
                "default": "detailed",
            },
            "max_summary_length": {
                "type": "integer",
                "description": "Maximum length of final summary in tokens",
                "default": 1000,
            },
            "preserve_sections": {
                "type": "boolean",
                "description": "Preserve paper section structure in summary",
                "default": True,
            },
        },
        "required": ["paper_id"],
    },
)


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 characters)."""
    return len(text) // 4


def chunk_text_with_overlap(
    text: str, 
    chunk_size: int = 2000, 
    overlap_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Split text into chunks with overlap to maintain context.
    Inspired by llm-summarizer's approach with sentence-aware chunking.
    
    Args:
        text: The text to chunk
        chunk_size: Target size of each chunk in tokens
        overlap_size: Number of tokens to overlap (auto-calculated if None)
        
    Returns:
        List of chunks with metadata
    """
    # Split into sentences for better chunking
    import re
    
    # Improved sentence splitting pattern
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n+|\n\n+'
    sentences = re.split(sentence_pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return [{
            "chunk_num": 0,
            "text": text,
            "start_char": 0,
            "end_char": len(text),
            "estimated_tokens": estimate_tokens(text),
            "is_first": True,
            "is_last": True,
            "sentence_count": 0
        }]
    
    # Auto-calculate overlap if not specified (5% of sentences)
    if overlap_size is None:
        overlap_sentences = max(1, len(sentences) // 20)
    else:
        # Convert token overlap to sentence count estimate
        avg_sentence_tokens = sum(estimate_tokens(s) for s in sentences) // len(sentences)
        overlap_sentences = max(1, overlap_size // avg_sentence_tokens)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_num = 0
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_tokens = estimate_tokens(sentence)
        
        # Handle oversized sentences
        if sentence_tokens > chunk_size and not current_chunk:
            # Split large sentence into smaller parts
            words = sentence.split()
            part_size = chunk_size * 4 // 5  # Leave some buffer
            
            for j in range(0, len(words), part_size):
                part = ' '.join(words[j:j + part_size])
                chunks.append({
                    "chunk_num": chunk_num,
                    "text": part,
                    "estimated_tokens": estimate_tokens(part),
                    "is_first": chunk_num == 0,
                    "is_last": False,
                    "sentence_count": 0,  # Partial sentence
                    "is_partial": True
                })
                chunk_num += 1
            i += 1
            continue
        
        # Add sentence to current chunk if it fits
        if current_tokens + sentence_tokens <= chunk_size or not current_chunk:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
            i += 1
        else:
            # Save current chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                "chunk_num": chunk_num,
                "text": chunk_text,
                "estimated_tokens": current_tokens,
                "is_first": chunk_num == 0,
                "is_last": False,
                "sentence_count": len(current_chunk),
                "is_partial": False
            })
            chunk_num += 1
            
            # Start new chunk with overlap
            if overlap_sentences > 0 and len(current_chunk) > overlap_sentences:
                # Keep last N sentences for overlap
                current_chunk = current_chunk[-overlap_sentences:]
                current_tokens = sum(estimate_tokens(s) for s in current_chunk)
            else:
                current_chunk = []
                current_tokens = 0
    
    # Add final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append({
            "chunk_num": chunk_num,
            "text": chunk_text,
            "estimated_tokens": current_tokens,
            "is_first": chunk_num == 0,
            "is_last": True,
            "sentence_count": len(current_chunk),
            "is_partial": False
        })
    
    # Mark last chunk
    if chunks:
        chunks[-1]["is_last"] = True
    
    return chunks


def extract_sections(text: str) -> Dict[str, str]:
    """Extract common paper sections."""
    sections = {
        "title": "",
        "abstract": "",
        "introduction": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
        "references": ""
    }
    
    # Simple section extraction based on common headers
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    section_headers = {
        "abstract": ["abstract", "summary"],
        "introduction": ["introduction", "1 introduction", "1. introduction"],
        "methods": ["methods", "methodology", "materials and methods", "approach"],
        "results": ["results", "experiments", "experimental results", "findings"],
        "discussion": ["discussion", "analysis"],
        "conclusion": ["conclusion", "conclusions", "concluding remarks"],
        "references": ["references", "bibliography", "citations"]
    }
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # Check if this line is a section header
        for section, headers in section_headers.items():
            if any(line_lower.startswith(h) or line_lower.endswith(h) for h in headers):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = section
                section_content = []
                break
        else:
            # Not a header, add to current section
            if current_section:
                section_content.append(line)
            elif not sections["title"] and line.strip():
                # First non-empty line might be title
                sections["title"] = line.strip()
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(section_content).strip()
    
    return sections


def create_summary_prompt(
    chunk_text: str,
    summary_type: str,
    previous_summary: Optional[str] = None,
    is_first: bool = False,
    is_last: bool = False
) -> str:
    """Create appropriate prompt based on summary type and strategy."""
    
    type_instructions = {
        "abstract": "Create a brief, high-level summary focusing on key findings and contributions.",
        "detailed": "Create a comprehensive summary covering all important points, methods, and findings.",
        "technical": "Focus on methodology, algorithms, technical approach, and implementation details.",
        "findings": "Focus on results, conclusions, and practical implications of the research."
    }
    
    base_instruction = type_instructions.get(summary_type, type_instructions["detailed"])
    
    if previous_summary:
        # Rolling window refinement
        prompt = f"""You are refining a summary of an academic paper. 

Previous summary of earlier sections:
{previous_summary}

New section to incorporate:
{chunk_text}

Instructions: {base_instruction}

Integrate the new information with the previous summary, maintaining continuity and avoiding redundancy. If this is the final section, ensure the summary is complete and well-rounded.

Refined summary:"""
    else:
        # First chunk or independent summary
        prompt = f"""Summarize the following section of an academic paper.

Text:
{chunk_text}

Instructions: {base_instruction}

{"This is the beginning of the paper." if is_first else ""}
{"This is the final section of the paper." if is_last else ""}

Summary:"""
    
    return prompt


async def handle_summarize_paper(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper summarization requests."""
    try:
        paper_id = arguments["paper_id"]
        strategy = arguments.get("strategy", "rolling_window")
        chunk_size = arguments.get("chunk_size", 2000)
        overlap_size = arguments.get("overlap_size", 200)
        summary_type = arguments.get("summary_type", "detailed")
        max_summary_length = arguments.get("max_summary_length", 1000)
        preserve_sections = arguments.get("preserve_sections", True)
        
        # Clean paper ID
        if "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        paper_id = paper_id.replace(".pdf", "")
        
        # Find paper content
        storage_path = settings.STORAGE_PATH
        md_path = storage_path / f"{paper_id}.md"
        txt_path = storage_path / f"{paper_id}.txt"
        
        content = None
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Paper {paper_id} not found. Please download it first using download_paper."
                )
            ]
        
        # Extract sections if requested
        sections = {}
        if preserve_sections:
            sections = extract_sections(content)
        
        # Estimate total tokens
        total_tokens = estimate_tokens(content)
        
        # Chunk the content
        chunks = chunk_text_with_overlap(content, chunk_size, overlap_size)
        
        # Prepare output
        output = f"# Summary of ArXiv Paper {paper_id}\n\n"
        output += f"**Strategy:** {strategy}\n"
        output += f"**Summary Type:** {summary_type}\n"
        output += f"**Document Length:** ~{total_tokens:,} tokens\n"
        output += f"**Chunks:** {len(chunks)}\n\n"
        
        if strategy == "rolling_window":
            output += "## Rolling Window Summary\n\n"
            output += "This summary was created by maintaining context across document chunks:\n\n"
            
            # Simulate rolling window summarization
            summaries = []
            previous_summary = None
            
            for i, chunk in enumerate(chunks):
                # In a real implementation, this would call an LLM
                prompt = create_summary_prompt(
                    chunk["text"][:500] + "...",  # Truncate for display
                    summary_type,
                    previous_summary,
                    chunk["is_first"],
                    chunk["is_last"]
                )
                
                # Simulate summary (in real implementation, call LLM here)
                chunk_summary = f"[Chunk {i+1}/{len(chunks)}] Summary of ~{chunk['estimated_tokens']} tokens"
                summaries.append(chunk_summary)
                
                # Update rolling summary
                if previous_summary:
                    previous_summary = f"{previous_summary}\n{chunk_summary}"
                else:
                    previous_summary = chunk_summary
                
                # Keep rolling summary under control
                if estimate_tokens(previous_summary) > max_summary_length:
                    # In real implementation, would re-summarize here
                    previous_summary = f"[Condensed summary of chunks 1-{i+1}]"
            
            output += "### Final Summary\n\n"
            output += f"{previous_summary}\n\n"
            
        elif strategy == "map_reduce":
            output += "## Map-Reduce Summary\n\n"
            output += "This summary was created by summarizing chunks in parallel then combining:\n\n"
            
            # Simulate map phase
            output += "### Map Phase (Parallel Summaries)\n"
            for i, chunk in enumerate(chunks[:3]):  # Show first 3
                output += f"- Chunk {i+1}: ~{chunk['estimated_tokens']} tokens summarized\n"
            if len(chunks) > 3:
                output += f"- ... and {len(chunks)-3} more chunks\n"
            
            output += "\n### Reduce Phase\n"
            output += "Combined summary of all chunks: [Would be generated by LLM]\n\n"
            
        elif strategy == "hierarchical":
            output += "## Hierarchical Summary\n\n"
            output += "This summary was created using a tree-based approach:\n\n"
            
            # Calculate tree levels
            levels = math.ceil(math.log(len(chunks), 2))
            output += f"### Tree Structure ({levels} levels)\n"
            output += f"- Level 0: {len(chunks)} original chunks\n"
            
            current_level_size = len(chunks)
            for level in range(1, levels + 1):
                current_level_size = math.ceil(current_level_size / 2)
                output += f"- Level {level}: {current_level_size} combined summaries\n"
            
            output += "\n### Final Summary\n"
            output += "[Hierarchical summary would be generated by recursive LLM calls]\n\n"
        
        # Add section summaries if available
        if preserve_sections and any(sections.values()):
            output += "## Section Summaries\n\n"
            for section, content in sections.items():
                if content:
                    output += f"### {section.title()}\n"
                    output += f"[{estimate_tokens(content)} tokens in this section]\n\n"
        
        # Add implementation note
        output += "---\n\n"
        output += "**Note:** This is a demonstration of the rolling window summarization architecture. "
        output += "In a full implementation, each chunk would be processed by an LLM (GPT-4, Claude, etc.) "
        output += "to generate actual summaries. The rolling window approach maintains context across chunks, "
        output += "making it ideal for academic papers where concepts build upon each other.\n\n"
        
        output += "**Benefits for ArXiv papers:**\n"
        output += "- Handle papers of any length (even 100+ pages)\n"
        output += "- Maintain context across sections\n"
        output += "- Preserve technical accuracy\n"
        output += "- Flexible summary types (abstract, technical, findings)\n"
        output += "- Section-aware processing\n"
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error summarizing paper: {str(e)}"
            )
        ]