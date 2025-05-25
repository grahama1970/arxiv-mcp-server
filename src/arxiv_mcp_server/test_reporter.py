"""
Automated Test Report Generator for ArXiv MCP Server.

This module generates Markdown test reports after test suite runs,
saving them to docs/reports/ with detailed test results.

Dependencies:
- pytest (for test result collection)
- pathlib (for file operations)
- datetime (for timestamps)

Expected output:
- Markdown report with test results table
- Saved to docs/reports/ directory
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pytest
from pytest import TestReport, ExitCode


class TestReportGenerator:
    """Generate Markdown test reports from pytest results."""
    
    def __init__(self, report_dir: Optional[Path] = None):
        """Initialize the report generator.
        
        Args:
            report_dir: Directory to save reports (default: docs/reports/)
        """
        if report_dir is None:
            # Find project root and create reports directory
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "pyproject.toml").exists():
                    break
                current = current.parent
            self.report_dir = current / "docs" / "reports"
        else:
            self.report_dir = Path(report_dir)
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
    
    def start_session(self):
        """Mark the start of a test session."""
        self.start_time = datetime.now()
        self.test_results.clear()
    
    def add_test_result(self, 
                       test_name: str,
                       description: str,
                       result: str,
                       status: str,
                       duration: float,
                       error_message: str = "",
                       **kwargs):
        """Add a test result to the report.
        
        Args:
            test_name: Name of the test
            description: Short description of what the test does
            result: Actual result/output from the test
            status: Pass/Fail/Skip
            duration: Test duration in seconds
            error_message: Error message if test failed
            **kwargs: Additional fields to include
        """
        test_data = {
            "test_name": test_name,
            "description": description,
            "result": result,
            "status": status,
            "duration": f"{duration:.2f}s",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_message": error_message
        }
        test_data.update(kwargs)
        self.test_results.append(test_data)
    
    def generate_report(self) -> str:
        """Generate the Markdown report content.
        
        Returns:
            Markdown formatted report string
        """
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        # Report header
        report = f"""# ArXiv MCP Server Test Report

