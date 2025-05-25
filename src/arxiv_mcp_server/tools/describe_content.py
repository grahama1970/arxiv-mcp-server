"""LLM-based content description tool for tables and images in papers."""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import base64
import mcp.types as types
from tqdm.asyncio import tqdm_asyncio
import logging
from ..config import Settings
from ..llm_providers import get_llm_provider

logger = logging.getLogger("arxiv-mcp-server.describe-content")
settings = Settings()

ContentType = Literal["table", "image", "both"]


@dataclass
class ContentItem:
    """Represents a table or image to be described."""
    
    paper_id: str
    content_type: Literal["table", "image"]
    index: int
    data: str  # Base64 encoded image or table data
    metadata: Dict[str, Any]  # Bounding box, page number, etc.
    

@dataclass 
class ContentDescription:
    """Description result for a content item."""
    
    paper_id: str
    content_type: str
    index: int
    description: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


describe_content_tool = types.Tool(
    name="describe_paper_content",
    description="Use LLM to describe tables and images extracted from a paper",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper",
            },
            "content_type": {
                "type": "string",
                "description": "Type of content to describe",
                "enum": ["table", "image", "both"],
                "default": "both",
            },
            "llm_model": {
                "type": "string", 
                "description": "LLM model to use for descriptions",
                "default": "gpt-4-vision-preview",
            },
            "max_concurrent": {
                "type": "integer",
                "description": "Maximum concurrent LLM calls",
                "default": 5,
            },
            "use_camelot": {
                "type": "boolean",
                "description": "Use Camelot for enhanced table extraction when marker-pdf quality is low",
                "default": False,
            },
            "camelot_flavor": {
                "type": "string",
                "description": "Camelot extraction method: 'lattice' for bordered tables, 'stream' for borderless",
                "enum": ["lattice", "stream"],
                "default": "lattice",
            },
        },
        "required": ["paper_id"],
    },
)


async def extract_content_from_json(paper_id: str, content_type: ContentType) -> List[ContentItem]:
    """Extract tables and images from marker-pdf JSON output."""
    json_path = Path(settings.STORAGE_PATH) / f"{paper_id}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(
            f"JSON file not found for {paper_id}. "
            "Please download with marker-pdf and output_format='json' first."
        )
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    content_items = []
    image_count = 0
    table_count = 0
    
    # Marker-pdf JSON structure includes blocks with type information
    # Process all blocks to find images and tables
    for block in data:
        if not isinstance(block, dict):
            continue
            
        block_type = block.get("type", "").lower()
        
        # Extract images (figures, pictures)
        if content_type in ["image", "both"] and block_type in ["figure", "picture", "figuregroup", "picturegroup"]:
            # Look for base64 image data
            if "image" in block and isinstance(block["image"], str):
                image_count += 1
                content_items.append(ContentItem(
                    paper_id=paper_id,
                    content_type="image",
                    index=image_count - 1,
                    data=block["image"],  # Base64 encoded
                    metadata={
                        "page": block.get("page", 0) + 1,
                        "bbox": block.get("bbox", []),
                        "polygon": block.get("polygon", []),
                        "caption": block.get("caption", ""),
                        "block_type": block_type,
                    }
                ))
        
        # Extract tables
        if content_type in ["table", "both"] and block_type in ["table", "tablegroup"]:
            table_count += 1
            
            # Extract table content - could be in different formats
            table_content = {}
            if "cells" in block:
                table_content = {"cells": block["cells"]}
            elif "rows" in block:
                table_content = {"rows": block["rows"]}
            elif "text" in block:
                # Sometimes table is just text
                table_content = {"text": block["text"]}
            
            # Convert to JSON string and encode
            table_data = json.dumps(table_content, indent=2)
            table_b64 = base64.b64encode(table_data.encode()).decode()
            
            content_items.append(ContentItem(
                paper_id=paper_id,
                content_type="table",
                index=table_count - 1,
                data=table_b64,
                metadata={
                    "page": block.get("page", 0) + 1,
                    "bbox": block.get("bbox", []),
                    "polygon": block.get("polygon", []),
                    "caption": block.get("caption", ""),
                    "block_type": block_type,
                    "has_cells": "cells" in block,
                    "has_rows": "rows" in block,
                }
            ))
    
    logger.info(f"Extracted {len(content_items)} items: {image_count} images, {table_count} tables")
    return content_items


