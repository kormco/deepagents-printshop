"""
LaTeX Optimizer - Milestone 3

Optimizes LaTeX document structure, typography, and formatting for professional quality.
"""

import re
import os
import csv
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import anthropic

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(project_root))

from tools.latex_generator import LaTeXGenerator, DocumentConfig
from tools.content_type_loader import ContentTypeLoader


class LaTeXOptimizer:
    """
    Optimizes LaTeX documents for professional formatting and structure.

    Features:
    - Document structure optimization
    - Typography enhancement
    - Table and figure formatting improvement
    - LaTeX best practices application
    """

    def __init__(self, content_source: str = "research_report"):
        """Initialize the LaTeX optimizer.

        Args:
            content_source: Content source folder name (e.g., 'research_report', 'magazine')
        """
        self.content_source = content_source
        self.content_dir = Path("artifacts/sample_content") / content_source
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.professional_packages = {
            'typography': [
                '\\usepackage[T1]{fontenc}',
                '\\usepackage[utf8]{inputenc}',
                '\\usepackage{microtype}',
                '\\usepackage{lmodern}'
            ],
            'tables': [
                '\\usepackage{booktabs}',
                '\\usepackage{array}',
                '\\usepackage{longtable}'
            ],
            'figures': [
                '\\usepackage{graphicx}',
                '\\usepackage{float}',
                '\\usepackage{caption}',
                '\\usepackage{subcaption}'
            ],
            'layout': [
                '\\usepackage{geometry}',
                '\\usepackage{fancyhdr}',
                '\\usepackage{titlesec}'
            ],
            'references': [
                '\\usepackage{hyperref}',
                '\\usepackage{cite}',
                '\\usepackage{url}'
            ]
        }

        self.document_templates = {
            'article': {
                'geometry': '\\geometry{margin=1in}',
                'spacing': '\\usepackage{setspace}\\onehalfspacing',
                'sections': ['section', 'subsection', 'subsubsection']
            },
            'report': {
                'geometry': '\\geometry{margin=1in}',
                'spacing': '\\usepackage{setspace}\\onehalfspacing',
                'sections': ['chapter', 'section', 'subsection', 'subsubsection']
            }
        }

    def optimize_document(self,
                         content: str,
                         markdown_content: Dict[str, str],
                         optimization_level: str = 'moderate') -> Dict:
        """
        Optimize LaTeX document comprehensively.

        Args:
            content: Original LaTeX content or markdown content
            markdown_content: Dictionary of markdown files to convert
            optimization_level: 'conservative', 'moderate', 'aggressive'

        Returns:
            Dictionary with optimized content and optimization details
        """
        print(f"🔧 Starting LaTeX optimization (level: {optimization_level})")

        # If we have markdown content, convert to LaTeX first
        if markdown_content:
            latex_content = self._convert_markdown_to_latex(markdown_content)
        else:
            latex_content = content

        # Apply optimizations in order
        optimizations_applied = []

        # 1. Structure optimization
        latex_content, struct_opts = self._optimize_structure(latex_content)
        optimizations_applied.extend(struct_opts)

        # 2. Typography optimization
        latex_content, typo_opts = self._optimize_typography(latex_content, optimization_level)
        optimizations_applied.extend(typo_opts)

        # 3. Table optimization
        latex_content, table_opts = self._optimize_tables(latex_content)
        optimizations_applied.extend(table_opts)

        # 4. Figure optimization
        latex_content, figure_opts = self._optimize_figures(latex_content)
        optimizations_applied.extend(figure_opts)

        # 5. References and citations
        latex_content, ref_opts = self._optimize_references(latex_content)
        optimizations_applied.extend(ref_opts)

        # 6. General cleanup
        latex_content, cleanup_opts = self._apply_general_cleanup(latex_content)
        optimizations_applied.extend(cleanup_opts)

        # 7. Final formatting pass
        latex_content = self._final_formatting_pass(latex_content)

        print(f"✅ Applied {len(optimizations_applied)} optimizations")

        return {
            'optimized_content': latex_content,
            'optimizations_applied': optimizations_applied,
            'optimization_count': len(optimizations_applied),
            'optimization_level': optimization_level,
            'timestamp': datetime.now().isoformat()
        }

    def load_config_from_markdown(self, markdown_content: Dict[str, str]) -> Dict:
        """Load document configuration from config.md in the markdown_content dict.

        Uses ContentTypeLoader to resolve the content type and extract
        document class, font size, and paper size from the type definition.
        Parses remaining config sections (metadata, manifest, options) from config.md.

        Args:
            markdown_content: Dictionary of filename -> content loaded by version manager

        Returns:
            Parsed configuration dictionary
        """
        config_md = markdown_content.get("config.md", "")
        config = {}

        if config_md:
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
        # _parse_config_section_simple already strips '- ' prefixes,
        # so lines arrive as "Key: Value" not "- Key: Value"
        project_meta = config.get('project metadata', '')
        if isinstance(project_meta, str):
            for line in project_meta.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
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
            if all(line.startswith('- ') or not line.strip() for line in content_lines if line.strip()):
                return '\n'.join(line[2:] if line.startswith('- ') else line for line in content_lines).strip()
            return content

    def _generate_visualizations(self, gen: LaTeXGenerator):
        """No-op: visualizations are now content-driven via IMAGE comments."""
        pass

    def _add_images(self, gen: LaTeXGenerator):
        """Add images from the content directory as figures."""
        images_dir = self.content_dir / "images"
        if not images_dir.exists():
            return

        for img_file in sorted(images_dir.iterdir()):
            if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                caption = img_file.stem.replace('_', ' ').replace('-', ' ').title()
                label = f"fig:{img_file.stem}"
                gen.add_figure(str(img_file), caption, label=label)

    def _add_csv_tables(self, gen: LaTeXGenerator):
        """Add CSV data tables from the content directory."""
        data_dir = self.content_dir / "data"
        if not data_dir.exists():
            return

        for csv_file in sorted(data_dir.iterdir()):
            if csv_file.suffix.lower() == '.csv':
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        rows = list(reader)

                    if rows:
                        headers = rows[0]
                        data_rows = rows[1:]
                        caption = csv_file.stem.replace('_', ' ').replace('-', ' ').title()
                        label = f"tab:{csv_file.stem}"
                        gen.add_table(
                            caption=caption,
                            headers=headers,
                            rows=data_rows,
                            label=label,
                        )
                except Exception as e:
                    gen.add_raw_latex(f"% Error loading CSV {csv_file.name}: {e}")

    def _add_bibliography(self, gen: LaTeXGenerator):
        """Add standard bibliography entries."""
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

    def _convert_markdown_to_latex(self, markdown_content: Dict[str, str]) -> str:
        """Convert markdown content to professional LaTeX document using LaTeXGenerator.

        Reads config.md from the markdown_content dict to determine title, authors,
        document structure, and formatting options. Produces a complete LaTeX document
        with proper section ordering, images, TikZ diagrams, CSV tables, and bibliography.
        """
        # Parse config.md from the loaded content
        config_data = self.load_config_from_markdown(markdown_content)

        # Build DocumentConfig from type defaults + config overrides
        doc_options = config_data.get('document options', {})
        headers_footers = config_data.get('headers and footers', {})
        authors_list = config_data.get('authors', [])
        author_str = authors_list[0] if isinstance(authors_list, list) and authors_list else 'Research Team'
        type_font_size = config_data.get('_type_font_size', '12pt')
        type_paper_size = config_data.get('_type_paper_size', 'letterpaper')

        config = DocumentConfig(
            doc_class=config_data.get('document class', 'article'),
            font_size=doc_options.get('font_size', type_font_size),
            paper_size=doc_options.get('paper_size', type_paper_size),
            title=config_data.get('title', 'Research Report'),
            author=author_str,
            date=r"\today",
            include_toc=doc_options.get('include_toc', True),
            include_bibliography=doc_options.get('include_bibliography', True),
            two_column=doc_options.get('two_column', False),
            header_left=headers_footers.get('header_left', ''),
            header_right=headers_footers.get('header_right', r'\today'),
            footer_center=headers_footers.get('footer_center', r'\thepage'),
        )

        gen = LaTeXGenerator(config)

        # Insert disclaimer if present in config (converted via shared markdown path)
        disclaimer_text = config_data.get('disclaimer', '')
        if disclaimer_text:
            disclaimer_latex = self._markdown_to_latex_content(disclaimer_text)
            gen.add_section("Disclaimer", disclaimer_latex.strip(), level=1)

        # Follow document structure ordering from config
        document_structure = config_data.get('content manifest', [])
        main_level = 1
        sub_level = 2

        if document_structure:
            for section in document_structure:
                title = section['title']
                source = section.get('source')
                section_type = section.get('type', 'auto')

                if title.lower() == 'abstract':
                    abstract_content = config_data.get('abstract', 'Abstract content not found.')
                    gen.add_section("Abstract", abstract_content.strip(), level=main_level)

                elif section_type == 'markdown' and source:
                    md_content = markdown_content.get(source, '')
                    if md_content:
                        # Process CSV, image, and TikZ references within the markdown
                        processed = self._process_csv_table_references(md_content, str(self.content_dir))
                        processed = self._process_image_references(processed, str(self.content_dir))
                        processed = self._process_tikz_references(processed)
                        # Strip top-level heading so the LLM doesn't duplicate the \section
                        processed = re.sub(r'^#\s+[^\n]*\n*', '', processed, count=1)
                        # Convert markdown formatting to LaTeX
                        latex_content = self._markdown_to_latex_content(processed)
                        # Add manifest-driven \section, then LLM content as subsections
                        gen.add_section(title, "", level=main_level)
                        gen.add_raw_latex(f"\n% Content from {source}")
                        gen.add_raw_latex(latex_content)
                    else:
                        gen.add_section(title, f"Content not found: {source}", level=main_level)

                elif section_type == 'auto':
                    gen.add_section(title, "Auto-generated content placeholder", level=main_level)
        else:
            # Fallback: iterate markdown files in dict order (original behavior)
            for filename, content in markdown_content.items():
                if filename == 'config.md':
                    continue
                processed = self._process_csv_table_references(content, str(self.content_dir))
                processed = self._process_image_references(processed, str(self.content_dir))
                processed = self._process_tikz_references(processed)
                latex_content = self._markdown_to_latex_content(processed)
                gen.add_raw_latex(f"\n% Content from {filename}")
                gen.add_raw_latex(latex_content)

        # Add bibliography
        self._add_bibliography(gen)

        document = gen.generate_document()

        # Apply rendering instructions (disclaimer + citation) from content type
        content_type = config_data.get('_content_type')
        has_disclaimer = bool(config_data.get('disclaimer', ''))
        if content_type:
            document = self._apply_rendering_instructions(document, content_type, has_disclaimer)

        return document

    def _apply_rendering_instructions(self, document: str, content_type, has_disclaimer: bool) -> str:
        """Apply rendering instructions from the content type definition.

        Parses the '## Rendering Instructions' section of type.md for
        'Cover Page Disclaimer' and 'PrintShop Citation' subsections,
        then generates and inserts the corresponding LaTeX blocks.

        Args:
            document: The complete LaTeX document string
            content_type: ContentTypeDefinition with type_md_content
            has_disclaimer: Whether config.md already provided a disclaimer

        Returns:
            Modified document string with disclaimer and citation inserted
        """
        type_md = content_type.type_md_content
        if not type_md:
            return document

        # Extract the Rendering Instructions section
        rendering_match = re.search(
            r'## Rendering Instructions\s*\n(.*?)(?=\n## |\Z)',
            type_md,
            re.DOTALL
        )
        if not rendering_match:
            return document

        rendering_text = rendering_match.group(1)

        # --- Cover Page Disclaimer ---
        if not has_disclaimer:
            disclaimer_match = re.search(
                r'### Cover Page Disclaimer\s*\n(.*?)(?=\n### |\n## |\Z)',
                rendering_text,
                re.DOTALL
            )
            if disclaimer_match and self.client:
                disclaimer_instruction = disclaimer_match.group(1).strip()
                try:
                    response = self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        temperature=0.2,
                        messages=[{
                            "role": "user",
                            "content": (
                                "Generate ONLY a small LaTeX block (no preamble, no "
                                "\\documentclass, no \\begin{document}) that implements "
                                "the following instruction for a cover page disclaimer. "
                                "Output raw LaTeX only, no code fences.\n\n"
                                f"Instruction: {disclaimer_instruction}"
                            ),
                        }],
                    )
                    disclaimer_latex = response.content[0].text.strip()
                    # Insert after \maketitle
                    document = document.replace(
                        '\\maketitle',
                        '\\maketitle\n\n' + disclaimer_latex,
                        1
                    )
                    print("✅ Inserted cover page disclaimer from rendering instructions")
                except Exception as e:
                    print(f"⚠️ Could not generate disclaimer: {e}")

        # --- PrintShop Citation ---
        citation_match = re.search(
            r'### PrintShop Citation\s*\n(.*?)(?=\n### |\n## |\Z)',
            rendering_text,
            re.DOTALL
        )
        if citation_match and self.client:
            citation_instruction = citation_match.group(1).strip()
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    temperature=0.2,
                    messages=[{
                        "role": "user",
                        "content": (
                            "Generate ONLY a small LaTeX block (no preamble, no "
                            "\\documentclass, no \\begin{document}) that implements "
                            "the following instruction for a production citation at "
                            "the end of a document. Output raw LaTeX only, no code fences.\n\n"
                            f"Instruction: {citation_instruction}"
                        ),
                    }],
                )
                citation_latex = response.content[0].text.strip()
                # Insert after bibliography (before \end{document})
                document = document.replace(
                    '\\end{document}',
                    '\n' + citation_latex + '\n\n\\end{document}',
                    1
                )
                print("✅ Inserted PrintShop citation from rendering instructions")
            except Exception as e:
                print(f"⚠️ Could not generate PrintShop citation: {e}")

        return document

    def _markdown_to_latex_content(self, markdown: str) -> str:
        """Convert markdown content to LaTeX body content using LLM."""
        if not self.client:
            raise RuntimeError("ANTHROPIC_API_KEY not set — cannot convert markdown to LaTeX")

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": (
                        "Convert the following markdown to LaTeX body content. "
                        "Output ONLY raw LaTeX — no preamble, no \\documentclass, "
                        "no \\begin{document}, no \\end{document}, no code fences. "
                        "Use \\subsection as the highest heading level (not \\section). "
                        "Use \\subsubsection for lower-level headings. "
                        "Use booktabs (\\toprule, \\midrule, \\bottomrule) for tables. "
                        "Use itemize/enumerate for lists. "
                        "Use \\textbf, \\textit, \\texttt for emphasis. "
                        "Use \\href for hyperlinks. "
                        "Do NOT generate \\ref{}, \\cite{}, or \\label{} commands "
                        "unless they already appear verbatim in the source.\n\n"
                        f"{markdown}"
                    ),
                }],
            )
            return self._sanitize_unicode_for_latex(response.content[0].text)
        except Exception as e:
            print(f"Error converting markdown to LaTeX via LLM: {e}")
            raise

    def _sanitize_unicode_for_latex(self, text: str) -> str:
        """Replace common Unicode characters with LaTeX equivalents for pdflatex compatibility."""
        replacements = {
            # Superscripts
            '\u2070': '$^{0}$', '\u00b9': '$^{1}$', '\u00b2': '$^{2}$',
            '\u00b3': '$^{3}$', '\u2074': '$^{4}$', '\u2075': '$^{5}$',
            '\u2076': '$^{6}$', '\u2077': '$^{7}$', '\u2078': '$^{8}$',
            '\u2079': '$^{9}$', '\u207a': '$^{+}$', '\u207b': '$^{-}$',
            # Subscripts
            '\u2080': '$_{0}$', '\u2081': '$_{1}$', '\u2082': '$_{2}$',
            '\u2083': '$_{3}$', '\u2084': '$_{4}$', '\u2085': '$_{5}$',
            '\u2086': '$_{6}$', '\u2087': '$_{7}$', '\u2088': '$_{8}$',
            '\u2089': '$_{9}$',
            # Math symbols
            '\u00d7': '$\\times$',    # ×
            '\u00f7': '$\\div$',      # ÷
            '\u2264': '$\\leq$',      # ≤
            '\u2265': '$\\geq$',      # ≥
            '\u2260': '$\\neq$',      # ≠
            '\u2248': '$\\approx$',   # ≈
            '\u221e': '$\\infty$',    # ∞
            '\u00b1': '$\\pm$',       # ±
            '\u2190': '$\\leftarrow$',  # ←
            '\u2192': '$\\rightarrow$', # →
            # Typography
            '\u2013': '--',           # en dash
            '\u2014': '---',          # em dash
            '\u2018': '`',            # left single quote
            '\u2019': "'",            # right single quote
            '\u201c': '``',           # left double quote
            '\u201d': "''",           # right double quote
            '\u2026': '\\ldots{}',    # …
        }
        for char, latex in replacements.items():
            text = text.replace(char, latex)
        return text

    def _process_csv_table_references(self, content: str, content_dir: str = "artifacts/sample_content") -> str:
        """Process CSV table references in markdown content."""
        import re
        from pathlib import Path

        # Pattern to match CSV table comments (including multi-line with flexible spacing)
        csv_pattern = r'<!-- CSV_TABLE:\s*(.*?)\s*-->'

        def replace_csv_table(match):
            metadata_text = match.group(1)
            return self._convert_csv_reference_to_latex(metadata_text, content_dir)

        # Replace all CSV table references (with DOTALL flag for multi-line matching)
        processed_content = re.sub(csv_pattern, replace_csv_table, content, flags=re.DOTALL)
        return processed_content

    def _process_image_references(self, content: str, content_dir: str = "artifacts/sample_content") -> str:
        """Process IMAGE references in markdown content and convert to LaTeX figures."""
        import re
        from pathlib import Path

        # Pattern to match IMAGE comments (multi-line)
        image_pattern = r'<!-- IMAGE:\s*(.*?)\s*-->'

        def replace_image_ref(match):
            metadata_text = match.group(1)
            return self._convert_image_reference_to_latex(metadata_text, content_dir)

        processed_content = re.sub(image_pattern, replace_image_ref, content, flags=re.DOTALL)
        return processed_content

    def _process_tikz_references(self, content: str) -> str:
        """Process TIKZ references in markdown content and convert to LaTeX tikzpicture environments."""
        tikz_pattern = r'<!-- TIKZ:\s*(.*?)\s*-->'

        def replace_tikz_ref(match):
            metadata_text = match.group(1)
            return self._convert_tikz_reference_to_latex(metadata_text)

        return re.sub(tikz_pattern, replace_tikz_ref, content, flags=re.DOTALL)

    def _convert_tikz_reference_to_latex(self, metadata_text: str) -> str:
        """Convert a single TIKZ reference to a LaTeX figure with tikzpicture."""
        lines = metadata_text.strip().split('\n')

        caption = ''
        label = ''
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('code:'):
                in_code = True
                # Check if there's code on the same line after "code:"
                rest = stripped[5:].strip()
                if rest:
                    code_lines.append(rest)
            elif in_code:
                code_lines.append(line.rstrip())
            elif ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'caption':
                    caption = value
                elif key == 'label':
                    label = value

        if not code_lines:
            return '% TIKZ reference missing code'

        tikz_code = '\n'.join(code_lines)

        latex_parts = [
            '\\begin{figure}[htbp]',
            '\\centering',
            '\\begin{tikzpicture}',
            tikz_code,
            '\\end{tikzpicture}',
        ]
        if caption:
            latex_parts.append(f'\\caption{{{caption}}}')
        if label:
            latex_parts.append(f'\\label{{{label}}}')
        latex_parts.append('\\end{figure}')

        return '\n'.join(latex_parts)

    def _convert_image_reference_to_latex(self, metadata_text: str, content_dir: str) -> str:
        """Convert a single IMAGE reference to a LaTeX figure environment."""
        from pathlib import Path

        lines = metadata_text.strip().split('\n')
        if not lines:
            return "% IMAGE reference missing path"

        # First line is the image path
        image_path = lines[0].strip()

        # Parse key-value metadata from remaining lines
        caption = ''
        label = ''
        width = '0.8\\textwidth'
        for line in lines[1:]:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key == 'caption':
                    caption = value
                elif key == 'label':
                    label = value
                elif key == 'width':
                    width = value

        # Resolve image path relative to content directory
        full_path = Path(content_dir) / image_path
        if not full_path.exists():
            return f"% Image not found: {image_path}"

        # Generate LaTeX figure
        latex_parts = [
            '\\begin{figure}[htbp]',
            '\\centering',
            f'\\includegraphics[width={width}]{{{full_path}}}',
        ]
        if caption:
            latex_parts.append(f'\\caption{{{caption}}}')
        if label:
            latex_parts.append(f'\\label{{{label}}}')
        latex_parts.append('\\end{figure}')

        return '\n'.join(latex_parts)

    def _convert_csv_reference_to_latex(self, metadata_text: str, content_dir: str) -> str:
        """Convert a single CSV reference to LaTeX table."""
        from pathlib import Path
        import csv

        # Parse metadata from the comment
        metadata = self._parse_csv_metadata(metadata_text)

        csv_filename = metadata.get('filename')
        if not csv_filename:
            return "% CSV table reference missing filename"

        # Load CSV data
        csv_path = Path(content_dir) / "data" / csv_filename
        if not csv_path.exists():
            return f"% CSV file not found: {csv_filename}"

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                return f"% Empty CSV file: {csv_filename}"

            # Extract headers and data based on metadata
            headers = rows[0]
            data_rows = rows[1:]

            # Apply column filtering
            columns = metadata.get('columns', 'all')
            if columns != 'all':
                try:
                    if isinstance(columns, str):
                        if '-' in columns:
                            # Range like "1-3"
                            start, end = map(int, columns.split('-'))
                            col_indices = list(range(start-1, end))  # Convert to 0-based
                        else:
                            # Single column
                            col_indices = [int(columns)-1]
                    else:
                        # List of columns
                        col_indices = [int(c)-1 for c in columns]

                    headers = [headers[i] for i in col_indices if i < len(headers)]
                    data_rows = [[row[i] if i < len(row) else '' for i in col_indices] for row in data_rows]
                except (ValueError, IndexError):
                    # Fall back to all columns if parsing fails
                    pass

            # Apply row filtering
            rows_spec = metadata.get('rows', 'all')
            if rows_spec != 'all':
                try:
                    if isinstance(rows_spec, str) and '-' in rows_spec:
                        # Range like "1-5"
                        start, end = map(int, rows_spec.split('-'))
                        data_rows = data_rows[start-1:end]  # Convert to 0-based
                    elif isinstance(rows_spec, str):
                        # Single row or number
                        max_rows = int(rows_spec)
                        data_rows = data_rows[:max_rows]
                except (ValueError, IndexError):
                    # Fall back to all rows if parsing fails
                    pass

            # Generate LaTeX table
            return self._generate_csv_latex_table(headers, data_rows, metadata)

        except Exception as e:
            return f"% Error loading CSV {csv_filename}: {str(e)}"

    def _parse_csv_metadata(self, metadata_text: str) -> dict:
        """Parse CSV table metadata from comment text."""
        metadata = {}
        lines = metadata_text.strip().split('\n')

        # First line should be the filename
        if lines:
            metadata['filename'] = lines[0].strip()

        # Parse key-value pairs from remaining lines
        for line in lines[1:]:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                metadata[key] = value

        return metadata

    def _generate_csv_latex_table(self, headers: list, data_rows: list, metadata: dict) -> str:
        """Generate LaTeX table from CSV data and metadata."""
        if not headers:
            return "% No headers found in CSV data"

        num_cols = len(headers)
        col_spec = 'l' * num_cols  # Default to left-aligned columns

        # Get metadata values
        caption = metadata.get('caption', 'CSV Data Table')
        label = metadata.get('label', 'tab:csv_table')
        table_format = metadata.get('format', 'professional')
        description = metadata.get('description', '')

        latex_parts = []

        # Add description if provided
        if description:
            latex_parts.append(f"% {description}")
            latex_parts.append("")

        # Start table
        latex_parts.extend([
            '\\begin{table}[htbp]',
            '\\centering',
            f'\\begin{{tabular}}{{{col_spec}}}'
        ])

        # Add professional formatting if requested
        if table_format == 'professional':
            latex_parts.append('\\toprule')
        else:
            latex_parts.append('\\hline')

        # Add header row
        header_latex = ' & '.join(headers) + ' \\\\'
        latex_parts.append(header_latex)

        # Add separator
        if table_format == 'professional':
            latex_parts.append('\\midrule')
        else:
            latex_parts.append('\\hline')

        # Add data rows
        for row in data_rows:
            # Ensure row has the right number of columns
            while len(row) < num_cols:
                row.append('')
            row = row[:num_cols]  # Truncate if too many columns

            row_latex = ' & '.join(str(cell) for cell in row) + ' \\\\'
            latex_parts.append(row_latex)

        # End table
        if table_format == 'professional':
            latex_parts.append('\\bottomrule')
        else:
            latex_parts.append('\\hline')

        latex_parts.extend([
            '\\end{tabular}',
            f'\\caption{{{caption}}}',
            f'\\label{{{label}}}',
            '\\end{table}'
        ])

        return '\n'.join(latex_parts)

    def _optimize_structure(self, content: str) -> Tuple[str, List[str]]:
        """Optimize document structure and organization."""
        optimizations = []
        optimized = content

        # Ensure proper document class
        if not re.search(r'\\documentclass', optimized):
            optimized = '\\documentclass[12pt,letterpaper]{article}\n\n' + optimized
            optimizations.append('Added professional document class')

        # Ensure title and author if missing
        if not re.search(r'\\title\{', optimized) and not re.search(r'\\maketitle', optimized):
            # Add after document class
            class_match = re.search(r'(\\documentclass.*\n)', optimized)
            if class_match:
                insert_pos = class_match.end()
                title_block = '\n\\title{Research Report}\n\\author{Research Team}\n\\date{\\today}\n'
                optimized = optimized[:insert_pos] + title_block + optimized[insert_pos:]
                optimizations.append('Added title and author information')

        # Add table of contents if document has sections
        if re.search(r'\\(section|chapter)', optimized) and not re.search(r'\\tableofcontents', optimized):
            # Add after \begin{document} and \maketitle
            begin_doc = re.search(r'\\begin\{document\}', optimized)
            if begin_doc:
                # Look for \maketitle or add TOC right after \begin{document}
                maketitle_match = re.search(r'\\maketitle', optimized[begin_doc.end():])
                if maketitle_match:
                    insert_pos = begin_doc.end() + maketitle_match.end()
                    toc_block = '\n\\tableofcontents\n\\newpage\n'
                else:
                    insert_pos = begin_doc.end()
                    toc_block = '\n\\tableofcontents\n\\newpage\n'

                optimized = optimized[:insert_pos] + toc_block + optimized[insert_pos:]
                optimizations.append('Added table of contents')

        # Ensure proper section hierarchy
        optimized, hierarchy_opts = self._fix_section_hierarchy(optimized)
        optimizations.extend(hierarchy_opts)

        return optimized, optimizations

    def _optimize_typography(self, content: str, level: str) -> Tuple[str, List[str]]:
        """Optimize typography and formatting."""
        optimizations = []
        optimized = content

        # Essential typography packages
        essential_packages = [
            ('fontenc', '\\usepackage[T1]{fontenc}'),
            ('inputenc', '\\usepackage[utf8]{inputenc}'),
            ('lmodern', '\\usepackage{lmodern}'),
            ('microtype', '\\usepackage{microtype}'),
        ]

        # Add packages if missing
        for package_name, package_line in essential_packages:
            if not re.search(f'\\\\usepackage.*{{{package_name}}}', optimized):
                # Insert after documentclass
                class_match = re.search(r'(\\documentclass.*\n)', optimized)
                if class_match:
                    insert_pos = class_match.end()
                    optimized = optimized[:insert_pos] + package_line + '\n' + optimized[insert_pos:]
                    optimizations.append(f'Added {package_name} package for better typography')

        # Add geometry for proper margins
        if not re.search(r'\\usepackage.*\{geometry\}', optimized):
            class_match = re.search(r'(\\documentclass.*\n)', optimized)
            if class_match:
                insert_pos = class_match.end()
                geometry_block = '\\usepackage{geometry}\n\\geometry{margin=1in}\n'
                optimized = optimized[:insert_pos] + geometry_block + optimized[insert_pos:]
                optimizations.append('Added geometry package with proper margins')

        # Add spacing improvements
        if level in ['moderate', 'aggressive']:
            if not re.search(r'\\usepackage.*\{setspace\}', optimized):
                class_match = re.search(r'(\\documentclass.*\n)', optimized)
                if class_match:
                    insert_pos = class_match.end()
                    spacing_block = '\\usepackage{setspace}\n\\onehalfspacing\n'
                    optimized = optimized[:insert_pos] + spacing_block + optimized[insert_pos:]
                    optimizations.append('Added improved line spacing')

        # Fix spacing issues
        spacing_fixes = [
            (r'\s{2,}', ' ', 'Fixed multiple consecutive spaces'),
            (r'([.!?])([A-Z])', r'\1 \2', 'Added missing spaces after sentences'),
            (r'\s+([.!?])', r'\1', 'Fixed spaces before punctuation'),
        ]

        for pattern, replacement, description in spacing_fixes:
            if re.search(pattern, optimized):
                optimized = re.sub(pattern, replacement, optimized)
                optimizations.append(description)

        return optimized, optimizations

    def _optimize_tables(self, content: str) -> Tuple[str, List[str]]:
        """Optimize table formatting."""
        optimizations = []
        optimized = content

        # Check if document has tables
        has_tables = re.search(r'\\begin\{tabular\}|\\begin\{table\}', optimized)

        if has_tables:
            # Add booktabs package
            if not re.search(r'\\usepackage.*\{booktabs\}', optimized):
                class_match = re.search(r'(\\documentclass.*\n)', optimized)
                if class_match:
                    insert_pos = class_match.end()
                    optimized = optimized[:insert_pos] + '\\usepackage{booktabs}\n' + optimized[insert_pos:]
                    optimizations.append('Added booktabs package for professional tables')

            # Replace \\hline with booktabs rules
            if re.search(r'\\hline', optimized):
                # This is a simplified replacement - in practice, you'd want more sophisticated logic
                optimized = re.sub(r'\\hline', '\\midrule', optimized)
                optimizations.append('Replaced \\hline with professional booktabs rules')

            # Add array package for better column types
            if not re.search(r'\\usepackage.*\{array\}', optimized):
                class_match = re.search(r'(\\documentclass.*\n)', optimized)
                if class_match:
                    insert_pos = class_match.end()
                    optimized = optimized[:insert_pos] + '\\usepackage{array}\n' + optimized[insert_pos:]
                    optimizations.append('Added array package for better table formatting')

        return optimized, optimizations

    def _optimize_figures(self, content: str) -> Tuple[str, List[str]]:
        """Optimize figure formatting and placement."""
        optimizations = []
        optimized = content

        # Check if document has figures
        has_figures = re.search(r'\\includegraphics|\\begin\{figure\}', optimized)

        if has_figures:
            # Essential figure packages
            figure_packages = [
                ('graphicx', '\\usepackage{graphicx}'),
                ('float', '\\usepackage{float}'),
                ('caption', '\\usepackage{caption}')
            ]

            for package_name, package_line in figure_packages:
                if not re.search(f'\\\\usepackage.*{{{package_name}}}', optimized):
                    class_match = re.search(r'(\\documentclass.*\n)', optimized)
                    if class_match:
                        insert_pos = class_match.end()
                        optimized = optimized[:insert_pos] + package_line + '\n' + optimized[insert_pos:]
                        optimizations.append(f'Added {package_name} package for better figures')

            # Improve figure placement
            figure_placements = re.findall(r'\\begin\{figure\}\[([^\]]*)\]', optimized)
            poor_placements = [p for p in figure_placements if 'h' in p and 't' not in p and 'b' not in p]

            if poor_placements:
                # Replace poor placements with better options
                optimized = re.sub(r'\\begin\{figure\}\[h\]', '\\begin{figure}[htbp]', optimized)
                optimizations.append('Improved figure placement options')

        return optimized, optimizations

    def _optimize_references(self, content: str) -> Tuple[str, List[str]]:
        """Optimize references and citations."""
        optimizations = []
        optimized = content

        # Add hyperref for better navigation (should be last)
        if not re.search(r'\\usepackage.*\{hyperref\}', optimized):
            # Add before \begin{document}
            begin_doc = re.search(r'\\begin\{document\}', optimized)
            if begin_doc:
                insert_pos = begin_doc.start()
                hyperref_block = '\\usepackage{hyperref}\n\\hypersetup{\n    colorlinks=true,\n    linkcolor=blue,\n    citecolor=red,\n    urlcolor=blue\n}\n\n'
                optimized = optimized[:insert_pos] + hyperref_block + optimized[insert_pos:]
                optimizations.append('Added hyperref package for better navigation')

        return optimized, optimizations

    def _apply_general_cleanup(self, content: str) -> Tuple[str, List[str]]:
        """Apply general cleanup and improvements."""
        optimizations = []
        optimized = content

        # Remove excessive blank lines
        original_lines = len(optimized.split('\n'))
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        new_lines = len(optimized.split('\n'))

        if new_lines < original_lines:
            optimizations.append(f'Cleaned up excessive blank lines ({original_lines - new_lines} lines removed)')

        # Fix common LaTeX spacing issues
        common_fixes = [
            (r'\\section\s*\{', r'\\section{', 'Fixed section command spacing'),
            (r'\\subsection\s*\{', r'\\subsection{', 'Fixed subsection command spacing'),
            (r'\\textbf\s*\{', r'\\textbf{', 'Fixed textbf command spacing'),
            (r'\\textit\s*\{', r'\\textit{', 'Fixed textit command spacing'),
        ]

        for pattern, replacement, description in common_fixes:
            if re.search(pattern, optimized):
                optimized = re.sub(pattern, replacement, optimized)
                optimizations.append(description)

        return optimized, optimizations

    def _fix_section_hierarchy(self, content: str) -> Tuple[str, List[str]]:
        """Fix section hierarchy issues."""
        optimizations = []
        # This would contain logic to fix section nesting issues
        # For now, return as-is
        return content, optimizations

    def _final_formatting_pass(self, content: str) -> str:
        """Apply final formatting improvements."""
        # Ensure proper spacing around environments
        content = re.sub(r'(\\begin\{[^}]+\})\n{0,1}', r'\1\n', content)
        content = re.sub(r'\n{0,1}(\\end\{[^}]+\})', r'\n\1', content)

        # Ensure proper spacing around sections
        content = re.sub(r'(\\(?:sub)*section\{[^}]+\})\n{0,1}', r'\1\n\n', content)

        # Clean up final whitespace
        content = content.strip()

        return content

    def calculate_optimization_score(self, before_issues: int, after_issues: int, optimizations_count: int) -> int:
        """Calculate optimization effectiveness score."""
        issues_fixed = max(0, before_issues - after_issues)

        # Base score from issues fixed
        score = min(50, issues_fixed * 5)

        # Bonus for optimizations applied
        score += min(30, optimizations_count * 2)

        # Bonus for significant improvement
        if issues_fixed > before_issues * 0.5:  # Fixed more than 50% of issues
            score += 20

        return min(100, score)