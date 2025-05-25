#!/usr/bin/env python3
"""
Test runner with automated Markdown report generation.

This script runs the test suite and generates a detailed Markdown report
in the docs/reports/ directory, following CLAUDE.md standards.

Usage:
    python run_tests_with_report.py [pytest args]
    
Examples:
    python run_tests_with_report.py                    # Run all tests
    python run_tests_with_report.py -m "not slow"      # Skip slow tests
    python run_tests_with_report.py tests/core/        # Run specific tests
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_tests_with_report():
    """Run pytest with automatic report generation."""
    print("=" * 80)
    print("ArXiv MCP Server - Test Suite with Automated Reporting")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ensure reports directory exists
    project_root = Path(__file__).parent
    reports_dir = project_root / "docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # Add report generation plugin if not already specified
    if "-p" not in " ".join(cmd):
        cmd.extend(["-p", "arxiv_mcp_server.test_reporter"])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Run pytest
    try:
        result = subprocess.run(cmd, cwd=project_root)
        exit_code = result.returncode
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
        exit_code = 1
    except Exception as e:
        print(f"\n\nError running tests: {e}")
        exit_code = 1
    
    print("\n" + "=" * 80)
    print(f"Test run completed with exit code: {exit_code}")
    
    # Check if report was generated
    latest_report = find_latest_report(reports_dir)
    if latest_report:
        print(f"\n📊 Test report generated: {latest_report}")
        print(f"   View with: cat {latest_report}")
    
    return exit_code


def find_latest_report(reports_dir: Path) -> Path:
    """Find the most recently created test report."""
    try:
        reports = list(reports_dir.glob("test_report_*.md"))
        if reports:
            return max(reports, key=lambda p: p.stat().st_mtime)
    except Exception:
        pass
    return None


def run_validation_example():
    """Run a validation example to demonstrate report generation."""
    from arxiv_mcp_server.test_reporter import TestReportGenerator
    
    print("\nRunning validation example...")
    print("-" * 40)
    
    # Create a sample report
    reporter = TestReportGenerator()
    reporter.start_session()
    
    # Add example test results
    test_data = [
        {
            "test_name": "test_search_arxiv_real",
            "description": "Search ArXiv for quantum computing papers",
            "result": "Found 15 papers matching query",
            "status": "Pass",
            "duration": 2.34,
        },
        {
            "test_name": "test_download_attention_paper",
            "description": "Download 'Attention Is All You Need' paper",
            "result": "Downloaded 1706.03762.pdf (2.1MB)",
            "status": "Pass",
            "duration": 5.67,
        },
        {
            "test_name": "test_extract_citations",
            "description": "Extract citations from BERT paper",
            "result": "Extracted 45 citations in BibTeX format",
            "status": "Pass",
            "duration": 1.23,
        },
        {
            "test_name": "test_batch_download_limit",
            "description": "Batch download respects concurrency limit",
            "result": "Max 3 concurrent downloads observed",
            "status": "Pass",
            "duration": 12.45,
        },
        {
            "test_name": "test_invalid_paper_id",
            "description": "Handle non-existent paper gracefully",
            "result": "Returned proper 404 error",
            "status": "Pass",
            "duration": 0.89,
        },
        {
            "test_name": "test_network_timeout",
            "description": "Handle network timeout properly",
            "result": "Timeout after 30s",
            "status": "Fail",
            "duration": 30.01,
            "error_message": "Network request timed out after 30 seconds"
        }
    ]
    
    for test in test_data:
        reporter.add_test_result(**test)
    
    # Save example report
    report_path = reporter.save_report("example_test_report.md")
    print(f"\n✅ Example report saved to: {report_path}")
    
    # Show report preview
    report_content = reporter.generate_report()
    preview_lines = report_content.split('\n')[:20]
    print("\nReport preview:")
    print("-" * 40)
    for line in preview_lines:
        print(line)
    print("... (truncated)")


if __name__ == "__main__":
    # Check if running validation example
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        run_validation_example()
        sys.exit(0)
    
    # Run actual tests
    exit_code = run_tests_with_report()
    sys.exit(exit_code)