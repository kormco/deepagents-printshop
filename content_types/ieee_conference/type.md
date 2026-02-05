# IEEE Conference Proceedings

## Type Metadata
- type_id: ieee_conference
- document_class: IEEEtran
- default_font_size: 10pt
- default_paper_size: letterpaper

## Rendering Instructions

Generate a professional IEEE conference proceedings paper using the `IEEEtran` document class in conference mode. The document must strictly follow IEEE formatting guidelines — do not alter margins, column widths, line spacing, or fonts from the class defaults.

### Document Class Declaration
```latex
\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
```

The `conference` option produces the standard two-column IEEE conference format. `\IEEEoverridecommandlockouts` is required to allow certain title page customizations such as `\thanks` footnotes.

### Title and Author Block
- Use `\title{}` for the paper title. Do NOT use special characters, footnotes, or math in the title.
- Use `\author{}` with `\IEEEauthorblockN{}` for author names and `\IEEEauthorblockA{}` for affiliations (department, university/organization, city, country, email).
- Multiple author groups can be arranged side-by-side using `\and`.
- Funding acknowledgments go in `\thanks{}` within the first author block.

Example:
```latex
\author{
  \IEEEauthorblockN{First Author}
  \IEEEauthorblockA{
    \textit{Department of Computer Science} \\
    \textit{University Name} \\
    City, Country \\
    email@example.org
  }
  \and
  \IEEEauthorblockN{Second Author}
  \IEEEauthorblockA{
    \textit{Department of Engineering} \\
    \textit{Another University} \\
    City, Country \\
    email2@example.org
  }
}
```

### Abstract and Keywords
- Use `\begin{abstract}` environment immediately after `\maketitle`.
- Keep the abstract to 150–250 words. Do NOT use special characters or math in the abstract.
- Follow the abstract with `\begin{IEEEkeywords}` for a comma-separated keyword list.

### Document Structure
- Use `\section{}` for top-level headings (automatically numbered as Roman numerals: I, II, III...).
- Use `\subsection{}` for second-level headings (A, B, C...).
- Use `\subsubsection{}` sparingly for third-level headings.
- Typical IEEE conference paper sections:
  1. Introduction
  2. Related Work / Background
  3. Proposed Method / System Design
  4. Experimental Setup
  5. Results and Discussion
  6. Conclusion
  7. References
- Do NOT include a table of contents — IEEE conference papers never have one.
- Do NOT include headers or footers — the `IEEEtran` class handles page formatting.

### Typography and Formatting
- The `IEEEtran` class enforces 10pt Times Roman font in two-column layout. Do NOT override these.
- Do NOT add custom geometry, margin, or spacing packages — the class handles all layout.
- Do NOT use `\onehalfspacing`, `\doublespacing`, or any spacing overrides.
- Do NOT use `fancyhdr` — the class manages headers/footers internally.
- Paragraphs use standard LaTeX indentation with no extra vertical space.

### Equations
- Use `align` environment (from `amsmath`) instead of `eqnarray`.
- Reference equations using `\eqref{}` (produces parenthesized numbers).
- Number only equations that are referenced in the text.

### Tables
- Format all tables with `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`).
- Place tables in `table` float environments with `[htbp]` or `[t]` placement.
- Captions go ABOVE the table (`\caption{}` before `\begin{tabular}`).
- Every table must have a `\caption{}` and `\label{}`.
- Use `\begin{table}` (not `table*`) to keep tables within a single column, or `\begin{table*}` for full-width tables spanning both columns.

#### Table Sizing for Two-Column Layout
- **Column count guideline**: Tables with ≤3 data columns typically fit in single column; 4+ columns often need adjustments.
- **Fitting strategies** (in order of preference):
  1. Abbreviate headers (e.g., "Acc." for "Accuracy", "Proc." for "Processing")
  2. Use `\small` or `\footnotesize` inside the table environment
  3. Use `\resizebox{\columnwidth}{!}{\begin{tabular}...}` for slight overflows (<20pt)
  4. Switch to `table*` for genuinely wide data that cannot be condensed
- **Math in cells**: Expressions like `$\pm$`, subscripts, and `\textbf{}` add width; account for this.
- Prefer splitting very wide tables into multiple focused tables over forcing everything into one.

