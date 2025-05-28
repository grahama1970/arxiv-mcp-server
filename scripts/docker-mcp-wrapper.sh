#!/bin/bash
# Wrapper script for running ArXiv MCP Server in Docker
# This script ensures the container is ready before Claude Desktop connects

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="arxiv-mcp"

# Change to project directory
cd "$PROJECT_DIR"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker Desktop." >&2
        exit 1
    fi
}

# Function to build image if needed
ensure_image() {
    if ! docker compose ps --services --filter "status=running" | grep -q "$SERVICE_NAME"; then
        echo "Building ArXiv MCP Server image..." >&2
        docker compose build "$SERVICE_NAME"
    fi
}

# Function to clean up on exit
cleanup() {
    # Don't remove volumes on exit - preserve user data
    docker compose stop "$SERVICE_NAME" 2>/dev/null || true
}

# Set up exit handler
trap cleanup EXIT

# Main execution
check_docker
ensure_image

# Run the MCP server
# - Remove container after exit (--rm)
# - Attach to stdin/stdout/stderr
# - Don't run in background
exec docker compose run \
    --rm \
    --no-deps \
    "$SERVICE_NAME"