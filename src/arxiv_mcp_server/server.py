"""
Arxiv MCP Server
===============

This module implements an MCP server for interacting with arXiv.
"""

import logging
import mcp.types as types
from typing import Dict, Any, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.stdio import stdio_server
from .config import Settings
from .tools import (
    handle_search, handle_diagnostics, handle_download, handle_list_papers, handle_read_paper, 
    handle_conversion_options, handle_describe_content, handle_system_stats, 
    handle_analyze_code, handle_summarize_paper, handle_extract_citations,
    handle_batch_download, handle_compare_paper_ideas, handle_find_similar_papers,
    handle_extract_sections, handle_add_paper_note, handle_list_paper_notes,
    handle_find_research_support, handle_search_research_findings, handle_semantic_search, handle_index_papers, handle_search_stats,
    # New handlers
    handle_add_to_reading_list, handle_get_reading_list, handle_mark_as_read, handle_remove_from_reading_list,
    handle_create_digest_subscription, handle_get_daily_digest, handle_list_digest_subscriptions, handle_delete_digest_subscription,
    handle_get_citations, handle_get_references, handle_get_citation_graph,
    handle_export_to_bibtex, handle_export_reading_list, handle_format_citation,
    # Additional daily workflow handlers
    handle_check_paper_updates, handle_follow_author, handle_unfollow_author, 
    handle_list_followed_authors, handle_check_followed_authors, handle_copy_citation,
    handle_format_multiple_citations, handle_save_search_template, handle_run_search_template,
    handle_list_search_templates, handle_create_collection, handle_add_to_collection,
    handle_get_collection, handle_list_collections
)
from .tools import (
    search_tool, diagnostics_tool, download_tool, list_tool, read_tool, conversion_options_tool, 
    describe_content_tool, system_stats_tool, analyze_code_tool, summarize_paper_tool,
    extract_citations_tool, batch_download_tool, compare_paper_ideas_tool,
    find_similar_papers_tool, extract_sections_tool, add_paper_note_tool,
    list_paper_notes_tool, find_research_support_tool, search_research_findings_tool, semantic_search_tool, index_papers_tool, search_stats_tool,
    # New tools
    add_to_reading_list_tool, get_reading_list_tool, mark_as_read_tool, remove_from_reading_list_tool,
    create_digest_subscription_tool, get_daily_digest_tool, list_digest_subscriptions_tool, delete_digest_subscription_tool,
    get_citations_tool, get_references_tool, get_citation_graph_tool,
    export_to_bibtex_tool, export_reading_list_tool, format_citation_tool,
    # Additional daily workflow tools
    check_paper_updates_tool, follow_author_tool, unfollow_author_tool, list_followed_authors_tool,
    check_followed_authors_tool, copy_citation_tool, format_multiple_citations_tool,
    save_search_template_tool, run_search_template_tool, list_search_templates_tool,
    create_collection_tool, add_to_collection_tool, get_collection_tool, list_collections_tool
)
from .prompts.handlers import list_prompts as handler_list_prompts
from .prompts.handlers import get_prompt as handler_get_prompt

settings = Settings()
logger = logging.getLogger("arxiv-mcp-server")
logger.setLevel(logging.INFO)
server = Server(settings.APP_NAME)


@server.list_prompts()
async def list_prompts() -> List[types.Prompt]:
    """List available prompts."""
    return await handler_list_prompts()