### Figures
- Use `figure` float environments with `[htbp]` or `[t]` placement.
- Captions go BELOW the figure.
- Single-column figures: `width=\columnwidth`.
- Full-width figures: Use `figure*` environment with `width=\textwidth`.
- Every figure must have a `\caption{}` and `\label{}`.
- Reference figures using `Fig.~\ref{fig:label}` (IEEE style uses "Fig." abbreviation).
- **PREFER inline TikZ/pgfplots** for diagrams and charts — generate them directly in the LaTeX source so they compile as part of the document pipeline. Only use `\includegraphics` for raster images (photos, screenshots) that cannot be reproduced programmatically.
- For inline figures, consult the sample content's `images/README.md` for descriptions, data, and placement guidance for each figure.

#### TikZ Diagram Layout for Two-Column Format
- **Design for column width first**: The single column is ~3.5in (252pt) wide. Design diagrams to fit this constraint by default.
- **Prefer vertical or wrapped layouts**: For flowcharts, pipelines, and multi-stage diagrams, stack nodes vertically or wrap into multiple rows rather than using long horizontal chains. A 3-stage pipeline can flow top-to-bottom; a 6-stage pipeline can wrap into 2 rows of 3.
- **When to use `figure*`**: Only use full-width figures for content that genuinely requires horizontal space (wide comparison charts, side-by-side architectures, matrices). Don't use `figure*` just because a horizontal layout was chosen.
- **Scaling**: Use `[scale=0.8]` or similar on `tikzpicture` for fine-tuning, but redesign the layout if scaling below 0.6 is needed (text becomes illegible).
- **Fallback**: `\resizebox{\columnwidth}{!}{...}` can force-fit a diagram but degrades text quality; prefer layout redesign.

### Citations and Bibliography
- Use `\cite{}` for citations — IEEE style produces numbered references in square brackets [1].
- Use `\begin{thebibliography}{00}` environment at the end of the paper.
- Each entry uses `\bibitem{key}` format.
- Follow IEEE reference formatting:
  - Journal articles: Author initials. Last, "Title," *Journal*, vol. X, no. Y, pp. Z–W, Month Year.
  - Conference papers: Author initials. Last, "Title," in *Proc. Conference Name*, City, Country, Year, pp. Z–W.
  - Books: Author initials. Last, *Title*. City, Country: Publisher, Year.
- Order references by first citation appearance in the text.

### Algorithms
- Use `algorithmic` package for pseudocode.
- Wrap in `algorithm` float environment with caption.

### Page Limits
- IEEE conference papers are typically limited to 6–8 pages including references.
- Generate content that would fit within 6 pages in the final two-column format.

## LaTeX Requirements

### Required Packages
```latex
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{url}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\usetikzlibrary{shapes.geometric,arrows.meta,positioning}
```

### Packages to AVOID
Do NOT include any of these — they conflict with or are unnecessary for `IEEEtran`:
- `geometry` (IEEEtran manages margins)
- `fancyhdr` (IEEEtran manages headers)
- `setspace` (IEEEtran manages line spacing)
- `fontenc` / `inputenc` / `lmodern` (IEEEtran manages fonts)
- `caption` (IEEEtran provides its own caption formatting)
- `multicol` (IEEEtran handles two-column layout internally)

### Preamble Configuration
```latex
\hypersetup{
    colorlinks=false,
    hidelinks
}
```

Note: IEEE submissions typically require hidden hyperlinks (no colored links).

## Structure Rules

- The document must compile cleanly with `pdflatex` (two passes for references).
- All cross-references must resolve (no `??` in output).
- Watch for "Overfull \hbox" warnings during compilation — these indicate content exceeding column width. Address by redesigning layout, abbreviating content, or using `*` float environments.
- Tables must not overflow column margins — use `p{}` column type, `\resizebox`, or `table*` if needed.
- Figures must use relative paths from the output directory (e.g., `../sample_content/ieee_conference/images/`).
- Every `\begin{}` must have a matching `\end{}`.
- Do NOT exceed the equivalent of 6 typeset pages of content.
- The `IEEEtran.cls` file is provided by the TeX Live distribution and does not need to be bundled.
