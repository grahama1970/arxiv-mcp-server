# Task 006: Test compare_paper_ideas tool

**Test ID**: compare_paper_ideas_mock
**Tool**: compare_paper_ideas
**Goal**: Verify AI-powered paper comparison works

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import json

async def test_compare_paper_ideas():
    paper_id = "2312.02813"
    
    # Test 1: Mock provider (no API key needed)
    result = await server.call_tool("compare_paper_ideas", {
        "paper_id": paper_id,
        "research_context": "My Natrium system pairs a 345-MW sodium-cooled fast reactor with a molten salt thermal battery",
        "comparison_type": "comprehensive",
        "llm_provider": "mock"
    })
    
    output = result[0].text
    assert "BETTER IDEAS IN PAPER:" in output
    assert "WORSE IDEAS/LIMITATIONS:" in output
    assert "CONTRADICTIONS:" in output
    assert "UNIQUE INSIGHTS:" in output
    assert "RECOMMENDATIONS:" in output
    
    # Test 2: With focus areas
    result = await server.call_tool("compare_paper_ideas", {
        "paper_id": paper_id,
        "research_context": "My quantum algorithm uses variational methods",
        "comparison_type": "technical",
        "focus_areas": ["efficiency", "scalability", "accuracy"],
        "llm_provider": "mock"
    })
    
    # Test 3: Real LLM provider (requires API key)
    if os.getenv("OPENAI_API_KEY"):
        result = await server.call_tool("compare_paper_ideas", {
            "paper_id": paper_id,
            "research_context": "My approach to transformer optimization",
            "llm_provider": "openai"
        })
        assert "Error:" not in result[0].text
    
    return result

# Run it:
result = asyncio.run(test_compare_paper_ideas())
print(result[0].text)
```

## Test Details

**Input Parameters**:
```json
{
    "paper_id": "2312.02813",
    "research_context": "My system uses advanced heat recovery with 95% efficiency",
    "comparison_type": "comprehensive",
    "focus_areas": ["efficiency", "cost", "scalability"],
    "llm_provider": "mock"
}
```

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_comparative_analysis.py -v
```

**Expected Output Structure**:
```text
Comparative Analysis: 2312.02813
Research Context: My system uses advanced heat recovery...
Comparison Type: comprehensive

BETTER IDEAS IN PAPER:
• The paper proposes a modular design approach...
• Their heat recovery system achieves 15% higher efficiency...

WORSE IDEAS/LIMITATIONS:
• The paper's cooling system requires 3x more maintenance...
• Their control strategy has longer response times...

CONTRADICTIONS:
• Paper claims sodium systems can't exceed 40% efficiency...
• They state thermal storage is impractical above 500°C...

UNIQUE INSIGHTS:
• Novel use of phase-change materials...
• Their economic analysis framework...

RECOMMENDATIONS:
• Consider integrating their heat exchanger design...
• Their safety protocols for sodium handling...

Confidence Score: 0.85
```

## Common Issues & Solutions

### Issue 1: Missing API key
```python
# Solution: Use mock provider or set environment variable
if llm_provider != "mock" and not os.getenv(f"{llm_provider.upper()}_API_KEY"):
    print(f"Warning: {llm_provider} requires API key. Using mock provider.")
    llm_provider = "mock"
```

### Issue 2: Paper too long for context
```python
# Solution: Truncate paper content intelligently
def truncate_for_llm(content, max_tokens=3000):
    # Prioritize abstract, introduction, and conclusion
    sections = extract_sections(content, ["abstract", "introduction", "conclusion"])
    return "\n\n".join(sections)[:max_tokens]
```

### Issue 3: Invalid comparison type
```python
# Solution: Validate comparison type
VALID_COMPARISON_TYPES = ["comprehensive", "technical", "approach", "results"]
if comparison_type not in VALID_COMPARISON_TYPES:
    comparison_type = "comprehensive"  # Default
```

## Validation Requirements

```python
# This test passes when:
assert result[0].type == "text", "Returns text content"

# For mock provider:
if llm_provider == "mock":
    assert "better_ideas" in result[0].text or "BETTER IDEAS" in result[0].text
    assert "worse_ideas" in result[0].text or "WORSE IDEAS" in result[0].text
    assert "Confidence Score:" in result[0].text

# For real providers:
else:
    assert "Error:" not in result[0].text, "No API errors"
    assert len(result[0].text) > 500, "Substantial analysis provided"
```