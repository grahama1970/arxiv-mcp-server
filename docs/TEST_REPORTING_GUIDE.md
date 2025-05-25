# Test Reporting Guide

## Overview

The ArXiv MCP Server includes an automated test reporting system that generates detailed Markdown reports after each test suite run. Reports are automatically saved to `docs/reports/` with comprehensive test results.

## Features

### Automatic Report Generation
- Reports are generated automatically after every full test suite run
- Each report includes detailed test results in a well-formatted table
- Reports are saved with timestamps for easy tracking

### Report Contents
Each report includes:
- **Header**: Generation timestamp, total duration, test counts
- **Results Table**: Detailed results for each test
- **Summary**: Success rate, average duration, failed test details

### Table Columns
| Column | Description |
|--------|-------------|
| Test Name | Name of the test function |
| Description | Short description from test docstring |
| Result | Actual outcome (no placeholder data) |
| Status | Pass ✅, Fail ❌, or Skip ⏭️ |
| Duration | Test execution time |
| Timestamp | When the test ran |
| Error Message | Error details for failed tests |

## Usage

### Method 1: Automatic with pytest
```bash
# The test reporter is automatically loaded via pytest.ini
pytest

# Report will be saved to docs/reports/test_report_YYYYMMDD_HHMMSS.md
```

### Method 2: Using the test runner script
```bash
# Run all tests with report
python run_tests_with_report.py

# Run specific tests with report
python run_tests_with_report.py tests/core/

# Skip slow tests
python run_tests_with_report.py -m "not slow"
```

### Method 3: Programmatic usage
```python
from arxiv_mcp_server.test_reporter import TestReportGenerator

# Create reporter
reporter = TestReportGenerator()
reporter.start_session()

# Add test results
reporter.add_test_result(
    test_name="test_search",
    description="Search for papers",
    result="Found 10 papers",
    status="Pass",
    duration=2.34
)

# Generate and save report
report_path = reporter.save_report()
```

## Example Report

```markdown
# ArXiv MCP Server Test Report

**Generated:** 2025-05-25 17:45:00  
**Total Duration:** 45.67s  
**Total Tests:** 25  
**Passed:** 23  
**Failed:** 2  
**Skipped:** 0

## Test Results

| Test Name | Description | Result | Status | Duration | Timestamp | Error Message |
|-----------|-------------|--------|--------|----------|-----------|---------------|
| test_search_quantum | Search for quantum computing papers | Found 15 papers | ✅ Pass | 2.34s | 2025-05-25 17:45:01 |  |
| test_download_bert | Download BERT paper | Downloaded 1810.04805.pdf | ✅ Pass | 5.67s | 2025-05-25 17:45:03 |  |
| test_extract_citations | Extract citations from paper | Extracted 45 citations | ✅ Pass | 1.23s | 2025-05-25 17:45:09 |  |
| test_invalid_api_key | Test with invalid API key | Authentication failed | ❌ Fail | 0.45s | 2025-05-25 17:45:10 | Invalid API key |

## Summary

- **Success Rate:** 92.0%
- **Average Test Duration:** 1.83s

### Failed Tests

- **test_invalid_api_key**: Invalid API key
- **test_network_timeout**: Request timed out
```

## Configuration

### pytest.ini Configuration
The test reporter is automatically loaded via the pytest configuration:
```ini
addopts = 
    -v
    --tb=short
    --strict-markers
    -p arxiv_mcp_server.test_reporter
```

### Custom Report Directory
```python
# Use custom directory
reporter = TestReportGenerator(report_dir=Path("/custom/reports"))
```

## Best Practices

### 1. Write Descriptive Docstrings
```python
def test_search_by_author():
    """Search ArXiv for papers by specific author."""
    # Test implementation
```

### 2. Return Meaningful Results
Instead of generic pass/fail, provide specific results:
```python
# Good
result = "Found 15 papers, 12 with quantum in title"

# Not as helpful
result = "Test passed"
```

### 3. Include Error Context
For failures, provide helpful error messages:
```python
error_message = f"Expected at least 5 results, got {len(results)}"
```

### 4. Use Test Markers
Mark tests for better organization:
```python
@pytest.mark.real_api
@pytest.mark.slow
def test_large_batch_download():
    """Download 50 papers in batch."""
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Tests with Report
  run: |
    python run_tests_with_report.py
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: docs/reports/*.md
```

### GitLab CI Example
```yaml
test:
  script:
    - python run_tests_with_report.py
  artifacts:
    paths:
      - docs/reports/
    expire_in: 1 week
```

## Viewing Reports

### Local Development
```bash
# List all reports
ls -la docs/reports/

# View latest report
cat docs/reports/test_report_*.md | tail -1

# Open in editor
code docs/reports/test_report_20250525_174500.md
```

### Markdown Preview
Reports are in standard Markdown format and can be:
- Viewed in any Markdown editor
- Rendered in GitHub/GitLab
- Converted to HTML/PDF
- Imported into documentation systems

## Troubleshooting

### Report Not Generated
1. Check that `pytest.ini` includes the plugin
2. Verify `docs/reports/` directory exists
3. Ensure tests actually ran (not all skipped)

### Missing Test Details
- Add docstrings to test functions
- Ensure test names are descriptive
- Check that results are captured properly

### Permission Errors
```bash
# Ensure reports directory is writable
chmod -R u+w docs/reports/
```

## CLAUDE.md Compliance

This test reporting system follows CLAUDE.md standards:
- Uses REAL test results, no placeholders
- Reports actual outcomes from test execution
- No mocking of test results
- Validates actual functionality

## Summary

The automated test reporting system provides:
- ✅ Automatic report generation after each test run
- ✅ Detailed results in Markdown format
- ✅ Real test data (no hallucination)
- ✅ Easy integration with CI/CD
- ✅ Historical test tracking in `docs/reports/`

Reports help track test suite health, identify flaky tests, and provide documentation of test coverage and results.