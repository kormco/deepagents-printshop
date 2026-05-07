# Common visual QA fix patterns

Reference catalogue for the `printshop-review` skill. Load on demand.

## Overflow / `Overfull \hbox`

**Symptom:** text or table runs into the right margin; visible bleed in the rendered PNG.

**Fix candidates (smallest first):**
- Add a soft hyphen at a sensible break: `\-` inside the offending word.
- Wrap the run in `\sloppy ... \fussy` if it's confined to one paragraph.
- Convert a long URL or path to use `\url{...}` (requires `\usepackage{url}`).
- For tables: switch the offending column to `p{<width>}` or `m{<width>}`.

Don't reach for `\setlength{\emergencystretch}` unless several paragraphs are affected — it changes spacing globally.

## Tables wider than the text block

**Fix candidates:**
- Wrap the tabular in `\resizebox{\textwidth}{!}{...}` (requires `graphicx`).
- Convert to `tabularx` with `X` columns for fluid widths.
- Reduce inter-column padding: `\setlength{\tabcolsep}{4pt}` *inside* the table only — restore afterward.
- For data tables specifically, drop a column or merge two columns rather than shrinking type.

## Figures placed wrong

**Symptom:** figure floats far from its reference, leaves a near-empty page, or splits a section.

**Fix candidates:**
- Tighten the placement specifier: `\begin{figure}[!htbp]` instead of `[h]`.
- Force a placement with `\FloatBarrier` (requires `placeins`) before the next section.
- For small inline figures, use `wrapfigure` (requires `wrapfig`).

Avoid `[H]` (`float` package) unless the user explicitly asks for "exactly here" — it usually looks worse.

## Caption / label issues

- Caption *below* a figure, *above* a table — flip if reversed.
- Duplicate `\label{}` produces a `multiply defined labels` warning. Find the duplicate via grep and rename one.
- `\ref{??}` in the rendered PDF means a missing label — recompile twice (the pipeline already does this; if it still shows, the label is genuinely absent).

## Headings on the wrong page

**Symptom:** a section heading sits at the bottom of a page with its body on the next.

**Fix candidates:**
- `\nopagebreak[4]` immediately after the heading (gentle hint).
- `\needspace{4\baselineskip}` before the heading (requires `needspace`).
- For real wrap-up: add a `\pagebreak` *before* the heading.

## Inconsistent spacing around lists / code blocks

- Reduce list separation: `\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}` inside the list (or use `enumitem`'s `noitemsep`).
- For code blocks (`verbatim` / `lstlisting`), surrounding blank-line whitespace is structural — strip an extra blank line in the source before/after the block.

## Citation / bibliography style mismatch

- If the bib style doesn't match the content type (e.g. IEEE numeric vs APA author-year), change `\bibliographystyle{...}`. Don't hand-edit individual `\cite` calls.
- `[1, 2, 3]` rendering as `[1][2][3]` usually means a missing `cite` package — add `\usepackage{cite}`.

## When to stop fixing

Three signals it's time to stop:

1. The user has accepted nothing on the last 2–3 issues.
2. Each fix reveals a new issue of similar magnitude (the document is fundamentally fighting the template — re-run the pipeline with a different content type).
3. Recompile fails twice in a row from the same fix family.
