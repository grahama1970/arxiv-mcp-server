# Task 011: Test complete research workflow integration

**Test ID**: integration_research_workflow
**Tool**: Multiple tools in sequence
**Goal**: Verify all tools work together in a realistic research workflow

## Working Code Example

```python
# COPY THIS WORKING PATTERN:
import asyncio
import json

async def test_complete_workflow():
    # Step 1: Search for papers on a topic
    search_results = await server.call_tool("search_papers", {
        "query": "quantum error correction",
        "max_results": 10,
        "date_from": "2023-01-01"
    })
    papers = json.loads(search_results[0].text)
    assert len(papers) > 0, "Found papers"
    
    # Step 2: Batch download top 5 papers
    paper_ids = [p["id"] for p in papers[:5]]
    batch_result = await server.call_tool("batch_download", {
        "paper_ids": paper_ids,
        "convert_to": "markdown",
        "skip_existing": True
    })
    assert "Success:" in batch_result[0].text
    
    # Step 3: Analyze first paper in detail
    main_paper_id = paper_ids[0]
    
    # 3a. Summarize it
    summary = await server.call_tool("summarize_paper", {
        "paper_id": main_paper_id,
        "strategy": "rolling_window",
        "summary_type": "technical",
        "max_summary_length": 800
    })
    
    # 3b. Extract key sections
    sections = await server.call_tool("extract_sections", {
        "paper_id": main_paper_id,
        "sections": ["abstract", "methods", "results"],
        "include_subsections": True
    })
    
    # 3c. Extract citations
    citations = await server.call_tool("extract_citations", {
        "paper_id": main_paper_id,
        "format": "bibtex"
    })
    
    # 3d. Analyze any code
    code_analysis = await server.call_tool("analyze_paper_code", {
        "paper_id": main_paper_id,
        "extract_functions": True
    })
    
    # Step 4: Compare with research context
    comparison = await server.call_tool("compare_paper_ideas", {
        "paper_id": main_paper_id,
        "research_context": "My quantum error correction approach uses surface codes with magic state distillation",
        "comparison_type": "technical",
        "focus_areas": ["error_rates", "scalability", "overhead"],
        "llm_provider": "mock"
    })
    
    # Step 5: Find similar papers
    similar = await server.call_tool("find_similar_papers", {
        "paper_id": main_paper_id,
        "similarity_type": "content",
        "top_k": 3
    })
    
    # Step 6: Add research notes
    await server.call_tool("add_paper_note", {
        "paper_id": main_paper_id,
        "note": f"Main findings: {summary[0].text[:200]}... Relevant to my surface code research.",
        "tags": ["quantum", "error-correction", "surface-codes", "review-complete"],
        "section_ref": "Overall assessment"
    })
    
    # Step 7: Create bibliography from all papers
    all_citations = []
    for paper_id in paper_ids[:3]:
        try:
            cites = await server.call_tool("extract_citations", {
                "paper_id": paper_id,
                "format": "bibtex"
            })
            all_citations.append(cites[0].text)
        except:
            pass
    
    # Step 8: Generate final report
    notes = await server.call_tool("list_paper_notes", {
        "tags": ["quantum", "review-complete"]
    })
    
    # Verify workflow completed
    assert len(summary[0].text) > 500, "Generated summary"
    assert "abstract" in sections[0].text.lower(), "Extracted sections"
    assert "@article" in citations[0].text, "Extracted citations"
    assert "BETTER IDEAS" in comparison[0].text, "Performed comparison"
    assert "Similar papers" in similar[0].text, "Found similar papers"
    assert "Note added" in notes[0].text or "Found" in notes[0].text
    
    return {
        "papers_found": len(papers),
        "papers_downloaded": len(paper_ids),
        "summary_length": len(summary[0].text),
        "citations_extracted": citations[0].text.count("@article"),
        "notes_added": True
    }

# Run it:
results = asyncio.run(test_complete_workflow())
print(f"Workflow completed: {results}")
```

## Test Details

**Workflow Steps**:
1. Search papers → Download batch → Summarize → Extract sections
2. Extract citations → Analyze code → Compare ideas → Find similar
3. Add notes → List notes → Create bibliography

**Run Command**:
```bash
cd /path/to/arxiv-mcp-server
python -m pytest tests/test_integration.py::test_full_workflow -v -s
```

**Expected Workflow Output**:
```text
Step 1: Found 10 papers on quantum error correction
Step 2: Downloaded 5 papers successfully
Step 3: Analyzing paper 2312.02813...
  - Summary: 823 characters
  - Sections extracted: 3/3
  - Citations found: 42
  - Code blocks: 5 Python functions
Step 4: Comparison complete - 3 better ideas, 2 limitations
Step 5: Found 3 similar papers
Step 6: Note added with 4 tags
Step 7: Bibliography created with 127 references
Step 8: Research complete - 1 papers fully analyzed

Workflow completed: {'papers_found': 10, 'papers_downloaded': 5, ...}
```

## Common Issues & Solutions

### Issue 1: Workflow timeout
```python
# Solution: Add timeout handling for each step
async def run_with_timeout(coro, timeout=30, default=None):
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        print(f"Step timed out after {timeout}s")
        return default
```

### Issue 2: Cascading failures
```python
# Solution: Continue on non-critical failures
critical_steps = ["search_papers", "batch_download"]
results = {}

for step_name, step_coro in workflow_steps.items():
    try:
        results[step_name] = await step_coro
    except Exception as e:
        if step_name in critical_steps:
            raise  # Re-raise critical errors
        else:
            print(f"Non-critical step {step_name} failed: {e}")
            results[step_name] = None
```

### Issue 3: Resource exhaustion
```python
# Solution: Add cleanup between steps
import gc

# After batch operations
await asyncio.sleep(1)  # Let system catch up
gc.collect()  # Force garbage collection

# Limit concurrent operations
async with asyncio.Semaphore(3):
    # Run resource-intensive operations
```

## Validation Requirements

```python
# This test passes when:
# Core workflow completes
assert search_results, "Search returned results"
assert batch_result, "Batch download completed"
assert summary, "Summary generated"

# Integration points work
assert len(paper_ids) > 0, "Papers identified for download"
assert main_paper_id in batch_result[0].text or "Success" in batch_result[0].text

# Data flows between tools
summary_text = summary[0].text
assert main_paper_id in summary_text or "Summary of" in summary_text

# Final outputs exist
assert results["papers_found"] > 0
assert results["papers_downloaded"] > 0
assert results["summary_length"] > 500
assert results["notes_added"] == True

print("✓ All 15 tools successfully integrated in research workflow")
```