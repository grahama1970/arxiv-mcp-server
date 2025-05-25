"""Comprehensive research guide prompt for using all ArXiv MCP server features."""

COMPREHENSIVE_RESEARCH_GUIDE = """
# ArXiv MCP Server - Comprehensive Research Assistant Guide

You have access to a powerful ArXiv research server with 15 specialized tools. This guide will help you use them effectively for any research task.

## Available Tools Overview

### Core Tools (Basic Operations)
1. **search_papers** - Search ArXiv with filters (date, category, query)
2. **download_paper** - Download and convert papers (PDF → Markdown/JSON)
3. **list_papers** - View all downloaded papers
4. **read_paper** - Read paper content

### Analysis Tools
5. **summarize_paper** - Create intelligent summaries with multiple strategies
6. **analyze_paper_code** - Extract and analyze code blocks
7. **describe_paper_content** - Use LLMs to describe tables/images
8. **extract_sections** - Extract specific sections (abstract, methods, etc.)

### Research Tools
9. **extract_citations** - Get references in BibTeX/JSON/EndNote
10. **find_similar_papers** - Find related papers by content/authors
11. **compare_paper_ideas** - AI comparison with your research

### Productivity Tools
12. **batch_download** - Download multiple papers efficiently
13. **add_paper_note** - Add tagged annotations
14. **list_paper_notes** - Search and retrieve notes
15. **get_conversion_options** - Check available converters

## Recommended Workflows

### 1. Initial Research Exploration
When starting research on a new topic:

```python
# Step 1: Broad search to understand the landscape
papers = await search_papers({
    "query": "your topic keywords",
    "max_results": 50,
    "date_from": "2020-01-01"
})

# Step 2: Batch download the most relevant papers
paper_ids = [p["id"] for p in papers[:20]]  # Top 20
await batch_download({
    "paper_ids": paper_ids,
    "convert_to": "markdown",
    "skip_existing": true
})

# Step 3: Generate summaries for quick overview
for paper_id in paper_ids[:5]:  # Start with top 5
    summary = await summarize_paper({
        "paper_id": paper_id,
        "strategy": "rolling_window",
        "summary_type": "abstract",
        "max_summary_length": 500
    })
```

### 2. Deep Paper Analysis
When you need to thoroughly understand a paper:

```python
# Step 1: Download with high-quality conversion
await download_paper({
    "paper_id": "2401.12345",
    "converter": "marker-pdf",  # Better accuracy
    "output_format": "json"  # For structured data
})

# Step 2: Extract key sections
sections = await extract_sections({
    "paper_id": "2401.12345",
    "sections": ["abstract", "introduction", "methods", "results", "conclusion"],
    "include_subsections": true
})

# Step 3: Analyze any code
code = await analyze_paper_code({
    "paper_id": "2401.12345",
    "extract_functions": true,
    "extract_classes": true
})

# Step 4: Extract citations for follow-up
citations = await extract_citations({
    "paper_id": "2401.12345",
    "format": "bibtex"
})

# Step 5: Add your analysis notes
await add_paper_note({
    "paper_id": "2401.12345",
    "note": "Your detailed analysis here",
    "tags": ["analyzed", "important", "methodology"],
    "section_ref": "Relevant section"
})
```

### 3. Comparative Research
When comparing papers or evaluating against your work:

```python
# Step 1: Find similar papers
similar = await find_similar_papers({
    "paper_id": "2401.12345",
    "similarity_type": "combined",
    "top_k": 10
})

# Step 2: Download the similar papers
similar_ids = [p["id"] for p in similar]
await batch_download({
    "paper_ids": similar_ids,
    "skip_existing": true
})

# Step 3: Compare each against your research
for paper_id in similar_ids:
    comparison = await compare_paper_ideas({
        "paper_id": paper_id,
        "research_context": "Describe your approach/system here",
        "comparison_type": "comprehensive",
        "focus_areas": ["efficiency", "accuracy", "scalability"],
        "llm_provider": "mock"  # or "openai"/"anthropic" with API key
    })
```

### 4. Literature Review
When conducting a systematic literature review:

```python
# Step 1: Comprehensive search with categories
papers = await search_papers({
    "query": "your review topic",
    "max_results": 200,
    "date_from": "2018-01-01",
    "categories": ["cs.LG", "cs.AI", "stat.ML"]
})

# Step 2: Batch download all papers
all_ids = [p["id"] for p in papers]
await batch_download({
    "paper_ids": all_ids,
    "max_concurrent": 5,  # Control resource usage
    "skip_existing": true
})

# Step 3: Extract abstracts for initial screening
for paper_id in all_ids:
    abstract = await extract_sections({
        "paper_id": paper_id,
        "sections": ["abstract"]
    })
    
    # Add screening note
    await add_paper_note({
        "paper_id": paper_id,
        "note": "Include/Exclude: reason",
        "tags": ["screening", "included/excluded"]
    })

# Step 4: For included papers, extract citations
included_papers = await list_paper_notes({
    "tags": ["included"]
})

for paper in included_papers:
    citations = await extract_citations({
        "paper_id": paper["paper_id"],
        "format": "bibtex"
    })
```

### 5. Daily Research Routine
For staying updated with new research:

```python
# Morning: Check new papers
today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

new_papers = await search_papers({
    "query": "your research keywords",
    "max_results": 20,
    "date_from": yesterday
})

# Quick download and review
if new_papers:
    await batch_download({
        "paper_ids": [p["id"] for p in new_papers[:5]],
        "skip_existing": true
    })
    
    for paper in new_papers[:5]:
        # Quick summary
        summary = await summarize_paper({
            "paper_id": paper["id"],
            "strategy": "map_reduce",
            "summary_type": "abstract",
            "max_summary_length": 200
        })
        
        # Tag for later
        await add_paper_note({
            "paper_id": paper["id"],
            "note": f"New paper {today}: {summary}",
            "tags": ["new", "unread", today]
        })
```

## Best Practices

### 1. Efficient Processing
- Use `batch_download` for multiple papers instead of individual downloads
- Set `skip_existing=true` to avoid re-downloading
- Use `max_concurrent` to control resource usage

### 2. Smart Search Strategies
- Start broad, then narrow with categories and date ranges
- Use the search results to find paper IDs for other operations
- Combine search with similarity finding for comprehensive coverage

### 3. Organized Note-Taking
- Use consistent tags: ["status", "relevance", "topic", "date"]
- Reference specific sections in notes
- Search notes regularly to avoid duplicate work

### 4. Converter Selection
- Default (pymupdf4llm): Fast, good for most papers
- marker-pdf: Slow but accurate, use for complex papers or when you need JSON

### 5. Comparison Strategies
- Start with "mock" LLM provider for testing
- Use specific focus_areas for targeted comparison
- Compare multiple papers to identify patterns

## Common Patterns

### Pattern 1: Paper Discovery Pipeline
```
search → batch_download → summarize → find_similar → repeat
```

### Pattern 2: Deep Analysis Pipeline
```
download(marker-pdf) → extract_sections → analyze_code → extract_citations → add_notes
```

### Pattern 3: Comparison Pipeline
```
download → summarize → compare_paper_ideas → add_notes → find_similar
```

### Pattern 4: Citation Network Building
```
download → extract_citations → search cited papers → download citations → repeat
```

## Tool Selection Guide

Ask yourself:
1. **What's my goal?**
   - Overview → use `summarize_paper`
   - Deep dive → use `extract_sections` + `analyze_code`
   - Comparison → use `compare_paper_ideas`
   
2. **How many papers?**
   - Single paper → use individual tools
   - Multiple papers → use `batch_download`
   
3. **What output do I need?**
   - Reading → use default Markdown
   - Data extraction → use marker-pdf with JSON
   - Citations → use `extract_citations`

Remember: All tools work with paper_id, so always start by searching or listing available papers!
"""

def get_comprehensive_guide():
    """Return the comprehensive research guide."""
    return COMPREHENSIVE_RESEARCH_GUIDE