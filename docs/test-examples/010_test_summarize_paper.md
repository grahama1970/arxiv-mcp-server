# Task 010: Test summarize_paper tool

**Test ID**: summarize_paper_strategies
**Tool**: summarize_paper
**Goal**: Verify paper summarization with different strategies

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import time

async def test_summarize_paper():
    paper_id = "2312.02813"
    
    # Test 1: Rolling window (default)
    start = time.time()
    result = await server.call_tool("summarize_paper", {
        "paper_id": paper_id,
        "strategy": "rolling_window",
        "chunk_size": 1500,
        "overlap_size": 200,
        "summary_type": "technical",
        "max_summary_length": 1000
    })
    rolling_time = time.time() - start
    
    summary = result[0].text
    assert "Summary of" in summary
    assert len(summary) <= 1500  # Reasonable length
    assert len(summary) > 500   # Substantial content
    
    # Test 2: Map-reduce (faster)
    start = time.time()
    result = await server.call_tool("summarize_paper", {
        "paper_id": paper_id,
        "strategy": "map_reduce",
        "summary_type": "abstract",
        "max_summary_length": 500
    })
    mapreduce_time = time.time() - start
    assert mapreduce_time < rolling_time  # Should be faster
    
    # Test 3: Hierarchical (for very long papers)
    result = await server.call_tool("summarize_paper", {
        "paper_id": paper_id,
        "strategy": "hierarchical",
        "summary_type": "findings",
        "preserve_sections": True
    })
    
    # Test 4: Different summary types
    for summary_type in ["technical", "abstract", "detailed", "findings"]:
        result = await server.call_tool("summarize_paper", {
            "paper_id": paper_id,
            "summary_type": summary_type,
            "max_summary_length": 800
        })
        assert len(result[0].text) > 200
    
    return result

# Run it:
result = asyncio.run(test_summarize_paper())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "strategy": "rolling_window",
    "chunk_size": 2000,
    "overlap_size": 300,
    "summary_type": "technical",
    "max_summary_length": 1200,
    "preserve_sections": true
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_summarize.py::test_rolling_window -v
```

**Expected Output Structure**:
```text
Summary of "Quantum Computing Advances in Error Correction" (2312.02813)

## Abstract Summary
This paper presents groundbreaking advances in quantum error correction...

## Key Contributions
1. Novel error correction algorithm with O(n log n) complexity
2. Experimental validation on 50-qubit system
3. 95% fidelity improvement over previous methods

## Technical Details
The proposed method uses topological codes combined with...

## Results
- Error rates reduced by 85%
- Computational overhead decreased by 40%
- Scalable to 1000+ qubits

## Implications
This work enables practical quantum computing for...

[Summary generated using rolling_window strategy, 1150/1200 max chars]
```

## Common Issues & Solutions

### Issue 1: Summary too short
```python
# Solution: Adjust chunk size and overlap
if len(summary) < min_expected_length:
    # Increase chunk size to capture more context
    result = await server.call_tool("summarize_paper", {
        "paper_id": paper_id,
        "chunk_size": 3000,  # Larger chunks
        "overlap_size": 500,  # More overlap
        "summary_type": "detailed"
    })
```

### Issue 2: Lost context between chunks
```python
# Solution: Use rolling window with proper overlap
def calculate_overlap(chunk_size):
    # 15-20% overlap is usually good
    return int(chunk_size * 0.15)

overlap = calculate_overlap(chunk_size)
```

### Issue 3: Timeout on long papers
```python
# Solution: Use map_reduce for speed
async def summarize_with_timeout(paper_id, timeout=30):
    try:
        return await asyncio.wait_for(
            server.call_tool("summarize_paper", {
                "paper_id": paper_id,
                "strategy": "map_reduce"  # Faster
            }),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        # Fallback to smaller chunks
        return await server.call_tool("summarize_paper", {
            "paper_id": paper_id,
            "chunk_size": 1000,  # Smaller
            "strategy": "map_reduce"
        })
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
summary = result[0].text

# Basic checks
assert len(summary) > 200, "Summary has substantial content"
assert len(summary) <= max_summary_length + 200, "Respects length limit"

# Content checks
assert "Summary of" in summary or paper_id in summary, "References the paper"

# Strategy-specific checks
if strategy == "rolling_window":
    assert "[Summary generated using rolling_window strategy" in summary

if preserve_sections:
    # Should have section markers
    assert "##" in summary or "**" in summary, "Preserves structure"

# Summary type checks
if summary_type == "technical":
    # Should include technical details
    technical_terms = ["algorithm", "method", "approach", "technique"]
    assert any(term in summary.lower() for term in technical_terms)
```