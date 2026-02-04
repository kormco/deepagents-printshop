"""Dynamic Visual QA Agent that processes findings and applies improvements."""

import os
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.visual_qa import VisualQAAgent, DocumentVisualQA
from tools.latex_generator import LaTeXGenerator, DocumentConfig
from tools.llm_latex_generator import LLMLaTeXGenerator
from tools.pdf_compiler import PDFCompiler
from tools.version_manager import VersionManager
from tools.change_tracker import ChangeTracker

try:
    from tools.pattern_injector import PatternInjector
except ImportError:
    PatternInjector = None


@dataclass
class ImprovementAction:
    """Represents a specific improvement action to take."""
    issue_type: str
    description: str
    latex_fix: str
    priority: int  # 1-10, higher is more important


class VisualQAFeedbackAgent:
    """Agent that processes Visual QA results and applies dynamic improvements."""

    def __init__(self, content_source: str = ""):
        self.content_source = content_source
        self.visual_qa = VisualQAAgent(content_source=content_source)
        self.pdf_compiler = PDFCompiler()
        self.llm_latex_generator = LLMLaTeXGenerator()
        self.version_manager = VersionManager()
        self.change_tracker = ChangeTracker()

        # Initialize pattern injector before loading improvement patterns
        self.pattern_injector = None
        self.learned_visual_context = ""
        if PatternInjector and content_source:
            try:
                self.pattern_injector = PatternInjector(document_type=content_source)
                self.learned_visual_context = self.pattern_injector.get_context_for_visual_qa()
            except Exception as e:
                print(f"⚠️  Could not load pattern injector: {e}")

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

    def analyze_and_improve(self, pdf_path: str, max_iterations: int = 3) -> Tuple[str, List[str], Optional[str]]:
        """
        Analyze PDF with Visual QA and iteratively improve it.

        Returns:
            Tuple of (final_pdf_path, improvements_made, final_version_name)
        """
        current_pdf = pdf_path
        improvements_made = []
        final_version = None

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

            # Track version before compilation
            version_name = f"v3_visual_qa_iter{iteration + 1}"
            parent_version = "v2_latex_optimized" if iteration == 0 else f"v3_visual_qa_iter{iteration}"

            # Read old and new LaTeX content for version tracking
            with open(tex_path, 'r', encoding='utf-8') as f:
                old_latex_content = f.read()
            with open(improved_tex, 'r', encoding='utf-8') as f:
                new_latex_content = f.read()

            # Recompile PDF to iterations folder
            iterations_dir = Path("artifacts/reviewed_content/v3_visual_qa/iterations")
            iterations_dir.mkdir(parents=True, exist_ok=True)
            new_pdf_path = str(iterations_dir / f"iteration_{iteration + 1}.pdf")

            if self._compile_improved_tex(improved_tex, new_pdf_path):
                # Save version to reviewed_content
                version_dir = Path(f"artifacts/reviewed_content/{version_name}")
                version_dir.mkdir(parents=True, exist_ok=True)

                # Save improved .tex file to version directory
                tex_filename = f"{self.content_source}.tex" if self.content_source else "research_report.tex"
                pdf_filename = f"{self.content_source}.pdf" if self.content_source else "research_report.pdf"
                version_tex_path = version_dir / tex_filename
                with open(version_tex_path, 'w', encoding='utf-8') as f:
                    f.write(new_latex_content)

                # Copy PDF to version directory
                version_pdf_path = version_dir / pdf_filename
                shutil.copy(new_pdf_path, version_pdf_path)

                # Track version in version manager
                content_dict = {tex_filename: new_latex_content}
                self.version_manager.create_version(
                    content_dict=content_dict,
                    version_name=version_name,
                    agent_name="visual_qa_feedback",
                    parent_version=parent_version,
                    metadata={
                        "iteration": iteration + 1,
                        "improvements": [action.description for action in actions],
                        "qa_score": qa_results.overall_score
                    }
                )

                # Track changes in version history
                old_content_dict = {tex_filename: old_latex_content}
                new_content_dict = {tex_filename: new_latex_content}
                self.change_tracker.create_change_report(
                    old_version=parent_version,
                    new_version=version_name,
                    old_content=old_content_dict,
                    new_content=new_content_dict
                )

                print(f"✅ Version {version_name} tracked in version_history")
                print(f"✅ Generated improved PDF: {new_pdf_path}")

                # Update current PDF for next iteration
                current_pdf = new_pdf_path
                improvements_made.extend([action.description for action in actions])
                final_version = version_name  # Track the final version created
            else:
                print("❌ Compilation failed, reverting changes")
                break

        return current_pdf, improvements_made, final_version

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
        """Apply improvement actions to LaTeX document using LLM reasoning."""
        # Read current LaTeX content
        with open(tex_path, 'r') as f:
            content = f.read()

        # Extract issue descriptions from actions
        issues = [action.description for action in actions]

        # Merge learned visual context into the issues list so the LLM sees it
        if self.learned_visual_context:
            issues = issues + [f"[Historical pattern] {self.learned_visual_context}"]

        # Use LLM-based LaTeX generator to apply fixes intelligently
        print(f"🤖 Using LLM to apply {len(issues)} improvements...")
        fixed_latex, success, fixes_applied = self.llm_latex_generator.apply_visual_qa_fixes(
            content, issues
        )

        if not success:
            print("⚠️ LLM fixes failed, falling back to manual approach")
            # Fallback to simple approach
            for action in actions:
                fixed_latex = self._apply_latex_fix_simple(fixed_latex, action)

        # Write improved version
        improved_path = tex_path.replace('.tex', '_improved.tex')
        with open(improved_path, 'w', encoding='utf-8') as f:
            f.write(fixed_latex)

        return improved_path

    def _apply_latex_fix_simple(self, content: str, action: ImprovementAction) -> str:
        """Apply a specific LaTeX fix to the content (simple fallback method)."""
        # This is the old simple method, kept as fallback
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

    def _compile_improved_tex(self, tex_path: str, output_pdf: str, max_corrections: int = 3) -> bool:
        """
        Compile improved LaTeX to PDF with LLM self-correction on errors.

        If compilation fails, uses LLM to analyze the error and fix it,
        then tries again. Repeats up to max_corrections times.
        """
        try:
            # First compilation attempt
            success, message = self.pdf_compiler.compile(tex_path)
            if success:
                # Move generated PDF to desired location
                generated_pdf = tex_path.replace('.tex', '.pdf')
                if os.path.exists(generated_pdf) and generated_pdf != output_pdf:
                    # Remove existing file first (Windows compatibility)
                    if os.path.exists(output_pdf):
                        os.remove(output_pdf)
                    shutil.move(generated_pdf, output_pdf)
                return True

            # Compilation failed - enter self-correction loop
            print(f"⚠️ Initial compilation failed. Starting LLM self-correction...")

            # Read the failed LaTeX
            with open(tex_path, 'r', encoding='utf-8') as f:
                failed_latex = f.read()

            # Use LLM to self-correct based on compilation error
            corrected_latex, correction_success, corrections = \
                self.llm_latex_generator.self_correct_compilation_errors(
                    failed_latex, message, max_attempts=max_corrections
                )

            if not correction_success:
                print(f"❌ LLM self-correction failed after {max_corrections} attempts")
                return False

            # Write the corrected LaTeX
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(corrected_latex)

            # Try compiling the corrected version
            print("🔄 Compiling LLM-corrected LaTeX...")
            success, message = self.pdf_compiler.compile(tex_path)

            if success:
                generated_pdf = tex_path.replace('.tex', '.pdf')
                if os.path.exists(generated_pdf) and generated_pdf != output_pdf:
                    # Remove existing file first (Windows compatibility)
                    if os.path.exists(output_pdf):
                        os.remove(output_pdf)
                    shutil.move(generated_pdf, output_pdf)
                print(f"✅ LLM self-correction successful! PDF generated.")
                return True
            else:
                print(f"❌ Compilation still failed after LLM correction: {message}")
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

    final_pdf, improvements, final_version = agent.analyze_and_improve(pdf_path)

    print(f"\n🎉 Process Complete!")
    print(f"📄 Final PDF: {final_pdf}")
    if final_version:
        print(f"📦 Final Version: {final_version}")
    print(f"🔧 Improvements Made: {len(improvements)}")
    for i, improvement in enumerate(improvements, 1):
        print(f"   {i}. {improvement}")


if __name__ == "__main__":
    main()