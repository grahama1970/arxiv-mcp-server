#!/usr/bin/env python3
"""
Run Real Tests and Generate Markdown Report.

This script runs actual tests with real ArXiv data and generates
a markdown report in docs/reports/.

NO MOCKS - CLAUDE.md compliant.
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path
import traceback

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


async def test_arxiv_search():
    """Test real ArXiv search functionality."""
    start = datetime.now()
    try:
        import arxiv
        
        # Real ArXiv search
        client = arxiv.Client()
        search = arxiv.Search(query="quantum computing", max_results=3)
        results = list(client.results(search))
        
        if results:
            first_paper = results[0]
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_arxiv_search",
                "Search ArXiv for quantum computing papers",
                f"Found {len(results)} papers. First: {first_paper.title[:50]}...",
                "Pass",
                duration
            )
            return True
        else:
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_arxiv_search",
                "Search ArXiv for quantum computing papers",
                "No results found",
                "Fail",
                duration,
                "Search returned 0 results"
            )
            return False
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        add_test_result(
            "test_arxiv_search",
            "Search ArXiv for quantum computing papers",
            "Search failed",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_specific_paper():
    """Test retrieving a specific known paper."""
    start = datetime.now()
    try:
        import arxiv
        
        # Search for Attention paper
        client = arxiv.Client()
        search = arxiv.Search(id_list=["1706.03762"])
        results = list(client.results(search))
        
        if results and results[0].title == "Attention Is All You Need":
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_specific_paper",
                "Retrieve 'Attention Is All You Need' paper",
                f"Successfully retrieved paper by ID",
                "Pass",
                duration
            )
            return True
        else:
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_specific_paper",
                "Retrieve 'Attention Is All You Need' paper",
                "Paper not found or wrong paper",
                "Fail",
                duration,
                "Could not retrieve the specific paper"
            )
            return False
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        add_test_result(
            "test_specific_paper",
            "Retrieve 'Attention Is All You Need' paper",
            "Retrieval failed",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_paper_metadata():
    """Test extracting paper metadata."""
    start = datetime.now()
    try:
        import arxiv
        
        # Get BERT paper metadata
        client = arxiv.Client()
        search = arxiv.Search(id_list=["1810.04805"])
        results = list(client.results(search))
        
        if results:
            paper = results[0]
            has_authors = len(paper.authors) > 0
            has_categories = len(paper.categories) > 0
            has_pdf_url = paper.pdf_url is not None
            
            if has_authors and has_categories and has_pdf_url:
                duration = (datetime.now() - start).total_seconds()
                add_test_result(
                    "test_paper_metadata",
                    "Extract metadata from BERT paper",
                    f"Authors: {len(paper.authors)}, Categories: {paper.categories[0]}",
                    "Pass",
                    duration
                )
                return True
            else:
                duration = (datetime.now() - start).total_seconds()
                add_test_result(
                    "test_paper_metadata",
                    "Extract metadata from BERT paper",
                    "Missing metadata fields",
                    "Fail",
                    duration,
                    "Some metadata fields are missing"
                )
                return False
        else:
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_paper_metadata",
                "Extract metadata from BERT paper",
                "Paper not found",
                "Fail",
                duration,
                "Could not retrieve BERT paper"
            )
            return False
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        add_test_result(
            "test_paper_metadata",
            "Extract metadata from BERT paper",
            "Metadata extraction failed",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_category_search():
    """Test searching by category."""
    start = datetime.now()
    try:
        import arxiv
        
        # Search in cs.LG category
        client = arxiv.Client()
        search = arxiv.Search(
            query="cat:cs.LG",
            max_results=5,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        results = list(client.results(search))
        
        if results:
            # Check if all are in cs.LG
            all_in_category = all("cs.LG" in paper.categories for paper in results)
            duration = (datetime.now() - start).total_seconds()
            
            if all_in_category:
                add_test_result(
                    "test_category_search",
                    "Search papers in cs.LG category",
                    f"Found {len(results)} papers in cs.LG",
                    "Pass",
                    duration
                )
                return True
            else:
                add_test_result(
                    "test_category_search",
                    "Search papers in cs.LG category",
                    "Some papers not in cs.LG category",
                    "Fail",
                    duration,
                    "Category filter not working correctly"
                )
                return False
        else:
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_category_search",
                "Search papers in cs.LG category",
                "No results found",
                "Fail",
                duration,
                "Category search returned 0 results"
            )
            return False
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        add_test_result(
            "test_category_search",
            "Search papers in cs.LG category",
            "Category search failed",
            "Fail",
            duration,
            str(e)
        )
        return False


async def test_author_search():
    """Test searching by author."""
    start = datetime.now()
    try:
        import arxiv
        
        # Search for Yoshua Bengio papers
        client = arxiv.Client()
        search = arxiv.Search(
            query="au:Bengio",
            max_results=3
        )
        results = list(client.results(search))
        
        if results:
            # Check if Bengio is in authors
            has_bengio = any(
                any("Bengio" in str(author) for author in paper.authors)
                for paper in results
            )
            duration = (datetime.now() - start).total_seconds()
            
            if has_bengio:
                add_test_result(
                    "test_author_search",
                    "Search papers by Yoshua Bengio",
                    f"Found {len(results)} papers by Bengio",
                    "Pass",
                    duration
                )
                return True
            else:
                add_test_result(
                    "test_author_search",
                    "Search papers by Yoshua Bengio",
                    "No papers with Bengio as author",
                    "Fail",
                    duration,
                    "Author search not working correctly"
                )
                return False
        else:
            duration = (datetime.now() - start).total_seconds()
            add_test_result(
                "test_author_search",
                "Search papers by Yoshua Bengio",
                "No results found",
                "Fail",
                duration,
                "Author search returned 0 results"
            )
            return False
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        add_test_result(
            "test_author_search",
            "Search papers by Yoshua Bengio",
            "Author search failed",
            "Fail",
            duration,
            str(e)
        )
        return False


def generate_markdown_report():
    """Generate the markdown report."""
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    passed = sum(1 for r in test_results if r["status"] == "Pass")
    failed = sum(1 for r in test_results if r["status"] == "Fail")
    total = len(test_results)
    
    report = f"""# ArXiv MCP Server Test Report

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
        result_text = result["result"][:60] + "..." if len(result["result"]) > 60 else result["result"]
        error_text = result["error_message"][:50] + "..." if len(result["error_message"]) > 50 else result["error_message"]
        
        report += f"| {result['test_name']} | {result['description']} | {result_text} | {status_emoji} | {result['duration']} | {result['timestamp']} | {error_text} |\n"
    
    report += f"""

## Summary

All tests use **REAL ArXiv API** calls with **NO MOCKS** as required by CLAUDE.md standards.

### Test Categories:
- **Search Tests**: Testing ArXiv search functionality with real queries
- **Metadata Tests**: Extracting real paper metadata
- **Category Tests**: Filtering by ArXiv categories
- **Author Tests**: Searching by author names

### Failed Tests:
"""
    
    if failed > 0:
        for result in test_results:
            if result["status"] == "Fail":
                report += f"\n- **{result['test_name']}**: {result['error_message']}"
    else:
        report += "\nNo failed tests! 🎉"
    
    return report


async def run_all_tests():
    """Run all tests."""
    print("Running ArXiv MCP Server Tests with REAL DATA...")
    print("=" * 60)
    
    tests = [
        ("ArXiv Search", test_arxiv_search),
        ("Specific Paper", test_specific_paper),
        ("Paper Metadata", test_paper_metadata),
        ("Category Search", test_category_search),
        ("Author Search", test_author_search),
    ]
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            await test_func()
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test run complete!")


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
    
    report_path = report_dir / f"test_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n📊 Test report saved to: {report_path}")
    
    # Also print summary
    passed = sum(1 for r in test_results if r["status"] == "Pass")
    failed = sum(1 for r in test_results if r["status"] == "Fail")
    total = len(test_results)
    
    print(f"\nSummary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)