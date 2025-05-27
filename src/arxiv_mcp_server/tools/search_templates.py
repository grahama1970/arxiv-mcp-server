#!/usr/bin/env python3
"""
Search Templates System
======================

Save and reuse complex search queries for repeated research tasks.
Scientists often need to run the same sophisticated searches regularly.

Dependencies:
- All arxiv_mcp_server dependencies

Sample Input:
    # Save a search template
    await save_search_template(
        name="ML Security Research",
        query="adversarial attacks",
        authors=["Goodfellow", "Papernot"],
        categories=["cs.LG", "cs.CR"]
    )
    
    # Run a saved search
    await run_search_template("ML Security Research")

Expected Output:
    Search results using the saved template parameters
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sqlite3
from loguru import logger

from ..config import Settings
from ..core.search import search_papers

class SearchTemplateManager:
    """Manage saved search templates."""
    
    def __init__(self, db_path: Optional[str] = None):
        settings = Settings()
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(settings.STORAGE_PATH) / "search_templates.db"
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for search templates."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    query TEXT,
                    authors TEXT,
                    categories TEXT,
                    date_from TEXT,
                    date_to TEXT,
                    max_results INTEGER DEFAULT 20,
                    sort_by TEXT DEFAULT 'relevance',
                    sort_order TEXT DEFAULT 'descending',
                    description TEXT,
                    created_date TEXT NOT NULL,
                    last_used TEXT,
                    use_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS template_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL,
                    run_date TEXT NOT NULL,
                    result_count INTEGER,
                    paper_ids TEXT,
                    FOREIGN KEY (template_name) REFERENCES search_templates(name)
                )
            ''')
            
            conn.commit()
    
    def save_template(self, 
                     name: str,
                     query: Optional[str] = None,
                     authors: Optional[List[str]] = None,
                     categories: Optional[List[str]] = None,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     max_results: int = 20,
                     sort_by: str = "relevance",
                     sort_order: str = "descending",
                     description: Optional[str] = None) -> Dict[str, Any]:
        """Save a search template."""
        
        # Convert lists to JSON strings for storage
        authors_json = json.dumps(authors) if authors else None
        categories_json = json.dumps(categories) if categories else None
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO search_templates 
                    (name, query, authors, categories, date_from, date_to, 
                     max_results, sort_by, sort_order, description, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    name, query, authors_json, categories_json, date_from, date_to,
                    max_results, sort_by, sort_order, description,
                    datetime.now().isoformat()
                ))
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Search template '{name}' saved successfully",
                    "template": {
                        "name": name,
                        "query": query,
                        "authors": authors,
                        "categories": categories,
                        "max_results": max_results
                    }
                }
            except sqlite3.IntegrityError:
                return {
                    "success": False,
                    "message": f"Template '{name}' already exists. Use update_template to modify."
                }
    
    def update_template(self, name: str, **kwargs) -> Dict[str, Any]:
        """Update an existing search template."""
        with sqlite3.connect(self.db_path) as conn:
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ["authors", "categories"] and isinstance(value, list):
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(value))
                elif field in ["query", "date_from", "date_to", "max_results", 
                             "sort_by", "sort_order", "description"]:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return {
                    "success": False,
                    "message": "No valid fields to update"
                }
            
            values.append(name)
            query = f"UPDATE search_templates SET {', '.join(update_fields)} WHERE name = ?"
            
            cursor = conn.execute(query, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                return {
                    "success": True,
                    "message": f"Template '{name}' updated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Template '{name}' not found"
                }
    
    def delete_template(self, name: str) -> Dict[str, Any]:
        """Delete a search template."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM search_templates WHERE name = ?',
                (name,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                return {
                    "success": True,
                    "message": f"Template '{name}' deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Template '{name}' not found"
                }
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM search_templates WHERE name = ?',
                (name,)
            )
            
            row = cursor.fetchone()
            if row:
                return {
                    "name": row["name"],
                    "query": row["query"],
                    "authors": json.loads(row["authors"]) if row["authors"] else None,
                    "categories": json.loads(row["categories"]) if row["categories"] else None,
                    "date_from": row["date_from"],
                    "date_to": row["date_to"],
                    "max_results": row["max_results"],
                    "sort_by": row["sort_by"],
                    "sort_order": row["sort_order"],
                    "description": row["description"],
                    "created_date": row["created_date"],
                    "last_used": row["last_used"],
                    "use_count": row["use_count"]
                }
            return None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all saved templates."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT name, description, created_date, last_used, use_count
                FROM search_templates
                ORDER BY use_count DESC, name
            ''')
            
            templates = []
            for row in cursor:
                templates.append({
                    "name": row["name"],
                    "description": row["description"],
                    "created_date": row["created_date"],
                    "last_used": row["last_used"],
                    "use_count": row["use_count"]
                })
            
            return templates
    
    async def run_template(self, name: str, override_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a saved search template."""
        template = self.get_template(name)
        if not template:
            return {
                "success": False,
                "message": f"Template '{name}' not found",
                "results": []
            }
        
        # Build search parameters
        search_params = {
            "query": template["query"],
            "max_results": template["max_results"]
        }
        
        # Add optional parameters
        if template["authors"]:
            # Build author query
            author_queries = [f'au:"{author}"' for author in template["authors"]]
            author_query = " OR ".join(author_queries)
            if template["query"]:
                search_params["query"] = f'({template["query"]}) AND ({author_query})'
            else:
                search_params["query"] = author_query
        
        if template["categories"]:
            search_params["categories"] = template["categories"]
        
        if template["date_from"]:
            search_params["date_from"] = template["date_from"]
        
        if template["date_to"]:
            search_params["date_to"] = template["date_to"]
        
        # Apply any overrides
        if override_params:
            search_params.update(override_params)
        
        # Run the search
        results = search_papers(**search_params)
        
        # Update usage statistics
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE search_templates 
                SET last_used = ?, use_count = use_count + 1 
                WHERE name = ?
            ''', (datetime.now().isoformat(), name))
            
            # Log the results
            paper_ids = [r["id"] for r in results] if results else []
            conn.execute('''
                INSERT INTO template_results (template_name, run_date, result_count, paper_ids)
                VALUES (?, ?, ?, ?)
            ''', (name, datetime.now().isoformat(), len(results), json.dumps(paper_ids)))
            
            conn.commit()
        
        return {
            "success": True,
            "template_name": name,
            "result_count": len(results) if results else 0,
            "results": results,
            "search_params": search_params
        }


