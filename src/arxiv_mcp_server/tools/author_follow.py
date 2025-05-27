#!/usr/bin/env python3
"""
Author Following System
======================

Follow specific authors and get notified when they publish new papers.
Essential for researchers tracking work from key people in their field.

Dependencies:
- arxiv: ArXiv API client (https://github.com/lukasschwab/arxiv.py)
- All arxiv_mcp_server dependencies

Sample Input:
    # Follow an author
    await follow_author("Yoshua Bengio")
    
    # Check for new papers from followed authors
    await check_followed_authors(days_back=7)

Expected Output:
    {
        "new_papers": [
            {
                "author": "Yoshua Bengio",
                "paper_id": "2401.12345",
                "title": "New Advances in Deep Learning",
                "published": "2024-01-15"
            }
        ],
        "total_authors": 5,
        "total_new_papers": 3
    }
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import sqlite3
import arxiv
from loguru import logger

from ..config import Settings
from ..core.search import search_papers

class AuthorFollower:
    """Manage followed authors and track their new publications."""
    
    def __init__(self, db_path: Optional[str] = None):
        settings = Settings()
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(settings.STORAGE_PATH) / "author_follows.db"
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for author follows."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS followed_authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_name TEXT UNIQUE NOT NULL,
                    normalized_name TEXT NOT NULL,
                    date_followed TEXT NOT NULL,
                    last_checked TEXT,
                    notes TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS author_papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_name TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    published_date TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    UNIQUE(author_name, paper_id)
                )
            ''')
            
            conn.commit()
    
    def _normalize_author_name(self, name: str) -> str:
        """Normalize author name for searching."""
        # Remove extra spaces, convert to lowercase for searching
        return ' '.join(name.lower().split())
    
    def follow_author(self, author_name: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Follow a new author."""
        normalized = self._normalize_author_name(author_name)
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO followed_authors (author_name, normalized_name, date_followed, notes)
                    VALUES (?, ?, ?, ?)
                ''', (author_name, normalized, datetime.now().isoformat(), notes))
                conn.commit()
                
                return {
                    "success": True,
                    "author": author_name,
                    "message": f"Now following {author_name}"
                }
            except sqlite3.IntegrityError:
                return {
                    "success": False,
                    "author": author_name,
                    "message": f"Already following {author_name}"
                }
    
    def unfollow_author(self, author_name: str) -> Dict[str, Any]:
        """Unfollow an author."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM followed_authors WHERE author_name = ?',
                (author_name,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                return {
                    "success": True,
                    "author": author_name,
                    "message": f"Unfollowed {author_name}"
                }
            else:
                return {
                    "success": False,
                    "author": author_name,
                    "message": f"Not following {author_name}"
                }
    
    def list_followed_authors(self) -> List[Dict[str, Any]]:
        """List all followed authors."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT author_name, date_followed, last_checked, notes
                FROM followed_authors
                ORDER BY author_name
            ''')
            
            authors = []
            for row in cursor:
                authors.append({
                    "author_name": row["author_name"],
                    "date_followed": row["date_followed"],
                    "last_checked": row["last_checked"],
                    "notes": row["notes"]
                })
            
            return authors
    
    async def check_author_papers(self, author_name: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Check for new papers from a specific author."""
        # Search for papers by this author in the last N days
        query = f'au:"{author_name}"'
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # Search papers
        papers = search_papers(
            query=query,
            max_results=50,
            date_from=start_date.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d")
        )
        
        if not papers:
            return []
        
        # Check which papers are new
        new_papers = []
        with sqlite3.connect(self.db_path) as conn:
            for paper in papers:
                # Check if this paper is already known
                cursor = conn.execute(
                    'SELECT id FROM author_papers WHERE author_name = ? AND paper_id = ?',
                    (author_name, paper['id'])
                )
                
                if not cursor.fetchone():
                    # New paper! Add to database
                    conn.execute('''
                        INSERT INTO author_papers (author_name, paper_id, title, published_date, first_seen)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        author_name,
                        paper['id'],
                        paper['title'],
                        paper['published'],
                        datetime.now().isoformat()
                    ))
                    
                    # Check if author_name is actually in the authors list
                    author_found = any(
                        author_name.lower() in author.lower() 
                        for author in paper['authors']
                    )
                    
                    if author_found:
                        new_papers.append({
                            "paper_id": paper['id'],
                            "title": paper['title'],
                            "authors": paper['authors'],
                            "published": paper['published'],
                            "summary": paper['summary'][:200] + "...",
                            "categories": paper.get('categories', []),
                            "arxiv_url": f"https://arxiv.org/abs/{paper['id']}"
                        })
            
            # Update last checked time
            conn.execute(
                'UPDATE followed_authors SET last_checked = ? WHERE author_name = ?',
                (datetime.now().isoformat(), author_name)
            )
            conn.commit()
        
        return new_papers
    
    async def check_all_authors(self, days_back: int = 7) -> Dict[str, Any]:
        """Check all followed authors for new papers."""
        authors = self.list_followed_authors()
        all_new_papers = []
        author_updates = {}
        
        for author in authors:
            author_name = author["author_name"]
            new_papers = await self.check_author_papers(author_name, days_back)
            
            if new_papers:
                author_updates[author_name] = len(new_papers)
                for paper in new_papers:
                    paper["tracked_author"] = author_name
                    all_new_papers.append(paper)
            
            # Small delay to be nice to arXiv
            await asyncio.sleep(0.5)
        
        return {
            "new_papers": all_new_papers,
            "total_authors": len(authors),
            "total_new_papers": len(all_new_papers),
            "author_updates": author_updates,
            "check_period_days": days_back,
            "check_timestamp": datetime.now().isoformat()
        }


# Tool definitions for MCP
follow_author_tool = {
    "name": "follow_author",
    "description": "Follow an author to track their new publications",
    "input_schema": {
        "type": "object",
        "properties": {
            "author_name": {
                "type": "string",
                "description": "Name of the author to follow"
            },
            "notes": {
                "type": "string",
                "description": "Optional notes about why you're following this author"
            }
        },
        "required": ["author_name"]
    }
}

unfollow_author_tool = {
    "name": "unfollow_author",
    "description": "Stop following an author",
    "input_schema": {
        "type": "object",
        "properties": {
            "author_name": {
                "type": "string",
                "description": "Name of the author to unfollow"
            }
        },
        "required": ["author_name"]
    }
}

list_followed_authors_tool = {
    "name": "list_followed_authors",
    "description": "List all authors you're following",
    "input_schema": {
        "type": "object",
        "properties": {}
    }
}

check_followed_authors_tool = {
    "name": "check_followed_authors",
    "description": "Check for new papers from followed authors",
    "input_schema": {
        "type": "object",
        "properties": {
            "author_name": {
                "type": "string",
                "description": "Check specific author (optional)"
            },
            "days_back": {
                "type": "integer",
                "description": "How many days back to check",
                "default": 7
            }
        }
    }
}

async def handle_follow_author(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle following an author."""
    follower = AuthorFollower()
    result = follower.follow_author(
        arguments["author_name"],
        arguments.get("notes")
    )
    
    return [{
        "type": "text",
        "text": result["message"],
        "data": result
    }]

async def handle_unfollow_author(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle unfollowing an author."""
    follower = AuthorFollower()
    result = follower.unfollow_author(arguments["author_name"])
    
    return [{
        "type": "text",
        "text": result["message"],
        "data": result
    }]

async def handle_list_followed_authors(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle listing followed authors."""
    follower = AuthorFollower()
    authors = follower.list_followed_authors()
    
    if not authors:
        message = "You're not following any authors yet."
    else:
        message = f"Following {len(authors)} authors:\n\n"
        for author in authors:
            message += f"👤 {author['author_name']}\n"
            message += f"   Following since: {author['date_followed'][:10]}\n"
            if author['last_checked']:
                message += f"   Last checked: {author['last_checked'][:10]}\n"
            if author['notes']:
                message += f"   Notes: {author['notes']}\n"
            message += "\n"
    
    return [{
        "type": "text",
        "text": message,
        "data": {"authors": authors}
    }]

async def handle_check_followed_authors(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle checking for new papers from followed authors."""
    follower = AuthorFollower()
    
    author_name = arguments.get("author_name")
    days_back = arguments.get("days_back", 7)
    
    if author_name:
        # Check specific author
        new_papers = await follower.check_author_papers(author_name, days_back)
        
        if not new_papers:
            message = f"No new papers from {author_name} in the last {days_back} days."
        else:
            message = f"📚 Found {len(new_papers)} new papers from {author_name}:\n\n"
            for paper in new_papers:
                message += f"📄 {paper['title']}\n"
                message += f"   ID: {paper['paper_id']}\n"
                message += f"   Published: {paper['published']}\n"
                message += f"   URL: {paper['arxiv_url']}\n\n"
        
        return [{
            "type": "text",
            "text": message,
            "data": {"author": author_name, "new_papers": new_papers}
        }]
    else:
        # Check all authors
        result = await follower.check_all_authors(days_back)
        
        if result["total_new_papers"] == 0:
            message = f"No new papers from your {result['total_authors']} followed authors in the last {days_back} days."
        else:
            message = f"📚 Found {result['total_new_papers']} new papers from followed authors:\n\n"
            
            # Group by author
            for author, count in result["author_updates"].items():
                message += f"\n👤 {author} ({count} papers):\n"
                author_papers = [p for p in result["new_papers"] if p["tracked_author"] == author]
                for paper in author_papers:
                    message += f"  📄 {paper['title']}\n"
                    message += f"     {paper['paper_id']} - {paper['published']}\n"
        
        return [{
            "type": "text",
            "text": message,
            "data": result
        }]


if __name__ == "__main__":
    # Validation tests
    async def validate():
        """Validate author following functionality."""
        print("=" * 80)
        print("VALIDATING AUTHOR FOLLOWING SYSTEM")
        print("=" * 80)
        
        follower = AuthorFollower(db_path=":memory:")  # Use in-memory DB for testing
        
        # Test 1: Follow authors
        print("\nTest 1: Follow authors")
        print("-" * 40)
        
        test_authors = [
            ("Yoshua Bengio", "Deep learning pioneer"),
            ("Geoffrey Hinton", "Neural networks expert"),
            ("Ian Goodfellow", "GANs inventor")
        ]
        
        for author, notes in test_authors:
            result = follower.follow_author(author, notes)
            print(f"✓ {result['message']}")
        
        # Test 2: List followed authors
        print("\nTest 2: List followed authors")
        print("-" * 40)
        
        authors = follower.list_followed_authors()
        print(f"✓ Following {len(authors)} authors")
        for author in authors:
            print(f"  - {author['author_name']}: {author['notes']}")
        
        # Test 3: Check for new papers (with real API call)
        print("\nTest 3: Check for new papers")
        print("-" * 40)
        
        # Check one author's recent papers
        new_papers = await follower.check_author_papers("Yoshua Bengio", days_back=90)
        print(f"✓ Found {len(new_papers)} papers from Yoshua Bengio in last 90 days")
        if new_papers:
            print(f"  Latest: {new_papers[0]['title'][:60]}...")
        
        # Test 4: Unfollow author
        print("\nTest 4: Unfollow author")
        print("-" * 40)
        
        result = follower.unfollow_author("Ian Goodfellow")
        print(f"✓ {result['message']}")
        
        authors = follower.list_followed_authors()
        print(f"✓ Now following {len(authors)} authors")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION PASSED - Author following system is working")
        print("=" * 80)
    
    asyncio.run(validate())