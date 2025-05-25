# ArXiv MCP Server Documentation

Welcome to the comprehensive documentation for the ArXiv MCP Server project.

## 📚 Documentation Structure

### Quick Start
- [Quick Reference](QUICK_REFERENCE.md) - All 15 tools at a glance with examples
- [Usage Guide](USAGE_GUIDE.md) - Detailed workflows and best practices

### Development
- [Development Standards](development/CLAUDE.md) - Coding standards and guidelines
- [Task Implementation Guide](tasks/README.md) - Implementation and test tasks

### Architecture
- [Refactoring Plan](architecture/REFACTORING_PLAN.md) - 3-layer architecture design
- [Refactoring Progress](architecture/REFACTORING_PROGRESS.md) - Current refactoring status

### Guides
- [Storage Guide](STORAGE_GUIDE.md) - Paper storage configuration and best practices
- [Task List Template Guide](guides/TASK_LIST_TEMPLATE_GUIDE.md) - Creating new tasks
- [3-Layer Architecture Guide](guides/3_LAYER_ARCHITECTURE.md) - Architecture patterns
- [MCP Status & Recommendations](guides/MCP_STATUS_AND_TREE_SITTER_RECOMMENDATION.md) - MCP implementation details

### Tasks
- [Implementation Tasks](tasks/) - Feature implementation tasks
- [Test Tasks](test-examples/) - Comprehensive test scenarios
- [Test Runner](tasks/TEST_RUNNER.md) - Running the test suite

## 🔍 Finding Information

### By Topic

**Getting Started**
- New users → [Quick Reference](QUICK_REFERENCE.md)
- Workflows → [Usage Guide](USAGE_GUIDE.md)

**Development**
- Contributing → [Development Standards](development/CLAUDE.md)
- Adding features → [Task Implementation Guide](tasks/README.md)

**Testing**
- Running tests → [Test Runner](tasks/TEST_RUNNER.md)
- Test examples → [Test Examples](test-examples/)

**Configuration**
- Storage setup → [Storage Guide](STORAGE_GUIDE.md)
- MCP configuration → Main README

### By Tool

Each tool has documentation in multiple places:
1. **Quick examples** - [Quick Reference](QUICK_REFERENCE.md)
2. **Detailed usage** - [Usage Guide](USAGE_GUIDE.md)
3. **Implementation** - [Task Files](tasks/001_arxiv_mcp_features.md)
4. **Tests** - [Test Examples](test-examples/)

## 📋 Complete Tool List

1. **search_papers** - Search ArXiv with filters
2. **download_paper** - Download and convert papers
3. **batch_download** - Download multiple papers concurrently
4. **list_papers** - View downloaded papers
5. **read_paper** - Read paper content
6. **summarize_paper** - Create intelligent summaries
7. **extract_citations** - Extract references (BibTeX/JSON/EndNote)
8. **extract_sections** - Extract specific sections
9. **analyze_paper_code** - Extract and analyze code blocks
10. **compare_paper_ideas** - AI-powered comparative analysis
11. **find_similar_papers** - Find related papers
12. **add_paper_note** - Add annotations
13. **list_paper_notes** - Search notes
14. **describe_paper_content** - AI description of tables/images
15. **get_system_stats** - System statistics

## 🚀 Quick Links

- [Main README](../README.md) - Project overview
- [CHANGELOG](../CHANGELOG.md) - Version history
- [LICENSE](../LICENSE) - MIT License