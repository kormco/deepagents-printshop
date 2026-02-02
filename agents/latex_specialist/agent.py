"""
LaTeX Specialist Agent - Milestone 3

Specialized agent for optimizing LaTeX formatting, typography, and document structure.
Integrates with version management system to create v2_latex_optimized versions.
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

from agents.latex_specialist.latex_analyzer import LaTeXAnalyzer, LaTeXAnalysisResult
from agents.latex_specialist.latex_optimizer import LaTeXOptimizer
from tools.version_manager import VersionManager
from tools.change_tracker import ChangeTracker


class LaTeXSpecialistAgent:
    """
    LaTeX Specialist Agent with version management and quality optimization.

    Features:
    - LaTeX document analysis and optimization
    - Professional typography and formatting
    - Version management integration
    - Quality progression tracking
    """

    def __init__(self, memory_dir: str = ".deepagents/latex_specialist/memories",
                 content_source: str = "research_report"):
        """
        Initialize the LaTeX specialist agent.

        Args:
            memory_dir: Directory for storing agent memories
            content_source: Content source folder (e.g., 'research_report', 'magazine')
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.content_source = content_source

        # Initialize components
        self.latex_analyzer = LaTeXAnalyzer()
        self.latex_optimizer = LaTeXOptimizer(content_source=content_source)
        self.version_manager = VersionManager()
        self.change_tracker = ChangeTracker()

        # Paths
        self.reports_dir = Path("artifacts/agent_reports/quality")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.output_filename = content_source  # e.g., 'magazine' or 'research_report'

        # Initialize memory
        self.init_memory()

    def init_memory(self):
        """Initialize agent memory files."""
        memory_files = {
            "latex_best_practices.md": """# LaTeX Best Practices and Standards

## Document Structure
- Use appropriate document class (article, report, book)
- Maintain consistent section hierarchy
- Include title, author, and date
- Add table of contents for longer documents

## Typography Excellence
- Use T1 font encoding for better output
- Enable microtype for improved typography
- Set appropriate line spacing (1.5 for academic)
- Maintain consistent font usage throughout

## Professional Packages
- booktabs: Professional table formatting
- geometry: Proper page margins and layout
- hyperref: Navigation and cross-references
- graphicx + float: Figure management
- caption: Professional figure captions

## Table Formatting
- Use booktabs package for professional tables
- Replace \\hline with \\toprule, \\midrule, \\bottomrule
- Align numbers in columns appropriately
- Use clear, descriptive table captions

## Figure Management
- Use [htbp] placement options
- Include descriptive captions
- Ensure proper figure sizing
- Reference all figures in text
""",
            "typography_rules.md": """# Typography and Formatting Rules

## Font and Encoding
- Always use T1 font encoding: \\usepackage[T1]{fontenc}
- UTF-8 input encoding: \\usepackage[utf8]{inputenc}
- Modern fonts: \\usepackage{lmodern}
- Microtypography: \\usepackage{microtype}

## Spacing Guidelines
- Line spacing: 1.5 for academic papers (\\onehalfspacing)
- Paragraph indentation: Default LaTeX (no manual spacing)
- Section spacing: Let LaTeX handle automatically
- Margin settings: 1 inch margins for most documents

## Text Formatting
- Bold: \\textbf{text} (not \\bf)
- Italic: \\textit{text} (not \\it)
- Typewriter: \\texttt{text} (not \\tt)
- Avoid nested emphasis commands

## Document Flow
- Use proper sectioning commands
- Include page breaks where appropriate
- Maintain consistent formatting throughout
- Use proper cross-referencing with \\ref{}
""",
            "table_figure_standards.md": """# Table and Figure Formatting Standards

## Professional Tables with Booktabs
```latex
\\usepackage{booktabs}
\\begin{table}[htbp]
\\centering
\\caption{Descriptive table caption}
\\label{tab:example}
\\begin{tabular}{lcc}
\\toprule
Column 1 & Column 2 & Column 3 \\\\
\\midrule
Data 1 & Data 2 & Data 3 \\\\
Data 4 & Data 5 & Data 6 \\\\
\\bottomrule
\\end{tabular}
\\end{table}
```

## Figure Best Practices
```latex
\\usepackage{graphicx}
\\usepackage{float}
\\begin{figure}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{figure.png}
\\caption{Clear, descriptive figure caption}
\\label{fig:example}
\\end{figure}
```

## Caption Guidelines
- Tables: Caption above the table
- Figures: Caption below the figure
- Use descriptive, self-contained captions
- Reference all tables and figures in text
- Use consistent numbering and labeling
""",
            "optimization_patterns.md": """# LaTeX Optimization Patterns

## Common Issues and Fixes
1. **Poor Typography**
   - Issue: Missing font encoding packages
   - Fix: Add fontenc, inputenc, microtype packages

2. **Unprofessional Tables**
   - Issue: Using \\hline for table rules
   - Fix: Replace with booktabs package rules

3. **Poor Figure Placement**
   - Issue: Using only [h] placement
   - Fix: Use [htbp] for better flexibility

4. **Inconsistent Spacing**
   - Issue: Manual spacing commands
   - Fix: Use proper LaTeX spacing mechanisms

## Quality Improvement Strategies
- Analyze document structure first
- Fix typography issues early
- Optimize tables and figures
- Apply consistent formatting
- Validate compilation success

## Optimization Levels
- Conservative: Essential fixes only
- Moderate: Professional improvements
- Aggressive: Maximum optimization with style changes
"""
        }

        for filename, content in memory_files.items():
            file_path = self.memory_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def analyze_latex_quality(self, content: str) -> LaTeXAnalysisResult:
        """
        Analyze LaTeX content quality.

        Args:
            content: LaTeX content to analyze

        Returns:
            Detailed analysis results
        """
        print("🔍 Analyzing LaTeX quality...")
        return self.latex_analyzer.analyze_document(content)

    def optimize_latex_content(self,
                              content: str,
                              markdown_content: Optional[Dict[str, str]] = None,
                              optimization_level: str = 'moderate') -> Dict:
        """
        Optimize LaTeX content for professional quality.

        Args:
            content: Original LaTeX content (if any)
            markdown_content: Markdown content to convert and optimize
            optimization_level: Level of optimization to apply

        Returns:
            Optimization results
        """
        print(f"🔧 Optimizing LaTeX content (level: {optimization_level})")

        if markdown_content:
            print(f"📄 Converting {len(markdown_content)} markdown files to LaTeX")

        return self.latex_optimizer.optimize_document(
            content=content,
            markdown_content=markdown_content,
            optimization_level=optimization_level
        )

    def process_with_versioning(self,
                               parent_version: str = "v1_content_edited",
                               target_version: str = "v2_latex_optimized",
                               optimization_level: str = 'moderate') -> Dict:
        """
        Process content with full LaTeX optimization and version management.

        Args:
            parent_version: Source version to optimize from
            target_version: Target version name for optimized content
            optimization_level: Level of optimization to apply

        Returns:
            Processing results with version information
        """
        print(f"🚀 LaTeX Specialist Processing: {parent_version} → {target_version}")
        print("=" * 60)

        # Load parent version content
        try:
            parent_content_dict = self.version_manager.get_version_content(parent_version)
            print(f"✅ Loaded {parent_version} with {len(parent_content_dict)} files")
        except Exception as e:
            print(f"❌ Failed to load {parent_version}: {e}")
            raise

        # Analyze parent version LaTeX quality (if it's already LaTeX)
        parent_latex_content = ""
        parent_quality_scores = {}

        # Convert markdown content to LaTeX and optimize
        print("\n🔄 Converting and optimizing content...")
        optimization_result = self.optimize_latex_content(
            content=parent_latex_content,
            markdown_content=parent_content_dict,
            optimization_level=optimization_level
        )

        optimized_latex = optimization_result['optimized_content']
        optimizations_applied = optimization_result['optimizations_applied']

        print(f"✅ Applied {len(optimizations_applied)} optimizations")

        # Analyze optimized LaTeX quality
        print("\n📊 Analyzing optimized LaTeX quality...")
        latex_analysis = self.analyze_latex_quality(optimized_latex)

        print(f"📈 LaTeX Quality Scores:")
        print(f"  • Structure: {latex_analysis.structure_score}/25")
        print(f"  • Typography: {latex_analysis.typography_score}/25")
        print(f"  • Tables/Figures: {latex_analysis.tables_figures_score}/25")
        print(f"  • Best Practices: {latex_analysis.best_practices_score}/25")
        print(f"  • Overall: {latex_analysis.overall_score}/100")

        # Create LaTeX file for the version
        latex_content_dict = {
            f"{self.output_filename}.tex": optimized_latex
        }

        # Create version metadata
        version_metadata = {
            "description": f"LaTeX formatting and typography optimized",
            "purpose": "latex_optimization",
            "optimization_level": optimization_level,
            "latex_quality_score": latex_analysis.overall_score,
            "optimizations_applied": len(optimizations_applied),
            "structure_score": latex_analysis.structure_score,
            "typography_score": latex_analysis.typography_score,
            "tables_figures_score": latex_analysis.tables_figures_score,
            "best_practices_score": latex_analysis.best_practices_score,
            "processing_timestamp": datetime.now().isoformat()
        }

        # Create new version
        print(f"\n📦 Creating version: {target_version}")
        version_info = self.version_manager.create_version(
            content_dict=latex_content_dict,
            version_name=target_version,
            agent_name="latex_specialist",
            parent_version=parent_version,
            metadata=version_metadata
        )

        # Generate change comparison (markdown to LaTeX)
        print(f"\n📊 Generating change analysis...")
        change_report = self.change_tracker.create_change_report(
            old_version=parent_version,
            new_version=target_version,
            old_content=parent_content_dict,
            new_content=latex_content_dict,
            old_quality=None,  # Would need to calculate markdown quality
            new_quality=latex_analysis.overall_score
        )

        # Create comprehensive processing report
        processing_results = {
            "version_created": version_info,
            "parent_version": parent_version,
            "target_version": target_version,
            "optimization_results": optimization_result,
            "latex_analysis": {
                "overall_score": latex_analysis.overall_score,
                "structure_score": latex_analysis.structure_score,
                "typography_score": latex_analysis.typography_score,
                "tables_figures_score": latex_analysis.tables_figures_score,
                "best_practices_score": latex_analysis.best_practices_score,
                "issues_found": len(latex_analysis.issues),
                "suggestions": latex_analysis.suggestions
            },
            "optimizations_applied": optimizations_applied,
            "change_report_path": change_report,
            "processing_timestamp": datetime.now().isoformat()
        }

        # Save processing report
        self.save_processing_report(processing_results, target_version)

        print(f"\n✅ LaTeX optimization complete!")
        print(f"   Version created: {target_version}")
        print(f"   LaTeX quality score: {latex_analysis.overall_score}/100")
        print(f"   Optimizations applied: {len(optimizations_applied)}")
        print(f"   Change report: {change_report}")

        return processing_results

    def save_processing_report(self, results: Dict, version_name: str):
        """Save processing results to quality reports directory."""
        # JSON report
        json_path = self.reports_dir / f"{version_name}_latex_processing_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        # Markdown report
        md_path = self.reports_dir / f"{version_name}_latex_processing_report.md"
        self.create_processing_markdown(results, md_path)

    def create_processing_markdown(self, results: Dict, output_path: Path):
        """Create human-readable markdown processing report."""
        version_info = results["version_created"]
        latex_analysis = results["latex_analysis"]
        optimizations = results["optimizations_applied"]
        parent_version = results["parent_version"]
        target_version = results["target_version"]

        content = f"""# LaTeX Processing Report: {target_version}

**Generated:** {results["processing_timestamp"]}
**Parent Version:** {parent_version}
**Agent:** latex_specialist
**Optimization Level:** {results["optimization_results"]["optimization_level"]}

## LaTeX Quality Analysis

| Metric | Score | Max |
|--------|-------|-----|
| Document Structure | {latex_analysis["structure_score"]} | 25 |
| Typography | {latex_analysis["typography_score"]} | 25 |
| Tables & Figures | {latex_analysis["tables_figures_score"]} | 25 |
| Best Practices | {latex_analysis["best_practices_score"]} | 25 |
| **Overall Score** | **{latex_analysis["overall_score"]}** | **100** |

## Optimizations Applied ({len(optimizations)} total)

"""

        for i, optimization in enumerate(optimizations, 1):
            content += f"{i}. {optimization}\n"

        content += f"""

## Quality Improvements

- **Issues Found:** {latex_analysis["issues_found"]} LaTeX issues detected
- **Optimizations Applied:** {len(optimizations)} improvements made
- **Final Quality Score:** {latex_analysis["overall_score"]}/100

## Recommendations

"""

        for suggestion in latex_analysis["suggestions"]:
            content += f"- {suggestion}\n"

        content += f"""

## Version Information

- **Version Name:** {version_info["name"]}
- **Created:** {version_info["created_at"]}
- **Parent Version:** {version_info["parent_version"]}
- **Content Hash:** {version_info["content_hash"]}
- **Files:** {", ".join(version_info["files"])}

## Change Analysis

Detailed change comparison available at: `{results["change_report_path"]}`

## LaTeX Output

The optimized LaTeX document includes:
- Professional document structure
- Enhanced typography with proper packages
- Optimized table and figure formatting
- Best practices implementation
- Publication-ready formatting
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def validate_latex_compilation(self, latex_content: str) -> Dict:
        """
        Validate that LaTeX content can be compiled (mock implementation).

        Args:
            latex_content: LaTeX content to validate

        Returns:
            Validation results
        """
        # This would use pdflatex in a real implementation
        # For now, we'll do basic syntax checking

        validation_result = {
            "compilation_successful": True,
            "warnings": [],
            "errors": [],
            "pdf_generated": True  # Mock
        }

        # Basic syntax checks
        if not re.search(r'\\begin\{document\}', latex_content):
            validation_result["errors"].append("Missing \\begin{document}")
            validation_result["compilation_successful"] = False

        if not re.search(r'\\end\{document\}', latex_content):
            validation_result["errors"].append("Missing \\end{document}")
            validation_result["compilation_successful"] = False

        # Check for unmatched braces (simplified)
        open_braces = latex_content.count('{')
        close_braces = latex_content.count('}')
        if open_braces != close_braces:
            validation_result["warnings"].append(f"Unmatched braces: {open_braces} open, {close_braces} close")

        return validation_result


def main():
    """Run the LaTeX specialist agent."""
    print("🚀 Starting LaTeX Specialist Agent - Milestone 3")
    print("=" * 60)

    # Initialize agent
    agent = LaTeXSpecialistAgent()

    try:
        # Process content with versioning
        results = agent.process_with_versioning(
            parent_version="v1_content_edited",
            target_version="v2_latex_optimized",
            optimization_level="moderate"
        )

        # Show version history
        print("\n📜 Updated Version History:")
        history = agent.version_manager.list_versions()
        for entry in history:
            quality = entry.get('metadata', {}).get('latex_quality_score')
            quality_str = f" (LaTeX: {quality})" if quality else ""
            print(f"  {entry['name']}: {entry.get('metadata', {}).get('description', 'No description')}{quality_str}")

        # Show version statistics
        stats = agent.version_manager.get_version_stats()
        print(f"\n📊 Version Statistics:")
        print(f"  Total versions: {stats['total_versions']}")
        print(f"  Agents used: {', '.join(stats['agents_used'])}")
        print(f"  Latest version: {stats['latest_version']}")

        print("\n" + "=" * 60)
        print("✅ MILESTONE 3: LaTeX optimization complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()