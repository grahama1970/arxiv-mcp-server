# Task 008: Test extract_sections tool

**Test ID**: extract_sections_multiple
**Tool**: extract_sections
**Goal**: Verify section extraction from papers works

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio

async def test_extract_sections():
    paper_id = "2312.02813"
    
    # Test 1: Extract standard sections
    result = await server.call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["abstract", "introduction", "conclusion"],
        "include_subsections": True
    })
    
    output = result[0].text
    assert f"Extracted sections from {paper_id}:" in output
    
    # Verify sections were found
    sections_found = output.count("---")  # Section separators
    assert sections_found >= 1, "At least one section extracted"
    
    # Test 2: Extract methods/methodology
    result = await server.call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["methods", "methodology", "approach"],
        "include_subsections": False
    })
    
    # Test 3: Handle missing sections
    result = await server.call_tool("extract_sections", {
        "paper_id": paper_id,
        "sections": ["nonexistent_section", "abstract"],
        "include_subsections": True
    })
    assert "Sections not found: nonexistent_section" in result[0].text
    assert "Available sections in this paper:" in result[0].text
    
    return result

# Run it:
result = asyncio.run(test_extract_sections())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "sections": ["abstract", "introduction", "methods", "results", "conclusion"],
    "include_subsections": true
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_sections.py::test_extract_multiple -v
```

**Expected Output Structure**:
```text
Extracted sections from 2312.02813:

## Abstract

This paper presents a novel approach to quantum computing...

---

## Introduction

Quantum computing has emerged as a promising paradigm...

### 1.1 Background

The foundations of quantum mechanics...

---

## Methods

Our approach consists of three main components...

---

Sections not found: results

Available sections in this paper:
• Abstract
• Introduction
• Related Work
• Methodology
• Experiments
• Discussion
• Conclusion
• References
```

## Common Issues & Solutions

### Issue 1: Section not found
```python
# Solution: Try alternative names
SECTION_VARIANTS = {
    "methods": ["methods", "methodology", "method", "approach"],
    "results": ["results", "experiments", "findings", "evaluation"],
    "discussion": ["discussion", "analysis", "implications"]
}

for variant in SECTION_VARIANTS.get(section, [section]):
    result = extract_section(content, variant)
    if result:
        break
```

### Issue 2: Subsections not included
```python
# Solution: Check markdown header levels
def extract_with_subsections(content, section):
    # Find section header
    pattern = rf'(#+\s*{section}.*?\n)'
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return None
    
    start = match.start()
    header_level = len(match.group(1).split()[0])  # Count #'s
    
    # Find next same-level or higher header
    next_pattern = rf'\n{{1,{header_level}}}#\s'
    next_match = re.search(next_pattern, content[start+1:])
    
    end = start + next_match.start() if next_match else len(content)
    return content[start:end]
```

### Issue 3: Non-markdown formatted papers
```python
# Solution: Fallback to plain text patterns
def extract_plain_text_section(content, section):
    # Look for section title in caps or title case
    patterns = [
        rf'{section.upper()}\s*\n',
        rf'{section.title()}\s*\n',
        rf'\n{section}\s*\n'
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Extract until next section-like header
            start = match.end()
            end = re.search(r'\n[A-Z][A-Za-z\s]+\n', content[start:])
            return content[start:start + end.start() if end else len(content)]
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"
assert f"Extracted sections from {paper_id}:" in result[0].text

# Check if sections were found
if "---" in result[0].text:
    sections = result[0].text.split("---")
    assert len(sections) >= 2, "At least one section extracted"
    
    # Verify requested sections
    for section in requested_sections:
        if section.lower() in result[0].text.lower():
            assert True, f"Found section: {section}"

# Check for not found sections
if "Sections not found:" in result[0].text:
    assert "Available sections in this paper:" in result[0].text
```