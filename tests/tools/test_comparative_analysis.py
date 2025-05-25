"""
Test Comparative Analysis Tool
==============================

Tests for the paper comparison functionality.

Dependencies:
- pytest, pytest-asyncio
- All arxiv_mcp_server dependencies

Expected behavior:
- Compare papers against research context
- Mock LLM provider returns appropriate results
- Error handling for missing papers
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from arxiv_mcp_server.tools.comparative_analysis import (
    handle_compare_paper_ideas,
    LLMAnalyzer,
    MockLLMProvider
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_paper():
    """Sample paper content."""
    return """
# Abstract
This paper presents a novel approach to quantum computing using topological qubits.
Our method achieves error rates below 0.1% through advanced error correction.

# Introduction
Previous quantum computing approaches have struggled with decoherence.
We propose using topological protection to maintain quantum states.

# Methods
We implemented a surface code with 99 physical qubits to protect 1 logical qubit.
The system operates at 20mK with coherence times exceeding 100 microseconds.

# Results
Our experiments demonstrate:
- Error rates of 0.08% per gate operation
- Coherence times of 120 microseconds
- Successful implementation of Shor's algorithm on 5-bit numbers

# Conclusion
Topological quantum computing provides a viable path to fault-tolerant quantum computation.
"""


@pytest.fixture
def mock_settings(temp_storage):
    """Mock settings."""
    mock = Mock()
    mock.STORAGE_PATH = temp_storage
    return mock


class TestMockLLMProvider:
    """Test mock LLM provider."""
    
    @pytest.mark.asyncio
    async def test_mock_analysis(self):
        """Test mock provider returns expected structure."""
        provider = MockLLMProvider()
        result = await provider.analyze(
            "paper content",
            "research context",
            "comprehensive",
            ["efficiency", "scalability"]
        )
        
        assert "better_ideas" in result
        assert "worse_ideas" in result
        assert "contradictions" in result
        assert "unique_insights" in result
        assert "recommendations" in result
        assert "confidence_score" in result
        
        assert isinstance(result["better_ideas"], list)
        assert isinstance(result["confidence_score"], float)


class TestLLMAnalyzer:
    """Test LLM analyzer."""
    
    @pytest.mark.asyncio
    async def test_analyze_with_mock(self):
        """Test analysis with mock provider."""
        analyzer = LLMAnalyzer("mock")
        result = await analyzer.analyze(
            "paper about quantum computing",
            "my quantum algorithm",
            "technical",
            ["performance"]
        )
        
        assert "better_ideas" in result
        assert len(result["better_ideas"]) > 0
        
    @pytest.mark.asyncio
    async def test_analyze_with_real_provider_no_key(self):
        """Test real provider without API key."""
        analyzer = LLMAnalyzer("openai")
        result = await analyzer.analyze(
            "paper content",
            "research context",
            "comprehensive",
            []
        )
        
        assert "error" in result
        assert "API key" in result["error"]
        
    def test_build_prompt(self):
        """Test prompt building."""
        analyzer = LLMAnalyzer("mock")
        prompt = analyzer._build_prompt(
            "Paper about AI",
            "My AI research",
            "technical",
            ["efficiency", "accuracy"]
        )
        
        assert "My AI research" in prompt
        assert "Paper about AI" in prompt
        assert "technical" in prompt
        assert "efficiency, accuracy" in prompt


@pytest.mark.asyncio
class TestHandler:
    """Test handler function."""
    
    async def test_handle_compare_success(self, mock_settings, temp_storage, sample_paper):
        """Test successful comparison."""
        # Create test paper
        paper_path = temp_storage / "2401.12345.md"
        paper_path.write_text(sample_paper)
        
        with patch('arxiv_mcp_server.tools.comparative_analysis.settings', mock_settings):
            result = await handle_compare_paper_ideas({
                "paper_id": "2401.12345",
                "research_context": "My quantum computing approach uses trapped ions",
                "comparison_type": "comprehensive",
                "llm_provider": "mock"
            })
        
        output = result[0].text
        assert "Comparative Analysis: 2401.12345" in output
        assert "BETTER IDEAS IN PAPER:" in output
        assert "WORSE IDEAS/LIMITATIONS:" in output
        assert "CONTRADICTIONS:" in output
        assert "UNIQUE INSIGHTS:" in output
        assert "RECOMMENDATIONS:" in output
        assert "Confidence Score:" in output
        
    async def test_handle_compare_with_focus_areas(self, mock_settings, temp_storage, sample_paper):
        """Test comparison with focus areas."""
        paper_path = temp_storage / "2401.12345.md"
        paper_path.write_text(sample_paper)
        
        with patch('arxiv_mcp_server.tools.comparative_analysis.settings', mock_settings):
            result = await handle_compare_paper_ideas({
                "paper_id": "2401.12345",
                "research_context": "Quantum error correction",
                "comparison_type": "technical",
                "llm_provider": "mock",
                "focus_areas": ["error_rates", "coherence", "scalability"]
            })
        
        output = result[0].text
        assert "Comparison Type: technical" in output
        
    async def test_handle_compare_missing_paper(self, mock_settings, temp_storage):
        """Test error when paper not found."""
        with patch('arxiv_mcp_server.tools.comparative_analysis.settings', mock_settings):
            result = await handle_compare_paper_ideas({
                "paper_id": "nonexistent",
                "research_context": "Test context",
                "llm_provider": "mock"
            })
        
        output = result[0].text
        assert "Error:" in output
        assert "not found" in output
        
    async def test_handle_compare_api_error(self, mock_settings, temp_storage, sample_paper):
        """Test handling of API errors."""
        paper_path = temp_storage / "2401.12345.md"
        paper_path.write_text(sample_paper)
        
        with patch('arxiv_mcp_server.tools.comparative_analysis.settings', mock_settings):
            result = await handle_compare_paper_ideas({
                "paper_id": "2401.12345",
                "research_context": "Test",
                "llm_provider": "openai"  # Will fail without API key
            })
        
        output = result[0].text
        assert "Error:" in output
        assert "Suggestion:" in output


# Validation function
if __name__ == "__main__":
    import sys
    
    async def validate():
        """Validate comparative analysis functionality."""
        all_validation_failures = []
        total_tests = 0
        
        print("=" * 80)
        print("VALIDATING COMPARATIVE ANALYSIS")
        print("=" * 80)
        
        # Test 1: Mock provider
        total_tests += 1
        print("\nTest 1: Mock LLM provider")
        print("-" * 40)
        
        try:
            provider = MockLLMProvider()
            result = await provider.analyze("content", "context", "comprehensive", [])
            
            if all(key in result for key in ["better_ideas", "worse_ideas", "contradictions"]):
                print("✓ Mock provider working")
            else:
                all_validation_failures.append("Test 1: Mock provider missing keys")
                
        except Exception as e:
            all_validation_failures.append(f"Test 1: Mock provider error - {str(e)}")
        
        # Test 2: LLM analyzer
        total_tests += 1
        print("\nTest 2: LLM analyzer")
        print("-" * 40)
        
        try:
            analyzer = LLMAnalyzer("mock")
            result = await analyzer.analyze("paper", "research", "technical", [])
            
            if "better_ideas" in result and len(result["better_ideas"]) > 0:
                print("✓ LLM analyzer working")
            else:
                all_validation_failures.append("Test 2: LLM analyzer no results")
                
        except Exception as e:
            all_validation_failures.append(f"Test 2: LLM analyzer error - {str(e)}")
        
        # Test 3: Error handling
        total_tests += 1
        print("\nTest 3: Error handling")
        print("-" * 40)
        
        try:
            temp_dir = tempfile.mkdtemp()
            mock_settings = Mock()
            mock_settings.STORAGE_PATH = Path(temp_dir)
            
            with patch('arxiv_mcp_server.tools.comparative_analysis.settings', mock_settings):
                result = await handle_compare_paper_ideas({
                    "paper_id": "nonexistent",
                    "research_context": "Test",
                    "llm_provider": "mock"
                })
            
            output = result[0].text
            if "Error:" in output and "not found" in output:
                print("✓ Error handling working")
            else:
                all_validation_failures.append("Test 3: Missing paper error not handled")
                
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            all_validation_failures.append(f"Test 3: Error handling failed - {str(e)}")
        
        # Final result
        print("\n" + "=" * 80)
        if all_validation_failures:
            print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)
        else:
            print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Comparative analysis is working correctly")
            sys.exit(0)
    
    asyncio.run(validate())