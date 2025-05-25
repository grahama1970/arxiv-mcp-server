"""
PDF to Markdown converters for arxiv-mcp-server.

This module provides multiple converter options for transforming PDF papers
into Markdown format, with support for different conversion engines and
quality settings.

Supported converters:
- pymupdf4llm: Fast, lightweight conversion (default)
- marker-pdf: Advanced conversion with better table/image handling

Reference:
- pymupdf4llm: https://github.com/pymupdf/PyMuPDF-Utilities
- marker-pdf: https://github.com/VikParuchuri/marker
"""

from pathlib import Path
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import subprocess
import asyncio
import logging

import pymupdf4llm
import pymupdf  # Import PyMuPDF directly for error handling

# Configure logging
logger = logging.getLogger("arxiv-mcp-server.converters")

ConverterType = Literal["pymupdf4llm", "marker-pdf"]
OutputFormat = Literal["markdown", "json"]


@dataclass
class ConversionResult:
    """Result of a PDF to Markdown conversion."""
    
    success: bool
    converter: ConverterType
    paper_id: str
    markdown_path: Optional[Path] = None
    pdf_path: Optional[Path] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "converter": self.converter,
            "paper_id": self.paper_id,
            "markdown_path": str(self.markdown_path) if self.markdown_path else None,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata or {}
        }


class PDFConverter:
    """Base class for PDF to Markdown converters."""
    
    def __init__(self, storage_path: Path):
        """Initialize converter with storage path."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    
    async def convert(self, paper_id: str, pdf_path: Path) -> ConversionResult:
        """Convert PDF to Markdown. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def get_markdown_path(self, paper_id: str) -> Path:
        """Get the path where markdown will be saved."""
        return self.storage_path / f"{paper_id}.md"


