"""
Pattern Learner - Milestone 1

Mines version history to extract actionable patterns and insights.
Simple, read-only analysis that generates learned_patterns.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict


class PatternLearner:
    """
    Learn from version history to identify improvement patterns.

    Milestone 1 Features:
    - Extract common LaTeX fixes
    - Track quality improvements
    - Identify recurring issues
    - Generate simple recommendations
    """

    def __init__(self, base_dir: str = "artifacts", document_type: str = "research_report"):
        """
        Initialize pattern learner.

        Args:
            base_dir: Base artifacts directory
            document_type: Type of document (e.g., 'research_report', 'article', 'technical_doc')
        """
        self.base_dir = Path(base_dir)
        self.version_dir = self.base_dir / "version_history"
        self.changes_dir = self.version_dir / "changes"
        self.reports_dir = self.base_dir / "agent_reports" / "quality"
        self.document_type = document_type
        self.output_dir = Path(".deepagents") / "memories" / document_type
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def mine_patterns(self) -> Dict:
        """
        Mine all patterns from version history.

        Returns:
            Dictionary of learned patterns
        """
        print("🔍 Mining version history for patterns...")
        print("=" * 60)

        patterns = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "documents_analyzed": 0,
                "transitions_analyzed": 0
            },
            "common_latex_fixes": {},
            "quality_improvements": [],
            "recurring_issues": [],
            "agent_performance": {},
            "insights": []
        }

        # 1. Load version manifest
        manifest_path = self.version_dir / "version_manifest.json"
        if not manifest_path.exists():
            print("⚠️  No version manifest found - no history to analyze yet")
            return patterns

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        patterns["metadata"]["documents_analyzed"] = len(manifest.get("versions", {}))

        # 2. Analyze each change file
        change_files = list(self.changes_dir.glob("*.json"))
        patterns["metadata"]["transitions_analyzed"] = len(change_files)

        print(f"📊 Found {len(change_files)} version transitions to analyze\n")

        for change_file in change_files:
            self._analyze_change_file(change_file, patterns)

        # 3. Analyze quality reports from agent_reports/quality
        if self.reports_dir.exists():
            quality_reports = list(self.reports_dir.glob("*_latex_processing_report.md"))
            print(f"📑 Found {len(quality_reports)} quality reports to analyze\n")

            for report_file in quality_reports:
                self._analyze_quality_report(report_file, patterns)

        # 4. Generate insights
        self._generate_insights(patterns)

        print("\n✅ Pattern mining complete!")
        return patterns

    def _analyze_change_file(self, change_file: Path, patterns: Dict):
        """Analyze a single change file for patterns."""
        try:
            with open(change_file, 'r') as f:
                change_data = json.load(f)
        except Exception as e:
            print(f"⚠️  Could not read {change_file.name}: {e}")
            return

        # Extract LaTeX optimizations
        if "optimizations_applied" in change_data:
            optimizations = change_data["optimizations_applied"]

            for opt in optimizations:
                if opt not in patterns["common_latex_fixes"]:
                    patterns["common_latex_fixes"][opt] = {
                        "count": 0,
                        "scores_before": [],
                        "scores_after": []
                    }

                patterns["common_latex_fixes"][opt]["count"] += 1

        # Extract quality improvements
        if "latex_analysis" in change_data:
            latex_data = change_data["latex_analysis"]

            # Track score improvements
            if "overall_score" in latex_data:
                parent_version = change_data.get("parent_version", "unknown")
                target_version = change_data.get("target_version", "unknown")

                improvement = {
                    "from_version": parent_version,
                    "to_version": target_version,
                    "score": latex_data["overall_score"],
                    "optimizations_count": change_data.get("optimization_results", {}).get("optimization_count", 0)
                }
                patterns["quality_improvements"].append(improvement)

            # Track recurring issues
            if "suggestions" in latex_data:
                for suggestion in latex_data["suggestions"]:
                    if suggestion not in patterns["recurring_issues"]:
                        patterns["recurring_issues"].append(suggestion)

        # Track agent performance
        agent = change_data.get("version_created", {}).get("agent", "unknown")
        if agent != "unknown":
            if agent not in patterns["agent_performance"]:
                patterns["agent_performance"][agent] = {
                    "versions_created": 0,
                    "avg_quality_score": [],
                    "optimizations_applied": 0
                }

            patterns["agent_performance"][agent]["versions_created"] += 1

            if "latex_analysis" in change_data:
                score = change_data["latex_analysis"].get("overall_score")
                if score:
                    patterns["agent_performance"][agent]["avg_quality_score"].append(score)

    def _analyze_quality_report(self, report_file: Path, patterns: Dict):
        """Analyze a quality report markdown file for patterns."""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Could not read {report_file.name}: {e}")
            return

        import re

        # Extract version name from filename (e.g., v2_latex_optimized_latex_processing_report.md)
        version_match = re.search(r'(v\d+_[^_]+(?:_[^_]+)?)', report_file.name)
        version_name = version_match.group(1) if version_match else "unknown"

        # Extract overall score (e.g., "| **Overall Score** | **89** | **100** |")
        score_match = re.search(r'\*\*Overall Score\*\*.*?\*\*(\d+)\*\*', content)
        if score_match:
            score = int(score_match.group(1))

            # Track quality improvement
            improvement = {
                "version": version_name,
                "score": score,
                "source": "quality_report"
            }
            patterns["quality_improvements"].append(improvement)

        # Extract optimizations applied
        # Pattern: ## Optimizations Applied (5 total)
        #          1. Fixed multiple consecutive spaces
        opt_section_match = re.search(r'## Optimizations Applied \((\d+) total\)\s+((?:\d+\. .+\n?)+)', content)
        if opt_section_match:
            opt_count = int(opt_section_match.group(1))
            opt_text = opt_section_match.group(2)

            # Parse each optimization line
            for line in opt_text.strip().split('\n'):
                line = line.strip()
                if line and re.match(r'^\d+\.', line):
                    # Remove numbering (e.g., "1. Fixed ..." -> "Fixed ...")
                    opt = re.sub(r'^\d+\.\s*', '', line)

                    if opt not in patterns["common_latex_fixes"]:
                        patterns["common_latex_fixes"][opt] = {
                            "count": 0,
                            "versions": []
                        }

                    patterns["common_latex_fixes"][opt]["count"] += 1
                    patterns["common_latex_fixes"][opt]["versions"].append(version_name)

        # Extract recommendations as recurring issues
        # Pattern: ## Recommendations
        #          - Address 3 formatting warnings...
        rec_match = re.search(r'## Recommendations\s+((?:- .+\n?)+)', content)
        if rec_match:
            rec_text = rec_match.group(1)
            for line in rec_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    recommendation = line[2:].strip()  # Remove "- " prefix
                    if recommendation not in patterns["recurring_issues"]:
                        patterns["recurring_issues"].append(recommendation)

        # Extract agent info
        agent_match = re.search(r'\*\*Agent:\*\* (\w+)', content)
        if agent_match and score_match:
            agent = agent_match.group(1)
            score = int(score_match.group(1))

            if agent not in patterns["agent_performance"]:
                patterns["agent_performance"][agent] = {
                    "versions_created": 0,
                    "avg_quality_score": [],
                    "optimizations_applied": 0
                }

            patterns["agent_performance"][agent]["versions_created"] += 1
            patterns["agent_performance"][agent]["avg_quality_score"].append(score)

            if opt_section_match:
                patterns["agent_performance"][agent]["optimizations_applied"] += int(opt_section_match.group(1))

    def _generate_insights(self, patterns: Dict):
        """Generate actionable insights from patterns."""
        insights = []

        # Insight 1: Most common fixes
        if patterns["common_latex_fixes"]:
            sorted_fixes = sorted(
                patterns["common_latex_fixes"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )

            if sorted_fixes:
                top_fix = sorted_fixes[0]
                insights.append({
                    "type": "common_fix",
                    "title": "Most Common LaTeX Fix",
                    "description": f"'{top_fix[0]}' appears in {top_fix[1]['count']} documents",
                    "recommendation": "Consider applying this fix proactively in future documents"
                })

        # Insight 2: Average quality improvement
        if patterns["quality_improvements"]:
            scores = [imp["score"] for imp in patterns["quality_improvements"]]
            avg_score = sum(scores) / len(scores)

            insights.append({
                "type": "quality_baseline",
                "title": "Average LaTeX Quality Score",
                "description": f"Average score across {len(scores)} optimizations: {avg_score:.1f}/100",
                "recommendation": f"Target score of {avg_score + 5:.1f} for above-average quality"
            })

        # Insight 3: Agent effectiveness
        for agent, perf in patterns["agent_performance"].items():
            if perf["avg_quality_score"]:
                avg = sum(perf["avg_quality_score"]) / len(perf["avg_quality_score"])

                insights.append({
                    "type": "agent_performance",
                    "title": f"{agent.replace('_', ' ').title()} Performance",
                    "description": f"Processed {perf['versions_created']} versions with avg quality {avg:.1f}",
                    "recommendation": "Performance is stable" if avg > 85 else "Consider tuning quality thresholds"
                })

        # Insight 4: Recurring issues
        unique_issues = len(patterns["recurring_issues"])
        if unique_issues > 0:
            insights.append({
                "type": "recurring_issues",
                "title": "Recurring Suggestions",
                "description": f"Found {unique_issues} recurring suggestions across documents",
                "recommendation": "Review these suggestions for proactive fixes"
            })

        patterns["insights"] = insights

    def save_patterns(self, patterns: Dict, filename: str = "learned_patterns.json") -> str:
        """
        Save learned patterns to file.

        Args:
            patterns: Pattern dictionary
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Patterns saved to: {output_path}")
        print(f"📁 Document type: {self.document_type}")
        return str(output_path)

    def generate_report(self, patterns: Dict) -> str:
        """
        Generate human-readable pattern report.

        Args:
            patterns: Pattern dictionary

        Returns:
            Path to report file
        """
        report_path = self.output_dir / "pattern_learning_report.md"

        report = f"""# Pattern Learning Report

**Generated:** {patterns['metadata']['generated_at']}

## Overview

- **Documents Analyzed:** {patterns['metadata']['documents_analyzed']}
- **Version Transitions:** {patterns['metadata']['transitions_analyzed']}

## Common LaTeX Fixes

The following fixes appear frequently across documents:

"""

        # Sort fixes by frequency
        sorted_fixes = sorted(
            patterns["common_latex_fixes"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        for fix, data in sorted_fixes:
            versions_str = ""
            if "versions" in data and data["versions"]:
                versions_str = f" (versions: {', '.join(data['versions'])})"
            report += f"- **{fix}** - Applied {data['count']} times{versions_str}\n"

        report += f"\n## Quality Improvements\n\n"
        report += f"Total optimizations tracked: {len(patterns['quality_improvements'])}\n\n"

        if patterns['quality_improvements']:
            scores = [imp["score"] for imp in patterns["quality_improvements"]]
            report += f"- Average LaTeX quality score: {sum(scores)/len(scores):.1f}/100\n"
            report += f"- Highest score achieved: {max(scores)}/100\n"
            report += f"- Lowest score achieved: {min(scores)}/100\n\n"

            # Show version-by-version scores
            report += f"**Score by Version:**\n\n"
            for imp in patterns["quality_improvements"]:
                report += f"- {imp.get('version', 'unknown')}: {imp['score']}/100\n"

        report += f"\n## Agent Performance\n\n"

        for agent, perf in patterns["agent_performance"].items():
            report += f"### {agent.replace('_', ' ').title()}\n\n"
            report += f"- Versions created: {perf['versions_created']}\n"

            if perf['avg_quality_score']:
                avg = sum(perf['avg_quality_score']) / len(perf['avg_quality_score'])
                report += f"- Average quality score: {avg:.1f}/100\n"

            if perf.get('optimizations_applied', 0) > 0:
                report += f"- Total optimizations applied: {perf['optimizations_applied']}\n"

            report += "\n"

        report += f"## Recurring Issues\n\n"

        if patterns["recurring_issues"]:
            for issue in patterns["recurring_issues"]:
                report += f"- {issue}\n"
        else:
            report += "*No recurring issues identified*\n"

        report += f"\n## Key Insights\n\n"

        for insight in patterns["insights"]:
            report += f"### {insight['title']}\n\n"
            report += f"**{insight['description']}**\n\n"
            report += f"💡 *Recommendation:* {insight['recommendation']}\n\n"

        report += f"""
---

*Generated by DeepAgents PrintShop Pattern Learner*
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Report saved to: {report_path}")
        return str(report_path)

    def print_summary(self, patterns: Dict):
        """Print a summary of learned patterns to console."""
        print("\n" + "=" * 60)
        print("📊 PATTERN LEARNING SUMMARY")
        print("=" * 60)

        print(f"\n📈 Analyzed: {patterns['metadata']['documents_analyzed']} documents, "
              f"{patterns['metadata']['transitions_analyzed']} transitions")

        print(f"\n🔧 Common Fixes ({len(patterns['common_latex_fixes'])}):")
        sorted_fixes = sorted(
            patterns["common_latex_fixes"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]  # Top 5

        for fix, data in sorted_fixes:
            print(f"   • {fix}: {data['count']}x")

        print(f"\n💡 Key Insights ({len(patterns['insights'])}):")
        for insight in patterns["insights"][:3]:  # Top 3
            print(f"   • {insight['title']}")
            print(f"     → {insight['recommendation']}")


    def learn_from_pipeline_run(self, pipeline_results: Dict) -> Dict:
        """
        Convenience wrapper: mine patterns, save them, and generate a report.

        Called by the orchestrator after a pipeline run completes.

        Args:
            pipeline_results: Results dict from the pipeline (currently unused,
                              but available for future per-run analysis).

        Returns:
            Dictionary of learned patterns.
        """
        patterns = self.mine_patterns()
        self.save_patterns(patterns)
        self.generate_report(patterns)
        self.print_summary(patterns)
        return patterns


def main():
    """Run pattern learning analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Pattern Learner - mine version history for patterns")
    parser.add_argument(
        "--type", "-t",
        default="research_report",
        help="Document type (e.g., research_report, magazine)"
    )
    args = parser.parse_args()

    document_type = args.type

    print("\n" + "=" * 60)
    print("🧠 DeepAgents PrintShop - Pattern Learner")
    print("=" * 60)
    print("\nMilestone 3: Mining version history for improvement patterns\n")

    # Initialize learner with document type
    learner = PatternLearner(document_type=document_type)
    print(f"📄 Learning patterns for document type: {document_type}\n")

    # Mine patterns
    patterns = learner.mine_patterns()

    # Save results
    learner.save_patterns(patterns)
    learner.generate_report(patterns)

    # Print summary
    learner.print_summary(patterns)

    print("\n" + "=" * 60)
    print("✅ Pattern learning complete!")
    print("=" * 60)
    print("\nNext steps:")
    print(f"  1. Review: .deepagents/memories/{document_type}/pattern_learning_report.md")
    print(f"  2. Check: .deepagents/memories/{document_type}/learned_patterns.json")
    print("  3. Use insights to optimize future document generation")
    print()


if __name__ == "__main__":
    main()
