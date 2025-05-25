"""
ArXiv Download Core Functionality
=================================

Pure business logic for downloading and converting ArXiv papers.

Dependencies:
- arxiv: https://github.com/lukasschwab/arxiv.py
- pathlib: File path handling

Sample Input:
    paper_id = "2401.12345"
    converter = "pymupdf4llm"
    output_format = "markdown"
    storage_path = Path("/home/user/.arxiv_papers")

Expected Output:
    Dictionary with download status, file path, and metadata
"""

import arxiv
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConversionStatus(Enum):
    """Status of paper conversion."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class PaperStatus:
    """Track the status of a paper download and conversion."""
    paper_id: str
    status: ConversionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    converter: Optional[str] = None
    output_format: str = "markdown"
    file_path: Optional[Path] = None


class DownloadManager:
    """Manages paper downloads and conversions without external dependencies."""
    
    def __init__(self, storage_path: Path):
        """Initialize download manager with storage path."""
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._statuses: Dict[str, PaperStatus] = {}
    
    def get_paper_path(self, paper_id: str, extension: str = ".md") -> Path:
        """Get the path for a paper file."""
        return self.storage_path / f"{paper_id}{extension}"
    
    def get_status(self, paper_id: str) -> Optional[PaperStatus]:
        """Get current status of a paper."""
        return self._statuses.get(paper_id)
    
    def check_existing(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Check if paper already exists in any format."""
        # Check for markdown file
        md_path = self.get_paper_path(paper_id, ".md")
        if md_path.exists():
            return {
                "exists": True,
                "path": md_path,
                "format": "markdown",
                "size": md_path.stat().st_size
            }
        
        # Check for JSON file
        json_path = self.get_paper_path(paper_id, ".json")
        if json_path.exists():
            return {
                "exists": True,
                "path": json_path,
                "format": "json",
                "size": json_path.stat().st_size
            }
        
        # Check for PDF file
        pdf_path = self.get_paper_path(paper_id, ".pdf")
        if pdf_path.exists():
            return {
                "exists": True,
                "path": pdf_path,
                "format": "pdf",
                "size": pdf_path.stat().st_size,
                "needs_conversion": True
            }
        
        return None
    
    def download_paper(self, paper_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Download a paper from ArXiv.
        
        Args:
            paper_id: ArXiv paper ID
            
        Returns:
            Tuple of (success, result_dict)
        """
        pdf_path = self.get_paper_path(paper_id, ".pdf")
        
        # Update status
        status = PaperStatus(
            paper_id=paper_id,
            status=ConversionStatus.DOWNLOADING,
            started_at=datetime.now()
        )
        self._statuses[paper_id] = status
        
        try:
            # Search for the paper
            client = arxiv.Client()
            search = arxiv.Search(id_list=[paper_id])
            
            # Get the paper
            paper = next(client.results(search))
            
            # Download PDF
            paper.download_pdf(dirpath=self.storage_path, filename=f"{paper_id}.pdf")
            
            # Update status
            status.file_path = pdf_path
            
            # Return paper metadata
            return True, {
                "paper_id": paper_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.isoformat(),
                "pdf_path": str(pdf_path),
                "pdf_url": paper.pdf_url,
                "abstract": paper.summary,
                "categories": paper.categories
            }
            
        except StopIteration:
            status.status = ConversionStatus.ERROR
            status.error = f"Paper {paper_id} not found on ArXiv"
            status.completed_at = datetime.now()
            return False, {"error": status.error}
            
        except Exception as e:
            status.status = ConversionStatus.ERROR
            status.error = str(e)
            status.completed_at = datetime.now()
            return False, {"error": f"Download failed: {str(e)}"}
    
    async def convert_paper(
        self, 
        paper_id: str, 
        converter_type: str = "pymupdf4llm",
        output_format: str = "markdown"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Convert a downloaded paper. This is a placeholder for the actual conversion.
        In the real implementation, this would call the converter modules.
        
        Args:
            paper_id: ArXiv paper ID
            converter_type: Type of converter to use
            output_format: Output format (markdown or json)
            
        Returns:
            Tuple of (success, result_dict)
        """
        pdf_path = self.get_paper_path(paper_id, ".pdf")
        
        if not pdf_path.exists():
            return False, {"error": f"PDF file not found for {paper_id}"}
        
        # Get or create status
        status = self._statuses.get(paper_id, PaperStatus(
            paper_id=paper_id,
            status=ConversionStatus.PENDING,
            started_at=datetime.now()
        ))
        
        status.status = ConversionStatus.CONVERTING
        status.converter = converter_type
        status.output_format = output_format
        self._statuses[paper_id] = status
        
        # Determine output path
        extension = ".json" if output_format == "json" else ".md"
        output_path = self.get_paper_path(paper_id, extension)
        
        # For core module, we just prepare the conversion request
        # Actual conversion will be handled by converter modules
        return True, {
            "paper_id": paper_id,
            "pdf_path": str(pdf_path),
            "output_path": str(output_path),
            "converter": converter_type,
            "output_format": output_format,
            "status": "ready_for_conversion"
        }


def download_and_check_paper(
    paper_id: str,
    storage_path: Path,
    check_only: bool = False
) -> Dict[str, Any]:
    """
    Download a paper or check its status.
    
    Args:
        paper_id: ArXiv paper ID
        storage_path: Path to storage directory
        check_only: If True, only check status without downloading
        
    Returns:
        Dictionary with status and paper information
    """
    manager = DownloadManager(storage_path)
    
    # Check if paper already exists
    existing = manager.check_existing(paper_id)
    if existing:
        return {
            "status": "exists",
            "paper_id": paper_id,
            "path": str(existing["path"]),
            "format": existing["format"],
            "size": existing["size"],
            "needs_conversion": existing.get("needs_conversion", False)
        }
    
    if check_only:
        return {
            "status": "not_found",
            "paper_id": paper_id,
            "message": "Paper not found in local storage"
        }
    
    # Download the paper
    success, result = manager.download_paper(paper_id)
    
    if success:
        return {
            "status": "downloaded",
            "paper_id": paper_id,
            **result
        }
    else:
        return {
            "status": "error",
            "paper_id": paper_id,
            **result
        }


# Validation
if __name__ == "__main__":
    import sys
    import tempfile
    import shutil
    
    all_validation_failures = []
    total_tests = 0
    
    print("=" * 80)
    print("VALIDATING ARXIV DOWNLOAD CORE FUNCTIONALITY")
    print("=" * 80)
    
    # Create temporary storage
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Test 1: Download manager initialization
        total_tests += 1
        print("\nTest 1: Download manager initialization")
        print("-" * 40)
        
        try:
            manager = DownloadManager(temp_dir / "arxiv_papers")
            if (temp_dir / "arxiv_papers").exists():
                print("✓ Storage directory created")
            else:
                all_validation_failures.append("Test 1: Failed to create storage directory")
        except Exception as e:
            all_validation_failures.append(f"Test 1: {str(e)}")
        
        # Test 2: Check non-existent paper
        total_tests += 1
        print("\nTest 2: Check non-existent paper")
        print("-" * 40)
        
        try:
            result = download_and_check_paper(
                "nonexistent123",
                temp_dir / "arxiv_papers",
                check_only=True
            )
            if result["status"] == "not_found":
                print("✓ Correctly reported paper not found")
            else:
                all_validation_failures.append("Test 2: Should report not found")
        except Exception as e:
            all_validation_failures.append(f"Test 2: {str(e)}")
        
        # Test 3: Download a real paper
        total_tests += 1
        print("\nTest 3: Download a real paper")
        print("-" * 40)
        
        try:
            # Use a small, well-known paper
            result = download_and_check_paper(
                "1706.03762",  # Attention is All You Need
                temp_dir / "arxiv_papers"
            )
            
            if result["status"] == "downloaded":
                print(f"✓ Downloaded paper: {result.get('title', 'Unknown')[:60]}...")
                print(f"  Authors: {len(result.get('authors', []))} authors")
                print(f"  PDF saved to: {result.get('pdf_path', 'Unknown')}")
            else:
                all_validation_failures.append(f"Test 3: Download failed - {result.get('error', 'Unknown error')}")
        except Exception as e:
            all_validation_failures.append(f"Test 3: {str(e)}")
        
        # Test 4: Check existing paper
        total_tests += 1
        print("\nTest 4: Check existing paper")
        print("-" * 40)
        
        try:
            result = download_and_check_paper(
                "1706.03762",
                temp_dir / "arxiv_papers",
                check_only=True
            )
            
            if result["status"] == "exists":
                print(f"✓ Found existing paper")
                print(f"  Format: {result['format']}")
                print(f"  Size: {result['size']} bytes")
            else:
                all_validation_failures.append("Test 4: Should find existing paper")
        except Exception as e:
            all_validation_failures.append(f"Test 4: {str(e)}")
        
        # Test 5: Paper status tracking
        total_tests += 1
        print("\nTest 5: Paper status tracking")
        print("-" * 40)
        
        try:
            manager = DownloadManager(temp_dir / "arxiv_papers")
            
            # Check initial status
            status = manager.get_status("test123")
            if status is None:
                print("✓ No initial status")
            
            # Download and check status
            success, _ = manager.download_paper("2301.00001")
            status = manager.get_status("2301.00001")
            
            if status and status.paper_id == "2301.00001":
                print(f"✓ Status tracked: {status.status.value}")
            else:
                all_validation_failures.append("Test 5: Status not tracked properly")
                
        except Exception as e:
            all_validation_failures.append(f"Test 5: {str(e)}")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
    
    # Final result
    print("\n" + "=" * 80)
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Download core functionality is working correctly")
        sys.exit(0)