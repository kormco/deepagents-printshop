"""
Versioned Content Editor Agent - Milestone 2

Enhanced content editor that integrates with version management and change tracking.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.content_editor.content_reviewer import ContentReviewer
from tools.version_manager import VersionManager
from tools.change_tracker import ChangeTracker


class VersionedContentEditorAgent:
    """
    Content Editor Agent with version management capabilities.

    Features:
    - Automatic version creation for improvements
    - Change tracking between versions
    - Quality progression analysis
    - Integration with existing content review workflow
    """

    def __init__(self, memory_dir: str = ".deepagents/content_editor/memories"):
        """
        Initialize the versioned content editor agent.

        Args:
            memory_dir: Directory for storing agent memories
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.content_reviewer = ContentReviewer()
        self.version_manager = VersionManager()
        self.change_tracker = ChangeTracker()

        # Paths
        self.input_dir = Path("artifacts/sample_content")
        self.reports_dir = Path("artifacts/quality_reports")

        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize memory
        self.init_memory()

    def init_memory(self):
        """Initialize agent memory files."""
        memory_files = {
            "version_strategy.md": """# Version Management Strategy

## Version Naming Convention
- v0_original: Original source content (baseline)
- v1_content_edited: Content editor improvements
- v2_latex_optimized: LaTeX specialist improvements
- v3_visual_refined: Visual QA improvements

## Quality Thresholds
- Minimum improvement for new version: +5 points
- Quality gate for human review: 85+ points
- Rollback threshold: Quality decrease > 10 points

## Change Tracking
- Track all content modifications
- Generate diffs for human review
- Maintain quality progression analysis
- Store change summaries for learning
""",
            "improvement_patterns.md": """# Content Improvement Patterns

## Successful Improvements Tracked
- Grammar and spelling corrections
- Sentence structure optimization
- Readability enhancements
- Academic tone adjustments

## Quality Metrics to Track
- Flesch Reading Ease improvements
- Sentence length optimization
- Passive voice reduction
- Error count reduction

## Version Comparison Insights
- Track which types of changes yield best quality improvements
- Identify content types that benefit most from editing
- Monitor quality regression patterns
""",
            "agent_coordination.md": """# Multi-Agent Coordination

## Version Handoff Protocol
1. Content Editor creates v1_content_edited
2. LaTeX Specialist receives v1, creates v2_latex_optimized
3. Visual QA receives v2, creates v3_visual_refined
4. Human review at quality gate thresholds

## Quality Progression Management
- Each agent must improve quality score
- Rollback if quality decreases significantly
- Track agent-specific improvement patterns
- Coordinate version naming and metadata
"""
        }

        for filename, content in memory_files.items():
            file_path = self.memory_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def load_original_content(self) -> Dict[str, str]:
        """Load original content from sample_content directory."""
        content_dict = {}

        for file_path in self.input_dir.glob("*.md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content_dict[file_path.name] = f.read()

        return content_dict

    def create_baseline_version(self) -> Dict:
        """
        Create v0_original baseline version from sample content.

        Returns:
            Version info for the baseline
        """
        original_content = self.load_original_content()

        if not original_content:
            raise ValueError("No original content found in sample_content directory")

        # Check if baseline already exists
        baseline_version = self.version_manager.get_version("v0_original")
        if baseline_version:
            print("✓ Baseline version v0_original already exists")
            return baseline_version

        # Create baseline version
        version_info = self.version_manager.create_version(
            content_dict=original_content,
            version_name="v0_original",
            agent_name="baseline",
            parent_version=None,
            metadata={
                "description": "Original source content from sample_content",
                "purpose": "baseline",
                "quality_score": None  # Will be calculated
            }
        )

        print(f"✓ Created baseline version: v0_original with {len(original_content)} files")
        return version_info

    def process_content_with_versioning(self,
                                      target_version: str = "v1_content_edited",
                                      parent_version: str = "v0_original") -> Dict:
        """
        Process content with full version management.

        Args:
            target_version: Name for the new version to create
            parent_version: Parent version to improve from

        Returns:
            Processing results with version information
        """
        print(f"🔄 Processing content: {parent_version} → {target_version}")

        # Ensure baseline exists
        self.create_baseline_version()

        # Load parent version content
        if parent_version == "v0_original":
            parent_content = self.load_original_content()
        else:
            parent_content = self.version_manager.get_version_content(parent_version)

        # Calculate parent quality scores
        parent_quality_scores = {}
        parent_total_score = 0

        for filename, content in parent_content.items():
            metrics = self.content_reviewer.analyze_readability(content)
            issues = self.content_reviewer._identify_issues(content, metrics)
            quality_score = self.content_reviewer.calculate_quality_score(metrics, issues)
            parent_quality_scores[filename] = quality_score
            parent_total_score += quality_score

        parent_avg_quality = parent_total_score / len(parent_content) if parent_content else 0

        # Process each file for improvements
        improved_content = {}
        improvement_results = {}

        for filename, content in parent_content.items():
            print(f"  📄 Processing {filename}...")

            try:
                # Review and improve content
                review_result = self.content_reviewer.review_text(content)
                improved_content[filename] = review_result["improved_content"]
                improvement_results[filename] = review_result

                improvement = review_result["quality_improvement"]
                print(f"    ✓ Quality: {review_result['original_quality_score']} → {review_result['improved_quality_score']} (+{improvement})")

            except Exception as e:
                print(f"    ❌ Failed to process {filename}: {e}")
                # Use original content as fallback
                improved_content[filename] = content
                improvement_results[filename] = {
                    "original_quality_score": parent_quality_scores[filename],
                    "improved_quality_score": parent_quality_scores[filename],
                    "quality_improvement": 0,
                    "changes_summary": f"Processing failed: {str(e)}"
                }

        # Calculate improved quality scores
        improved_total_score = sum(r["improved_quality_score"] for r in improvement_results.values())
        improved_avg_quality = improved_total_score / len(improvement_results) if improvement_results else 0

        # Create new version
        version_metadata = {
            "description": f"Content improved by ContentEditorAgent",
            "purpose": "content_editing",
            "parent_avg_quality": parent_avg_quality,
            "improved_avg_quality": improved_avg_quality,
            "quality_improvement": improved_avg_quality - parent_avg_quality,
            "files_processed": len(improved_content),
            "processing_timestamp": datetime.now().isoformat()
        }

        version_info = self.version_manager.create_version(
            content_dict=improved_content,
            version_name=target_version,
            agent_name="content_editor",
            parent_version=parent_version,
            metadata=version_metadata
        )

        # Generate change comparison
        comparison_report = self.change_tracker.create_change_report(
            old_version=parent_version,
            new_version=target_version,
            old_content=parent_content,
            new_content=improved_content,
            old_quality=int(parent_avg_quality),
            new_quality=int(improved_avg_quality)
        )

        # Create comprehensive processing report
        processing_results = {
            "version_created": version_info,
            "parent_version": parent_version,
            "target_version": target_version,
            "quality_progression": {
                "parent_avg_quality": parent_avg_quality,
                "improved_avg_quality": improved_avg_quality,
                "overall_improvement": improved_avg_quality - parent_avg_quality
            },
            "file_improvements": improvement_results,
            "change_report_path": comparison_report,
            "processing_timestamp": datetime.now().isoformat()
        }

        # Save processing report
        self.save_processing_report(processing_results, target_version)

        print(f"✅ Version created: {target_version}")
        print(f"   Quality improvement: +{improved_avg_quality - parent_avg_quality:.2f} points")
        print(f"   Change report: {comparison_report}")

        return processing_results

    def save_processing_report(self, results: Dict, version_name: str):
        """Save processing results to quality reports directory."""
        # JSON report
        json_path = self.reports_dir / f"{version_name}_processing_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Markdown report
        md_path = self.reports_dir / f"{version_name}_processing_report.md"
        self.create_processing_markdown(results, md_path)

    def create_processing_markdown(self, results: Dict, output_path: Path):
        """Create human-readable markdown processing report."""
        version_info = results["version_created"]
        quality = results["quality_progression"]
        parent_version = results["parent_version"]
        target_version = results["target_version"]

        content = f"""# Processing Report: {target_version}

**Generated:** {results["processing_timestamp"]}
**Parent Version:** {parent_version}
**Agent:** content_editor

## Quality Improvement Summary

| Metric | Value |
|--------|-------|
| Parent Avg Quality | {quality["parent_avg_quality"]:.1f}/100 |
| Improved Avg Quality | {quality["improved_avg_quality"]:.1f}/100 |
| Overall Improvement | +{quality["overall_improvement"]:.2f} points |
| Files Processed | {len(results["file_improvements"])} |

## File-by-File Results

"""

        for filename, improvement in results["file_improvements"].items():
            original_score = improvement["original_quality_score"]
            improved_score = improvement["improved_quality_score"]
            improvement_points = improvement["quality_improvement"]

            content += f"""### {filename}
- **Quality:** {original_score} → {improved_score} (+{improvement_points} points)
- **Changes:** {improvement.get("changes_summary", "No summary available")}

"""

        content += f"""## Version Information

- **Version Name:** {version_info["name"]}
- **Created:** {version_info["created_at"]}
- **Parent Version:** {version_info["parent_version"]}
- **Content Hash:** {version_info["content_hash"]}
- **Files:** {", ".join(version_info["files"])}

## Change Analysis

Detailed change comparison available at: `{results["change_report_path"]}`
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_version_history(self) -> List[Dict]:
        """Get complete version history with quality progression."""
        versions = self.version_manager.list_versions()

        history = []
        for version in versions:
            # Get quality information from metadata
            metadata = version.get("metadata", {})
            quality_score = metadata.get("improved_avg_quality") or metadata.get("parent_avg_quality")

            history_entry = {
                "version_name": version["name"],
                "agent": version["agent"],
                "created_at": version["created_at"],
                "parent_version": version.get("parent_version"),
                "quality_score": quality_score,
                "file_count": version["file_count"],
                "description": metadata.get("description", "No description")
            }

            history.append(history_entry)

        return history

    def rollback_to_version(self, version_name: str) -> Dict:
        """Rollback to a specific version and update current symlink."""
        print(f"🔄 Rolling back to version: {version_name}")

        # Perform rollback
        version_info = self.version_manager.rollback_to_version(version_name)

        # Log rollback action
        rollback_log = {
            "action": "rollback",
            "target_version": version_name,
            "timestamp": datetime.now().isoformat(),
            "version_info": version_info
        }

        # Save rollback log
        log_path = self.reports_dir / f"rollback_{version_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(rollback_log, f, indent=2, ensure_ascii=False)

        print(f"✅ Rolled back to {version_name}")
        print(f"   Log saved: {log_path}")

        return rollback_log


def main():
    """Run the versioned content editor agent."""
    print("🚀 Starting Versioned Content Editor Agent - Milestone 2")
    print("=" * 60)

    # Initialize agent
    agent = VersionedContentEditorAgent()

    try:
        # Process content with versioning
        results = agent.process_content_with_versioning()

        # Show version history
        print("\n📜 Version History:")
        history = agent.get_version_history()
        for entry in history:
            quality = f" (Q: {entry['quality_score']:.1f})" if entry['quality_score'] else ""
            print(f"  {entry['version_name']}: {entry['description']}{quality}")

        # Show version statistics
        stats = agent.version_manager.get_version_stats()
        print(f"\n📊 Version Statistics:")
        print(f"  Total versions: {stats['total_versions']}")
        print(f"  Agents used: {', '.join(stats['agents_used'])}")
        print(f"  Latest version: {stats['latest_version']}")

        print("\n" + "=" * 60)
        print("✅ MILESTONE 2: Version management complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()