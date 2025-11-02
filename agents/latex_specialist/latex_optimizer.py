"""
LaTeX Optimizer - Milestone 3

Optimizes LaTeX document structure, typography, and formatting for professional quality.
"""

import re
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime


class LaTeXOptimizer:
    """
    Optimizes LaTeX documents for professional formatting and structure.

    Features:
    - Document structure optimization
    - Typography enhancement
    - Table and figure formatting improvement
    - LaTeX best practices application
    """

    def __init__(self):
        """Initialize the LaTeX optimizer."""
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

    def _convert_markdown_to_latex(self, markdown_content: Dict[str, str]) -> str:
        """Convert markdown content to professional LaTeX document."""
        # Start with professional document template
        latex_parts = [
            '\\documentclass[12pt,letterpaper]{article}',
            '',
            '% Professional packages',
            '\\usepackage[T1]{fontenc}',
            '\\usepackage[utf8]{inputenc}',
            '\\usepackage{lmodern}',
            '\\usepackage{microtype}',
            '\\usepackage{geometry}',
            '\\usepackage{setspace}',
            '\\usepackage{booktabs}',
            '\\usepackage{array}',
            '\\usepackage{graphicx}',
            '\\usepackage{float}',
            '\\usepackage{caption}',
            '\\usepackage{hyperref}',
            '\\usepackage{cite}',
            '',
            '% Page setup',
            '\\geometry{margin=1in}',
            '\\onehalfspacing',
            '',
            '% Title and author',
            '\\title{Research Report}',
            '\\author{Research Team}',
            '\\date{\\today}',
            '',
            '\\begin{document}',
            '\\maketitle',
            '\\tableofcontents',
            '\\newpage',
            ''
        ]

        # Convert each markdown file
        for filename, content in markdown_content.items():
            latex_parts.append(f'% Content from {filename}')
            latex_content = self._markdown_to_latex_content(content)
            latex_parts.append(latex_content)
            latex_parts.append('')

        latex_parts.append('\\end{document}')

        return '\n'.join(latex_parts)

    def _markdown_to_latex_content(self, markdown: str) -> str:
        """Convert markdown content to LaTeX with professional formatting."""
        content = markdown

        # Convert headers
        content = re.sub(r'^# (.+)$', r'\\section{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)

        # Convert hyperlinks
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\href{\2}{\1}', content)

        # Convert emphasis
        content = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', content)
        content = re.sub(r'\*(.+?)\*', r'\\textit{\1}', content)
        content = re.sub(r'`(.+?)`', r'\\texttt{\1}', content)

        # Process CSV table references first
        content = self._process_csv_table_references(content)

        # Convert tables
        content = self._convert_markdown_tables(content)

        # Convert lists
        content = re.sub(r'^- (.+)$', r'\\item \1', content, flags=re.MULTILINE)
        content = re.sub(r'^(\d+)\. (.+)$', r'\\item \2', content, flags=re.MULTILINE)

        # Wrap lists in environments
        content = self._wrap_lists(content)

        # Clean up extra newlines
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def _wrap_lists(self, content: str) -> str:
        """Wrap list items in proper LaTeX environments."""
        lines = content.split('\n')
        result = []
        in_list = False
        list_type = None

        for line in lines:
            if line.strip().startswith('\\item'):
                if not in_list:
                    # Starting a new list
                    if re.search(r'^\d+\.', line):
                        result.append('\\begin{enumerate}')
                        list_type = 'enumerate'
                    else:
                        result.append('\\begin{itemize}')
                        list_type = 'itemize'
                    in_list = True
                result.append(line)
            else:
                if in_list:
                    # Ending the list
                    result.append(f'\\end{{{list_type}}}')
                    in_list = False
                    list_type = None
                result.append(line)

        # Close any remaining list
        if in_list:
            result.append(f'\\end{{{list_type}}}')

        return '\n'.join(result)

    def _convert_markdown_tables(self, content: str) -> str:
        """Convert markdown tables to professional LaTeX tables."""
        lines = content.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this line looks like a table header
            if '|' in line and line.count('|') >= 2:
                # Check next line for separator
                if i + 1 < len(lines) and re.match(r'^\s*\|[\s\-\|:]+\|\s*$', lines[i + 1]):
                    # This is a markdown table
                    table_lines = [line]
                    i += 1  # Skip separator line
                    i += 1  # Move to first data row

                    # Collect all table rows
                    while i < len(lines) and '|' in lines[i] and lines[i].strip():
                        table_lines.append(lines[i].strip())
                        i += 1

                    # Convert to LaTeX table
                    latex_table = self._markdown_table_to_latex(table_lines)
                    result.append(latex_table)
                    continue

            result.append(lines[i])
            i += 1

        return '\n'.join(result)

    def _markdown_table_to_latex(self, table_lines: List[str]) -> str:
        """Convert markdown table lines to LaTeX table format."""
        if not table_lines:
            return ""

        # Parse header row
        header_row = table_lines[0]
        headers = [cell.strip() for cell in header_row.split('|')[1:-1]]  # Remove empty first/last

        # Parse data rows
        data_rows = []
        for line in table_lines[1:]:
            if line.strip():
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
                if cells:  # Only add non-empty rows
                    data_rows.append(cells)

        if not headers:
            return ""

        # Generate LaTeX table
        num_cols = len(headers)
        col_spec = 'l' * num_cols  # Default to left-aligned columns

        latex_parts = [
            '\\begin{table}[htbp]',
            '\\centering',
            f'\\begin{{tabular}}{{{col_spec}}}',
            '\\toprule'
        ]

        # Add header row
        header_latex = ' & '.join(headers) + ' \\\\'
        latex_parts.append(header_latex)
        latex_parts.append('\\midrule')

        # Add data rows
        for row in data_rows:
            # Ensure row has the right number of columns
            while len(row) < num_cols:
                row.append('')
            row = row[:num_cols]  # Truncate if too many columns

            row_latex = ' & '.join(row) + ' \\\\'
            latex_parts.append(row_latex)

        latex_parts.extend([
            '\\bottomrule',
            '\\end{tabular}',
            '\\caption{Table Caption}',
            '\\label{tab:table}',
            '\\end{table}'
        ])

        return '\n'.join(latex_parts)

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