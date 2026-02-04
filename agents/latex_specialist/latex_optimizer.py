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
                         optimization_level: str = 'moderate',
                         pattern_context: str = "") -> Dict:
        """
        Optimize LaTeX document comprehensively.

        Args:
            content: Original LaTeX content or markdown content
            markdown_content: Dictionary of markdown files to convert
            optimization_level: 'conservative', 'moderate', 'aggressive'
            pattern_context: Historical pattern context to inject into LLM prompts

        Returns:
            Dictionary with optimized content and optimization details
        """
        print(f"🔧 Starting LaTeX optimization (level: {optimization_level})")
        self._current_pattern_context = pattern_context

        # If we have markdown content, convert to LaTeX first
        has_type_preamble = False
        if markdown_content:
            latex_content = self._convert_markdown_to_latex(markdown_content)
            # Check if the content type provided its own preamble blocks
            config_data = self.load_config_from_markdown(markdown_content)
            content_type = config_data.get('_content_type')
            if content_type and content_type.latex_preamble_blocks:
                has_type_preamble = True
        else:
            latex_content = content

        # Apply optimizations in order
        optimizations_applied = []

        # Skip structure and typography optimization when content type provides its own preamble
        # (these add duplicate packages and rewrite the preamble)
        if not has_type_preamble:
            # 1. Structure optimization
            latex_content, struct_opts = self._optimize_structure(latex_content)
            optimizations_applied.extend(struct_opts)

            # 2. Typography optimization
            latex_content, typo_opts = self._optimize_typography(latex_content, optimization_level)
            optimizations_applied.extend(typo_opts)

            # 5. References and citations
            latex_content, ref_opts = self._optimize_references(latex_content)
            optimizations_applied.extend(ref_opts)

        # 3. Table optimization
        latex_content, table_opts = self._optimize_tables(latex_content)
        optimizations_applied.extend(table_opts)

        # 4. Figure optimization
        latex_content, figure_opts = self._optimize_figures(latex_content)
        optimizations_applied.extend(figure_opts)

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

        loader = ContentTypeLoader(types_dir=str(project_root / "content_types"))
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
                        # Try "Title (filename.md)" format first
                        paren_match = re.match(r'^(.+?)\s*\((\S+\.md)\)\s*$', section_def)
                        if paren_match:
                            title = paren_match.group(1).strip()
                            source = paren_match.group(2).strip()
                            structure.append({
                                'title': title,
                                'source': source,
                                'type': 'markdown'
                            })
                        elif ':' in section_def:
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
        """Convert markdown content to a complete LaTeX document.

        Uses a single holistic LLM call with the full type.md rendering instructions,
        available macros, structure rules, and all section content. The preamble is
        built programmatically from type.md LaTeX code blocks.
        """
        config_data = self.load_config_from_markdown(markdown_content)
        content_type = config_data.get('_content_type')

        # Pre-process all markdown sections for inline references
        document_structure = config_data.get('content manifest', [])
        processed_sections = []

        if document_structure:
            for section in document_structure:
                title = section['title']
                source = section.get('source')
                section_type = section.get('type', 'auto')

                if section_type == 'markdown' and source:
                    md_content = markdown_content.get(source, '')
                    if md_content:
                        processed = self._process_csv_table_references(md_content, str(self.content_dir))
                        processed = self._process_image_references(processed, str(self.content_dir))
                        processed = self._process_tikz_references(processed)
                        processed = re.sub(r'^#\s+[^\n]*\n*', '', processed, count=1)
                        processed_sections.append({'title': title, 'content': processed, 'source': source})
                    else:
                        processed_sections.append({'title': title, 'content': f'[Content not found: {source}]', 'source': source})
                elif title.lower() == 'abstract':
                    abstract_content = config_data.get('abstract', '')
                    if abstract_content:
                        processed_sections.append({'title': 'Abstract', 'content': abstract_content.strip(), 'source': None})
                else:
                    processed_sections.append({'title': title, 'content': '[Auto-generated content placeholder]', 'source': None})
        else:
            for filename, content in markdown_content.items():
                if filename == 'config.md':
                    continue
                processed = self._process_csv_table_references(content, str(self.content_dir))
                processed = self._process_image_references(processed, str(self.content_dir))
                processed = self._process_tikz_references(processed)
                title = filename.replace('.md', '').replace('_', ' ').title()
                processed_sections.append({'title': title, 'content': processed, 'source': filename})

        # Get type.md properties
        rendering_instructions = content_type.rendering_instructions if content_type else ""
        preamble_blocks = content_type.latex_preamble_blocks if content_type else []
        structure_rules = content_type.structure_rules if content_type else ""

        # Build preamble
        preamble = self._build_preamble(config_data, preamble_blocks)

        # Assemble content for prompt
        assembled_content = self._assemble_content_for_prompt(config_data, document_structure, processed_sections)

        # Generate document body via single holistic LLM call
        body = self._generate_document_body(
            assembled_content, config_data, rendering_instructions, preamble, structure_rules
        )

        # Assemble final document
        document = preamble + "\n\n\\begin{document}\n\n" + body + "\n\n\\end{document}\n"

        return document

    def _build_preamble(self, config_data: Dict, type_preamble_blocks: List[str]) -> str:
        """Build the LaTeX preamble from type.md code blocks or defaults."""
        doc_class = config_data.get('document class', 'article')
        font_size = config_data.get('_type_font_size', '12pt')
        paper_size = config_data.get('_type_paper_size', 'letterpaper')
        doc_options = config_data.get('document options', {})
        font_size = doc_options.get('font_size', font_size)
        paper_size = doc_options.get('paper_size', paper_size)

        documentclass_line = f"\\documentclass[{font_size},{paper_size}]{{{doc_class}}}"
        preamble_lines = [documentclass_line]
        print(f"   [LaTeX] Preamble documentclass: {documentclass_line}")

        content_type_id = config_data.get('content type', config_data.get('_content_type', None))
        if hasattr(content_type_id, 'type_id'):
            content_type_id = content_type_id.type_id

        if type_preamble_blocks:
            print(f"   [LaTeX] Loaded {len(type_preamble_blocks)} preamble blocks from {content_type_id or 'content type'} type.md")
            for block in type_preamble_blocks:
                preamble_lines.append(block.strip())
        else:
            if content_type_id and content_type_id != 'research_report':
                print(f"   [LaTeX] WARNING: Content type '{content_type_id}' has ZERO preamble blocks — falling back to default preamble. "
                      f"This is likely a bug (type.md not found or missing ```latex blocks).")
            else:
                print(f"   [LaTeX] Using default preamble (no content type preamble blocks)")
            preamble_lines.append(self._default_preamble())

        return "\n\n".join(preamble_lines)

    def _default_preamble(self) -> str:
        """Fallback preamble packages for content types without explicit LaTeX code blocks."""
        return (
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage{lmodern}\n"
            "\\usepackage{microtype}\n"
            "\\usepackage{amsmath}\n"
            "\\usepackage{graphicx}\n"
            "\\usepackage{booktabs}\n"
            "\\usepackage{array}\n"
            "\\usepackage{longtable}\n"
            "\\usepackage{float}\n"
            "\\usepackage{caption}\n"
            "\\usepackage{geometry}\n"
            "\\geometry{margin=1in}\n"
            "\\usepackage{fancyhdr}\n"
            "\\usepackage{setspace}\n"
            "\\onehalfspacing\n"
            "\\usepackage{hyperref}\n"
            "\\hypersetup{colorlinks=true,linkcolor=blue,citecolor=red,urlcolor=blue}\n"
            "\\usepackage{tikz}\n"
        )

    def _assemble_content_for_prompt(self, config_data: Dict, structure: List, sections: List[Dict]) -> str:
        """Concatenate all sections with delimiters for the LLM prompt."""
        parts = []
        for sec in sections:
            parts.append(f"=== SECTION: {sec['title']} ===")
            if sec.get('source'):
                parts.append(f"(source: {sec['source']})")
            parts.append(sec['content'])
            parts.append("")
        return "\n".join(parts)

    def _generate_document_body(self, content: str, config: Dict, instructions: str,
                                preamble: str, rules: str) -> str:
        """Generate the complete document body via a single holistic LLM call."""
        if not self.client:
            raise RuntimeError("ANTHROPIC_API_KEY not set — cannot convert markdown to LaTeX")

        # Build system prompt with rendering context
        system_parts = [
            "You are a LaTeX document generation specialist. Generate the BODY of a LaTeX document "
            "(everything between \\begin{document} and \\end{document}). Output ONLY raw LaTeX — "
            "no code fences, no \\documentclass, no preamble, no \\begin{document}/\\end{document}."
        ]

        if instructions:
            system_parts.append(f"\n\n## RENDERING INSTRUCTIONS\nFollow these instructions precisely:\n\n{instructions}")

        if preamble:
            system_parts.append(
                f"\n\n## AVAILABLE PREAMBLE (already included — you may use all macros/environments defined here)\n\n{preamble}"
            )

        if rules:
            system_parts.append(f"\n\n## STRUCTURE RULES\n\n{rules}")

        # Inject historical patterns if available
        pattern_ctx = getattr(self, '_current_pattern_context', '')
        if pattern_ctx:
            system_parts.append(f"\n\n## HISTORICAL PATTERNS\nApply these learnings from previous documents:\n\n{pattern_ctx}")

        system_prompt = "\n".join(system_parts)

        # Build user prompt with config metadata and content
        user_parts = ["Generate the complete LaTeX document body for the following content.\n"]

        # Config metadata
        title = config.get('title', '')
        if title:
            user_parts.append(f"Document Title: {title}")
        authors = config.get('authors', [])
        if authors:
            user_parts.append(f"Authors: {', '.join(authors) if isinstance(authors, list) else authors}")

        # Include all project metadata
        project_meta = config.get('project metadata', '')
        if project_meta:
            user_parts.append(f"\nProject Metadata:\n{project_meta}")

        # Include disclaimer if present
        disclaimer = config.get('disclaimer', '')
        if disclaimer:
            user_parts.append(f"\nDisclaimer text (include on cover page):\n{disclaimer}")

        doc_options = config.get('document options', {})
        if isinstance(doc_options, dict):
            if doc_options.get('include_toc', False):
                user_parts.append("\nInclude a table of contents.")
            if doc_options.get('include_bibliography', False):
                user_parts.append("Include a bibliography/references section at the end.")

        user_parts.append(f"\n\n## CONTENT\n\n{content}")

        user_prompt = "\n".join(user_parts)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0.2,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt,
                }],
            )
            body = response.content[0].text
            # Strip code fences if the LLM wrapped the output
            body = re.sub(r'^```(?:latex)?\s*\n', '', body)
            body = re.sub(r'\n```\s*$', '', body)
            return self._sanitize_unicode_for_latex(body)
        except Exception as e:
            print(f"Error generating document body via LLM: {e}")
            raise

    def _markdown_to_latex_content(self, markdown: str) -> str:
        """Convert markdown content to LaTeX body content using LLM.

        Simple per-fragment conversion used by external callers (e.g. report_generator).
        For full document generation, use _convert_markdown_to_latex instead.
        """
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
        """Apply final formatting improvements.

        Only modifies the document body — the preamble (everything before
        \\begin{document}) is returned unchanged to avoid breaking custom
        macro definitions (\\newcommand, \\newenvironment, etc.).
        """
        # Split at \begin{document} so regexes only touch the body
        split_marker = "\\begin{document}"
        marker_pos = content.find(split_marker)
        if marker_pos == -1:
            # No \begin{document} — apply to entire content (legacy path)
            body = content
            preamble = ""
            rejoin = False
        else:
            preamble = content[:marker_pos + len(split_marker)]
            body = content[marker_pos + len(split_marker):]
            rejoin = True

        # Ensure proper spacing around environments
        # Preserve optional arguments like \begin{tikzpicture}[remember picture, overlay]
        body = re.sub(r'(\\begin\{[^}]+\}(?:\[[^\]]*\])?)\n{0,1}', r'\1\n', body)
        body = re.sub(r'\n{0,1}(\\end\{[^}]+\})', r'\n\1', body)

        # Ensure proper spacing around sections
        body = re.sub(r'(\\(?:sub)*section\{[^}]+\})\n{0,1}', r'\1\n\n', body)

        if rejoin:
            result = preamble + body
        else:
            result = body

        # Clean up final whitespace
        return result.strip()

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