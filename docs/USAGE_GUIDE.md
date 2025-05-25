# ArXiv MCP Server Usage Guide

This guide provides practical examples and workflows for using all the ArXiv MCP server features effectively.

## Table of Contents
1. [Complete Research Workflow](#complete-research-workflow)
2. [Individual Tool Examples](#individual-tool-examples)
3. [Common Use Cases](#common-use-cases)
4. [Tips and Best Practices](#tips-and-best-practices)

## Complete Research Workflow

Here's a comprehensive example showing how to use all tools together for a research project:

```python
# 1. Start by searching for papers in your area
papers = await call_tool("search_papers", {
    "query": "sodium-cooled fast reactor thermal storage",
    "max_results": 20,
    "date_from": "2020-01-01",
    "categories": ["physics.app-ph", "nucl-ex"]
})

# 2. Batch download the most relevant papers
await call_tool("batch_download", {
    "paper_ids": ["2401.12345", "2401.12346", "2401.12347", "2401.12348", "2401.12349"],
    "convert_to": "markdown",
    "skip_existing": true
})

# 3. Read and analyze a specific paper
paper_content = await call_tool("read_paper", {
    "paper_id": "2401.12345"
})

# 4. Extract key sections for focused reading
sections = await call_tool("extract_sections", {
    "paper_id": "2401.12345",
    "sections": ["abstract", "methods", "results", "conclusion"],
    "include_subsections": true
})

# 5. Extract citations for your bibliography
citations = await call_tool("extract_citations", {
    "paper_id": "2401.12345",
    "format": "bibtex",
    "include_arxiv_links": true
})

# 6. Compare the paper with your research
comparison = await call_tool("compare_paper_ideas", {
    "paper_id": "2401.12345",
    "research_context": "my Natrium system pairs a 345-MW sodium-cooled fast reactor with a molten salt thermal battery for grid storage",
    "comparison_type": "comprehensive",
    "focus_areas": ["efficiency", "safety", "cost", "scalability"],
    "llm_provider": "mock"  # Use "openai" or "anthropic" with API keys
})

# 7. Find similar papers to explore related work
similar = await call_tool("find_similar_papers", {
    "paper_id": "2401.12345",
    "similarity_type": "combined",  # Uses both content and author similarity
    "top_k": 10,
    "min_similarity": 0.4
})

# 8. Add notes for future reference
await call_tool("add_paper_note", {
    "paper_id": "2401.12345",
    "note": "Novel heat exchanger design could improve our thermal efficiency by 15%. Need to investigate compatibility with molten salt.",
    "tags": ["heat-exchanger", "efficiency", "follow-up"],
    "section_ref": "Section 3.2 - Heat Transfer Analysis"
})

# 9. Summarize the paper for quick review
summary = await call_tool("summarize_paper", {
    "paper_id": "2401.12345",
    "strategy": "rolling_window",
    "summary_type": "technical",
    "max_summary_length": 1000,
    "preserve_sections": true
})

# 10. Extract and analyze code if the paper includes implementations
code_analysis = await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "languages": ["python", "matlab"],
    "extract_functions": true,
    "include_docstrings": true
})
```

## Individual Tool Examples

### 1. Advanced Search with Filters

```python
# Search for recent machine learning papers
results = await call_tool("search_papers", {
    "query": "transformer attention mechanism",
    "max_results": 50,
    "date_from": "2023-01-01",
    "date_to": "2024-01-01",
    "categories": ["cs.LG", "cs.CL"]
})
```

### 2. Smart Batch Operations

```python
# Download papers from a search query with advanced options
await call_tool("batch_download", {
    "search_query": "large language models safety alignment",
    "max_results": 15,
    "max_concurrent": 4,  # Limit concurrent downloads
    "convert_to": "markdown",
    "skip_existing": true
})

# Download specific papers with different converters
await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",  # High accuracy for complex papers
    "output_format": "json"  # For structured data extraction
})
```

### 3. Paper Comparison Workflows

```python
# Compare multiple papers against your research
paper_ids = ["2401.12345", "2401.12346", "2401.12347"]
comparisons = []

for paper_id in paper_ids:
    result = await call_tool("compare_paper_ideas", {
        "paper_id": paper_id,
        "research_context": "my approach uses reinforcement learning with human feedback for LLM alignment",
        "comparison_type": "approach",
        "focus_areas": ["sample efficiency", "human oversight", "scalability"],
        "llm_provider": "mock"
    })
    comparisons.append(result)
```

### 4. Building a Citation Network

```python
# Extract citations from multiple papers to build a network
base_papers = ["2401.12345", "2401.12346", "2401.12347"]
all_citations = {}

for paper_id in base_papers:
    citations = await call_tool("extract_citations", {
        "paper_id": paper_id,
        "format": "json",
        "include_arxiv_links": true
    })
    all_citations[paper_id] = citations

# Find papers that cite similar work
for paper_id in base_papers:
    similar = await call_tool("find_similar_papers", {
        "paper_id": paper_id,
        "similarity_type": "content",
        "top_k": 5
    })
```

### 5. Research Notes Management

```python
# Create a structured note-taking system
await call_tool("add_paper_note", {
    "paper_id": "2401.12345",
    "note": "Key insight: Uses contrastive learning for better representations",
    "tags": ["methodology", "contrastive-learning", "representation"],
    "section_ref": "Section 4.1"
})

# Add implementation notes
await call_tool("add_paper_note", {
    "paper_id": "2401.12345",
    "note": "Implementation available at github.com/author/repo - tested with our data",
    "tags": ["implementation", "code", "tested"],
    "section_ref": "Appendix A"
})

# Search across all notes
all_methodology_notes = await call_tool("list_paper_notes", {
    "tags": ["methodology"],
    "search_text": "learning"
})
```

### 6. Section-Based Analysis

```python
# Extract specific sections from multiple papers for comparison
papers = ["2401.12345", "2401.12346", "2401.12347"]
all_methods = []

for paper_id in papers:
    methods = await call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["methods", "methodology", "approach"],
        "include_subsections": true
    })
    all_methods.append(methods)

# Extract only abstracts for quick overview
abstracts = []
for paper_id in papers:
    abstract = await call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["abstract"],
        "include_subsections": false
    })
    abstracts.append(abstract)
```

### 7. Code Extraction and Analysis

```python
# Analyze code in papers with specific language focus
code_analysis = await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "languages": ["python"],
    "min_lines": 5,  # Ignore small snippets
    "extract_functions": true,
    "extract_classes": true,
    "include_docstrings": true
})

# Extract all code for reproduction
all_code = await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "min_lines": 1,  # Get everything
    "include_context": true
})
```

## Common Use Cases

### Literature Review Workflow

```python
# 1. Broad search
papers = await call_tool("search_papers", {
    "query": "your research topic",
    "max_results": 100,
    "date_from": "2020-01-01"
})

# 2. Batch download promising papers
await call_tool("batch_download", {
    "paper_ids": selected_paper_ids,
    "convert_to": "markdown"
})

# 3. Extract and compile all abstracts
for paper_id in selected_paper_ids:
    abstract = await call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["abstract"]
    })
    
    # Add summary note
    await call_tool("add_paper_note", {
        "paper_id": paper_id,
        "note": f"Relevance: {relevance_score}/10. Main contribution: {main_point}",
        "tags": ["literature-review", category]
    })

# 4. Create bibliography
for paper_id in selected_paper_ids:
    citations = await call_tool("extract_citations", {
        "paper_id": paper_id,
        "format": "bibtex"
    })
```

### Competitive Analysis Workflow

```python
# Compare your approach against multiple competing methods
competing_papers = ["2401.12345", "2401.12346", "2401.12347"]
my_approach = "Description of your method/system"

comparisons = {}
for paper_id in competing_papers:
    # Get paper summary first
    summary = await call_tool("summarize_paper", {
        "paper_id": paper_id,
        "strategy": "rolling_window",
        "summary_type": "technical",
        "max_summary_length": 500
    })
    
    # Compare against your approach
    comparison = await call_tool("compare_paper_ideas", {
        "paper_id": paper_id,
        "research_context": my_approach,
        "comparison_type": "technical",
        "focus_areas": ["performance", "complexity", "scalability"],
        "llm_provider": "mock"
    })
    
    comparisons[paper_id] = {
        "summary": summary,
        "comparison": comparison
    }
```

### Daily Research Tracking

```python
# Morning routine: Check new papers
new_papers = await call_tool("search_papers", {
    "query": "your research keywords",
    "max_results": 10,
    "date_from": "2024-01-01"  # Recent papers only
})

# Download interesting ones
await call_tool("batch_download", {
    "paper_ids": interesting_ids,
    "skip_existing": true
})

# Quick review with summaries
for paper_id in interesting_ids:
    summary = await call_tool("summarize_paper", {
        "paper_id": paper_id,
        "strategy": "map_reduce",  # Faster for quick review
        "summary_type": "abstract",
        "max_summary_length": 300
    })
    
    # Tag for later reading
    await call_tool("add_paper_note", {
        "paper_id": paper_id,
        "note": "To read - relevant to current project",
        "tags": ["unread", "relevant", date.today().isoformat()]
    })
```

## Tips and Best Practices

### 1. Efficient Paper Processing

```python
# Use batch operations for efficiency
# Good: Process multiple papers at once
await call_tool("batch_download", {
    "paper_ids": paper_list,
    "max_concurrent": 5
})

# Less efficient: Download one by one
for paper_id in paper_list:
    await call_tool("download_paper", {"paper_id": paper_id})
```

### 2. Smart Converter Selection

```python
# For quick reading: use default pymupdf4llm
await call_tool("download_paper", {
    "paper_id": "2401.12345"
    # Uses pymupdf4llm by default - fast
})

# For detailed analysis: use marker-pdf
await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",
    "output_format": "json"  # For structured extraction
})
```

### 3. Effective Note Organization

```python
# Use consistent tagging system
tags_schema = {
    "status": ["unread", "reading", "read"],
    "relevance": ["high", "medium", "low"],
    "topic": ["methodology", "results", "theory"],
    "action": ["to-implement", "to-cite", "to-review"]
}

# Add structured notes
await call_tool("add_paper_note", {
    "paper_id": paper_id,
    "note": note_content,
    "tags": ["read", "high", "methodology", "to-implement"],
    "section_ref": section
})
```

### 4. Similarity Search Strategy

```python
# Start with content similarity for discovering related work
similar_by_content = await call_tool("find_similar_papers", {
    "paper_id": paper_id,
    "similarity_type": "content",
    "top_k": 10
})

# Then check author networks
similar_by_authors = await call_tool("find_similar_papers", {
    "paper_id": paper_id,
    "similarity_type": "authors",
    "top_k": 5
})

# For comprehensive search use combined
similar_combined = await call_tool("find_similar_papers", {
    "paper_id": paper_id,
    "similarity_type": "combined",
    "min_similarity": 0.3
})
```

### 5. LLM Provider Configuration

```python
# For testing without API keys
result = await call_tool("compare_paper_ideas", {
    "paper_id": paper_id,
    "research_context": context,
    "llm_provider": "mock"  # Returns example data
})

# For production with real analysis
# Set environment variables first:
# export OPENAI_API_KEY=your-key
# or
# export ANTHROPIC_API_KEY=your-key

result = await call_tool("compare_paper_ideas", {
    "paper_id": paper_id,
    "research_context": context,
    "llm_provider": "openai",  # or "anthropic"
    "comparison_type": "comprehensive"
})
```

## Error Handling

All tools include built-in error handling:

```python
# Example: Handling missing papers
result = await call_tool("read_paper", {
    "paper_id": "nonexistent"
})
# Returns: "Error: Paper nonexistent not found. Please download it first."

# Example: Handling batch failures
result = await call_tool("batch_download", {
    "paper_ids": ["valid_id", "invalid_id"],
    "skip_existing": true
})
# Returns summary with failed downloads listed
```

## Next Steps

1. Start with the complete workflow example
2. Customize the tools for your specific research needs
3. Build your own paper management system using these tools
4. Integrate with your preferred LLM provider for advanced analysis

For more details on each tool, see the main README.md file.