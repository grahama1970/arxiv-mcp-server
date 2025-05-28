# ArXiv Search Tips

## Search Syntax Guide

ArXiv supports advanced search queries with boolean operators and field-specific searches. Here's the complete syntax guide:

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

### Boolean Operators

ArXiv supports full boolean logic for powerful searches:

```bash
# OR operator - finds papers matching ANY term
arxiv-cli search "transformer OR bert OR gpt"

# AND operator - finds papers matching ALL terms
arxiv-cli search "transformer AND attention"

# ANDNOT operator - excludes papers with specific terms
arxiv-cli search "transformer ANDNOT bert"

# Parentheses for grouping
arxiv-cli search "(transformer OR bert) AND attention"
arxiv-cli search "au:Hinton AND (neural OR deep OR network)"
```

### Complex Queries

```bash
# Combine multiple fields with boolean logic
arxiv-cli search "au:Vaswani AND ti:attention"
arxiv-cli search "au:(Hinton OR Bengio) AND cat:cs.LG"

# Search within categories with OR
arxiv-cli search "(ti:transformer OR ti:bert) AND cat:cs.CL"

# Complex grouped queries
arxiv-cli search "(transformer OR bert OR gpt) AND (attention OR self-attention)"

# Exclude specific terms
arxiv-cli search "au:del_maestro ANDNOT (ti:checkerboard OR ti:Pyrochlore)"

# Use quotes for exact phrases
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

1. **Use OR for Flexible Searches**: When looking for related concepts
   ```bash
   # Find papers about any of these topics
   arxiv-cli search "transformer OR attention OR self-attention"
   
   # Find papers by any of these authors
   arxiv-cli search "au:(Hinton OR LeCun OR Bengio)"
   ```

2. **Use Parentheses for Complex Logic**: Group related terms
   ```bash
   # Papers about transformers OR bert, that also mention attention
   arxiv-cli search "(transformer OR bert) AND attention"
   
   # Papers in ML that discuss neural OR deep methods
   arxiv-cli search "cat:cs.LG AND (neural OR deep)"
   ```

3. **Use ANDNOT to Filter Out Topics**: Exclude unwanted results
   ```bash
   # Transformers but not BERT-related
   arxiv-cli search "transformer ANDNOT bert"
   
   # Machine learning but not reinforcement learning
   arxiv-cli search "cat:cs.LG ANDNOT reinforcement"
   ```

4. **Check Spelling**: ArXiv doesn't do fuzzy matching for field searches
   ```bash
   # This works:
   arxiv-cli search "au:Hinton"
   
   # This doesn't:
   arxiv-cli search "au:Hinto"  # Missing 'n'
   ```

5. **Combine Strategies**: Mix field searches with boolean logic
   ```bash
   # Papers by specific authors on specific topics
   arxiv-cli search "au:(Hinton OR Bengio) AND ti:(neural OR deep)"
   
   # Recent papers in multiple categories
   arxiv-cli search "(cat:cs.LG OR cat:stat.ML) AND transformer"
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