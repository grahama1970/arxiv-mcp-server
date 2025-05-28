# ArXiv Search Tips

## Search Syntax Guide

ArXiv uses specific prefixes for targeted searches. Here's the correct syntax:

### Author Search
```bash
# CORRECT - Use 'au:' prefix
arxiv-cli search "au:Hinton" --max-results 5
arxiv-cli search "au:\"Geoffrey Hinton\"" --max-results 5

# INCORRECT - Don't use 'author:'
# arxiv-cli search "author:Hinton"  # This won't work!
```

### Field-Specific Searches

| Field | Prefix | Example |
|-------|---------|---------|
| Author | `au:` | `au:Bengio` |
| Title | `ti:` | `ti:transformer` |
| Abstract | `abs:` | `abs:"neural network"` |
| Category | `cat:` | `cat:cs.LG` |
| All fields | `all:` | `all:attention` |

### Complex Queries

```bash
# Combine multiple fields
arxiv-cli search "au:Vaswani AND ti:attention"

# Search within categories
arxiv-cli search "ti:transformer AND cat:cs.CL"

# Use quotes for phrases
arxiv-cli search "ti:\"attention is all you need\""
```

### Date Filtering

```bash
# Papers from 2024
arxiv-cli search "transformer" --date-from "2024-01-01"

# Papers in a date range
arxiv-cli search "quantum computing" \
  --date-from "2024-01-01" \
  --date-to "2024-12-31"
```

### Category Codes

Common ArXiv categories:
- `cs.LG` - Machine Learning
- `cs.CL` - Computation and Language
- `cs.CV` - Computer Vision
- `cs.AI` - Artificial Intelligence
- `stat.ML` - Machine Learning (Statistics)
- `math.OC` - Optimization and Control
- `quant-ph` - Quantum Physics

### Tips for Better Results

1. **Start Simple**: If complex queries return no results, try simpler terms
   ```bash
   # Instead of this:
   arxiv-cli search "transformer architecture attention mechanism"
   
   # Try this:
   arxiv-cli search "transformer attention"
   ```

2. **Use ArXiv's Syntax**: Always use the documented prefixes (au:, ti:, etc.)

3. **Check Spelling**: ArXiv doesn't do fuzzy matching
   ```bash
   # This works:
   arxiv-cli search "au:Hinton"
   
   # This doesn't:
   arxiv-cli search "au:Hinto"  # Missing 'n'
   ```

4. **Recent Papers First**: Results are sorted by submission date (newest first)

5. **Boolean Operators**: Use AND, OR, NOT for complex queries
   ```bash
   arxiv-cli search "transformer AND NOT bert"
   arxiv-cli search "quantum OR classical"
   ```

## Troubleshooting Searches

If you're getting no results:

1. **Remove filters**: Start with just keywords
2. **Check syntax**: Ensure you're using correct prefixes
3. **Try diagnostics**: Run `arxiv-cli diagnostics` to check connectivity
4. **Simplify query**: Break complex queries into simpler parts

## Examples

```bash
# Find papers by a specific author
arxiv-cli search "au:\"Yann LeCun\""

# Find papers about transformers in NLP
arxiv-cli search "ti:transformer AND cat:cs.CL"

# Recent papers on quantum computing
arxiv-cli search "all:quantum computing" --date-from "2024-01-01"

# Papers with specific terms in abstract
arxiv-cli search "abs:\"few-shot learning\""
```