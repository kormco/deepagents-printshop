"""Dynamic Visual QA Agent that processes findings and applies improvements."""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.visual_qa import VisualQAAgent, DocumentVisualQA
from tools.latex_generator import LaTeXGenerator, DocumentConfig
from tools.pdf_compiler import PDFCompiler


@dataclass
class ImprovementAction:
    """Represents a specific improvement action to take."""
    issue_type: str
    description: str
    latex_fix: str
    priority: int  # 1-10, higher is more important


class VisualQAFeedbackAgent:
    """Agent that processes Visual QA results and applies dynamic improvements."""

    def __init__(self):
        self.visual_qa = VisualQAAgent()
        self.pdf_compiler = PDFCompiler()
        self.improvement_patterns = self._load_improvement_patterns()

    def _load_improvement_patterns(self) -> Dict[str, Dict]:
        """Load patterns for mapping Visual QA issues to LaTeX improvements."""
        return {
            "line_spacing": {
                "keywords": ["line spacing", "linespacing", "spacing between lines"],
                "latex_fixes": [
                    "\\linespread{0.9}",
                    "\\linespread{1.1}",
                    "\\setlength{\\baselineskip}{1.2\\baselineskip}"
                ]
            },
            "paragraph_spacing": {
                "keywords": ["paragraph spacing", "parskip", "spacing between paragraphs"],
                "latex_fixes": [
                    "\\setlength{\\parskip}{0.5em plus 0.1em minus 0.05em}",
                    "\\setlength{\\parskip}{1em plus 0.2em minus 0.1em}",
                    "\\setlength{\\parskip}{1.2em plus 0.3em minus 0.1em}"
                ]
            },
            "section_spacing": {
                "keywords": ["section spacing", "uneven spacing", "spacing between sections"],
                "latex_fixes": [
                    "\\titlespacing\\section{0pt}{1.5em plus 0.2em minus 0.1em}{0.8em plus 0.1em minus 0.05em}",
                    "\\titlespacing\\subsection{0pt}{1.2em plus 0.15em minus 0.08em}{0.6em plus 0.08em minus 0.04em}"
                ]
            },
            "typography": {
                "keywords": ["font size", "typography", "readability", "text flow"],
                "latex_fixes": [
                    "\\usepackage[11pt]{extsizes}",
                    "\\usepackage{microtype}",
                    "\\setlength{\\textwidth}{0.9\\textwidth}"
                ]
            },
            "table_formatting": {
                "keywords": ["table", "tabular", "formatting", "alignment"],
                "latex_fixes": [
                    "\\renewcommand{\\arraystretch}{1.2}",
                    "\\setlength{\\tabcolsep}{6pt}",
                    "\\usepackage{longtabu}"
                ]
            },
            "header_footer": {
                "keywords": ["header", "footer", "page numbers", "headheight"],
                "latex_fixes": [
                    "\\setlength{\\headheight}{14.5pt}",
                    "\\addtolength{\\topmargin}{-2.5pt}"
                ]
            }
        }

    def analyze_and_improve(self, pdf_path: str, max_iterations: int = 3) -> Tuple[str, List[str]]:
        """
        Analyze PDF with Visual QA and iteratively improve it.

        Returns:
            Final PDF path and list of improvements made
        """
        current_pdf = pdf_path
        improvements_made = []

        for iteration in range(max_iterations):
            print(f"\n🔄 Visual QA Iteration {iteration + 1}/{max_iterations}")
            print("=" * 50)

            # Run Visual QA analysis
            qa_results = self.visual_qa.validate_pdf_visual_quality(current_pdf)

            print(f"📊 Current Score: {qa_results.overall_score:.1f}/100")

            # Stop if score is good enough
            if qa_results.overall_score >= 90:
                print("✅ Quality target achieved!")
                break

            # Extract improvement actions from QA results
            actions = self._extract_improvement_actions(qa_results)

            if not actions:
                print("ℹ️ No more actionable improvements found")
                break

            print(f"🔧 Found {len(actions)} potential improvements:")
            for action in actions:
                print(f"  - {action.description} (Priority: {action.priority})")

            # Apply improvements
            tex_path = pdf_path.replace('.pdf', '.tex')
            improved_tex = self._apply_improvements(tex_path, actions)

            # Recompile PDF
            new_pdf_path = f"artifacts/output/research_report_v{iteration + 2}.pdf"
            if self._compile_improved_tex(improved_tex, new_pdf_path):
                current_pdf = new_pdf_path
                improvements_made.extend([action.description for action in actions])
                print(f"✅ Generated improved version: {new_pdf_path}")
            else:
                print("❌ Compilation failed, reverting changes")
                break

        return current_pdf, improvements_made

    def _extract_improvement_actions(self, qa_results: DocumentVisualQA) -> List[ImprovementAction]:
        """Extract actionable improvements from Visual QA results."""
        actions = []

        # Analyze all page issues
        all_issues = []
        for page_result in qa_results.page_results:
            all_issues.extend(page_result.issues_found)

        # Map issues to improvement actions using AI analysis
        for issue in all_issues:
            action = self._map_issue_to_action(issue, qa_results.overall_score)
            if action:
                actions.append(action)

        # Sort by priority
        actions.sort(key=lambda x: x.priority, reverse=True)

        return actions[:3]  # Limit to top 3 actions per iteration

    def _map_issue_to_action(self, issue: str, current_score: float) -> Optional[ImprovementAction]:
        """Map a specific issue to an improvement action."""
        issue_lower = issue.lower()

        # Priority based on current score (lower score = higher priority fixes)
        base_priority = max(1, 10 - int(current_score / 10))

        for pattern_name, pattern_info in self.improvement_patterns.items():
            for keyword in pattern_info["keywords"]:
                if keyword in issue_lower:
                    # Select appropriate fix based on issue context
                    latex_fix = self._select_best_fix(issue, pattern_info["latex_fixes"])

                    return ImprovementAction(
                        issue_type=pattern_name,
                        description=f"Fix {pattern_name}: {issue}",
                        latex_fix=latex_fix,
                        priority=base_priority + self._calculate_issue_priority(issue)
                    )

        return None

    def _select_best_fix(self, issue: str, available_fixes: List[str]) -> str:
        """Select the most appropriate fix for the specific issue."""
        issue_lower = issue.lower()

        # Simple heuristics for fix selection
        if "reduce" in issue_lower or "decrease" in issue_lower:
            return available_fixes[0]  # Usually the "smaller" option
        elif "increase" in issue_lower or "improve" in issue_lower:
            return available_fixes[-1]  # Usually the "larger" option
        else:
            return available_fixes[len(available_fixes) // 2]  # Middle option

    def _calculate_issue_priority(self, issue: str) -> int:
        """Calculate additional priority based on issue severity."""
        issue_lower = issue.lower()

        # High priority keywords
        if any(word in issue_lower for word in ["unreadable", "poor", "bad", "error"]):
            return 3
        elif any(word in issue_lower for word in ["improve", "enhance", "better"]):
            return 2
        elif any(word in issue_lower for word in ["slightly", "minor", "small"]):
            return 1
        else:
            return 2

    def _apply_improvements(self, tex_path: str, actions: List[ImprovementAction]) -> str:
        """Apply improvement actions to LaTeX document."""
        # Read current LaTeX content
        with open(tex_path, 'r') as f:
            content = f.read()

        # Apply each improvement
        for action in actions:
            content = self._apply_latex_fix(content, action)

        # Write improved version
        improved_path = tex_path.replace('.tex', '_improved.tex')
        with open(improved_path, 'w') as f:
            f.write(content)

        return improved_path

    def _apply_latex_fix(self, content: str, action: ImprovementAction) -> str:
        """Apply a specific LaTeX fix to the content."""
        # Insert fix in preamble before \begin{document}
        begin_doc_pos = content.find('\\begin{document}')
        if begin_doc_pos == -1:
            return content

        # Add improvement comment and fix
        improvement_block = f"""
% Visual QA Improvement: {action.description}
{action.latex_fix}

"""

        # Insert before \begin{document}
        improved_content = (
            content[:begin_doc_pos] +
            improvement_block +
            content[begin_doc_pos:]
        )

        return improved_content

    def _compile_improved_tex(self, tex_path: str, output_pdf: str) -> bool:
        """Compile improved LaTeX to PDF."""
        try:
            success, message = self.pdf_compiler.compile(tex_path)
            if success:
                # Move generated PDF to desired location
                generated_pdf = tex_path.replace('.tex', '.pdf')
                if os.path.exists(generated_pdf) and generated_pdf != output_pdf:
                    os.rename(generated_pdf, output_pdf)
                return True
            else:
                print(f"❌ Compilation failed: {message}")
                return False
        except Exception as e:
            print(f"❌ Compilation error: {e}")
            return False


def main():
    """Test the dynamic Visual QA feedback system."""
    if len(os.sys.argv) != 2:
        print("Usage: python visual_qa_agent.py <pdf_path>")
        return

    pdf_path = os.sys.argv[1]
    agent = VisualQAFeedbackAgent()

    print("🎯 Starting Dynamic Visual QA Improvement Process")
    print("=" * 60)

    final_pdf, improvements = agent.analyze_and_improve(pdf_path)

    print(f"\n🎉 Process Complete!")
    print(f"📄 Final PDF: {final_pdf}")
    print(f"🔧 Improvements Made: {len(improvements)}")
    for i, improvement in enumerate(improvements, 1):
        print(f"   {i}. {improvement}")


if __name__ == "__main__":
    main()