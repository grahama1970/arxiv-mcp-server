"""
Mac Compatibility Checker for Sentence Transformers
===================================================

Detects Mac hardware architecture and provides graceful handling
for Intel Mac incompatibility with sentence-transformers.

Purpose:
    - Detect if running on Intel Mac vs Apple Silicon
    - Provide helpful messages when features aren't available
    - Gracefully disable semantic search on incompatible systems

Links:
    - platform module: https://docs.python.org/3/library/platform.html
    - sentence-transformers issues: https://github.com/UKPLab/sentence-transformers/issues

Sample Usage:
    if not check_mac_compatibility():
        return "Semantic search not available on Intel Macs"
"""

import platform
import subprocess
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def get_mac_architecture() -> Optional[str]:
    """
    Detect Mac architecture (Intel vs Apple Silicon).
    
    Returns:
        'arm64' for Apple Silicon (M1/M2/M3)
        'x86_64' for Intel
        None if not macOS
    """
    if platform.system() != "Darwin":
        return None
    
    try:
        # Use uname to get the machine architecture
        result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        arch = result.stdout.strip()
        return arch
    except Exception as e:
        logger.error(f"Failed to detect Mac architecture: {e}")
        return None


def check_sentence_transformers_compatibility() -> Tuple[bool, str]:
    """
    Check if sentence-transformers can run on current system.
    
    Returns:
        (is_compatible, message)
    """
    # First check if we're on macOS
    if platform.system() != "Darwin":
        return True, "Not on macOS, assuming compatible"
    
    arch = get_mac_architecture()
    
    if arch == "x86_64":
        # Intel Mac - known compatibility issues
        return False, (
            "🚨 Semantic search is currently not available on Intel Macs.\n"
            "   This is due to compatibility issues with sentence-transformers.\n"
            "   We're working on a solution! In the meantime:\n"
            "   • BM25 search is fully functional\n"
            "   • All other ArXiv tools work perfectly\n"
            "   • Consider using a cloud instance or Apple Silicon Mac for semantic search"
        )
    elif arch == "arm64":
        # Apple Silicon - should work
        return True, "Apple Silicon Mac detected - semantic search available"
    else:
        # Unknown architecture
        return False, f"Unknown Mac architecture: {arch}"


def check_semantic_search_availability() -> Tuple[bool, Optional[str]]:
    """
    Complete check for semantic search availability.
    
    Returns:
        (is_available, error_message)
    """
    # First check Mac compatibility
    is_compatible, message = check_sentence_transformers_compatibility()
    if not is_compatible:
        return False, message
    
    # Then check if sentence-transformers is installed
    try:
        import sentence_transformers
        return True, None
    except ImportError:
        return False, (
            "📦 Sentence-transformers not installed.\n"
            "   Install with: pip install sentence-transformers"
        )
    except Exception as e:
        return False, f"Error loading sentence-transformers: {str(e)}"


def get_compatibility_info() -> Dict[str, any]:
    """Get detailed compatibility information."""
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    
    if platform.system() == "Darwin":
        info["mac_architecture"] = get_mac_architecture()
        info["is_apple_silicon"] = info["mac_architecture"] == "arm64"
        info["is_intel_mac"] = info["mac_architecture"] == "x86_64"
    
    # Check semantic search
    is_available, message = check_semantic_search_availability()
    info["semantic_search_available"] = is_available
    info["semantic_search_message"] = message
    
    return info


# Validation
if __name__ == "__main__":
    import json
    
    print("=" * 80)
    print("MAC COMPATIBILITY CHECK")
    print("=" * 80)
    
    info = get_compatibility_info()
    
    print("\nSystem Information:")
    print(f"Platform: {info['platform']}")
    print(f"Machine: {info['machine']}")
    
    if info['platform'] == 'Darwin':
        print(f"Mac Architecture: {info.get('mac_architecture', 'Unknown')}")
        print(f"Is Apple Silicon: {info.get('is_apple_silicon', False)}")
        print(f"Is Intel Mac: {info.get('is_intel_mac', False)}")
    
    print("\nSemantic Search Status:")
    if info['semantic_search_available']:
        print("✅ Semantic search is available!")
    else:
        print("❌ Semantic search is NOT available")
        print(info['semantic_search_message'])
    
    print("\n" + "=" * 80)
    print("Full compatibility info:")
    print(json.dumps(info, indent=2))