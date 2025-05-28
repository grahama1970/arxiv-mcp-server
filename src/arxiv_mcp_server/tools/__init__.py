"""Tool definitions for the arXiv MCP server."""

from .search import search_tool, handle_search, diagnostics_tool, handle_diagnostics
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
    "diagnostics_tool",
    "download_tool",
    "read_tool",
    "handle_search",
    "handle_diagnostics",
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

# Semantic search tools
from .semantic_search import (
    semantic_search_tool,
    handle_semantic_search,
    index_papers_tool,
    handle_index_papers,
    search_stats_tool,
    handle_search_stats,
)

# Reading list tools
from .reading_list import (
    add_to_reading_list_tool,
    get_reading_list_tool,
    mark_as_read_tool,
    remove_from_reading_list_tool,
    handle_add_to_reading_list,
    handle_get_reading_list,
    handle_mark_as_read,
    handle_remove_from_reading_list,
)

# Daily digest tools
from .daily_digest import (
    create_digest_subscription_tool,
    get_daily_digest_tool,
    list_digest_subscriptions_tool,
    delete_digest_subscription_tool,
    handle_create_digest_subscription,
    handle_get_daily_digest,
    handle_list_digest_subscriptions,
    handle_delete_digest_subscription,
)

# Citation tracking tools
from .citation_tracking import (
    get_citations_tool,
    get_references_tool,
    get_citation_graph_tool,
    handle_get_citations,
    handle_get_references,
    handle_get_citation_graph,
)

# Export/reference tools
from .export_references import (
    export_to_bibtex_tool,
    export_reading_list_tool,
    format_citation_tool,
    handle_export_to_bibtex,
    handle_export_reading_list,
    handle_format_citation,
)

# Paper updates tools
from .paper_updates import (
    check_paper_updates_tool,
    handle_check_paper_updates,
)

# Author following tools
from .author_follow import (
    follow_author_tool,
    unfollow_author_tool,
    list_followed_authors_tool,
    check_followed_authors_tool,
    handle_follow_author,
    handle_unfollow_author,
    handle_list_followed_authors,
    handle_check_followed_authors,
)

# Quick citation tools
from .quick_cite import (
    copy_citation_tool,
    format_multiple_citations_tool,
    handle_copy_citation,
    handle_format_multiple_citations,
)

# Search template tools
from .search_templates import (
    save_search_template_tool,
    run_search_template_tool,
    list_search_templates_tool,
    handle_save_search_template,
    handle_run_search_template,
    handle_list_search_templates,
)

# Paper collection tools
from .paper_collections import (
    create_collection_tool,
    add_to_collection_tool,
    get_collection_tool,
    list_collections_tool,
    handle_create_collection,
    handle_add_to_collection,
    handle_get_collection,
    handle_list_collections,
)

# Update __all__ list
__all__.extend([
    "semantic_search_tool",
    "handle_semantic_search", 
    "index_papers_tool",
    "handle_index_papers",
    "search_stats_tool",
    "handle_search_stats",
    # Reading list
    "add_to_reading_list_tool",
    "get_reading_list_tool",
    "mark_as_read_tool",
    "remove_from_reading_list_tool",
    "handle_add_to_reading_list",
    "handle_get_reading_list",
    "handle_mark_as_read",
    "handle_remove_from_reading_list",
    # Daily digest
    "create_digest_subscription_tool",
    "get_daily_digest_tool",
    "list_digest_subscriptions_tool",
    "delete_digest_subscription_tool",
    "handle_create_digest_subscription",
    "handle_get_daily_digest",
    "handle_list_digest_subscriptions",
    "handle_delete_digest_subscription",
    # Citation tracking
    "get_citations_tool",
    "get_references_tool",
    "get_citation_graph_tool",
    "handle_get_citations",
    "handle_get_references",
    "handle_get_citation_graph",
    # Export/references
    "export_to_bibtex_tool",
    "export_reading_list_tool",
    "format_citation_tool",
    "handle_export_to_bibtex",
    "handle_export_reading_list",
    "handle_format_citation",
    # Paper updates
    "check_paper_updates_tool",
    "handle_check_paper_updates",
    # Author following
    "follow_author_tool",
    "unfollow_author_tool",
    "list_followed_authors_tool",
    "check_followed_authors_tool",
    "handle_follow_author",
    "handle_unfollow_author",
    "handle_list_followed_authors",
    "handle_check_followed_authors",
    # Quick citations
    "copy_citation_tool",
    "format_multiple_citations_tool",
    "handle_copy_citation",
    "handle_format_multiple_citations",
    # Search templates
    "save_search_template_tool",
    "run_search_template_tool",
    "list_search_templates_tool",
    "handle_save_search_template",
    "handle_run_search_template",
    "handle_list_search_templates",
    # Paper collections
    "create_collection_tool",
    "add_to_collection_tool",
    "get_collection_tool",
    "list_collections_tool",
    "handle_create_collection",
    "handle_add_to_collection",
    "handle_get_collection",
    "handle_list_collections",
])