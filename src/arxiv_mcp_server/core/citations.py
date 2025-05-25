"""
ArXiv Citations Core Functionality
==================================

Pure business logic for extracting and formatting citations from papers.

Dependencies:
- re: Regular expressions for parsing
- json: JSON formatting

Sample Input:
    text = "References\\n[1] Smith et al. (2023). Deep Learning. arXiv:2301.12345"
    format = "bibtex"

Expected Output:
    BibTeX, JSON, or EndNote formatted citations
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Citation:
    """Represents a single citation."""
    index: int
    raw_text: str
    authors: List[str]
    title: str
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CitationExtractor:
    """Extract and format citations from academic papers."""
    
    # Common reference section headers
    REFERENCE_HEADERS = [
        "references", "bibliography", "works cited", "literature cited",
        "citations", "sources", "riferimenti", "bibliographie"
    ]
    
    # Citation patterns
    PATTERNS = {
        'numbered_bracket': r'\[(\d+)\]\s*(.*?)(?=\[\d+\]|\Z)',  # [1] Author...
        'numbered_dot': r'(\d+)\.\s*(.*?)(?=\d+\.|\Z)',          # 1. Author...
        'bulleted': r'[•·▪]\s*(.*?)(?=[•·▪]|\Z)',               # • Author...
        'alpha': r'\[([A-Za-z]+\d{2,4}[a-z]?)\]\s*(.*?)(?=\[[A-Za-z]+\d{2,4}[a-z]?\]|\Z)',  # [Smith23a]
    }
    
    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract citations from paper text.
        
        Args:
            text: Full paper text
            
        Returns:
            List of Citation objects
        """
        # Find references section
        ref_section = self._find_references_section(text)
        if not ref_section:
            return []
        
        # Try different citation patterns
        citations = []
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, ref_section, re.DOTALL | re.MULTILINE)
            if matches:
                citations = self._parse_matches(matches, pattern_name)
                if citations:  # Found valid citations
                    break
        
        return citations
    
    def _find_references_section(self, text: str) -> Optional[str]:
        """Find the references/bibliography section in the text."""
        # Try to find section header
        for header in self.REFERENCE_HEADERS:
            # Look for header at start of line
            pattern = rf'(?:^|\n)(?:#+\s*)?{header}(?:\s*\n|:)(.*?)(?:\n{{2,}}[A-Z]|\Z)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        # Fallback: Look for concentration of years and author patterns
        # This helps when references aren't clearly marked
        lines = text.split('\n')
        ref_score = []
        
        for i, line in enumerate(lines):
            score = 0
            # Check for year patterns
            if re.search(r'\(\d{4}\)', line):
                score += 2
            if re.search(r'\d{4}[a-z]?\)', line):
                score += 2
            # Check for author patterns
            if re.search(r'[A-Z][a-z]+,\s*[A-Z]\.', line):
                score += 1
            # Check for journal/conference names
            if re.search(r'(?:Proceedings|Journal|Conference|Trans\.)', line):
                score += 1
            # Check for DOI/arXiv
            if re.search(r'(?:doi:|arXiv:)', line, re.IGNORECASE):
                score += 2
                
            ref_score.append((i, score))
        
        # Find region with highest concentration of reference-like lines
        if ref_score:
            # Use sliding window to find dense region
            window_size = 20
            max_score = 0
            best_start = 0
            
            for i in range(len(ref_score) - window_size):
                window_score = sum(score for _, score in ref_score[i:i+window_size])
                if window_score > max_score:
                    max_score = window_score
                    best_start = i
            
            if max_score > 10:  # Threshold for reference section
                start_line = ref_score[best_start][0]
                return '\n'.join(lines[start_line:])
        
        return None
    
    def _parse_matches(self, matches: List[Tuple], pattern_type: str) -> List[Citation]:
        """Parse regex matches into Citation objects."""
        citations = []
        
        for i, match in enumerate(matches):
            if pattern_type in ['numbered_bracket', 'numbered_dot']:
                index = int(match[0]) if pattern_type == 'numbered_bracket' else int(match[0])
                text = match[1].strip()
            elif pattern_type == 'alpha':
                index = i + 1
                text = match[1].strip()
            else:  # bulleted
                index = i + 1
                text = match[0].strip() if isinstance(match, str) else match.strip()
            
            citation = self._parse_single_citation(text, index)
            if citation:
                citations.append(citation)
        
        return citations
    
    def _parse_single_citation(self, text: str, index: int) -> Optional[Citation]:
        """Parse a single citation string into structured format."""
        # Clean up text
        text = ' '.join(text.split())
        if not text or len(text) < 10:
            return None
        
        citation = Citation(
            index=index,
            raw_text=text,
            authors=[],
            title=""
        )
        
        # Extract ArXiv ID
        arxiv_patterns = [
            r'arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'(\d{4}\.\d{4,5}(?:v\d+)?)\s*\[',
        ]
        for pattern in arxiv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                citation.arxiv_id = match.group(1)
                break
        
        # Extract DOI
        doi_patterns = [
            r'(?:doi:|DOI:|https?://doi\.org/)(10\.\d{4,}/[-._;()/:\w]+)',
            r'(10\.\d{4,}/[-._;()/:\w]+)',
        ]
        for pattern in doi_patterns:
            match = re.search(pattern, text)
            if match:
                citation.doi = match.group(1)
                break
        
        # Extract year
        year_patterns = [
            r'\((\d{4})\)',      # (2023)
            r'\b(\d{4})[a-z]?\)', # 2023a)
            r',\s*(\d{4})\b',    # , 2023
        ]
        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    citation.year = int(match.group(1))
                    break
                except ValueError:
                    pass
        
        # Extract title (usually in quotes or after authors/year)
        title_patterns = [
            r'"([^"]+)"',           # "Title in quotes"
            r'"([^"]+)"',           # "Title in fancy quotes"
            r'[.]\s+([^.]+?)\.\s+(?:In\s+)?(?:[A-Z]|arXiv|doi)',  # . Title. Journal
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                citation.title = match.group(1).strip()
                break
        
        # Extract authors (before year or title)
        if citation.year:
            # Find text before year
            year_match = re.search(r'\(\d{4}\)', text)
            if year_match:
                authors_text = text[:year_match.start()].strip()
                citation.authors = self._parse_authors(authors_text)
        elif citation.title and citation.title in text:
            # Find text before title
            title_idx = text.find(citation.title)
            if title_idx > 0:
                authors_text = text[:title_idx].strip().rstrip('.')
                citation.authors = self._parse_authors(authors_text)
        
        # Extract journal/conference
        journal_patterns = [
            r'(?:In\s+)?(?:Proceedings of |Proc\.\s+)?([A-Z][^.]+?)\s*(?:,|\.|$)',
            r'(?:In\s+)?([A-Z][A-Za-z\s&]+?)\s+\d+',
        ]
        # Search after title if found
        search_text = text
        if citation.title and citation.title in text:
            title_end = text.find(citation.title) + len(citation.title)
            search_text = text[title_end:]
            
        for pattern in journal_patterns:
            match = re.search(pattern, search_text)
            if match:
                journal = match.group(1).strip()
                if len(journal) > 5 and not journal.startswith('http'):
                    citation.journal = journal
                    break
        
        return citation
    
    def _parse_authors(self, text: str) -> List[str]:
        """Parse author names from text."""
        authors = []
        
        # Clean text
        text = text.strip().rstrip(',.')
        
        # Split by "and" or commas
        # Handle "LastName, F., LastName, F., and LastName, F."
        if ',' in text:
            parts = re.split(r',\s*(?:and\s+)?', text)
            
            # Group parts that might be split names
            i = 0
            while i < len(parts):
                part = parts[i].strip()
                
                # Check if this looks like a last name (next part might be initials)
                if i + 1 < len(parts) and re.match(r'^[A-Z][a-z]+$', part):
                    next_part = parts[i + 1].strip()
                    if re.match(r'^[A-Z]\.?(?:\s*[A-Z]\.?)*$', next_part):
                        # Combine as "LastName, F."
                        authors.append(f"{part}, {next_part}")
                        i += 2
                        continue
                
                if part and not part.isdigit():
                    authors.append(part)
                i += 1
        else:
            # Split by "and"
            parts = re.split(r'\s+and\s+', text)
            authors = [p.strip() for p in parts if p.strip()]
        
        # Clean up authors
        cleaned = []
        for author in authors:
            author = author.strip()
            if author and len(author) > 2 and not author.startswith('http'):
                cleaned.append(author)
        
        return cleaned[:10]  # Limit to 10 authors


def format_citations_as_bibtex(citations: List[Citation], include_links: bool = True) -> str:
    """
    Format citations as BibTeX.
    
    Args:
        citations: List of Citation objects
        include_links: Whether to include URLs for ArXiv papers
        
    Returns:
        BibTeX formatted string
    """
    entries = []
    
    for cite in citations:
        # Generate citation key
        if cite.authors:
            first_author = cite.authors[0].split(',')[0].split()[-1]
        else:
            first_author = "Unknown"
        
        year = cite.year or "XXXX"
        key = f"{first_author}{year}"
        
        # Make key unique if needed
        if any(key in e for e in entries):
            key = f"{key}_{cite.index}"
        
        # Build entry
        lines = [f"@article{{{key},"]
        
        if cite.authors:
            authors_str = " and ".join(cite.authors)
            lines.append(f'  author = "{{{authors_str}}}",')
        
        if cite.title:
            lines.append(f'  title = "{{{cite.title}}}",')
        
        if cite.year:
            lines.append(f'  year = {{{cite.year}}},')
        
        if cite.journal:
            lines.append(f'  journal = "{{{cite.journal}}}",')
        
        if cite.volume:
            lines.append(f'  volume = "{{{cite.volume}}}",')
        
        if cite.pages:
            lines.append(f'  pages = "{{{cite.pages}}}",')
        
        if cite.arxiv_id:
            lines.append(f'  eprint = "{{{cite.arxiv_id}}}",')
            lines.append(f'  archivePrefix = "arXiv",')
            if include_links:
                lines.append(f'  url = "https://arxiv.org/abs/{cite.arxiv_id}",')
        
        if cite.doi:
            lines.append(f'  doi = "{{{cite.doi}}}",')
        
        lines.append("}")
        entries.append("\n".join(lines))
    
    return "\n\n".join(entries)


def format_citations_as_endnote(citations: List[Citation]) -> str:
    """
    Format citations as EndNote.
    
    Args:
        citations: List of Citation objects
        
    Returns:
        EndNote formatted string
    """
    entries = []
    
    for cite in citations:
        lines = ["%0 Journal Article"]
        
        for author in cite.authors:
            lines.append(f"%A {author}")
        
        if cite.title:
            lines.append(f"%T {cite.title}")
        
        if cite.journal:
            lines.append(f"%J {cite.journal}")
        
        if cite.year:
            lines.append(f"%D {cite.year}")
        
        if cite.volume:
            lines.append(f"%V {cite.volume}")
        
        if cite.pages:
            lines.append(f"%P {cite.pages}")
        
        if cite.arxiv_id:
            lines.append(f"%U https://arxiv.org/abs/{cite.arxiv_id}")
        
        if cite.doi:
            lines.append(f"%R {cite.doi}")
        
        entries.append("\n".join(lines))
    
    return "\n\n".join(entries)


def extract_and_format_citations(
    text: str,
    output_format: str = "bibtex",
    include_links: bool = True
) -> Tuple[bool, str]:
    """
    Extract and format citations from paper text.
    
    Args:
        text: Full paper text
        output_format: "bibtex", "endnote", or "json"
        include_links: Whether to include URLs in BibTeX
        
    Returns:
        Tuple of (success, formatted_output)
    """
    extractor = CitationExtractor()
    citations = extractor.extract_citations(text)
    
    if not citations:
        return False, "No citations found. The paper may not have a standard References section."
    
    if output_format == "bibtex":
        output = format_citations_as_bibtex(citations, include_links)
    elif output_format == "endnote":
        output = format_citations_as_endnote(citations)
    else:  # json
        output = json.dumps([c.to_dict() for c in citations], indent=2)
    
    return True, output


# Validation
if __name__ == "__main__":
    import sys
    
    all_validation_failures = []
    total_tests = 0
    
    print("=" * 80)
    print("VALIDATING CITATION EXTRACTION FUNCTIONALITY")
    print("=" * 80)
    
    # Test 1: Basic citation extraction
    total_tests += 1
    print("\nTest 1: Basic citation extraction")
    print("-" * 40)
    
    test_text = """
    Some paper content here...
    
    References
    
    [1] Smith, J., Johnson, K. (2023). Deep Learning for NLP. arXiv:2301.12345.
    
    [2] Brown, A., Davis, C., and Wilson, E. (2022). "Machine Learning Applications". 
        In Proceedings of ICML 2022, pages 123-456. doi:10.1234/icml.2022.001
    
    [3] Garcia, M. (2024). Transformers Revisited. Journal of AI Research, 45(3), 789-812.
    """
    
    try:
        extractor = CitationExtractor()
        citations = extractor.extract_citations(test_text)
        
        if len(citations) >= 2:
            print(f"✓ Extracted {len(citations)} citations")
            for cite in citations:
                print(f"  [{cite.index}] {cite.authors[0] if cite.authors else 'Unknown'} ({cite.year})")
        else:
            all_validation_failures.append(f"Test 1: Only found {len(citations)} citations")
            
    except Exception as e:
        all_validation_failures.append(f"Test 1: {str(e)}")
    
    # Test 2: BibTeX formatting
    total_tests += 1
    print("\nTest 2: BibTeX formatting")
    print("-" * 40)
    
    try:
        success, output = extract_and_format_citations(test_text, "bibtex")
        
        if success and "@article{" in output:
            print("✓ BibTeX formatting works")
            print(output[:200] + "..." if len(output) > 200 else output)
        else:
            all_validation_failures.append("Test 2: BibTeX formatting failed")
            
    except Exception as e:
        all_validation_failures.append(f"Test 2: {str(e)}")
    
    # Test 3: JSON formatting
    total_tests += 1
    print("\nTest 3: JSON formatting")
    print("-" * 40)
    
    try:
        success, output = extract_and_format_citations(test_text, "json")
        
        if success:
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                print(f"✓ JSON formatting works - {len(data)} citations")
                print(f"  First citation: {data[0].get('title', 'No title')[:50]}...")
            else:
                all_validation_failures.append("Test 3: JSON format invalid")
        else:
            all_validation_failures.append("Test 3: JSON formatting failed")
            
    except Exception as e:
        all_validation_failures.append(f"Test 3: {str(e)}")
    
    # Test 4: Different citation styles
    total_tests += 1
    print("\nTest 4: Different citation styles")
    print("-" * 40)
    
    test_text2 = """
    References
    
    1. Anderson, P. (2023). Neural Networks. Nature, 123, 45-67.
    2. Baker, R., Clark, S. (2022). Deep Learning. arXiv:2201.98765.
    """
    
    try:
        extractor = CitationExtractor()
        citations = extractor.extract_citations(test_text2)
        
        if len(citations) >= 2:
            print(f"✓ Numbered citation style works - found {len(citations)} citations")
        else:
            all_validation_failures.append("Test 4: Failed to parse numbered citations")
            
    except Exception as e:
        all_validation_failures.append(f"Test 4: {str(e)}")
    
    # Test 5: No citations handling
    total_tests += 1
    print("\nTest 5: No citations handling")
    print("-" * 40)
    
    try:
        success, output = extract_and_format_citations("This paper has no references section.")
        
        if not success and "No citations found" in output:
            print("✓ Handles missing citations correctly")
        else:
            all_validation_failures.append("Test 5: Should report no citations found")
            
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
        print("Citation extraction functionality is working correctly")
        sys.exit(0)