import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import mcp.types as types
from ..config import Settings

settings = Settings()

compare_paper_ideas_tool = types.Tool(
    name="compare_paper_ideas",
    description="Compare paper ideas against your research question or system. Uses AI to find better/worse ideas, contradictions, and unique insights.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ArXiv paper ID to analyze",
            },
            "research_context": {
                "type": "string",
                "description": "Your research question/system to compare against (e.g., 'my Natrium system pairs a 345-MW sodium-cooled fast reactor with thermal storage')",
            },
            "comparison_type": {
                "type": "string",
                "description": "Type of comparison to perform",
                "enum": ["comprehensive", "technical", "approach", "results"],
                "default": "comprehensive",
            },
            "llm_provider": {
                "type": "string",
                "description": "LLM provider to use for analysis",
                "enum": ["openai", "anthropic", "perplexity", "mock"],
                "default": "mock",
            },
            "focus_areas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific areas to focus on (e.g., ['efficiency', 'cost', 'safety'])",
            },
        },
        "required": ["paper_id", "research_context"],
    },
)

class MockLLMProvider:
    """Mock provider for testing without API keys."""
    
    async def analyze(self, paper_content: str, research_context: str, comparison_type: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Provide mock analysis for testing."""
        return {
            "better_ideas": [
                "The paper proposes a modular design approach that could improve scalability",
                "Their heat recovery system achieves 15% higher efficiency through cascaded heat exchangers"
            ],
            "worse_ideas": [
                "The paper's cooling system requires 3x more maintenance due to complex piping",
                "Their control strategy has longer response times (45s vs your 10s)"
            ],
            "contradictions": [
                "Paper claims sodium systems can't exceed 40% efficiency, but your Natrium achieves 42%",
                "They state thermal storage is impractical above 500°C, contradicting your 600°C design"
            ],
            "unique_insights": [
                "Novel use of phase-change materials could reduce storage tank size by 30%",
                "Their economic analysis framework accounts for grid stability value"
            ],
            "recommendations": [
                "Consider integrating their heat exchanger design with your thermal storage",
                "Their safety protocols for sodium handling could enhance your system"
            ],
            "confidence_score": 0.85
        }

class LLMAnalyzer:
    """Handles LLM-based paper comparison."""
    
    def __init__(self, provider: str):
        self.provider = provider
        
    async def analyze(self, paper_content: str, research_context: str, comparison_type: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Analyze paper against research context."""
        
        if self.provider == "mock":
            mock = MockLLMProvider()
            return await mock.analyze(paper_content, research_context, comparison_type, focus_areas)
        
        # For real providers, construct prompt
        prompt = self._build_prompt(paper_content, research_context, comparison_type, focus_areas)
        
        # Here you would call the actual LLM API
        # For now, return mock data with a note
        return {
            "error": f"Real {self.provider} integration requires API key. Set {self.provider.upper()}_API_KEY environment variable.",
            "suggestion": "Use 'mock' provider for testing without API keys."
        }
    
    def _build_prompt(self, paper_content: str, research_context: str, comparison_type: str, focus_areas: List[str]) -> str:
        """Build comparison prompt for LLM."""
        focus_str = ", ".join(focus_areas) if focus_areas else "all aspects"
        
        prompt = f"""Compare the following research paper against this context:

RESEARCH CONTEXT: {research_context}

PAPER CONTENT:
{paper_content[:3000]}...  # Truncated for context window

COMPARISON TYPE: {comparison_type}
FOCUS AREAS: {focus_str}

Analyze and provide:
1. Better ideas in the paper compared to the research context
2. Worse ideas or limitations compared to the research context  
3. Contradictions with the research context
4. Unique insights that could enhance the research
5. Specific recommendations

Format as JSON with keys: better_ideas, worse_ideas, contradictions, unique_insights, recommendations"""
        
        return prompt

async def handle_compare_paper_ideas(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle comparative analysis requests."""
    paper_id = arguments["paper_id"]
    research_context = arguments["research_context"]
    comparison_type = arguments.get("comparison_type", "comprehensive")
    llm_provider = arguments.get("llm_provider", "mock")
    focus_areas = arguments.get("focus_areas", [])
    
    # Load paper content
    storage_path = settings.STORAGE_PATH
    md_path = storage_path / f"{paper_id}.md"
    
    if not md_path.exists():
        return [types.TextContent(
            type="text",
            text=f"Error: Paper {paper_id} not found. Please download it first."
        )]
    
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            paper_content = f.read()
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading paper: {str(e)}")]
    
    # Perform analysis
    analyzer = LLMAnalyzer(llm_provider)
    try:
        analysis = await analyzer.analyze(paper_content, research_context, comparison_type, focus_areas)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Analysis error: {str(e)}")]
    
    # Format output
    if "error" in analysis:
        output = f"Error: {analysis['error']}\n"
        if "suggestion" in analysis:
            output += f"Suggestion: {analysis['suggestion']}\n"
    else:
        output = f"Comparative Analysis: {paper_id}\n"
        output += f"Research Context: {research_context}\n"
        output += f"Comparison Type: {comparison_type}\n\n"
        
        output += "BETTER IDEAS IN PAPER:\n"
        for idea in analysis.get("better_ideas", []):
            output += f"• {idea}\n"
        
        output += "\nWORSE IDEAS/LIMITATIONS:\n"
        for idea in analysis.get("worse_ideas", []):
            output += f"• {idea}\n"
        
        output += "\nCONTRADICTIONS:\n"
        for item in analysis.get("contradictions", []):
            output += f"• {item}\n"
        
        output += "\nUNIQUE INSIGHTS:\n"
        for insight in analysis.get("unique_insights", []):
            output += f"• {insight}\n"
        
        output += "\nRECOMMENDATIONS:\n"
        for rec in analysis.get("recommendations", []):
            output += f"• {rec}\n"
        
        if "confidence_score" in analysis:
            output += f"\nConfidence Score: {analysis['confidence_score']:.2f}"
    
    return [types.TextContent(type="text", text=output)]