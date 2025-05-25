# 3-Layer Architecture Refactoring Plan for ArXiv MCP Server

## ⚠️ IMPORTANT CONSIDERATIONS

This refactoring would be a **MAJOR architectural change** that would:
- Require moving/renaming most files
- Change all import paths
- Potentially break existing integrations
- Require extensive testing

## Current vs Target Architecture

### Current Structure
```
src/arxiv_mcp_server/
├── tools/              # 20+ individual tool files
├── prompts/            # Prompt management
├── resources/          # Resource management  
├── server.py           # MCP server
├── cli.py             # CLI interface
├── config.py          # Configuration
├── llm_providers.py   # LLM integrations
└── converters*.py     # PDF converters
```

### Target 3-Layer Structure
```
src/arxiv_mcp_server/
├── core/              # Pure business logic
│   ├── search.py      # ArXiv search functionality
│   ├── download.py    # Paper download logic
│   ├── analysis.py    # Paper analysis functions
│   ├── similarity.py  # Similarity calculations
│   ├── citations.py   # Citation extraction
│   ├── research.py    # Research support logic
│   ├── converters.py  # PDF conversion logic
│   ├── llm.py        # LLM provider abstractions
│   └── utils.py      # Shared utilities
├── cli/              # CLI layer
│   ├── app.py        # Main Typer application
│   ├── formatters.py # Rich formatting
│   ├── validators.py # Input validation
│   └── schemas.py    # Pydantic models
└── mcp/              # MCP layer
    ├── schema.py     # MCP schemas for all tools
    ├── wrapper.py    # FastMCP integration
    └── handlers.py   # Tool handlers
```

## Refactoring Steps Required

### Phase 1: Create Core Layer
1. Extract business logic from `tools/*.py` into `core/` modules
2. Remove MCP-specific imports and types
3. Make functions pure and independently testable
4. Consolidate related functionality

### Phase 2: Refactor CLI Layer  
1. Move existing `cli.py` to `cli/app.py`
2. Extract formatting logic to `cli/formatters.py`
3. Add input validation to `cli/validators.py`
4. Create Pydantic models in `cli/schemas.py`

### Phase 3: Refactor MCP Layer
1. Move `server.py` logic to `mcp/wrapper.py`
2. Create unified schema definitions in `mcp/schema.py`
3. Move tool handlers to `mcp/handlers.py`
4. Update MCP registration

### Phase 4: Update Imports
1. Update all import statements throughout the codebase
2. Update `__init__.py` files
3. Update test imports
4. Update pyproject.toml entry points

## Impact Analysis

### Files to Move/Refactor
- 20+ files in `tools/` → `core/` (consolidated)
- `cli.py` → `cli/app.py` (enhanced)
- `server.py` → `mcp/wrapper.py`
- All prompt files → integrated into appropriate layers

### Import Changes Required
```python
# Before
from arxiv_mcp_server.tools.search import search_handler

# After  
from arxiv_mcp_server.core.search import search_papers
from arxiv_mcp_server.mcp.handlers import search_handler
```

### Testing Impact
- All tests would need import updates
- Integration tests might break
- CLI tests would need refactoring

## Risk Assessment

### High Risk Areas
1. **Import paths**: All imports would change
2. **Entry points**: CLI and MCP server entry points
3. **External integrations**: Any code depending on current structure
4. **Test suite**: Extensive test updates needed

### Mitigation Strategies
1. Create compatibility layer during transition
2. Update imports incrementally
3. Run full test suite after each phase
4. Keep backup of current structure

## Recommendation

Given the requirement to avoid breaking functionality, I recommend:

### Option 1: Gradual Migration
- Create new 3-layer structure alongside existing
- Migrate one module at a time
- Maintain compatibility layer
- Deprecate old structure over time

### Option 2: Feature Freeze Refactoring
- Stop new feature development
- Refactor entire codebase at once
- Extensive testing period
- Single cutover

### Option 3: New Project Structure
- Keep current structure for MCP server
- Apply 3-layer architecture to new features only
- Gradually migrate as modules are updated

## Decision Required

Before proceeding with this major refactoring:

1. **Confirm**: Do you want to proceed with this architectural change?
2. **Choose**: Which migration approach (1, 2, or 3)?
3. **Timeline**: When should this be completed?
4. **Testing**: What level of testing is required?

⚠️ **This is a significant undertaking that will require careful planning and execution to avoid breaking existing functionality.**