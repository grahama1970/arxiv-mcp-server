"""Code analysis prompt for analyzing code in ArXiv papers."""

CODE_ANALYSIS_PROMPT = """# Analyzing Code in ArXiv Papers

You now have access to the `analyze_paper_code` tool which can extract and analyze code blocks from ArXiv papers using Tree-Sitter parsing technology.

## Tool Capabilities

The `analyze_paper_code` tool can:
- Extract code blocks from downloaded ArXiv papers (markdown or JSON format)
- Identify programming languages automatically
- Parse code using Tree-Sitter for 100+ languages
- Extract detailed metadata including:
  - Function definitions with parameters and types
  - Class definitions with methods
  - Docstrings and documentation
  - Line numbers and code structure

## Usage Examples

### Basic Code Analysis
```
analyze_paper_code(paper_id="2301.00001")
```

### Language-Specific Analysis
```
analyze_paper_code(
    paper_id="2301.00001",
    languages=["python", "cpp"],  # Only analyze Python and C++ code
    min_lines=5,  # Only analyze code blocks with 5+ lines
    include_docstrings=true
)
```

### Function-Only Analysis
```
analyze_paper_code(
    paper_id="2301.00001",
    extract_functions=true,
    extract_classes=false
)
```

## Best Practices

1. **Download First**: Always download the paper using `download_paper` before analyzing
2. **Use pymupdf4llm**: For code extraction, pymupdf4llm converter is usually sufficient and much faster than marker-pdf
3. **Filter by Language**: If you're looking for specific language implementations, use the `languages` filter
4. **Check Results**: The tool will report how many code blocks were found vs. analyzed

## Supported Languages

Major languages include: Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, Ruby, Swift, Kotlin, Scala, R, Julia, MATLAB, and many more.

## Example Workflow

1. Search for papers with implementations:
   ```
   search_papers(query="neural network implementation code")
   ```

2. Download a paper:
   ```
   download_paper(paper_id="2301.00001", converter="pymupdf4llm")
   ```

3. Analyze the code:
   ```
   analyze_paper_code(paper_id="2301.00001", languages=["python"])
   ```

This will extract all Python code blocks and provide detailed analysis of functions, classes, and their documentation."""