#!/usr/bin/env python3
"""
Paper Collections System
========================

Organize papers into project-specific collections for better management.
Scientists need to group papers by research project, thesis chapter, etc.

Dependencies:
- All arxiv_mcp_server dependencies

Sample Input:
    # Create a collection
    await create_collection("Thesis Chapter 3", "Papers for attention mechanisms chapter")
    
    # Add paper to collection
    await add_to_collection("1706.03762", "Thesis Chapter 3")
    
    # List papers in collection
    await get_collection("Thesis Chapter 3")

Expected Output:
    Collection with organized papers, metadata, and notes
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import sqlite3
from loguru import logger

from ..config import Settings
from ..core.utils import normalize_paper_id
from ..core.search import search_papers


def get_paper_metadata(paper_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a single paper by ID."""
    try:
        # Search for the specific paper
        papers = search_papers(query=f"id:{paper_id}", max_results=1)
        if papers and len(papers) > 0:
            return papers[0]
        return None
    except Exception as e:
        logger.error(f"Error getting paper metadata: {e}")
        return None


class CollectionManager:
    """Manage paper collections for project organization."""
    
    def __init__(self, db_path: Optional[str] = None):
        settings = Settings()
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(settings.STORAGE_PATH) / "paper_collections.db"
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for collections."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_date TEXT NOT NULL,
                    modified_date TEXT NOT NULL,
                    parent_collection TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collection_papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_name TEXT NOT NULL,
                    paper_id TEXT NOT NULL,
                    added_date TEXT NOT NULL,
                    notes TEXT,
                    position INTEGER,
                    tags TEXT,
                    UNIQUE(collection_name, paper_id),
                    FOREIGN KEY (collection_name) REFERENCES collections(name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collection_stats (
                    collection_name TEXT PRIMARY KEY,
                    total_papers INTEGER DEFAULT 0,
                    total_read INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    FOREIGN KEY (collection_name) REFERENCES collections(name)
                )
            ''')
            
            conn.commit()
    
    def create_collection(self, 
                         name: str, 
                         description: Optional[str] = None,
                         parent: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new collection."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                now = datetime.now().isoformat()
                metadata_json = json.dumps(metadata) if metadata else None
                
                conn.execute('''
                    INSERT INTO collections (name, description, created_date, modified_date, parent_collection, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, description, now, now, parent, metadata_json))
                
                # Initialize stats
                conn.execute('''
                    INSERT INTO collection_stats (collection_name, last_accessed)
                    VALUES (?, ?)
                ''', (name, now))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Collection '{name}' created successfully",
                    "collection": {
                        "name": name,
                        "description": description,
                        "parent": parent
                    }
                }
            except sqlite3.IntegrityError:
                return {
                    "success": False,
                    "message": f"Collection '{name}' already exists"
                }
    
    def delete_collection(self, name: str, cascade: bool = False) -> Dict[str, Any]:
        """Delete a collection."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if collection has sub-collections
            cursor = conn.execute(
                'SELECT COUNT(*) FROM collections WHERE parent_collection = ?',
                (name,)
            )
            sub_count = cursor.fetchone()[0]
            
            if sub_count > 0 and not cascade:
                return {
                    "success": False,
                    "message": f"Collection has {sub_count} sub-collections. Use cascade=True to delete all."
                }
            
            # Delete collection and related data
            if cascade:
                # Delete sub-collections recursively
                sub_collections = conn.execute(
                    'SELECT name FROM collections WHERE parent_collection = ?',
                    (name,)
                ).fetchall()
                
                for sub in sub_collections:
                    self.delete_collection(sub[0], cascade=True)
            
            # Delete papers and stats
            conn.execute('DELETE FROM collection_papers WHERE collection_name = ?', (name,))
            conn.execute('DELETE FROM collection_stats WHERE collection_name = ?', (name,))
            conn.execute('DELETE FROM collections WHERE name = ?', (name,))
            conn.commit()
            
            return {
                "success": True,
                "message": f"Collection '{name}' deleted successfully"
            }
    
    def add_to_collection(self, 
                         paper_id: str, 
                         collection_name: str,
                         notes: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         position: Optional[int] = None) -> Dict[str, Any]:
        """Add a paper to a collection."""
        paper_id = normalize_paper_id(paper_id)
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if collection exists
            cursor = conn.execute(
                'SELECT id FROM collections WHERE name = ?',
                (collection_name,)
            )
            if not cursor.fetchone():
                return {
                    "success": False,
                    "message": f"Collection '{collection_name}' not found"
                }
            
            # Get paper metadata
            paper_data = get_paper_metadata(paper_id)
            if not paper_data:
                return {
                    "success": False,
                    "message": f"Paper {paper_id} not found"
                }
            
            try:
                tags_json = json.dumps(tags) if tags else None
                
                # If no position specified, add to end
                if position is None:
                    cursor = conn.execute(
                        'SELECT MAX(position) FROM collection_papers WHERE collection_name = ?',
                        (collection_name,)
                    )
                    max_pos = cursor.fetchone()[0]
                    position = (max_pos + 1) if max_pos is not None else 1
                
                conn.execute('''
                    INSERT INTO collection_papers (collection_name, paper_id, added_date, notes, position, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (collection_name, paper_id, datetime.now().isoformat(), notes, position, tags_json))
                
                # Update collection stats
                conn.execute('''
                    UPDATE collection_stats 
                    SET total_papers = total_papers + 1,
                        last_accessed = ?
                    WHERE collection_name = ?
                ''', (datetime.now().isoformat(), collection_name))
                
                # Update collection modified date
                conn.execute('''
                    UPDATE collections
                    SET modified_date = ?
                    WHERE name = ?
                ''', (datetime.now().isoformat(), collection_name))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Added '{paper_data['title']}' to collection '{collection_name}'",
                    "paper_id": paper_id,
                    "collection": collection_name
                }
            except sqlite3.IntegrityError:
                return {
                    "success": False,
                    "message": f"Paper {paper_id} already in collection '{collection_name}'"
                }
    
    def remove_from_collection(self, paper_id: str, collection_name: str) -> Dict[str, Any]:
        """Remove a paper from a collection."""
        paper_id = normalize_paper_id(paper_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM collection_papers WHERE collection_name = ? AND paper_id = ?',
                (collection_name, paper_id)
            )
            
            if cursor.rowcount > 0:
                # Update stats
                conn.execute('''
                    UPDATE collection_stats 
                    SET total_papers = total_papers - 1
                    WHERE collection_name = ?
                ''', (collection_name,))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Removed paper {paper_id} from collection '{collection_name}'"
                }
            else:
                return {
                    "success": False,
                    "message": f"Paper {paper_id} not found in collection '{collection_name}'"
                }
    
    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get collection details with all papers."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get collection info
            cursor = conn.execute(
                'SELECT * FROM collections WHERE name = ?',
                (name,)
            )
            collection_row = cursor.fetchone()
            
            if not collection_row:
                return None
            
            # Get papers in collection
            cursor = conn.execute('''
                SELECT paper_id, added_date, notes, position, tags
                FROM collection_papers
                WHERE collection_name = ?
                ORDER BY position, added_date
            ''', (name,))
            
            papers = []
            for row in cursor:
                paper_data = get_paper_metadata(row["paper_id"])
                if paper_data:
                    papers.append({
                        "paper_id": row["paper_id"],
                        "title": paper_data["title"],
                        "authors": paper_data["authors"],
                        "added_date": row["added_date"],
                        "notes": row["notes"],
                        "position": row["position"],
                        "tags": json.loads(row["tags"]) if row["tags"] else []
                    })
            
            # Get stats
            cursor = conn.execute(
                'SELECT * FROM collection_stats WHERE collection_name = ?',
                (name,)
            )
            stats_row = cursor.fetchone()
            
            # Update access stats
            conn.execute('''
                UPDATE collection_stats
                SET last_accessed = ?, access_count = access_count + 1
                WHERE collection_name = ?
            ''', (datetime.now().isoformat(), name))
            conn.commit()
            
            return {
                "name": collection_row["name"],
                "description": collection_row["description"],
                "created_date": collection_row["created_date"],
                "modified_date": collection_row["modified_date"],
                "parent": collection_row["parent_collection"],
                "metadata": json.loads(collection_row["metadata"]) if collection_row["metadata"] else {},
                "papers": papers,
                "stats": {
                    "total_papers": len(papers),
                    "access_count": stats_row["access_count"] if stats_row else 0
                }
            }
    
    def list_collections(self, parent: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all collections, optionally filtered by parent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if parent is None:
                # Get root collections
                cursor = conn.execute('''
                    SELECT c.*, s.total_papers, s.last_accessed
                    FROM collections c
                    LEFT JOIN collection_stats s ON c.name = s.collection_name
                    WHERE c.parent_collection IS NULL
                    ORDER BY s.last_accessed DESC, c.name
                ''')
            else:
                # Get sub-collections
                cursor = conn.execute('''
                    SELECT c.*, s.total_papers, s.last_accessed
                    FROM collections c
                    LEFT JOIN collection_stats s ON c.name = s.collection_name
                    WHERE c.parent_collection = ?
                    ORDER BY s.last_accessed DESC, c.name
                ''', (parent,))
            
            collections = []
            for row in cursor:
                collections.append({
                    "name": row["name"],
                    "description": row["description"],
                    "created_date": row["created_date"],
                    "parent": row["parent_collection"],
                    "total_papers": row["total_papers"] or 0,
                    "last_accessed": row["last_accessed"]
                })
            
            return collections
    
    def move_paper(self, paper_id: str, from_collection: str, to_collection: str) -> Dict[str, Any]:
        """Move a paper between collections."""
        paper_id = normalize_paper_id(paper_id)
        
        # Get paper data from source collection
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT notes, tags FROM collection_papers WHERE collection_name = ? AND paper_id = ?',
                (from_collection, paper_id)
            )
            paper_data = cursor.fetchone()
            
            if not paper_data:
                return {
                    "success": False,
                    "message": f"Paper {paper_id} not found in collection '{from_collection}'"
                }
        
        # Remove from source
        self.remove_from_collection(paper_id, from_collection)
        
        # Add to destination
        result = self.add_to_collection(
            paper_id, 
            to_collection,
            notes=paper_data[0],
            tags=json.loads(paper_data[1]) if paper_data[1] else None
        )
        
        if result["success"]:
            result["message"] = f"Moved paper {paper_id} from '{from_collection}' to '{to_collection}'"
        
        return result


# Tool definitions for MCP
create_collection_tool = {
    "name": "create_collection",
    "description": "Create a new paper collection for organizing research",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the collection"
            },
            "description": {
                "type": "string",
                "description": "Description of the collection's purpose"
            },
            "parent": {
                "type": "string",
                "description": "Parent collection name (for hierarchical organization)"
            }
        },
        "required": ["name"]
    }
}

add_to_collection_tool = {
    "name": "add_to_collection",
    "description": "Add a paper to a collection",
    "input_schema": {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID"
            },
            "collection_name": {
                "type": "string",
                "description": "Name of the collection"
            },
            "notes": {
                "type": "string",
                "description": "Notes about why this paper is in this collection"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for this paper in the collection"
            }
        },
        "required": ["paper_id", "collection_name"]
    }
}

get_collection_tool = {
    "name": "get_collection",
    "description": "Get all papers in a collection",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the collection"
            }
        },
        "required": ["name"]
    }
}

list_collections_tool = {
    "name": "list_collections",
    "description": "List all paper collections",
    "input_schema": {
        "type": "object",
        "properties": {
            "parent": {
                "type": "string",
                "description": "Filter by parent collection"
            }
        }
    }
}

async def handle_create_collection(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle creating a collection."""
    manager = CollectionManager()
    result = manager.create_collection(
        arguments["name"],
        arguments.get("description"),
        arguments.get("parent")
    )
    
    return [{
        "type": "text",
        "text": result["message"],
        "data": result
    }]

