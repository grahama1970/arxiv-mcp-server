# Task 005: Test extract_citations tool

**Test ID**: extract_citations_formats
**Tool**: extract_citations
**Goal**: Verify citation extraction in multiple formats

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import json

async def test_extract_citations():
    paper_id = "2312.02813"  # Must be downloaded first
    
    # Test 1: BibTeX format (default)
    result = await server.call_tool("extract_citations", {
        "paper_id": paper_id
    })
    bibtex = result[0].text
    assert "@article{" in bibtex
    assert "author =" in bibtex
    assert "title =" in bibtex
    
    # Test 2: JSON format
    result = await server.call_tool("extract_citations", {
        "paper_id": paper_id,
        "format": "json",
        "include_arxiv_links": True
    })
    citations = json.loads(result[0].text)
    assert isinstance(citations, list)
    assert all("raw_text" in c for c in citations)
    assert any(c.get("arxiv_id") for c in citations)
    
    # Test 3: EndNote format
    result = await server.call_tool("extract_citations", {
        "paper_id": paper_id,
        "format": "endnote"
    })
    endnote = result[0].text
    assert "%0 Journal Article" in endnote
    assert "%A " in endnote  # Author tag
    
    return citations

# Run it:
citations = asyncio.run(test_extract_citations())
print(f"Extracted {len(citations)} citations")
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "format": "bibtex",
    "include_arxiv_links": true
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_citations.py::test_extract_bibtex -v
```

**Expected Output Structure (BibTeX)**:
```bibtex
@article{Smith2023_1,
  author = "Smith, J. and Doe, A.",
  title = "{Quantum Computing Advances}",
  year = {2023},
  eprint = "2301.12345",
  archivePrefix = "arXiv",
  url = "https://arxiv.org/abs/2301.12345"
}
```

**Expected Output Structure (JSON)**:
```json
[
    {
        "index": 1,
        "raw_text": "Smith, J. and Doe, A. (2023). Quantum Computing...",
        "authors": ["Smith, J.", "Doe, A."],
        "title": "Quantum Computing Advances",
        "year": 2023,
        "arxiv_id": "2301.12345",
        "doi": "10.1234/example"
    }
]
```

## Common Issues & Solutions

### Issue 1: No citations found
```python
# Solution: Check if paper has References section
content = await server.call_tool("read_paper", {"paper_id": paper_id})
if "references" not in content[0].text.lower():
    print("Warning: Paper may not have a standard References section")
# Try alternative patterns
patterns = ["bibliography", "works cited", "literature cited"]
```

### Issue 2: Malformed BibTeX
```python
# Solution: Validate BibTeX syntax
import bibtexparser
try:
    bib_db = bibtexparser.loads(bibtex_output)
    assert len(bib_db.entries) > 0
except Exception as e:
    print(f"Invalid BibTeX: {e}")
```

### Issue 3: Missing ArXiv IDs
```python
# Solution: Use regex fallback for different formats
arxiv_patterns = [
    r'arXiv:(\d{4}\.\d{4,5})',
    r'arxiv\.org/abs/(\d{4}\.\d{4,5})',
    r'ArXiv:(\d{4}\.\d{4,5})'
]
for pattern in arxiv_patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        arxiv_id = match.group(1)
        break
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"

# For BibTeX format:
if format == "bibtex":
    assert "@article{" in result[0].text, "Contains BibTeX entries"
    assert result[0].text.count("@article{") > 0, "Has at least one citation"

# For JSON format:
elif format == "json":
    citations = json.loads(result[0].text)
    assert isinstance(citations, list), "Returns list of citations"
    assert len(citations) > 0, "Found at least one citation"

# For EndNote format:
elif format == "endnote":
    assert "%0 Journal Article" in result[0].text, "Contains EndNote entries"
```