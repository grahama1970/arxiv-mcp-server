# Task 003: Test download_paper tool

**Test ID**: download_paper_converters
**Tool**: download_paper
**Goal**: Verify paper download with different converters

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import os
from pathlib import Path

async def test_download_paper():
    paper_id = "2312.02813"  # Known paper ID
    
    # Test 1: Default download (pymupdf4llm)
    result = await server.call_tool("download_paper", {
        "paper_id": paper_id
    })
    assert "Downloaded successfully" in result[0].text
    assert Path(f"{STORAGE_PATH}/{paper_id}.pdf").exists()
    assert Path(f"{STORAGE_PATH}/{paper_id}.md").exists()
    
    # Test 2: Download with marker-pdf
    result = await server.call_tool("download_paper", {
        "paper_id": "2401.00001",
        "converter": "marker-pdf",
        "output_format": "json"
    })
    assert Path(f"{STORAGE_PATH}/2401.00001.json").exists()
    
    # Test 3: Skip conversion
    result = await server.call_tool("download_paper", {
        "paper_id": "2401.00002",
        "converter": None
    })
    assert Path(f"{STORAGE_PATH}/2401.00002.pdf").exists()
    assert not Path(f"{STORAGE_PATH}/2401.00002.md").exists()
    
    return result

# Run it:
result = asyncio.run(test_download_paper())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "converter": "marker-pdf",
    "output_format": "json"
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_download.py::test_download_with_conversion -v
```

**Expected Output Structure**:
```text
"Downloaded paper 2312.02813 successfully to /path/to/storage/2312.02813.pdf
Converted to JSON format at /path/to/storage/2312.02813.json"
```

## Common Issues & Solutions

### Issue 1: Invalid paper ID
```python
# Solution: Validate ArXiv ID format
import re
ARXIV_ID_PATTERN = r'^\d{4}\.\d{4,5}$'
if not re.match(ARXIV_ID_PATTERN, paper_id):
    raise ValueError(f"Invalid ArXiv ID format: {paper_id}")
```

### Issue 2: Converter not found
```python
# Solution: Check available converters first
converters = await server.call_tool("get_conversion_options", {})
available = json.loads(converters[0].text)
assert converter in available["converters"]
```

### Issue 3: Disk space error
```python
# Solution: Check available space before download
import shutil
stats = shutil.disk_usage(STORAGE_PATH)
if stats.free < 100 * 1024 * 1024:  # 100MB minimum
    raise IOError("Insufficient disk space")
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
assert "successfully" in result[0].text.lower(), "Reports success"
assert Path(f"{STORAGE_PATH}/{paper_id}.pdf").exists(), "PDF saved"
if converter:
    ext = "json" if output_format == "json" else "md"
    assert Path(f"{STORAGE_PATH}/{paper_id}.{ext}").exists(), f"Converted file exists"
```