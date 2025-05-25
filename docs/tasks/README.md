# ArXiv MCP Server Tasks

This directory contains implementation tasks for the ArXiv MCP server following the task template guide format.

## Implementation Tasks

| Task File | Description | Status |
|-----------|-------------|--------|
| `001_arxiv_mcp_features.md` | Implement 7 research-focused tools for the ArXiv MCP server | ✅ COMPLETED |
| `002_3layer_architecture_refactor.md` | Refactor to 3-layer architecture (core/cli/mcp) | 🚧 IN PROGRESS |

## Test Tasks

| Task File | Description | Status |
|-----------|-------------|--------|
| `002_test_search_papers.md` | Test search_papers tool with filters | ✅ READY |
| `003_test_download_paper.md` | Test download_paper with converters | ✅ READY |
| `004_test_batch_download.md` | Test batch_download concurrent operations | ✅ READY |
| `005_test_extract_citations.md` | Test extract_citations formats | ✅ READY |
| `006_test_compare_paper_ideas.md` | Test compare_paper_ideas AI analysis | ✅ READY |
| `007_test_find_similar_papers.md` | Test find_similar_papers similarity | ✅ READY |
| `008_test_extract_sections.md` | Test extract_sections from papers | ✅ READY |
| `009_test_paper_notes.md` | Test add/list_paper_notes CRUD | ✅ READY |
| `010_test_summarize_paper.md` | Test summarize_paper strategies | ✅ READY |
| `011_test_integration_workflow.md` | Test complete research workflow | ✅ READY |

## Test Runner

| File | Description |
|------|-------------|
| `TEST_RUNNER.md` | Comprehensive guide for running all tests |
| `/test_all_tools.py` | Automated test suite executable |

## Task Structure

Each task file contains:
1. **Complete working code** - Copy-paste ready implementations
2. **Exact integration steps** - Where to add imports and handlers
3. **Test commands** - How to verify the implementation
4. **Common issues** - Pre-solved problems with solutions
5. **Validation checklist** - Clear success criteria

## Implementation Guide

To implement a task:

```bash
# 1. Read the task file
cat docs/tasks/001_arxiv_mcp_features.md

# 2. Copy each tool's code to the specified location
# 3. Update integration files as shown
# 4. Run the test commands
# 5. Check off items in the validation checklist
```

## Design Principles

All features follow these constraints:
- ✅ No external service dependencies (except optional LLM APIs)
- ✅ Local storage only
- ✅ Build on existing MCP architecture
- ✅ Add value for daily research workflows
- ✅ Handle errors gracefully

## Task Naming Convention

Following the template guide:
- Tasks are numbered: `00N_task_name.md`
- Each task is self-contained with all code needed
- Tasks focus on implementation, not research