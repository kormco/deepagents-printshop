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

    @property
    def rendering_instructions(self) -> str:
        """Extract the ## Rendering Instructions section text."""
        if not self.type_md_content:
            return ""
        match = re.search(
            r'## Rendering Instructions\s*\n(.*?)(?=\n## |\Z)',
            self.type_md_content,
            re.DOTALL
        )
        return match.group(1).strip() if match else ""

    @property
    def latex_preamble_blocks(self) -> List[str]:
        """Extract all ```latex code blocks from the ## LaTeX Requirements section."""
        if not self.type_md_content:
            return []
        section_match = re.search(
            r'## LaTeX Requirements\s*\n(.*?)(?=\n## |\Z)',
            self.type_md_content,
            re.DOTALL
        )
        if not section_match:
            return []
        section_text = section_match.group(1)
        return re.findall(r'```latex\s*\n(.*?)```', section_text, re.DOTALL)

    @property
    def structure_rules(self) -> str:
        """Extract the ## Structure Rules section text."""
        if not self.type_md_content:
            return ""
        match = re.search(
            r'## Structure Rules\s*\n(.*?)(?=\n## |\Z)',
            self.type_md_content,
            re.DOTALL
        )
        return match.group(1).strip() if match else ""


class ContentTypeLoader:
    """
    Loads content type definitions from content_types/ directory.

    Each content type is a directory containing a type.md file with:
    - Type Metadata section with structured fields
    - Rendering Instructions for LLM consumption
    - LaTeX Requirements for package/preamble info
    - Structure Rules for compilation constraints
    """

    def __init__(self, types_dir: Optional[str] = None):
        if types_dir is not None:
            self.types_dir = Path(types_dir)
        else:
            # Resolve from this file's location so it works regardless of CWD
            self.types_dir = Path(__file__).parent.parent / "content_types"

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
