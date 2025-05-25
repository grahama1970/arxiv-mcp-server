[![Twitter Follow](https://img.shields.io/twitter/follow/JoeBlazick?style=social)](https://twitter.com/JoeBlazick)
[![smithery badge](https://smithery.ai/badge/arxiv-mcp-server)](https://smithery.ai/server/arxiv-mcp-server)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/blazickjp/arxiv-mcp-server/actions/workflows/tests.yml/badge.svg)](https://github.com/blazickjp/arxiv-mcp-server/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://img.shields.io/pypi/dm/arxiv-mcp-server.svg)](https://pypi.org/project/arxiv-mcp-server/)
[![PyPI Version](https://img.shields.io/pypi/v/arxiv-mcp-server.svg)](https://pypi.org/project/arxiv-mcp-server/)

# ArXiv MCP Server

> 🔍 Enable AI assistants to search and access arXiv papers through a simple MCP interface.

The ArXiv MCP Server provides a bridge between AI assistants and arXiv's research repository through the Model Context Protocol (MCP). It allows AI models to search for papers and access their content in a programmatic way.

<div align="center">
  
🤝 **[Contribute](https://github.com/blazickjp/arxiv-mcp-server/blob/main/CONTRIBUTING.md)** • 
📝 **[Report Bug](https://github.com/blazickjp/arxiv-mcp-server/issues)**

<a href="https://www.pulsemcp.com/servers/blazickjp-arxiv-mcp-server"><img src="https://www.pulsemcp.com/badge/top-pick/blazickjp-arxiv-mcp-server" width="400" alt="Pulse MCP Badge"></a>
</div>

## 📚 Documentation

- [**Quick Reference**](docs/QUICK_REFERENCE.md) - All 15 tools at a glance with examples
- [**Usage Guide**](docs/USAGE_GUIDE.md) - Detailed workflows and best practices
- [**Task Implementation**](docs/tasks/001_arxiv_mcp_features.md) - Technical implementation details

## ✨ Core Features

- 🔎 **Paper Search**: Query arXiv papers with filters for date ranges and categories
- 📄 **Paper Access**: Download and read paper content with advanced PDF conversion
- 📋 **Paper Listing**: View all downloaded papers
- 🗃️ **Local Storage**: Papers are saved locally for faster access
- 📝 **Prompts**: A Set of Research Prompts
- 💻 **Code Analysis**: Extract and analyze code blocks from papers using Tree-Sitter
- 🖼️ **Content Description**: Use LLMs to describe tables and images in papers
- 📚 **Smart Summarization**: Rolling window summarization for long papers with context preservation
- 📖 **Citation Extraction**: Extract references in BibTeX, JSON, or EndNote formats
- ⚡ **Batch Operations**: Download multiple papers concurrently with resource management
- 🤖 **AI Comparison**: Compare papers against your research using LLMs
- 🔍 **Paper Similarity**: Find similar papers by content or authors
- 📑 **Section Extraction**: Extract specific sections from papers
- 📝 **Annotations**: Add notes and tags to papers with local storage

## 🚀 Quick Start

### Installing via Smithery

To install ArXiv Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/arxiv-mcp-server):

```bash
npx -y @smithery/cli install arxiv-mcp-server --client claude
```

### Installing Manually
Install using uv:

```bash
uv tool install arxiv-mcp-server
```

For development:

```bash
# Clone and set up development environment
git clone https://github.com/blazickjp/arxiv-mcp-server.git
cd arxiv-mcp-server

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install with test dependencies
uv pip install -e ".[test]"
```

### 🔌 MCP Integration

Add this configuration to your MCP client config file:

```json
{
    "mcpServers": {
        "arxiv-mcp-server": {
            "command": "uv",
            "args": [
                "tool",
                "run",
                "arxiv-mcp-server",
                "--storage-path", "/path/to/paper/storage"
            ]
        }
    }
}
```

For Development:

```json
{
    "mcpServers": {
        "arxiv-mcp-server": {
            "command": "uv",
            "args": [
                "--directory",
                "path/to/cloned/arxiv-mcp-server",
                "run",
                "arxiv-mcp-server",
                "--storage-path", "/path/to/paper/storage"
            ]
        }
    }
}
```

## 💡 Available Tools

The server provides fifteen main tools:

### 1. Paper Search
Search for papers with optional filters:

```python
result = await call_tool("search_papers", {
    "query": "transformer architecture",
    "max_results": 10,
    "date_from": "2023-01-01",
    "categories": ["cs.AI", "cs.LG"]
})
```

### 2. Paper Download with Advanced Conversion
Download a paper with conversion options:

```python
# Default (fast conversion)
result = await call_tool("download_paper", {
    "paper_id": "2401.12345"
})

# High accuracy with marker-pdf (recommended)
result = await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf"
})

# JSON output for structured data (marker-pdf only)
result = await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",
    "output_format": "json"
})
```

### 3. List Papers
View all downloaded papers:

```python
result = await call_tool("list_papers", {})
```

### 4. Read Paper
Access the content of a downloaded paper:

```python
result = await call_tool("read_paper", {
    "paper_id": "2401.12345"
})
```

### 5. Get Conversion Options
Check available PDF converters and their capabilities:

```python
result = await call_tool("get_conversion_options", {})
```

### 6. Describe Paper Content
Use LLM to describe tables and images extracted from papers:

```python
# Describe all content (requires JSON format from marker-pdf)
result = await call_tool("describe_paper_content", {
    "paper_id": "2401.12345",
    "content_type": "both",  # or "table" or "image"
    "llm_model": "gpt-4-vision-preview"  # or "claude-3-opus-20240229"
})
```

### 7. Analyze Paper Code
Extract and analyze code blocks from papers using Tree-Sitter:

```python
# Analyze all code in the paper
result = await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "min_lines": 3
})

# Analyze specific languages
result = await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "languages": ["python", "javascript"],
    "extract_functions": true,
    "extract_classes": true,
    "include_docstrings": true
})
```

This tool uses Tree-Sitter to:
- Extract code blocks from papers
- Identify programming languages automatically
- Parse code structure (functions, classes, parameters)
- Support 100+ programming languages
- Provide detailed metadata about code implementations

### 8. Summarize Paper (Rolling Window)
Summarize long ArXiv papers using advanced chunking strategies:

```python
# Basic summarization with rolling window
result = await call_tool("summarize_paper", {
    "paper_id": "2401.12345"
})

# Advanced summarization options
result = await call_tool("summarize_paper", {
    "paper_id": "2401.12345",
    "strategy": "rolling_window",  # or "map_reduce", "hierarchical"
    "chunk_size": 2000,  # tokens per chunk
    "overlap_size": 200,  # overlap tokens (auto if not set)
    "summary_type": "technical",  # or "abstract", "detailed", "findings"
    "max_summary_length": 1500,
    "preserve_sections": true
})
```

Features:
- **Rolling Window**: Maintains context across chunks for coherent summaries
- **Map-Reduce**: Parallel processing for faster results
- **Hierarchical**: Tree-based summarization for very long papers
- **Smart Chunking**: Sentence-aware splitting with configurable overlap
- **Section Preservation**: Maintains paper structure in summaries
- Handles papers of any length by chunking intelligently

### 9. Extract Citations
Extract bibliography/references from papers in multiple formats:

```python
# Extract as BibTeX (default)
result = await call_tool("extract_citations", {
    "paper_id": "2401.12345"
})

# Extract as JSON or EndNote
result = await call_tool("extract_citations", {
    "paper_id": "2401.12345",
    "format": "json",  # or "endnote"
    "include_arxiv_links": true
})
```

Features:
- Supports BibTeX, JSON, and EndNote formats
- Auto-detects ArXiv paper references
- Adds clickable links for ArXiv papers
- Handles various citation styles

### 10. Batch Download
Download multiple papers concurrently with resource management:

```python
# Download specific papers
result = await call_tool("batch_download", {
    "paper_ids": ["2401.12345", "2401.12346", "2401.12347"],
    "skip_existing": true
})

# Download from search results
result = await call_tool("batch_download", {
    "search_query": "transformer architecture attention",
    "max_results": 10,
    "convert_to": "markdown"
})
```

Features:
- Concurrent downloads with auto-adjustment based on CPU
- Progress tracking for each paper
- Skip already downloaded papers
- Automatic conversion after download

### 11. Compare Paper Ideas
Compare paper content against your research using AI:

```python
# Basic comparison
result = await call_tool("compare_paper_ideas", {
    "paper_id": "2401.12345",
    "research_context": "my Natrium system pairs a 345-MW sodium-cooled fast reactor with thermal storage"
})

# Detailed comparison with focus areas
result = await call_tool("compare_paper_ideas", {
    "paper_id": "2401.12345",
    "research_context": "my quantum algorithm for optimization",
    "comparison_type": "technical",  # or "comprehensive", "approach", "results"
    "focus_areas": ["efficiency", "scalability", "accuracy"],
    "llm_provider": "openai"  # or "anthropic", "perplexity", "mock"
})
```

Features:
- Finds better/worse ideas relative to your approach
- Identifies contradictions with your research
- Extracts unique insights
- Provides actionable recommendations
- Mock provider for testing without API keys

### 12. Find Similar Papers
Find papers similar to a given paper:

```python
# Find by content similarity
result = await call_tool("find_similar_papers", {
    "paper_id": "2401.12345",
    "similarity_type": "content",
    "top_k": 5
})

# Find by author overlap
result = await call_tool("find_similar_papers", {
    "paper_id": "2401.12345",
    "similarity_type": "authors",
    "min_similarity": 0.3
})
```

Features:
- Content similarity using TF-IDF
- Author-based similarity (Jaccard)
- Combined similarity scoring
- Works with locally stored papers

### 13. Extract Sections
Extract specific sections from papers:

```python
# Extract multiple sections
result = await call_tool("extract_sections", {
    "paper_id": "2401.12345",
    "sections": ["abstract", "introduction", "methods", "results"],
    "include_subsections": true
})
```

Features:
- Handles common section name variations
- Include/exclude subsections
- Shows available sections if not found
- Supports both markdown and plain text formats

### 14. Add Paper Notes
Add annotations and tags to papers:

```python
# Add a note with tags
result = await call_tool("add_paper_note", {
    "paper_id": "2401.12345",
    "note": "Interesting approach to attention mechanism, could apply to my work",
    "tags": ["attention", "transformer", "to-read"],
    "section_ref": "Section 3.2"
})
```

### 15. List Paper Notes
Search and list notes across papers:

```python
# List all notes for a paper
result = await call_tool("list_paper_notes", {
    "paper_id": "2401.12345"
})

# Search notes by tags or text
result = await call_tool("list_paper_notes", {
    "tags": ["attention", "transformer"],
    "search_text": "interesting"
})
```

Features:
- Local JSON storage for notes
- Tag-based organization
- Full-text search in notes
- Section references

## 🔄 PDF Conversion Features

The server supports multiple PDF to Markdown converters with different capabilities:

### Available Converters

1. **pymupdf4llm** (default) ⚡ Fast & Lightweight
   - **Very fast** conversion speed
   - **Low memory usage** and computational requirements
   - Good text extraction for most papers
   - Basic table support
   - Supports: Markdown output only
   - ✅ Use when: Speed matters, resources are limited

2. **marker-pdf** 🎯 Accurate but Resource-Intensive
   - **Much more accurate** than pymupdf4llm
   - Superior table and equation extraction
   - Better handling of complex layouts
   - Supports: Markdown and JSON output
   - ⚠️ **WARNING: VERY computationally expensive**
     - Requires 4GB+ RAM for large papers
     - 10-50x slower than pymupdf4llm
     - May cause system slowdown
   - ✅ Use when: Accuracy is critical
   - Install with: `pip install marker-pdf`

### Conversion Examples

```python
# High-quality markdown for reading
result = await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf"
})

# Structured JSON for data extraction
result = await call_tool("download_paper", {
    "paper_id": "2401.12345", 
    "converter": "marker-pdf",
    "output_format": "json"
})
```

## 🤖 LLM Content Description

The server can use AI models to automatically describe tables and images in papers:

### Prerequisites
1. Download paper with marker-pdf in JSON format
2. Set up LLM API keys (optional, uses mock provider otherwise):
   - OpenAI: `export OPENAI_API_KEY=your-key`
   - Anthropic: `export ANTHROPIC_API_KEY=your-key`

### Example Workflow
```python
# 1. Download paper with JSON output
await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",
    "output_format": "json"
})

# 2. Describe all tables and images
await call_tool("describe_paper_content", {
    "paper_id": "2401.12345",
    "content_type": "both",
    "llm_model": "gpt-4-vision-preview"
})

# 3. Or use Camelot for better table extraction
await call_tool("describe_paper_content", {
    "paper_id": "2401.12345",
    "content_type": "table",
    "use_camelot": true,
    "camelot_flavor": "lattice"
})
```

### Features
- Concurrent processing with progress tracking
- Supports GPT-4 Vision and Claude for analysis
- Extracts images and tables with location metadata
- Batch processing with rate limiting
- Detailed descriptions of visual content
- Optional Camelot integration for enhanced table extraction
- Extraction accuracy metrics for quality assurance

## 📝 Research Prompts

The server offers specialized prompts to help analyze academic papers:

### Paper Analysis Prompt
A comprehensive workflow for analyzing academic papers that only requires a paper ID:

```python
result = await call_prompt("deep-paper-analysis", {
    "paper_id": "2401.12345"
})
```

This prompt includes:
- Detailed instructions for using available tools (list_papers, download_paper, read_paper, search_papers)
- A systematic workflow for paper analysis
- Comprehensive analysis structure covering:
  - Executive summary
  - Research context
  - Methodology analysis
  - Results evaluation
  - Practical and theoretical implications
  - Future research directions
  - Broader impacts

### Conversion Guide Prompt
Get guidance on using the advanced PDF conversion features:

```python
result = await call_prompt("conversion-guide", {
    "use_case": "tables"  # or "data-extraction", "reading", "analysis"
})
```

This prompt provides:
- Detailed converter comparison
- Best practices for different use cases
- Examples of when to use each converter
- JSON vs Markdown format selection guidance

### Content Description Guide Prompt
Learn how to use LLM-based content description:

```python
result = await call_prompt("content-description-guide", {})
```

This prompt provides:
- Complete workflow for content description
- LLM model selection guidance
- API setup instructions
- Use cases and best practices

### Comprehensive Research Guide Prompt
Get a complete guide for using all 15 ArXiv MCP server tools effectively:

```python
result = await call_prompt("comprehensive-research-guide", {})
```

This prompt provides:
- Overview of all 15 available tools
- Complete workflows for common research tasks:
  - Initial research exploration
  - Deep paper analysis
  - Comparative research
  - Literature reviews
  - Daily research tracking
- Best practices and efficiency tips
- Tool selection guidance
- Common usage patterns
- Detailed examples for each tool

## ⚙️ Configuration

Configure through environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ARXIV_STORAGE_PATH` | Paper storage location | ~/.arxiv-mcp-server/papers |

### Optional Dependencies

For enhanced table extraction with Camelot:
```bash
# Install with Camelot support
uv pip install arxiv-mcp-server[camelot]

# Or install Camelot separately
pip install camelot-py[cv]

# Note: Camelot also requires Ghostscript
# Ubuntu/Debian: sudo apt-get install ghostscript
# macOS: brew install ghostscript
# Windows: Download from https://www.ghostscript.com/
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest
```

## 📄 License

Released under the MIT License. See the LICENSE file for details.

---

<div align="center">

Made with ❤️ by the Pearl Labs Team

<a href="https://glama.ai/mcp/servers/04dtxi5i5n"><img width="380" height="200" src="https://glama.ai/mcp/servers/04dtxi5i5n/badge" alt="ArXiv Server MCP server" /></a>
</div>
