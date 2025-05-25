"""
Test Paper Similarity Tool
=========================

Tests for finding similar papers by content or authors.

Dependencies:
- pytest, pytest-asyncio
- scikit-learn
- All arxiv_mcp_server dependencies

Expected behavior:
- Find similar papers by content (TF-IDF)
- Find similar papers by authors (Jaccard)
- Combined similarity scoring
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from arxiv_mcp_server.tools.paper_similarity import (
    handle_find_similar_papers,
    extract_abstract,
    compute_content_similarity,
    compute_author_similarity
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_papers():
    """Create sample papers with metadata."""
    papers = [
        {
            "id": "2401.12345",
            "content": """
# Abstract
This paper presents a novel approach to transformer architectures
using attention mechanisms for improved performance.

# Introduction
Transformers have revolutionized NLP...
""",
            "authors": ["John Doe", "Jane Smith"],
            "title": "Novel Transformer Architecture"
        },
        {
            "id": "2401.12346",
            "content": """
# Abstract
We propose an enhancement to transformer models
with focus on attention efficiency.

# Introduction
Building on previous transformer work...
""",
            "authors": ["Jane Smith", "Bob Johnson"],
            "title": "Efficient Attention Mechanisms"
        },
        {
            "id": "2401.12347",
            "content": """
# Abstract
This work explores quantum computing applications
in cryptography and security.

# Introduction
Quantum computers pose challenges...
""",
            "authors": ["Alice Chen", "Bob Johnson"],
            "title": "Quantum Cryptography"
        }
    ]
    return papers


@pytest.fixture
def mock_settings(temp_storage):
    """Mock settings."""
    mock = Mock()
    mock.STORAGE_PATH = temp_storage
    return mock


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_extract_abstract_found(self):
        """Test abstract extraction when found."""
        content = """
Some preamble text

# Abstract
This is the abstract content.
It has multiple lines.

