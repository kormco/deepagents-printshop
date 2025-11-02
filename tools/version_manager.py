"""
Version Manager - Milestone 2

Handles content versioning, tracking, and management for iterative improvements.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib


class VersionManager:
    """
    Manages content versions and provides version tracking capabilities.

    Features:
    - Create and track content versions
    - Generate version manifests
    - Handle rollback operations
    - Maintain version lineage
    """

    def __init__(self, base_dir: str = "artifacts"):
        """
        Initialize the version manager.

        Args:
            base_dir: Base directory for all artifacts
        """
        self.base_dir = Path(base_dir)
        self.content_dir = self.base_dir / "reviewed_content"
        self.history_dir = self.base_dir / "version_history"
        self.manifest_path = self.history_dir / "version_manifest.json"

        # Ensure directories exist
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        (self.history_dir / "changes").mkdir(exist_ok=True)
        (self.history_dir / "diffs").mkdir(exist_ok=True)

        # Initialize manifest if it doesn't exist
        self._init_manifest()

    def _init_manifest(self):
        """Initialize the version manifest file."""
        if not self.manifest_path.exists():
            manifest = {
                "versions": {},
                "latest_version": None,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            self._save_manifest(manifest)

    def _load_manifest(self) -> Dict:
        """Load the version manifest."""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_manifest(self, manifest: Dict):
        """Save the version manifest."""
        manifest["last_updated"] = datetime.now().isoformat()
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def _calculate_content_hash(self, content_dict: Dict[str, str]) -> str:
        """Calculate a hash of the content for integrity checking."""
        content_str = json.dumps(content_dict, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def create_version(self,
                      content_dict: Dict[str, str],
                      version_name: str,
                      agent_name: str = "unknown",
                      parent_version: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> Dict:
        """
        Create a new content version.

        Args:
            content_dict: Dictionary of filename -> content
            version_name: Name for this version (e.g., "v1_content_edited")
            agent_name: Name of the agent that created this version
            parent_version: Name of the parent version (if any)
            metadata: Additional metadata for this version

        Returns:
            Version info dictionary
        """
        manifest = self._load_manifest()

        # Check if version already exists
        if version_name in manifest["versions"]:
            raise ValueError(f"Version {version_name} already exists")

        # Create version directory
        version_dir = self.content_dir / version_name
        version_dir.mkdir(exist_ok=True)

        # Save content files
        for filename, content in content_dict.items():
            file_path = version_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Create version metadata
        version_info = {
            "name": version_name,
            "agent": agent_name,
            "parent_version": parent_version,
            "created_at": datetime.now().isoformat(),
            "content_hash": self._calculate_content_hash(content_dict),
            "files": list(content_dict.keys()),
            "file_count": len(content_dict),
            "directory": str(version_dir.relative_to(self.base_dir)),
            "metadata": metadata or {}
        }

        # Update manifest
        manifest["versions"][version_name] = version_info
        manifest["latest_version"] = version_name
        self._save_manifest(manifest)

        # Update current symlink
        self._update_current_symlink(version_name)

        return version_info

    def get_version(self, version_name: str) -> Optional[Dict]:
        """
        Get information about a specific version.

        Args:
            version_name: Name of the version to retrieve

        Returns:
            Version info dictionary or None if not found
        """
        manifest = self._load_manifest()
        return manifest["versions"].get(version_name)

    def get_version_content(self, version_name: str) -> Dict[str, str]:
        """
        Load the content of a specific version.

        Args:
            version_name: Name of the version to load

        Returns:
            Dictionary of filename -> content
        """
        version_info = self.get_version(version_name)
        if not version_info:
            raise ValueError(f"Version {version_name} not found")

        version_dir = self.base_dir / version_info["directory"]
        content_dict = {}

        for filename in version_info["files"]:
            file_path = version_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content_dict[filename] = f.read()

        return content_dict

    def list_versions(self) -> List[Dict]:
        """
        List all versions in chronological order.

        Returns:
            List of version info dictionaries
        """
        manifest = self._load_manifest()
        versions = list(manifest["versions"].values())

        # Sort by creation date
        versions.sort(key=lambda v: v["created_at"])

        return versions

    def get_latest_version(self) -> Optional[str]:
        """
        Get the name of the latest version.

        Returns:
            Latest version name or None if no versions exist
        """
        manifest = self._load_manifest()
        return manifest.get("latest_version")

    def get_version_lineage(self, version_name: str) -> List[str]:
        """
        Get the lineage (ancestry) of a version.

        Args:
            version_name: Version to trace lineage for

        Returns:
            List of version names from root to specified version
        """
        lineage = []
        current = version_name

        while current:
            version_info = self.get_version(current)
            if not version_info:
                break

            lineage.insert(0, current)
            current = version_info.get("parent_version")

        return lineage

    def rollback_to_version(self, version_name: str) -> Dict:
        """
        Rollback to a specific version (updates current symlink).

        Args:
            version_name: Version to rollback to

        Returns:
            Version info of the rollback target
        """
        version_info = self.get_version(version_name)
        if not version_info:
            raise ValueError(f"Version {version_name} not found")

        # Update current symlink
        self._update_current_symlink(version_name)

        # Update manifest to mark this as latest
        manifest = self._load_manifest()
        manifest["latest_version"] = version_name
        self._save_manifest(manifest)

        return version_info

    def delete_version(self, version_name: str) -> bool:
        """
        Delete a version (use with caution).

        Args:
            version_name: Version to delete

        Returns:
            True if deletion was successful
        """
        version_info = self.get_version(version_name)
        if not version_info:
            return False

        # Remove directory
        version_dir = self.base_dir / version_info["directory"]
        if version_dir.exists():
            shutil.rmtree(version_dir)

        # Update manifest
        manifest = self._load_manifest()
        del manifest["versions"][version_name]

        # Update latest if this was the latest
        if manifest.get("latest_version") == version_name:
            versions = list(manifest["versions"].values())
            if versions:
                latest = max(versions, key=lambda v: v["created_at"])
                manifest["latest_version"] = latest["name"]
            else:
                manifest["latest_version"] = None

        self._save_manifest(manifest)
        return True

    def _update_current_symlink(self, version_name: str):
        """Update the 'current' symlink to point to the specified version."""
        current_link = self.content_dir / "current"
        target_dir = version_name

        # Remove existing symlink
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()

        # Create new symlink
        current_link.symlink_to(target_dir)

    def get_version_stats(self) -> Dict:
        """
        Get statistics about all versions.

        Returns:
            Statistics dictionary
        """
        versions = self.list_versions()

        if not versions:
            return {
                "total_versions": 0,
                "earliest_version": None,
                "latest_version": None,
                "agents_used": [],
                "total_files": 0
            }

        agents = set()
        total_files = 0

        for version in versions:
            agents.add(version.get("agent", "unknown"))
            total_files += version.get("file_count", 0)

        return {
            "total_versions": len(versions),
            "earliest_version": versions[0]["name"],
            "latest_version": versions[-1]["name"],
            "agents_used": list(agents),
            "total_files": total_files,
            "average_files_per_version": total_files / len(versions) if versions else 0
        }

    def export_version_history(self, output_path: str):
        """Export complete version history to a JSON file."""
        manifest = self._load_manifest()
        stats = self.get_version_stats()

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "manifest": manifest,
            "version_lineages": {}
        }

        # Add lineage for each version
        for version_name in manifest["versions"]:
            export_data["version_lineages"][version_name] = self.get_version_lineage(version_name)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)