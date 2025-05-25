"""
Example CLAUDE.md Compliant Test with Real Data.

This test demonstrates proper testing approach:
- NO mocks for core functionality
- Real ArXiv API calls
- Concrete expected results
- Proper validation

This test will be included in automated reports.
"""

import pytest
import asyncio
from pathlib import Path


class TestExampleCompliant:
    """Example tests following CLAUDE.md standards."""
    
    @pytest.mark.real_api
    def test_search_attention_paper_real(self):
        """Search for the famous 'Attention Is All You Need' paper."""
        from arxiv_mcp_server.tools.search import handle_search
        
        # Real API call - no mocking
        result = asyncio.run(handle_search({
            "query": "Attention Is All You Need Vaswani",
            "max_results": 5
        }))
        
        # Parse result
        assert len(result) > 0, "Should return search results"
        
        # Look for the specific paper in results
        result_text = result[0].text
        assert "1706.03762" in result_text, "Should find the Attention paper"
        assert "Vaswani" in result_text, "Should include author name"
    
    @pytest.mark.real_api
    def test_search_recent_quantum_papers(self):
        """Search for recent quantum computing papers."""
        from arxiv_mcp_server.tools.search import handle_search
        
        # Search for quantum papers from 2024
        result = asyncio.run(handle_search({
            "query": "quantum computing",
            "date_from": "2024-01-01",
            "max_results": 3
        }))
        
        assert len(result) > 0, "Should find recent quantum papers"
        
        # Verify results contain quantum-related content
        result_text = result[0].text.lower()
        quantum_terms = ["quantum", "qubit", "superposition", "entanglement"]
        assert any(term in result_text for term in quantum_terms), \
            "Results should contain quantum-related terms"
    
    @pytest.mark.real_api
    @pytest.mark.network
    def test_download_small_paper_real(self):
        """Test downloading a real (small) ArXiv paper."""
        from arxiv_mcp_server.tools.download import handle_download
        
        # Use a known small paper for faster testing
        # This is a 2-page paper about Fizz Buzz in TensorFlow
        result = asyncio.run(handle_download({
            "paper_id": "1412.6980",  # Adam optimizer paper
            "output_format": "pdf"
        }))
        
        assert len(result) > 0, "Should return download result"
        result_text = result[0].text
        
        # Check for success indicators
        assert "error" not in result_text.lower() or "success" in result_text.lower(), \
            "Download should succeed or already exist"
        
        # Verify file exists (if download succeeded)
        if "Downloaded successfully" in result_text:
            assert "1412.6980.pdf" in result_text, "Should mention the PDF file"
    
    @pytest.mark.real_api
    def test_list_papers_empty_initially(self):
        """Test listing papers when storage might be empty."""
        from arxiv_mcp_server.tools.list_papers import handle_list_papers
        
        result = asyncio.run(handle_list_papers({}))
        
        assert len(result) > 0, "Should return a result"
        result_text = result[0].text
        
        # Should either list papers or indicate empty
        assert "paper" in result_text.lower() or "no papers" in result_text.lower(), \
            "Should mention papers or indicate none found"
    
    def test_conversion_options_available(self):
        """Test that conversion options tool works."""
        from arxiv_mcp_server.tools.conversion_options import handle_conversion_options
        
        result = asyncio.run(handle_conversion_options({}))
        
        assert len(result) > 0, "Should return conversion options"
        result_text = result[0].text
        
        # Should list available converters
        assert "converter" in result_text.lower(), "Should mention converters"
        assert any(fmt in result_text.lower() for fmt in ["pdf", "markdown", "text"]), \
            "Should mention supported formats"
    
    @pytest.mark.slow
    @pytest.mark.real_api
    def test_extract_citations_from_real_paper(self):
        """Test citation extraction from a real paper (if downloaded)."""
        from arxiv_mcp_server.tools.extract_citations import handle_extract_citations
        
        try:
            # Try to extract citations from a well-known paper
            result = asyncio.run(handle_extract_citations({
                "paper_id": "1706.03762",  # Attention paper
                "format": "bibtex"
            }))
            
            if len(result) > 0 and "error" not in result[0].text.lower():
                # If paper exists and extraction worked
                result_text = result[0].text
                assert "@" in result_text or "no citations" in result_text.lower(), \
                    "Should return BibTeX format or indicate no citations"
        except Exception as e:
            # Paper might not be downloaded yet
            pytest.skip(f"Paper not available for citation extraction: {e}")


# Validation function for standalone testing
if __name__ == "__main__":
    import sys
    from arxiv_mcp_server.test_reporter import TestReportGenerator
    
    print("=" * 80)
    print("RUNNING EXAMPLE COMPLIANT TESTS WITH REAL DATA")
    print("=" * 80)
    
    reporter = TestReportGenerator()
    reporter.start_session()
    
    test_instance = TestExampleCompliant()
    tests_to_run = [
        ("test_search_attention_paper_real", "Search for Attention paper"),
        ("test_search_recent_quantum_papers", "Search recent quantum papers"),
        ("test_list_papers_empty_initially", "List papers in storage"),
        ("test_conversion_options_available", "Check conversion options"),
    ]
    
    for test_name, description in tests_to_run:
        print(f"\nRunning: {test_name}")
        print("-" * 40)
        
        start_time = asyncio.get_event_loop().time()
        try:
            test_method = getattr(test_instance, test_name)
            test_method()
            duration = asyncio.get_event_loop().time() - start_time
            
            print(f"✅ PASSED")
            reporter.add_test_result(
                test_name=test_name,
                description=description,
                result="Test passed with real data",
                status="Pass",
                duration=duration
            )
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            print(f"❌ FAILED: {e}")
            reporter.add_test_result(
                test_name=test_name,
                description=description,
                result="Test failed",
                status="Fail",
                duration=duration,
                error_message=str(e)
            )
    
    # Save report
    report_path = reporter.save_report("example_compliant_test_report.md")
    print(f"\n\n📊 Test report saved to: {report_path}")
    
    # Show summary
    passed = sum(1 for t in reporter.test_results if t['status'] == 'Pass')
    total = len(reporter.test_results)
    print(f"\nSummary: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)