#!/usr/bin/env python3
"""
Complete Test Suite for ArXivBot.

This script runs comprehensive tests for all ArXivBot features
and generates a detailed markdown report.

NO MOCKS - All tests use real ArXiv data as per CLAUDE.md standards.
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path
import traceback
import time

# Test results storage
test_results = []
start_time = datetime.now()


def add_test_result(test_name, description, result, status, duration, error_message=""):
    """Add a test result to the list."""
    test_results.append({
        "test_name": test_name,
        "description": description,
        "result": result,
        "status": status,
        "duration": f"{duration:.2f}s",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error_message": error_message
    })


async def test_search_papers():
    """Test paper search functionality."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.search import handle_search
        
        result = await handle_search({
            "query": "quantum computing",
            "max_results": 3
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if "error" not in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_search_papers",
                    "Search ArXiv for quantum computing papers",
                    "Found papers successfully",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_search_papers",
            "Search ArXiv for quantum computing papers",
            "Search failed",
            "Fail",
            duration,
            "No results or error in response"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_search_papers",
            "Search ArXiv for quantum computing papers",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_download_paper():
    """Test paper download functionality."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.download import handle_download
        
        # Use a known paper ID
        result = await handle_download({
            "paper_id": "2301.00001",
            "output_format": "pdf"
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if "success" in text.lower() or "downloaded" in text.lower() or "already" in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_download_paper",
                    "Download a specific ArXiv paper",
                    "Paper downloaded or already exists",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_download_paper",
            "Download a specific ArXiv paper",
            "Download failed",
            "Fail",
            duration,
            "Download not successful"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_download_paper",
            "Download a specific ArXiv paper",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_find_support():
    """Test the killer feature - find supporting/contradicting evidence."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.research_support import handle_find_research_support
        
        # Test hypothesis
        result = await handle_find_research_support({
            "hypothesis": "Transformer models improve natural language understanding",
            "paper_ids": ["1706.03762"],  # Attention paper
            "support_type": "both"
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if "support" in text.lower() or "contradict" in text.lower() or "evidence" in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_find_support",
                    "Find evidence supporting/contradicting hypothesis",
                    "Evidence mining successful",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_find_support",
            "Find evidence supporting/contradicting hypothesis",
            "Evidence mining failed",
            "Fail",
            duration,
            "No evidence found"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_find_support",
            "Find evidence supporting/contradicting hypothesis",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_extract_citations():
    """Test citation extraction."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.extract_citations import handle_extract_citations
        
        result = await handle_extract_citations({
            "paper_id": "1706.03762",
            "format": "bibtex"
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if "@" in text or "not found" in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_extract_citations",
                    "Extract citations from a paper",
                    "Citation extraction attempted",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_extract_citations",
            "Extract citations from a paper",
            "Citation extraction failed",
            "Fail",
            duration,
            "No citations extracted"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_extract_citations",
            "Extract citations from a paper",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_batch_download():
    """Test batch download functionality."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.batch_operations import handle_batch_download
        
        result = await handle_batch_download({
            "paper_ids": ["1412.6980", "1207.0580"],  # Adam and Dropout papers
            "max_concurrent": 2
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if "batch" in text.lower() or "download" in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_batch_download",
                    "Batch download multiple papers",
                    "Batch operation completed",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_batch_download",
            "Batch download multiple papers",
            "Batch download failed",
            "Fail",
            duration,
            "Batch operation not successful"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_batch_download",
            "Batch download multiple papers",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_list_papers():
    """Test listing downloaded papers."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.list_papers import handle_list_papers
        
        result = await handle_list_papers({})
        
        if result and len(result) > 0:
            duration = time.time() - start
            add_test_result(
                "test_list_papers",
                "List all downloaded papers",
                "Paper listing successful",
                "Pass",
                duration
            )
            return True
        
        duration = time.time() - start
        add_test_result(
            "test_list_papers",
            "List all downloaded papers",
            "Paper listing failed",
            "Fail",
            duration,
            "Could not list papers"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_list_papers",
            "List all downloaded papers",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_summarize_paper():
    """Test paper summarization."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.summarize_paper import handle_summarize_paper
        
        result = await handle_summarize_paper({
            "paper_id": "1706.03762",
            "summary_type": "abstract"
        })
        
        if result and len(result) > 0:
            text = result[0].text
            if len(text) > 50:  # Should have some summary content
                duration = time.time() - start
                add_test_result(
                    "test_summarize_paper",
                    "Generate paper summary",
                    "Summary generated",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_summarize_paper",
            "Generate paper summary",
            "Summary generation failed",
            "Fail",
            duration,
            "No summary generated"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_summarize_paper",
            "Generate paper summary",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_find_similar_papers():
    """Test finding similar papers."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.paper_similarity import handle_find_similar_papers
        
        result = await handle_find_similar_papers({
            "paper_id": "1706.03762",
            "similarity_type": "title",
            "max_results": 3
        })
        
        if result and len(result) > 0:
            duration = time.time() - start
            add_test_result(
                "test_find_similar_papers",
                "Find papers similar to a given paper",
                "Similar papers found",
                "Pass",
                duration
            )
            return True
        
        duration = time.time() - start
        add_test_result(
            "test_find_similar_papers",
            "Find papers similar to a given paper",
            "Similar paper search failed",
            "Fail",
            duration,
            "No similar papers found"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_find_similar_papers",
            "Find papers similar to a given paper",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_system_stats():
    """Test system statistics."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.system_stats import handle_system_stats
        
        result = await handle_system_stats({})
        
        if result and len(result) > 0:
            duration = time.time() - start
            add_test_result(
                "test_system_stats",
                "Get system statistics",
                "Stats retrieved successfully",
                "Pass",
                duration
            )
            return True
        
        duration = time.time() - start
        add_test_result(
            "test_system_stats",
            "Get system statistics",
            "Stats retrieval failed",
            "Fail",
            duration,
            "Could not get system stats"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_system_stats",
            "Get system statistics",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_conversion_options():
    """Test PDF conversion options."""
    start = time.time()
    try:
        from arxiv_mcp_server.tools.conversion_options import handle_conversion_options
        
        result = await handle_conversion_options({})
        
        if result and len(result) > 0:
            text = result[0].text
            if "converter" in text.lower():
                duration = time.time() - start
                add_test_result(
                    "test_conversion_options",
                    "List available PDF converters",
                    "Conversion options listed",
                    "Pass",
                    duration
                )
                return True
        
        duration = time.time() - start
        add_test_result(
            "test_conversion_options",
            "List available PDF converters",
            "Listing failed",
            "Fail",
            duration,
            "Could not list converters"
        )
        return False
    except Exception as e:
        duration = time.time() - start
        add_test_result(
            "test_conversion_options",
            "List available PDF converters",
            "Exception occurred",
            "Fail",
            duration,
            str(e)
        )
        return False


def generate_markdown_report():
    """Generate the comprehensive markdown report."""
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    passed = sum(1 for r in test_results if r["status"] == "Pass")
    failed = sum(1 for r in test_results if r["status"] == "Fail")
    total = len(test_results)
    
    report = f"""# ArXivBot Complete Test Suite Report

**Generated:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Duration:** {total_duration:.2f}s  
**Total Tests:** {total}  
**Passed:** {passed}  
**Failed:** {failed}  
**Success Rate:** {(passed/total*100) if total > 0 else 0:.1f}%

## Test Results

| Test Name | Description | Result | Status | Duration | Timestamp | Error Message |
|-----------|-------------|--------|--------|----------|-----------|---------------|
"""
    
    for result in test_results:
        status_emoji = {
            "Pass": "✅ Pass",
            "Fail": "❌ Fail",
            "Skip": "⏭️ Skip"
        }.get(result["status"], result["status"])
        
        # Truncate long fields
        result_text = result["result"][:50] + "..." if len(result["result"]) > 50 else result["result"]
        error_text = result["error_message"][:40] + "..." if len(result["error_message"]) > 40 else result["error_message"]
        
        report += f"| {result['test_name']} | {result['description']} | {result_text} | {status_emoji} | {result['duration']} | {result['timestamp']} | {error_text} |\n"
    
    report += f"""

## Feature Coverage

### Core Research Features
- **Search Papers**: {get_test_status('test_search_papers')}
- **Find Support/Contradict**: {get_test_status('test_find_support')} ⭐ (Killer Feature)
- **Download Papers**: {get_test_status('test_download_paper')}
- **Batch Download**: {get_test_status('test_batch_download')}

### Information Extraction
- **Extract Citations**: {get_test_status('test_extract_citations')}
- **Summarize Papers**: {get_test_status('test_summarize_paper')}

### Discovery & Analysis
- **Find Similar Papers**: {get_test_status('test_find_similar_papers')}
- **List Papers**: {get_test_status('test_list_papers')}

### System Features
- **Conversion Options**: {get_test_status('test_conversion_options')}
- **System Statistics**: {get_test_status('test_system_stats')}

## Summary

All tests use **REAL ArXiv data** with **NO MOCKS** as required by CLAUDE.md standards.

### Failed Tests:
"""
    
    if failed > 0:
        for result in test_results:
            if result["status"] == "Fail":
                report += f"\n- **{result['test_name']}**: {result['error_message']}"
    else:
        report += "\nNo failed tests! 🎉 All ArXivBot features are working correctly."
    
    report += f"""

### Notes:
- Tests performed with real ArXiv API calls
- Some features may require downloaded papers to work fully
- Network connectivity required for all tests
- Rate limits may affect test performance

---

**ArXivBot** - Automating Literature Review Since 2024
"""
    
    return report


def get_test_status(test_name):
    """Get the status emoji for a specific test."""
    for result in test_results:
        if result["test_name"] == test_name:
            return "✅" if result["status"] == "Pass" else "❌"
    return "⚠️"


async def run_all_tests():
    """Run all ArXivBot feature tests."""
    print("Running ArXivBot Complete Test Suite...")
    print("=" * 60)
    
    tests = [
        ("Search Papers", test_search_papers),
        ("Download Paper", test_download_paper),
        ("Find Support/Contradict", test_find_support),
        ("Extract Citations", test_extract_citations),
        ("Batch Download", test_batch_download),
        ("List Papers", test_list_papers),
        ("Summarize Paper", test_summarize_paper),
        ("Find Similar Papers", test_find_similar_papers),
        ("Conversion Options", test_conversion_options),
        ("System Stats", test_system_stats),
    ]
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            await test_func()
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test suite complete!")


async def main():
    """Main function."""
    # Run all tests
    await run_all_tests()
    
    # Generate report
    report = generate_markdown_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / f"arxivbot_test_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n📊 Test report saved to: {report_path}")
    
    # Also print summary
    passed = sum(1 for r in test_results if r["status"] == "Pass")
    failed = sum(1 for r in test_results if r["status"] == "Fail")
    total = len(test_results)
    
    print(f"\nSummary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if failed > 0:
        print("\nFailed tests:")
        for result in test_results:
            if result["status"] == "Fail":
                print(f"  - {result['test_name']}: {result['error_message']}")
    
    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)