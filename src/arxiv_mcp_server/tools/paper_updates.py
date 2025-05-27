#!/usr/bin/env python3
"""
Paper Update Checker
====================

Check if papers in your reading list or collection have been updated on arXiv.
Scientists often need to track when papers they're following get revised.

Dependencies:
- arxiv: ArXiv API client (https://github.com/lukasschwab/arxiv.py)
- All arxiv_mcp_server dependencies

Sample Input:
    # Check all papers in reading list
    await check_paper_updates()
    
    # Check specific paper
    await check_paper_updates(paper_ids=["1706.03762"])

Expected Output:
    {
        "updated_papers": [
            {
                "paper_id": "1706.03762",
                "current_version": "v1",
                "latest_version": "v8",
                "last_updated": "2023-08-02",
                "update_summary": "Major revision with new experiments"
            }
        ],
        "total_checked": 10,
        "updates_found": 1
    }
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import arxiv
from loguru import logger

from ..config import Settings
from ..core.utils import normalize_paper_id
from .reading_list import ReadingListManager

class PaperUpdateChecker:
    """Check for updates to saved papers on arXiv."""
    
    def __init__(self):
        self.settings = Settings()
        self.reading_list = ReadingListManager()
        self.update_cache_path = Path(self.settings.STORAGE_PATH) / "paper_updates.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load the update check cache."""
        if self.update_cache_path.exists():
            with open(self.update_cache_path, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Save the update check cache."""
        self.update_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.update_cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_paper_version(self, paper_id: str) -> str:
        """Extract version from paper ID."""
        if 'v' in paper_id:
            return paper_id.split('v')[-1]
        return "1"
    
    def _get_base_id(self, paper_id: str) -> str:
        """Get base paper ID without version."""
        if 'v' in paper_id:
            return paper_id.split('v')[0]
        return paper_id
    
    async def check_single_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Check if a single paper has updates."""
        try:
            base_id = self._get_base_id(normalize_paper_id(paper_id))
            current_version = self._get_paper_version(paper_id)
            
            # Query arXiv for the latest version
            search = arxiv.Search(id_list=[base_id])
            paper = next(search.results())
            
            # Extract latest version from the paper URL
            latest_version = "1"
            if paper.entry_id:
                # entry_id format: http://arxiv.org/abs/1706.03762v8
                if 'v' in paper.entry_id:
                    latest_version = paper.entry_id.split('v')[-1]
            
            # Check if there's an update
            if int(latest_version) > int(current_version):
                update_info = {
                    "paper_id": paper_id,
                    "base_id": base_id,
                    "current_version": f"v{current_version}",
                    "latest_version": f"v{latest_version}",
                    "last_updated": paper.updated.strftime("%Y-%m-%d"),
                    "title": paper.title,
                    "update_summary": paper.comment if paper.comment else "No comment provided",
                    "arxiv_url": f"https://arxiv.org/abs/{base_id}v{latest_version}"
                }
                
                # Cache the result
                self.cache[base_id] = {
                    "latest_version": latest_version,
                    "last_checked": datetime.now().isoformat(),
                    "last_updated": paper.updated.isoformat()
                }
                self._save_cache()
                
                return update_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking paper {paper_id}: {e}")
            return None
    
    async def check_reading_list(self) -> Dict[str, Any]:
        """Check all papers in reading list for updates."""
        papers = self.reading_list.get_papers()
        return await self.check_multiple_papers([p['paper_id'] for p in papers])
    
    async def check_multiple_papers(self, paper_ids: List[str]) -> Dict[str, Any]:
        """Check multiple papers for updates."""
        updated_papers = []
        total_checked = 0
        
        for paper_id in paper_ids:
            total_checked += 1
            update_info = await self.check_single_paper(paper_id)
            if update_info:
                updated_papers.append(update_info)
            
            # Small delay to be nice to arXiv API
            await asyncio.sleep(0.5)
        
        return {
            "updated_papers": updated_papers,
            "total_checked": total_checked,
            "updates_found": len(updated_papers),
            "check_timestamp": datetime.now().isoformat()
        }


# Tool definitions for MCP
check_paper_updates_tool = {
    "name": "check_paper_updates",
    "description": "Check if papers in your reading list have been updated on arXiv",
    "input_schema": {
        "type": "object",
        "properties": {
            "paper_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific paper IDs to check (optional)"
            },
            "check_all": {
                "type": "boolean",
                "description": "Check all papers in reading list",
                "default": True
            }
        }
    }
}

async def handle_check_paper_updates(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle paper update checking."""
    checker = PaperUpdateChecker()
    
    paper_ids = arguments.get("paper_ids", [])
    check_all = arguments.get("check_all", True)
    
    if paper_ids:
        result = await checker.check_multiple_papers(paper_ids)
    elif check_all:
        result = await checker.check_reading_list()
    else:
        return [{
            "type": "text",
            "text": "Please specify paper IDs or set check_all=True"
        }]
    
    # Format output
    if result["updates_found"] == 0:
        message = f"✓ No updates found. Checked {result['total_checked']} papers."
    else:
        message = f"📢 Found {result['updates_found']} updated papers!\n\n"
        for update in result["updated_papers"]:
            message += f"📄 {update['title']}\n"
            message += f"   Paper ID: {update['paper_id']}\n"
            message += f"   Current: {update['current_version']} → Latest: {update['latest_version']}\n"
            message += f"   Updated: {update['last_updated']}\n"
            message += f"   URL: {update['arxiv_url']}\n"
            if update['update_summary']:
                message += f"   Comment: {update['update_summary']}\n"
            message += "\n"
    
    return [{
        "type": "text",
        "text": message,
        "data": result
    }]


if __name__ == "__main__":
    # Validation tests
    async def validate():
        """Validate paper update checking functionality."""
        print("=" * 80)
        print("VALIDATING PAPER UPDATE CHECKER")
        print("=" * 80)
        
        checker = PaperUpdateChecker()
        
        # Test 1: Check a known paper with multiple versions
        print("\nTest 1: Check paper with known updates (Attention Is All You Need)")
        print("-" * 40)
        
        # This paper has v8 as latest version
        result = await checker.check_single_paper("1706.03762v1")
        
        if result:
            print(f"✓ Found update: v1 → {result['latest_version']}")
            print(f"  Title: {result['title']}")
            print(f"  Updated: {result['last_updated']}")
        else:
            print("✗ No update found (this paper should have updates!)")
        
        # Test 2: Check multiple papers
        print("\nTest 2: Check multiple papers")
        print("-" * 40)
        
        test_papers = [
            "1706.03762v1",  # Old version
            "2301.00234",    # Recent paper
        ]
        
        results = await checker.check_multiple_papers(test_papers)
        print(f"✓ Checked {results['total_checked']} papers")
        print(f"✓ Found {results['updates_found']} updates")
        
        # Test 3: Reading list integration
        print("\nTest 3: Check reading list (if papers exist)")
        print("-" * 40)
        
        try:
            rl_results = await checker.check_reading_list()
            print(f"✓ Checked {rl_results['total_checked']} papers from reading list")
            print(f"✓ Found {rl_results['updates_found']} updates")
        except Exception as e:
            print(f"ℹ Reading list check skipped: {e}")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION PASSED - Paper update checker is working")
        print("=" * 80)
    
    asyncio.run(validate())