# Resume

## Type Metadata
- type_id: resume
- document_class: article
- default_font_size: 10pt
- default_paper_size: letterpaper
- default_theme: banker

## Rendering Instructions

### Theme Selection

This content type supports **four themes**. The theme is chosen via the `theme:` field in `config.md`. If no theme is specified, default to `banker`. The **macro contract is the same across all themes** (`\resumeheader`, `\resumesection`, `\jobentry`, `\subjobentry`, `\jobcontext`, `\skillgroup`, `\speakentry`); only the color palette, typography, and the rendered output of those macros change per theme. See the **Theme Definitions** section below for per-theme palettes and layout overrides. The body of the Rendering Instructions describes the default `banker` theme; theme-specific deviations are called out inline and consolidated under Theme Definitions.

| Theme ID | Name | Mood |
|----------|------|------|
| `banker` | Banker | Trust, capital markets, regulated industries (default) |
| `letterpress` | Letterpress | Editorial, brand-adjacent, senior creative |
| `architect` | Architect's Margin | Engineering / platform leadership — sidebar layout |
| `editorial` | Asymmetric Editorial | Creative leadership, content, comms — serif, no band |

### Overall Direction

Generate a polished, modern, single-document resume that is dense, scannable, and ATS-friendly while looking visually distinctive. The target audience is senior hiring managers and recruiters — they will skim the first half-page in seconds, then scan headers and bolded leads. Optimize for that pattern. Keep the document to **2 pages** when possible, **3 pages maximum** for senior candidates with deep history.

The resume must NOT look like an academic paper, a magazine, or a research report. It is a professional CV: clean section headers with accent color rules, tight job entries with company/role/dates aligned, bulleted accomplishments using strong verbs, and a compact skills/certifications block.

### Header (top of page 1)
- The header block sits on a **solid accent-color background band** spanning the full text width (no thin rules — the band itself is the visual weight)
- Candidate name in large bold sans-serif (24–28pt), white text on the accent background
- One-line professional title/tagline directly under the name (12pt, light/white text on the accent background)
- Contact line: city · phone · email (mailto link) · linkedin (url link) · personal site (url link)
  - Rendered in white/light text on the accent band
  - Use middle dots `·` as separators
  - Hyperlinks colored white (or a very light tint) so they remain legible on the dark band; do NOT use the default blue hyperref color inside the header
- Implement with `\colorbox{resumeaccent}{\parbox{...}{...}}` or an equivalent full-width TikZ/`tcolorbox` construct. Leave ~10pt of vertical space after the header band before the first section

### Section Headers
- Use a custom `\resumesection{NAME}` macro that renders a **full-width solid accent-color bar** with the section label in white uppercase sans-serif inside (reversed / knock-out style)
- No thin rule underneath — the solid bar IS the separator
- Bar height should be just tall enough to comfortably hold the label with ~3pt padding above and below (≈ 14–18pt total)
- Standard sections in this order (omit any that are empty):
  1. SUMMARY
  2. EXPERIENCE
  3. SELECTED PROJECTS / SPEAKING & WRITING (optional, before or after experience)
  4. EDUCATION
  5. CERTIFICATIONS
  6. SKILLS
- Keep ~6pt vertical space between sections — tight, not airy

### Job Entries
- Use a `\jobentry{Company}{Role}{Location}{Dates}` macro that produces:
  - Line 1: **Company** (bold) — Role (regular weight, same line, or wrapped if long)
  - Line 1 right-aligned: Location · Dates (gray, 9pt)
- Optional one-line context paragraph directly under the header (italic gray, 9.5pt) describing scope/mandate
- Bullets using `itemize` with `enumitem` settings:
  - `\setlist[itemize]{leftmargin=1.2em, itemsep=2pt, parsep=0pt, topsep=2pt}`
  - Use a small filled square or en-dash as the bullet marker, not the default bullet
