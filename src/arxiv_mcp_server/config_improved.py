"""Improved configuration settings for the arXiv MCP server."""

import sys
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Server configuration settings."""

    APP_NAME: str = "arxiv-mcp-server"
    APP_VERSION: str = "0.3.0"
    MAX_RESULTS: int = 50
    BATCH_SIZE: int = 20
    REQUEST_TIMEOUT: int = 60
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    model_config = SettingsConfigDict(extra="allow")

    @property
    def PROJECT_ROOT(self) -> Path:
        """Get the project root directory."""
        # Try to find project root by looking for pyproject.toml
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        # Fallback to parent of src directory
        return Path(__file__).resolve().parent.parent.parent

    @property
    def STORAGE_PATH(self) -> Path:
        """Get the resolved storage path and ensure it exists.

        Priority order:
        1. Command line argument (--storage-path)
        2. Environment variable (ARXIV_STORAGE_PATH)
        3. Project directory (./data/papers)
        4. User home directory (~/.arxiv-mcp-server/papers) - backwards compatibility

        Returns:
            Path: The absolute storage path.
        """
        path = (
            self._get_storage_path_from_args()
            or self._get_storage_path_from_env()
            or self._get_project_storage_path()
            or Path.home() / ".arxiv-mcp-server" / "papers"  # Fallback for backwards compatibility
        )
        path = path.resolve()
        path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (path / "pdfs").mkdir(exist_ok=True)
        (path / "markdown").mkdir(exist_ok=True)
        (path / "json").mkdir(exist_ok=True)
        (path / "metadata").mkdir(exist_ok=True)
        
        return path

    def _get_storage_path_from_env(self) -> Path | None:
        """Get storage path from environment variable."""
        env_path = os.getenv("ARXIV_STORAGE_PATH")
        if env_path:
            try:
                return Path(env_path).resolve()
            except Exception as e:
                logger.warning(f"Invalid ARXIV_STORAGE_PATH: {e}")
        return None

    def _get_project_storage_path(self) -> Path | None:
        """Get storage path within project directory."""
        try:
            project_root = self.PROJECT_ROOT
            return project_root / "data" / "papers"
        except Exception as e:
            logger.warning(f"Could not determine project storage path: {e}")
        return None

    def _get_storage_path_from_args(self) -> Path | None:
        """Extract storage path from command line arguments.

        Returns:
            Path | None: The storage path if specified in arguments, None otherwise.
        """
        args = sys.argv[1:]

        # If not enough arguments
        if len(args) < 2:
            return None

        # Look for the --storage-path option
        try:
            storage_path_index = args.index("--storage-path")
        except ValueError:
            return None

        # Early return if --storage-path is the last argument
        if storage_path_index + 1 >= len(args):
            return None

        # Try to resolve the path
        try:
            path = Path(args[storage_path_index + 1])
            return path.resolve()
        except (TypeError, ValueError) as e:
            # TypeError: If the path argument is not string-like
            # ValueError: If the path string is malformed
            logger.warning(f"Invalid storage path format: {e}")
        except OSError as e:
            # OSError: If the path contains invalid characters or is too long
            logger.warning(f"Invalid storage path: {e}")

        return None

    def get_paper_path(self, paper_id: str, file_type: str = "pdf") -> Path:
        """Get the path for a specific paper file.
        
        Args:
            paper_id: ArXiv paper ID
            file_type: Type of file (pdf, markdown, json, metadata)
            
        Returns:
            Path to the file
        """
        if file_type == "pdf":
            return self.STORAGE_PATH / "pdfs" / f"{paper_id}.pdf"
        elif file_type == "markdown":
            return self.STORAGE_PATH / "markdown" / f"{paper_id}.md"
        elif file_type == "json":
            return self.STORAGE_PATH / "json" / f"{paper_id}.json"
        elif file_type == "metadata":
            return self.STORAGE_PATH / "metadata" / f"{paper_id}_meta.json"
        else:
            raise ValueError(f"Unknown file type: {file_type}")