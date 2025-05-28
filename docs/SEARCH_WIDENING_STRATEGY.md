# Search Widening Strategy

## Overview

Our search implementation follows an **iterative widening** approach. We start with the exact query the user provided, and if that returns no results, we progressively broaden the search using various strategies until we find relevant papers.

## The Widening Cascade

```
User Query: "transformer architecture attention mechanism"
    ↓
1. EXACT SEARCH → 0 results? Continue...
    ↓
2. REMOVE QUOTES → Still 0? Continue...
   "exact phrase search" → exact phrase search
    ↓
3. USE OR OPERATORS → Still 0? Continue...
   "transformer attention" → "transformer OR attention"
    ↓
4. TRY ALL FIELDS → Still 0? Continue...
   "ti:transformer" → "all:(transformer)"
    ↓
5. FIX MISSPELLINGS → Still 0? Continue...
   "author:Hinton" → "au:Hinton"
   "transfomer" → "transformer"
    ↓
6. EXTRACT KEY TERMS → Still 0? Show helpful message
   "the transformer architecture" → "transformer OR architecture"
```

## Detailed Strategy Breakdown

### Strategy 1: Exact Search (Always First)
```python
# Try exactly what the user asked for
query = "transformer architecture attention mechanism"
```

### Strategy 2: Remove Restrictive Quotes
```python
# Quotes might be too restrictive
"neural network \"exact phrase\" model" → "neural network exact phrase model"
```

### Strategy 3: OR Search with Keywords
```python
# Find papers matching ANY of the terms
"transformer attention mechanism" → "transformer OR attention OR mechanism"
```

### Strategy 4: Grouped All-Fields Search
```python
# Search across all fields with grouping
"transformer attention" → "all:(transformer OR attention)"
```

### Strategy 5: Fix Common Issues
```python
# Correct misspellings and wrong syntax
corrections = {
    'author:': 'au:',        # Wrong prefix
    'transfomer': 'transformer',  # Misspelling
    'nueral': 'neural',      # Common typo
}
```

### Strategy 6: Final Attempt with Core Terms
```python
# Extract only the most important words
"the transformer architecture for nlp" → "transformer OR architecture OR nlp"
```

## User Feedback

When we widen the search, users receive clear feedback:

```json
{
  "search_status": "widened",
  "widening_info": {
    "notice": "SEARCH AUTOMATICALLY BROADENED",
    "reason": "No exact matches found for: transformer architecture attention mechanism",
    "action": "Showing results from a simplified search",
    "details": [
      "Used OR operators to find papers matching any of your terms",
      "Searched across all paper fields instead of specific ones",
      "Corrected common misspellings and syntax errors",
      "Found 15 potentially relevant papers"
    ],
    "recommendation": "Please review these results as they may still be relevant to your needs"
  },
  "papers": [...]
}
```

## Benefits of This Approach

1. **User Intent Preserved**: We always try the exact query first
2. **Progressive Relaxation**: Each step slightly broadens the search
3. **Transparent Process**: Users know when and how we widened their search
4. **Better UX**: Users get results instead of "0 papers found"
5. **AI-Friendly**: Claude Desktop can evaluate if widened results are still relevant

## Examples

### Example 1: Misspelled Author
```
User: "author:Hinto neural networks"
Step 1: Exact search → 0 results
Step 2: Fix "author:" → "au:" → Still 0 results
Step 3: Fix "Hinto" → "Hinton" → Results found!
Message: "Corrected query to: au:Hinton neural networks"
```

### Example 2: Too Specific Query
```
User: "transformer self-attention mechanism for protein folding in drug discovery"
Step 1: Exact search → 0 results
Step 2: Extract keywords → "transformer OR self-attention OR protein OR folding OR drug OR discovery"
Step 3: Results found!
Message: "No exact matches. Showing papers matching any of your key terms."
```

### Example 3: Wrong Field Syntax
```
User: "title:attention is all you need"
Step 1: Exact search → 0 results  
Step 2: Fix prefix → "ti:attention is all you need"
Step 3: Try without quotes → "ti:attention ti:all ti:you ti:need"
Step 4: Try OR → "ti:(attention OR all OR you OR need)"
Step 5: Results found!
Message: "Corrected field prefix and broadened title search"
```

## Implementation Notes

- We only widen if the initial search returns **exactly 0 results**
- Date filters disable widening (to preserve user's time constraints)
- Each strategy is logged for debugging
- The process stops as soon as results are found
- Maximum time limit prevents infinite searching

This iterative approach ensures users get the most relevant results possible while being transparent about how we modified their search.