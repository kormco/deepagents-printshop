# System Design

This section describes the PrintShop pipeline architecture, including the three agent stages, the quality gate mechanism, and the data flow from markdown input to PDF output.

## Pipeline Overview

PrintShop is implemented as a LangGraph StateGraph with three sequential stages connected by quality gates. The pipeline ingests a markdown manuscript alongside a configuration manifest and content-type-specific rendering instructions, and produces a compiled PDF with a detailed quality report.

<!-- TIKZ:
caption: PrintShop pipeline architecture. Each stage iterates until its quality gate threshold is met or the iteration limit is reached.
label: fig:architecture
code:
\tikzstyle{stage} = [rectangle, draw=black, fill=blue!15, text width=2.8cm, minimum height=1.2cm, text centered, font=\small\bfseries, rounded corners=3pt]
\tikzstyle{gate} = [diamond, draw=black, fill=orange!20, text width=1.4cm, minimum height=1cm, text centered, font=\scriptsize, aspect=1.5]
\tikzstyle{io} = [rectangle, draw=black, fill=green!10, text width=2cm, minimum height=0.8cm, text centered, font=\small, rounded corners=3pt]
\tikzstyle{arrow} = [->, >=stealth, thick]

\node[io] (input) at (0,0) {Markdown + Config};
\node[stage] (ce) at (3.2,0) {Content\\Editor};
\node[gate] (g1) at (6,0) {Score\\$\geq 80$?};
\node[stage] (ls) at (8.8,0) {LaTeX\\Specialist};
\node[gate] (g2) at (11.6,0) {Score\\$\geq 85$?};
\node[stage] (vqa) at (14.4,0) {Visual\\QA};
\node[gate] (g3) at (17.2,0) {Score\\$\geq 80$?};
\node[io] (output) at (20,0) {PDF +\\Report};

\draw[arrow] (input) -- (ce);
\draw[arrow] (ce) -- (g1);
\draw[arrow] (g1) -- node[above, font=\scriptsize] {pass} (ls);
\draw[arrow] (ls) -- (g2);
\draw[arrow] (g2) -- node[above, font=\scriptsize] {pass} (vqa);
\draw[arrow] (vqa) -- (g3);
\draw[arrow] (g3) -- node[above, font=\scriptsize] {pass} (output);

\draw[arrow] (g1.south) -- ++(0,-0.8) -| node[near start, below, font=\scriptsize] {iterate} (ce.south);
\draw[arrow] (g2.south) -- ++(0,-0.8) -| node[near start, below, font=\scriptsize] {iterate} (ls.south);
\draw[arrow] (g3.south) -- ++(0,-0.8) -| node[near start, below, font=\scriptsize] {iterate} (vqa.south);
-->

The pipeline processes documents through three stages in sequence. Each stage produces versioned artifacts stored in a structured output directory, enabling traceability and rollback.

## Stage 1: Content Editor

The content editor agent receives the raw markdown sections and evaluates them on three dimensions: grammatical correctness, readability (measured via the Flesch Reading Ease score), and adherence to the target academic tone. The agent uses an LLM to identify issues and propose revisions, then re-scores the revised text. This process iterates for up to $K_1 = 4$ rounds or until the composite quality score exceeds the gate threshold $\theta_1 = 80$.

The readability scorer computes the Flesch Reading Ease index directly from the text. Scores below 30 indicate highly complex prose typical of dense academic writing; the content editor aims for scores in the 35–50 range, balancing accessibility with scholarly rigor.

## Stage 2: LaTeX Specialist

The LaTeX specialist converts the edited markdown into a compilable LaTeX document. This stage is guided by two inputs beyond the markdown itself:

- **Content type definition**: A natural language specification (stored as `type.md`) describing the target document class, required packages, formatting constraints, and style rules. For example, the IEEE conference type specifies `IEEEtran` document class, two-column layout, and numbered citations.
- **Configuration manifest**: Metadata including title, authors, abstract, and the ordered list of section files.

The specialist processes inline reference directives embedded in the markdown as HTML comments: `<!-- IMAGE: -->` for figures, `<!-- CSV_TABLE: -->` for data tables, and `<!-- TIKZ: -->` for programmatic diagrams. Each directive is expanded into the corresponding LaTeX environment with proper labels, captions, and cross-references.

After initial generation, the optimizer applies automated corrections: Unicode sanitization for pdflatex compatibility, duplicate label detection, package conflict resolution, and table formatting normalization. The stage iterates until the LaTeX quality score exceeds $\theta_2 = 85$.

## Stage 3: Visual Quality Assurance

The visual QA stage closes the loop between source-level generation and rendered output. The process operates as follows:

1. Compile the LaTeX source to PDF using pdflatex with multi-pass compilation for cross-references.
2. Render each page of the PDF as a raster image.
3. Submit each page image to a vision-language model with a prompt requesting identification of formatting defects (overflow, misalignment, orphaned headings, incorrect spacing, broken figures).
4. Parse the model's defect report and generate targeted LaTeX patches.
5. Apply patches, recompile, and re-evaluate.

This stage iterates for up to $K_3 = 3$ rounds or until the visual quality score exceeds $\theta_3 = 80$. The feedback loop enables the pipeline to catch and correct defects that are invisible at the source level but apparent in the rendered output, such as figure placement conflicts, column overflow, and widowed lines.

## Quality Gates

Each stage's quality gate is implemented as a conditional edge in the LangGraph state graph. The gate evaluates the stage output against its threshold and routes execution either forward to the next stage or back to the current stage for another iteration. An iteration counter prevents infinite loops. If the maximum iteration count is reached without meeting the threshold, the pipeline proceeds with the best result achieved and flags the quality shortfall in the output report.
