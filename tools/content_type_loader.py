"""
Content Type Loader

Loads content type definitions from content_types/{type_id}/type.md files.
Provides structured metadata for DocumentConfig and raw markdown for LLM prompts.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContentTypeDefinition:
    """A loaded content type definition."""
    type_id: str
    type_md_content: str        # Full type.md — goes to LLM as-is
    document_class: str         # Extracted for DocumentConfig
    default_font_size: str      # Extracted for DocumentConfig
    default_paper_size: str     # Extracted for DocumentConfig


class ContentTypeLoader:
    """
    Loads content type definitions from content_types/ directory.

    Each content type is a directory containing a type.md file with:
    - Type Metadata section with structured fields
    - Rendering Instructions for LLM consumption
    - LaTeX Requirements for package/preamble info
    - Structure Rules for compilation constraints
    """

    def __init__(self, types_dir: str = "content_types"):
        self.types_dir = Path(types_dir)

    def load_type(self, type_id: str) -> ContentTypeDefinition:
        """
        Load a content type definition by ID.

        Args:
            type_id: The type identifier (e.g., 'research_report', 'magazine')

        Returns:
            ContentTypeDefinition with metadata and full markdown content
        """
        type_path = self.types_dir / type_id / "type.md"

        if not type_path.exists():
            logger.warning(
                "Content type '%s' not found at %s, using defaults",
                type_id, type_path
            )
            return ContentTypeDefinition(
                type_id=type_id,
                type_md_content="",
                document_class="article",
                default_font_size="12pt",
                default_paper_size="letterpaper",
            )

        with open(type_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = self._extract_metadata(content)

        return ContentTypeDefinition(
            type_id=type_id,
            type_md_content=content,
            document_class=metadata.get("document_class", "article"),
            default_font_size=metadata.get("default_font_size", "12pt"),
            default_paper_size=metadata.get("default_paper_size", "letterpaper"),
        )

    def list_types(self) -> List[str]:
        """
        List all available content type IDs.

        Returns:
            List of type_id strings
        """
        if not self.types_dir.exists():
            return []

        return sorted(
            d.name for d in self.types_dir.iterdir()
            if d.is_dir() and (d / "type.md").exists()
        )

    def _extract_metadata(self, content: str) -> dict:
        """
        Extract structured metadata from the ## Type Metadata section.

        Parses key-value pairs in the format:
            - key: value

        Returns:
            Dictionary of metadata fields
        """
        metadata = {}

        # Find the Type Metadata section
        in_metadata = False
        for line in content.split('\n'):
            stripped = line.strip()

            if stripped == '## Type Metadata':
                in_metadata = True
                continue

            if in_metadata:
                # Stop at next section header
                if stripped.startswith('## '):
                    break

                # Parse "- key: value" lines
                if stripped.startswith('- ') and ':' in stripped:
                    key_value = stripped[2:].split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        metadata[key] = value

        return metadata