async def extract_tables_with_camelot(
    paper_id: str, 
    flavor: str = "lattice",
    pages: Optional[str] = None
) -> List[ContentItem]:
    """Extract tables using Camelot for better quality when marker-pdf fails."""
    try:
        import camelot
    except ImportError:
        logger.warning("Camelot not installed. Install with: pip install camelot-py[cv]")
        return []
    
    pdf_path = Path(settings.STORAGE_PATH) / f"{paper_id}.pdf"
    
    if not pdf_path.exists():
        logger.error(f"PDF file not found for {paper_id}")
        return []
    
    content_items = []
    
    try:
        # Extract tables with Camelot
        # If pages not specified, try first 50 pages (Camelot limitation)
        if pages is None:
            pages = "1-50"
            
        logger.info(f"Extracting tables with Camelot (flavor={flavor}) from pages {pages}")
        tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor=flavor)
        
        for idx, table in enumerate(tables):
            # Get table data
            df = table.df
            
            # Convert DataFrame to structured format
            table_data = {
                "headers": df.iloc[0].tolist() if len(df) > 0 else [],
                "rows": df.iloc[1:].values.tolist() if len(df) > 1 else [],
                "shape": df.shape,
                "accuracy": table.parsing_report.get('accuracy', 0),
                "page": table.parsing_report.get('page', 0),
            }
            
            # Encode as JSON
            table_json = json.dumps(table_data, indent=2)
            table_b64 = base64.b64encode(table_json.encode()).decode()
            
            content_items.append(ContentItem(
                paper_id=paper_id,
                content_type="table",
                index=idx,
                data=table_b64,
                metadata={
                    "page": table.parsing_report.get('page', 0),
                    "accuracy": table.parsing_report.get('accuracy', 0),
                    "whitespace": table.parsing_report.get('whitespace', 0),
                    "order": table.parsing_report.get('order', idx + 1),
                    "extraction_method": f"camelot-{flavor}",
                    "rows": len(df) - 1,  # Excluding header
                    "columns": len(df.columns),
                }
            ))
            
        logger.info(f"Camelot extracted {len(content_items)} tables")
        return content_items
        
    except Exception as e:
        logger.error(f"Camelot extraction failed: {str(e)}")
        return []


async def describe_with_llm(
    item: ContentItem, 
    llm_model: str = "gpt-4-vision-preview"
) -> ContentDescription:
    """Describe a single content item using an LLM."""
    try:
        # Determine provider from model name
        if "gpt" in llm_model.lower():
            provider_name = "openai"
        elif "claude" in llm_model.lower():
            provider_name = "anthropic"
        else:
            provider_name = "mock"  # Default to mock for testing
        
        # Get LLM provider
        provider = get_llm_provider(provider_name, model=llm_model)
        
        if item.content_type == "image":
            prompt = (
                "Describe this image from an academic paper. Include:\n"
                "1. What the image shows (diagram, graph, photo, etc.)\n"
                "2. Key elements and their relationships\n"
                "3. Any text, labels, or annotations\n"
                "4. The apparent purpose or significance in the paper's context"
            )
            
            # Call LLM to describe image
            response = await provider.describe_image(item.data, prompt)
            
        else:  # table
            # Decode table data
            table_json = base64.b64decode(item.data).decode()
            prompt = (
                "Describe this table from an academic paper. Include:\n"
                "1. The table's purpose and what it compares/shows\n"
                "2. Column headers and their meaning\n"
                "3. Key findings or patterns in the data\n"
                "4. Any notable values or trends"
            )
            
            # Call LLM to describe table
            response = await provider.describe_text(table_json, prompt)
        
        if response.error:
            logger.error(f"LLM error for {item.content_type} {item.index}: {response.error}")
            return ContentDescription(
                paper_id=item.paper_id,
                content_type=item.content_type,
                index=item.index,
                description="",
                metadata={**item.metadata, "llm_model": response.model},
                error=response.error
            )
        
        return ContentDescription(
            paper_id=item.paper_id,
            content_type=item.content_type,
            index=item.index,
            description=response.content,
            metadata={
                **item.metadata, 
                "llm_model": response.model,
                "usage": response.usage
            }
        )
        
    except Exception as e:
        logger.error(f"Error describing {item.content_type} {item.index}: {str(e)}")
        return ContentDescription(
            paper_id=item.paper_id,
            content_type=item.content_type,
            index=item.index,
            description="",
            metadata=item.metadata,
            error=str(e)
        )


async def batch_describe_content(
    items: List[ContentItem],
    llm_model: str = "gpt-4-vision-preview",
    max_concurrent: int = 5
) -> List[ContentDescription]:
    """Batch process content items with concurrent LLM calls."""
    
    # Create semaphore to limit concurrent calls
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def describe_with_limit(item: ContentItem) -> ContentDescription:
        async with semaphore:
            return await describe_with_llm(item, llm_model)
    
    # Create tasks for all items
    tasks = [describe_with_limit(item) for item in items]
    
    # Process with progress bar
    results = []
    desc = f"Describing {len(items)} items"
    
    # Use tqdm_asyncio.as_completed for progress tracking
    for future in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc=desc):
        result = await future
        results.append(result)
    
    # Sort results by type and index for consistent output
    results.sort(key=lambda x: (x.content_type, x.index))
    
    return results


