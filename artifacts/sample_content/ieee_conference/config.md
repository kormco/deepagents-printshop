# Document Configuration

## DISCLAIMER

**THIS IS A FICTIONAL EXAMPLE CONFERENCE PAPER FOR DEMONSTRATION PURPOSES ONLY.**

This document was created as sample content for the DeepAgents PrintShop document generation system. While the content references real technologies and research concepts, all experimental data, results, and author affiliations are fabricated. Any resemblance to actual published research is coincidental.

Do not cite this document as a factual source.

---

## Content Type
ieee_conference

## Project Metadata
- Title: PrintShop: A Multi-Agent Pipeline for Automated Professional Document Generation with Visual Quality Assurance
- Authors:
  - Name: A. Morgan
    Affiliation: Department of Computer Science, Westbrook University, Denver, CO, USA
    Email: amorgan@westbrook.edu
  - Name: S. Patel
    Affiliation: Applied AI Research Group, Cascadia Labs, Seattle, WA, USA
    Email: spatel@cascadialabs.ai
  - Name: L. Torres
    Affiliation: Department of Information Systems, Westbrook University, Denver, CO, USA
    Email: ltorres@westbrook.edu
- Conference: 2026 IEEE International Conference on Software Engineering and Applications (ICSEA)
- Funding: This work was supported in part by the National Science Foundation under Grant No. 2241097.

## Abstract
Producing professionally typeset documents from structured content remains a labor-intensive process that demands expertise in both subject matter and typesetting systems such as LaTeX. We present PrintShop, a multi-agent pipeline orchestrated by a LangGraph state graph that automates the end-to-end transformation of markdown manuscripts into publication-ready PDFs. The pipeline comprises three quality-gated stages — content editing, LaTeX generation, and visual quality assurance — each driven by large language models and governed by configurable score thresholds. The visual QA stage compiles the document, renders pages as images, and uses a vision-language model to detect and correct formatting defects in a closed feedback loop. We evaluate PrintShop on a benchmark of 120 documents spanning five content types (research report, conference paper, magazine article, technical manual, and thesis). PrintShop achieves 94.7% first-pass formatting accuracy and a 99.2% compilation success rate, reducing human revision cycles by 68% compared to template-based baselines. Ablation experiments confirm that the visual QA feedback loop accounts for the largest share of quality improvement.

## Keywords
document generation, multi-agent systems, large language models, LaTeX, visual quality assurance, LangGraph

## Content Manifest
1. Introduction: introduction.md
2. Related Work: related_work.md
3. System Design: system_design.md
4. Experimental Setup: experimental_setup.md
5. Results and Discussion: results.md
6. Conclusion: conclusion.md

## Rendering Notes
- Standard IEEE two-column conference format.
- Include all CSV data tables in the Results section.
- Include bibliography with IEEE-style numbered references.
- Generate all figures as **inline TikZ/pgfplots** within the LaTeX source (no pre-rendered images). See `images/README.md` for figure descriptions, data points, and placement guidance.
- Keep total content within 6-page equivalent length.

## Document Options
- include_toc: false
- include_bibliography: true
- two_column: true

## Headers and Footers
- Managed by IEEEtran class — do not override.
