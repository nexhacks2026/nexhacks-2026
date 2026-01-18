"""
Document Loader Service

Loads markdown documentation files and compresses them using tokenc
for optimal token usage when feeding context to AI agents.
"""

import os
import logging
from pathlib import Path
from typing import Dict

from tokenc import TokenClient

from app.config import Config

logger = logging.getLogger(__name__)


class DocLoader:
    """Load and compress documentation for AI context."""

    def __init__(self):
        self.client = None
        self.docs_path = Path(Config.DOCS_PATH)
        self.compressed_docs: Dict[str, str] = {}
        self.raw_docs: Dict[str, str] = {}
        self._initialized = False

    def _init_client(self):
        """Initialize the TokenClient if API key is available."""
        if Config.TOKENC_API_KEY:
            self.client = TokenClient(api_key=Config.TOKENC_API_KEY)
            logger.info("TokenClient initialized with API key")
        else:
            logger.warning("TOKENC_API_KEY not set - docs will be used without compression")

    async def load_and_compress_docs(self):
        """Load all markdown docs from DOCS folder and compress them."""
        self._init_client()

        if not self.docs_path.exists():
            logger.warning(f"Docs path does not exist: {self.docs_path}")
            return

        logger.info(f"Loading docs from: {self.docs_path}")

        for md_file in self.docs_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                doc_name = md_file.stem

                # Store raw content
                self.raw_docs[doc_name] = content

                # Compress if client is available
                if self.client:
                    try:
                        response = self.client.compress_input(
                            input=content,
                            aggressiveness=0.5
                        )
                        self.compressed_docs[doc_name] = response.output
                        logger.info(
                            f"Compressed '{doc_name}': {response.original_input_tokens} -> "
                            f"{response.output_tokens} tokens ({response.compression_ratio:.2f}x)"
                        )
                    except Exception as e:
                        logger.error(f"Failed to compress '{doc_name}': {e}")
                        self.compressed_docs[doc_name] = content
                else:
                    # No compression - use raw content
                    self.compressed_docs[doc_name] = content

            except Exception as e:
                logger.error(f"Failed to load doc '{md_file}': {e}")

        self._initialized = True
        logger.info(f"Loaded {len(self.compressed_docs)} documentation files")

    def get_docs_context(self) -> str:
        """
        Get all compressed docs formatted as context for AI prompts.
        
        Returns:
            Formatted string with all documentation.
        """
        if not self.compressed_docs:
            return "No documentation available."

        sections = []
        for name, content in self.compressed_docs.items():
            # Clean up the name for display
            display_name = name.replace("_", " ").replace("-", " ").title()
            sections.append(f"## {display_name}\n{content}")

        return "\n\n---\n\n".join(sections)

    def get_doc(self, name: str) -> str:
        """Get a specific compressed doc by name."""
        return self.compressed_docs.get(name, "")

    def list_docs(self) -> list:
        """List all available doc names."""
        return list(self.compressed_docs.keys())


# Singleton instance
doc_loader = DocLoader()
