# ArXiv MCP Server Test Suite

This directory contains the comprehensive test suite for the ArXiv MCP Server project.

## 🚀 Quick Start

### Run All Tests
```bash
# From project root
cd /home/graham/workspace/mcp-servers/arxiv-mcp-server
export PYTHONPATH=/home/graham/workspace/mcp-servers/arxiv-mcp-server/src
uv run pytest tests/ -v
```

### Run Tests with Coverage
```bash
uv run pytest tests/ --cov=arxiv_mcp_server --cov-report=html
# View coverage report in htmlcov/index.html
```

## 📁 Test Structure

```
tests/
├── conftest.py              # Root test configuration and fixtures
├── test_cli.py              # CLI command tests
├── test_config.py           # Configuration tests
├── test_mcp_basic.py        # Basic MCP server integration test
├── prompts/                 # Prompt-related tests
│   ├── conftest.py          # Prompt test fixtures
│   ├── test_prompts.py      # Prompt functionality tests
│   └── test_prompt_integration.py  # Server prompt integration
└── tools/                   # Tool-specific tests
    ├── test_comparative_analysis.py  # Paper comparison tool
    ├── test_download.py              # Paper download functionality
    ├── test_paper_similarity.py      # Similar paper finder
    ├── test_research_support.py      # Bolster/contradict features
    └── test_search.py                # ArXiv search functionality
```

## 🧪 Running Specific Test Categories

### Run Only Tool Tests
```bash
uv run pytest tests/tools/ -v
```

### Run Only CLI Tests
```bash
uv run pytest tests/test_cli.py -v
```

### Run Only Prompt Tests
```bash
uv run pytest tests/prompts/ -v
```

### Run a Single Test File
```bash
uv run pytest tests/tools/test_research_support.py -v
```

### Run a Single Test Function
```bash
uv run pytest tests/tools/test_research_support.py::TestResearchSupportDB::test_add_finding -v
```

## 🔍 Test Options

### Verbose Output
```bash
uv run pytest tests/ -v              # Verbose test names
uv run pytest tests/ -vv             # Very verbose (shows assertions)
```

### Show Print Statements
```bash
uv run pytest tests/ -v -s           # Capture disabled (shows prints)
```

### Stop on First Failure
```bash
uv run pytest tests/ -x              # Stop after first failure
uv run pytest tests/ --maxfail=3     # Stop after 3 failures
```

### Run Tests Matching Pattern
```bash
uv run pytest tests/ -k "search"     # Run tests with "search" in name
uv run pytest tests/ -k "not slow"   # Skip tests marked as slow
```

## 📊 Test Coverage

### Generate Coverage Report
```bash
# Terminal report
uv run pytest tests/ --cov=arxiv_mcp_server

# HTML report
uv run pytest tests/ --cov=arxiv_mcp_server --cov-report=html

# XML report (for CI/CD)
uv run pytest tests/ --cov=arxiv_mcp_server --cov-report=xml
```

### Coverage Goals
- Minimum overall coverage: 70%
- Critical paths (handlers, core tools): 80%+
- New features must include tests

## ⚠️ Common Issues and Solutions

### Import Errors
```bash
# Always set PYTHONPATH before running tests
export PYTHONPATH=/home/graham/workspace/mcp-servers/arxiv-mcp-server/src
```

### Asyncio Warnings
- The `asyncio.coroutine` deprecation warnings are from older test patterns
- These are being migrated to modern `async def` syntax

### Test Failures
1. **Search tests failing**: Check if mock data matches expected format
2. **CLI tests failing**: Ensure all handlers are properly registered
3. **Similarity tests failing**: Verify threshold values match implementation

## 🛠️ Writing New Tests

### Test File Naming
- Test files must start with `test_`
- Place in appropriate subdirectory (tools/, prompts/, etc.)

### Test Structure Example
```python
import pytest
from arxiv_mcp_server.tools.your_tool import your_function

class TestYourFeature:
    """Test suite for your feature."""
    
    def test_basic_functionality(self):
        """Test basic happy path."""
        result = your_function("input")
        assert result == "expected"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async operations."""
        result = await your_async_function()
        assert result is not None
```

### Using Fixtures
```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## 🔄 Continuous Integration

Before pushing changes:

1. **Run all tests**:
   ```bash
   uv run pytest tests/
   ```

2. **Check coverage**:
   ```bash
   uv run pytest tests/ --cov=arxiv_mcp_server
   ```

3. **Run linting** (if configured):
   ```bash
   uv run ruff check src/
   ```

## 📝 Test Categories

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution

### Integration Tests
- Test tool handlers end-to-end
- Use real mock providers (not MagicMock)
- Verify MCP protocol compliance

### CLI Tests
- Test command parsing
- Verify output formatting
- Check error handling

## 🚨 Important Notes

1. **No Mocking Core Functionality**: Following CLAUDE.md standards, tests use real implementations with mock data providers
2. **Real Data**: Tests use realistic sample data, not dummy values
3. **Async Testing**: Use `@pytest.mark.asyncio` for async tests
4. **Temp Files**: Tests create temp directories for file operations

## 🐛 Debugging Tests

### Run with Python Debugger
```bash
uv run pytest tests/test_file.py -v --pdb
```

### Show Full Diffs
```bash
uv run pytest tests/ -vv
```

### Capture Logs
```bash
uv run pytest tests/ --log-cli-level=DEBUG
```

## 📅 Maintenance

- Review and update tests when adding new features
- Remove obsolete tests when removing features
- Keep test data realistic and up-to-date
- Ensure all tests pass before merging PRs

---

For more information about the project structure and development guidelines, see [CLAUDE.md](../CLAUDE.md)