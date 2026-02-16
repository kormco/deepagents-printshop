# IEEE Conference Proceedings

## Type Metadata
- type_id: ieee_conference
- document_class: IEEEtran
- default_class_options: conference
- default_font_size: 10pt
- default_paper_size: letterpaper

## Rendering Instructions

Generate a professional IEEE conference proceedings paper using the `IEEEtran` document class in conference mode. The document must strictly follow IEEE formatting guidelines — do not alter margins, column widths, line spacing, or fonts from the class defaults.

This guidance is derived from the official IEEEtran HOWTO (Michael Shell, "How to Use the IEEEtran LaTeX Class," v1.8b+) and the IEEE conference template (June 2024).

### Document Class Declaration
```latex
\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
```

The `conference` option produces the standard two-column IEEE conference format. `\IEEEoverridecommandlockouts` is required to allow certain title page customizations such as `\thanks` footnotes. Without it, commands like `\thanks`, `\IEEEPARstart`, `\IEEEbiography`, `\IEEEpubid`, and `\IEEEpubidadjcol` are intentionally disabled.

#### Conference Mode Behavior

Conference mode makes several significant changes to IEEEtran's behavior:

- **Margins**: Text height is increased to ~9.25in. The bottom margin is larger than the top (IEEE wants extra clearance at the bottom). Margins are symmetric (no one-sided/two-sided difference).
- **No headers or footers**: Headings and page numbers are NOT displayed. `\markboth{}{}` has no effect.
- **Author area**: The `\author{}` content is placed within a modified **tabular environment** to enable multicolumn formatting of author names and affiliations. This is why `\and` creates new columns.
- **Spacing**: Spacing after authors' names and around section names is reduced.
- **Figure captions**: Centered (not left-aligned as in journal mode).
- **Special paper notice**: Appears BETWEEN author names and title (not after as in journal mode).
- **Camera-ready reminders**: Warning notices are enabled.
- **Last page**: Equalize columns on the last page (see Section XIV guidance below).

### Title

```latex
\title{A Heuristic Coconut-based Algorithm}
```

- Titles are generally capitalized except for words like: a, an, and, as, at, but, by, for, in, nor, of, on, or, the, to, and up (unless they are the first or last word).
- Line breaks (`\\`) may be used to equalize title line lengths.
- Do NOT use math or special symbols in the title.

### Author Block

#### Standard multicolumn format (3 or fewer affiliations)

In conference mode, the `\author{}` content is placed in a tabular environment. Use `\IEEEauthorblockN{}` for names and `\IEEEauthorblockA{}` for affiliations. Use `\and` to separate author columns. IEEEtran automatically arranges authors in rows of 3. The columns are automatically centered with respect to each other and the side margins.

Each affiliation block MUST be kept to exactly 4 lines (department, organization, city/country, email) to fit within the column width.

```latex
\author{\IEEEauthorblockN{1\textsuperscript{st} Given Name Surname}
\IEEEauthorblockA{\textit{dept. name of organization (of Aff.)} \\
\textit{name of organization (of Aff.)}\\
City, Country \\
email address or ORCID}
\and
\IEEEauthorblockN{2\textsuperscript{nd} Given Name Surname}
\IEEEauthorblockA{\textit{dept. name of organization (of Aff.)} \\
\textit{name of organization (of Aff.)}\\
City, Country \\
email address or ORCID}
\and
\IEEEauthorblockN{3\textsuperscript{rd} Given Name Surname}
\IEEEauthorblockA{\textit{dept. name of organization (of Aff.)} \\
\textit{name of organization (of Aff.)}\\
City, Country \\
email address or ORCID}
}
```

**Rules for keeping author blocks compact (prevents column overflow)**:
- Each `\IEEEauthorblockA` MUST have exactly 4 lines: department, organization, city/country, email
- Abbreviate long department names (e.g., "Dept. of Computer Science" not "Department of Computer Science")
- Keep each line under ~35 characters — if a name is too long, abbreviate it
- Do NOT add extra lines (no zip codes, no phone numbers, no second department)
- Use `\textit{}` for department and organization lines (IEEE convention)
- It is not necessary to prevent spaces from being between the `\IEEEauthorblock`'s because each block starts a new group of lines and LaTeX will ignore spaces at the very end and beginning of lines.

#### Alternate long format (4+ authors or when columns too wide)

