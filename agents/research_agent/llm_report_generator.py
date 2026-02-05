"""
LLM-Enhanced Research Report Generator - Milestone 3

Uses Claude with pattern learning to generate intelligent LaTeX documents.
Applies learned patterns from historical document generation.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.content_type_loader import ContentTypeLoader
from tools.llm_latex_generator import LaTeXGenerationRequest, LaTeXGenerationResult, LLMLaTeXGenerator
from tools.magazine_layout import MagazineLayoutGenerator
from tools.pattern_injector import PatternInjector
from tools.pdf_compiler import PDFCompiler


class LLMResearchReportGenerator:
    """
    LLM-powered LaTeX report generator with pattern learning integration.

    Features:
    - Uses Claude to generate intelligent LaTeX
    - Applies learned patterns from historical documents
    - Self-correcting LaTeX generation
    - Context-aware optimization
    - Supports multiple content sources (research_report, magazine)
    """

    def __init__(self, output_dir: str = "artifacts/output", document_type: str = "research_report",
                 content_source: str = None):
        """
        Initialize the LLM report generator.

        Args:
            output_dir: Directory to save generated files
            document_type: Type of document (e.g., 'research_report', 'article', 'magazine')
            content_source: Source content folder (e.g., 'research_report', 'magazine').
                           If None, defaults to document_type.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = Path("artifacts")
        self.document_type = document_type

        # Content source determines which sample_content subdirectory to use
        self.content_source = content_source or document_type
        self.content_dir = self.artifacts_dir / "sample_content" / self.content_source
        self.data_dir = self.content_dir / "data"
        self.images_dir = self.content_dir / "images"

        # Load configuration from config.md if available
        self.config = self._load_config()

        # Initialize LLM generator and pattern injector
        self.llm_generator = LLMLaTeXGenerator()
        self.pattern_injector = PatternInjector(document_type=document_type)
        self.pdf_compiler = PDFCompiler()

    def _load_config(self) -> Dict:
        """Load document configuration from config.md.

        Uses ContentTypeLoader to resolve the content type definition.
        Parses remaining config sections (metadata, manifest, options) from config.md.
        """
        config = {
            "title": "Research Report",
            "subtitle": "",
            "author": "Research Team",
            "date": "",
            "document_type": self.document_type,
            "sections": [],
            "style": {},
            "options": {}
        }

        config_path = self.content_dir / "config.md"
        if not config_path.exists():
            return config

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse key-value pairs from config.md
        current_section = None
        disclaimer_lines = []
        in_disclaimer = False
        rendering_notes_lines = []
        in_rendering_notes = False
        content_type_id = None

        for line in content.split('\n'):
            line_stripped = line.strip()

            # Track sections
            if line_stripped.startswith('## '):
                current_section = line_stripped[3:].strip().lower()
                in_disclaimer = (current_section == 'disclaimer')
                in_rendering_notes = (current_section == 'rendering notes')
                continue

            # Capture content type
            if current_section == 'content type' and line_stripped and not line_stripped.startswith('---'):
                content_type_id = line_stripped
                continue

            # Capture disclaimer content (multi-line)
            if in_disclaimer and line_stripped and not line_stripped.startswith('---'):
                disclaimer_lines.append(line_stripped)
                continue

            # Capture rendering notes (multi-line)
            if in_rendering_notes and line_stripped:
                rendering_notes_lines.append(line_stripped)
                continue

            line = line_stripped  # Use stripped version for rest of parsing

            # Parse key-value pairs
            if line.startswith('- ') and ':' in line:
                key_value = line[2:].split(':', 1)
                if len(key_value) == 2:
                    # Strip bold markers (**) from key
                    key = key_value[0].strip().strip('*').lower().replace(' ', '_')
                    value = key_value[1].strip()

                    # Map to config
                    if key == 'title':
                        config['title'] = value
                    elif key == 'subtitle':
                        config['subtitle'] = value
                    elif key == 'author' or key == 'publisher':
                        config['author'] = value
                    elif key == 'date':
                        config['date'] = value
                    elif key == 'issue':
                        config['issue'] = value
                    elif key == 'price':
                        config['price'] = value
                    elif key == 'barcode_text':
                        config['barcode_text'] = value
                    elif current_section == 'document options':
                        config['options'][key] = value
                    elif current_section == 'headers and footers':
                        config['style'][key] = value

            # Parse numbered section list (supports both "Sections" and "Content Manifest")
            if current_section in ('sections', 'content manifest') and line and line[0].isdigit():
                # e.g., "1. Editor's Letter (introduction.md)"
                if '(' in line and ')' in line:
                    start = line.index('(') + 1
                    end = line.index(')')
                    filename = line[start:end]
                    title_part = line.split('.', 1)[1] if '.' in line else line
                    title = title_part.split('(')[0].strip()
                    config['sections'].append({'file': filename, 'title': title})

        # Store disclaimer if found
        if disclaimer_lines:
            config['disclaimer'] = ' '.join(disclaimer_lines)

        # Store rendering notes
        if rendering_notes_lines:
            config['rendering_notes'] = '\n'.join(rendering_notes_lines)

        # Load content type definition
        type_id = content_type_id or self.content_source
        loader = ContentTypeLoader()
        content_type = loader.load_type(type_id)
        config['_content_type'] = content_type

        return config

    def load_markdown_content(self, filename: str) -> str:
        """Load markdown content from the sample_content directory."""
        file_path = self.content_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def load_all_markdown_sections(self) -> List[Dict]:
        """
        Load all markdown content files and organize into sections.
        Uses sections from config.md if available, otherwise auto-discovers .md files.

        Returns:
            List of section dictionaries with title and content
        """
        sections = []

        # Use sections from config if available
        if self.config.get('sections'):
            markdown_files = [(s['file'], s['title']) for s in self.config['sections']]
        else:
            # Auto-discover .md files (excluding config.md and README.md)
            exclude_files = {'config.md', 'readme.md'}
            markdown_files = []
            if self.content_dir.exists():
                for md_file in sorted(self.content_dir.glob('*.md')):
                    if md_file.name.lower() not in exclude_files:
                        # Generate title from filename
                        title = md_file.stem.replace('_', ' ').replace('-', ' ').title()
                        markdown_files.append((md_file.name, title))

        for filename, title in markdown_files:
            content = self.load_markdown_content(filename)
            if content:
                sections.append({
                    "title": title,
                    "content": content,
                    "type": "markdown"
                })

        return sections

    def load_csv_tables(self) -> List[Dict]:
        """
        Load CSV data files as table specifications.

        Returns:
            List of table dictionaries
        """
        tables = []

        # Model performance table
        csv_file = self.data_dir / "model_performance.csv"
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    tables.append({
                        "caption": "Model Performance Comparison",
                        "data": rows,
                        "format": "booktabs"
                    })

        # Training metrics table
        csv_file2 = self.data_dir / "training_metrics.csv"
        if csv_file2.exists():
            with open(csv_file2, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows and len(rows) > 1:
                    # Only first 5 data rows for conciseness
                    limited_rows = [rows[0]] + rows[1:6]
                    tables.append({
                        "caption": "Training Progression (First 5 Epochs)",
                        "data": limited_rows,
                        "format": "booktabs"
                    })

        return tables

    def load_figures(self) -> List[Dict]:
        """
        Discover figure files in images directory and load placement guidance from README.

        Returns:
            List of figure dictionaries with descriptions and placement guidance
        """
        figures = []

        if not self.images_dir.exists():
            return figures

        # Load image descriptions from README.md if it exists
        image_guidance = {}
        readme_path = self.images_dir / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                image_guidance = self._parse_image_readme(readme_content)

        # Look for common image extensions
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.pdf']:
            for img_path in self.images_dir.glob(ext):
                filename = img_path.name

                # Get guidance from README if available
                guidance = image_guidance.get(filename, {})

                # Calculate path relative to output directory (pdflatex runs from artifacts/output/)
                relative_path = f"../sample_content/{self.content_source}/images/" + filename

                figures.append({
                    "path": relative_path,
                    "caption": guidance.get("caption", img_path.stem.replace('_', ' ').replace('-', ' ').title()),
                    "width": guidance.get("width", "0.8\\textwidth"),
                    "description": guidance.get("description", ""),
                    "placement": guidance.get("placement", "")
                })

        return figures

    def _fix_common_latex_issues(self, latex_content: str) -> str:
        """
        Fix common LaTeX issues that the LLM often generates.

        These are syntactic issues that prevent compilation.
        """
        import re
        fixes_applied = []

        # Fix invalid TikZ options
        # "letter spacing=X" is not a valid TikZ option, remove it
        if 'letter spacing=' in latex_content:
            latex_content = re.sub(r',?\s*letter spacing=[^,\]]+', '', latex_content)
            fixes_applied.append("Removed invalid 'letter spacing' TikZ option")

        # Fix other common invalid TikZ options
        invalid_tikz_opts = ['word spacing=', 'tracking=', 'stretch=']
        for opt in invalid_tikz_opts:
            if opt in latex_content:
                latex_content = re.sub(rf',?\s*{re.escape(opt)}[^,\]]+', '', latex_content)
                fixes_applied.append(f"Removed invalid '{opt[:-1]}' TikZ option")

        # Replace placeholder figures with actual images
        latex_content = self._replace_placeholder_figures(latex_content)

        if fixes_applied:
            print(f"🔧 Fixed LaTeX issues: {', '.join(fixes_applied)}")

        return latex_content

    def _replace_placeholder_figures(self, latex_content: str) -> str:
        """
        Replace LLM-generated placeholder figures with actual images.

        The LLM sometimes generates text placeholders like:
        \\fbox{\\parbox{...}{[Chart Name]}}

        This replaces them with actual \\includegraphics commands.
        """
        # Get available images
        figures = self.load_figures()
        if not figures:
            return latex_content

        # Get content images (exclude cover, barcode)
        content_images = []
        for fig in figures:
            fig_path = fig.get('path', '')
            filename = fig_path.split('/')[-1].lower() if fig_path else ''
            if not any(skip in filename for skip in ['cover', 'barcode']):
                content_images.append(fig)

        if not content_images:
            return latex_content

        # Find and replace placeholder patterns using string operations
        # Look for \fbox{\parbox patterns that contain bracketed placeholder text
        lines = latex_content.split('\n')
        new_lines = []
        replacements = 0
        image_idx = 0

        for line in lines:
            # Check if this line contains a placeholder figure
            if '\\fbox{\\parbox' in line and '[' in line and ']' in line:
                # This looks like a placeholder - check for common indicators
                line_lower = line.lower()
                is_placeholder = any(indicator in line_lower for indicator in [
                    'placeholder', 'would be displayed', 'image here',
                    'chart]', 'graph]', 'figure]', 'comparison]'
                ])

                if is_placeholder and image_idx < len(content_images):
                    # Replace with actual image
                    img = content_images[image_idx]
                    image_idx += 1
                    new_line = f"\\includegraphics[width=0.8\\textwidth]{{{img['path']}}}"
                    new_lines.append(new_line)
                    replacements += 1
                    continue

            new_lines.append(line)

        if replacements > 0:
            print(f"🔧 Replaced {replacements} placeholder figure(s) with actual images")
            return '\n'.join(new_lines)

        return latex_content

    def _fix_image_paths(self, latex_content: str) -> str:
        """
        Fix image paths in LaTeX content.

        The LLM often generates incorrect relative paths like:
        - sample_content/magazine/images/image.jpg
        - artifacts/sample_content/magazine/images/image.jpg
        - images/image.jpg
        - example-image (placeholder)

        The correct path (relative to artifacts/output/) is:
        - ../sample_content/{content_source}/images/image.jpg
        """
        import re

        correct_prefix = f"../sample_content/{self.content_source}/images/"

        # Get list of actual image files to use for replacements
        actual_images = []
        if self.images_dir.exists():
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                actual_images.extend([f.name for f in self.images_dir.glob(ext)])

        # Separate special images from content images
        cover_image = None
        content_images = []
        for img in actual_images:
            if 'cover' in img.lower():
                cover_image = img
            elif 'barcode' not in img.lower():
                content_images.append(img)

        # Track which content images have been used
        image_index = [0]  # Use list to allow mutation in nested function

        def fix_path(match):
            full_match = match.group(0)
            path = match.group(1)

            # Extract just the filename from any path
            filename = path.split('/')[-1]

            # Check if this is a placeholder image
            is_placeholder = filename.startswith('example-image') or filename == 'placeholder'

            # Check for special images by context
            if 'paperwidth' in full_match or 'paperheight' in full_match:
                # This is likely a cover/background image
                if cover_image:
                    return full_match.replace(path, correct_prefix + cover_image)

            if is_placeholder and content_images:
                # Replace placeholder with actual content image
                actual_file = content_images[image_index[0] % len(content_images)]
                image_index[0] += 1
                return full_match.replace(path, correct_prefix + actual_file)

            # Skip if already has correct prefix with a real filename
            if path.startswith(correct_prefix) and not is_placeholder:
                return full_match

            # Reconstruct with correct prefix
            new_path = correct_prefix + filename
            return full_match.replace(path, new_path)

        # Match \includegraphics[...]{path} or \includegraphics{path}
        pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        new_content, count = re.subn(pattern, fix_path, latex_content)

        if count > 0:
            # Count how many were actually changed
            original_paths = re.findall(pattern, latex_content)
            new_paths = re.findall(pattern, new_content)
            changes = sum(1 for o, n in zip(original_paths, new_paths) if o != n)
            if changes > 0:
                print(f"🔧 Fixed {changes} image path(s)")

        return new_content

    def _ensure_printshop_attribution(self, latex_content: str, figures: list) -> str:
        """
        Ensure the document has PrintShop attribution and barcode (if available).

        Reads barcode text from config if available.
        """
        # Check if PrintShop attribution already exists (the specific footer text, not disclaimer)
        if 'Generated by DeepAgents PrintShop' in latex_content:
            return latex_content

        # Find barcode image path if available
        barcode_path = None
        for fig in figures:
            # Extract filename from path to check for barcode
            fig_path = fig.get('path', '')
            filename = fig_path.split('/')[-1].lower() if fig_path else ''
            if 'barcode' in filename:
                barcode_path = fig_path
                break

        # Get barcode text from config (e.g., "ISSUE 01 | $9.99 US")
        barcode_text = self.config.get('barcode_text', '')

        print("📄 Adding PrintShop attribution...")

        # Minimal attribution block - just the tool credit and barcode
        attribution_code = "\n% PrintShop Attribution\n"

        if barcode_path:
            attribution_code += f"""\\vfill
\\begin{{center}}
\\includegraphics[width=1in]{{{barcode_path}}}
"""
            if barcode_text:
                # Escape $ signs for LaTeX
                barcode_text_escaped = barcode_text.replace('$', '\\$')
                attribution_code += f"""
\\vspace{{0.3em}}
{{\\tiny {barcode_text_escaped}}}
"""
            attribution_code += """
\\vspace{1em}
{\\footnotesize\\itshape Generated by DeepAgents PrintShop}
\\end{center}
"""
        else:
            attribution_code += """\\vfill
\\begin{center}
{\\footnotesize\\itshape Generated by DeepAgents PrintShop}
\\end{center}
"""

        # Insert before \end{document}
        end_doc_pos = latex_content.find('\\end{document}')
        if end_doc_pos != -1:
            latex_content = latex_content[:end_doc_pos] + attribution_code + latex_content[end_doc_pos:]

        return latex_content

    def _inject_missing_figures(self, latex_content: str) -> str:
        """
        Post-process LaTeX to inject missing figures if the LLM didn't include them.

        This is a safety net for when the LLM generation doesn't include images.
        Note: PrintShop attribution is handled separately in generate_and_compile().
        """
        # Check if figures are already included (uncommented)
        # Look for \includegraphics that's NOT on a line starting with %
        has_uncommented_figures = False
        for line in latex_content.split('\n'):
            stripped = line.strip()
            if '\\includegraphics' in stripped and not stripped.startswith('%'):
                has_uncommented_figures = True
                break

        if has_uncommented_figures:
            return latex_content  # Figures already present

        figures = self.load_figures()
        if not figures:
            return latex_content  # No figures to inject

        print(f"🖼️  Injecting {len(figures)} missing figures into LaTeX...")

        # For magazine content, handle special images
        if self.content_source == 'magazine':
            # Find the cover image and barcode
            cover_image = None
            barcode_image = None
            other_images = []

            for fig in figures:
                # Extract filename from path
                fig_path = fig.get('path', '')
                filename = fig_path.split('/')[-1].lower() if fig_path else ''
                if 'cover' in filename:
                    cover_image = fig
                elif 'barcode' in filename:
                    barcode_image = fig
                else:
                    other_images.append(fig)

            # Inject cover image as background on first page
            if cover_image:
                cover_code = f"""
% Cover page background
\\AddToShipoutPictureBG*{{%
  \\AtPageUpperLeft{{%
    \\includegraphics[width=\\paperwidth,height=\\paperheight]{{{cover_image['path']}}}%
  }}%
}}
"""
                # Insert after \begin{document}
                begin_doc_pos = latex_content.find('\\begin{document}')
                if begin_doc_pos != -1:
                    insert_pos = latex_content.find('\n', begin_doc_pos) + 1
                    latex_content = latex_content[:insert_pos] + cover_code + latex_content[insert_pos:]

            # Inject barcode before \end{document}
            if barcode_image:
                barcode_code = f"""
% Back cover barcode
\\newpage
\\thispagestyle{{empty}}
\\vspace*{{\\fill}}
\\begin{{center}}
\\includegraphics[width=1in]{{{barcode_image['path']}}}

\\vspace{{0.3em}}
{{\\tiny ISSUE 01 | \\$9.99 US}}
\\end{{center}}
"""
                end_doc_pos = latex_content.find('\\end{document}')
                if end_doc_pos != -1:
                    latex_content = latex_content[:end_doc_pos] + barcode_code + latex_content[end_doc_pos:]

            # Inject chart images into content sections
            for fig in other_images:
                # Extract filename from path
                fig_path = fig.get('path', '')
                filename = fig_path.split('/')[-1].lower() if fig_path else ''
                # Skip certain images that are decorative
                if any(skip in filename for skip in ['cover', 'logo', 'icon']):
                    continue

                # For charts and data visualizations, inject after methodology or results sections
                if 'chart' in filename or 'graph' in filename or 'comparison' in filename:
                    figure_code = f"""
\\begin{{figure}}[H]
\\centering
\\includegraphics[width=0.9\\textwidth]{{{fig['path']}}}
\\caption{{{fig.get('caption', 'Figure')}}}
\\end{{figure}}
"""
                    # Try to insert after a results or data section
                    for section_marker in ['State of AI Agents', 'methodology', 'results', 'data']:
                        section_pos = latex_content.lower().find(section_marker.lower())
                        if section_pos != -1:
                            # Find end of paragraph after section
                            next_para = latex_content.find('\\end{multicols}', section_pos)
                            if next_para != -1:
                                latex_content = latex_content[:next_para] + figure_code + latex_content[next_para:]
                                break
        else:
            # For other document types, inject figures at appropriate locations
            for fig in figures:
                fig_width = fig.get('width', '0.8\\\\textwidth')
                figure_code = f"""
\\begin{{figure}}[H]
\\centering
\\includegraphics[width={fig_width}]{{{fig['path']}}}
\\caption{{{fig.get('caption', 'Figure')}}}
\\end{{figure}}
"""
                # Insert before \end{document}
                end_doc_pos = latex_content.find('\\end{document}')
                if end_doc_pos != -1:
                    latex_content = latex_content[:end_doc_pos] + figure_code + latex_content[end_doc_pos:]

        return latex_content

    def _parse_image_readme(self, readme_content: str) -> Dict:
        """
        Parse the images README.md to extract image descriptions and placement guidance.

        Returns:
            Dictionary mapping filename to guidance dict
        """
        guidance = {}
        current_file = None
        current_data = {}

        for line in readme_content.split('\n'):
            line = line.strip()

            # Detect image filename (e.g., **cover-image.jpg**)
            if line.startswith('**') and line.endswith('**') and ('.' in line):
                # Save previous entry
                if current_file:
                    guidance[current_file] = current_data

                current_file = line.strip('*')
                current_data = {}

            # Parse description, placement, caption
            elif current_file and line.startswith('- '):
                if line.startswith('- Description:'):
                    current_data['description'] = line.replace('- Description:', '').strip()
                elif line.startswith('- Placement:'):
                    current_data['placement'] = line.replace('- Placement:', '').strip()
                elif line.startswith('- Caption suggestion:'):
                    current_data['caption'] = line.replace('- Caption suggestion:', '').strip().strip('"')
                elif line.startswith('- Style:'):
                    # Check for width hints in style
                    if '40%' in line:
                        current_data['width'] = "0.4\\textwidth"
                    elif '30%' in line:
                        current_data['width'] = "0.3\\textwidth"

        # Save last entry
        if current_file:
            guidance[current_file] = current_data

        return guidance

    def _get_magazine_requirements(self) -> List[str]:
        """Get magazine-specific LaTeX requirements.

        Uses the content type definition for rendering instructions and the
        MagazineLayoutGenerator for the concrete preamble code.
        """
        requirements = []

        # Get preamble from MagazineLayoutGenerator (concrete LaTeX code)
        layout_gen = MagazineLayoutGenerator()
        preamble = layout_gen.get_full_preamble()
        preamble_requirement = f"""MAGAZINE PREAMBLE - INCLUDE THIS EXACT CODE IN YOUR DOCUMENT PREAMBLE:
```latex
{preamble}
```
You MUST include all these package imports and macro definitions in your document preamble."""
        requirements.append(preamble_requirement)

        # Get layout requirements from the generator
        requirements.extend(layout_gen.get_magazine_requirements())

        # Inject the content type definition as rendering context
        content_type = self.config.get('_content_type')
        if content_type and content_type.type_md_content:
            requirements.append(
                "CONTENT TYPE RENDERING INSTRUCTIONS:\n" + content_type.type_md_content
            )

        # Inject rendering notes from config.md (content-specific instructions)
        rendering_notes = self.config.get('rendering_notes', '')
        if rendering_notes:
            requirements.append(
                "ADDITIONAL RENDERING NOTES FROM CONTENT CONFIG:\n" + rendering_notes
            )

        return requirements

    def _get_research_report_requirements(self) -> List[str]:
        """Get research report-specific LaTeX requirements.

        Uses the content type definition for rendering instructions.
        """
        requirements = []

        # Inject the content type definition as rendering context
        content_type = self.config.get('_content_type')
        if content_type and content_type.type_md_content:
            requirements.append(
                "CONTENT TYPE RENDERING INSTRUCTIONS:\n" + content_type.type_md_content
            )
        else:
            # Fallback if type definition not available
            requirements.extend([
                "Use standard academic article format",
                "Include abstract if content has one",
                "Use numbered sections and subsections",
                "Format references properly if bibliography exists",
                "Use single-column layout throughout"
            ])

        # Inject rendering notes from config.md
        rendering_notes = self.config.get('rendering_notes', '')
        if rendering_notes:
            requirements.append(
                "ADDITIONAL RENDERING NOTES FROM CONTENT CONFIG:\n" + rendering_notes
            )

        return requirements

    def generate_with_patterns(self) -> LaTeXGenerationResult:
        """
        Generate LaTeX document using LLM with learned patterns.

        Returns:
            Generation result with LaTeX content
        """
        print("🚀 LLM-Enhanced LaTeX Generation")
        print("=" * 60)
        print(f"📁 Content Source: {self.content_source}")
        print(f"📄 Document Type: {self.document_type}")
        print(f"📝 Title: {self.config.get('title', 'Untitled')}")
        print()

        # Get pattern context for Author agent
        pattern_context = self.pattern_injector.get_context_for_author()

        if pattern_context:
            print("✅ Loaded learned patterns from historical documents")
            print(self.pattern_injector.get_summary())
        else:
            print(f"ℹ️  No learned patterns available yet for '{self.document_type}'")

        print()

        # Load document components
        sections = self.load_all_markdown_sections()
        tables = self.load_csv_tables()
        figures = self.load_figures()

        print(f"📄 Loaded {len(sections)} content sections")
        print(f"📊 Loaded {len(tables)} data tables")
        print(f"🖼️  Found {len(figures)} figures")
        print()

        # Build base requirements
        requirements = [
            "Use professional typography packages (lmodern)",
            "Format tables with booktabs package",
            "Include proper hyperref setup for navigation",
            "Use appropriate section hierarchy",
            "Add proper spacing and layout"
        ]

        # Add disclaimer if present in config
        if self.config.get('disclaimer'):
            disclaimer_text = self.config['disclaimer']
            requirements.append(f"""IMPORTANT - DISCLAIMER SECTION:
Include a prominently styled disclaimer box/section at the VERY BEGINNING of the document (right after the title/maketitle).
Use a framed box or shaded environment to make it stand out.
The disclaimer text is:
"{disclaimer_text}"
This disclaimer MUST appear before any content sections.""")
            print("📋 Adding disclaimer requirement")

        # Add document-type-specific requirements
        if self.content_source == 'magazine' or self.document_type == 'magazine':
            print("📰 Adding magazine-specific styling requirements")
            requirements.extend(self._get_magazine_requirements())
        else:
            requirements.extend(self._get_research_report_requirements())

        # Add pattern-based requirements
        if pattern_context:
            requirements.append(
                "IMPORTANT: Apply the following learned patterns from historical documents:\n" +
                pattern_context
            )

        # Build title from config
        title = self.config.get('title', 'Document')
        if self.config.get('subtitle'):
            title = f"{title}: {self.config['subtitle']}"

        # Create generation request
        request = LaTeXGenerationRequest(
            title=title,
            author=self.config.get('author', 'Author'),
            content_sections=sections,
            tables=tables,
            figures=figures,
            requirements=requirements
        )

        # Generate using LLM
        print("🤖 Generating LaTeX with Claude Sonnet 4.5...")
        result = self.llm_generator.generate_document(request, validate=True)

        if result.success:
            print("✅ Generation successful!")
            if result.improvements_made:
                print(f"💡 Applied {len(result.improvements_made)} improvements:")
                for improvement in result.improvements_made[:5]:
                    print(f"   • {improvement}")
            if result.warnings:
                print(f"⚠️  {len(result.warnings)} warnings:")
                for warning in result.warnings[:3]:
                    print(f"   • {warning}")
        else:
            print(f"❌ Generation failed: {result.error_message}")

        return result

    def generate_and_compile(self, max_llm_corrections: int = 3) -> Dict:
        """
        Generate LaTeX and compile to PDF with LLM self-correction loop.

        Args:
            max_llm_corrections: Maximum LLM self-correction attempts

        Returns:
            Dictionary with paths and status
        """
        # Generate LaTeX
        result = self.generate_with_patterns()

        if not result.success:
            return {
                "success": False,
                "error": result.error_message
            }

        latex_content = result.latex_content
        output_filename = f"{self.content_source}.tex"
        tex_path = self.output_dir / output_filename

        # Pre-validation: Check for truncated output FIRST (before figure injection)
        # This ensures \end{document} exists for subsequent processing
        if '\\end{document}' not in latex_content:
            print("⚠️  Generated LaTeX appears truncated (missing \\end{document})")
            print("🔧 Attempting to complete the document...")
            # Use specialized truncation completion (not full document regeneration)
            latex_content, fixed = self.llm_generator.complete_truncated_document(latex_content)
            if fixed:
                print("✅ Document completion successful")
            else:
                print("⚠️  Document completion failed - will try to compile anyway")

        # Post-process: Inject figures if missing (AFTER self-correction so \end{document} exists)
        latex_content = self._inject_missing_figures(latex_content)

        # Fix image paths: LLM often generates wrong relative paths
        # Correct path is ../sample_content/{content_source}/images/ (relative to artifacts/output/)
        latex_content = self._fix_image_paths(latex_content)

        # Fix common LaTeX issues that LLM generates
        latex_content = self._fix_common_latex_issues(latex_content)

        # Ensure PrintShop attribution is present (runs after figure injection)
        figures = self.load_figures()
        latex_content = self._ensure_printshop_attribution(latex_content, figures)

        # Save LaTeX file
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"\n💾 Saved LaTeX to: {tex_path}")

        # Compile with LLM self-correction loop
        print("\n📄 Compiling to PDF...")
        pdf_path = tex_path.with_suffix('.pdf')

        for attempt in range(max_llm_corrections + 1):
            success, message = self.pdf_compiler.compile(str(tex_path))

            if success:
                print(f"✅ PDF generated: {pdf_path}")
                return {
                    "success": True,
                    "tex_path": str(tex_path),
                    "pdf_path": str(pdf_path),
                    "latex_result": result,
                    "compilation_result": {"success": True, "message": message}
                }

            # Last attempt - give up
            if attempt == max_llm_corrections:
                print(f"❌ PDF compilation failed after {max_llm_corrections} LLM correction attempts")
                print(f"Error: {message}")
                break

            # Try LLM self-correction
            print(f"\n🤖 LLM Self-Correction Attempt {attempt + 1}/{max_llm_corrections}...")
            corrected_latex, fixed, corrections = self.llm_generator.self_correct_compilation_errors(
                latex_content, message, max_attempts=1
            )

            if fixed:
                latex_content = corrected_latex
                # Save corrected version
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                print(f"   ✅ Applied corrections: {corrections}")
            else:
                print("   ❌ LLM could not fix the issue")
                break

        return {
            "success": False,
            "tex_path": str(tex_path),
            "pdf_path": None,
            "latex_result": result,
            "compilation_result": {"success": False, "message": message}
        }


def main():
    """Demonstration of LLM-enhanced report generation."""
    import argparse

    parser = argparse.ArgumentParser(description='LLM-Enhanced Document Generator')
    parser.add_argument(
        '--content', '-c',
        default='research_report',
        help='Content source folder (e.g., research_report, magazine)'
    )
    parser.add_argument(
        '--type', '-t',
        default=None,
        help='Document type for pattern learning (defaults to content source)'
    )
    args = parser.parse_args()

    content_source = args.content
    document_type = args.type or content_source

    print("\n" + "=" * 60)
    print("🧠 LLM-Enhanced Document Generator with Pattern Learning")
    print("=" * 60)
    print(f"📁 Content source: {content_source}")
    print(f"📄 Document type: {document_type}")
    print()

    generator = LLMResearchReportGenerator(
        content_source=content_source,
        document_type=document_type
    )
    result = generator.generate_and_compile()

    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ Document generation complete!")
        print("=" * 60)
        print(f"\n📄 LaTeX: {result['tex_path']}")
        print(f"📑 PDF: {result['pdf_path']}")
    else:
        print("❌ Document generation failed")
        print("=" * 60)
        if result.get("error"):
            print(f"\nError: {result['error']}")
    print()


if __name__ == "__main__":
    main()
