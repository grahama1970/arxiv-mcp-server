# Task 002: Test search_papers tool

**Test ID**: search_papers_basic
**Tool**: search_papers
**Goal**: Verify paper search with filters works correctly

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
from arxiv_mcp_server import server

async def test_search_papers():
    # Basic search
    result = await server.call_tool("search_papers", {
        "query": "quantum computing",
        "max_results": 5
    })
    assert len(result) == 1
    assert result[0].type == "text"
    papers = json.loads(result[0].text)
    assert len(papers) <= 5
    
    # Search with date filter
    result = await server.call_tool("search_papers", {
        "query": "transformer architecture",
        "max_results": 10,
        "date_from": "2023-01-01",
        "date_to": "2024-01-01"
    })
    
    # Search with categories
    result = await server.call_tool("search_papers", {
        "query": "machine learning",
        "categories": ["cs.LG", "cs.AI"],
        "max_results": 20
    })
    
    return result

# Run it:
result = asyncio.run(test_search_papers())
print(f"Found {len(json.loads(result[0].text))} papers")
```

## Test Details

**Input Parameters**:
```json
{
    "query": "quantum computing",
    "max_results": 5,
    "date_from": "2023-01-01",
    "categories": ["quant-ph", "cs.CR"]
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_search.py -v
```

**Expected Output Structure**:
```json
[
    {
        "id": "2401.12345",
        "title": "Quantum Computing Advances...",
        "authors": ["Author One", "Author Two"],
        "summary": "Abstract text...",
        "published": "2024-01-15",
        "updated": "2024-01-16",
        "categories": ["quant-ph"],
        "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf"
    }
]
```

## Common Issues & Solutions

### Issue 1: Empty results
```python
# Solution: Check query spelling and date format
# Date must be YYYY-MM-DD format
assert "date_from" not in args or re.match(r'\d{4}-\d{2}-\d{2}', args["date_from"])
```

### Issue 2: Category not found
```python
# Solution: Use valid arXiv categories
VALID_CATEGORIES = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "math.CO", "physics.app-ph"]
if "categories" in args:
    assert all(cat in VALID_CATEGORIES for cat in args["categories"])
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
papers = json.loads(result[0].text)
assert isinstance(papers, list), "Returns list of papers"
assert all("id" in p for p in papers), "Each paper has ID"
assert all("title" in p for p in papers), "Each paper has title"
assert len(papers) <= args.get("max_results", 10), "Respects max_results"
```