## Introduction
This is the introduction.
"""
        abstract = extract_abstract(content)
        assert "This is the abstract content" in abstract
        assert "Introduction" not in abstract
        
    def test_extract_abstract_not_found(self):
        """Test abstract extraction fallback."""
        content = "Short paper without abstract section."
        abstract = extract_abstract(content)
        assert abstract == content  # Should return first 1000 chars
        
    def test_compute_content_similarity(self, sample_papers):
        """Test content similarity computation."""
        similarities = compute_content_similarity(sample_papers, 0)
        
        # Should find papers 0 and 1 similar (both about transformers)
        assert len(similarities) > 0
        assert similarities[0][0] == 1  # Most similar should be paper 1
        assert similarities[0][1] > 0.1  # Should have decent similarity
        
        # Paper 2 (quantum) should be less similar
        quantum_similarity = next((s for s in similarities if s[0] == 2), None)
        if quantum_similarity:
            assert quantum_similarity[1] < similarities[0][1]
            
    def test_compute_author_similarity(self, sample_papers):
        """Test author similarity computation."""
        similarities = compute_author_similarity(sample_papers, 0)
        
        # Paper 1 shares "Jane Smith" with paper 0
        assert len(similarities) > 0
        assert similarities[0][0] == 1
        assert similarities[0][1] == 1/3  # 1 shared author out of 3 total


@pytest.mark.asyncio
class TestHandler:
    """Test handler function."""
    
    async def test_find_similar_by_content(self, mock_settings, temp_storage, sample_papers):
        """Test finding similar papers by content."""
        # Create test papers
        for paper in sample_papers:
            paper_path = temp_storage / f"{paper['id']}.md"
            paper_path.write_text(paper['content'])
            
            # Create metadata
            meta_path = temp_storage / f"{paper['id']}_metadata.json"
            meta_path.write_text(json.dumps({
                "authors": paper['authors'],
                "title": paper['title']
            }))
        
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "2401.12345",
                "similarity_type": "content",
                "top_k": 2,
                "min_similarity": 0.1
            })
        
        output = result[0].text
        assert "Similar papers to 2401.12345" in output
        assert "content similarity" in output
        assert "2401.12346" in output  # Should find the other transformer paper
        
    async def test_find_similar_by_authors(self, mock_settings, temp_storage, sample_papers):
        """Test finding similar papers by authors."""
        # Create test papers
        for paper in sample_papers:
            paper_path = temp_storage / f"{paper['id']}.md"
            paper_path.write_text(paper['content'])
            
            meta_path = temp_storage / f"{paper['id']}_metadata.json"
            meta_path.write_text(json.dumps({
                "authors": paper['authors'],
                "title": paper['title']
            }))
        
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "2401.12345",
                "similarity_type": "authors",
                "top_k": 5
            })
        
        output = result[0].text
        assert "authors similarity" in output
        assert "Jane Smith" in output or "2401.12346" in output
        
    async def test_find_similar_combined(self, mock_settings, temp_storage, sample_papers):
        """Test combined similarity."""
        # Create test papers
        for paper in sample_papers:
            paper_path = temp_storage / f"{paper['id']}.md"
            paper_path.write_text(paper['content'])
            
            meta_path = temp_storage / f"{paper['id']}_metadata.json"
            meta_path.write_text(json.dumps({
                "authors": paper['authors'],
                "title": paper['title']
            }))
        
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "2401.12345",
                "similarity_type": "combined",
                "top_k": 2
            })
        
        output = result[0].text
        # Combined should still find paper 2401.12346 as most similar
        assert "2401.12346" in output
        
    async def test_paper_not_found(self, mock_settings, temp_storage):
        """Test error when paper not found."""
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "nonexistent",
                "similarity_type": "content"
            })
        
        output = result[0].text
        assert "Error:" in output
        assert "not found" in output
        
    async def test_not_enough_papers(self, mock_settings, temp_storage):
        """Test error when not enough papers."""
        # Create only one paper
        paper_path = temp_storage / "2401.12345.md"
        paper_path.write_text("Single paper content")
        
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "2401.12345",
                "similarity_type": "content"
            })
        
        output = result[0].text
        assert "Not enough papers" in output
        
    async def test_no_similar_papers_found(self, mock_settings, temp_storage):
        """Test when no papers meet similarity threshold."""
        # Create two very different papers
        papers = [
            ("2401.12345.md", "Paper about apples and fruit farming."),
            ("2401.12346.md", "Paper about quantum mechanics and physics.")
        ]
        
        for filename, content in papers:
            (temp_storage / filename).write_text(content)
        
        with patch('arxiv_mcp_server.tools.paper_similarity.settings', mock_settings):
            result = await handle_find_similar_papers({
                "paper_id": "2401.12345",
                "similarity_type": "content",
                "min_similarity": 0.9  # Very high threshold
            })
        
        output = result[0].text
        assert "No similar papers found" in output


# Validation function
if __name__ == "__main__":
    import sys
    
    async def validate():
        """Validate paper similarity functionality."""
        all_validation_failures = []
        total_tests = 0
        
        print("=" * 80)
        print("VALIDATING PAPER SIMILARITY")
        print("=" * 80)
        
        # Test 1: Abstract extraction
        total_tests += 1
        print("\nTest 1: Abstract extraction")
        print("-" * 40)
        
        try:
            content = "# Abstract\nTest abstract\n## Introduction\nTest intro"
            abstract = extract_abstract(content)
            
            if "Test abstract" in abstract and "Introduction" not in abstract:
                print("✓ Abstract extraction working")
            else:
                all_validation_failures.append("Test 1: Abstract extraction failed")
                
        except Exception as e:
            all_validation_failures.append(f"Test 1: Abstract extraction error - {str(e)}")
        
        # Test 2: Content similarity
        total_tests += 1
        print("\nTest 2: Content similarity")
        print("-" * 40)
        
        try:
            test_papers = [
                {"content": "Paper about transformers and attention"},
                {"content": "Another paper on transformer models"},
                {"content": "Paper about quantum computing"}
            ]
            
            similarities = compute_content_similarity(test_papers, 0)
            
            if len(similarities) > 0 and similarities[0][1] > 0:
                print("✓ Content similarity working")
            else:
                all_validation_failures.append("Test 2: Content similarity failed")
                
        except Exception as e:
            all_validation_failures.append(f"Test 2: Content similarity error - {str(e)}")
        
        # Test 3: Author similarity
        total_tests += 1
        print("\nTest 3: Author similarity")
        print("-" * 40)
        
        try:
            test_papers = [
                {"authors": ["John Doe", "Jane Smith"]},
                {"authors": ["Jane Smith", "Bob Johnson"]},
                {"authors": ["Alice Chen", "Bob Johnson"]}
            ]
            
            similarities = compute_author_similarity(test_papers, 0)
            
            if len(similarities) > 0 and similarities[0][0] == 1:
                print("✓ Author similarity working")
            else:
                all_validation_failures.append("Test 3: Author similarity failed")
                
        except Exception as e:
            all_validation_failures.append(f"Test 3: Author similarity error - {str(e)}")
        
        # Final result
        print("\n" + "=" * 80)
        if all_validation_failures:
            print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)
        else:
            print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Paper similarity is working correctly")
            sys.exit(0)
    
    asyncio.run(validate())