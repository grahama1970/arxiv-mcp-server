"""Prompt definitions for arXiv MCP server with research journey support."""

from mcp.types import (
    Prompt,
    PromptArgument,
)

# Define all prompts
PROMPTS = {
    "research-discovery": Prompt(
        name="research-discovery",
        description="Begin research exploration on a specific topic",
        arguments=[
            PromptArgument(
                name="topic", description="Research topic or question", required=True
            ),
            PromptArgument(
                name="expertise_level",
                description="User's familiarity (beginner/intermediate/expert)",
                required=False,
            ),
            PromptArgument(
                name="time_period",
                description="Time period for search (e.g., '2023-present')",
                required=False,
            ),
            PromptArgument(
                name="domain",
                description="Academic domain (e.g., computer_science/physics/biology)",
                required=False,
            ),
        ],
    ),
    "deep-paper-analysis": Prompt(
        name="deep-paper-analysis",
        description="Analyze a specific paper in detail",
        arguments=[
            PromptArgument(
                name="paper_id", description="arXiv paper ID", required=True
            ),
        ],
    ),
    "literature-synthesis": Prompt(
        name="literature-synthesis",
        description="Synthesize findings across multiple papers",
        arguments=[
            PromptArgument(
                name="paper_ids",
                description="Comma-separated list of arXiv paper IDs",
                required=True,
            ),
            PromptArgument(
                name="synthesis_type",
                description="Synthesis type (themes/methods/timeline/gaps/comprehensive)",
                required=False,
            ),
            PromptArgument(
                name="domain",
                description="Academic domain (e.g., computer_science/physics/biology)",
                required=False,
            ),
        ],
    ),
    "research-question": Prompt(
        name="research-question",
        description="Formulate research questions based on literature",
        arguments=[
            PromptArgument(
                name="paper_ids",
                description="Comma-separated list of arXiv paper IDs",
                required=True,
            ),
            PromptArgument(
                name="topic", description="Research topic or question", required=True
            ),
            PromptArgument(
                name="domain",
                description="Academic domain (e.g., computer_science/physics/biology)",
                required=False,
            ),
        ],
    ),
    "conversion-guide": Prompt(
        name="conversion-guide",
        description="Guide for using advanced PDF conversion features with marker-pdf",
        arguments=[
            PromptArgument(
                name="use_case",
                description="Your use case (reading/analysis/data-extraction/tables)",
                required=False,
            ),
        ],
    ),
    "content-description-guide": Prompt(
        name="content-description-guide",
        description="Guide for using LLM to describe tables and images in papers",
        arguments=[],
    ),
    "code-analysis": Prompt(
        name="code-analysis",
        description="Guide for analyzing code blocks in ArXiv papers using Tree-Sitter",
        arguments=[
            PromptArgument(
                name="language",
                description="Programming language to focus on (optional)",
                required=False,
            ),
        ],
    ),
    "comprehensive-research-guide": Prompt(
        name="comprehensive-research-guide",
        description="Complete guide for using all 15 ArXiv MCP server tools effectively",
        arguments=[],
    ),
}