async def handle_describe_content(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle content description requests."""
    try:
        paper_id = arguments["paper_id"]
        content_type = arguments.get("content_type", "both")
        llm_model = arguments.get("llm_model", "gpt-4-vision-preview")
        max_concurrent = arguments.get("max_concurrent", 5)
        use_camelot = arguments.get("use_camelot", False)
        camelot_flavor = arguments.get("camelot_flavor", "lattice")
        
        # Extract content
        logger.info(f"Extracting {content_type} content from {paper_id}")
        
        if use_camelot and content_type in ["table", "both"]:
            # Try Camelot for tables
            logger.info("Using Camelot for enhanced table extraction")
            
            # Extract images from JSON if needed
            image_items = []
            if content_type == "both":
                all_items = await extract_content_from_json(paper_id, "image")
                image_items = [item for item in all_items if item.content_type == "image"]
            
            # Extract tables with Camelot
            table_items = await extract_tables_with_camelot(paper_id, camelot_flavor)
            
            # Combine items
            content_items = image_items + table_items
            
            # If Camelot failed, fall back to marker-pdf
            if not table_items and content_type == "table":
                logger.warning("Camelot extraction failed, falling back to marker-pdf")
                content_items = await extract_content_from_json(paper_id, content_type)
        else:
            # Use marker-pdf JSON extraction
            content_items = await extract_content_from_json(paper_id, content_type)
        
        if not content_items:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "no_content",
                        "message": f"No {content_type} content found in paper",
                        "paper_id": paper_id
                    })
                )
            ]
        
        logger.info(f"Found {len(content_items)} items to describe")
        
        # Batch describe with LLM
        descriptions = await batch_describe_content(
            content_items,
            llm_model=llm_model,
            max_concurrent=max_concurrent
        )
        
        # Format results
        results = {
            "status": "success",
            "paper_id": paper_id,
            "total_items": len(content_items),
            "extraction_method": "camelot" if use_camelot else "marker-pdf",
            "descriptions": []
        }
        
        # Group by type
        for desc in descriptions:
            item_result = {
                "type": desc.content_type,
                "index": desc.index,
                "page": desc.metadata.get("page"),
                "description": desc.description,
                "error": desc.error
            }
            
            # Add extraction method for tables
            if desc.content_type == "table":
                extraction_method = desc.metadata.get("extraction_method", "marker-pdf")
                item_result["extraction_method"] = extraction_method
                
                # Add Camelot-specific metrics if available
                if "accuracy" in desc.metadata:
                    item_result["accuracy"] = desc.metadata["accuracy"]
                    
            results["descriptions"].append(item_result)
        
        # Summary statistics
        successful = sum(1 for d in descriptions if not d.error)
        results["summary"] = {
            "successful": successful,
            "failed": len(descriptions) - successful,
            "tables": sum(1 for d in descriptions if d.content_type == "table"),
            "images": sum(1 for d in descriptions if d.content_type == "image")
        }
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )
        ]
        
    except FileNotFoundError as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": str(e),
                    "hint": "Use download_paper with converter='marker-pdf' and output_format='json'"
                })
            )
        ]
    except Exception as e:
        logger.error(f"Error in describe_content: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error", 
                    "message": f"Error describing content: {str(e)}"
                })
            )
        ]


# Validation function
if __name__ == "__main__":
    import sys
    
    print("\n=== CONTENT DESCRIPTION TOOL VALIDATION ===")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Tool definition
    total_tests += 1
    print("\n1. Testing tool definition...")
    
    if describe_content_tool.name == "describe_paper_content":
        print("   ✓ Tool name is correct")
    else:
        failure_msg = f"Tool name incorrect: {describe_content_tool.name}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 2: ContentItem creation
    total_tests += 1
    print("\n2. Testing ContentItem creation...")
    
    try:
        test_item = ContentItem(
            paper_id="test_paper",
            content_type="table",
            index=0,
            data="test_data",
            metadata={"page": 1}
        )
        print("   ✓ ContentItem created successfully")
    except Exception as e:
        failure_msg = f"Failed to create ContentItem: {e}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 3: ContentDescription creation
    total_tests += 1
    print("\n3. Testing ContentDescription...")
    
    try:
        test_desc = ContentDescription(
            paper_id="test_paper",
            content_type="image",
            index=0,
            description="Test description",
            metadata={"page": 1}
        )
        print("   ✓ ContentDescription created successfully")
    except Exception as e:
        failure_msg = f"Failed to create ContentDescription: {e}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 4: Async functionality
    total_tests += 1
    print("\n4. Testing async describe_with_llm...")
    
    async def test_async():
        try:
            result = await describe_with_llm(test_item)
            return result.description != ""
        except Exception:
            return False
    
    try:
        success = asyncio.run(test_async())
        if success:
            print("   ✓ Async LLM description works")
        else:
            failure_msg = "Async LLM description failed"
            all_validation_failures.append(failure_msg)
            print(f"   ✗ {failure_msg}")
    except Exception as e:
        failure_msg = f"Async test failed: {e}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Final validation result
    print("\n=== VALIDATION SUMMARY ===")
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("\nContent description tool features:")
        print("  - Extracts tables and images from marker-pdf JSON output")
        print("  - Batch processes with concurrent LLM calls")
        print("  - Progress tracking with tqdm")
        print("  - Supports rate limiting with semaphore")
        print("  - Returns structured descriptions with metadata")
        sys.exit(0)