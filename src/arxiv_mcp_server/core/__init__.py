"""
ArXiv MCP Server Core Layer
===========================

Pure business logic for ArXiv paper operations.
No MCP or CLI dependencies - just core functionality.
"""

from .search import search_papers, format_search_results
from .download import DownloadManager, download_and_check_paper, ConversionStatus, PaperStatus
from .utils import (
    normalize_paper_id,
    validate_paper_id,
    get_file_hash,
    ensure_storage_path,
    load_json_file,
    save_json_file,
    truncate_text,
    format_file_size,
    parse_date_safely,
    extract_arxiv_id_from_path
)

__all__ = [
    # Search functions
    "search_papers",
    "format_search_results",
    
    # Download functions
    "DownloadManager",
    "download_and_check_paper",
    "ConversionStatus",
    "PaperStatus",
    
    # Utility functions
    "normalize_paper_id",
    "validate_paper_id", 
    "get_file_hash",
    "ensure_storage_path",
    "load_json_file",
    "save_json_file",
    "truncate_text",
    "format_file_size",
    "parse_date_safely",
    "extract_arxiv_id_from_path",
]