If there are more than three authors and/or the text is too wide to fit across the page, use the `\IEEEauthorrefmark{}` alternate long format. This command generates a footnote symbol corresponding to the number in its argument, linking author names to their respective affiliations:

```latex
\author{\IEEEauthorblockN{Michael Shell\IEEEauthorrefmark{1},
Homer Simpson\IEEEauthorrefmark{2},
James Kirk\IEEEauthorrefmark{3},
Montgomery Scott\IEEEauthorrefmark{3}
and Eldon Tyrell\IEEEauthorrefmark{4}}
\IEEEauthorblockA{\IEEEauthorrefmark{1}School of Electrical and
Computer Engineering\\
Georgia Institute of Technology, Atlanta, Georgia 30332--0250\\
Email: mshell@ece.gatech.edu}
\IEEEauthorblockA{\IEEEauthorrefmark{2}Twentieth Century Fox,
Springfield, USA\\
Email: homer@thesimpsons.com}
\IEEEauthorblockA{\IEEEauthorrefmark{3}Starfleet Academy,
San Francisco, California 96678-2391\\
Telephone: (800) 555--1212, Fax: (888) 555--1212}
\IEEEauthorblockA{\IEEEauthorrefmark{4}Tyrell Inc.,
123 Replicant Street, Los Angeles, California 90210--4321}}
```

**IMPORTANT**: When using `\IEEEauthorrefmark`, each `\IEEEauthorblockA` block will render as a separate centered line (not side-by-side columns). This is the correct behavior for the long format.

#### `\thanks{}` footnotes

- **CRITICAL: `\thanks{}` MUST be placed INSIDE the `\author{}` block** — placing it outside `\author{}` causes a blank first page in conference mode. Attach it to the first author's `\IEEEauthorblockA`, typically after the email line.
- The `\thanks` command produces "first footnotes" on the title page.
- Because `\thanks` was not designed for multiple paragraphs, use a separate `\thanks` for each paragraph.
- Regular line breaks (`\\`) can be used within `\thanks`.
- Use nonbreaking spaces (`~`) to keep name/membership pairs together.
- Funding acknowledgments go in `\thanks{}` within the first author block.

Example with `\thanks` correctly placed:
```latex
\author{\IEEEauthorblockN{First Author}
\IEEEauthorblockA{\textit{Dept. of CS} \\
\textit{University}\\
City, Country \\
email@example.com}
\thanks{This work was supported by Grant No. 123.}
\and
\IEEEauthorblockN{Second Author}
\IEEEauthorblockA{\textit{Dept. of EE} \\
\textit{University}\\
City, Country \\
email2@example.com}
}
```

### Abstract and Keywords

```latex
\begin{abstract}
We propose ...
\end{abstract}

\begin{IEEEkeywords}
component, formatting, style, styling, insert
\end{IEEEkeywords}
```

- The abstract is the first part of the paper after `\maketitle`.
- Keep the abstract to 150–250 words.
- Math, special symbols, and citations should generally NOT be used in abstracts.
- Do NOT use math or special symbols in the keywords.
- In conference mode, the abstract and keywords appear in the standard two-column position (first column of main text before the first section).

### Document Structure (Sections)

Sections are declared via `\section`, `\subsection`, `\subsubsection`, and `\paragraph`.

- `\section{}` — Top-level headings, numbered as **Roman numerals** (I, II, III...).
- `\subsection{}` — Second-level headings, numbered as **uppercase letters** (A, B, C...).
- `\subsubsection{}` — Third-level headings, numbered as **Arabic numerals** (1, 2, 3...). Use sparingly.
- `\paragraph` — Not permitted for conference papers (section nesting too deep).

Typical IEEE conference paper sections:
1. Introduction
2. Related Work / Background
3. Proposed Method / System Design
4. Experimental Setup
5. Results and Discussion
6. Conclusion
7. References

- Do NOT include a table of contents — IEEE conference papers never have one.
- Do NOT include headers or footers — the `IEEEtran` class handles page formatting, and conference mode disables them entirely.
- Acknowledgments use `\section*{Acknowledgment}` (unnumbered, singular "Acknowledgment" per IEEE style). Note: IEEE Computer Society papers typically use the plural "Acknowledgments."

### Typography and Formatting

