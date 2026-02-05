"""
Pattern Injector - Milestone 3

Injects learned patterns into agent prompts to improve decision-making.
Uses historical learnings to guide LLM behavior without hard-coding fixes.
"""

import json
from pathlib import Path
from typing import Dict


class PatternInjector:
    """
    Inject learned patterns into agent prompts.

    Provides context-aware prompt augmentation based on historical patterns.
    """

    def __init__(self, document_type: str = "research_report"):
        """
        Initialize pattern injector.

        Args:
            document_type: Type of document (e.g., 'research_report', 'article', 'technical_doc')
        """
        self.document_type = document_type
        self.patterns_file = Path(".deepagents") / "memories" / document_type / "learned_patterns.json"
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict:
        """Load learned patterns from file."""
        if not self.patterns_file.exists():
            return {
                "common_latex_fixes": {},
                "quality_improvements": [],
                "recurring_issues": [],
                "agent_performance": {},
                "insights": []
            }

        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load patterns: {e}")
            return {
                "common_latex_fixes": {},
                "quality_improvements": [],
                "recurring_issues": [],
                "agent_performance": {},
                "insights": []
            }

    def get_context_for_latex_specialist(self) -> str:
        """
        Generate prompt context for LaTeX Specialist agent.

        Returns:
            Formatted context string with historical learnings
        """
        if not self.patterns:
            return ""

        context_parts = []

        # Add common fixes
        if self.patterns.get("common_latex_fixes"):
            context_parts.append("## Historical Patterns - Common LaTeX Issues\n")
            context_parts.append("Based on analysis of previous documents, the following issues appear frequently:\n")

            # Sort by frequency
            fixes = sorted(
                self.patterns["common_latex_fixes"].items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )

            for fix, data in fixes[:10]:  # Top 10
                context_parts.append(f"- **{fix}** (seen {data['count']}x)")

            context_parts.append("\n💡 Consider checking for these issues proactively.\n")

        # Add recurring recommendations
        if self.patterns.get("recurring_issues"):
            context_parts.append("\n## Recurring Recommendations\n")
            context_parts.append("These suggestions have been made across multiple documents:\n")

            for issue in self.patterns["recurring_issues"][:5]:  # Top 5
                context_parts.append(f"- {issue}")

            context_parts.append("\n💡 Pay special attention to these areas.\n")

        # Add quality baseline
        if self.patterns.get("quality_improvements"):
            scores = [imp["score"] for imp in self.patterns["quality_improvements"]]
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)

                context_parts.append("\n## Quality Baseline\n")
                context_parts.append(f"- Average historical quality score: {avg_score:.1f}/100\n")
                context_parts.append(f"- Best score achieved: {max_score}/100\n")
                context_parts.append(f"- Target for this document: {min(max_score + 5, 100)}/100\n")

        return "\n".join(context_parts)

    def get_context_for_content_editor(self) -> str:
        """
        Generate prompt context for Content Editor agent.

        Returns:
            Formatted context string with historical learnings
        """
        if not self.patterns:
            return ""

        context_parts = []

        # Add recurring content issues (if we track them in the future)
        if self.patterns.get("recurring_issues"):
            # Filter for content-related issues
            content_issues = [
                issue for issue in self.patterns["recurring_issues"]
                if any(keyword in issue.lower() for keyword in ["readability", "grammar", "style", "clarity"])
            ]

            if content_issues:
                context_parts.append("## Historical Patterns - Content Issues\n")
                context_parts.append("Based on previous content reviews:\n")

                for issue in content_issues[:5]:
                    context_parts.append(f"- {issue}")

                context_parts.append("\n💡 Focus on these areas during review.\n")

        # Add quality expectations
        if self.patterns.get("quality_improvements"):
            scores = [imp["score"] for imp in self.patterns["quality_improvements"]]
            if scores:
                avg_score = sum(scores) / len(scores)
                context_parts.append("\n## Quality Expectations\n")
                context_parts.append(f"Previous documents achieved an average quality of {avg_score:.1f}/100.\n")
                context_parts.append("Aim for content that will support or exceed this quality level.\n")

        return "\n".join(context_parts)

    def get_context_for_visual_qa(self) -> str:
        """
        Generate prompt context for Visual QA agent.

        Returns:
            Formatted context string with historical learnings
        """
        if not self.patterns:
            return ""

        context_parts = []

        # Add visual-specific recurring issues
        if self.patterns.get("recurring_issues"):
            visual_issues = [
                issue for issue in self.patterns["recurring_issues"]
                if any(keyword in issue.lower() for keyword in ["typography", "spacing", "layout", "formatting"])
            ]

            if visual_issues:
                context_parts.append("## Historical Patterns - Visual Issues\n")
                context_parts.append("These visual/formatting issues have been identified before:\n")

                for issue in visual_issues[:5]:
                    context_parts.append(f"- {issue}")

                context_parts.append("\n💡 Check carefully for these in the PDF analysis.\n")

        return "\n".join(context_parts)

    def get_context_for_author(self) -> str:
        """
        Generate prompt context for Author/Research agent.

        Returns:
            Formatted context string with historical learnings
        """
        if not self.patterns:
            return ""

        context_parts = []

        # Add general quality insights
        if self.patterns.get("insights"):
            context_parts.append("## Document Generation Insights\n")

            for insight in self.patterns["insights"][:3]:
                context_parts.append(f"**{insight['title']}:**")
                context_parts.append(f"{insight['description']}")
                context_parts.append(f"💡 {insight['recommendation']}\n")

        return "\n".join(context_parts)

    def get_agent_memory_context(self, agent_name: str) -> str:
        """
        Read .deepagents/{agent_name}/memories/*.md files and return concatenated context.

        This makes the init_memory files written by each agent actually useful
        by feeding their contents into the agent's LLM prompts.

        Args:
            agent_name: Agent directory name (e.g., 'content_editor', 'latex_specialist')

        Returns:
            Concatenated markdown content from all memory files, or empty string.
        """
        memory_dir = Path(".deepagents") / agent_name / "memories"
        if not memory_dir.exists():
            return ""

        context_parts = []
        for md_file in sorted(memory_dir.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8").strip()
                if content:
                    context_parts.append(content)
            except Exception:
                continue

        return "\n\n".join(context_parts)

    def get_summary(self) -> str:
        """
        Get a brief summary of available patterns.

        Returns:
            Summary string
        """
        if not self.patterns or not self.patterns_file.exists():
            return f"No learned patterns available yet for document type: {self.document_type}"

        metadata = self.patterns.get("metadata", {})
        num_fixes = len(self.patterns.get("common_latex_fixes", {}))
        num_issues = len(self.patterns.get("recurring_issues", []))
        num_insights = len(self.patterns.get("insights", []))

        return (
            f"Learned patterns for '{self.document_type}' from {metadata.get('documents_analyzed', 0)} documents:\n"
            f"  - {num_fixes} common LaTeX fixes\n"
            f"  - {num_issues} recurring recommendations\n"
            f"  - {num_insights} actionable insights"
        )


def demo():
    """Demonstrate pattern injection."""
    print("\n" + "=" * 60)
    print("🧠 Pattern Injector - Demonstration")
    print("=" * 60)

    injector = PatternInjector()

    print("\n" + injector.get_summary())

    print("\n" + "=" * 60)
    print("📝 Context for LaTeX Specialist:")
    print("=" * 60)
    print(injector.get_context_for_latex_specialist())

    print("\n" + "=" * 60)
    print("👁️ Context for Visual QA:")
    print("=" * 60)
    print(injector.get_context_for_visual_qa())

    print("\n" + "=" * 60)
    print("✅ Pattern injection ready!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
