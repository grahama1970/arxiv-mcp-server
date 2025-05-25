# Task 009: Test add_paper_note and list_paper_notes tools

**Test ID**: paper_notes_crud
**Tool**: add_paper_note, list_paper_notes
**Goal**: Verify paper annotation system works

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import json
from datetime import datetime

async def test_paper_notes():
    paper_id = "2312.02813"
    
    # Test 1: Add a simple note
    result = await server.call_tool("add_paper_note", {
        "paper_id": paper_id,
        "note": "This paper introduces a novel quantum algorithm with O(n log n) complexity",
        "tags": ["quantum", "algorithm", "complexity"]
    })
    
    assert "Note added to" in result[0].text
    assert "ID: 1" in result[0].text
    
    # Test 2: Add note with section reference
    result = await server.call_tool("add_paper_note", {
        "paper_id": paper_id,
        "note": "The experimental setup in section 3.2 could be improved with better isolation",
        "tags": ["experimental", "improvement", "methodology"],
        "section_ref": "Section 3.2 - Experimental Setup"
    })
    
    # Test 3: List notes for specific paper
    result = await server.call_tool("list_paper_notes", {
        "paper_id": paper_id
    })
    
    output = result[0].text
    assert "Found 2 notes:" in output
    assert "quantum algorithm" in output
    assert "experimental setup" in output
    
    # Test 4: Search notes by tags
    result = await server.call_tool("list_paper_notes", {
        "tags": ["quantum"]
    })
    assert "quantum algorithm" in result[0].text
    
    # Test 5: Search notes by text
    result = await server.call_tool("list_paper_notes", {
        "search_text": "complexity"
    })
    assert "O(n log n)" in result[0].text
    
    # Test 6: Cross-paper search
    # Add note to another paper
    await server.call_tool("add_paper_note", {
        "paper_id": "2401.00001",
        "note": "Related to quantum research in 2312.02813",
        "tags": ["quantum", "cross-reference"]
    })
    
    # Search across all papers
    result = await server.call_tool("list_paper_notes", {
        "tags": ["quantum"]
    })
    assert "2312.02813" in result[0].text
    assert "2401.00001" in result[0].text
    
    return result

# Run it:
result = asyncio.run(test_paper_notes())
print(result[0].text)
```

## Test Details

**Input Parameters (add_paper_note)**:
```json
{
    "paper_id": "2312.02813",
    "note": "Important finding: The proposed method achieves 95% accuracy",
    "tags": ["important", "accuracy", "results"],
    "section_ref": "Section 4.3 - Results"
}
```

**Input Parameters (list_paper_notes)**:
```json
{
    "paper_id": "2312.02813",
    "tags": ["important"],
    "search_text": "accuracy"
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_annotations.py -v
```

**Expected Output Structure (add_paper_note)**:
```text
Note added to 2312.02813:
ID: 1
Timestamp: 2024-01-15T10:30:45.123456
Note: Important finding: The proposed method achieves 95% accuracy
Tags: important, accuracy, results
Section: Section 4.3 - Results
```

**Expected Output Structure (list_paper_notes)**:
```text
Found 3 notes:

Paper: 2312.02813
Note ID: 1
Time: 2024-01-15T10:30:45.123456
Note: Important finding: The proposed method achieves 95% accuracy
Tags: important, accuracy, results
Section: Section 4.3 - Results
----------------------------------------
Paper: 2312.02813
Note ID: 2
Time: 2024-01-15T10:35:12.456789
Note: Consider implementing this approach
Tags: todo, implementation
----------------------------------------
```

## Common Issues & Solutions

### Issue 1: Paper not found
```python
# Solution: Ensure paper is downloaded first
try:
    await server.call_tool("add_paper_note", {"paper_id": paper_id, "note": "test"})
except:
    # Download paper first
    await server.call_tool("download_paper", {"paper_id": paper_id})
    # Retry
```

### Issue 2: Duplicate tags
```python
# Solution: Use set to avoid duplicates
def add_tags(existing_tags, new_tags):
    return list(set(existing_tags + new_tags))
```

### Issue 3: Large number of notes
```python
# Solution: Implement pagination
async def list_notes_paginated(page=1, per_page=10):
    all_notes = await get_all_notes()
    start = (page - 1) * per_page
    end = start + per_page
    return all_notes[start:end]
```

## Validation Requirements

```python
# This test passes when:

# For add_paper_note:
assert result[0].type == "text", "Returns text content"
assert f"Note added to {paper_id}" in result[0].text
assert "ID:" in result[0].text
assert "Timestamp:" in result[0].text

# For list_paper_notes:
assert result[0].type == "text", "Returns text content"
if "Found 0 notes" not in result[0].text:
    assert "Paper:" in result[0].text
    assert "Note ID:" in result[0].text
    assert "Time:" in result[0].text
    assert "Note:" in result[0].text
    
# Verify persistence
annotations_dir = Path(f"{STORAGE_PATH}/annotations")
assert annotations_dir.exists(), "Annotations directory created"
assert len(list(annotations_dir.glob("*_annotations.json"))) > 0
```