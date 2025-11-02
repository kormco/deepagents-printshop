"""LaTeX document generator with comprehensive formatting support."""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentConfig:
    """Configuration for LaTeX document generation."""
    doc_class: str = "article"  # article, book, report, etc.
    font_size: str = "12pt"
    paper_size: str = "letterpaper"
    title: str = ""
    author: str = ""
    date: str = r"\today"

    # Document options
    include_toc: bool = True
    include_bibliography: bool = True
    two_column: bool = False

    # Header/Footer
    header_left: str = ""
    header_center: str = ""
    header_right: str = ""
    footer_left: str = ""
    footer_center: str = r"\thepage"
    footer_right: str = ""

    # Packages to include
    extra_packages: List[str] = field(default_factory=list)


class LaTeXGenerator:
    """Generate LaTeX documents with advanced formatting."""

    def __init__(self, config: DocumentConfig):
        self.config = config
        self.content_sections = []
        self.bibliography_entries = []

    def generate_preamble(self) -> str:
        """Generate the document preamble with packages and settings."""
        options = [self.config.font_size, self.config.paper_size]
        if self.config.two_column:
            options.append("twocolumn")

        preamble = [
            f"\\documentclass[{','.join(options)}]{{{self.config.doc_class}}}",
            "",
            "% Packages",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage{graphicx}",
            "\\usepackage{hyperref}",
            "\\usepackage{cite}",
            "\\usepackage{amsmath}",
            "\\usepackage{booktabs}",
            "\\usepackage{array}",
            "\\usepackage{float}",
            "\\usepackage{wrapfig}",
            "\\usepackage{caption}",
            "\\usepackage{subcaption}",
            "\\usepackage{geometry}",
            "\\usepackage{fancyhdr}",
            "\\usepackage{csvsimple}",
            "\\usepackage{longtable}",
            "\\usepackage{tikz}",
            "\\usepackage{xcolor}",
        ]

        # Add extra packages
        for pkg in self.config.extra_packages:
            preamble.append(f"\\usepackage{{{pkg}}}")

        # Geometry settings
        preamble.extend([
            "",
            "% Page geometry",
            "\\geometry{margin=1in}",
        ])

        # Header/Footer setup
        if any([self.config.header_left, self.config.header_center, self.config.header_right,
                self.config.footer_left, self.config.footer_center, self.config.footer_right]):
            preamble.extend([
                "",
                "% Header and Footer",
                "\\pagestyle{fancy}",
                "\\fancyhf{}",
            ])

            if self.config.header_left:
                preamble.append(f"\\fancyhead[L]{{{self.config.header_left}}}")
            if self.config.header_center:
                preamble.append(f"\\fancyhead[C]{{{self.config.header_center}}}")
            if self.config.header_right:
                preamble.append(f"\\fancyhead[R]{{{self.config.header_right}}}")
            if self.config.footer_left:
                preamble.append(f"\\fancyfoot[L]{{{self.config.footer_left}}}")
            if self.config.footer_center:
                preamble.append(f"\\fancyfoot[C]{{{self.config.footer_center}}}")
            if self.config.footer_right:
                preamble.append(f"\\fancyfoot[R]{{{self.config.footer_right}}}")

        # Hyperref settings
        preamble.extend([
            "",
            "% Hyperref settings",
            "\\hypersetup{",
            "    colorlinks=true,",
            "    linkcolor=blue,",
            "    filecolor=magenta,",
            "    urlcolor=cyan,",
            "    citecolor=blue,",
            "}",
        ])

        # Title information
        if self.config.title:
            preamble.extend([
                "",
                f"\\title{{{self.config.title}}}",
                f"\\author{{{self.config.author}}}",
                f"\\date{{{self.config.date}}}",
            ])

        return "\n".join(preamble)

    def add_section(self, title: str, content: str, level: int = 1):
        """Add a section to the document."""
        section_cmd = {
            0: "chapter",
            1: "section",
            2: "subsection",
            3: "subsubsection",
        }.get(level, "section")

        self.content_sections.append({
            "type": "section",
            "command": section_cmd,
            "title": title,
            "content": content
        })

    def add_table(self, caption: str, headers: List[str], rows: List[List[str]],
                  label: Optional[str] = None):
        """Add a formatted table to the document."""
        col_format = "l" * len(headers)

        table_content = [
            "\\begin{table}[H]",
            "\\centering",
            f"\\begin{{tabular}}{{{col_format}}}",
            "\\toprule",
            " & ".join(headers) + " \\\\",
            "\\midrule",
        ]

        for row in rows:
            table_content.append(" & ".join(row) + " \\\\")

        table_content.extend([
            "\\bottomrule",
            "\\end{tabular}",
            f"\\caption{{{caption}}}",
        ])

        if label:
            table_content.append(f"\\label{{{label}}}")

        table_content.append("\\end{table}")

        self.content_sections.append({
            "type": "table",
            "content": "\n".join(table_content)
        })

    def add_csv_table(self, caption: str, csv_file: str, label: Optional[str] = None):
        """Add a table from a CSV file."""
        table_content = [
            "\\begin{table}[H]",
            "\\centering",
            "\\csvautotabular{" + csv_file + "}",
            f"\\caption{{{caption}}}",
        ]

        if label:
            table_content.append(f"\\label{{{label}}}")

        table_content.append("\\end{table}")

        self.content_sections.append({
            "type": "csv_table",
            "content": "\n".join(table_content)
        })

    def add_figure(self, image_path: str, caption: str, width: str = "0.8\\textwidth",
                   label: Optional[str] = None):
        """Add a figure to the document."""
        figure_content = [
            "\\begin{figure}[H]",
            "\\centering",
            f"\\includegraphics[width={width}]{{{image_path}}}",
            f"\\caption{{{caption}}}",
        ]

        if label:
            figure_content.append(f"\\label{{{label}}}")

        figure_content.append("\\end{figure}")

        self.content_sections.append({
            "type": "figure",
            "content": "\n".join(figure_content)
        })

    def add_wrapped_figure(self, image_path: str, caption: str, width: str = "0.4\\textwidth",
                          position: str = "r", label: Optional[str] = None):
        """Add a figure with text wrapping."""
        figure_content = [
            f"\\begin{{wrapfigure}}{{{position}}}{{{width}}}",
            "\\centering",
            f"\\includegraphics[width={width}]{{{image_path}}}",
            f"\\caption{{{caption}}}",
        ]

        if label:
            figure_content.append(f"\\label{{{label}}}")

        figure_content.append("\\end{wrapfigure}")

        self.content_sections.append({
            "type": "wrapfigure",
            "content": "\n".join(figure_content)
        })

    def add_tikz_diagram(self, tikz_code: str, caption: str, label: Optional[str] = None):
        """Add a TikZ vector diagram."""
        figure_content = [
            "\\begin{figure}[H]",
            "\\centering",
            "\\begin{tikzpicture}",
            tikz_code,
            "\\end{tikzpicture}",
            f"\\caption{{{caption}}}",
        ]

        if label:
            figure_content.append(f"\\label{{{label}}}")

        figure_content.append("\\end{figure}")

        self.content_sections.append({
            "type": "tikz",
            "content": "\n".join(figure_content)
        })

    def add_citation(self, cite_key: str) -> str:
        """Add an inline citation reference."""
        return f"\\cite{{{cite_key}}}"

    def add_bib_entry(self, entry: str):
        """Add a bibliography entry."""
        self.bibliography_entries.append(entry)

    def add_itemize_list(self, items: List[str]):
        """Add a bulleted list."""
        list_content = ["\\begin{itemize}"]
        for item in items:
            list_content.append(f"  \\item {item}")
        list_content.append("\\end{itemize}")

        self.content_sections.append({
            "type": "list",
            "content": "\n".join(list_content)
        })

    def add_enumerate_list(self, items: List[str]):
        """Add a numbered list."""
        list_content = ["\\begin{enumerate}"]
        for item in items:
            list_content.append(f"  \\item {item}")
        list_content.append("\\end{enumerate}")

        self.content_sections.append({
            "type": "list",
            "content": "\n".join(list_content)
        })

    def add_hyperlink(self, url: str, text: Optional[str] = None) -> str:
        """Create a hyperlink."""
        if text:
            return f"\\href{{{url}}}{{{text}}}"
        else:
            return f"\\url{{{url}}}"

    def add_raw_latex(self, latex_code: str):
        """Add raw LaTeX code."""
        self.content_sections.append({
            "type": "raw",
            "content": latex_code
        })

    def generate_document(self) -> str:
        """Generate the complete LaTeX document."""
        doc = [self.generate_preamble(), "", "\\begin{document}"]

        # Title page
        if self.config.title:
            doc.extend(["", "\\maketitle"])

        # Table of contents
        if self.config.include_toc:
            doc.extend(["", "\\tableofcontents", "\\newpage"])

        # Content sections
        for section in self.content_sections:
            doc.append("")
            if section["type"] == "section":
                doc.append(f"\\{section['command']}{{{section['title']}}}")
                doc.append(section["content"])
            else:
                doc.append(section["content"])

        # Bibliography
        if self.config.include_bibliography and self.bibliography_entries:
            doc.extend([
                "",
                "\\begin{thebibliography}{99}",
            ])
            for entry in self.bibliography_entries:
                doc.append(entry)
            doc.append("\\end{thebibliography}")

        doc.extend(["", "\\end{document}"])

        return "\n".join(doc)

    def save(self, output_path: str):
        """Save the LaTeX document to a file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_document())
        return output_path


def markdown_to_latex(markdown_text: str) -> str:
    """Convert basic markdown to LaTeX."""
    latex = markdown_text

    # Bold
    import re
    latex = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', latex)
    latex = re.sub(r'__(.+?)__', r'\\textbf{\1}', latex)

    # Italic
    latex = re.sub(r'\*(.+?)\*', r'\\textit{\1}', latex)
    latex = re.sub(r'_(.+?)_', r'\\textit{\1}', latex)

    # Code
    latex = re.sub(r'`(.+?)`', r'\\texttt{\1}', latex)

    # Special characters
    latex = latex.replace('&', '\\&')
    latex = latex.replace('%', '\\%')
    latex = latex.replace('$', '\\$')
    latex = latex.replace('#', '\\#')
    latex = latex.replace('_', '\\_')
    latex = latex.replace('{', '\\{')
    latex = latex.replace('}', '\\}')

    return latex
