# ArXiv MCP Server - Quick Reference

## All 15 Tools at a Glance

### 🔍 Search & Discovery
```python
# 1. Search papers
await call_tool("search_papers", {
    "query": "keywords",
    "max_results": 10,
    "date_from": "2023-01-01",
    "categories": ["cs.AI"]
})

# 2. Find similar papers
await call_tool("find_similar_papers", {
    "paper_id": "2401.12345",
    "similarity_type": "content",  # or "authors", "combined"
    "top_k": 5
})
```

### 📥 Download & Access
```python
# 3. Download single paper
await call_tool("download_paper", {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",  # or "pymupdf4llm" (default)
    "output_format": "json"  # or "markdown"
})

# 4. Batch download
await call_tool("batch_download", {
    "paper_ids": ["id1", "id2", "id3"],
    # OR: "search_query": "query",
    "skip_existing": true,
    "max_concurrent": 5
})

# 5. List downloaded papers
await call_tool("list_papers", {})

# 6. Read paper content
await call_tool("read_paper", {
    "paper_id": "2401.12345"
})
```

### 📊 Analysis & Extraction
```python
# 7. Summarize paper
await call_tool("summarize_paper", {
    "paper_id": "2401.12345",
    "strategy": "rolling_window",  # or "map_reduce", "hierarchical"
    "summary_type": "technical",  # or "abstract", "detailed", "findings"
    "max_summary_length": 1000
})

# 8. Extract sections
await call_tool("extract_sections", {
    "paper_id": "2401.12345",
    "sections": ["abstract", "methods", "results"],
    "include_subsections": true
})

# 9. Extract citations
await call_tool("extract_citations", {
    "paper_id": "2401.12345",
    "format": "bibtex",  # or "json", "endnote"
    "include_arxiv_links": true
})

# 10. Analyze code
await call_tool("analyze_paper_code", {
    "paper_id": "2401.12345",
    "languages": ["python"],
    "extract_functions": true,
    "extract_classes": true
})

# 11. Describe content (tables/images)
await call_tool("describe_paper_content", {
    "paper_id": "2401.12345",
    "content_type": "both",  # or "table", "image"
    "llm_model": "gpt-4-vision-preview"
})
```

### 🤖 AI-Powered Features
```python
# 12. Compare with your research
await call_tool("compare_paper_ideas", {
    "paper_id": "2401.12345",
    "research_context": "my approach uses...",
    "comparison_type": "comprehensive",  # or "technical", "approach", "results"
    "focus_areas": ["efficiency", "accuracy"],
    "llm_provider": "mock"  # or "openai", "anthropic", "perplexity"
})
```

### 📝 Notes & Organization
```python
# 13. Add note
await call_tool("add_paper_note", {
    "paper_id": "2401.12345",
    "note": "Important finding...",
    "tags": ["important", "methodology"],
    "section_ref": "Section 3.2"
})

# 14. List/search notes
await call_tool("list_paper_notes", {
    "paper_id": "2401.12345",  # optional
    "tags": ["important"],  # optional
    "search_text": "finding"  # optional
})
```

### ℹ️ System Info
```python
# 15. Get system stats
await call_tool("get_system_stats", {})

# Bonus: Check conversion options
await call_tool("get_conversion_options", {})
```

## 🎯 Common Workflows

### Literature Review
```python
# 1. Search → 2. Batch download → 3. Extract abstracts → 4. Add notes → 5. Extract citations
```

### Paper Deep Dive
```python
# 1. Download (marker-pdf) → 2. Extract sections → 3. Analyze code → 4. Summarize → 5. Compare
```

### Daily Research
```python
# 1. Search (recent) → 2. Batch download → 3. Quick summaries → 4. Tag interesting papers
```

### Building Citation Network
```python
# 1. Extract citations → 2. Search cited papers → 3. Find similar → 4. Download → 5. Repeat
```

## 💡 Pro Tips

1. **Batch operations** are faster than individual calls
2. **Skip_existing=true** saves time and bandwidth
3. **Mock LLM provider** works without API keys
4. **Marker-pdf** is slower but more accurate
5. **Tags** help organize large paper collections
6. **Combined similarity** finds the best matches

## 📚 Get Full Guide

```python
# For detailed examples and workflows:
await call_prompt("comprehensive-research-guide", {})
```