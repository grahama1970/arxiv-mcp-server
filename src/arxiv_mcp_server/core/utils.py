"""
Shared Utilities for ArXiv MCP Server Core
==========================================

Common utilities used across core modules.

Dependencies:
- pathlib: File path handling
- json: JSON serialization
- hashlib: File hashing

Sample Usage:
    paper_id = normalize_paper_id("arxiv:2401.12345v2")
    # Returns: "2401.12345v2"
    
    is_valid = validate_paper_id("2401.12345")
    # Returns: True
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def normalize_paper_id(paper_id: str) -> str:
    """
    Normalize various ArXiv ID formats to standard format.
    
    Args:
        paper_id: ArXiv ID in various formats
        
    Returns:
        Normalized paper ID
        
    Examples:
        "arxiv:2401.12345" -> "2401.12345"
        "2401.12345v2" -> "2401.12345v2"
        "http://arxiv.org/abs/2401.12345" -> "2401.12345"
    """
    # Remove common prefixes
    paper_id = paper_id.strip()
    
    # Handle URLs
    if "arxiv.org" in paper_id:
        # Extract ID from URL
        match = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', paper_id)
        if match:
            return match.group(1)
    
    # Remove arxiv: prefix
    if paper_id.startswith("arxiv:"):
        paper_id = paper_id[6:]
    
    # Remove abs/ prefix
    if paper_id.startswith("abs/"):
        paper_id = paper_id[4:]
    
    return paper_id


def validate_paper_id(paper_id: str) -> bool:
    """
    Validate if a string is a valid ArXiv paper ID.
    
    Args:
        paper_id: Paper ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic pattern for new-style ArXiv IDs (YYMM.NNNNN or YYMM.NNNNNvN)
    pattern = r'^\d{4}\.\d{4,5}(?:v\d+)?$'
    return bool(re.match(pattern, paper_id))


def get_file_hash(file_path: Path) -> str:
    """
    Get SHA256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex string of file hash
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def ensure_storage_path(base_path: Path, subdirs: Optional[List[str]] = None) -> Path:
    """
    Ensure storage directories exist.
    
    Args:
        base_path: Base storage path
        subdirs: Optional subdirectories to create
        
    Returns:
        Full path with subdirectories
    """
    full_path = base_path
    
    if subdirs:
        for subdir in subdirs:
            full_path = full_path / subdir
    
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation level
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def parse_date_safely(date_str: str) -> Optional[datetime]:
    """
    Safely parse date string with multiple format attempts.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try dateutil parser as fallback
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except:
        return None


def extract_arxiv_id_from_path(file_path: Union[str, Path]) -> Optional[str]:
    """
    Extract ArXiv ID from a file path.
    
    Args:
        file_path: Path to file
        
    Returns:
        ArXiv ID or None if not found
    """
    path = Path(file_path)
    stem = path.stem
    
    # Check if stem looks like an ArXiv ID
    if validate_paper_id(stem):
        return stem
    
    # Try to extract from filename
    match = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', str(path))
    if match:
        return match.group(1)
    
    return None


# Validation
if __name__ == "__main__":
    import sys
    import tempfile
    
    all_validation_failures = []
    total_tests = 0
    
    print("=" * 80)
    print("VALIDATING CORE UTILITIES")
    print("=" * 80)
    
    # Test 1: Paper ID normalization
    total_tests += 1
    print("\nTest 1: Paper ID normalization")
    print("-" * 40)
    
    test_ids = [
        ("arxiv:2401.12345", "2401.12345"),
        ("2401.12345v2", "2401.12345v2"),
        ("http://arxiv.org/abs/2401.12345", "2401.12345"),
        ("https://arxiv.org/abs/1706.03762v5", "1706.03762v5"),
        ("abs/2401.12345", "2401.12345"),
    ]
    
    for input_id, expected in test_ids:
        result = normalize_paper_id(input_id)
        if result == expected:
            print(f"✓ {input_id} -> {result}")
        else:
            all_validation_failures.append(f"Test 1: {input_id} -> {result} (expected {expected})")
    
    # Test 2: Paper ID validation
    total_tests += 1
    print("\nTest 2: Paper ID validation")
    print("-" * 40)
    
    valid_ids = ["2401.12345", "1706.03762v5", "2301.00001"]
    invalid_ids = ["arxiv:2401.12345", "invalid", "12345", "2401.123"]
    
    for paper_id in valid_ids:
        if validate_paper_id(paper_id):
            print(f"✓ {paper_id} is valid")
        else:
            all_validation_failures.append(f"Test 2: {paper_id} should be valid")
    
    for paper_id in invalid_ids:
        if not validate_paper_id(paper_id):
            print(f"✓ {paper_id} is invalid")
        else:
            all_validation_failures.append(f"Test 2: {paper_id} should be invalid")
    
    # Test 3: File operations
    total_tests += 1
    print("\nTest 3: File operations")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Test JSON save/load
            test_data = {"papers": ["2401.12345"], "count": 1}
            json_path = tmppath / "test.json"
            
            save_json_file(test_data, json_path)
            loaded_data = load_json_file(json_path)
            
            if loaded_data == test_data:
                print("✓ JSON save/load works")
            else:
                all_validation_failures.append("Test 3: JSON data mismatch")
            
            # Test file hash
            hash_val = get_file_hash(json_path)
            if len(hash_val) == 64:  # SHA256 is 64 hex chars
                print(f"✓ File hash computed: {hash_val[:16]}...")
            else:
                all_validation_failures.append("Test 3: Invalid hash length")
                
    except Exception as e:
        all_validation_failures.append(f"Test 3: {str(e)}")
    
    # Test 4: Text utilities
    total_tests += 1
    print("\nTest 4: Text utilities")
    print("-" * 40)
    
    # Test truncation
    long_text = "This is a very long text that needs to be truncated"
    truncated = truncate_text(long_text, 20)
    if len(truncated) == 20 and truncated.endswith("..."):
        print(f"✓ Text truncation: '{truncated}'")
    else:
        all_validation_failures.append("Test 4: Truncation failed")
    
    # Test file size formatting
    sizes = [(1023, "1023.0 B"), (1024, "1.0 KB"), (1048576, "1.0 MB")]
    for size, expected in sizes:
        result = format_file_size(size)
        if result == expected:
            print(f"✓ {size} bytes -> {result}")
        else:
            all_validation_failures.append(f"Test 4: {size} -> {result} (expected {expected})")
    
    # Test 5: Path extraction
    total_tests += 1
    print("\nTest 5: Path utilities")
    print("-" * 40)
    
    test_paths = [
        ("/home/user/papers/2401.12345.pdf", "2401.12345"),
        ("downloads/arxiv_1706.03762v5_paper.md", "1706.03762v5"),
        ("paper.pdf", None),
    ]
    
    for path, expected in test_paths:
        result = extract_arxiv_id_from_path(path)
        if result == expected:
            print(f"✓ {path} -> {result}")
        else:
            all_validation_failures.append(f"Test 5: {path} -> {result} (expected {expected})")
    
    # Final result
    print("\n" + "=" * 80)
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Core utilities are working correctly")
        sys.exit(0)