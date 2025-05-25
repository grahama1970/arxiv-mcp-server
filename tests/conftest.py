"""
CLAUDE.md Compliant Test Configuration
=====================================

This conftest provides REAL test data and fixtures.
NO MOCKS for core functionality as per CLAUDE.md standards.

Key Principles:
- Real ArXiv paper IDs
- Actual API calls
- Concrete expected results
- NO MagicMock usage
"""

import pytest
import sys
import os
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
import arxiv

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


# Real ArXiv papers for testing - these are stable, well-known papers
REAL_TEST_PAPERS = {
    "attention_paper": {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", 
                   "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", 
                   "Lukasz Kaiser", "Illia Polosukhin"],
        "year": 2017,
        "categories": ["cs.CL", "cs.LG"],
        "known_citations": ["neural machine translation", "sequence transduction"]
    },
    "bert_paper": {
        "arxiv_id": "1810.04805",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "year": 2018,
        "categories": ["cs.CL"],
        "has_code": True
    },
    "quantum_paper": {
        "arxiv_id": "1907.02540",
        "title": "Quantum supremacy using a programmable superconducting processor",
        "authors_contains": ["John M. Martinis"],
        "year": 2019,
        "categories": ["quant-ph"]
    },
    "gan_paper": {
        "arxiv_id": "1406.2661",
        "title": "Generative Adversarial Networks",
        "authors": ["Ian J. Goodfellow", "Jean Pouget-Abadie", "Mehdi Mirza",
                   "Bing Xu", "David Warde-Farley", "Sherjil Ozair",
                   "Aaron Courville", "Yoshua Bengio"],
        "year": 2014,
        "categories": ["stat.ML", "cs.LG"]
    }
}


@pytest.fixture
def real_paper_ids():
    """Provide real ArXiv paper IDs for testing."""
    return {
        "attention": "1706.03762",
        "bert": "1810.04805",
        "quantum": "1907.02540",
        "gan": "1406.2661",
        "adam": "1412.6980",  # Adam optimizer paper
        "dropout": "1207.0580",  # Dropout paper
    }


@pytest.fixture
def real_arxiv_client():
    """Create a real ArXiv client for actual API calls."""
    # Real client - no mocking
    return arxiv.Client()


@pytest.fixture
def test_search_queries():
    """Real search queries that should return results."""
    return {
        "quantum_computing": {
            "query": "quantum computing",
            "expected_keywords": ["quantum", "computing", "qubit"],
            "min_results": 10
        },
        "machine_learning": {
            "query": "machine learning",
            "expected_keywords": ["learning", "neural", "model"],
            "min_results": 20
        },
        "attention_mechanism": {
            "query": "attention mechanism transformer",
            "expected_keywords": ["attention", "transformer"],
            "min_results": 5
        }
    }


@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for paper storage during tests."""
    temp_dir = tempfile.mkdtemp(prefix="arxiv_test_")
    path = Path(temp_dir)
    
    # Create subdirectories
    (path / "pdfs").mkdir(exist_ok=True)
    (path / "metadata").mkdir(exist_ok=True)
    (path / "markdown").mkdir(exist_ok=True)
    (path / "annotations").mkdir(exist_ok=True)
    
    yield path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def expected_paper_content():
    """Expected content patterns in real papers."""
    return {
        "1706.03762": {  # Attention paper
            "contains_sections": ["Abstract", "Introduction", "Conclusion"],
            "contains_text": ["attention", "transformer", "encoder", "decoder"],
            "min_pages": 10,
            "has_equations": True,
            "has_references": True,
            "min_references": 20
        },
        "1810.04805": {  # BERT paper
            "contains_sections": ["Abstract", "Introduction", "Pre-training BERT"],
            "contains_text": ["BERT", "bidirectional", "transformer", "masked"],
            "min_pages": 10,
            "has_references": True
        }
    }


@pytest.fixture
def known_citation_counts():
    """Minimum expected citation counts for papers (will only grow)."""
    return {
        "1706.03762": 50,  # Attention paper - thousands of citations
        "1810.04805": 50,  # BERT - thousands of citations
        "1406.2661": 50,   # GAN - thousands of citations
    }


@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Set up test environment."""
    # Set test mode
    monkeypatch.setenv("ARXIV_TEST_MODE", "true")
    
    # Set storage path if not set
    if "ARXIV_STORAGE_PATH" not in os.environ:
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("ARXIV_STORAGE_PATH", tmpdir)
            yield
    else:
        yield


@pytest.fixture
def real_llm_config():
    """Configuration for real LLM testing (when API keys available)."""
    return {
        "use_mock": os.getenv("OPENAI_API_KEY") is None,
        "test_prompts": [
            "Summarize this paper in one sentence.",
            "What is the main contribution?",
            "List the key findings."
        ]
    }


# Helper functions for real data validation

def is_valid_arxiv_id(arxiv_id: str) -> bool:
    """Check if an ArXiv ID follows valid format."""
    import re
    # New format: YYMM.NNNNN
    new_format = re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', arxiv_id)
    # Old format: category/YYMMNNN
    old_format = re.match(r'^[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$', arxiv_id)
    return bool(new_format or old_format)


def is_valid_pdf(file_path: Path) -> bool:
    """Check if a file is a valid PDF."""
    if not file_path.exists():
        return False
    
    with open(file_path, 'rb') as f:
        header = f.read(4)
        return header == b'%PDF'


def has_expected_content(text: str, expected_keywords: list) -> bool:
    """Check if text contains expected keywords."""
    text_lower = text.lower()
    return all(keyword.lower() in text_lower for keyword in expected_keywords)


# Validation utilities for tests

def validate_search_results(results, min_count=1, required_keywords=None):
    """Validate search results meet expectations."""
    assert len(results) >= min_count, f"Expected at least {min_count} results, got {len(results)}"
    
    for result in results:
        assert hasattr(result, 'arxiv_id'), "Result should have arxiv_id"
        assert hasattr(result, 'title'), "Result should have title"
        assert hasattr(result, 'authors'), "Result should have authors"
        assert is_valid_arxiv_id(result.arxiv_id), f"Invalid arxiv_id: {result.arxiv_id}"
    
    if required_keywords:
        all_text = " ".join(r.title + " " + r.summary for r in results).lower()
        for keyword in required_keywords:
            assert keyword.lower() in all_text, f"Results should contain keyword: {keyword}"


def validate_paper_download(download_result, expected_size_min=10000):
    """Validate paper download result."""
    assert download_result.success is True, "Download should succeed"
    assert download_result.file_path is not None, "Should have file path"
    
    path = Path(download_result.file_path)
    assert path.exists(), f"Downloaded file should exist at {path}"
    assert path.stat().st_size >= expected_size_min, \
        f"PDF should be at least {expected_size_min} bytes"
    assert is_valid_pdf(path), "Should be a valid PDF file"


def validate_citations(citations, min_count=1):
    """Validate extracted citations."""
    assert len(citations) >= min_count, f"Expected at least {min_count} citations"
    
    for citation in citations:
        assert 'title' in citation or 'text' in citation, "Citation should have title or text"
        if 'authors' in citation:
            assert isinstance(citation['authors'], list), "Authors should be a list"
        if 'year' in citation:
            assert citation['year'].isdigit() or \
                   (len(citation['year']) == 4 and int(citation['year']) > 1900), \
                   f"Invalid year: {citation['year']}"