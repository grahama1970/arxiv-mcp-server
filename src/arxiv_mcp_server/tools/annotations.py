import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings

settings = Settings()

# Tool 1: Add notes
add_paper_note_tool = types.Tool(
    name="add_paper_note",
    description="Add notes and tags to ArXiv papers stored locally.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID",
            },
            "note": {
                "type": "string",
                "description": "Note content to add",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags to associate with this note",
                "default": [],
            },
            "section_ref": {
                "type": "string",
                "description": "Optional reference to specific section",
            },
        },
        "required": ["paper_id", "note"],
    },
)

# Tool 2: List notes
list_paper_notes_tool = types.Tool(
    name="list_paper_notes",
    description="List all notes for a paper or search notes by tags.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID (optional - omit to search all papers)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter notes by these tags",
            },
            "search_text": {
                "type": "string",
                "description": "Search for this text in notes",
            },
        },
    },
)

class AnnotationStore:
    """Manages paper annotations in JSON format."""
    
    def __init__(self):
        self.annotations_dir = settings.STORAGE_PATH / "annotations"
        self.annotations_dir.mkdir(exist_ok=True)
    
    def _get_annotation_file(self, paper_id: str) -> Path:
        return self.annotations_dir / f"{paper_id}_annotations.json"
    
    def load_annotations(self, paper_id: str) -> Dict[str, Any]:
        """Load annotations for a paper."""
        file_path = self._get_annotation_file(paper_id)
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return {
            "paper_id": paper_id,
            "notes": [],
            "tags": set(),
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
        }
    
    def save_annotations(self, paper_id: str, annotations: Dict[str, Any]):
        """Save annotations for a paper."""
        # Convert sets to lists for JSON serialization
        if isinstance(annotations.get("tags"), set):
            annotations["tags"] = list(annotations["tags"])
        
        annotations["modified"] = datetime.now().isoformat()
        
        file_path = self._get_annotation_file(paper_id)
        with open(file_path, "w") as f:
            json.dump(annotations, f, indent=2)
    
    def add_note(self, paper_id: str, note: str, tags: List[str], section_ref: Optional[str] = None) -> Dict[str, Any]:
        """Add a note to a paper."""
        annotations = self.load_annotations(paper_id)
        
        note_entry = {
            "id": len(annotations["notes"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "note": note,
            "tags": tags,
            "section_ref": section_ref,
        }
        
        annotations["notes"].append(note_entry)
        
        # Update global tags
        if isinstance(annotations.get("tags"), list):
            annotations["tags"] = set(annotations["tags"])
        else:
            annotations["tags"] = set()
        
        annotations["tags"].update(tags)
        
        self.save_annotations(paper_id, annotations)
        return note_entry
    
    def search_notes(self, paper_id: Optional[str] = None, tags: Optional[List[str]] = None, 
                    search_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search notes across papers."""
        results = []
        
        # Determine which files to search
        if paper_id:
            files = [self._get_annotation_file(paper_id)]
        else:
            files = list(self.annotations_dir.glob("*_annotations.json"))
        
        for file_path in files:
            if not file_path.exists():
                continue
            
            with open(file_path, "r") as f:
                annotations = json.load(f)
            
            paper_id = annotations["paper_id"]
            
            for note in annotations.get("notes", []):
                # Check tag filter
                if tags and not any(tag in note.get("tags", []) for tag in tags):
                    continue
                
                # Check text search
                if search_text and search_text.lower() not in note["note"].lower():
                    continue
                
                # Add paper context
                note_with_context = note.copy()
                note_with_context["paper_id"] = paper_id
                results.append(note_with_context)
        
        return results

async def handle_add_paper_note(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle adding notes to papers."""
    paper_id = arguments["paper_id"]
    note = arguments["note"]
    tags = arguments.get("tags", [])
    section_ref = arguments.get("section_ref")
    
    # Check if paper exists
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    if not md_path.exists():
        return [types.TextContent(
            type="text",
            text=f"Error: Paper {paper_id} not found. Please download it first."
        )]
    
    # Add note
    store = AnnotationStore()
    note_entry = store.add_note(paper_id, note, tags, section_ref)
    
    output = f"Note added to {paper_id}:\n"
    output += f"ID: {note_entry['id']}\n"
    output += f"Timestamp: {note_entry['timestamp']}\n"
    output += f"Note: {note_entry['note']}\n"
    if tags:
        output += f"Tags: {', '.join(tags)}\n"
    if section_ref:
        output += f"Section: {section_ref}\n"
    
    return [types.TextContent(type="text", text=output)]

async def handle_list_paper_notes(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle listing/searching notes."""
    paper_id = arguments.get("paper_id")
    tags = arguments.get("tags", [])
    search_text = arguments.get("search_text")
    
    store = AnnotationStore()
    notes = store.search_notes(paper_id, tags, search_text)
    
    if not notes:
        output = "No notes found matching criteria."
    else:
        output = f"Found {len(notes)} notes:\n\n"
        
        for note in notes:
            output += f"Paper: {note['paper_id']}\n"
            output += f"Note ID: {note['id']}\n"
            output += f"Time: {note['timestamp']}\n"
            output += f"Note: {note['note']}\n"
            if note.get('tags'):
                output += f"Tags: {', '.join(note['tags'])}\n"
            if note.get('section_ref'):
                output += f"Section: {note['section_ref']}\n"
            output += "-" * 40 + "\n"
    
    return [types.TextContent(type="text", text=output)]