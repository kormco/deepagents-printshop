"""
Research Report Generator using LaTeX.

This module demonstrates the LaTeX report generation capabilities
for the DeepAgents PrintShop research agent.
"""

import os
import sys
from pathlib import Path
from typing import Dict

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.latex_generator import (
    LaTeXGenerator, DocumentConfig, markdown_to_latex
)
from tools.pdf_compiler import PDFCompiler
from tools.content_type_loader import ContentTypeLoader


class ResearchReportGenerator:
    """Generate comprehensive LaTeX research reports."""

    def __init__(self, output_dir: str = "artifacts/output"):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = Path("artifacts")
        self.content_dir = self.artifacts_dir / "sample_content"
        self.data_dir = self.content_dir / "data"
        self.images_dir = self.content_dir / "images"

    def load_markdown_content(self, filename: str) -> str:
        """Load markdown content from the sample_content directory."""
        file_path = self.content_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def load_config_from_markdown(self) -> Dict:
        """Load document configuration from config.md file.

        Uses ContentTypeLoader to resolve the content type and extract
        document class, font size, and paper size from the type definition.
        Parses remaining config sections (metadata, manifest, options) from config.md.
        """
        config_md = self.load_markdown_content("config.md")
        config = {}

        if not config_md:
            return config

        lines = config_md.split('\n')
        current_section = None
        content_lines = []

        for line in lines:
            if line.startswith('## '):
                if current_section and content_lines:
                    config[current_section] = self._parse_config_section_simple(current_section, content_lines)
                current_section = line.replace('## ', '').strip().lower()
                content_lines = []
            elif line.strip() and not line.startswith('#'):
                content_lines.append(line)

        if current_section and content_lines:
            config[current_section] = self._parse_config_section_simple(current_section, content_lines)

        # Load content type definition
        type_id = config.get('content type', 'research_report')
        if isinstance(type_id, str):
            type_id = type_id.strip()

        loader = ContentTypeLoader()
        content_type = loader.load_type(type_id)

        # Inject type defaults into config
        config['document class'] = content_type.document_class
        config['_content_type'] = content_type
        config['_type_font_size'] = content_type.default_font_size
        config['_type_paper_size'] = content_type.default_paper_size

        # Parse project metadata into top-level fields
        project_meta = config.get('project metadata', '')
        if isinstance(project_meta, str):
            for line in project_meta.split('\n'):
                line = line.strip()
                if line.startswith('- ') and ':' in line:
                    key, value = line[2:].split(':', 1)
                    key = key.strip().strip('*').lower()
                    value = value.strip()
                    if key == 'title':
                        config['title'] = value
                    elif key == 'authors':
                        config['authors'] = [a.strip() for a in value.split(',')]

        return config

    def _parse_config_section_simple(self, section_name: str, content_lines: list):
        """Parse configuration sections from config.md."""
        if section_name in ['document options', 'headers and footers']:
            result = {}
            for line in content_lines:
                if line.startswith('- ') and ':' in line:
                    key_value = line[2:].split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        if value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        result[key] = value
            return result
        elif section_name == 'content manifest':
            structure = []
            for line in content_lines:
                if line.strip() and line[0].isdigit():
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        section_def = parts[1].strip()
                        if ':' in section_def:
                            title, source = section_def.split(':', 1)
                            structure.append({
                                'title': title.strip(),
                                'source': source.strip(),
                                'type': 'markdown' if source.strip().endswith('.md') else 'auto'
                            })
                        else:
                            structure.append({
                                'title': section_def,
                                'source': None,
                                'type': 'auto'
                            })
            return structure
        else:
            content = '\n'.join(content_lines).strip()
            return content

    def _process_markdown_with_csv(self, markdown_content: str) -> str:
        """Process markdown content with CSV table support using LaTeX optimizer."""
        from agents.latex_specialist.latex_optimizer import LaTeXOptimizer

        optimizer = LaTeXOptimizer()
        # Use the LaTeX optimizer's enhanced markdown processing
        return optimizer._markdown_to_latex_content(markdown_content)

    def generate_document_from_structure(self, gen, structure: list, config_data: dict):
        """Generate document sections based on configurable structure."""
        section_config = config_data.get('section configuration', {})
        main_level = int(section_config.get('main_section_level', 1))
        sub_level = int(section_config.get('subsection_level', 2))

        for section in structure:
            title = section['title']
            source = section.get('source')
            section_type = section.get('type', 'auto')

            if title.lower() == 'abstract':
                # Handle abstract specially
                abstract_content = config_data.get('abstract', 'Abstract content not found.')
                gen.add_section("Abstract", abstract_content.strip(), level=main_level)

            elif section_type == 'markdown' and source:
                # Load and process markdown file
                markdown_content = self.load_markdown_content(source)
                if markdown_content:
                    if source in ['performance_table.md', 'research_areas.md', 'detailed_results.md']:
                        # Files that should be processed as raw markdown with CSV support
                        processed_content = self._process_markdown_with_csv(markdown_content)
                        gen.add_raw_latex(processed_content)
                    else:
                        # Files that should be processed with section headers
                        self.process_markdown_with_sections(gen, markdown_content, title, main_level, sub_level)
                else:
                    gen.add_section(title, f"Content not found: {source}", level=main_level)

            elif section_type == 'auto':
                # Auto-generated sections (like Visualizations)
                if title.lower() == 'visualizations':
                    self.generate_visualizations_section(gen, main_level)
                else:
                    gen.add_section(title, "Auto-generated content placeholder", level=main_level)

    def process_markdown_with_sections(self, gen, markdown: str, main_title: str, main_level: int, sub_level: int):
        """Process markdown content with section handling."""
        lines = markdown.split('\n')
        current_section = []
        section_title = None

        # Add main section
        gen.add_section(main_title, "", level=main_level)

        for line in lines:
            if line.startswith('# '):
                # Skip main title (already added)
                continue
            elif line.startswith('## '):
                # Save previous subsection if exists
                if section_title and current_section:
                    content = '\n'.join(current_section).strip()
                    gen.add_section(section_title, content, level=sub_level)
                # Start new subsection
                section_title = line.replace('## ', '').strip()
                current_section = []
            elif line.startswith('### '):
                # Save previous subsection if exists
                if section_title and current_section:
                    content = '\n'.join(current_section).strip()
                    gen.add_section(section_title, content, level=sub_level)
                # Start new subsection
                section_title = line.replace('### ', '').strip()
                current_section = []
            else:
                current_section.append(line)

        # Add last subsection
        if section_title and current_section:
            content = '\n'.join(current_section).strip()
            gen.add_section(section_title, content, level=sub_level)

    def generate_visualizations_section(self, gen, level: int):
        """Generate the visualizations section."""
        gen.add_section("Visualizations", "", level=level)

        tikz_code = """
  % Simple neural network diagram
  \\node[circle, draw, minimum size=1cm] (input) at (0,0) {Input};
  \\node[circle, draw, minimum size=1cm] (hidden1) at (3,1) {H1};
  \\node[circle, draw, minimum size=1cm] (hidden2) at (3,-1) {H2};
  \\node[circle, draw, minimum size=1cm] (output) at (6,0) {Output};

  \\draw[->] (input) -- (hidden1);
  \\draw[->] (input) -- (hidden2);
  \\draw[->] (hidden1) -- (output);
  \\draw[->] (hidden2) -- (output);
        """
        gen.add_raw_latex(f"""
\\begin{{figure}}[htbp]
\\centering
\\begin{{tikzpicture}}
{tikz_code}
\\end{{tikzpicture}}
\\caption{{Neural Network Architecture}}
\\label{{fig:neural_net}}
\\end{{figure}}
""")

        gen.add_raw_latex("""
The neural network architecture is shown in Figure~\\ref{fig:neural_net}.
In a complete report, you would include figures using commands like:

\\begin{verbatim}
\\includegraphics[width=0.8\\textwidth]{artifacts/images/results_graph.jpg}
\\end{verbatim}

For wrapped figures with text flow, use the wrapfig environment.
""")

    def generate_sample_report(self) -> str:
        """
        Generate a comprehensive sample research report demonstrating all features.

        Returns:
            Path to the generated .tex file
        """
        # Load configuration from markdown
        config_data = self.load_config_from_markdown()

        # Get document options and type defaults
        doc_options = config_data.get('document options', {})
        headers_footers = config_data.get('headers and footers', {})
        type_font_size = config_data.get('_type_font_size', '12pt')
        type_paper_size = config_data.get('_type_paper_size', 'letterpaper')

        # Configure the document (type defaults, overridden by config options)
        config = DocumentConfig(
            doc_class=config_data.get('document class', 'article'),
            font_size=doc_options.get('font_size', type_font_size),
            paper_size=doc_options.get('paper_size', type_paper_size),
            title=config_data.get('title', 'Research Report'),
            author=config_data.get('authors', ['Anonymous'])[0] if isinstance(config_data.get('authors'), list) else config_data.get('authors', 'Anonymous'),
            date=r"\today",
            include_toc=doc_options.get('include_toc', True),
            include_bibliography=doc_options.get('include_bibliography', True),
            two_column=doc_options.get('two_column', False),
            header_left=headers_footers.get('header_left', 'Research Report'),
            header_right=headers_footers.get('header_right', r'\today'),
            footer_center=headers_footers.get('footer_center', r'\thepage')
        )

        # Create the generator
        gen = LaTeXGenerator(config)

        # Get document structure from config
        document_structure = config_data.get('content manifest', [])

        if document_structure:
            # Use configurable document structure
            self.generate_document_from_structure(gen, document_structure, config_data)
        else:
            # Fallback to default structure if no config found
            gen.add_section("Abstract", config_data.get('abstract', 'No abstract provided'), level=1)

        # Note: CSV tables are now handled via inline markdown references

        # Add citations in bibliography
        self.add_bibliography_entries(gen)

        # Add CSV-based table
        csv_file = self.data_dir / "model_performance.csv"
        if csv_file.exists():
            gen.add_raw_latex("""

\\subsection{Detailed Performance Metrics}

The complete performance data is presented below:

""")
            # For CSV tables, we'll read and create a table manually
            # since csvsimple might need specific configuration
            import csv
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    headers = rows[0]
                    data_rows = rows[1:]
                    gen.add_table(
                        caption="Complete Model Performance Data",
                        headers=headers,
                        rows=data_rows,
                        label="tab:complete_perf"
                    )

        # Add training metrics table
        csv_file2 = self.data_dir / "training_metrics.csv"
        if csv_file2.exists():
            import csv
            with open(csv_file2, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    headers = rows[0]
                    # Only show first 5 rows to keep table concise
                    data_rows = rows[1:6]
                    gen.add_table(
                        caption="Training Progression (First 5 Epochs)",
                        headers=headers,
                        rows=data_rows,
                        label="tab:training"
                    )

        # Add Results discussion
        results_md = self.load_markdown_content("results.md")
        if results_md:
            # Process results markdown
            results_lines = results_md.split('\n')
            current_section = []
            section_title = None

            for line in results_lines:
                if line.startswith('# '):
                    continue
                elif line.startswith('## '):
                    if section_title and current_section:
                        content = '\n'.join(current_section).strip()
                        gen.add_section(section_title, content, level=2)
                    section_title = line.replace('## ', '').strip()
                    current_section = []
                elif line.startswith('### '):
                    if section_title and current_section:
                        content = '\n'.join(current_section).strip()
                        gen.add_section(section_title, content, level=2)
                    section_title = line.replace('### ', '').strip()
                    current_section = []
                else:
                    current_section.append(line)

            if section_title and current_section:
                content = '\n'.join(current_section).strip()
                gen.add_section(section_title, content, level=2)

        # Add a TikZ diagram (simple graph example)
        gen.add_section("Visualizations", "", level=1)

        tikz_code = """
  % Simple neural network diagram
  \\node[circle, draw, minimum size=1cm] (input) at (0,0) {Input};
  \\node[circle, draw, minimum size=1cm] (hidden1) at (3,1) {H1};
  \\node[circle, draw, minimum size=1cm] (hidden2) at (3,-1) {H2};
  \\node[circle, draw, minimum size=1cm] (output) at (6,0) {Output};

  \\draw[->] (input) -- (hidden1);
  \\draw[->] (input) -- (hidden2);
  \\draw[->] (hidden1) -- (output);
  \\draw[->] (hidden2) -- (output);
"""
        gen.add_tikz_diagram(tikz_code, "Simple Neural Network Architecture", label="fig:nn")

        # Add note about images (since we may not have actual image files)
        gen.add_raw_latex("""

\\subsection{Image Placement Examples}

In a complete report, you would include figures using commands like:

\\begin{verbatim}
\\includegraphics[width=0.8\\textwidth]{artifacts/images/results_graph.jpg}
\\end{verbatim}

For wrapped figures with text flow, use the wrapfig environment.
""")

        # Add citations in bibliography
        gen.add_bib_entry(
            "\\bibitem{vaswani2017attention}\n"
            "Vaswani, A., et al. (2017). "
            "Attention is all you need. "
            "In Advances in neural information processing systems (pp. 5998-6008)."
        )
        gen.add_bib_entry(
            "\\bibitem{devlin2018bert}\n"
            "Devlin, J., et al. (2018). "
            "BERT: Pre-training of deep bidirectional transformers for language understanding. "
            "arXiv preprint arXiv:1810.04805."
        )
        gen.add_bib_entry(
            "\\bibitem{brown2020gpt3}\n"
            "Brown, T., et al. (2020). "
            "Language models are few-shot learners. "
            "Advances in neural information processing systems, 33, 1877-1901."
        )

        # Add conclusion from markdown
        conclusion_md = self.load_markdown_content("conclusion.md")
        if conclusion_md:
            gen.add_raw_latex(markdown_to_latex(conclusion_md))

        # Save the document
        output_file = self.output_dir / "research_report.tex"
        gen.save(str(output_file))

        return str(output_file)

    # Note: CSV table handling has been moved to inline markdown references
    # Tables are now defined in markdown files with CSV_TABLE comments

    def add_bibliography_entries(self, gen):
        """Add bibliography entries to the document."""
        gen.add_bib_entry(
            "\\bibitem{vaswani2017attention}\n"
            "Vaswani, A., et al. (2017). "
            "Attention is all you need. "
            "In Advances in neural information processing systems (pp. 5998-6008)."
        )
        gen.add_bib_entry(
            "\\bibitem{devlin2018bert}\n"
            "Devlin, J., et al. (2018). "
            "BERT: Pre-training of deep bidirectional transformers for language understanding. "
            "arXiv preprint arXiv:1810.04805."
        )
        gen.add_bib_entry(
            "\\bibitem{brown2020gpt3}\n"
            "Brown, T., et al. (2020). "
            "Language models are few-shot learners. "
            "Advances in neural information processing systems, 33, 1877-1901."
        )

    def compile_to_pdf(self, tex_file: str) -> bool:
        """
        Compile the LaTeX file to PDF.

        Args:
            tex_file: Path to the .tex file

        Returns:
            True if successful, False otherwise
        """
        compiler = PDFCompiler(output_dir=str(self.output_dir))

        # Check LaTeX installation
        is_installed, message = compiler.validate_latex_installation()
        print(f"LaTeX Installation: {message}")

        if not is_installed:
            print("ERROR: LaTeX is not installed. Cannot compile PDF.")
            return False

        # Compile the document (2 runs for references)
        success, message = compiler.compile(tex_file, runs=2)
        print(f"\nCompilation result: {message}")

        return success


def main():
    """Main function to demonstrate report generation."""
    print("=" * 60)
    print("DeepAgents PrintShop - LaTeX Research Report Generator")
    print("=" * 60)
    print()

    generator = ResearchReportGenerator()

    print("Generating LaTeX report...")
    tex_file = generator.generate_sample_report()
    print(f"✓ LaTeX file created: {tex_file}")
    print()

    print("Compiling to PDF...")
    success = generator.compile_to_pdf(tex_file)

    if success:
        print()
        print("=" * 60)
        print("✓ Report generation complete!")
        print(f"  LaTeX file: {tex_file}")
        print(f"  PDF file: {tex_file.replace('.tex', '.pdf')}")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("⚠ LaTeX file created but PDF compilation failed.")
        print(f"  You can manually compile: pdflatex {tex_file}")
        print("=" * 60)


if __name__ == "__main__":
    main()