- Bullet structure: lead with **bolded keyword or accomplishment phrase** (the thing a skimmer should catch), then concrete result with metrics where possible
- For long tenures with sub-roles, use `\subjobentry{Sub-role}{Dates}` for nested role headers (slightly smaller, indented 0.5em, no Company repeated)

### Bullet Density
- 3–6 bullets per role for recent/relevant positions
- 1–3 bullets for older/less relevant positions
- Each bullet should fit on 1–2 lines; if it spills to 3, tighten the prose
- Older roles (>10 years) can collapse to a single sentence summary with no bullets

### Skills Block
- Use a 2-column layout with `multicols` or `tabular` for the skills section
- Group skills under bolded category labels (e.g., **Leadership & Growth** — items separated by middle dots)
- Use middle dot `·` as the inline separator within a category, NOT bullets or commas
- Keep each category to 1–2 lines max

### Certifications
- Single dense paragraph or two-column list — do NOT put each certification on its own line
- Mark inactive certs with an asterisk and a short footnote at the bottom

### Education
- Compact: `\jobentry`-style with school in bold, degree on the same line, location · dates right-aligned
- Honors/notable items as a single line under, NOT as bullets

### Speaking & Writing (when present)
- Each entry: **Event/Publication Name** (bold) — short description (1–2 sentences)
- Mark upcoming/invited talks clearly

### Typography
- Use a clean modern sans-serif for headers (e.g., `\usepackage{helvet}` with `\renewcommand{\familydefault}{\sfdefault}` OR mix: serif body + sans headers via `\sffamily` in macros)
- Body font: 10pt, line spacing 1.05–1.1 (`\linespread{1.05}`)
- Accent color used SPARINGLY — section headers, the contact links, and the rules. Body text stays black/dark gray.
- NO drop caps, NO pull quotes, NO multicolumn body text (only skills section may use multicols)
- NO page numbers, NO running headers/footers — this is a CV, not an article

### Punctuation and Prose Tone
- **Use em-dashes sparingly in body prose.** The macros (`\jobentry`, `\speakentry`, `\skillgroup`) already insert one em-dash as a structural separator — adding more em-dashes inside the same sentence makes the resume feel tic-heavy and over-punctuated.
- **Hard rule: at most ONE em-dash per sentence** in body prose (summary paragraphs, bullet text, speaking descriptions). If you feel the urge to add a second em-dash, use a comma, colon, semicolon, or parentheses instead.
- **Prefer commas and colons over em-dashes** for appositives and clause joins. Reserve em-dashes for genuine emphasis / break-of-thought, not as a default joiner.
- **Never use an em-dash inside a value passed to a macro that already renders an em-dash separator.** For example, write `\speakentry{ESTO Summit: "Orchestrating AI Workflows"}{...}`, not `\speakentry{ESTO Summit --- "Orchestrating AI Workflows"}{...}` — the macro already renders one dash after the title.
- When listing parallel phases or sub-topics inside a bullet (e.g., "Phase 1" / "Phase 2"), use a colon rather than an em-dash: `\textbf{Phase 1: Crypto infrastructure.}` not `\textbf{Phase 1 --- Crypto infrastructure}:`.
- Middle dots (`\textperiodcentered{}` / `·`) are the approved separator inside skill-group item lists and tagline contact rows; em-dashes have no role there.

### Spacing and Density
- Tight is better than airy — recruiters reward density
- Use `\geometry{margin=0.55in, top=0.5in, bottom=0.5in}` for tight margins
- AVOID large empty whitespaces — if a page break leaves a half-empty page, tighten upstream content rather than padding
- Do NOT use `\vfill` or `\newpage` to force layout — let content flow

### What to AVOID
- NO cover image, NO full-bleed backgrounds, NO dark pages
- NO TikZ infographics, circle stats, or pull quotes
- NO photos of the candidate (US convention)
- NO "References available upon request" line
- NO objective statement (the summary replaces it)
- NO icons that depend on FontAwesome unless the package is in the LaTeX distribution — prefer text/Unicode middle dots

