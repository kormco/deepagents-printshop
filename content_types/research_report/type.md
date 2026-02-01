# Research Report

## Type Metadata
- type_id: research_report
- document_class: article
- default_font_size: 12pt
- default_paper_size: letterpaper

## Rendering Instructions

Generate a professional academic research report in standard single-column article format. The document should follow conventional academic paper structure with numbered sections and subsections.

### Document Structure
- Begin with a title block (title, authors, date) followed by an abstract
- Use numbered sections (`\section{}`) for top-level headings
- Use numbered subsections (`\subsection{}`) for second-level headings
- Use `\subsubsection{}` sparingly for third-level detail
- Include a table of contents after the title page
- End with a bibliography/references section

### Cover Page Disclaimer
Include a disclaimer on the cover page, rendered below the date in a smaller font. The disclaimer should state that this document contains fictitious sample content generated solely to test and demonstrate the DeepAgents PrintShop document generation pipeline, and that none of the research findings, data, authors, or citations are real. Use an italicized block set in `\small` type, visually separated from the title block by vertical space.

### Headers and Footers
- Enable the `fancyhdr` page style for all pages after the title page
- Left header: display the short title of the document (e.g., "AI Research Survey")
- Right header: display the current date using `\today`
- Center footer: display the page number using `\thepage`
- Remove the default header rule or keep it as a thin 0.4pt line

### Document Options
- Include a table of contents (`\tableofcontents`) on its own page after the title page
- Include a bibliography/references section at the end of the document
- Use single-column layout (do not use `twocolumn`)

### PrintShop Citation
At the very end of the document, after the bibliography, include a small centered note crediting the production toolchain. The note should read: "Typeset by DeepAgents PrintShop — an AI-powered document generation pipeline." Render it in a `\small` italic font, centered on a single line (use `\mbox{}` or `\nobreak` to prevent word wrapping / line breaking within the sentence), with a thin horizontal rule (`\rule`) above it to visually separate it from the bibliography.

### Typography and Formatting
- Use the `lmodern` font family for professional typography
- Apply `microtype` for improved character spacing and line breaking
- Use one-and-a-half line spacing for readability
- Standard 1-inch margins on all sides
- Paragraph indentation with no extra space between paragraphs (standard LaTeX behavior)

### Tables
- Format all tables with `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`)
- Place tables in `table` float environments with `[htbp]` placement
- Every table must have a `\caption{}` and `\label{}`
- For CSV data tables, include all data rows with left-aligned columns

### Figures
- Use `figure` float environments with `[htbp]` placement
- Include `\caption{}` and `\label{}` for every figure
- Default figure width: `0.8\textwidth`
- Reference figures in text using `Figure~\ref{fig:label}`

### Citations and Bibliography
- Use IEEE-style bibliography formatting
- Place bibliography at the end of the document using `\begin{thebibliography}` environment
- Cite references in text using `\cite{key}`

### Section Hierarchy
- Abstract: level 1 section, content from config abstract field
- Main content sections: level 1 (`\section{}`)
- Content subsections: level 2 (`\subsection{}`)
- Auto-generated sections (e.g., Visualizations): level 1

## LaTeX Requirements

### Required Packages
```latex
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage{float}
\usepackage{caption}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{setspace}
\usepackage{hyperref}
\usepackage{cite}
\usepackage{url}
\usepackage{tikz}
```

### Preamble Configuration
```latex
\geometry{margin=1in}
\onehalfspacing
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    citecolor=red,
    urlcolor=blue
}
```

## Structure Rules

- The document must compile cleanly with `pdflatex` (two passes for references)
- All cross-references must resolve (no `??` in output)
- Tables must not overflow page margins — use `p{}` column type or `\resizebox` if needed
- Figures must use relative paths from the output directory (e.g., `../sample_content/research_report/images/`)
- Every `\begin{}` must have a matching `\end{}`