- The `IEEEtran` class enforces **10pt Times Roman font** in two-column layout. Do NOT override these.
- Do NOT add custom geometry, margin, or spacing packages — the class handles all layout.
- Do NOT use `\onehalfspacing`, `\doublespacing`, or any spacing overrides.
- Do NOT use `fancyhdr` — the class manages headers/footers internally.
- Paragraphs use standard LaTeX indentation with no extra vertical space.
- IEEEtran normally alters the default interword spacing to reduce hyphenation, producing more pleasant text for two-column format.

### Citations

```latex
\usepackage{cite}
```

- Use `\cite{}` for citations — IEEEtran produces numbered references in square brackets `[1]`.
- The base IEEEtran does NOT sort or compress citation ranges. Load the `cite` package (Donald Arseneau's cite.sty) to automatically sort and compress adjacent citation numbers into ranges (e.g., `[1], [2], [3]` becomes `[1]--[3]`).
- Multiple adjacent citations should always be declared within a single `\cite{}`, comma separated (e.g., `\cite{ref1,ref2,ref3}`) for sorting/compression to work.
- cite.sty's `\cite` may add a leading space. To prevent unwanted leading spaces when a citation follows non-space punctuation, use the `noadjust` option: `\usepackage[noadjust]{cite}`.
- `\cite` allows an optional note (e.g., `\cite[Th. 7.1]{mshell01}`). If the `\cite` with note has more than one reference, the note will be applied to the last reference. Only one reference should be listed per noted `\cite`.

### Equations

- Equations are created with the standard `equation` environment. Use `displaymath` if no equation number is desired.
- Reference equations by enclosing the equation number in parentheses: `(\ref{eqn_example})`. IEEE publications do not typically use the word "equation" — they reference by number in parentheses.
- **Use `amsmath` instead of `eqnarray`**. The `eqnarray` environment has serious shortcomings:
  1. Uses `2\arraycolsep` for column separation, providing unnatural math spacing.
  2. Column definitions cannot be altered.
  3. Limited to three alignment columns.
  4. Column alignment cannot be overridden within individual cells.
  The `amsmath` package (with `align`, `gather`, `multline`, etc.) is vastly superior.
- When loading amsmath, it will disallow page breaks within multiline equations. To restore IEEEtran's ability to break within multiline equations, add: `\interdisplaylinepenalty=2500`
- **Column width constraint**: IEEE's two-column format puts serious constraints on equation width. It is the author's responsibility to ensure all equations fit within the column width. Break over-length equations across multiple lines. In rare cases, double-column equations (using `figure*`) are acceptable, but most should be broken to fit.
- Number only equations that are referenced in the text.
- For multiline equations, prefer `align` (from `amsmath`) over `eqnarray`.

### Floating Structures (General)

Authors should keep in mind when choosing float placement:
- Most IEEE journals strongly favor positioning floats to the **top** of the page and rarely, if ever, use bottom floats.
- IEEE Computer Society journals also favor top floats but do occasionally employ bottom floats.
- IEEE journals never place floats in the first column of the first page and rarely (if ever) in the second column of the first page.
- Middle in-text placement ("here") is usually not used for IEEE work — with one notable exception: IEEE Computer Society conferences.
- LaTeX's float routine places footnotes above bottom floats. The `stfloats` package's `\fnbelowfloat` command can change this.
- **CRITICAL — Consecutive floats**: When multiple tables or figures appear within the same section or adjacent sections, LaTeX's float algorithm will stack them all at the top of the same column, causing them to collide and overlap. **Prevention rules:**
  1. Never place two `[!t]` floats within 20 lines of each other in the source.
  2. If two floats must appear close together, make the first `[!t]` and the second `[htbp]` — this lets LaTeX place the second one wherever it fits.
  3. A full paragraph of body text between floats is necessary but NOT sufficient — LaTeX may still defer both to the top. You MUST alternate the placement specifier.
  4. For three or more floats in a results section, use the pattern: `[!t]`, `[htbp]`, `[!t]`, `[htbp]`, etc.

### Figures

```latex
\begin{figure}[!t]
\centering
\includegraphics[width=2.5in]{myfigure}
\caption{Simulation results for the network.}
\label{fig_sim}
\end{figure}
```

- Use `figure` float environments with `[!t]` or `[htbp]` placement. Prefer `[!t]` (top of page) for IEEE style.
- **Use `\centering`, NOT the `center` environment** — `center` adds unwanted vertical spacing.
- Captions go **BELOW** the figure (opposite of tables).
- **CRITICAL: `\label` must be placed after (or within) `\caption`** — this is one of the most frequent LaTeX mistakes. `\caption` is what sets up the reference counter. A `\label` placed before `\caption` will refer to the section number, not the figure/table number.
- In IEEE conference papers, use the abbreviation **"Fig."** when referencing figures: `Fig.~\ref{fig:label}`. (Note: IEEE Computer Society conference papers use the full word "Figure".) IEEEtran provides the `\figurename` macro with the correct name for the given formatting mode.
- Single-column figures: `width=\columnwidth`.
- Full-width figures: Use `figure*` environment with `width=\textwidth`.
- Every figure must have a `\caption{}` and `\label{}`.
- The `\includegraphics` command (from `graphicx` package) is the preferred way to include images. Use the `graphics` or `graphicx` package (the latter is recommended).
- **Use vector graphics** (EPS/PDF) for drawings, graphs, charts. Use bitmap (JPEG/PNG) only for photos. Other formats (BMP, EMF, VSD) are unacceptable for IEEE journals. The IEEE recommends EPS/PDF for portable import into pdfLaTeX.
- **PREFER inline TikZ/pgfplots** for diagrams and charts — generate them directly in the LaTeX source so they compile as part of the document pipeline. Only use `\includegraphics` for raster images (photos, screenshots) that cannot be reproduced programmatically.
- For inline figures, consult the sample content's `images/README.md` for descriptions, data, and placement guidance for each figure.

#### Subfigures

Multiple subfigures that require more width than a single column are often placed within the `figure*` environment. Use the `subfig` package (not the deprecated `subfigure` package):

```latex
\begin{figure*}[!t]
\centering
\subfloat[Case I]{\includegraphics[width=2.5in]{subfigcase1}
\label{fig_first_case}}
\hfil
\subfloat[Case II]{\includegraphics[width=2.5in]{subfigcase2}
\label{fig_second_case}}
\caption{Simulation results for the network.}
\label{fig_sim}
\end{figure*}
```

If using `subfig`, load it with `caption=false` to prevent it from overriding IEEEtran's caption formatting:
```latex
\usepackage[caption=false,font=footnotesize]{subfig}
```

#### TikZ Diagram Layout for Two-Column Format
- **Design for column width first**: The single column is ~3.5in (252pt) wide. Design diagrams to fit this constraint by default.
- **Prefer vertical or wrapped layouts**: For flowcharts, pipelines, and multi-stage diagrams, stack nodes vertically or wrap into multiple rows rather than using long horizontal chains. A 3-stage pipeline can flow top-to-bottom; a 6-stage pipeline can wrap into 2 rows of 3.
- **When to use `figure*`**: Only use full-width figures for content that genuinely requires horizontal space (wide comparison charts, side-by-side architectures, matrices). Don't use `figure*` just because a horizontal layout was chosen.
- **Scaling**: Use `[scale=0.8]` or similar on `tikzpicture` for fine-tuning, but redesign the layout if scaling below 0.6 is needed (text becomes illegible).
- **Fallback**: `\resizebox{\columnwidth}{!}{...}` can force-fit a diagram but degrades text quality; prefer layout redesign.

### Tables

```latex
\begin{table}[!t]
\renewcommand{\arraystretch}{1.3}
\caption{A Simple Example Table}
\label{table_example}
\centering
\begin{tabular}{c||c}
\hline
\bfseries First & \bfseries Next\\
\hline\hline
1.0 & 2.0\\
\hline
\end{tabular}
\end{table}
```

- **Captions go ABOVE the table** (`\caption{}` before `\begin{tabular}`) — opposite of figures. Table captions serve much like titles and are usually capitalized using the same rules as titles.
- Place tables in `table` float environments with `[!t]` or `[htbp]` placement. Prefer `[!t]`.
- Every table must have a `\caption{}` and `\label{}`.
- **`\label` must be placed after (or within) `\caption`** — same critical rule as figures.
- **Use `\renewcommand{\arraystretch}{1.3}`** inside the table environment to "open up" the rows slightly. This is standard IEEE practice for tables.
- The default text size in tables is footnotesize. IEEE typically uses footnote-sized text in tables.
- **Units in captions**: Use `\upshape` for units and non-italic text in table captions to prevent case changes. Example: `\caption{Diagnosis of Rotor Faults in a DRFOC Drive Using the VCT(Flux Loop Bandwidth (FLB) = 10 {\upshape Hz}; 75\% Load; 1450 {\upshape r/min})}`
- **Open-sided tables preferred**: IEEE often uses tables without vertical lines along each side ("open sides"), though closed-side forms are also acceptable.
- Use `\begin{table}` (not `table*`) to keep tables within a single column, or `\begin{table*}` for full-width tables spanning both columns.
- Format all tables with `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`) as the preferred modern style, OR use traditional `\hline` rules.

