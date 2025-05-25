"""
Test ArXiv CLI
==============

Tests for the CLI interface including all commands and options.

Dependencies:
- pytest, pytest-asyncio
- typer
- click.testing
- All arxiv_mcp_server dependencies

Expected behavior:
- All CLI commands work correctly
- Proper error handling
- Correct output formatting
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typer.testing import CliRunner

from arxiv_mcp_server.cli import app


runner = CliRunner()


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_settings(temp_storage):
    """Mock settings with temp storage."""
    mock = Mock()
    mock.STORAGE_PATH = temp_storage
    return mock


@pytest.fixture
def mock_search_result():
    """Mock search result."""
    return [{
        "type": "text",
        "text": json.dumps({
            "total_results": 2,
            "papers": [
                {
                    "id": "2401.12345",
                    "title": "Test Paper 1",
                    "authors": ["Author 1"],
                    "summary": "Test summary 1"
                },
                {
                    "id": "2401.12346", 
                    "title": "Test Paper 2",
                    "authors": ["Author 2"],
                    "summary": "Test summary 2"
                }
            ]
        }, indent=2)
    }]


class TestSearchCommand:
    """Test search command."""
    
    @patch('arxiv_mcp_server.cli.handle_search')
    def test_search_basic(self, mock_handle, mock_search_result):
        """Test basic search."""
        mock_handle.return_value = asyncio.coroutine(lambda: mock_search_result)()
        
        result = runner.invoke(app, ["search", "quantum computing"])
        
        assert result.exit_code == 0
        assert "2401.12345" in result.stdout
        mock_handle.assert_called_once()
        
    @patch('arxiv_mcp_server.cli.handle_search')
    def test_search_with_options(self, mock_handle, mock_search_result):
        """Test search with options."""
        mock_handle.return_value = asyncio.coroutine(lambda: mock_search_result)()
        
        result = runner.invoke(app, [
            "search", "quantum",
            "--max-results", "5",
            "--from", "2023-01-01",
            "--category", "cs.AI"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["max_results"] == 5
        assert args["date_from"] == "2023-01-01"
        assert args["categories"] == ["cs.AI"]


class TestDownloadCommand:
    """Test download command."""
    
    @patch('arxiv_mcp_server.cli.handle_download')
    def test_download_basic(self, mock_handle):
        """Test basic download."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Downloaded successfully"}]
        )()
        
        result = runner.invoke(app, ["download", "2401.12345"])
        
        assert result.exit_code == 0
        assert "Downloaded successfully" in result.stdout
        
    @patch('arxiv_mcp_server.cli.handle_download')
    def test_download_with_options(self, mock_handle):
        """Test download with options."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Downloaded"}]
        )()
        
        result = runner.invoke(app, [
            "download", "2401.12345",
            "--converter", "marker-pdf",
            "--format", "json",
            "--keep-pdf"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["converter"] == "marker-pdf"
        assert args["output_format"] == "json"
        assert args["keep_pdf"] is True


class TestFindSupportCommand:
    """Test find-support command."""
    
    @patch('arxiv_mcp_server.cli.handle_find_research_support')
    def test_find_support_all(self, mock_handle):
        """Test find support with all papers."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "SUPPORTING EVIDENCE (5 findings)"}]
        )()
        
        result = runner.invoke(app, [
            "find-support", "My hypothesis",
            "--all"
        ])
        
        assert result.exit_code == 0
        assert "SUPPORTING EVIDENCE" in result.stdout
        args = mock_handle.call_args[0][0]
        assert args["paper_ids"] == ["all"]
        
    @patch('arxiv_mcp_server.cli.handle_find_research_support')
    def test_find_support_specific_papers(self, mock_handle):
        """Test find support with specific papers."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Results"}]
        )()
        
        result = runner.invoke(app, [
            "find-support", "My hypothesis",
            "--paper", "2401.12345",
            "--paper", "2401.12346",
            "--type", "contradict"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["paper_ids"] == ["2401.12345", "2401.12346"]
        assert args["support_type"] == "contradict"
        
    def test_find_support_no_papers_error(self):
        """Test error when no papers specified."""
        result = runner.invoke(app, ["find-support", "My hypothesis"])
        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestSearchFindingsCommand:
    """Test search-findings command."""
    
    @patch('arxiv_mcp_server.cli.handle_search_research_findings')
    def test_search_findings(self, mock_handle):
        """Test search findings."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Found 5 findings"}]
        )()
        
        result = runner.invoke(app, [
            "search-findings", "thermal",
            "--type", "bolster",
            "--top", "20"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["query"] == "thermal"
        assert args["support_type"] == "bolster"
        assert args["top_k"] == 20


class TestBatchDownloadCommand:
    """Test batch-download command."""
    
    @patch('arxiv_mcp_server.cli.handle_batch_download')
    def test_batch_download_ids(self, mock_handle):
        """Test batch download with IDs."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Downloaded 3 papers"}]
        )()
        
        result = runner.invoke(app, [
            "batch-download",
            "--id", "2401.12345",
            "--id", "2401.12346"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["paper_ids"] == ["2401.12345", "2401.12346"]
        
    @patch('arxiv_mcp_server.cli.handle_batch_download')
    def test_batch_download_search(self, mock_handle):
        """Test batch download with search."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Downloaded"}]
        )()
        
        result = runner.invoke(app, [
            "batch-download",
            "--search", "quantum computing",
            "--max", "10"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["search_query"] == "quantum computing"
        assert args["max_results"] == 10


class TestAnalysisCommands:
    """Test analysis commands."""
    
    @patch('arxiv_mcp_server.cli.handle_summarize_paper')
    def test_summarize(self, mock_handle):
        """Test summarize command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Summary of paper"}]
        )()
        
        result = runner.invoke(app, [
            "summarize", "2401.12345",
            "--strategy", "rolling_window",
            "--type", "technical"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["strategy"] == "rolling_window"
        assert args["summary_type"] == "technical"
        
    @patch('arxiv_mcp_server.cli.handle_analyze_code')
    def test_analyze_code(self, mock_handle):
        """Test analyze-code command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Found 5 code blocks"}]
        )()
        
        result = runner.invoke(app, [
            "analyze-code", "2401.12345",
            "--lang", "python",
            "--lang", "javascript",
            "--functions"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["languages"] == ["python", "javascript"]
        assert args["extract_functions"] is True


class TestNotesCommands:
    """Test notes commands."""
    
    @patch('arxiv_mcp_server.cli.handle_add_paper_note')
    def test_add_note(self, mock_handle):
        """Test add-note command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Note added"}]
        )()
        
        result = runner.invoke(app, [
            "add-note", "2401.12345", "Important finding",
            "--tag", "important",
            "--tag", "review",
            "--section", "Section 3.2"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["note"] == "Important finding"
        assert args["tags"] == ["important", "review"]
        assert args["section_ref"] == "Section 3.2"
        
    @patch('arxiv_mcp_server.cli.handle_list_paper_notes')
    def test_list_notes(self, mock_handle):
        """Test list-notes command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Found 3 notes"}]
        )()
        
        result = runner.invoke(app, [
            "list-notes",
            "--tag", "important",
            "--search", "thermal"
        ])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["tags"] == ["important"]
        assert args["search_text"] == "thermal"


class TestUtilityCommands:
    """Test utility commands."""
    
    @patch('arxiv_mcp_server.cli.handle_list_papers')
    def test_list_papers(self, mock_handle):
        """Test list-papers command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Papers list"}]
        )()
        
        result = runner.invoke(app, ["list-papers"])
        assert result.exit_code == 0
        
    @patch('arxiv_mcp_server.cli.handle_conversion_options')
    def test_conversion_options(self, mock_handle):
        """Test conversion-options command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "Converters available"}]
        )()
        
        result = runner.invoke(app, ["conversion-options"])
        assert result.exit_code == 0
        
    @patch('arxiv_mcp_server.cli.handle_system_stats')
    def test_system_stats(self, mock_handle):
        """Test system-stats command."""
        mock_handle.return_value = asyncio.coroutine(
            lambda: [{"type": "text", "text": "System stats"}]
        )()
        
        result = runner.invoke(app, ["system-stats"])
        assert result.exit_code == 0


