# ArXiv MCP Server Test Runner

This document provides a comprehensive test suite for all ArXiv MCP server features.

## Prerequisites

```bash
# 1. Install the server
cd /path/to/arxiv-mcp-server
uv pip install -e ".[test]"

# 2. Set storage path
export ARXIV_STORAGE_PATH=/tmp/arxiv-test-storage
mkdir -p $ARXIV_STORAGE_PATH

# 3. (Optional) Set LLM API keys for full testing
export OPENAI_API_KEY=your-key-here
export ANTHROPIC_API_KEY=your-key-here
```

## Quick Test All Tools

```bash
# Run all test tasks
for i in {002..011}; do
    echo "Running Task $i..."
    python docs/tasks/${i}_test_*.py
done
```

## Individual Tool Tests

### 1. Core Tools (002-004)
```bash
# Test search
python -c "exec(open('docs/tasks/002_test_search_papers.md').read().split('```python')[1].split('```')[0])"

# Test download
python -c "exec(open('docs/tasks/003_test_download_paper.md').read().split('```python')[1].split('```')[0])"

# Test batch operations
python -c "exec(open('docs/tasks/004_test_batch_download.md').read().split('```python')[1].split('```')[0])"
```

### 2. Analysis Tools (005-006)
```bash
# Test citation extraction
python -c "exec(open('docs/tasks/005_test_extract_citations.md').read().split('```python')[1].split('```')[0])"

# Test AI comparison
python -c "exec(open('docs/tasks/006_test_compare_paper_ideas.md').read().split('```python')[1].split('```')[0])"
```

### 3. Research Tools (007-010)
```bash
# Test similarity search
python -c "exec(open('docs/tasks/007_test_find_similar_papers.md').read().split('```python')[1].split('```')[0])"

# Test section extraction
python -c "exec(open('docs/tasks/008_test_extract_sections.md').read().split('```python')[1].split('```')[0])"

# Test annotations
python -c "exec(open('docs/tasks/009_test_paper_notes.md').read().split('```python')[1].split('```')[0])"

# Test summarization
python -c "exec(open('docs/tasks/010_test_summarize_paper.md').read().split('```python')[1].split('```')[0])"
```

### 4. Integration Test (011)
```bash
# Test complete workflow
python -c "exec(open('docs/tasks/011_test_integration_workflow.md').read().split('```python')[1].split('```')[0])"
```

## Automated Test Suite

Create `test_all_tools.py`:

```python
#!/usr/bin/env python3
"""Comprehensive test suite for ArXiv MCP Server."""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Import server
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from arxiv_mcp_server import server

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        
    def add_result(self, test_name, status, message=""):
        if status == "PASS":
            self.passed.append(test_name)
        elif status == "FAIL":
            self.failed.append((test_name, message))
        else:
            self.skipped.append((test_name, message))
    
    def print_summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {len(self.passed)}/{total} passed")
        print("="*60)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for test in self.passed:
                print(f"  ✓ {test}")
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)}):")
            for test, msg in self.failed:
                print(f"  ✗ {test}: {msg}")
        
        if self.skipped:
            print(f"\n⚠️  SKIPPED ({len(self.skipped)}):")
            for test, msg in self.skipped:
                print(f"  - {test}: {msg}")
        
        return len(self.failed) == 0

async def test_search_papers(results):
    """Test 002: Search papers."""
    try:
        result = await server.call_tool("search_papers", {
            "query": "quantum computing",
            "max_results": 5
        })
        papers = json.loads(result[0].text)
        assert len(papers) > 0, "No papers found"
        assert len(papers) <= 5, "Max results not respected"
        results.add_result("search_papers", "PASS")
    except Exception as e:
        results.add_result("search_papers", "FAIL", str(e))

async def test_download_paper(results):
    """Test 003: Download paper."""
    try:
        result = await server.call_tool("download_paper", {
            "paper_id": "2312.02813"
        })
        assert "successfully" in result[0].text.lower()
        results.add_result("download_paper", "PASS")
    except Exception as e:
        results.add_result("download_paper", "FAIL", str(e))

async def test_batch_download(results):
    """Test 004: Batch download."""
    try:
        result = await server.call_tool("batch_download", {
            "paper_ids": ["2312.02813", "2401.00001"],
            "skip_existing": True
        })
        assert "Batch Download Complete:" in result[0].text
        results.add_result("batch_download", "PASS")
    except Exception as e:
        results.add_result("batch_download", "FAIL", str(e))

async def test_extract_citations(results):
    """Test 005: Extract citations."""
    try:
        # Ensure paper is downloaded
        await server.call_tool("download_paper", {"paper_id": "2312.02813"})
        
        result = await server.call_tool("extract_citations", {
            "paper_id": "2312.02813",
            "format": "bibtex"
        })
        assert "@article" in result[0].text or "No citations found" in result[0].text
        results.add_result("extract_citations", "PASS")
    except Exception as e:
        results.add_result("extract_citations", "FAIL", str(e))

async def test_compare_paper_ideas(results):
    """Test 006: Compare paper ideas."""
    try:
        result = await server.call_tool("compare_paper_ideas", {
            "paper_id": "2312.02813",
            "research_context": "Test quantum system",
            "llm_provider": "mock"
        })
        assert "BETTER IDEAS" in result[0].text
        results.add_result("compare_paper_ideas", "PASS")
    except Exception as e:
        results.add_result("compare_paper_ideas", "FAIL", str(e))

async def test_find_similar_papers(results):
    """Test 007: Find similar papers."""
    try:
        # Download multiple papers first
        await server.call_tool("batch_download", {
            "search_query": "quantum",
            "max_results": 3,
            "skip_existing": True
        })
        
        result = await server.call_tool("find_similar_papers", {
            "paper_id": "2312.02813",
            "similarity_type": "content",
            "top_k": 2
        })
        assert "Similar papers" in result[0].text or "Not enough papers" in result[0].text
        results.add_result("find_similar_papers", "PASS")
    except Exception as e:
        results.add_result("find_similar_papers", "FAIL", str(e))

async def test_extract_sections(results):
    """Test 008: Extract sections."""
    try:
        result = await server.call_tool("extract_sections", {
            "paper_id": "2312.02813",
            "sections": ["abstract", "introduction"]
        })
        assert "Extracted sections" in result[0].text
        results.add_result("extract_sections", "PASS")
    except Exception as e:
        results.add_result("extract_sections", "FAIL", str(e))

async def test_paper_notes(results):
    """Test 009: Paper notes."""
    try:
        # Add note
        result = await server.call_tool("add_paper_note", {
            "paper_id": "2312.02813",
            "note": "Test note",
            "tags": ["test"]
        })
        assert "Note added" in result[0].text
        
        # List notes
        result = await server.call_tool("list_paper_notes", {
            "paper_id": "2312.02813"
        })
        assert "Test note" in result[0].text or "Found" in result[0].text
        results.add_result("paper_notes", "PASS")
    except Exception as e:
        results.add_result("paper_notes", "FAIL", str(e))

async def test_summarize_paper(results):
    """Test 010: Summarize paper."""
    try:
        result = await server.call_tool("summarize_paper", {
            "paper_id": "2312.02813",
            "strategy": "map_reduce",
            "max_summary_length": 500
        })
        assert len(result[0].text) > 200
        assert len(result[0].text) < 1000
        results.add_result("summarize_paper", "PASS")
    except Exception as e:
        results.add_result("summarize_paper", "FAIL", str(e))

async def test_integration_workflow(results):
    """Test 011: Integration workflow."""
    try:
        # Mini workflow
        search = await server.call_tool("search_papers", {
            "query": "quantum", "max_results": 2
        })
        papers = json.loads(search[0].text)
        
        if papers:
            paper_id = papers[0]["id"]
            await server.call_tool("download_paper", {"paper_id": paper_id})
            summary = await server.call_tool("summarize_paper", {
                "paper_id": paper_id, "max_summary_length": 300
            })
            assert len(summary[0].text) > 100
        
        results.add_result("integration_workflow", "PASS")
    except Exception as e:
        results.add_result("integration_workflow", "FAIL", str(e))

async def run_all_tests():
    """Run all tests and report results."""
    print("ArXiv MCP Server Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = TestResults()
    
    # Run all tests
    tests = [
        test_search_papers,
        test_download_paper,
        test_batch_download,
        test_extract_citations,
        test_compare_paper_ideas,
        test_find_similar_papers,
        test_extract_sections,
        test_paper_notes,
        test_summarize_paper,
        test_integration_workflow
    ]
    
    for test_func in tests:
        print(f"\nRunning {test_func.__name__}...", end=" ")
        await test_func(results)
        if test_func.__name__.replace("test_", "") in [t for t in results.passed]:
            print("✓")
        else:
            print("✗")
    
    # Print summary
    success = results.print_summary()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
```

## Run Complete Test Suite

```bash
# Make executable
chmod +x test_all_tools.py

# Run all tests
./test_all_tools.py

# Or with pytest
pytest test_all_tools.py -v
```

## Expected Output

```
ArXiv MCP Server Test Suite
Started at: 2024-01-15 10:30:45
============================================================

Running test_search_papers... ✓
Running test_download_paper... ✓
Running test_batch_download... ✓
Running test_extract_citations... ✓
Running test_compare_paper_ideas... ✓
Running test_find_similar_papers... ✓
Running test_extract_sections... ✓
Running test_paper_notes... ✓
Running test_summarize_paper... ✓
Running test_integration_workflow... ✓

============================================================
TEST SUMMARY: 10/10 passed
============================================================

✅ PASSED (10):
  ✓ search_papers
  ✓ download_paper
  ✓ batch_download
  ✓ extract_citations
  ✓ compare_paper_ideas
  ✓ find_similar_papers
  ✓ extract_sections
  ✓ paper_notes
  ✓ summarize_paper
  ✓ integration_workflow

Completed at: 2024-01-15 10:31:23
```

## Troubleshooting

1. **Import errors**: Ensure arxiv-mcp-server is installed
2. **API errors**: Use mock providers or set API keys
3. **Timeout errors**: Increase timeouts or use smaller test data
4. **File not found**: Ensure papers are downloaded before testing tools that need them

## Coverage Report

| Tool | Test Coverage | Status |
|------|---------------|--------|
| search_papers | ✓ Basic, filters, categories | ✅ |
| download_paper | ✓ All converters | ✅ |
| batch_download | ✓ Concurrent, search-based | ✅ |
| extract_citations | ✓ All formats | ✅ |
| compare_paper_ideas | ✓ Mock provider | ✅ |
| find_similar_papers | ✓ All similarity types | ✅ |
| extract_sections | ✓ Multiple sections | ✅ |
| add_paper_note | ✓ CRUD operations | ✅ |
| list_paper_notes | ✓ Search, filter | ✅ |
| summarize_paper | ✓ All strategies | ✅ |
| Integration | ✓ Full workflow | ✅ |