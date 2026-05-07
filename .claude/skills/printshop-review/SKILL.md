---
name: printshop-review
description: Use when the user invokes /printshop-review, asks to "review the printshop output", or wants to walk page-by-page through a deepagents-printshop run and decide which visual fixes to apply. Drives an interactive visual QA loop on a rendered PDF — render pages, propose targeted fixes, accept/reject each, edit the .tex, recompile, repeat. Activate only inside a deepagents-printshop project (artifacts/output/ must exist).
license: Apache-2.0
metadata:
  project: deepagents-printshop
  pairs_with: VISUAL_QA_MODE=interactive
allowed-tools: Read, Edit, Write, Bash, Glob
---

# printshop-review — interactive visual QA for deepagents-printshop

This skill replaces the autonomous `visual_qa` pipeline stage with a **human-in-the-loop** review of the rendered PDF. The pipeline produced the `.tex` and PDF; you walk the user through them page-by-page and apply only the fixes they accept.

## When to activate

- User runs `/printshop-review [run_id]`.
- User asks to review or QA a printshop run, e.g. "review the output", "let's go through the resume PDF", "QA my latest run".

Only activate inside a deepagents-printshop project (the cwd or a parent has `artifacts/output/`). Otherwise tell the user this skill needs that directory and stop.

## Inputs you'll find on disk

A run lives at `artifacts/output/<run_id>/` and contains:

- `<content_source>.tex` — the LaTeX source the LaTeX-specialist agent generated (e.g. `resume.tex`, `magazine.tex`, `research_report.tex`).
- `<content_source>.pdf` — the compiled PDF.
- `handoff.json` — present when `VISUAL_QA_MODE=interactive` was set on the run. Contains run id, tex/pdf paths, page count, and concerns the LaTeX stage flagged.

A `handoff.json` looks like:

```json
{
  "run_id": "abc12345",
  "content_source": "resume",
  "tex_path": "/path/to/artifacts/output/abc12345/resume.tex",
  "pdf_path": "/path/to/artifacts/output/abc12345/resume.pdf",
  "tex_exists": true,
  "pdf_exists": true,
  "page_count": 2,
  "visual_qa_mode": "interactive",
  "next_step": "interactive_review",
  "concerns": ["typography: bad spacing on page 2", "weak typography score: 15/25"]
}
```

If `handoff.json` is missing (a run produced under `auto` or `disabled` mode), proceed anyway — discover the .tex/PDF directly and skip the concerns hint.

## The review loop

1. **Locate the run.**
   - If the user passed a `run_id`, use `artifacts/output/<run_id>/`.
   - Otherwise list newest-first directories under `artifacts/output/`. Pick the most-recent and confirm with the user before proceeding ("Review run abc12345 (resume, 2 pages, 4 minutes ago)?").

2. **Read context.** Read `handoff.json` if present and `<content_source>.tex` (always). Note the concerns from the manifest — they're hints, not commands.

3. **Render the PDF to per-page PNGs.** Use `pdftoppm`:
   ```bash
   pdftoppm -png -r 150 <pdf_path> <run_dir>/page
   ```
   This produces `<run_dir>/page-1.png`, `page-2.png`, etc. (Use `-r 200` for dense layouts where 150 dpi looks fuzzy.)

4. **Walk pages one at a time.** For each page:
   - Read the rendered PNG.
   - Identify *targeted* visual issues — overflow, misaligned figures, table widths, label collisions, awkward spacing, orphan headings, broken citations. Skip nitpicks the user clearly doesn't care about.
   - For each issue, propose a concrete fix referencing the `.tex` line/region. Show the user the smallest possible diff.
   - Wait for accept / reject / "explain" / "ask follow-up". Don't apply anything they didn't accept.
   - Apply accepted fixes with the Edit tool.

5. **Recompile after each batch of accepted fixes.**
   ```bash
   python3 -m tools.recompile <run_id>
   ```
   This wraps `PDFCompiler` so you get the same multi-pass + regex-fix behavior as the pipeline, and refreshes `handoff.json` with the new page count.

6. **Re-render and continue.** Run `pdftoppm` again, compare the affected page to the previous version, then move to the next page (or revisit if the fix didn't land cleanly).

7. **Stop when the user says "ship it"** (or equivalent). Print a one-line summary: pages reviewed, fixes applied, recompile count.

## Rules of engagement

- **The human is the gate.** No fix gets applied without explicit user accept. Don't batch-apply "obvious" fixes silently.
- **Surface, don't pile.** Surface 1–3 issues per page max. If a page has more, ask the user if they want to keep going or move on.
- **Preserve the preamble.** Edit the body. If a fix needs a new package, propose it explicitly and let the user accept the preamble change separately.
- **Don't rewrite the document.** This is QA, not authoring. If the user wants a major restructure, route them to re-run the full pipeline.
- **No silent recompiles.** The user should always know when you're invoking pdflatex.
- **If recompile fails after a fix:** show the error, offer to revert the last edit, and ask before retrying.

## Common fix patterns

See `references/fix-patterns.md` for the catalogue of typical issues (overflow, table widths, figure placement, citation style, etc.) and the small targeted edits that resolve each.

## What this skill is NOT

- Not a content editor — don't propose prose changes; that's the content-editor stage.
- Not an authoring tool — don't generate new sections or restructure.
- Not a deploy tool — "ship it" just means stop the loop. The user takes the PDF wherever it goes next.
