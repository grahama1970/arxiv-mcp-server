# Changelog

All notable changes to the arxiv-mcp-server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-01-24

### Added
- **Advanced PDF Conversion Features**
  - New `converter` parameter in `download_paper` tool to choose between converters
  - Support for `marker-pdf` converter which is **much more accurate** than the default
  - New `output_format` parameter supporting both `markdown` and `json` outputs
  - JSON output format for structured data extraction (marker-pdf only)
  - New `get_conversion_options` tool to check available converters and capabilities
  - New `conversion-guide` prompt for detailed usage instructions

- **LLM-Based Content Description** 
  - New `describe_paper_content` tool for AI-powered analysis of tables and images
  - Support for OpenAI GPT-4 Vision and Anthropic Claude models
  - Concurrent processing with tqdm progress tracking
  - Batch description capabilities with rate limiting
  - Extracts images and tables from marker-pdf JSON output
  - Optional Camelot integration for enhanced table extraction when marker-pdf quality is low
  - Support for both "lattice" (bordered) and "stream" (borderless) table extraction
  - Extraction accuracy metrics for quality assurance
  - New `content-description-guide` prompt with comprehensive workflow

- **New Converter Module** (`converters.py`)
  - Modular converter architecture supporting multiple backends
  - `PyMuPDF4LLMConverter` for fast, lightweight conversion (default)
  - `MarkerPDFConverter` for high-accuracy conversion with advanced features
  - Factory pattern for easy converter selection
  - Async conversion support with proper error handling
  - Automatic converter availability detection

- **LLM Provider Integration** (`llm_providers.py`)
  - Abstract base class for LLM providers
  - OpenAI GPT-4 Vision implementation
  - Anthropic Claude implementation  
  - Mock provider for testing without API calls
  - Structured response handling with usage tracking

- **Enhanced Prompts**
  - Updated `deep-paper-analysis` prompt to recommend marker-pdf for accuracy
  - New `conversion-guide` prompt with detailed converter usage instructions
  - New `content-description-guide` prompt for LLM content analysis workflow
  - Added specific guidance for different use cases (tables, data extraction, etc.)

### Changed
- `download_paper` tool now accepts optional `converter` and `output_format` parameters
- Paper storage now supports both `.md` and `.json` file extensions
- Conversion status tracking includes converter type and output format
- Updated all prompts to list available tools (not just deep-paper-analysis)
- Documentation now clearly states performance characteristics:
  - pymupdf4llm: Fast, lightweight, low memory usage (default)
  - marker-pdf: Extremely computationally expensive, 10-50x slower, requires 4GB+ RAM

### Improved
- Documentation updated with comprehensive conversion feature guide
- README.md now includes detailed converter comparison and usage examples
- Better error handling for unavailable converters
- More informative status messages during conversion

## [0.2.10] - Previous Release

### Added
- PDF files are now kept after conversion (removed automatic cleanup)
- Various bug fixes and improvements

[Note: For complete version history prior to 0.2.10, see git commit history]