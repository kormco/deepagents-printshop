# Experimental Setup

## Document Benchmark

We evaluate PrintShop on a benchmark corpus of 120 documents spanning five content types, with 24 documents per type:

- **Research report**: 8–15 page single-column documents with figures, tables, bibliography, and table of contents.
- **Conference paper**: 6-page two-column IEEE-format papers with inline TikZ figures and numbered citations.
- **Magazine article**: Multi-page layouts with pull quotes, sidebars, drop caps, and full-bleed images.
- **Technical manual**: Structured documents with numbered sections, code listings, warning callouts, and cross-references.
- **Thesis chapter**: Long-form academic documents with theorem environments, appendices, and multi-level headings.

Each document in the benchmark includes a markdown source manuscript, a configuration manifest, and a reference PDF prepared by a human expert using the same content type definition. Source documents range from 2,000 to 12,000 words and contain between 2 and 8 inline reference directives (images, CSV tables, or TikZ diagrams).

## Evaluation Metrics

We assess pipeline performance using four metrics:

- **Formatting accuracy** (\%): Percentage of rendered pages with no formatting defects, as judged by a human evaluator using a standardized rubric covering margin compliance, figure placement, table formatting, heading hierarchy, and typographic consistency.
- **Compilation success rate** (\%): Percentage of documents that compile to PDF without errors on the first pipeline run.
- **Average revision cycles**: Mean number of human revision passes required to bring the generated PDF to publication-ready quality, starting from the pipeline output.
- **Processing time** (min): Wall-clock time from markdown input to final PDF output, measured on a system with an NVIDIA A100 GPU and 64 GB RAM.

## Baselines

We compare PrintShop against three baselines:

- **Template-Only**: The markdown is converted to LaTeX using Pandoc with the appropriate document class template. No LLM processing or quality assurance is applied.
- **Single-Pass LLM**: A single LLM call converts the markdown to LaTeX using the same content type definition and configuration manifest as PrintShop, but without iterative refinement or visual QA.
- **Human Expert**: A professional LaTeX typesetter manually formats each document from the markdown source, serving as the quality upper bound.

## Configuration

All LLM calls use Claude 3.5 Sonnet with temperature 0.3. Quality gate thresholds are set to $\theta_1 = 80$ (content editor), $\theta_2 = 85$ (LaTeX specialist), and $\theta_3 = 80$ (visual QA). Maximum iterations per stage are $K_1 = 4$, $K_2 = 3$, and $K_3 = 3$. The visual QA stage uses Claude 3.5 Sonnet's vision capabilities for page inspection. All experiments are repeated three times with different random seeds, and we report mean and standard deviation.