### AI-Disclosure Footer
- Every resume must include a single italic gray line in the bottom-right corner of the last page (or every page): *"Drafted with AI assistance via DeepAgents PrintShop."*
- Render at ~7pt, italic, in `resumemuted` color
- Implementation: either `\vfill\hfill\textit{...}` immediately before `\end{document}`, or `\AddToShipoutPictureFG{}` from `eso-pic` for per-page placement
- Do NOT add this in headers — footer only

## Theme Definitions

The four themes share the same macro contract and section structure. Each theme overrides the color palette, typography, and the body of the layout macros (`\resumeheader`, `\resumesection`). Pick the palette and layout from the theme matching `config.md`'s `theme:` value.

### Theme: banker (default)
- **Palette**: primary `#1F3A5F` (deep navy), accent `#6B7F9C` (light navy), page `#FFFFFF`
- **Typography**: clean sans-serif throughout (`helvet`); body 10pt, headers bold sans
- **Header**: full-width solid navy band; name in white bold sans 26pt; tagline + contact in white below — as described in the main Rendering Instructions
- **Section markers**: full-width solid navy bar with reversed white uppercase label (knock-out style)
- **Optional flair**: a single ghosted monogram of the candidate's last-name initial in the lower-right corner of page 1, ~120pt, 8–10% opacity, in the accent color, via `eso-pic`'s `\AddToShipoutPictureBG`

### Theme: letterpress
- **Palette**: primary `#1F3A5F` (navy), accent `#C8A45E` (brass), page `#FAF7F2` (warm off-white)
- **Typography**: serif body (Latin Modern Roman) + sans labels (Helvetica) for section headings only; tagline italicized in serif on the band
- **Page**: warm cream background — set with `\pagecolor{resumepage}`
- **Header**: same banded structure as banker; add a 0.6pt brass rule sitting 2pt below the navy band
- **Section markers**: navy band with white reversed label, plus the brass rule below it
- **Optional flair**: ghosted monogram in brass, lower-right
- **Tone**: classic editorial — feels like printed stationery

### Theme: architect (Architect's Margin)
- **Palette**: primary `#1F2937` (slate), accent `#84A98C` (sage), page `#FFFFFF`
- **Typography**: sans-serif throughout (Helvetica)
- **Layout**: **sidebar instead of top band.** A 1.30in solid slate sidebar runs the full height of page 1 holding the candidate's name (white sans bold), tagline (white sans), contact info (small white sans), and a ghosted sage monogram. Main content (sections + job entries) occupies the right column starting at the same top margin.
- **`\resumeheader` override**: emit the sidebar (TikZ overlay or `tcolorbox` block) instead of the full-width band
- **Section markers**: short 0.4in sage rule, then the section label in slate uppercase sans bold below it. NO full-width bar.
- **Job entries**: company in slate sans bold, role italicized in `resumemuted`; dates right-aligned in `resumemuted`
- **Bullets**: small sage filled square or sage filled circle
- **Pages 2+**: drop the sidebar — only page 1 carries it; subsequent pages use full text width with the same section-marker treatment

### Theme: editorial (Asymmetric Editorial)
- **Palette**: primary `#1A1A1A` (ink), accent `#722F37` (oxblood), page `#FBF8F1` (cream)
- **Typography**: serif (Latin Modern Roman) for the candidate name, body, and job entries; sans-serif (Helvetica) only for the small numbered section markers
- **Page**: cream background — `\pagecolor{resumepage}`
- **Header**: NO band. Candidate name in serif bold 26pt, ink color, top-left. Contact info top-right, small sans, `resumemuted`. Tagline in serif italic ~10pt directly under the name. A single 1.2pt oxblood rule across the page width separates the header from body content.
- **`\resumesection` override**: numbered (`01`, `02`, …) in oxblood sans bold, followed by the section name in ink sans bold uppercase. NO full-width bar.
- **Job entries**: company in serif bold, comma, role in italics, all in ink color; dates right-aligned in `resumemuted` italic
- **Bullets**: en-dash (`\textemdash`) in oxblood instead of a bullet glyph
- **Optional flair**: oversized ghosted serif initial of the last name in lower-right of page 1, ~140pt, 6–8% opacity, oxblood color
- **Tone**: editorial magazine profile

