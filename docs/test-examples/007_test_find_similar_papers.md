# Task 007: Test find_similar_papers tool

**Test ID**: find_similar_papers_content
**Tool**: find_similar_papers
**Goal**: Verify paper similarity search works correctly

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import json

async def test_find_similar_papers():
    # Ensure we have multiple papers for comparison
    papers_to_download = ["2312.02813", "2401.00001", "2401.00002", "2312.00100"]
    await server.call_tool("batch_download", {
        "paper_ids": papers_to_download,
        "skip_existing": True
    })
    
    # Test 1: Content similarity
    result = await server.call_tool("find_similar_papers", {
        "paper_id": "2312.02813",
        "similarity_type": "content",
        "top_k": 3,
        "min_similarity": 0.1
    })
    
    output = result[0].text
    assert "Similar papers to 2312.02813" in output
    assert "Similarity:" in output
    
    # Test 2: Author similarity
    result = await server.call_tool("find_similar_papers", {
        "paper_id": "2312.02813",
        "similarity_type": "authors",
        "top_k": 5
    })
    
    # Test 3: Combined similarity
    result = await server.call_tool("find_similar_papers", {
        "paper_id": "2312.02813",
        "similarity_type": "combined",
        "min_similarity": 0.2
    })
    
    return result

# Run it:
result = asyncio.run(test_find_similar_papers())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "similarity_type": "content",
    "top_k": 5,
    "min_similarity": 0.3
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_similarity.py::test_content_similarity -v
```

**Expected Output Structure**:
```text
Similar papers to 2312.02813 (content similarity):

• 2401.00001: Quantum Computing in Practice
  Similarity: 0.754
  Authors: Smith, J., Doe, A.

• 2401.00002: Advanced Quantum Algorithms
  Similarity: 0.623
  Authors: Johnson, M.

• 2312.00100: Quantum Error Correction
  Similarity: 0.412
  Authors: Williams, R., Brown, T.
```

## Common Issues & Solutions

### Issue 1: Not enough papers
```python
# Solution: Download more papers first
papers_list = await server.call_tool("list_papers", {})
if len(json.loads(papers_list[0].text)) < 2:
    print("Need at least 2 papers for similarity comparison")
    # Download more papers
    await server.call_tool("batch_download", {
        "search_query": "quantum computing",
        "max_results": 5
    })
```

### Issue 2: Low similarity scores
```python
# Solution: Adjust min_similarity threshold
# TF-IDF can produce low scores for dissimilar papers
if not similar_papers:
    # Lower threshold or remove it
    result = await server.call_tool("find_similar_papers", {
        "paper_id": paper_id,
        "similarity_type": "content",
        "top_k": 10,
        "min_similarity": 0.05  # Very low threshold
    })
```

### Issue 3: Missing metadata
```python
# Solution: Ensure metadata is loaded
import json
from pathlib import Path

# Check if metadata exists
meta_path = Path(f"{STORAGE_PATH}/{paper_id}_metadata.json")
if not meta_path.exists():
    # Extract metadata from paper
    content = await server.call_tool("read_paper", {"paper_id": paper_id})
    # Parse and save metadata
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
assert "Similar papers to" in result[0].text, "Shows target paper"

# Parse similarity results
lines = result[0].text.split('\n')
paper_lines = [l for l in lines if l.startswith('•')]
assert len(paper_lines) > 0, "Found at least one similar paper"

# Verify similarity scores
for line in lines:
    if "Similarity:" in line:
        score = float(line.split(":")[-1].strip())
        assert 0 <= score <= 1, "Valid similarity score"
        assert score >= min_similarity if min_similarity else True
```