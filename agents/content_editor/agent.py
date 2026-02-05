"""
Content Editor Agent - Milestone 1

A specialized agent for improving grammar, readability, and overall content quality.
Part of the DeepAgents PrintShop quality assurance system.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.content_editor.content_reviewer import ContentReviewer


class ContentEditorAgent:
    """
    Content Editor Agent with memory for improving research content quality.

    This agent focuses on:
    1. Grammar and spelling corrections
    2. Readability improvements
    3. Sentence structure optimization
    4. Content flow and coherence
    """

    def __init__(self, memory_dir: str = ".deepagents/content_editor/memories", document_type: str = "research_report"):
        """
        Initialize the content editor agent.

        Args:
            memory_dir: Directory for storing agent memories
            document_type: Type of document for pattern learning
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.document_type = document_type
        self.content_reviewer = ContentReviewer(document_type=document_type)

        # Paths
        self.input_dir = Path("artifacts/sample_content")
        self.output_dir = Path("artifacts/reviewed_content/v1_content_edited")
        self.reports_dir = Path("artifacts/agent_reports/quality")

        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize memory
        self.init_memory()

    def init_memory(self):
        """Initialize agent memory files."""
        memory_files = {
            "grammar_rules.md": """# Grammar and Style Rules

## Common Grammar Issues to Fix
- Subject-verb agreement errors
- Comma splices and run-on sentences
- Misplaced modifiers
- Inconsistent tense usage
- Passive voice overuse

## Style Guidelines
- Use active voice when possible
- Vary sentence length for readability
- Avoid redundant phrases
- Use precise, technical vocabulary
- Maintain consistent terminology throughout

## Academic Writing Standards
- Third person perspective for research
- Present tense for established facts
- Past tense for specific studies conducted
- Clear, concise sentences (15-20 words average)
- Logical paragraph structure with topic sentences
""",
            "readability_patterns.md": """# Readability Improvement Patterns

## Sentence Structure
- Break long sentences (>25 words) into shorter ones
- Use transitional phrases between ideas
- Vary sentence beginnings to avoid monotony
- Replace complex constructions with simpler alternatives

## Word Choice
- Replace vague terms with specific ones
- Eliminate unnecessary jargon
- Use strong verbs instead of weak verb + adverb combinations
- Choose concrete nouns over abstract ones when possible

## Flow and Coherence
- Ensure each paragraph has a clear main idea
- Use connecting words and phrases
- Maintain logical progression of ideas
- Eliminate redundant information
""",
            "quality_metrics.md": """# Content Quality Metrics

## Grammar Score (0-100)
- 0-20 errors: 90-100 points
- 21-40 errors: 70-89 points
- 41-60 errors: 50-69 points
- 60+ errors: 0-49 points

## Readability Score (0-100)
- Based on Flesch Reading Ease
- 90-100: Very Easy (Graduate level appropriate: 30-50)
- 60-70: Standard (Target for academic writing)
- 30-50: Difficult (Acceptable for technical content)
- 0-30: Very Difficult (May need simplification)

## Content Quality Indicators
- Average sentence length: 15-20 words
- Passive voice usage: <20%
- Paragraph length: 3-5 sentences
- Transition word usage: Present in 60%+ of sentences
"""
        }

        for filename, content in memory_files.items():
            file_path = self.memory_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def load_content(self, filename: str) -> str:
        """Load content from the sample_content directory."""
        file_path = self.input_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def save_content(self, filename: str, content: str):
        """Save reviewed content to the output directory."""
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def review_content(self, content: str) -> Dict:
        """
        Review and improve content quality.

        Args:
            content: Original content text

        Returns:
            Dict with improved content and quality metrics
        """
        return self.content_reviewer.review_text(content)

    def process_all_content(self) -> Dict:
        """
        Process all content files in the sample_content directory.

        Returns:
            Dict with processing results and overall quality improvements
        """
        print(f"📄 Document Type: {self.document_type}")
        print(f"🧠 Pattern Learning: {'Enabled' if self.content_reviewer.pattern_injector else 'Disabled'}")
        print()

        results = {
            "files_processed": [],
            "overall_quality_improvement": 0,
            "total_issues_fixed": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Process each markdown file
        for file_path in self.input_dir.glob("*.md"):
            print(f"Processing {file_path.name}...")

            # Load original content
            original_content = self.load_content(file_path.name)

            # Review and improve content
            review_result = self.review_content(original_content)

            # Save improved content
            self.save_content(file_path.name, review_result["improved_content"])

            # Track results
            file_result = {
                "filename": file_path.name,
                "original_quality_score": review_result["original_quality_score"],
                "improved_quality_score": review_result["improved_quality_score"],
                "quality_improvement": review_result["quality_improvement"],
                "issues_fixed": len(review_result["changes_made"]),
                "changes_summary": review_result["changes_summary"]
            }

            results["files_processed"].append(file_result)
            results["total_issues_fixed"] += file_result["issues_fixed"]

        # Calculate overall improvement
        if results["files_processed"]:
            avg_improvement = sum(f["quality_improvement"] for f in results["files_processed"]) / len(results["files_processed"])
            results["overall_quality_improvement"] = round(avg_improvement, 2)

        # Save processing report
        self.save_report(results)

        return results

    def save_report(self, results: Dict):
        """Save the content review report."""
        report_path = self.reports_dir / "content_review_report.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        # Also create a human-readable markdown report
        md_report_path = self.reports_dir / "content_review_report.md"
        self.create_markdown_report(results, md_report_path)

    def create_markdown_report(self, results: Dict, output_path: Path):
        """Create a human-readable markdown report."""
        report_content = f"""# Content Review Report

**Generated:** {results['timestamp']}

## Summary
- **Files Processed:** {len(results['files_processed'])}
- **Overall Quality Improvement:** +{results['overall_quality_improvement']} points
- **Total Issues Fixed:** {results['total_issues_fixed']}

## File-by-File Results

"""

        for file_result in results["files_processed"]:
            report_content += f"""### {file_result['filename']}
- **Original Quality Score:** {file_result['original_quality_score']}/100
- **Improved Quality Score:** {file_result['improved_quality_score']}/100
- **Quality Improvement:** +{file_result['quality_improvement']} points
- **Issues Fixed:** {file_result['issues_fixed']}

**Changes Summary:** {file_result['changes_summary']}

---

"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)


def main():
    """Run the content editor agent."""
    print("Starting Content Editor Agent - Milestone 1")
    print("=" * 50)

    # Initialize agent
    agent = ContentEditorAgent()

    # Process all content
    results = agent.process_all_content()

    # Display summary
    print("\n" + "=" * 50)
    print("CONTENT REVIEW COMPLETE")
    print("=" * 50)
    print(f"Files processed: {len(results['files_processed'])}")
    print(f"Overall quality improvement: +{results['overall_quality_improvement']} points")
    print(f"Total issues fixed: {results['total_issues_fixed']}")
    print("\nReviewed content saved to: artifacts/reviewed_content/v1_content_edited/")
    print("Quality report saved to: artifacts/agent_reports/quality/")


if __name__ == "__main__":
    main()
