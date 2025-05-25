"""Conversion options tool for the arXiv MCP server."""

import json
from typing import List, Dict, Any
import mcp.types as types
from ..converters import ConverterFactory


conversion_options_tool = types.Tool(
    name="get_conversion_options",
    description="Get available PDF to Markdown conversion options and their status",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)


async def handle_conversion_options(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle conversion options query."""
    try:
        # Get available converters
        available = ConverterFactory.get_available_converters()
        
        # Prepare detailed information
        converters_info = []
        
        # PyMuPDF4LLM info
        converters_info.append({
            "name": "pymupdf4llm",
            "available": available["pymupdf4llm"],
            "description": "Fast, lightweight PDF to Markdown conversion",
            "features": [
                "Very fast conversion speed",
                "Low memory usage",
                "Minimal computational requirements",
                "Good text extraction",
                "Basic table support",
                "Handles most academic papers adequately"
            ],
            "recommended_for": "General use, quick conversions, resource-constrained environments",
            "performance": "Fast and efficient",
            "supported_formats": ["markdown"],
            "is_default": True
        })
        
        # Marker-PDF info
        converters_info.append({
            "name": "marker-pdf",
            "available": available["marker-pdf"],
            "description": "Much more accurate PDF to Markdown conversion with ML-based extraction",
            "features": [
                "Significantly higher accuracy than pymupdf4llm",
                "Superior table extraction",
                "Better handling of complex layouts",
                "Image extraction capabilities",
                "Mathematical formula support",
                "Preserves document structure more faithfully",
                "Supports JSON output format for structured data"
            ],
            "recommended_for": "Best choice for accuracy - especially for papers with complex tables, figures, or mathematical content",
            "performance": "VERY computationally expensive and memory intensive",
            "warnings": [
                "Requires significant RAM (4GB+ for large papers)",
                "Much slower than pymupdf4llm (10-50x)",
                "May cause system slowdown during conversion",
                "Consider using only when accuracy is critical"
            ],
            "supported_formats": ["markdown", "json"],
            "is_default": False,
            "install_command": "pip install marker-pdf" if not available["marker-pdf"] else None
        })
        
        response = {
            "converters": converters_info,
            "default_converter": "pymupdf4llm",
            "usage_examples": [
                {
                    "description": "Download with marker-pdf for best accuracy",
                    "tool": "download_paper",
                    "arguments": {
                        "paper_id": "2401.12345",
                        "converter": "marker-pdf"
                    }
                },
                {
                    "description": "Download with JSON output (marker-pdf only)",
                    "tool": "download_paper",
                    "arguments": {
                        "paper_id": "2401.12345",
                        "converter": "marker-pdf",
                        "output_format": "json"
                    }
                }
            ]
        }
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )
        ]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Error getting conversion options: {str(e)}"
                })
            )
        ]


# Validation function
if __name__ == "__main__":
    import sys
    import asyncio
    # Add parent directory to path for testing
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from arxiv_mcp_server.converters import ConverterFactory
    
    print("\n=== CONVERSION OPTIONS TOOL VALIDATION ===")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Tool definition
    total_tests += 1
    print("\n1. Testing tool definition...")
    
    if conversion_options_tool.name == "get_conversion_options":
        print("   ✓ Tool name is correct")
    else:
        failure_msg = f"Tool name incorrect: {conversion_options_tool.name}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Test 2: Handle function
    total_tests += 1
    print("\n2. Testing handle function...")
    
    async def test_handle():
        result = await handle_conversion_options({})
        return result
    
    try:
        result = asyncio.run(test_handle())
        if result and len(result) > 0:
            content = json.loads(result[0].text)
            
            # Check response structure
            expected_keys = {"converters", "default_converter", "usage_examples"}
            if set(content.keys()) >= expected_keys:
                print("   ✓ Response has correct structure")
                print(f"   ✓ Found {len(content['converters'])} converters")
                
                # Show converter availability
                for conv in content['converters']:
                    status = "✓ Available" if conv['available'] else "✗ Not available"
                    print(f"      - {conv['name']}: {status}")
            else:
                failure_msg = f"Response missing keys: {expected_keys - set(content.keys())}"
                all_validation_failures.append(failure_msg)
                print(f"   ✗ {failure_msg}")
        else:
            failure_msg = "Handle function returned empty result"
            all_validation_failures.append(failure_msg)
            print(f"   ✗ {failure_msg}")
            
    except Exception as e:
        failure_msg = f"Handle function test failed: {e}"
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
        print("\nConversion options tool features:")
        print("  - Lists all available converters")
        print("  - Shows converter features and recommendations")
        print("  - Provides installation instructions for missing converters")
        print("  - Includes usage examples")
        sys.exit(0)