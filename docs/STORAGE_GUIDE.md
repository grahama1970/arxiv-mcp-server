# ArXiv MCP Server Storage Guide

## Storage Location

The ArXiv MCP server stores papers in a configurable location, with the following priority:

1. **Command line argument**: `--storage-path /path/to/storage`
2. **Environment variable**: `ARXIV_STORAGE_PATH=/path/to/storage`
3. **Project directory**: `./data/papers/` (recommended for MCP projects)
4. **User home**: `~/.arxiv-mcp-server/papers/` (backwards compatibility)

## Recommended Structure for MCP Projects

```
project-root/
├── data/
│   ├── papers/
│   │   ├── pdfs/          # Original PDF files
│   │   ├── markdown/      # Converted markdown files
│   │   ├── json/          # JSON conversions (from marker-pdf)
│   │   └── metadata/      # Paper metadata and version info
│   └── annotations/       # User notes and tags
└── tests/
    └── test_data/        # Sample papers for testing
```

## Benefits of Project-Based Storage

1. **Portability**: Everything is self-contained within the project
2. **Version Control**: Can include test papers in git
3. **Deployment**: Easier to deploy as a complete package
4. **Testing**: Tests can use local test data
5. **Development**: Multiple developers can work without conflicts

## Configuration Examples

### Using Project Directory (Recommended)

```json
{
  "mcpServers": {
    "arxiv-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/arxiv-mcp-server",
        "run",
        "arxiv-mcp-server",
        "--storage-path", "./data/papers"
      ]
    }
  }
}
```

### Using Environment Variable

```bash
export ARXIV_STORAGE_PATH=/path/to/arxiv-mcp-server/data/papers
```

### Using Absolute Path

```json
{
  "mcpServers": {
    "arxiv-mcp-server": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "arxiv-mcp-server",
        "--storage-path", "/home/user/research/papers"
      ]
    }
  }
}
```

## Migration from Old Storage

If you have papers in the old location (`~/.arxiv-mcp-server/papers/`), use the migration script:

```bash
cd /path/to/arxiv-mcp-server
python scripts/migrate_papers.py
```

## Version Tracking

To properly handle ArXiv paper versions, the system should store metadata:

```json
{
  "paper_id": "2312.02813",
  "version": "v2",
  "downloaded_at": "2024-01-15T10:30:00Z",
  "arxiv_updated": "2023-12-15T14:22:00Z",
  "file_paths": {
    "pdf": "pdfs/2312.02813.pdf",
    "markdown": "markdown/2312.02813.md"
  }
}
```

## Storage Best Practices

1. **Organize by type**: Keep PDFs, markdown, and JSON files in separate directories
2. **Preserve originals**: Always keep the original PDF
3. **Track versions**: Store metadata about paper versions
4. **Clean filenames**: Use paper ID as filename (e.g., `2312.02813.pdf`)
5. **Gitignore data**: Don't commit downloaded papers to git (except test data)

## Disk Space Management

Typical space requirements:
- PDF: 1-5 MB per paper
- Markdown: 50-200 KB per paper
- JSON: 100-500 KB per paper
- Metadata: ~1 KB per paper

For 1000 papers, expect to use 2-6 GB of disk space.

## Backup Recommendations

1. **Important papers**: Keep backups of critical research papers
2. **Annotations**: Always backup the `annotations/` directory
3. **Metadata**: Backup metadata to track paper versions
4. **Cloud sync**: Consider syncing the data directory to cloud storage

## Security Considerations

1. **Permissions**: Ensure data directory has appropriate permissions
2. **Sensitive data**: Don't store sensitive papers in shared locations
3. **Access control**: Use file system permissions to control access
4. **Encryption**: Consider encrypting the storage for sensitive research