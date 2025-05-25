"""Enhanced paper summarization with LLM integration support."""

from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from abc import abstractmethod
import os


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers to implement."""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text from prompt."""
        pass


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Simulate LLM response."""
        lines = prompt.split('\n')
        if "Previous summary" in prompt:
            return f"[Refined summary incorporating new information, max {max_tokens} tokens]"
        else:
            return f"[Initial summary of chunk, max {max_tokens} tokens]"


class OpenAIProvider:
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                pass
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using OpenAI API."""
        if not self.client:
            return "[OpenAI API not configured]"
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for factual summaries
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI error: {str(e)}]"


class AnthropicProvider:
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                pass
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Anthropic API."""
        if not self.client:
            return "[Anthropic API not configured]"
        
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic error: {str(e)}]"


def get_llm_provider(provider_name: str = "mock") -> LLMProvider:
    """Get LLM provider by name."""
    providers = {
        "mock": MockLLMProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,  # Alias
        "gpt4": OpenAIProvider,  # Alias
    }
    
    provider_class = providers.get(provider_name.lower(), MockLLMProvider)
    return provider_class()


async def summarize_with_rolling_window(
    chunks: List[Dict[str, Any]],
    llm_provider: LLMProvider,
    summary_type: str = "detailed",
    max_summary_tokens: int = 1000
) -> Dict[str, Any]:
    """
    Implement rolling window summarization with actual LLM calls.
    
    Args:
        chunks: List of text chunks with metadata
        llm_provider: LLM provider instance
        summary_type: Type of summary to generate
        max_summary_tokens: Maximum tokens for each summary
        
    Returns:
        Dictionary with summary results and metadata
    """
    summaries = []
    previous_summary = None
    prompts_used = []
    
    for i, chunk in enumerate(chunks):
        # Create prompt
        prompt = create_summary_prompt(
            chunk["text"],
            summary_type,
            previous_summary,
            chunk["is_first"],
            chunk["is_last"]
        )
        prompts_used.append(prompt)
        
        # Generate summary
        chunk_summary = await llm_provider.generate(prompt, max_summary_tokens)
        summaries.append({
            "chunk_num": i,
            "summary": chunk_summary,
            "tokens_in": chunk["estimated_tokens"],
            "prompt_type": "initial" if previous_summary is None else "refinement"
        })
        
        # Update rolling summary
        if previous_summary:
            # Combine previous and new summary
            previous_summary = chunk_summary  # LLM already integrated them
        else:
            previous_summary = chunk_summary
        
        # If rolling summary is too long, condense it
        if estimate_tokens(previous_summary) > max_summary_tokens * 1.5:
            condensation_prompt = f"""Condense this summary to its key points while maintaining all critical information:

{previous_summary}

Condensed summary (max {max_summary_tokens} tokens):"""
            
            previous_summary = await llm_provider.generate(condensation_prompt, max_summary_tokens)
            summaries[-1]["condensed"] = True
    
    return {
        "final_summary": previous_summary,
        "chunk_summaries": summaries,
        "total_chunks": len(chunks),
        "prompts_used": len(prompts_used),
        "strategy": "rolling_window"
    }


async def summarize_with_map_reduce(
    chunks: List[Dict[str, Any]],
    llm_provider: LLMProvider,
    summary_type: str = "detailed",
    max_summary_tokens: int = 1000,
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """
    Implement map-reduce summarization with parallel processing.
    
    Args:
        chunks: List of text chunks with metadata
        llm_provider: LLM provider instance
        summary_type: Type of summary to generate
        max_summary_tokens: Maximum tokens for each summary
        max_concurrent: Maximum concurrent LLM calls
        
    Returns:
        Dictionary with summary results and metadata
    """
    import asyncio
    
    # Map phase - summarize chunks in parallel
    async def summarize_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
        prompt = create_summary_prompt(
            chunk["text"],
            summary_type,
            None,  # No previous summary in map-reduce
            chunk["is_first"],
            chunk["is_last"]
        )
        
        summary = await llm_provider.generate(prompt, max_summary_tokens // 2)
        
        return {
            "chunk_num": chunk["chunk_num"],
            "summary": summary,
            "tokens_in": chunk["estimated_tokens"]
        }
    
    # Process chunks with concurrency limit
    chunk_summaries = []
    for i in range(0, len(chunks), max_concurrent):
        batch = chunks[i:i + max_concurrent]
        batch_summaries = await asyncio.gather(
            *[summarize_chunk(chunk) for chunk in batch]
        )
        chunk_summaries.extend(batch_summaries)
    
    # Reduce phase - combine summaries
    all_summaries = "\n\n".join([s["summary"] for s in chunk_summaries])
    
    reduce_prompt = f"""Combine these summaries of different sections into a single coherent summary:

{all_summaries}

Create a unified {summary_type} summary (max {max_summary_tokens} tokens):"""
    
    final_summary = await llm_provider.generate(reduce_prompt, max_summary_tokens)
    
    return {
        "final_summary": final_summary,
        "chunk_summaries": chunk_summaries,
        "total_chunks": len(chunks),
        "strategy": "map_reduce",
        "parallel_batches": (len(chunks) + max_concurrent - 1) // max_concurrent
    }


async def summarize_with_hierarchical(
    chunks: List[Dict[str, Any]],
    llm_provider: LLMProvider,
    summary_type: str = "detailed",
    max_summary_tokens: int = 1000
) -> Dict[str, Any]:
    """
    Implement hierarchical summarization (tree-based).
    
    Args:
        chunks: List of text chunks with metadata
        llm_provider: LLM provider instance
        summary_type: Type of summary to generate
        max_summary_tokens: Maximum tokens for each summary
        
    Returns:
        Dictionary with summary results and metadata
    """
    import math
    
    # Build tree bottom-up
    current_level = []
    
    # Level 0: Summarize individual chunks
    for chunk in chunks:
        prompt = create_summary_prompt(
            chunk["text"],
            summary_type,
            None,
            chunk["is_first"],
            chunk["is_last"]
        )
        
        summary = await llm_provider.generate(prompt, max_summary_tokens // 4)
        current_level.append(summary)
    
    tree_levels = [current_level.copy()]
    
    # Build higher levels
    while len(current_level) > 1:
        next_level = []
        
        # Pair up summaries
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                # Combine two summaries
                combine_prompt = f"""Combine these two summaries into one:

Summary 1:
{current_level[i]}

Summary 2:
{current_level[i + 1]}

Combined {summary_type} summary:"""
                
                combined = await llm_provider.generate(combine_prompt, max_summary_tokens // 2)
                next_level.append(combined)
            else:
                # Odd summary, carry forward
                next_level.append(current_level[i])
        
        tree_levels.append(next_level.copy())
        current_level = next_level
    
    # Final summary is at the root
    final_summary = current_level[0] if current_level else ""
    
    return {
        "final_summary": final_summary,
        "tree_levels": len(tree_levels),
        "total_chunks": len(chunks),
        "strategy": "hierarchical",
        "tree_structure": [len(level) for level in tree_levels]
    }


# Import utility functions from main module
from .summarize_paper import (
    estimate_tokens,
    chunk_text_with_overlap,
    extract_sections,
    create_summary_prompt
)