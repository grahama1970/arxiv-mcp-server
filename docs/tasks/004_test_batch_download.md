# Task 004: Test batch_download tool

**Test ID**: batch_download_concurrent
**Tool**: batch_download
**Goal**: Verify concurrent paper downloads work correctly

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import time

async def test_batch_download():
    # Test 1: Download specific papers
    start_time = time.time()
    result = await server.call_tool("batch_download", {
        "paper_ids": ["2312.02813", "2401.00001", "2401.00002"],
        "skip_existing": True,
        "max_concurrent": 3,
        "convert_to": "markdown"
    })
    elapsed = time.time() - start_time
    
    # Parse results
    output = result[0].text
    assert "Batch Download Complete:" in output
    assert "Total: 3" in output
    assert elapsed < 30  # Should be faster than sequential
    
    # Test 2: Download from search
    result = await server.call_tool("batch_download", {
        "search_query": "quantum computing",
        "max_results": 5,
        "skip_existing": True,
        "convert_to": "none"  # PDF only
    })
    
    # Test 3: Handle failures gracefully
    result = await server.call_tool("batch_download", {
        "paper_ids": ["2312.02813", "invalid_id", "2401.00001"],
        "skip_existing": False
    })
    assert "Failed: 1" in result[0].text
    assert "Success: 2" in result[0].text
    
    return result

# Run it:
result = asyncio.run(test_batch_download())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_ids": ["2312.02813", "2401.00001", "2401.00002"],
    "max_concurrent": 5,
    "skip_existing": true,
    "convert_to": "markdown"
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_batch_operations.py -v
```

**Expected Output Structure**:
```text
Batch Download Complete:
- Total: 3
- Success: 2
- Skipped: 1
- Failed: 0
```

## Common Issues & Solutions

### Issue 1: Rate limiting
```python
# Solution: Adjust max_concurrent based on system
import os
cpu_count = os.cpu_count() or 2
max_concurrent = min(cpu_count * 2, 8)  # Cap at 8
```

### Issue 2: Memory issues with many papers
```python
# Solution: Process in chunks
def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

for chunk in chunk_list(paper_ids, 10):
    await server.call_tool("batch_download", {
        "paper_ids": chunk
    })
```

### Issue 3: Network timeout
```python
# Solution: Implement retry logic
async def download_with_retry(paper_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await download_paper(paper_id)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
assert "Batch Download Complete:" in result[0].text, "Shows completion summary"
assert re.search(r"Total: \d+", result[0].text), "Shows total count"
assert re.search(r"Success: \d+", result[0].text), "Shows success count"
# Verify files exist
for paper_id in successful_ids:
    assert Path(f"{STORAGE_PATH}/{paper_id}.pdf").exists()
```