#### Table Sizing for Two-Column Layout
- **Column count guideline**: Tables with 3 or fewer data columns typically fit in single column; 4+ columns often need adjustments.
- **Fitting strategies** (in order of preference):
  1. Abbreviate headers (e.g., "Acc." for "Accuracy", "Proc." for "Processing")
  2. Use `\small` or `\footnotesize` inside the table environment
  3. Use `\resizebox{\columnwidth}{!}{\begin{tabular}...}` for slight overflows (<20pt)
  4. Switch to `table*` for genuinely wide data that cannot be condensed
- **Math in cells**: Expressions like `$\pm$`, subscripts, and `\textbf{}` add width; account for this.
- Prefer splitting very wide tables into multiple focused tables over forcing everything into one.

#### Footnotes Within Tables

Footnotes cannot be placed directly within `tabular` environments (they become "trapped"). Solutions:
1. Split the `\footnotemark` (inside the table) from `\footnotetext` (outside the table).
2. Use the `footnote` package with `\makesavenoteenv{tabular}`.
3. Enclose `tabular` in a minipage (no extra package needed) — footnote appears at end of table instead of page bottom.
4. Use the `threeparttable` package (recommended for IEEE) — generates table notes directly below the table.

### Double Column Floats

- `figure*` and `table*` produce figures and tables that span both columns.
- **LaTeX kernel limitation**: Double column floats **cannot be placed at the bottom** of pages. `\begin{figure*}[!b]` will not work as intended. Authors needing this capability should use the `stfloats` package.
- Double column floats will not appear on the same page where they are defined — define them on the page *prior* to where they should appear.
- LaTeX does not attempt to keep double and single column floats in sequence. Load the `fixltx2e` package (or `dblfloatfix`) to fix this.
- Double column floats can cause underfull vbox errors because the remaining text height may not equal an integer number of normal size lines. Insert `\vspace*{-3pt}` (adjusted as needed) within the double column structure to compensate.