class TestCLIValidation:
    """Test CLI validation functionality."""
    
    def test_help_command(self):
        """Test help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ArXiv MCP Server CLI" in result.stdout
        assert "search" in result.stdout
        assert "find-support" in result.stdout
        
    def test_command_help(self):
        """Test individual command help."""
        result = runner.invoke(app, ["find-support", "--help"])
        assert result.exit_code == 0
        assert "Find evidence that supports or contradicts" in result.stdout


# Validation function
if __name__ == "__main__":
    import sys
    
    def validate():
        """Validate CLI functionality."""
        all_validation_failures = []
        total_tests = 0
        
        print("=" * 80)
        print("VALIDATING CLI TESTS")
        print("=" * 80)
        
        # Test 1: Help command
        total_tests += 1
        print("\nTest 1: Help command")
        print("-" * 40)
        
        result = runner.invoke(app, ["--help"])
        if result.exit_code == 0 and "ArXiv MCP Server CLI" in result.stdout:
            print("✓ Help command working")
        else:
            all_validation_failures.append("Test 1: Help command failed")
        
        # Test 2: Command list
        total_tests += 1
        print("\nTest 2: Command availability")
        print("-" * 40)
        
        expected_commands = [
            "search", "download", "batch-download", "find-support",
            "search-findings", "summarize", "analyze-code", "add-note"
        ]
        
        help_output = result.stdout
        missing_commands = [cmd for cmd in expected_commands if cmd not in help_output]
        
        if not missing_commands:
            print("✓ All commands available")
        else:
            all_validation_failures.append(f"Test 2: Missing commands: {missing_commands}")
        
        # Test 3: Error handling
        total_tests += 1
        print("\nTest 3: Error handling")
        print("-" * 40)
        
        result = runner.invoke(app, ["find-support", "test"])
        if result.exit_code == 1 and "Error" in result.stdout:
            print("✓ Error handling working")
        else:
            all_validation_failures.append("Test 3: Error handling not working properly")
        
        # Final result
        print("\n" + "=" * 80)
        if all_validation_failures:
            print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)
        else:
            print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("CLI tests are working correctly")
            sys.exit(0)
    
    validate()