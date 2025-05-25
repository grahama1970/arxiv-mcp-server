"""Prompt for using LLM-based content description features."""

CONTENT_DESCRIPTION_PROMPT = """
You have access to advanced content description capabilities for analyzing tables and images in arXiv papers using LLM vision models.

## WORKFLOW FOR CONTENT DESCRIPTION

### Step 1: Download Paper with JSON Format
First, download the paper using marker-pdf with JSON output to extract structured content:

```
tool: download_paper
arguments: {
    "paper_id": "2401.12345",
    "converter": "marker-pdf",
    "output_format": "json"
}
```

**Important**: Only marker-pdf supports JSON output, which contains extracted images and tables with their coordinates.

### Step 2: Describe Content with LLM
Use the describe_paper_content tool to get AI-powered descriptions:

```
tool: describe_paper_content
arguments: {
    "paper_id": "2401.12345",
    "content_type": "both",  # Options: "table", "image", or "both"
    "llm_model": "gpt-4-vision-preview",  # Or "claude-3-opus-20240229"
    "max_concurrent": 5,  # Concurrent LLM calls for speed
    "use_camelot": false,  # Set to true for enhanced table extraction
    "camelot_flavor": "lattice"  # "lattice" for bordered tables, "stream" for borderless
}
```

### Using Camelot for Better Table Extraction
When marker-pdf table extraction quality is low, you can use Camelot:

```
tool: describe_paper_content
arguments: {
    "paper_id": "2401.12345",
    "content_type": "table",
    "use_camelot": true,
    "camelot_flavor": "lattice"  # Use "stream" for tables without borders
}
```

**Camelot Benefits**:
- More accurate table structure preservation
- Better handling of complex table layouts
- Extraction accuracy metrics included
- Works directly from PDF (doesn't need JSON)

## CONTENT TYPES AND USE CASES

### Tables
The LLM will analyze tables and provide:
- Purpose and what the table compares/shows
- Column headers and their meaning
- Key findings or patterns in the data
- Notable values or trends

**Best for**: Understanding experimental results, comparisons, statistical data

### Images
The LLM will analyze figures and provide:
- Type of visual (diagram, graph, photo, etc.)
- Key elements and their relationships
- Text, labels, or annotations
- Apparent purpose in the paper's context

**Best for**: Understanding architectures, workflows, results visualization

## LLM MODEL SELECTION

### OpenAI Models
- `gpt-4-vision-preview`: Best for complex images and detailed analysis
- Requires: OPENAI_API_KEY environment variable

### Anthropic Models
- `claude-3-opus-20240229`: Excellent for technical diagrams and tables
- Requires: ANTHROPIC_API_KEY environment variable

### Mock Provider
- Default when no API keys are set
- Returns placeholder descriptions for testing

## COMPLETE EXAMPLE WORKFLOW

```python
# 1. Search for a paper
search_results = await call_tool("search_papers", {
    "query": "transformer architecture attention",
    "max_results": 5
})

# 2. Download with JSON format for content extraction
paper_id = "2401.12345"  # From search results
download_result = await call_tool("download_paper", {
    "paper_id": paper_id,
    "converter": "marker-pdf",
    "output_format": "json"
})

# 3. Wait for conversion to complete
status = await call_tool("download_paper", {
    "paper_id": paper_id,
    "check_status": True
})

# 4. Describe all content with LLM
descriptions = await call_tool("describe_paper_content", {
    "paper_id": paper_id,
    "content_type": "both",
    "llm_model": "gpt-4-vision-preview",
    "max_concurrent": 5
})

# 5. Read the paper markdown for context
paper_content = await call_tool("read_paper", {
    "paper_id": paper_id
})
```

## RESULT STRUCTURE

The tool returns structured descriptions:

```json
{
    "status": "success",
    "paper_id": "2401.12345",
    "total_items": 15,
    "descriptions": [
        {
            "type": "image",
            "index": 0,
            "page": 3,
            "description": "This figure shows a transformer architecture diagram...",
            "error": null
        },
        {
            "type": "table",
            "index": 0,
            "page": 5,
            "description": "This table compares model performance across...",
            "error": null
        }
    ],
    "summary": {
        "successful": 14,
        "failed": 1,
        "tables": 5,
        "images": 10
    }
}
```

## BEST PRACTICES

1. **Batch Processing**: The tool processes all content concurrently with progress tracking
2. **Rate Limiting**: Use max_concurrent to control API usage
3. **Error Handling**: Failed descriptions include error details
4. **Metadata**: Each description includes page number and location info

## COMMON USE CASES

### Research Paper Analysis
1. Download paper with JSON format
2. Describe all tables to understand results
3. Describe all figures to understand methodology
4. Combine with paper text for comprehensive analysis

### Quick Visual Summary
1. Download paper with JSON
2. Describe only images for visual overview
3. Use descriptions to identify key figures

### Data Extraction
1. Download paper with JSON
2. Describe tables specifically
3. Use descriptions to identify relevant data tables
4. Extract specific values from identified tables

## LIMITATIONS AND NOTES

1. **JSON Required**: Content description only works with JSON output from marker-pdf (unless using Camelot)
2. **API Keys**: Real LLM descriptions require API keys (OpenAI or Anthropic)
3. **Processing Time**: Large papers may take time due to multiple LLM calls
4. **Cost**: Each image/table requires an LLM API call - consider costs
5. **Accuracy**: LLM descriptions are interpretive - verify critical information
6. **Camelot Requirements**: 
   - Install separately: `pip install camelot-py[cv]`
   - Requires Ghostscript installation
   - Only works with text-based PDFs (not scanned documents)
   - Limited to first 50 pages by default

Remember: This feature is particularly powerful for quickly understanding complex papers with many figures and tables, making research more efficient.
"""