### Algorithms

- IEEE publications use the **`figure` environment** to contain algorithms — do NOT use the floating `algorithm.sty` or `algorithm2e.sty` environments, as IEEEtran will not be in control of their (non-IEEE) caption style.
- Use the `algorithmic` package (Peter Williams and Rogerio Brito) or `algorithmicx` package (Szasz Janos) for the pseudocode content within a figure.

```latex
\begin{figure}[!t]
\caption{My Algorithm}
\label{alg:example}
\begin{algorithmic}[1]
\STATE Initialize $x = 0$
\WHILE{$x < n$}
\STATE Process($x$)
\STATE $x \gets x + 1$
\ENDWHILE
\end{algorithmic}
\end{figure}
```

### Lists

IEEEtran provides enhanced IED (itemize, enumerate, description) list environments that produce IEEE-style lists. Key differences from standard LaTeX lists:

- IEEEtran uses `\IEEElabelindent` (indentation from left margin to label box) instead of LaTeX's `\leftmargin`-based positioning.
- The default indentation decreases with nesting depth (1st level: full, 2nd level: 75%, 3rd+: 0%).
- **IEEEtran list aliases**: `IEEEitemize`, `IEEEenumerate`, and `IEEEdescription` provide access to IEEEtran's list environments even if another package overrides the standard names.
- For enumerated lists with more than 9 items, manually set the label width: `\begin{enumerate}[\IEEEsetlabelwidth{12}]`.

### Bibliography

```latex
\begin{thebibliography}{00}
\bibitem{ref1} Author initials. Last, ``Title,'' \textit{Journal}, vol. X, no. Y, pp. Z--W, Month Year.
\bibitem{ref2} Author initials. Last, ``Title,'' in \textit{Proc. Conference Name}, City, Country, Year, pp. Z--W.
\end{thebibliography}
```