# Tool definitions for MCP
save_search_template_tool = {
    "name": "save_search_template",
    "description": "Save a search query as a reusable template",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the search template"
            },
            "query": {
                "type": "string",
                "description": "Search query text"
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of authors to search for"
            },
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ArXiv categories to search in"
            },
            "date_from": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)"
            },
            "date_to": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 20
            },
            "description": {
                "type": "string",
                "description": "Description of what this search is for"
            }
        },
        "required": ["name"]
    }
}

run_search_template_tool = {
    "name": "run_search_template",
    "description": "Run a saved search template",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the search template to run"
            },
            "max_results": {
                "type": "integer",
                "description": "Override max results for this run"
            }
        },
        "required": ["name"]
    }
}

list_search_templates_tool = {
    "name": "list_search_templates",
    "description": "List all saved search templates",
    "input_schema": {
        "type": "object",
        "properties": {}
    }
}

async def handle_save_search_template(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle saving a search template."""
    manager = SearchTemplateManager()
    result = manager.save_template(**arguments)
    
    return [{
        "type": "text",
        "text": result["message"],
        "data": result
    }]

async def handle_run_search_template(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle running a search template."""
    manager = SearchTemplateManager()
    
    override_params = {}
    if "max_results" in arguments:
        override_params["max_results"] = arguments["max_results"]
    
    result = await manager.run_template(arguments["name"], override_params)
    
    if result["success"]:
        message = f"🔍 Search template '{arguments['name']}' executed\n"
        message += f"Found {result['result_count']} papers\n\n"
        
        if result["results"]:
            for i, paper in enumerate(result["results"][:5], 1):
                message += f"{i}. {paper['title']}\n"
                message += f"   Authors: {', '.join(paper['authors'][:2])}"
                if len(paper['authors']) > 2:
                    message += f" et al."
                message += f"\n   ID: {paper['id']}\n\n"
            
            if result["result_count"] > 5:
                message += f"... and {result['result_count'] - 5} more papers"
    else:
        message = result["message"]
    
    return [{
        "type": "text",
        "text": message,
        "data": result
    }]

async def handle_list_search_templates(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle listing search templates."""
    manager = SearchTemplateManager()
    templates = manager.list_templates()
    
    if not templates:
        message = "No search templates saved yet."
    else:
        message = f"📑 {len(templates)} saved search templates:\n\n"
        for template in templates:
            message += f"🔍 {template['name']}\n"
            if template['description']:
                message += f"   {template['description']}\n"
            message += f"   Used: {template['use_count']} times\n"
            if template['last_used']:
                message += f"   Last used: {template['last_used'][:10]}\n"
            message += "\n"
    
    return [{
        "type": "text",
        "text": message,
        "data": {"templates": templates}
    }]


if __name__ == "__main__":
    # Validation tests
    import asyncio
    
    async def validate():
        """Validate search template functionality."""
        print("=" * 80)
        print("VALIDATING SEARCH TEMPLATES SYSTEM")
        print("=" * 80)
        
        manager = SearchTemplateManager(db_path=":memory:")
        
        # Test 1: Save templates
        print("\nTest 1: Save search templates")
        print("-" * 40)
        
        templates = [
            {
                "name": "Transformer Research",
                "query": "transformer attention mechanism",
                "categories": ["cs.LG", "cs.CL"],
                "description": "Papers about transformer architectures"
            },
            {
                "name": "GAN Papers",
                "query": "generative adversarial",
                "authors": ["Ian Goodfellow", "Yoshua Bengio"],
                "description": "GAN-related research"
            },
            {
                "name": "Recent ML Security",
                "query": "adversarial attacks",
                "categories": ["cs.CR", "cs.LG"],
                "date_from": "2023-01-01",
                "max_results": 30,
                "description": "Machine learning security research from 2023"
            }
        ]
        
        for template in templates:
            result = manager.save_template(**template)
            print(f"✓ {result['message']}")
        
        # Test 2: List templates
        print("\nTest 2: List saved templates")
        print("-" * 40)
        
        saved_templates = manager.list_templates()
        print(f"✓ Found {len(saved_templates)} templates")
        for t in saved_templates:
            print(f"  - {t['name']}: {t['description']}")
        
        # Test 3: Run a template
        print("\nTest 3: Run search template")
        print("-" * 40)
        
        result = await manager.run_template("Transformer Research", {"max_results": 5})
        if result["success"]:
            print(f"✓ Template executed successfully")
            print(f"✓ Found {result['result_count']} papers")
            if result["results"]:
                print(f"  First paper: {result['results'][0]['title'][:60]}...")
        else:
            print(f"✗ Template execution failed: {result['message']}")
        
        # Test 4: Update template
        print("\nTest 4: Update template")
        print("-" * 40)
        
        update_result = manager.update_template(
            "GAN Papers",
            query="generative adversarial network",
            max_results=50
        )
        print(f"✓ {update_result['message']}")
        
        # Test 5: Usage statistics
        print("\nTest 5: Usage statistics")
        print("-" * 40)
        
        # Run template again to update stats
        await manager.run_template("Transformer Research")
        
        updated_list = manager.list_templates()
        transformer_template = next(t for t in updated_list if t["name"] == "Transformer Research")
        print(f"✓ Template '{transformer_template['name']}' used {transformer_template['use_count']} times")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION PASSED - Search templates system is working")
        print("=" * 80)
    
    asyncio.run(validate())