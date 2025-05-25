"""Tool for analyzing code in ArXiv papers using Tree-Sitter."""

import json
from typing import Dict, Any, List
import re
from pathlib import Path
import mcp.types as types
from .tree_sitter_utils import (
    extract_code_metadata,
    get_supported_language,
    get_language_info
)
from ..converters import PyMuPDF4LLMConverter
from ..config import Settings

settings = Settings()

analyze_code_tool = types.Tool(
    name="analyze_paper_code",
    description="Extract and analyze code blocks from ArXiv papers. Uses Tree-Sitter to parse code in 100+ languages and extract function/class metadata, parameters, docstrings, etc.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID (e.g., '2301.00001' or full URL)",
            },
            "languages": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of programming languages to analyze (e.g., ['python', 'cpp']). Leave empty to analyze all detected languages.",
            },
            "min_lines": {
                "type": "integer",
                "description": "Minimum number of lines for a code block to be analyzed (default: 3)",
                "default": 3,
            },
            "extract_functions": {
                "type": "boolean",
                "description": "Extract function definitions and metadata",
                "default": True,
            },
            "extract_classes": {
                "type": "boolean",
                "description": "Extract class definitions and metadata",
                "default": True,
            },
            "include_docstrings": {
                "type": "boolean",
                "description": "Include docstrings in the output",
                "default": True,
            },
        },
        "required": ["paper_id"],
    },
)


def extract_code_blocks(content: str) -> List[Dict[str, Any]]:
    """Extract code blocks from markdown/text content."""
    code_blocks = []
    
    # Pattern for fenced code blocks with optional language
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        language = match.group(1) or "unknown"
        code = match.group(2).strip()
        
        # Skip very short code blocks
        if code.count('\n') + 1 >= 3:  # At least 3 lines
            code_blocks.append({
                "language": language,
                "code": code,
                "line_count": code.count('\n') + 1
            })
    
    # Also look for indented code blocks (4 spaces or tab)
    indented_pattern = r'(?:^|\n)((?:[ ]{4}|\t).*(?:\n(?:[ ]{4}|\t).*)*)'
    indented_matches = re.finditer(indented_pattern, content, re.MULTILINE)
    
    for match in indented_matches:
        code = match.group(1)
        # Remove the indentation
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.startswith('    '):
                cleaned_lines.append(line[4:])
            elif line.startswith('\t'):
                cleaned_lines.append(line[1:])
            else:
                cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines).strip()
        if code.count('\n') + 1 >= 3:
            # Try to detect language from content
            language = detect_language_from_code(code)
            code_blocks.append({
                "language": language,
                "code": code,
                "line_count": code.count('\n') + 1
            })
    
    return code_blocks


def detect_language_from_code(code: str) -> str:
    """Simple heuristic to detect programming language from code content."""
    # Common patterns for different languages
    patterns = {
        "python": [r"^\s*def\s+\w+", r"^\s*class\s+\w+", r"^\s*import\s+", r"^\s*from\s+\w+\s+import"],
        "javascript": [r"^\s*function\s+\w+", r"^\s*const\s+\w+\s*=", r"^\s*let\s+\w+\s*=", r"=>\s*{"],
        "java": [r"^\s*public\s+class", r"^\s*private\s+\w+", r"^\s*public\s+static\s+void\s+main"],
        "cpp": [r"^\s*#include\s*<", r"^\s*using\s+namespace", r"^\s*int\s+main\s*\("],
        "rust": [r"^\s*fn\s+\w+", r"^\s*impl\s+", r"^\s*use\s+", r"^\s*let\s+mut\s+"],
        "go": [r"^\s*func\s+\w+", r"^\s*package\s+\w+", r"^\s*import\s+"],
    }
    
    for language, language_patterns in patterns.items():
        for pattern in language_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return language
    
    return "unknown"


