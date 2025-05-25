"""Enhanced converters that add Tree-Sitter code analysis to converted content."""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .converters import MarkdownConverter, JSONConverter
try:
    from .tools.tree_sitter_utils import CodeAnalyzer
except ImportError:
    # Fallback if tree_sitter_utils is not available
    class CodeAnalyzer:
        def analyze(self, code: str, language: str) -> Dict[str, Any]:
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity": 1
            }

class EnhancedMarkdownConverter(MarkdownConverter):
    """Markdown converter with code analysis enrichment."""
    
    def __init__(self):
        super().__init__()
        self.code_analyzer = CodeAnalyzer()
    
    def convert(self, pdf_path: Path, output_path: Optional[Path] = None) -> Path:
        """Convert PDF to markdown with code analysis."""
        # First do standard conversion
        md_path = super().convert(pdf_path, output_path)
        
        # Read the markdown
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Enhance code blocks
        enhanced_content = self._enhance_code_blocks(content)
        
        # Write back
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(enhanced_content)
        
        return md_path
    
    def _enhance_code_blocks(self, content: str) -> str:
        """Add code analysis metadata to code blocks."""
        # Find all code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)```'
        
        def enhance_block(match):
            language = match.group(1) or "text"
            code = match.group(2)
            
            if language in ["python", "javascript", "typescript", "java", "cpp", "c"]:
                # Analyze the code
                analysis = self.code_analyzer.analyze(code, language)
                
                # Create enhanced block with metadata as HTML comment
                metadata = self._format_metadata(analysis)
                enhanced = f"```{language}\n<!-- Code Analysis:\n{metadata}\n-->\n{code}```"
                return enhanced
            
            return match.group(0)  # Return unchanged
        
        return re.sub(code_block_pattern, enhance_block, content, flags=re.DOTALL)
    
    def _format_metadata(self, analysis: Dict[str, Any]) -> str:
        """Format analysis metadata for embedding."""
        lines = []
        
        if analysis.get("functions"):
            lines.append("Functions:")
            for func in analysis["functions"]:
                lines.append(f"  - {func['name']}({', '.join(func['params'])})")
        
        if analysis.get("classes"):
            lines.append("Classes:")
            for cls in analysis["classes"]:
                lines.append(f"  - {cls['name']}")
                if cls.get("methods"):
                    for method in cls["methods"]:
                        lines.append(f"    - {method}")
        
        if analysis.get("imports"):
            lines.append("Imports:")
            for imp in analysis["imports"]:
                lines.append(f"  - {imp}")
        
        if analysis.get("complexity"):
            lines.append(f"Complexity: {analysis['complexity']}")
        
        return "\n".join(lines)

class EnhancedJSONConverter(JSONConverter):
    """JSON converter with code analysis enrichment."""
    
    def __init__(self):
        super().__init__()
        self.code_analyzer = CodeAnalyzer()
    
    def convert(self, pdf_path: Path, output_path: Optional[Path] = None) -> Path:
        """Convert PDF to JSON with code analysis."""
        # First do standard conversion
        json_path = super().convert(pdf_path, output_path)
        
        # Read the JSON
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Enhance with code analysis
        data["code_analysis"] = self._analyze_code_in_document(data)
        
        # Write back
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        return json_path
    
    def _analyze_code_in_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all code in the document."""
        results = {
            "total_code_blocks": 0,
            "languages": {},
            "all_functions": [],
            "all_classes": [],
            "complexity_stats": {
                "min": None,
                "max": None,
                "average": None
            }
        }
        
        # Extract text content
        text = ""
        if isinstance(data.get("content"), str):
            text = data["content"]
        elif isinstance(data.get("sections"), list):
            for section in data["sections"]:
                if isinstance(section.get("content"), str):
                    text += section["content"] + "\n"
        
        # Find code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
        
        complexities = []
        for language, code in code_blocks:
            if not language:
                continue
            
            results["total_code_blocks"] += 1
            results["languages"][language] = results["languages"].get(language, 0) + 1
            
            if language in ["python", "javascript", "typescript", "java", "cpp", "c"]:
                analysis = self.code_analyzer.analyze(code, language)
                
                results["all_functions"].extend(analysis.get("functions", []))
                results["all_classes"].extend(analysis.get("classes", []))
                
                if analysis.get("complexity"):
                    complexities.append(analysis["complexity"])
        
        # Calculate complexity stats
        if complexities:
            results["complexity_stats"]["min"] = min(complexities)
            results["complexity_stats"]["max"] = max(complexities)
            results["complexity_stats"]["average"] = sum(complexities) / len(complexities)
        
        return results

# Update the converter registry
ENHANCED_CONVERTERS = {
    "markdown": EnhancedMarkdownConverter,
    "json": EnhancedJSONConverter,
}