- Use `\begin{thebibliography}{00}` environment at the end of the paper.
- Each entry uses `\bibitem{key}` format.
- When submitting the .tex file, it is strongly recommended that the BibTeX .bbl file be **manually copied into the document** (within `thebibliography`) so as not to depend on external files.
- Follow IEEE reference formatting:
  - Journal articles: Author initials. Last, "Title," *Journal*, vol. X, no. Y, pp. Z--W, Month Year.
  - Conference papers: Author initials. Last, "Title," in *Proc. Conference Name*, City, Country, Year, pp. Z--W.
  - Books: Author initials. Last, *Title*. City, Country: Publisher, Year.
- Order references by first citation appearance in the text.

### Last Page Column Equalization

The IEEE coarsely equalizes column lengths on the last page. This is especially important for camera-ready work.

- Use `\newpage` at the appropriate point, OR
- Use `\enlargethispage{-X.Yin}` somewhere at the top of the first column of the last page (where "X.Y in" shortens the text height of that page).
- Sometimes the command must be located between bibliography entries. IEEEtran offers `\IEEEtriggeratref{N}` to invoke a command just before reference number N. For example: `\IEEEtriggeratref{10}` will insert a `\newpage` before reference 10. The triggered command can be changed via `\IEEEtriggercmd{\enlargethispage{-5.35in}}`.

### Page Limits
- IEEE conference papers are typically limited to 6--8 pages including references.
- Generate content that would fit within 6 pages in the final two-column format.

## LaTeX Requirements

### Required Packages
```latex
\IEEEoverridecommandlockouts
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

After loading amsmath, add this to restore IEEEtran's ability to break within multiline equations:
```latex
\usepackage{amsmath,amssymb,amsfonts}
\interdisplaylinepenalty=2500
```

### Packages to AVOID
Do NOT include any of these — they conflict with or are unnecessary for `IEEEtran`:
- `geometry` (IEEEtran manages margins)
- `fancyhdr` (IEEEtran manages headers)
- `setspace` (IEEEtran manages line spacing)
- `fontenc` / `inputenc` / `lmodern` (IEEEtran manages fonts — do not attempt to use pslatex, mathptm, etc.)
- `caption` (IEEEtran provides its own caption formatting)
- `multicol` (IEEEtran handles two-column layout internally)
- `algorithm` / `algorithm2e` (use `figure` environment instead — IEEEtran cannot control their caption style)
- `subfigure` (deprecated; use `subfig` with `caption=false` if needed)
- `psfig`, `epsfig` (obsolete graphics interfaces)

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

## Common Mistakes to Avoid

These are the most frequently encountered mistakes (from IEEEtran HOWTO Appendix D):

1. **Placing `\label` before `\caption`**: `\label` must be placed after or within `\caption`. It is `\caption` that sets up the reference counter — a `\label` before it will refer to the section number, not the figure/table number.

2. **Altering default fonts**: Let IEEEtran manage fonts. Do not load packages like pslatex, mathptm, etc. unless specifically instructed by the conference.

3. **Altering default spacings, section heading styles, margins, or column style**: Do not manually alter margins, paper size, or use packages like geometry.sty. There should be no need to add spacing around figures, equations, etc.

4. **Using bitmapped graphics for line art**: Use vector (EPS/PDF) format for drawings, graphs, charts. Bitmap (JPEG/PNG) should only be used for photos. Vector graphics can be scaled and magnified without degradation.

5. **Using bitmapped fonts and/or not embedding all document fonts**: Ensure only vector (Type 1) fonts are used and all fonts are embedded and subsetted. A document that uses bitmapped fonts may be rejected by the IEEE.

6. **Using older graphics packages**: Do not use `psfig`, `epsfig`, etc. — they have been obsolete for many years. Use `graphicx`.

7. **Failing to properly divide long equations**: It is the author's responsibility to ensure all equations fit within the column width. Use subfunctions to reduce width; do not alter the math font size.

8. **Manually formatting references**: Use the `thebibliography` environment with `\bibitem{}`. Follow IEEE reference formatting conventions consistently.

9. **Placing `\thanks{}` outside `\author{}`**: In conference mode, a `\thanks{}` command that appears AFTER the closing `}` of `\author{}` will produce a blank first page. Always place `\thanks{}` inside the `\author{}` block, attached to the first author's affiliation block.