## LaTeX Requirements

### Required Packages
```latex
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{helvet}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage{multicol}
\usepackage{array}
\usepackage{tabularx}
\usepackage{ragged2e}
\usepackage{eso-pic}        % for ghosted monogram backgrounds
\usepackage{tikz}           % for sidebar (architect) and editorial layouts
\usepackage{fontawesome5}   % optional, only if available
```

### Color Definitions

Define `resumeaccent`, `resumeaccent2`, `resumemuted`, `resumerule`, `resumelink`, and (when the theme uses one) `resumepage`. Pick the palette from the **selected theme**. The block below is the `banker` default; for other themes substitute the theme's palette and call `\pagecolor{resumepage}` if the theme uses a non-white page color.

```latex
% --- banker (default) ---
\definecolor{resumeaccent}{HTML}{1F3A5F}   % deep navy
\definecolor{resumeaccent2}{HTML}{6B7F9C}  % light navy
\definecolor{resumemuted}{HTML}{6B7280}
\definecolor{resumerule}{HTML}{1F3A5F}
\definecolor{resumelink}{HTML}{1F3A5F}
```

Theme palette swaps:
- **letterpress**: accent `#1F3A5F` · accent2 `#C8A45E` (brass) · page `#FAF7F2` — also `\pagecolor{resumepage}`
- **architect**: accent `#1F2937` (slate) · accent2 `#84A98C` (sage) · page `#FFFFFF`
- **editorial**: accent `#1A1A1A` (ink) · accent2 `#722F37` (oxblood) · page `#FBF8F1` — also `\pagecolor{resumepage}`, switch body to serif

### Page Setup
```latex
\geometry{margin=0.55in, top=0.5in, bottom=0.5in}
\pagestyle{empty}
\linespread{1.05}
\setlength{\parindent}{0pt}
\setlength{\parskip}{2pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=2pt, parsep=0pt, topsep=2pt, label={\small\textcolor{resumeaccent}{\textbullet}}}

\hypersetup{
  colorlinks=true,
  urlcolor=resumelink,
  linkcolor=resumelink
}
```

### Custom Macro Definitions

The macro signatures are theme-agnostic — only their internal rendering changes per theme. The implementations below show the **banker** default. For non-default themes, override the bodies according to the **Theme Definitions** above (e.g., `\resumeheader` becomes a slate sidebar in `architect`; `\resumesection` becomes a numbered marker with no bar in `editorial`; `letterpress` adds a brass rule beneath each section bar).

