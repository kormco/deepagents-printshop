"""
Change Tracker - Milestone 2

Tracks changes between content versions and generates detailed comparison reports.
"""

import difflib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ChangeTracker:
    """
    Tracks and analyzes changes between content versions.

    Features:
    - Generate text diffs between versions
    - Summarize changes with AI analysis
    - Track quality improvements over time
    - Create detailed change reports
    """

    def __init__(self, base_dir: str = "artifacts"):
        """
        Initialize the change tracker.

        Args:
            base_dir: Base directory for artifacts
        """
        self.base_dir = Path(base_dir)
        self.history_dir = self.base_dir / "version_history"
        self.changes_dir = self.history_dir / "changes"
        self.diffs_dir = self.history_dir / "diffs"

        # Ensure directories exist
        self.changes_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)

    def generate_diff(self,
                     old_content: str,
                     new_content: str,
                     filename: str = "content") -> Dict:
        """
        Generate a detailed diff between two text contents.

        Args:
            old_content: Original content
            new_content: Modified content
            filename: Name of the file being compared

        Returns:
            Dictionary containing diff information
        """
        # Split content into lines
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate unified diff
        unified_diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{filename} (old)",
            tofile=f"{filename} (new)",
            lineterm=""
        ))

        # Generate HTML diff
        html_diff = difflib.HtmlDiff()
        html_table = html_diff.make_table(
            old_lines,
            new_lines,
            fromdesc=f"{filename} (old)",
            todesc=f"{filename} (new)"
        )

        # Calculate statistics
        differ = difflib.SequenceMatcher(None, old_content, new_content)
        similarity_ratio = differ.ratio()

        # Count changes
        additions = sum(1 for line in unified_diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in unified_diff if line.startswith('-') and not line.startswith('---'))
        modifications = min(additions, deletions)
        net_additions = additions - modifications
        net_deletions = deletions - modifications

        return {
            "filename": filename,
            "unified_diff": unified_diff,
            "html_diff": html_table,
            "similarity_ratio": similarity_ratio,
            "statistics": {
                "additions": net_additions,
                "deletions": net_deletions,
                "modifications": modifications,
                "total_changes": additions + deletions,
                "similarity_percentage": round(similarity_ratio * 100, 2)
            },
            "old_line_count": len(old_lines),
            "new_line_count": len(new_lines),
            "line_change": len(new_lines) - len(old_lines)
        }

    def compare_versions(self,
                        old_content_dict: Dict[str, str],
                        new_content_dict: Dict[str, str],
                        old_version: str,
                        new_version: str) -> Dict:
        """
        Compare two complete versions and generate comprehensive change analysis.

        Args:
            old_content_dict: Content of the old version
            new_content_dict: Content of the new version
            old_version: Name of the old version
            new_version: Name of the new version

        Returns:
            Complete comparison report
        """
        comparison = {
            "old_version": old_version,
            "new_version": new_version,
            "comparison_timestamp": datetime.now().isoformat(),
            "file_changes": {},
            "summary": {
                "files_added": [],
                "files_removed": [],
                "files_modified": [],
                "total_additions": 0,
                "total_deletions": 0,
                "total_modifications": 0,
                "average_similarity": 0
            }
        }

        # Find all files in both versions
        old_files = set(old_content_dict.keys())
        new_files = set(new_content_dict.keys())

        # Categorize changes
        added_files = new_files - old_files
        removed_files = old_files - new_files
        common_files = old_files & new_files

        comparison["summary"]["files_added"] = list(added_files)
        comparison["summary"]["files_removed"] = list(removed_files)

        # Analyze common files
        similarities = []
        for filename in common_files:
            old_content = old_content_dict[filename]
            new_content = new_content_dict[filename]

            diff_result = self.generate_diff(old_content, new_content, filename)
            comparison["file_changes"][filename] = diff_result

            # Check if file was actually modified
            if diff_result["statistics"]["total_changes"] > 0:
                comparison["summary"]["files_modified"].append(filename)

            # Accumulate statistics
            stats = diff_result["statistics"]
            comparison["summary"]["total_additions"] += stats["additions"]
            comparison["summary"]["total_deletions"] += stats["deletions"]
            comparison["summary"]["total_modifications"] += stats["modifications"]
            similarities.append(diff_result["similarity_ratio"])

        # Handle added files
        for filename in added_files:
            new_content = new_content_dict[filename]
            line_count = len(new_content.splitlines())
            comparison["file_changes"][filename] = {
                "filename": filename,
                "status": "added",
                "new_line_count": line_count,
                "statistics": {
                    "additions": line_count,
                    "deletions": 0,
                    "modifications": 0,
                    "total_changes": line_count
                }
            }
            comparison["summary"]["total_additions"] += line_count

        # Handle removed files
        for filename in removed_files:
            old_content = old_content_dict[filename]
            line_count = len(old_content.splitlines())
            comparison["file_changes"][filename] = {
                "filename": filename,
                "status": "removed",
                "old_line_count": line_count,
                "statistics": {
                    "additions": 0,
                    "deletions": line_count,
                    "modifications": 0,
                    "total_changes": line_count
                }
            }
            comparison["summary"]["total_deletions"] += line_count

        # Calculate average similarity
        if similarities:
            comparison["summary"]["average_similarity"] = round(sum(similarities) / len(similarities) * 100, 2)

        return comparison

    def save_comparison(self,
                       comparison: Dict,
                       save_diffs: bool = True) -> Tuple[str, str]:
        """
        Save a comparison report to disk.

        Args:
            comparison: Comparison result from compare_versions
            save_diffs: Whether to save individual diff files

        Returns:
            Tuple of (comparison_file_path, summary_file_path)
        """
        old_version = comparison["old_version"]
        new_version = comparison["new_version"]

        # Save main comparison file
        comparison_filename = f"{old_version}_to_{new_version}.json"
        comparison_path = self.changes_dir / comparison_filename

        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)

        # Save individual diff files if requested
        if save_diffs:
            for filename, change_info in comparison["file_changes"].items():
                if "unified_diff" in change_info:
                    diff_filename = f"{filename}_{old_version}_{new_version}.diff"
                    diff_path = self.diffs_dir / diff_filename

                    with open(diff_path, 'w', encoding='utf-8') as f:
                        f.writelines(change_info["unified_diff"])

        # Create human-readable summary
        summary_filename = f"{old_version}_to_{new_version}_summary.md"
        summary_path = self.changes_dir / summary_filename
        self._create_summary_markdown(comparison, summary_path)

        return str(comparison_path), str(summary_path)

    def _create_summary_markdown(self, comparison: Dict, output_path: Path):
        """Create a human-readable markdown summary of changes."""
        old_version = comparison["old_version"]
        new_version = comparison["new_version"]
        summary = comparison["summary"]

        content = f"""# Change Summary: {old_version} → {new_version}

**Generated:** {comparison["comparison_timestamp"]}

## Overview

| Metric | Count |
|--------|-------|
| Files Added | {len(summary["files_added"])} |
| Files Removed | {len(summary["files_removed"])} |
| Files Modified | {len(summary["files_modified"])} |
| Total Additions | +{summary["total_additions"]} lines |
| Total Deletions | -{summary["total_deletions"]} lines |
| Net Change | {summary["total_additions"] - summary["total_deletions"]:+d} lines |
| Average Similarity | {summary["average_similarity"]}% |

"""

        # Files added
        if summary["files_added"]:
            content += "## Files Added\n\n"
            for filename in summary["files_added"]:
                file_info = comparison["file_changes"][filename]
                content += f"- **{filename}** (+{file_info['statistics']['additions']} lines)\n"
            content += "\n"

        # Files removed
        if summary["files_removed"]:
            content += "## Files Removed\n\n"
            for filename in summary["files_removed"]:
                file_info = comparison["file_changes"][filename]
                content += f"- **{filename}** (-{file_info['statistics']['deletions']} lines)\n"
            content += "\n"

        # Files modified
        if summary["files_modified"]:
            content += "## Files Modified\n\n"
            for filename in summary["files_modified"]:
                file_info = comparison["file_changes"][filename]
                stats = file_info["statistics"]
                similarity = stats["similarity_percentage"]

                content += f"### {filename}\n"
                content += f"- **Similarity:** {similarity}%\n"
                content += f"- **Changes:** +{stats['additions']} -{stats['deletions']} lines\n"
                content += f"- **Modifications:** {stats['modifications']} lines\n"

                # Add sample changes if available
                if "unified_diff" in file_info and file_info["unified_diff"]:
                    content += "- **Sample changes:**\n"
                    content += "  ```diff\n"
                    # Show first few diff lines
                    diff_lines = file_info["unified_diff"][:10]
                    for line in diff_lines:
                        if line.startswith(('+', '-', '@')):
                            content += f"  {line.rstrip()}\n"
                    if len(file_info["unified_diff"]) > 10:
                        content += "  ...\n"
                    content += "  ```\n"
                content += "\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def analyze_quality_progression(self, version_qualities: List[Tuple[str, int]]) -> Dict:
        """
        Analyze quality progression across multiple versions.

        Args:
            version_qualities: List of (version_name, quality_score) tuples

        Returns:
            Quality progression analysis
        """
        if len(version_qualities) < 2:
            return {"error": "Need at least 2 versions for progression analysis"}

        analysis = {
            "versions_analyzed": len(version_qualities),
            "quality_progression": [],
            "overall_improvement": 0,
            "best_version": None,
            "worst_version": None,
            "improvement_trend": "unknown"
        }

        # Calculate progression
        for i in range(1, len(version_qualities)):
            prev_version, prev_score = version_qualities[i-1]
            curr_version, curr_score = version_qualities[i]

            improvement = curr_score - prev_score
            analysis["quality_progression"].append({
                "from": prev_version,
                "to": curr_version,
                "improvement": improvement,
                "from_score": prev_score,
                "to_score": curr_score
            })

        # Overall metrics
        first_score = version_qualities[0][1]
        last_score = version_qualities[-1][1]
        analysis["overall_improvement"] = last_score - first_score

        # Best and worst versions
        best_score = max(version_qualities, key=lambda x: x[1])
        worst_score = min(version_qualities, key=lambda x: x[1])
        analysis["best_version"] = {"name": best_score[0], "score": best_score[1]}
        analysis["worst_version"] = {"name": worst_score[0], "score": worst_score[1]}

        # Determine trend
        improvements = [step["improvement"] for step in analysis["quality_progression"]]
        positive_steps = sum(1 for imp in improvements if imp > 0)
        negative_steps = sum(1 for imp in improvements if imp < 0)

        if positive_steps > negative_steps:
            analysis["improvement_trend"] = "improving"
        elif negative_steps > positive_steps:
            analysis["improvement_trend"] = "declining"
        else:
            analysis["improvement_trend"] = "stable"

        return analysis

    def create_change_report(self,
                           old_version: str,
                           new_version: str,
                           old_content: Dict[str, str],
                           new_content: Dict[str, str],
                           old_quality: Optional[int] = None,
                           new_quality: Optional[int] = None) -> str:
        """
        Create a comprehensive change report.

        Args:
            old_version: Name of the old version
            new_version: Name of the new version
            old_content: Content of the old version
            new_content: Content of the new version
            old_quality: Quality score of old version
            new_quality: Quality score of new version

        Returns:
            Path to the generated report
        """
        # Generate comparison
        comparison = self.compare_versions(old_content, new_content, old_version, new_version)

        # Add quality information if provided
        if old_quality is not None and new_quality is not None:
            comparison["quality_analysis"] = {
                "old_quality_score": old_quality,
                "new_quality_score": new_quality,
                "quality_improvement": new_quality - old_quality
            }

        # Save comparison
        comparison_path, summary_path = self.save_comparison(comparison)

        return summary_path
