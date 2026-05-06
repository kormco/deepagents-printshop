# Resume Cover Letter

## Type Metadata
- type_id: resume_cover_letter
- document_class: article
- default_font_size: 10.5pt
- default_paper_size: letterpaper
- default_theme: architect

## Rendering Instructions

Generate a one-page professional cover letter that is **visually matched** to the candidate's resume. The four themes mirror those of the `resume` content type — selecting the same theme on both documents produces a matched-pair packet (resume + cover letter) for a single application.

The cover letter must read as a **letter**, not a marketing brochure. It should be one page, single column, with body prose in 3–5 short paragraphs. The candidate's name and contact info appear in the same visual treatment as the resume (e.g., slate sidebar in `architect`, navy band in `banker`).

### Theme Selection

Same four themes as `resume`. The theme is chosen via `theme:` in `config.md`. If absent, default to `architect`.

| Theme ID | Header treatment |
|----------|------------------|
| `banker` | Full-width navy band with name + tagline + contact (matches resume) |
| `letterpress` | Navy band on cream paper with brass rule (matches resume) |
| `architect` | Slate sidebar on the left holding name + tagline + contact + ghosted monogram (matches resume page 1) |
| `editorial` | Serif name top-left, contact top-right, oxblood horizontal rule below (matches resume) |

The macro contract for cover letters is its own:
- `\letterheader{Name}{Tagline}{Contact line}` — same theme treatment as the resume header
- `\letterdate{Date}` — right-aligned date at top of body column
- `\letterrecipient{Recipient block}` — addressee block (left-aligned, 3–4 lines)
- `\lettersubject{Re: Role title}` — bold subject line above salutation
- `\lettersignature{Name}` — closing signature block

Body paragraphs are plain markdown paragraphs in `body.md` — the LaTeX agent emits them as standard paragraphs separated by `\par`/blank lines.

### Body Structure (canonical order)

1. **Header** — name + tagline + contact (theme-styled)
2. **Date** — top-right of body column
3. **Recipient block** — Hiring Director / Company / address (3–4 lines, left)
4. **Subject line** — `Re: <Role title>` in bold
5. **Salutation** — `Dear <Recipient>,` (or `Dear Hiring Team,` if unknown)
6. **Body paragraphs** — opening hook, 2–3 substantive paragraphs, closing thanks
7. **Closing** — `Sincerely,` followed by 2 blank lines and the signature
8. **Signature block** — candidate name + 1-line contact

### Tone and Length
- **One page maximum.** If content overflows, tighten paragraphs — do not let it spill to page 2.
- Each body paragraph: 3–6 sentences. No bullet lists in cover letters.
- Voice: professional, specific, concrete. Lead each paragraph with a clear claim and back it with one specific example from the resume.
- Avoid filler ("I am writing to express my strong interest in..."). Open with the most relevant credential or shared context.

### Typography
- Body in the same body font as the matching resume theme (sans for `banker`/`architect`, serif for `letterpress`/`editorial`)
- Body line-height ~1.15 (slightly looser than resume) for letter readability
- Body size 10.5pt
- 12pt margin between paragraphs (`\parskip 8pt` or equivalent)

### What to AVOID
- NO bullet lists, NO multi-column layout
- NO repeating the resume verbatim — the cover letter is a focused argument, not a summary
- NO opening with "To Whom It May Concern" — use a specific recipient or "Dear Hiring Team"
- NO references, salary expectations, or generic "I am a hard-working team player" boilerplate

### AI-Disclosure Footer
- Same convention as the resume: italic gray line in the bottom-right of the page reading *"Drafted with AI assistance via DeepAgents PrintShop."* at ~7pt, in `resumemuted` color
- Implementation: `\AddToShipoutPictureFG{}` from `eso-pic`

## Theme Definitions

The four themes share the same color tokens and palette swap convention as `content_types/resume/type.md`. See that file's **Theme Definitions** section for the per-theme palette, typography, and layout details. The cover letter applies the same theme treatment to its header (`\letterheader`) so the resume and cover letter look like a matched pair when the same `theme:` is selected.

| Theme | Palette swap | Header treatment |
|-------|-------------|------------------|
| `banker` (default in `resume`) | navy `#1F3A5F` + light navy `#6B7F9C` on white | full-width band |
| `letterpress` | navy `#1F3A5F` + brass `#C8A45E` on cream `#FAF7F2` | banded with brass rule |
| `architect` (default here) | slate `#1F2937` + sage `#84A98C` on white | slate sidebar |
| `editorial` | ink `#1A1A1A` + oxblood `#722F37` on cream `#FBF8F1` | serif name + oxblood rule |

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
\usepackage{hyperref}
\usepackage{eso-pic}
\usepackage{tikz}
\usepackage{parskip}
```

### Color Definitions
Use the same palette as the matching resume theme — see `content_types/resume/type.md` for the per-theme color block. The cover letter must declare `resumeaccent`, `resumeaccent2`, `resumemuted`, and (if the theme uses one) `resumepage`.

### Page Setup
For `architect` (default), match the resume's page-1 geometry so the slate sidebar lines up identically:

```latex
\geometry{paperwidth=8.5in, paperheight=11in,
          top=0.5in, bottom=0.55in,
          left=1.85in, right=0.55in}
\pagestyle{empty}
\linespread{1.10}
```

For non-sidebar themes (`banker`, `letterpress`, `editorial`) use even side margins:
```latex
\geometry{margin=0.85in, top=0.7in, bottom=0.7in}
```

### Custom Macro Definitions

```latex
% Date — right-aligned
\newcommand{\letterdate}[1]{%
  \hfill {\sffamily\color{resumemuted} #1}\par\vspace{8pt}%
}

% Recipient block — left-aligned, 3–4 lines
\newcommand{\letterrecipient}[1]{%
  \noindent #1\par\vspace{6pt}%
}

% Subject line — bold, accent color
\newcommand{\lettersubject}[1]{%
  \noindent{\sffamily\bfseries\color{resumeaccent} #1}\par\vspace{6pt}%
}

% Signature block — name + 1-line contact
\newcommand{\lettersignature}[2]{%
  \par\vspace{8pt}%
  \noindent{\sffamily\bfseries\color{resumeaccent} #1}\\%
  {\fontsize{8.5}{11}\selectfont\sffamily\color{resumemuted} #2}%
}
```

The `\letterheader` macro is theme-specific — see Theme Definitions and the resume content type for the per-theme implementation. For `architect`, it should emit the same TikZ slate sidebar overlay used in the resume.

## Inline Directives

Cover letters are short and rarely use inline asset references. The following are honored if present:
- `<!-- DATE -->` — replaced with the date from `config.md` or today's date
- `<!-- SIGNATURE -->` — emits the `\lettersignature{}` block at the end

## Structure Rules

- Output must be exactly **1 page**. If the body overflows, tighten upstream content.
- The candidate name in the header must match the `Name` field in `config.md`
- The recipient block must match the `Recipient` field in `config.md`
- The subject line must match the `Target Role` field in `config.md`
- The `theme:` value in `config.md` must be one of: `banker`, `letterpress`, `architect`, `editorial`. If absent, default to `architect`.
- The AI-disclosure footer must be present on the rendered output
