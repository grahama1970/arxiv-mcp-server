"""Download functionality for the arXiv MCP server."""

import arxiv
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import mcp.types as types
from ..config import Settings
from ..converters import ConverterFactory, ConverterType, OutputFormat
import logging

logger = logging.getLogger("arxiv-mcp-server")
settings = Settings()

# Global dictionary to track conversion status
conversion_statuses: Dict[str, Any] = {}


@dataclass
class ConversionStatus:
    """Track the status of a PDF to Markdown conversion."""

    paper_id: str
    status: str  # 'downloading', 'converting', 'success', 'error'
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    converter: Optional[str] = None


download_tool = types.Tool(
    name="download_paper",
    description="Download a paper and convert to markdown. Default uses fast pymupdf4llm. Only use marker-pdf when accuracy is critical (10-50x slower, 4GB+ RAM)",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper to download",
            },
            "check_status": {
                "type": "boolean",
                "description": "If true, only check conversion status without downloading",
                "default": False,
            },
            "converter": {
                "type": "string",
                "description": "PDF converter: pymupdf4llm (fast, default) or marker-pdf (very slow but accurate)",
                "enum": ["pymupdf4llm", "marker-pdf"],
                "default": "pymupdf4llm",
            },
            "output_format": {
                "type": "string",
                "description": "Output format (markdown or json - json only supported by marker-pdf)",
                "enum": ["markdown", "json"],
                "default": "markdown",
            },
        },
        "required": ["paper_id"],
    },
)


def get_paper_path(paper_id: str, suffix: str = ".md", output_format: str = "markdown") -> Path:
    """Get the absolute file path for a paper with given suffix."""
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    # Override suffix based on output format
    if output_format == "json":
        suffix = ".json"
    return storage_path / f"{paper_id}{suffix}"


async def convert_pdf_to_markdown(paper_id: str, pdf_path: Path, converter_type: ConverterType, output_format: OutputFormat = "markdown") -> None:
    """Convert PDF to specified format using specified converter."""
    try:
        logger.info(f"Starting conversion for {paper_id} using {converter_type} to {output_format}")
        
        # Create converter
        converter = ConverterFactory.create(converter_type, Path(settings.STORAGE_PATH))
        result = await converter.convert(paper_id, pdf_path, output_format)
        
        status = conversion_statuses.get(paper_id)
        if status:
            if result.success:
                status.status = "success"
                status.completed_at = result.completed_at
                status.converter = converter_type
            else:
                status.status = "error"
                status.completed_at = result.completed_at
                status.error = result.error
                status.converter = converter_type

        logger.info(f"Conversion {'completed' if result.success else 'failed'} for {paper_id}")

    except Exception as e:
        logger.error(f"Conversion failed for {paper_id}: {str(e)}")
        status = conversion_statuses.get(paper_id)
        if status:
            status.status = "error"
            status.completed_at = datetime.now()
            status.error = str(e)
            status.converter = converter_type


async def handle_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper download and conversion requests."""
    try:
        paper_id = arguments["paper_id"]
        check_status = arguments.get("check_status", False)
        converter_type = arguments.get("converter", "pymupdf4llm")
        output_format = arguments.get("output_format", "markdown")

        # If only checking status
        if check_status:
            status = conversion_statuses.get(paper_id)
            if not status:
                # Check for both markdown and json files
                md_path = get_paper_path(paper_id, ".md", "markdown")
                json_path = get_paper_path(paper_id, ".json", "json")
                
                if md_path.exists() or json_path.exists():
                    existing_format = "markdown" if md_path.exists() else "json"
                    existing_path = md_path if md_path.exists() else json_path
                    return [
                        types.TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "status": "success",
                                    "message": "Paper is ready",
                                    "resource_uri": f"file://{existing_path}",
                                    "format": existing_format,
                                }
                            ),
                        )
                    ]
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "status": "unknown",
                                "message": "No download or conversion in progress",
                            }
                        ),
                    )
                ]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": status.status,
                            "started_at": status.started_at.isoformat(),
                            "completed_at": (
                                status.completed_at.isoformat()
                                if status.completed_at
                                else None
                            ),
                            "error": status.error,
                            "converter": getattr(status, "converter", None),
                            "message": f"Paper conversion {status.status}",
                        }
                    ),
                )
            ]

        # Check if paper is already converted
        output_path = get_paper_path(paper_id, ".md" if output_format == "markdown" else ".json", output_format)
        if output_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "message": "Paper already available",
                            "resource_uri": f"file://{output_path}",
                            "format": output_format,
                        }
                    ),
                )
            ]

        # Check if already in progress
        if paper_id in conversion_statuses:
            status = conversion_statuses[paper_id]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": status.status,
                            "message": f"Paper conversion {status.status}",
                            "started_at": status.started_at.isoformat(),
                            "converter": getattr(status, "converter", converter_type),
                        }
                    ),
                )
            ]

        # Start new download and conversion
        pdf_path = get_paper_path(paper_id, ".pdf")
        client = arxiv.Client()

        # Initialize status
        conversion_statuses[paper_id] = ConversionStatus(
            paper_id=paper_id, status="downloading", started_at=datetime.now()
        )

        # Download PDF
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        paper.download_pdf(dirpath=pdf_path.parent, filename=pdf_path.name)

        # Update status and start conversion
        status = conversion_statuses[paper_id]
        status.status = "converting"

        # Start conversion as async task
        asyncio.create_task(
            convert_pdf_to_markdown(paper_id, pdf_path, converter_type, output_format)
        )

        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "converting",
                        "message": f"Paper downloaded, conversion started with {converter_type} to {output_format}",
                        "started_at": status.started_at.isoformat(),
                        "converter": converter_type,
                        "output_format": output_format,
                    }
                ),
            )
        ]

    except StopIteration:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": f"Paper {paper_id} not found on arXiv",
                    }
                ),
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Error: {str(e)}"}),
            )
        ]
