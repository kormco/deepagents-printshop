"""
DeepAgents PrintShop - Research Agent

A specialized agent for generating LaTeX research reports with persistent memory.
Integrates with DeepAgents CLI framework.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from report_generator import ResearchReportGenerator


class ResearchAgent:
    """
    Research agent with memory for generating LaTeX reports.

    This agent demonstrates how to:
    1. Track research artifacts across sessions
    2. Generate professional LaTeX documents
    3. Compile PDFs with proper formatting
    4. Maintain report structure and styling
    """

    def __init__(self, memory_dir: str = ".deepagents/research_agent/memories"):
        """
        Initialize the research agent.

        Args:
            memory_dir: Directory for storing agent memories
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.report_gen = ResearchReportGenerator()

        # Initialize memory files
        self.init_memory()

    def init_memory(self):
        """Initialize agent memory files."""
        memory_files = {
            "latex_knowledge.md": """# LaTeX Document Generation Knowledge

## Document Classes
- article: For short reports and papers
- report: For longer reports with chapters
- book: For books with complex structure
- beamer: For presentations

## Key Packages
- graphicx: Image handling
- hyperref: Hyperlinks and cross-references
- cite: Citation management
- booktabs: Professional tables
- tikz: Vector graphics

## Best Practices
1. Run pdflatex at least twice for proper cross-references
2. Use \\label{} and \\ref{} for internal references
3. Keep image paths relative to the .tex file
4. Use vector graphics (PDF/EPS) when possible
""",
            "report_structure.md": """# Research Report Structure

## Standard Sections
1. Abstract
2. Introduction
3. Background/Related Work
4. Methodology
5. Results
6. Discussion
7. Conclusion
8. References

## Tables and Figures
- Always include captions
- Use labels for cross-referencing
- Place close to first reference in text
- Number sequentially

## Citations
- Use consistent citation style
- Include all necessary bibliographic information
- Cite primary sources when possible
""",
            "artifacts_tracking.md": """# Research Artifacts Tracking

## Content Types
- Markdown files: Primary content source
- CSV files: Data tables
- Images: JPG/PNG for photos, diagrams
- Vector graphics: EPS/SVG for charts
- LaTeX snippets: Custom formatting

## Artifact Locations
- artifacts/sample_content/: Text content in markdown
- artifacts/data/: CSV data files
- artifacts/images/: Image assets
- artifacts/output/: Generated LaTeX and PDFs

## Conversion Pipeline
1. Load markdown content
2. Convert to LaTeX formatting
3. Add tables from CSV
4. Include images and diagrams
5. Generate bibliography
6. Compile to PDF
"""
        }

        for filename, content in memory_files.items():
            filepath = self.memory_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

    def generate_report(self, report_type: str = "sample"):
        """
        Generate a research report.

        Args:
            report_type: Type of report to generate (currently only 'sample')
        """
        print(f"\n{'='*60}")
        print(f"Generating {report_type} research report...")
        print(f"{'='*60}\n")

        if report_type == "sample":
            tex_file = self.report_gen.generate_sample_report()
            print(f"✓ LaTeX file created: {tex_file}\n")

            # Compile to PDF
            print("Compiling to PDF...")
            success = self.report_gen.compile_to_pdf(tex_file)

            if success:
                pdf_file = tex_file.replace('.tex', '.pdf')
                print(f"\n{'='*60}")
                print("✓ Report generation complete!")
                print(f"{'='*60}")
                print(f"LaTeX: {tex_file}")
                print(f"PDF: {pdf_file}")
                print(f"{'='*60}\n")

                # Update memory with successful generation
                self.log_generation(tex_file, pdf_file)
            else:
                print(f"\n{'='*60}")
                print("⚠ PDF compilation failed")
                print(f"{'='*60}")
                print(f"LaTeX file created: {tex_file}")
                print("You can compile manually with: pdflatex <filename>.tex")
                print(f"{'='*60}\n")
        else:
            print(f"Unknown report type: {report_type}")

    def log_generation(self, tex_file: str, pdf_file: str):
        """Log successful report generation to memory."""
        log_file = self.memory_dir / "generation_log.md"

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = f"""
## Report Generated: {timestamp}
- LaTeX: {tex_file}
- PDF: {pdf_file}
- Status: Success
"""

        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def show_capabilities(self):
        """Display agent capabilities."""
        print(f"\n{'='*60}")
        print("DeepAgents PrintShop - Research Agent Capabilities")
        print(f"{'='*60}\n")

        capabilities = [
            "📄 Generate LaTeX documents with customizable structure",
            "📊 Create tables from CSV data with headers",
            "🖼️  Include images (JPG/PNG) with text wrapping",
            "📈 Generate vector diagrams with TikZ",
            "🔗 Add hyperlinks and cross-references",
            "📚 Manage citations and bibliography",
            "🎨 Customize document class, fonts, and layout",
            "📑 Generate table of contents automatically",
            "✏️  Support for lists, equations, and formatting",
            "📖 Compile to PDF with pdflatex",
            "💾 Track artifacts across sessions with memory",
        ]

        for cap in capabilities:
            print(f"  {cap}")

        print(f"\n{'='*60}\n")

    def interactive_mode(self):
        """Run the agent in interactive mode."""
        self.show_capabilities()

        print("Available commands:")
        print("  1. generate - Generate sample research report")
        print("  2. help - Show capabilities")
        print("  3. exit - Exit the agent")
        print()

        while True:
            try:
                command = input("research-agent> ").strip().lower()

                if command in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                elif command in ['generate', 'gen', '1']:
                    self.generate_report("sample")
                elif command in ['help', 'h', '2']:
                    self.show_capabilities()
                elif command == '':
                    continue
                else:
                    print(f"Unknown command: {command}")
                    print("Try 'help' for available commands")
            except KeyboardInterrupt:
                print("\nInterrupted. Use 'exit' to quit.")
            except EOFError:
                print("\nGoodbye!")
                break


def main():
    """Main entry point for the research agent."""
    agent = ResearchAgent()

    # Check if running with arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "generate":
            agent.generate_report("sample")
        elif command == "help":
            agent.show_capabilities()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: generate, help")
    else:
        # Run in interactive mode
        agent.interactive_mode()


if __name__ == "__main__":
    main()
