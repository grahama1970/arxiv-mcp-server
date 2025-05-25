"""
ArXiv Search Core Functionality
==============================

Pure business logic for searching ArXiv papers.

Dependencies:
- arxiv: https://github.com/lukasschwab/arxiv.py
- python-dateutil: Date parsing

Sample Input:
    query = "quantum computing"
    max_results = 5
    date_from = "2023-01-01"
    date_to = "2024-01-01"
    categories = ["cs.AI", "cs.LG"]

Expected Output:
    List of paper dictionaries with id, title, authors, abstract, etc.
"""

import arxiv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser


def search_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "submitted",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    categories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search ArXiv papers with filters.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        sort_by: Sort criterion - "relevance", "submitted", or "lastUpdated"
        date_from: Start date filter (YYYY-MM-DD format)
        date_to: End date filter (YYYY-MM-DD format)
        categories: List of ArXiv categories to filter by
        
    Returns:
        List of paper dictionaries with full metadata
    """
    # Build search client
    client = arxiv.Client()
    
    # Build query with category filtering
    search_query = query
    if categories:
        category_filter = " OR ".join(f"cat:{cat}" for cat in categories)
        search_query = f"({query}) AND ({category_filter})"
    
    # Map sort options
    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted": arxiv.SortCriterion.SubmittedDate,
        "lastUpdated": arxiv.SortCriterion.LastUpdatedDate
    }
    sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.SubmittedDate)
    
    # Create search
    search = arxiv.Search(
        query=search_query,
        max_results=max_results * 2,  # Get extra to account for date filtering
        sort_by=sort_criterion,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Parse date filters
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = date_parser.parse(date_from).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date_from format: {date_from}")
    
    if date_to:
        try:
            date_to_parsed = date_parser.parse(date_to).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date_to format: {date_to}")
    
    # Execute search and format results
    papers = []
    for result in client.results(search):
        # Apply date filtering
        if date_from_parsed and result.published < date_from_parsed:
            continue
        if date_to_parsed and result.published > date_to_parsed:
            continue
            
        papers.append({
            "id": result.get_short_id(),
            "entry_id": result.entry_id,
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary,
            "abstract": result.summary,  # Alias for compatibility
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "categories": result.categories,
            "primary_category": result.primary_category,
            "pdf_url": result.pdf_url,
            "url": result.pdf_url,  # Alias for compatibility
            "entry_url": result.entry_id,
            "comment": result.comment,
            "journal_ref": result.journal_ref,
            "doi": result.doi,
            "resource_uri": f"arxiv://{result.get_short_id()}"
        })
        
        if len(papers) >= max_results:
            break
    
    return papers


def format_search_results(papers: List[Dict[str, Any]]) -> str:
    """
    Format search results as human-readable text.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        Formatted string with paper information
    """
    if not papers:
        return "No papers found matching your search criteria."
    
    result_text = f"Found {len(papers)} papers:\n\n"
    
    for i, paper in enumerate(papers, 1):
        result_text += f"{i}. {paper['title']}\n"
        
        # Format authors
        authors = paper['authors']
        if len(authors) <= 3:
            result_text += f"   Authors: {', '.join(authors)}\n"
        else:
            result_text += f"   Authors: {', '.join(authors[:3])} and {len(authors) - 3} others\n"
        
        result_text += f"   Published: {paper['published'][:10]}\n"
        result_text += f"   Categories: {', '.join(paper['categories'])}\n"
        result_text += f"   arXiv ID: {paper['id']}\n"
        result_text += f"   PDF: {paper['pdf_url']}\n"
        
        # Add truncated abstract
        abstract = paper['summary']
        if len(abstract) > 200:
            abstract = abstract[:197] + "..."
        result_text += f"   Abstract: {abstract}\n\n"
    
    return result_text


# Validation
if __name__ == "__main__":
    import sys
    import json
    
    all_validation_failures = []
    total_tests = 0
    
    print("=" * 80)
    print("VALIDATING ARXIV SEARCH CORE FUNCTIONALITY")
    print("=" * 80)
    
    # Test 1: Basic search
    total_tests += 1
    print("\nTest 1: Basic search")
    print("-" * 40)
    
    try:
        results = search_papers("quantum computing", max_results=3)
        if len(results) > 0:
            print(f"✓ Found {len(results)} papers")
            print(f"  First paper: {results[0]['title'][:60]}...")
            print(f"  Authors: {', '.join(results[0]['authors'][:3])}")
            print(f"  Categories: {', '.join(results[0]['categories'])}")
        else:
            all_validation_failures.append("Test 1: No results returned")
    except Exception as e:
        all_validation_failures.append(f"Test 1: {str(e)}")
    
    # Test 2: Date filtered search
    total_tests += 1
    print("\nTest 2: Date filtered search")
    print("-" * 40)
    
    try:
        results = search_papers(
            "machine learning",
            max_results=5,
            date_from="2024-01-01",
            date_to="2024-12-31"
        )
        print(f"✓ Found {len(results)} papers from 2024")
        if results:
            # Verify dates are in range
            for paper in results:
                pub_date = paper['published'][:10]
                if pub_date < "2024-01-01" or pub_date > "2024-12-31":
                    all_validation_failures.append(f"Test 2: Paper {paper['id']} outside date range: {pub_date}")
    except Exception as e:
        all_validation_failures.append(f"Test 2: {str(e)}")
    
    # Test 3: Category filtered search
    total_tests += 1
    print("\nTest 3: Category filtered search")
    print("-" * 40)
    
    try:
        results = search_papers(
            "neural networks",
            max_results=3,
            categories=["cs.LG", "cs.AI"]
        )
        print(f"✓ Found {len(results)} papers in cs.LG or cs.AI")
        if results:
            # Verify categories
            for paper in results:
                has_category = any(cat in ["cs.LG", "cs.AI"] for cat in paper['categories'])
                if not has_category:
                    all_validation_failures.append(f"Test 3: Paper {paper['id']} missing required categories")
    except Exception as e:
        all_validation_failures.append(f"Test 3: {str(e)}")
    
    # Test 4: Formatting function
    total_tests += 1
    print("\nTest 4: Result formatting")
    print("-" * 40)
    
    try:
        results = search_papers("deep learning", max_results=2)
        formatted = format_search_results(results)
        if "Found" in formatted and "Authors:" in formatted:
            print("✓ Formatting function works")
            print(formatted[:300] + "..." if len(formatted) > 300 else formatted)
        else:
            all_validation_failures.append("Test 4: Formatting function failed")
    except Exception as e:
        all_validation_failures.append(f"Test 4: {str(e)}")
    
    # Test 5: Empty results
    total_tests += 1
    print("\nTest 5: Empty results handling")
    print("-" * 40)
    
    try:
        results = search_papers("asdfghjklzxcvbnmqwertyuiop", max_results=5)
        formatted = format_search_results(results)
        if "No papers found" in formatted:
            print("✓ Empty results handled correctly")
        else:
            all_validation_failures.append("Test 5: Empty results not handled properly")
    except Exception as e:
        all_validation_failures.append(f"Test 5: {str(e)}")
    
    # Final result
    print("\n" + "=" * 80)
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Search core functionality is working correctly")
        sys.exit(0)