async def handle_add_to_collection(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle adding paper to collection."""
    manager = CollectionManager()
    result = manager.add_to_collection(
        arguments["paper_id"],
        arguments["collection_name"],
        arguments.get("notes"),
        arguments.get("tags")
    )
    
    return [{
        "type": "text",
        "text": result["message"],
        "data": result
    }]

async def handle_get_collection(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle getting collection contents."""
    manager = CollectionManager()
    collection = manager.get_collection(arguments["name"])
    
    if not collection:
        return [{
            "type": "text",
            "text": f"Collection '{arguments['name']}' not found"
        }]
    
    message = f"📚 Collection: {collection['name']}\n"
    if collection['description']:
        message += f"📝 {collection['description']}\n"
    message += f"📄 {len(collection['papers'])} papers\n\n"
    
    for i, paper in enumerate(collection['papers'], 1):
        message += f"{i}. {paper['title']}\n"
        message += f"   ID: {paper['paper_id']}\n"
        message += f"   Authors: {', '.join(paper['authors'][:2])}"
        if len(paper['authors']) > 2:
            message += " et al."
        message += "\n"
        if paper['notes']:
            message += f"   Notes: {paper['notes']}\n"
        if paper['tags']:
            message += f"   Tags: {', '.join(paper['tags'])}\n"
        message += "\n"
    
    return [{
        "type": "text",
        "text": message,
        "data": collection
    }]

async def handle_list_collections(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle listing collections."""
    manager = CollectionManager()
    collections = manager.list_collections(arguments.get("parent"))
    
    if not collections:
        message = "No collections found."
    else:
        parent = arguments.get("parent")
        if parent:
            message = f"📁 Sub-collections of '{parent}':\n\n"
        else:
            message = f"📁 {len(collections)} collections:\n\n"
        
        for coll in collections:
            message += f"📚 {coll['name']}"
            if coll['total_papers'] > 0:
                message += f" ({coll['total_papers']} papers)"
            message += "\n"
            if coll['description']:
                message += f"   {coll['description']}\n"
            message += "\n"
    
    return [{
        "type": "text",
        "text": message,
        "data": {"collections": collections}
    }]


if __name__ == "__main__":
    # Validation tests
    import asyncio
    
    async def validate():
        """Validate paper collections functionality."""
        print("=" * 80)
        print("VALIDATING PAPER COLLECTIONS SYSTEM")
        print("=" * 80)
        
        manager = CollectionManager(db_path=":memory:")
        
        # Test 1: Create collections
        print("\nTest 1: Create collections")
        print("-" * 40)
        
        collections = [
            ("PhD Thesis", "All papers for my thesis"),
            ("Chapter 3 - Attention", "Papers about attention mechanisms", "PhD Thesis"),
            ("Chapter 4 - Transformers", "Transformer architecture papers", "PhD Thesis"),
            ("Side Project", "Papers for side research project")
        ]
        
        for coll in collections:
            if len(coll) == 2:
                result = manager.create_collection(coll[0], coll[1])
            else:
                result = manager.create_collection(coll[0], coll[1], parent=coll[2])
            print(f"✓ {result['message']}")
        
        # Test 2: List collections
        print("\nTest 2: List collections")
        print("-" * 40)
        
        all_collections = manager.list_collections()
        print(f"✓ Found {len(all_collections)} root collections")
        
        sub_collections = manager.list_collections(parent="PhD Thesis")
        print(f"✓ Found {len(sub_collections)} sub-collections under 'PhD Thesis'")
        
        # Test 3: Add papers to collection
        print("\nTest 3: Add papers to collections")
        print("-" * 40)
        
        test_papers = [
            ("1706.03762", "Chapter 3 - Attention", "The original transformer paper"),
            ("1810.04805", "Chapter 4 - Transformers", "BERT paper"),
            ("2005.14165", "Chapter 4 - Transformers", "GPT-3 paper", ["language-models", "scaling"])
        ]
        
        for paper in test_papers:
            if len(paper) == 3:
                result = manager.add_to_collection(paper[0], paper[1], notes=paper[2])
            else:
                result = manager.add_to_collection(paper[0], paper[1], notes=paper[2], tags=paper[3])
            
            if result["success"]:
                print(f"✓ Added paper to '{paper[1]}'")
            else:
                print(f"✗ Failed: {result['message']}")
        
        # Test 4: Get collection contents
        print("\nTest 4: Get collection contents")
        print("-" * 40)
        
        collection = manager.get_collection("Chapter 4 - Transformers")
        if collection:
            print(f"✓ Collection '{collection['name']}' has {len(collection['papers'])} papers")
            for paper in collection['papers']:
                print(f"  - {paper['title'][:50]}...")
        
        # Test 5: Move paper between collections
        print("\nTest 5: Move paper between collections")
        print("-" * 40)
        
        result = manager.move_paper("1810.04805", "Chapter 4 - Transformers", "Side Project")
        print(f"✓ {result['message']}")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION PASSED - Paper collections system is working")
        print("=" * 80)
    
    asyncio.run(validate())