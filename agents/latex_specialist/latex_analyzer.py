"""
LaTeX Analyzer - Milestone 3

Analyzes LaTeX document structure, typography, and formatting quality.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LaTeXIssue:
    """Represents a LaTeX formatting issue."""
    severity: str  # 'error', 'warning', 'suggestion'
    category: str  # 'structure', 'typography', 'tables', 'figures', 'general'
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class LaTeXAnalysisResult:
    """Results of LaTeX document analysis."""
    structure_score: int  # 0-25
    typography_score: int  # 0-25
    tables_figures_score: int  # 0-25
    best_practices_score: int  # 0-25
    overall_score: int  # 0-100
    issues: List[LaTeXIssue]
    document_class: str
    packages_used: List[str]
    structure_info: Dict
    suggestions: List[str]


class LaTeXAnalyzer:
    """
    Analyzes LaTeX documents for quality, structure, and formatting issues.

    Features:
    - Document structure analysis
    - Typography quality assessment
    - Table and figure formatting validation
    - LaTeX best practices checking
    """

    def __init__(self):
        """Initialize the LaTeX analyzer."""
        self.document_classes = {
            'article': {'sections': ['section', 'subsection', 'subsubsection']},
            'report': {'sections': ['chapter', 'section', 'subsection', 'subsubsection']},
            'book': {'sections': ['part', 'chapter', 'section', 'subsection', 'subsubsection']},
        }

        self.recommended_packages = {
            'typography': ['fontenc', 'inputenc', 'microtype'],
            'tables': ['booktabs', 'array', 'longtable'],
            'figures': ['graphicx', 'float', 'caption'],
            'references': ['hyperref', 'cite', 'natbib'],
            'math': ['amsmath', 'amssymb', 'amsthm']
        }

        self.deprecated_commands = [
            '\\bf', '\\it', '\\rm', '\\sc', '\\sf', '\\sl', '\\tt',
            '\\centerline', '\\over', '\\above', '\\atop'
        ]

    def analyze_document(self, latex_content: str) -> LaTeXAnalysisResult:
        """
        Perform comprehensive LaTeX document analysis.

        Args:
            latex_content: The LaTeX document content

        Returns:
            Detailed analysis results
        """
        issues = []

        # Analyze different aspects
        structure_result = self._analyze_structure(latex_content)
        typography_result = self._analyze_typography(latex_content)
        tables_figures_result = self._analyze_tables_figures(latex_content)
        best_practices_result = self._analyze_best_practices(latex_content)

        # Combine issues
        issues.extend(structure_result['issues'])
        issues.extend(typography_result['issues'])
        issues.extend(tables_figures_result['issues'])
        issues.extend(best_practices_result['issues'])

        # Calculate scores
        structure_score = structure_result['score']
        typography_score = typography_result['score']
        tables_figures_score = tables_figures_result['score']
        best_practices_score = best_practices_result['score']

        overall_score = structure_score + typography_score + tables_figures_score + best_practices_score

        # Extract document info
        doc_class = self._extract_document_class(latex_content)
        packages = self._extract_packages(latex_content)

        # Generate suggestions
        suggestions = self._generate_suggestions(issues, structure_result, typography_result)

        return LaTeXAnalysisResult(
            structure_score=structure_score,
            typography_score=typography_score,
            tables_figures_score=tables_figures_score,
            best_practices_score=best_practices_score,
            overall_score=overall_score,
            issues=issues,
            document_class=doc_class,
            packages_used=packages,
            structure_info=structure_result['info'],
            suggestions=suggestions
        )

    def _analyze_structure(self, content: str) -> Dict:
        """Analyze document structure and hierarchy."""
        issues = []
        score = 25  # Start with full points

        # Extract document class
        doc_class = self._extract_document_class(content)

        # Find all sections
        section_patterns = [
            (r'\\part\{([^}]+)\}', 'part'),
            (r'\\chapter\{([^}]+)\}', 'chapter'),
            (r'\\section\{([^}]+)\}', 'section'),
            (r'\\subsection\{([^}]+)\}', 'subsection'),
            (r'\\subsubsection\{([^}]+)\}', 'subsubsection'),
        ]

        sections_found = []
        for pattern, level in section_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                sections_found.append({
                    'level': level,
                    'title': match.group(1),
                    'line': line_num,
                    'position': match.start()
                })

        # Sort by position in document
        sections_found.sort(key=lambda x: x['position'])

        # Check section hierarchy
        hierarchy_issues = self._check_section_hierarchy(sections_found, doc_class)
        issues.extend(hierarchy_issues)
        if hierarchy_issues:
            score -= min(10, len(hierarchy_issues) * 3)

        # Check for title and author
        if not re.search(r'\\title\{', content):
            issues.append(LaTeXIssue(
                severity='warning',
                category='structure',
                description='Document is missing \\title command',
                suggestion='Add \\title{Your Title Here} in the preamble'
            ))
            score -= 3

        if not re.search(r'\\author\{', content):
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='structure',
                description='Document is missing \\author command',
                suggestion='Add \\author{Your Name} in the preamble'
            ))
            score -= 2

        # Check for proper document environment
        if not re.search(r'\\begin\{document\}', content):
            issues.append(LaTeXIssue(
                severity='error',
                category='structure',
                description='Document is missing \\begin{document}',
                suggestion='Add \\begin{document} and \\end{document}'
            ))
            score -= 10

        return {
            'score': max(0, score),
            'issues': issues,
            'info': {
                'document_class': doc_class,
                'sections_found': sections_found,
                'section_count': len(sections_found)
            }
        }

    def _analyze_typography(self, content: str) -> Dict:
        """Analyze typography and formatting quality."""
        issues = []
        score = 25  # Start with full points

        # Check for proper font encoding
        if not re.search(r'\\usepackage\[[^]]*\]\{fontenc\}', content):
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='typography',
                description='Missing font encoding package',
                suggestion='Add \\usepackage[T1]{fontenc} for better font encoding'
            ))
            score -= 2

        # Check for input encoding
        if not re.search(r'\\usepackage\[[^]]*\]\{inputenc\}', content):
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='typography',
                description='Missing input encoding package',
                suggestion='Add \\usepackage[utf8]{inputenc} for UTF-8 support'
            ))
            score -= 2

        # Check for microtype (better typography)
        if not re.search(r'\\usepackage.*\{microtype\}', content):
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='typography',
                description='Missing microtype package for better typography',
                suggestion='Add \\usepackage{microtype} for improved spacing'
            ))
            score -= 1

        # Check for proper spacing issues
        spacing_issues = [
            (r'\s{2,}', 'Multiple consecutive spaces found'),
            (r'[.!?]\w', 'Missing space after sentence ending'),
            (r'\w[.!?][.!?]', 'Multiple consecutive punctuation marks'),
        ]

        for pattern, description in spacing_issues:
            matches = list(re.finditer(pattern, content))
            if matches:
                issues.append(LaTeXIssue(
                    severity='warning',
                    category='typography',
                    description=f'{description} ({len(matches)} instances)',
                    suggestion='Fix spacing issues for better typography'
                ))
                score -= min(3, len(matches))

        # Check for proper emphasis usage
        if re.search(r'\\textit\{[^}]*\\textit\{', content):
            issues.append(LaTeXIssue(
                severity='warning',
                category='typography',
                description='Nested emphasis commands found',
                suggestion='Avoid nesting \\textit or \\textbf commands'
            ))
            score -= 2

        # Check line length (if we can detect it)
        lines = content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100 and not line.strip().startswith('%')]
        if len(long_lines) > 5:
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='typography',
                description=f'Many long lines detected ({len(long_lines)} lines > 100 chars)',
                suggestion='Consider breaking long lines for better readability'
            ))
            score -= 1

        return {
            'score': max(0, score),
            'issues': issues,
            'info': {
                'long_lines_count': len(long_lines),
                'average_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0
            }
        }

    def _analyze_tables_figures(self, content: str) -> Dict:
        """Analyze table and figure formatting."""
        issues = []
        score = 25

        # Find tables
        table_patterns = [
            r'\\begin\{tabular\}',
            r'\\begin\{table\}',
            r'\\begin\{longtable\}'
        ]

        tables_found = 0
        for pattern in table_patterns:
            tables_found += len(re.findall(pattern, content))

        # Find figures
        figure_patterns = [
            r'\\begin\{figure\}',
            r'\\includegraphics'
        ]

        figures_found = 0
        for pattern in figure_patterns:
            figures_found += len(re.findall(pattern, content))

        # Check for booktabs usage in tables
        if tables_found > 0:
            if not re.search(r'\\usepackage.*\{booktabs\}', content):
                issues.append(LaTeXIssue(
                    severity='suggestion',
                    category='tables',
                    description='Consider using booktabs package for professional tables',
                    suggestion='Add \\usepackage{booktabs} and use \\toprule, \\midrule, \\bottomrule'
                ))
                score -= 3

            # Check for old-style table rules
            if re.search(r'\\hline', content) and not re.search(r'\\(top|mid|bottom)rule', content):
                issues.append(LaTeXIssue(
                    severity='suggestion',
                    category='tables',
                    description='Using \\hline instead of booktabs rules',
                    suggestion='Replace \\hline with \\toprule, \\midrule, \\bottomrule'
                ))
                score -= 2

        # Check figure placement
        if figures_found > 0:
            if not re.search(r'\\usepackage.*\{float\}', content):
                issues.append(LaTeXIssue(
                    severity='suggestion',
                    category='figures',
                    description='Consider using float package for better figure placement',
                    suggestion='Add \\usepackage{float} for better figure control'
                ))
                score -= 1

            # Check for proper figure captions
            caption_count = len(re.findall(r'\\caption\{', content))
            if figures_found > caption_count:
                issues.append(LaTeXIssue(
                    severity='warning',
                    category='figures',
                    description=f'Some figures missing captions ({figures_found} figures, {caption_count} captions)',
                    suggestion='Add \\caption{...} to all figures'
                ))
                score -= 3

        return {
            'score': max(0, score),
            'issues': issues,
            'info': {
                'tables_found': tables_found,
                'figures_found': figures_found,
                'caption_count': caption_count if figures_found > 0 else 0
            }
        }

    def _analyze_best_practices(self, content: str) -> Dict:
        """Analyze LaTeX best practices compliance."""
        issues = []
        score = 25

        # Check for deprecated commands
        for cmd in self.deprecated_commands:
            if cmd in content:
                issues.append(LaTeXIssue(
                    severity='warning',
                    category='general',
                    description=f'Deprecated command {cmd} found',
                    suggestion=f'Replace {cmd} with modern equivalent'
                ))
                score -= 2

        # Check for proper package loading order
        hyperref_pos = content.find('\\usepackage{hyperref}')
        other_packages = re.findall(r'\\usepackage\{([^}]+)\}', content)

        if hyperref_pos != -1:
            # hyperref should generally be loaded last
            later_packages = []
            for match in re.finditer(r'\\usepackage\{([^}]+)\}', content[hyperref_pos:]):
                pkg = match.group(1)
                if pkg != 'hyperref':
                    later_packages.append(pkg)

            if later_packages:
                issues.append(LaTeXIssue(
                    severity='suggestion',
                    category='general',
                    description='hyperref package should generally be loaded last',
                    suggestion='Move \\usepackage{hyperref} to end of preamble'
                ))
                score -= 1

        # Check for proper label usage
        labels = re.findall(r'\\label\{([^}]+)\}', content)
        refs = re.findall(r'\\ref\{([^}]+)\}', content)

        unused_labels = set(labels) - set(refs)
        if unused_labels:
            issues.append(LaTeXIssue(
                severity='suggestion',
                category='general',
                description=f'Unused labels found: {", ".join(list(unused_labels)[:3])}{"..." if len(unused_labels) > 3 else ""}',
                suggestion='Remove unused \\label commands'
            ))
            score -= 1

        # Check for proper math mode usage
        inline_math_issues = re.findall(r'\$[^$]*\$\$[^$]*\$', content)
        if inline_math_issues:
            issues.append(LaTeXIssue(
                severity='warning',
                category='general',
                description='Possible incorrect math mode usage ($ mixed with $$)',
                suggestion='Use consistent math delimiters: $ for inline, $$ or \\[ \\] for display'
            ))
            score -= 2

        return {
            'score': max(0, score),
            'issues': issues,
            'info': {
                'packages_count': len(other_packages),
                'labels_count': len(labels),
                'refs_count': len(refs),
                'unused_labels': list(unused_labels)
            }
        }

    def _extract_document_class(self, content: str) -> str:
        """Extract document class from LaTeX content."""
        match = re.search(r'\\documentclass(?:\[[^]]*\])?\{([^}]+)\}', content)
        return match.group(1) if match else 'unknown'

    def _extract_packages(self, content: str) -> List[str]:
        """Extract all packages used in the document."""
        return re.findall(r'\\usepackage(?:\[[^]]*\])?\{([^}]+)\}', content)

    def _check_section_hierarchy(self, sections: List[Dict], doc_class: str) -> List[LaTeXIssue]:
        """Check if section hierarchy is logical."""
        issues = []

        if not sections:
            return issues

        # Define hierarchy levels
        hierarchy = {
            'article': ['section', 'subsection', 'subsubsection'],
            'report': ['chapter', 'section', 'subsection', 'subsubsection'],
            'book': ['part', 'chapter', 'section', 'subsection', 'subsubsection']
        }

        expected_hierarchy = hierarchy.get(doc_class, hierarchy['article'])

        # Check for proper nesting
        prev_level_index = -1
        for section in sections:
            level = section['level']
            if level in expected_hierarchy:
                level_index = expected_hierarchy.index(level)

                # Check if we're skipping levels
                if level_index > prev_level_index + 1:
                    issues.append(LaTeXIssue(
                        severity='warning',
                        category='structure',
                        description=f'Section hierarchy skip detected at "{section["title"]}"',
                        line_number=section['line'],
                        suggestion='Consider adding intermediate section levels'
                    ))

                prev_level_index = level_index

        return issues

    def _generate_suggestions(self, issues: List[LaTeXIssue], structure_result: Dict, typography_result: Dict) -> List[str]:
        """Generate overall improvement suggestions."""
        suggestions = []

        # Priority suggestions based on severity
        error_count = sum(1 for issue in issues if issue.severity == 'error')
        warning_count = sum(1 for issue in issues if issue.severity == 'warning')

        if error_count > 0:
            suggestions.append(f"Fix {error_count} critical LaTeX errors for compilation")

        if warning_count > 0:
            suggestions.append(f"Address {warning_count} formatting warnings for better quality")

        # Specific recommendations
        if structure_result['score'] < 20:
            suggestions.append("Improve document structure and section organization")

        if typography_result['score'] < 20:
            suggestions.append("Enhance typography with proper packages and spacing")

        # Package recommendations
        common_packages = ['booktabs', 'microtype', 'hyperref']
        missing_packages = [pkg for pkg in common_packages if not any(pkg in issue.description for issue in issues)]

        if len(missing_packages) > 1:
            suggestions.append(f"Consider adding packages: {', '.join(missing_packages)}")

        return suggestions[:5]  # Limit to top 5 suggestions