class PyMuPDF4LLMConverter(PDFConverter):
    """Converter using pymupdf4llm library."""
    
    async def convert(self, paper_id: str, pdf_path: Path) -> ConversionResult:
        """Convert PDF to Markdown using pymupdf4llm."""
        started_at = datetime.now()
        
        try:
            logger.info(f"Converting {paper_id} with pymupdf4llm")
            
            # First check if PDF is valid and not password-protected
            if pymupdf:
                try:
                    doc = await asyncio.to_thread(pymupdf.open, str(pdf_path))
                    if doc.is_encrypted:
                        doc.close()
                        error_msg = (
                            f"PDF is password-protected. ArXiv papers should not be encrypted. "
                            f"This may indicate: 1) A download error - try downloading again, "
                            f"2) The wrong file was downloaded - verify the paper ID, "
                            f"3) This is not an ArXiv paper - ArXiv provides open access PDFs without passwords."
                        )
                        logger.error(f"Password-protected PDF for {paper_id}")
                        return ConversionResult(
                            success=False,
                            converter="pymupdf4llm",
                            paper_id=paper_id,
                            pdf_path=pdf_path,
                            error=error_msg,
                            started_at=started_at,
                            completed_at=datetime.now(),
                            metadata={"error_type": "password_protected"}
                        )
                    
                    # Check if PDF has pages
                    if doc.page_count == 0:
                        doc.close()
                        error_msg = (
                            f"PDF appears to be corrupted (0 pages detected). "
                            f"This usually means: 1) Incomplete download - try downloading again, "
                            f"2) Network error during download - check your connection, "
                            f"3) The ArXiv server had a temporary issue - wait and retry."
                        )
                        logger.error(f"Corrupted PDF (0 pages) for {paper_id}")
                        return ConversionResult(
                            success=False,
                            converter="pymupdf4llm",
                            paper_id=paper_id,
                            pdf_path=pdf_path,
                            error=error_msg,
                            started_at=started_at,
                            completed_at=datetime.now(),
                            metadata={"error_type": "corrupted_pdf", "page_count": 0}
                        )
                    doc.close()
                except Exception as pdf_check_error:
                    # If we can't even open the PDF, it's likely corrupted
                    error_msg = (
                        f"Cannot open PDF file: {str(pdf_check_error)}. "
                        f"Common causes: 1) Corrupted download - try downloading again, "
                        f"2) Invalid PDF format - verify this is a valid ArXiv paper ID, "
                        f"3) File permissions issue - check file access permissions."
                    )
                    logger.error(f"Cannot open PDF for {paper_id}: {str(pdf_check_error)}")
                    return ConversionResult(
                        success=False,
                        converter="pymupdf4llm",
                        paper_id=paper_id,
                        pdf_path=pdf_path,
                        error=error_msg,
                        started_at=started_at,
                        completed_at=datetime.now(),
                        metadata={"error_type": "invalid_pdf"}
                    )
            
            # Run conversion in thread to avoid blocking
            markdown = await asyncio.to_thread(
                pymupdf4llm.to_markdown, 
                pdf_path, 
                show_progress=False
            )
            
            # Save markdown
            md_path = self.get_markdown_path(paper_id)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            return ConversionResult(
                success=True,
                converter="pymupdf4llm",
                paper_id=paper_id,
                markdown_path=md_path,
                pdf_path=pdf_path,
                started_at=started_at,
                completed_at=completed_at,
                metadata={
                    "duration_seconds": duration,
                    "markdown_size": len(markdown),
                    "file_size": md_path.stat().st_size
                }
            )
            
        except Exception as e:
            # Try to provide more specific error messages
            error_str = str(e)
            if "password" in error_str.lower():
                error_msg = f"PDF appears to be password-protected: {error_str}"
                metadata = {"error_type": "password_protected"}
            elif "corrupt" in error_str.lower() or "invalid" in error_str.lower():
                error_msg = f"PDF appears to be corrupted: {error_str}"
                metadata = {"error_type": "corrupted_pdf"}
            elif "no such file" in error_str.lower():
                error_msg = f"PDF file not found: {error_str}"
                metadata = {"error_type": "file_not_found"}
            else:
                error_msg = f"Conversion failed: {error_str}"
                metadata = {"error_type": "conversion_error"}
            
            logger.error(f"pymupdf4llm conversion failed for {paper_id}: {error_msg}")
            return ConversionResult(
                success=False,
                converter="pymupdf4llm",
                paper_id=paper_id,
                pdf_path=pdf_path,
                error=error_msg,
                started_at=started_at,
                completed_at=datetime.now(),
                metadata=metadata
            )


