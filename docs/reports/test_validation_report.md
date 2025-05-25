# ArXiv MCP Server Test Report

**Generated:** 2025-05-25 17:48:56  
**Total Duration:** 0.00s  
**Total Tests:** 3  
**Passed:** 2  
**Failed:** 1  
**Skipped:** 0

## Test Results

| Test Name | Description | Result | Status | Duration | Timestamp | Error Message |
|-----------|-------------|--------|--------|----------|-----------|---------------|
| test_search_quantum | Search for quantum computing papers | Found 5 papers | ✅ Pass | 1.23s | 2025-05-25 17:48:56 |  |
| test_download_paper | Download specific paper PDF | Downloaded 1706.03762.pdf | ✅ Pass | 3.45s | 2025-05-25 17:48:56 |  |
| test_invalid_paper | Try to download non-existent paper | 404 Not Found | ❌ Fail | 0.67s | 2025-05-25 17:48:56 | Paper 9999.99999 does not exist |


## Summary

- **Success Rate:** 66.7%
- **Average Test Duration:** 1.78s

### Failed Tests

- **test_invalid_paper**: Paper 9999.99999 does not exist