async def handle_analyze_code(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle code analysis requests for ArXiv papers."""
    try:
        paper_id = arguments["paper_id"]
        languages_filter = arguments.get("languages", [])
        min_lines = arguments.get("min_lines", 3)
        extract_functions = arguments.get("extract_functions", True)
        extract_classes = arguments.get("extract_classes", True)
        include_docstrings = arguments.get("include_docstrings", True)
        
        # Clean paper ID
        if "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        paper_id = paper_id.replace(".pdf", "")
        
        # Check if paper content exists
        download_dir = settings.STORAGE_PATH
        pdf_path = download_dir / f"{paper_id}.pdf"
        
        if not pdf_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Paper {paper_id} not found. Please download it first using download_paper."
                )
            ]
        
        # Look for converted content (prefer markdown for code extraction)
        md_path = download_dir / f"{paper_id}.md"
        json_path = download_dir / f"{paper_id}.json"
        
        content = None
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif json_path.exists():
            # Extract text from marker-pdf JSON
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Combine all page text
                content = ""
                for page in data.get("pages", []):
                    for block in page.get("blocks", []):
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                content += span.get("text", "") + " "
                            content += "\n"
        else:
            # Convert PDF to markdown for code extraction
            converter = PyMuPDF4LLMConverter(storage_path=download_dir)
            result = await converter.convert(paper_id, pdf_path)
            if result.success and result.markdown_path:
                with open(result.markdown_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error converting PDF: {result.error}"
                    )
                ]
        
        # Extract code blocks
        code_blocks = extract_code_blocks(content)
        
        # Filter by minimum lines
        code_blocks = [cb for cb in code_blocks if cb["line_count"] >= min_lines]
        
        # Filter by language if specified
        if languages_filter:
            code_blocks = [cb for cb in code_blocks if cb["language"] in languages_filter]
        
        # Analyze each code block
        results = {
            "paper_id": paper_id,
            "total_code_blocks": len(code_blocks),
            "analyzed_blocks": [],
            "language_summary": {},
            "total_functions": 0,
            "total_classes": 0,
        }
        
        for block in code_blocks:
            language = block["language"]
            
            # Check if language is supported by tree-sitter
            supported_lang = get_supported_language(language)
            if not supported_lang and language != "unknown":
                continue
            
            # If language is unknown, try to detect it
            if language == "unknown":
                detected = detect_language_from_code(block["code"])
                supported_lang = get_supported_language(detected)
                if supported_lang:
                    language = detected
                else:
                    continue
            
            # Extract metadata using tree-sitter
            metadata = extract_code_metadata(block["code"], language)
            
            if metadata["tree_sitter_success"]:
                # Build analysis result
                analysis = {
                    "language": language,
                    "line_count": block["line_count"],
                    "functions": [],
                    "classes": [],
                }
                
                # Add functions
                if extract_functions:
                    for func in metadata["functions"]:
                        func_info = {
                            "name": func["name"],
                            "parameters": func["parameters"],
                            "line_span": func["line_span"],
                        }
                        if func.get("return_type"):
                            func_info["return_type"] = func["return_type"]
                        if include_docstrings and func.get("docstring"):
                            func_info["docstring"] = func["docstring"]
                        analysis["functions"].append(func_info)
                
                # Add classes
                if extract_classes:
                    for cls in metadata["classes"]:
                        cls_info = {
                            "name": cls["name"],
                            "line_span": cls["line_span"],
                        }
                        if include_docstrings and cls.get("docstring"):
                            cls_info["docstring"] = cls["docstring"]
                        analysis["classes"].append(cls_info)
                
                # Only add if we found something
                if analysis["functions"] or analysis["classes"]:
                    results["analyzed_blocks"].append(analysis)
                    
                    # Update language summary
                    if language not in results["language_summary"]:
                        results["language_summary"][language] = {
                            "blocks": 0,
                            "functions": 0,
                            "classes": 0,
                        }
                    
                    results["language_summary"][language]["blocks"] += 1
                    results["language_summary"][language]["functions"] += len(analysis["functions"])
                    results["language_summary"][language]["classes"] += len(analysis["classes"])
                    results["total_functions"] += len(analysis["functions"])
                    results["total_classes"] += len(analysis["classes"])
        
        # Format output
        output = f"# Code Analysis for ArXiv Paper {paper_id}\n\n"
        output += f"**Total code blocks found:** {results['total_code_blocks']}\n"
        output += f"**Analyzed blocks:** {len(results['analyzed_blocks'])}\n"
        output += f"**Total functions:** {results['total_functions']}\n"
        output += f"**Total classes:** {results['total_classes']}\n\n"
        
        if results["language_summary"]:
            output += "## Language Summary\n\n"
            for lang, stats in results["language_summary"].items():
                output += f"- **{lang}**: {stats['blocks']} blocks, {stats['functions']} functions, {stats['classes']} classes\n"
            output += "\n"
        
        if results["analyzed_blocks"]:
            output += "## Detailed Analysis\n\n"
            for i, block in enumerate(results["analyzed_blocks"], 1):
                output += f"### Block {i} ({block['language']}, {block['line_count']} lines)\n\n"
                
                if block["functions"]:
                    output += "**Functions:**\n"
                    for func in block["functions"]:
                        params_str = ", ".join([
                            f"{p['name']}{': ' + p['type'] if p['type'] else ''}"
                            for p in func["parameters"]
                        ])
                        output += f"- `{func['name']}({params_str})`"
                        if func.get("return_type"):
                            output += f" -> {func['return_type']}"
                        output += f" (lines {func['line_span'][0]}-{func['line_span'][1]})\n"
                        if func.get("docstring"):
                            output += f"  - Docstring: {func['docstring'][:100]}{'...' if len(func['docstring']) > 100 else ''}\n"
                    output += "\n"
                
                if block["classes"]:
                    output += "**Classes:**\n"
                    for cls in block["classes"]:
                        output += f"- `{cls['name']}` (lines {cls['line_span'][0]}-{cls['line_span'][1]})\n"
                        if cls.get("docstring"):
                            output += f"  - Docstring: {cls['docstring'][:100]}{'...' if len(cls['docstring']) > 100 else ''}\n"
                    output += "\n"
        else:
            output += "\nNo analyzable code blocks found. This could be because:\n"
            output += "- The paper contains no code blocks\n"
            output += "- Code blocks are in unsupported languages\n"
            output += "- Code blocks are shorter than the minimum line requirement\n"
            if languages_filter:
                output += f"- No code blocks match the language filter: {', '.join(languages_filter)}\n"
        
        # Add JSON output for programmatic access
        output += "\n## Raw Analysis Data (JSON)\n\n"
        output += "```json\n"
        output += json.dumps(results, indent=2)
        output += "\n```"
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error analyzing code in paper: {str(e)}"
            )
        ]