class MarkerPDFConverter(PDFConverter):
    """Converter using marker-pdf command line tool."""
    
    def __init__(self, storage_path: Path):
        """Initialize and check for marker-pdf availability."""
        super().__init__(storage_path)
        self._check_marker_available()
    
    def _check_marker_available(self):
        """Check if marker_single command is available."""
        try:
            result = subprocess.run(
                ["marker_single", "--help"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                logger.warning("marker_single command not found in PATH")
                self.available = False
            else:
                self.available = True
        except FileNotFoundError:
            logger.warning("marker_single not found - install with: pip install marker-pdf")
            self.available = False
    
    async def convert(self, paper_id: str, pdf_path: Path, output_format: OutputFormat = "markdown") -> ConversionResult:
        """Convert PDF to Markdown or JSON using marker-pdf."""
        started_at = datetime.now()
        
        if not self.available:
            return ConversionResult(
                success=False,
                converter="marker-pdf",
                paper_id=paper_id,
                pdf_path=pdf_path,
                error="marker-pdf not installed",
                started_at=started_at,
                completed_at=datetime.now()
            )
        
        try:
            logger.info(f"Converting {paper_id} with marker-pdf")
            
            # Create temp output directory for marker
            temp_output = self.storage_path / "marker_temp" / paper_id
            temp_output.mkdir(parents=True, exist_ok=True)
            
            # Run marker_single command
            cmd = [
                "marker_single",
                str(pdf_path),
                "--output_dir", str(temp_output),
                "--output_format", "markdown"
            ]
            
            # Run in thread to avoid blocking
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find generated file based on format
            if output_format == "markdown":
                output_files = list(temp_output.glob("**/*.md"))
                source_file = None
                
                for output_file in output_files:
                    # Skip metadata files
                    if not output_file.name.endswith("_meta.md"):
                        source_file = output_file
                        break
                
                if not source_file:
                    raise FileNotFoundError("No markdown file generated by marker")
                    
            else:  # json format
                output_files = list(temp_output.glob("**/*.json"))
                source_file = None
                
                for output_file in output_files:
                    # Skip metadata files
                    if not output_file.name.endswith("_meta.json"):
                        source_file = output_file
                        break
                
                if not source_file:
                    raise FileNotFoundError("No JSON file generated by marker")
            
            # Read and save to standard location
            output_content = source_file.read_text(encoding='utf-8')
            
            # Save with appropriate extension
            if output_format == "markdown":
                output_path = self.get_markdown_path(paper_id)
            else:
                output_path = self.storage_path / f"{paper_id}.json"
                
            output_path.write_text(output_content, encoding='utf-8')
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_output, ignore_errors=True)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            return ConversionResult(
                success=True,
                converter="marker-pdf",
                paper_id=paper_id,
                markdown_path=output_path,
                pdf_path=pdf_path,
                started_at=started_at,
                completed_at=completed_at,
                metadata={
                    "duration_seconds": duration,
                    "content_size": len(output_content),
                    "file_size": output_path.stat().st_size,
                    "output_format": output_format,
                    "advanced_features": True
                }
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"marker-pdf failed: {e.stderr}"
            # Check for specific error patterns
            stderr_lower = e.stderr.lower() if e.stderr else ""
            metadata = {"error_type": "conversion_error"}
            
            if "password" in stderr_lower or "encrypted" in stderr_lower:
                error_msg = (
                    f"PDF is password-protected (marker-pdf cannot process it). "
                    f"ArXiv papers are open access and should never be encrypted. "
                    f"Please verify the paper ID and try downloading again. "
                    f"Technical details: {e.stderr}"
                )
                metadata["error_type"] = "password_protected"
            elif "corrupt" in stderr_lower or "invalid" in stderr_lower or "damaged" in stderr_lower:
                error_msg = (
                    f"PDF appears to be corrupted or damaged (marker-pdf cannot process it). "
                    f"Try: 1) Re-downloading the paper, 2) Using pymupdf4llm converter instead, "
                    f"3) Checking if the paper is available on ArXiv. "
                    f"Technical details: {e.stderr}"
                )
                metadata["error_type"] = "corrupted_pdf"
            elif "memory" in stderr_lower:
                error_msg = (
                    f"Insufficient memory for marker-pdf conversion. "
                    f"Marker-pdf requires 4GB+ RAM for large papers. "
                    f"Solutions: 1) Use pymupdf4llm converter (much less memory), "
                    f"2) Close other applications to free memory, "
                    f"3) Use get_system_stats to check available resources. "
                    f"Technical details: {e.stderr}"
                )
                metadata["error_type"] = "memory_error"
                
            logger.error(f"marker-pdf conversion failed for {paper_id}: {error_msg}")
            return ConversionResult(
                success=False,
                converter="marker-pdf",
                paper_id=paper_id,
                pdf_path=pdf_path,
                error=error_msg,
                started_at=started_at,
                completed_at=datetime.now(),
                metadata=metadata
            )
        except Exception as e:
            error_str = str(e)
            metadata = {"error_type": "conversion_error"}
            
            if "password" in error_str.lower():
                error_msg = f"PDF appears to be password-protected: {error_str}"
                metadata["error_type"] = "password_protected"
            elif "corrupt" in error_str.lower() or "invalid" in error_str.lower():
                error_msg = f"PDF appears to be corrupted: {error_str}"
                metadata["error_type"] = "corrupted_pdf"
            elif "no such file" in error_str.lower():
                error_msg = f"PDF file not found: {error_str}"
                metadata["error_type"] = "file_not_found"
            else:
                error_msg = f"Conversion failed: {error_str}"
                
            logger.error(f"marker-pdf conversion error for {paper_id}: {error_msg}")
            return ConversionResult(
                success=False,
                converter="marker-pdf",
                paper_id=paper_id,
                pdf_path=pdf_path,
                error=error_msg,
                started_at=started_at,
                completed_at=datetime.now(),
                metadata=metadata
            )


class ConverterFactory:
    """Factory for creating PDF converters."""
    
    @staticmethod
    def create(converter_type: ConverterType, storage_path: Path) -> PDFConverter:
        """Create a converter instance based on type."""
        if converter_type == "pymupdf4llm":
            return PyMuPDF4LLMConverter(storage_path)
        elif converter_type == "marker-pdf":
            return MarkerPDFConverter(storage_path)
        else:
            raise ValueError(f"Unknown converter type: {converter_type}")
    
    @staticmethod
    def get_available_converters() -> Dict[str, bool]:
        """Check which converters are available."""
        available = {
            "pymupdf4llm": True  # Always available as it's a dependency
        }
        
        # Check marker-pdf
        try:
            result = subprocess.run(
                ["marker_single", "--help"],
                capture_output=True,
                text=True,
                check=False
            )
            available["marker-pdf"] = result.returncode == 0
        except FileNotFoundError:
            available["marker-pdf"] = False
        
        return available


# Validation function
if __name__ == "__main__":
    import sys
    
    print("\n=== PDF CONVERTER MODULE VALIDATION ===")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check available converters
    total_tests += 1
    print("\n1. Checking available converters...")
    
    available = ConverterFactory.get_available_converters()
    print(f"   pymupdf4llm: {'✓ Available' if available['pymupdf4llm'] else '✗ Not available'}")
    print(f"   marker-pdf: {'✓ Available' if available['marker-pdf'] else '✗ Not available'}")
    
    if not available["pymupdf4llm"]:
        all_validation_failures.append("pymupdf4llm converter not available")
    
    # Test 2: Create converter instances
    total_tests += 1
    print("\n2. Testing converter creation...")
    
    test_storage = Path("./test_conversions")
    test_storage.mkdir(exist_ok=True)
    
    try:
        pymupdf_converter = ConverterFactory.create("pymupdf4llm", test_storage)
        print("   ✓ PyMuPDF4LLM converter created")
    except Exception as e:
        failure_msg = f"Failed to create PyMuPDF4LLM converter: {e}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    if available["marker-pdf"]:
        try:
            marker_converter = ConverterFactory.create("marker-pdf", test_storage)
            print("   ✓ Marker-PDF converter created")
        except Exception as e:
            failure_msg = f"Failed to create Marker-PDF converter: {e}"
            all_validation_failures.append(failure_msg)
            print(f"   ✗ {failure_msg}")
    else:
        print("   ⚠️  Skipping Marker-PDF converter (not installed)")
    
    # Test 3: Test ConversionResult
    total_tests += 1
    print("\n3. Testing ConversionResult...")
    
    test_result = ConversionResult(
        success=True,
        converter="pymupdf4llm",
        paper_id="test_paper",
        markdown_path=Path("/tmp/test.md"),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        metadata={"test": "data"}
    )
    
    result_dict = test_result.to_dict()
    expected_keys = {"success", "converter", "paper_id", "markdown_path", "started_at", "completed_at", "metadata"}
    
    if set(result_dict.keys()) >= expected_keys:
        print("   ✓ ConversionResult serialization works correctly")
    else:
        failure_msg = f"ConversionResult missing keys: {expected_keys - set(result_dict.keys())}"
        all_validation_failures.append(failure_msg)
        print(f"   ✗ {failure_msg}")
    
    # Clean up test directory
    import shutil
    shutil.rmtree(test_storage, ignore_errors=True)
    
    # Final validation result
    print("\n=== VALIDATION SUMMARY ===")
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("\nConverter module features:")
        print("  - Multiple converter backends (pymupdf4llm, marker-pdf)")
        print("  - Async conversion support")
        print("  - Structured result objects")
        print("  - Factory pattern for converter creation")
        print("  - Automatic availability checking")
        sys.exit(0)