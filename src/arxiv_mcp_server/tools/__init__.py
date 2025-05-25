"""Tool definitions for the arXiv MCP server."""

from .search import search_tool, handle_search
from .download import download_tool, handle_download
from .list_papers import list_tool, handle_list_papers
from .read_paper import read_tool, handle_read_paper
from .conversion_options import conversion_options_tool, handle_conversion_options
from .describe_content import describe_content_tool, handle_describe_content
from .system_stats import system_stats_tool, handle_system_stats
from .analyze_code import analyze_code_tool, handle_analyze_code
from .summarize_paper import summarize_paper_tool, handle_summarize_paper
from .extract_citations import extract_citations_tool, handle_extract_citations
from .batch_operations import batch_download_tool, handle_batch_download
from .comparative_analysis import compare_paper_ideas_tool, handle_compare_paper_ideas
from .paper_similarity import find_similar_papers_tool, handle_find_similar_papers
from .extract_sections import extract_sections_tool, handle_extract_sections
from .annotations import (
    add_paper_note_tool, 
    list_paper_notes_tool,
    handle_add_paper_note,
    handle_list_paper_notes
)
from .research_support import (
    find_research_support_tool,
    search_research_findings_tool,
    handle_find_research_support,
    handle_search_research_findings
)


__all__ = [
    "search_tool",
    "download_tool",
    "read_tool",
    "handle_search",
    "handle_download",
    "handle_read_paper",
    "list_tool",
    "handle_list_papers",
    "conversion_options_tool",
    "handle_conversion_options",
    "describe_content_tool",
    "handle_describe_content",
    "system_stats_tool",
    "handle_system_stats",
    "analyze_code_tool",
    "handle_analyze_code",
    "summarize_paper_tool",
    "handle_summarize_paper",
    "extract_citations_tool",
    "handle_extract_citations",
    "batch_download_tool",
    "handle_batch_download",
    "compare_paper_ideas_tool",
    "handle_compare_paper_ideas",
    "find_similar_papers_tool",
    "handle_find_similar_papers",
    "extract_sections_tool",
    "handle_extract_sections",
    "add_paper_note_tool",
    "handle_add_paper_note",
    "list_paper_notes_tool",
    "handle_list_paper_notes",
    "find_research_support_tool",
    "handle_find_research_support",
    "search_research_findings_tool",
    "handle_search_research_findings",
]
