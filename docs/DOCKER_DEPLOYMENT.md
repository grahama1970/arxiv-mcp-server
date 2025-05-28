# Docker Deployment Guide for ArXiv MCP Server

## Why Docker?

For technically proficient scientists and engineers, Docker provides significant advantages:

1. **Dependency Isolation**: Heavy ML packages (sentence-transformers, torch) don't pollute your system
2. **Reproducibility**: Same environment across all machines
3. **Future-Proof**: Ready for ArangoDB integration
4. **Resource Control**: Memory limits prevent runaway processes
5. **Easy Updates**: Pull new image instead of managing dependencies

## Quick Start

### 1. Build and Run

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-mcp-server.git
cd arxiv-mcp-server

# Build and start the service
docker compose up -d arxiv-mcp

# View logs
docker compose logs -f arxiv-mcp
```

### 2. Configure Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "arxiv-bot": {
      "command": "bash",
      "args": ["/path/to/arxiv-mcp-server/scripts/docker-mcp-wrapper.sh"]
    }
  }
}
```

Or directly with docker compose:

```json
{
  "mcpServers": {
    "arxiv-bot": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "/path/to/arxiv-mcp-server/docker-compose.yml",
        "run", "--rm", "--no-deps", "arxiv-mcp"
      ]
    }
  }
}
```

## Architecture

### Container Structure

```
arxiv-mcp-server/
├── docker-compose.yml     # Service definitions
├── Dockerfile            # Container build instructions
├── .dockerignore        # Exclude unnecessary files
└── scripts/
    └── docker-mcp-wrapper.sh  # Claude Desktop integration
```

### Volumes

- `arxiv_papers`: Persistent storage for downloaded papers
- `model_cache`: Sentence transformer models (avoid re-downloading)
- Host mount: Optional access to papers from your filesystem

### Resource Limits

Default configuration:
- Memory: 8GB limit, 4GB reserved
- CPU: No limit (uses available cores)

Adjust in `docker-compose.yml` if needed:

```yaml
deploy:
  resources:
    limits:
      memory: 16G
      cpus: '4'
```

## Advanced Usage

### With ArangoDB (Future)

Start with database support:

```bash
docker compose --profile with-db up -d
```

This starts both the MCP server and ArangoDB for advanced features.

### Research Environment

Launch Jupyter for paper analysis:

```bash
docker compose --profile research up -d jupyter
```

Access at http://localhost:8888

### Development Mode

The compose file mounts `./src` for hot-reloading during development:

```yaml
volumes:
  - ./src:/app/src:ro  # Read-only mount
```

Edit your code locally and changes reflect immediately.

### Environment Variables

Create `.env` file for configuration:

```bash
# API Keys (optional)
GEMINI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Logging
LOG_LEVEL=DEBUG

# Database (when using --profile with-db)
ARANGO_PASSWORD=secure_password_here
```

## Performance Optimization

### For Mac Users (Apple Silicon)

The container handles Mac compatibility automatically:
- Disables sentence-transformers on Intel Macs
- Uses native ARM builds on M1/M2/M3

### Large Paper Collections

If processing many papers:

1. Increase memory limit
2. Use named volumes for better I/O performance
3. Consider local SSD storage

### Model Caching

Sentence transformer models are cached in a named volume to avoid re-downloading:

```yaml
volumes:
  - model_cache:/data/models
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs arxiv-mcp

# Rebuild if needed
docker compose build --no-cache arxiv-mcp
```

### Permission Issues

```bash
# Fix volume permissions
docker compose run --rm arxiv-mcp chown -R 1000:1000 /data/papers
```

### Memory Issues

```bash
# Check resource usage
docker stats arxiv-mcp

# Increase limits in docker-compose.yml
```

### Clean Up

```bash
# Stop services
docker compose down

# Remove volumes (WARNING: deletes all papers)
docker compose down -v

# Remove all traces
docker system prune -a
```

## Production Deployment

### Cloud Deployment

The same Docker image works on:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- Kubernetes

### Security Considerations

1. Don't expose ports unless needed
2. Use secrets management for API keys
3. Run as non-root user (add to Dockerfile)
4. Enable read-only root filesystem

### Monitoring

Add health checks and metrics:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Benefits Over Direct Installation

1. **No Python Version Conflicts**: Container has its own Python 3.11
2. **Clean System**: No global pip packages
3. **Easy Removal**: Just delete the container
4. **Consistent Environment**: Same versions everywhere
5. **Future Database Ready**: ArangoDB integration is trivial

## Next Steps

1. **Basic Usage**: Start with the default configuration
2. **Add API Keys**: Enable LLM features via `.env`
3. **Enable Database**: Use `--profile with-db` when ready
4. **Customize Resources**: Adjust memory/CPU for your workload

For scientists and engineers comfortable with Docker, this deployment method provides the most flexibility and control over the ArXiv MCP Server.