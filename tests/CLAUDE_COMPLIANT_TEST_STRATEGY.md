# CLAUDE.md Compliant Test Strategy

## Overview
This document outlines the proper testing approach that complies with CLAUDE.md standards, specifically:
- NO mocking of core functionality
- NO use of MagicMock
- Testing with REAL data from ArXiv
- Verifying against CONCRETE expected results

## Key Principles from CLAUDE.md

1. **Real Data**: Always test with actual data, never fake inputs (line 99)
2. **No Mocking**: NEVER mock core functionality (line 101)
3. **MagicMock Ban**: MagicMock is strictly forbidden for testing core functionality (line 102)
4. **Expected Results**: Verify outputs against concrete expected results (line 100)
5. **Meaningful Assertions**: Use assertions that verify specific expected values (line 103)

## Test Strategy

### 1. Use Real ArXiv Papers for Testing

Instead of mocking, use actual ArXiv paper IDs that are stable and well-known:

```python
# Good - Real paper IDs
TEST_PAPERS = {
    "quantum_computing": "1907.02540",  # "Quantum Computing: An Overview"
    "machine_learning": "1206.5538",    # "Representation Learning: A Review"
    "attention_mechanism": "1706.03762", # "Attention Is All You Need"
}

# Bad - Mock data
mock_paper = MagicMock()  # FORBIDDEN!
```

### 2. Test Against Real API Responses

```python
# Good - Real API call
def test_search_real_papers():
    """Test search with real ArXiv API."""
    result = search_arxiv("quantum computing", max_results=5)
    
    # Verify against known characteristics
    assert len(result) > 0, "Search should return results"
    assert any("quantum" in paper.title.lower() for paper in result)
    
# Bad - Mocked response
@patch('arxiv.Client')  # FORBIDDEN!
def test_search_mocked(mock_client):
    pass
```

### 3. Integration Tests with Real Downloads

```python
# Good - Real download test
def test_download_real_paper():
    """Test downloading a real paper."""
    paper_id = "1706.03762"  # Known stable paper
    
    result = download_paper(paper_id)
    
    assert result.success is True
    assert Path(result.file_path).exists()
    assert Path(result.file_path).stat().st_size > 100000  # Real PDFs are large
```

### 4. Test Data Management

Create a dedicated test data module with known good papers:

```python
# tests/test_data/known_papers.py
STABLE_TEST_PAPERS = {
    "1706.03762": {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
        "year": 2017,
        "categories": ["cs.CL", "cs.LG"],
        "has_code": True,
        "citation_count_min": 50  # At least 50 citations
    }
}
```

### 5. Validation Functions in Test Files

Each test file should have its own validation function:

```python
if __name__ == "__main__":
    import sys
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Real search
    total_tests += 1
    try:
        results = search_arxiv("attention mechanism", max_results=3)
        if len(results) == 0:
            all_validation_failures.append("Search returned 0 results - FAILURE")
        elif not any("attention" in r.title.lower() for r in results):
            all_validation_failures.append("Search results don't contain 'attention'")
    except Exception as e:
        all_validation_failures.append(f"Search test failed: {e}")
    
    # Final result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
```

## Implementation Plan

### Phase 1: Core Module Tests
1. `test_search.py` - Test with real ArXiv searches
2. `test_download.py` - Download actual papers
3. `test_citations.py` - Extract citations from real papers
4. `test_utils.py` - Use real data for utility functions

### Phase 2: Tool Tests
1. Use actual tool implementations
2. Test with real paper IDs
3. Verify actual outputs

### Phase 3: Integration Tests
1. Full workflow tests with real papers
2. Performance tests with actual downloads
3. Concurrent operation tests

## Example: Rewritten Search Test

```python
"""
Test ArXiv search functionality with REAL data.
NO MOCKS - Following CLAUDE.md standards.
"""

import pytest
from arxiv_mcp_server.core.search import search_arxiv

class TestArxivSearchReal:
    """Test ArXiv search with real API calls."""
    
    def test_search_quantum_computing(self):
        """Test searching for quantum computing papers."""
        # Real API call
        results = search_arxiv("quantum computing", max_results=5)
        
        # Verify real results
        assert len(results) > 0, "Should find quantum computing papers"
        assert all(r.arxiv_id for r in results), "All results should have IDs"
        
        # Check for expected content
        titles_lower = [r.title.lower() for r in results]
        assert any("quantum" in title for title in titles_lower), \
            "At least one result should mention 'quantum'"
    
    def test_search_by_author(self):
        """Test searching by known author."""
        # Search for papers by Yoshua Bengio
        results = search_arxiv("", author="Bengio", max_results=3)
        
        assert len(results) > 0, "Should find papers by Bengio"
        assert any("Bengio" in author for r in results for author in r.authors), \
            "Results should include Bengio as author"
    
    def test_search_empty_query(self):
        """Test that empty search returns results."""
        results = search_arxiv("", max_results=5)
        assert len(results) == 5, "Empty search should return requested number"

if __name__ == "__main__":
    # Direct validation without pytest
    test = TestArxivSearchReal()
    
    failures = []
    
    try:
        test.test_search_quantum_computing()
        print("✓ Quantum computing search passed")
    except AssertionError as e:
        failures.append(f"Quantum search: {e}")
    
    try:
        test.test_search_by_author()
        print("✓ Author search passed")
    except AssertionError as e:
        failures.append(f"Author search: {e}")
    
    if failures:
        print(f"\n❌ {len(failures)} tests failed:")
        for f in failures:
            print(f"  - {f}")
        exit(1)
    else:
        print("\n✅ All tests passed with REAL data!")
        exit(0)
```

## Benefits of This Approach

1. **Reliability**: Tests verify actual system behavior
2. **Confidence**: No false positives from mocked responses
3. **Integration**: Tests the full stack including network calls
4. **Real-world**: Catches issues that mocks would hide
5. **Compliance**: Follows CLAUDE.md standards exactly

## Considerations

1. **Speed**: Real API calls are slower than mocks
2. **Network**: Tests require internet connection
3. **Rate Limits**: May need to space out API calls
4. **Stability**: Use well-known papers that won't disappear

## Conclusion

By following CLAUDE.md standards and avoiding ALL mocks for core functionality, our tests will:
- Provide real confidence in the system
- Catch actual integration issues
- Validate against real ArXiv behavior
- Comply with project standards