```latex
% Candidate header - full-width solid accent bar with name, tagline, and contact in white
% Usage: \resumeheader{NAME}{Tagline}{contact line with \href{} links}
% NOTE: hyperlinks inside the header should be wrapped with \textcolor{white}{...} around
% the \href to keep them legible on the dark band. Set local hypersetup to white if needed.
\newcommand{\resumeheader}[3]{%
  \noindent\colorbox{resumeaccent}{%
    \begin{minipage}{\dimexpr\textwidth-2\fboxsep\relax}
      \vspace{4pt}
      {\fontsize{26}{30}\selectfont\sffamily\bfseries\color{white} #1}\\[2pt]
      {\fontsize{12}{14}\selectfont\sffamily\color{white} #2}\\[4pt]
      {\fontsize{9.5}{11}\selectfont\sffamily\color{white} #3}
      \vspace{4pt}
    \end{minipage}%
  }\\[10pt]
}

% Section heading - full-width solid accent bar with reversed white uppercase label
% Usage: \resumesection{EXPERIENCE}
\newcommand{\resumesection}[1]{%
  \vspace{6pt}
  \noindent\colorbox{resumeaccent}{%
    \begin{minipage}{\dimexpr\textwidth-2\fboxsep\relax}
      \vspace{2pt}
      {\fontsize{11}{13}\selectfont\sffamily\bfseries\color{white} \MakeUppercase{#1}}
      \vspace{2pt}
    \end{minipage}%
  }\\[4pt]
}

% Job entry header - company + role on left, location + dates on right
% Usage: \jobentry{Company}{Role}{Location}{Dates}
\newcommand{\jobentry}[4]{%
  \vspace{3pt}
  \noindent\begin{tabularx}{\textwidth}{@{}X r@{}}
    {\sffamily\bfseries #1} \textemdash{} {\sffamily #2} &
    {\fontsize{9}{11}\selectfont\sffamily\color{resumemuted} #3 \textperiodcentered{} #4} \\
  \end{tabularx}\\[1pt]
}

% Sub-role within a long tenure (e.g., promotions at the same company)
% Usage: \subjobentry{Sub-role title}{Dates}
\newcommand{\subjobentry}[2]{%
  \vspace{2pt}
  \noindent\hspace{0.5em}\begin{tabularx}{\dimexpr\textwidth-0.5em\relax}{@{}X r@{}}
    {\sffamily\itshape #1} &
    {\fontsize{9}{11}\selectfont\sffamily\color{resumemuted} #2} \\
  \end{tabularx}\\[1pt]
}

% Optional one-line scope/mandate under a job header
% Usage: \jobcontext{One-line scope/mandate description}
\newcommand{\jobcontext}[1]{%
  {\fontsize{9.5}{11}\selectfont\itshape\color{resumemuted} #1}\\[2pt]
}

% Skill category line - bold label, then dot-separated items
% Usage: \skillgroup{Category}{item · item · item}
\newcommand{\skillgroup}[2]{%
  \noindent{\sffamily\bfseries #1} \textemdash{} #2\\[2pt]
}

% Speaking/writing entry
% Usage: \speakentry{Event/Publication}{Description}
\newcommand{\speakentry}[2]{%
  \noindent{\sffamily\bfseries #1} \textemdash{} #2\\[3pt]
}
```

### AI-Disclosure Footer

Add the disclosure once at the end of the document, immediately before `\end{document}`:

```latex
\vfill\hfill{\fontsize{7}{8}\selectfont\itshape\color{resumemuted}Drafted with AI assistance via DeepAgents PrintShop.}
```

For per-page placement (preferred for multi-page resumes), use `eso-pic`:

```latex
\AddToShipoutPictureFG{%
  \AtPageLowerLeft{%
    \put(\dimexpr\paperwidth-2.4in,0.35in){%
      \fontsize{7}{8}\selectfont\itshape\color{resumemuted}Drafted with AI assistance via DeepAgents PrintShop.%
    }%
  }%
}
```

## Inline Directives

Markdown content may include the following HTML-comment directives. The LaTeX agent MUST honor them:

- `<!-- PAGEBREAK -->` — emit `\newpage` at this location in the rendered `.tex`. Used to force a clean page boundary between logically distinct blocks (e.g., separating two sub-roles at the same company when they would otherwise split awkwardly).

## Structure Rules

- The document must compile cleanly with `pdflatex`
- Output must be **2 pages** target, **3 pages maximum**
- Use the `\jobentry` macro for every job header — do NOT inline custom formatting
- Use the `\resumesection` macro for every section header — never use `\section` or `\section*`
- Skills section is the ONLY place `multicols` may appear; the rest of the document is single-column
- All hyperlinks (email, linkedin, personal site) must use `\href{}` from `hyperref`
- No image assets are required for this content type — resumes are text-only
- The candidate name in the header must match the `Name` field in `config.md`
- Dates should use the format `Mon YYYY – Mon YYYY` (en-dash, not hyphen) or `Mon YYYY – Present`
- The `theme:` value in `config.md` must be one of: `banker`, `letterpress`, `architect`, `editorial`. If absent, missing, or invalid, default to `banker`.
- The AI-disclosure footer must be present on the rendered output
