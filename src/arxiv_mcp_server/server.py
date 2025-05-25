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
    handle_search, handle_download, handle_list_papers, handle_read_paper, 
    handle_conversion_options, handle_describe_content, handle_system_stats, 
    handle_analyze_code, handle_summarize_paper, handle_extract_citations,
    handle_batch_download, handle_compare_paper_ideas, handle_find_similar_papers,
    handle_extract_sections, handle_add_paper_note, handle_list_paper_notes
)
from .tools import (
    search_tool, download_tool, list_tool, read_tool, conversion_options_tool, 
    describe_content_tool, system_stats_tool, analyze_code_tool, summarize_paper_tool,
    extract_citations_tool, batch_download_tool, compare_paper_ideas_tool,
    find_similar_papers_tool, extract_sections_tool, add_paper_note_tool,
    list_paper_notes_tool
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
        search_tool, download_tool, list_tool, read_tool, conversion_options_tool, 
        describe_content_tool, system_stats_tool, analyze_code_tool, summarize_paper_tool,
        extract_citations_tool, batch_download_tool, compare_paper_ideas_tool,
        find_similar_papers_tool, extract_sections_tool, add_paper_note_tool,
        list_paper_notes_tool
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for arXiv research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_papers":
            return await handle_search(arguments)
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