@server.get_prompt()
async def get_prompt(
    name: str, arguments: Dict[str, str] | None = None
) -> types.GetPromptResult:
    """Get a specific prompt with arguments."""
    return await handler_get_prompt(name, arguments)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available arXiv research tools."""
    return [
        search_tool, diagnostics_tool, download_tool, list_tool, read_tool, conversion_options_tool, 
        describe_content_tool, system_stats_tool, analyze_code_tool, summarize_paper_tool,
        extract_citations_tool, batch_download_tool, compare_paper_ideas_tool,
        find_similar_papers_tool, extract_sections_tool, add_paper_note_tool,
        list_paper_notes_tool, find_research_support_tool, search_research_findings_tool, semantic_search_tool, index_papers_tool, search_stats_tool,
        # New tools
        add_to_reading_list_tool, get_reading_list_tool, mark_as_read_tool, remove_from_reading_list_tool,
        create_digest_subscription_tool, get_daily_digest_tool, list_digest_subscriptions_tool, delete_digest_subscription_tool,
        get_citations_tool, get_references_tool, get_citation_graph_tool,
        export_to_bibtex_tool, export_reading_list_tool, format_citation_tool,
        # Additional daily workflow tools
        check_paper_updates_tool, follow_author_tool, unfollow_author_tool, list_followed_authors_tool,
        check_followed_authors_tool, copy_citation_tool, format_multiple_citations_tool,
        save_search_template_tool, run_search_template_tool, list_search_templates_tool,
        create_collection_tool, add_to_collection_tool, get_collection_tool, list_collections_tool
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for arXiv research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_papers":
            return await handle_search(arguments)
        elif name == "get_diagnostics":
            return await handle_diagnostics(arguments)
        elif name == "download_paper":
            return await handle_download(arguments)
        elif name == "list_papers":
            return await handle_list_papers(arguments)
        elif name == "read_paper":
            return await handle_read_paper(arguments)
        elif name == "get_conversion_options":
            return await handle_conversion_options(arguments)
        elif name == "describe_paper_content":
            return await handle_describe_content(arguments)
        elif name == "get_system_stats":
            return await handle_system_stats(arguments)
        elif name == "analyze_paper_code":
            return await handle_analyze_code(arguments)
        elif name == "summarize_paper":
            return await handle_summarize_paper(arguments)
        elif name == "extract_citations":
            return await handle_extract_citations(arguments)
        elif name == "batch_download":
            return await handle_batch_download(arguments)
        elif name == "compare_paper_ideas":
            return await handle_compare_paper_ideas(arguments)
        elif name == "find_similar_papers":
            return await handle_find_similar_papers(arguments)
        elif name == "extract_sections":
            return await handle_extract_sections(arguments)
        elif name == "add_paper_note":
            return await handle_add_paper_note(arguments)
        elif name == "list_paper_notes":
            return await handle_list_paper_notes(arguments)
        elif name == "find_research_support":
            return await handle_find_research_support(arguments)
        elif name == "search_research_findings":
            return await handle_search_research_findings(arguments)
        elif name == "semantic_search":
            return await handle_semantic_search(arguments)
        elif name == "index_papers":
            return await handle_index_papers(arguments)
        elif name == "search_stats":
            return await handle_search_stats(arguments)
        # Reading list tools
        elif name == "add_to_reading_list":
            return await handle_add_to_reading_list(arguments)
        elif name == "get_reading_list":
            return await handle_get_reading_list(arguments)
        elif name == "mark_paper_as_read":
            return await handle_mark_as_read(arguments)
        elif name == "remove_from_reading_list":
            return await handle_remove_from_reading_list(arguments)
        # Daily digest tools
        elif name == "create_digest_subscription":
            return await handle_create_digest_subscription(arguments)
        elif name == "get_daily_digest":
            return await handle_get_daily_digest(arguments)
        elif name == "list_digest_subscriptions":
            return await handle_list_digest_subscriptions(arguments)
        elif name == "delete_digest_subscription":
            return await handle_delete_digest_subscription(arguments)
        # Citation tracking tools
        elif name == "get_citations":
            return await handle_get_citations(arguments)
        elif name == "get_references":
            return await handle_get_references(arguments)
        elif name == "get_citation_graph":
            return await handle_get_citation_graph(arguments)
        # Export tools
        elif name == "export_to_bibtex":
            return await handle_export_to_bibtex(arguments)
        elif name == "export_reading_list":
            return await handle_export_reading_list(arguments)
        elif name == "format_citation":
            return await handle_format_citation(arguments)
        # Additional daily workflow tools
        elif name == "check_paper_updates":
            return await handle_check_paper_updates(arguments)
        elif name == "follow_author":
            return await handle_follow_author(arguments)
        elif name == "unfollow_author":
            return await handle_unfollow_author(arguments)
        elif name == "list_followed_authors":
            return await handle_list_followed_authors(arguments)
        elif name == "check_followed_authors":
            return await handle_check_followed_authors(arguments)
        elif name == "copy_citation":
            return await handle_copy_citation(arguments)
        elif name == "format_multiple_citations":
            return await handle_format_multiple_citations(arguments)
        elif name == "save_search_template":
            return await handle_save_search_template(arguments)
        elif name == "run_search_template":
            return await handle_run_search_template(arguments)
        elif name == "list_search_templates":
            return await handle_list_search_templates(arguments)
        elif name == "create_collection":
            return await handle_create_collection(arguments)
        elif name == "add_to_collection":
            return await handle_add_to_collection(arguments)
        elif name == "get_collection":
            return await handle_get_collection(arguments)
        elif name == "list_collections":
            return await handle_list_collections(arguments)
        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool {name}")]
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.APP_NAME,
                server_version=settings.APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