**Generated:** {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Duration:** {duration:.2f}s  
**Total Tests:** {len(self.test_results)}  
**Passed:** {sum(1 for t in self.test_results if t['status'] == 'Pass')}  
**Failed:** {sum(1 for t in self.test_results if t['status'] == 'Fail')}  
**Skipped:** {sum(1 for t in self.test_results if t['status'] == 'Skip')}

## Test Results

| Test Name | Description | Result | Status | Duration | Timestamp | Error Message |
|-----------|-------------|--------|--------|----------|-----------|---------------|
"""
        
        # Add test results to table
        for test in self.test_results:
            # Escape pipe characters in text fields
            test_name = test['test_name'].replace('|', '\\|')
            description = test['description'].replace('|', '\\|')[:50]
            result = str(test['result']).replace('|', '\\|')[:50]
            error_msg = test['error_message'].replace('|', '\\|')[:50]
            
            # Format status with emoji
            status_display = {
                'Pass': '✅ Pass',
                'Fail': '❌ Fail',
                'Skip': '⏭️ Skip'
            }.get(test['status'], test['status'])
            
            report += f"| {test_name} | {description} | {result} | {status_display} | {test['duration']} | {test['timestamp']} | {error_msg} |\n"
        
        # Add summary section
        report += f"""

## Summary

- **Success Rate:** {(sum(1 for t in self.test_results if t['status'] == 'Pass') / len(self.test_results) * 100) if self.test_results else 0:.1f}%
- **Average Test Duration:** {sum(float(t['duration'][:-1]) for t in self.test_results) / len(self.test_results) if self.test_results else 0:.2f}s

### Failed Tests
"""
        
        failed_tests = [t for t in self.test_results if t['status'] == 'Fail']
        if failed_tests:
            for test in failed_tests:
                report += f"\n- **{test['test_name']}**: {test['error_message']}"
        else:
            report += "\nNo failed tests! 🎉"
        
        return report
    
    def save_report(self, filename: Optional[str] = None) -> Path:
        """Save the report to a file.
        
        Args:
            filename: Custom filename (default: auto-generated with timestamp)
            
        Returns:
            Path to the saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.md"
        
        report_path = self.report_dir / filename
        report_content = self.generate_report()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_path


# Pytest plugin for automatic report generation
class ArxivTestReportPlugin:
    """Pytest plugin to automatically generate test reports."""
    
    def __init__(self):
        self.reporter = TestReportGenerator()
        self.test_descriptions = {}
    
    def pytest_sessionstart(self, session):
        """Called when test session starts."""
        self.reporter.start_session()
    
    def pytest_runtest_logreport(self, report: TestReport):
        """Called after each test phase."""
        if report.when == "call":  # Only capture main test execution
            # Extract test description from docstring
            test_func = report.item.function
            description = (test_func.__doc__ or "").strip().split('\n')[0] if test_func else ""
            
            # Determine result and status
            if report.passed:
                status = "Pass"
                result = "Test passed successfully"
                error_message = ""
            elif report.failed:
                status = "Fail"
                result = "Test failed"
                error_message = str(report.longrepr).split('\n')[-1] if report.longrepr else "Unknown error"
            elif report.skipped:
                status = "Skip"
                result = "Test skipped"
                error_message = str(report.longrepr) if report.longrepr else ""
            else:
                return  # Unknown status
            
            # Add test result
            self.reporter.add_test_result(
                test_name=report.nodeid.split("::")[-1],
                description=description,
                result=result,
                status=status,
                duration=report.duration,
                error_message=error_message,
                module=report.nodeid.split("::")[0]
            )
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called after test session ends."""
        if self.reporter.test_results:
            report_path = self.reporter.save_report()
            print(f"\n\n📊 Test report saved to: {report_path}")
            
            # Also print summary to console
            passed = sum(1 for t in self.reporter.test_results if t['status'] == 'Pass')
            failed = sum(1 for t in self.reporter.test_results if t['status'] == 'Fail')
            total = len(self.reporter.test_results)
            
            print(f"✅ Passed: {passed}/{total}")
            if failed > 0:
                print(f"❌ Failed: {failed}/{total}")


def pytest_configure(config):
    """Register the plugin with pytest."""
    config.pluginmanager.register(ArxivTestReportPlugin(), "arxiv_test_reporter")


# Standalone report generation for custom test runners
def generate_test_report(test_results: List[Dict[str, Any]], 
                        output_dir: Optional[Path] = None) -> Path:
    """Generate a test report from a list of test results.
    
    Args:
        test_results: List of test result dictionaries
        output_dir: Directory to save report (default: docs/reports/)
        
    Returns:
        Path to saved report file
    """
    reporter = TestReportGenerator(output_dir)
    reporter.start_session()
    
    for result in test_results:
        reporter.add_test_result(**result)
    
    return reporter.save_report()


# Validation function
if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("VALIDATING TEST REPORT GENERATOR")
    print("=" * 80)
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create reporter instance
    total_tests += 1
    print("\nTest 1: Create TestReportGenerator")
    print("-" * 40)
    
    try:
        reporter = TestReportGenerator()
        print(f"✓ Created reporter")
        print(f"✓ Report directory: {reporter.report_dir}")
        
        if not reporter.report_dir.exists():
            reporter.report_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created report directory")
    except Exception as e:
        all_validation_failures.append(f"Test 1: Failed to create reporter - {e}")
    
    # Test 2: Add test results
    total_tests += 1
    print("\nTest 2: Add test results")
    print("-" * 40)
    
    try:
        reporter.start_session()
        
        # Add sample test results
        reporter.add_test_result(
            test_name="test_search_quantum",
            description="Search for quantum computing papers",
            result="Found 5 papers",
            status="Pass",
            duration=1.23
        )
        
        reporter.add_test_result(
            test_name="test_download_paper",
            description="Download specific paper PDF",
            result="Downloaded 1706.03762.pdf",
            status="Pass",
            duration=3.45
        )
        
        reporter.add_test_result(
            test_name="test_invalid_paper",
            description="Try to download non-existent paper",
            result="404 Not Found",
            status="Fail",
            duration=0.67,
            error_message="Paper 9999.99999 does not exist"
        )
        
        print(f"✓ Added {len(reporter.test_results)} test results")
    except Exception as e:
        all_validation_failures.append(f"Test 2: Failed to add test results - {e}")
    
    # Test 3: Generate report
    total_tests += 1
    print("\nTest 3: Generate Markdown report")
    print("-" * 40)
    
    try:
        report_content = reporter.generate_report()
        
        # Verify report contains expected elements
        if "# ArXiv MCP Server Test Report" not in report_content:
            all_validation_failures.append("Test 3: Report missing title")
        elif "| Test Name | Description |" not in report_content:
            all_validation_failures.append("Test 3: Report missing table header")
        elif "test_search_quantum" not in report_content:
            all_validation_failures.append("Test 3: Report missing test results")
        else:
            print("✓ Generated report with all sections")
            print(f"✓ Report length: {len(report_content)} characters")
    except Exception as e:
        all_validation_failures.append(f"Test 3: Failed to generate report - {e}")
    
    # Test 4: Save report
    total_tests += 1
    print("\nTest 4: Save report to file")
    print("-" * 40)
    
    try:
        report_path = reporter.save_report("test_validation_report.md")
        
        if not report_path.exists():
            all_validation_failures.append("Test 4: Report file not created")
        else:
            print(f"✓ Saved report to: {report_path}")
            
            # Verify content
            with open(report_path, 'r') as f:
                saved_content = f.read()
            
            if len(saved_content) < 100:
                all_validation_failures.append("Test 4: Saved report seems too short")
            else:
                print(f"✓ Report file contains {len(saved_content)} characters")
    except Exception as e:
        all_validation_failures.append(f"Test 4: Failed to save report - {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Test report generator is working correctly!")
        sys.exit(0)