# Introduction

Professional document preparation is a persistent bottleneck in academic and industrial workflows. Authors spend substantial effort formatting manuscripts to comply with publisher style guides, adjusting figure placement, resolving citation formatting, and debugging LaTeX compilation errors [1]. Studies of researcher time allocation estimate that formatting accounts for 15–25% of total manuscript preparation effort [2], a figure that rises sharply for complex document types such as conference proceedings, technical manuals, and magazine layouts.

Template-based approaches address part of this problem by providing pre-configured LaTeX classes and style files. However, templates only define structure — they do not generate content, process inline references, or detect visual defects in the compiled output. Authors must still manually convert prose into LaTeX, manage figure and table placement, and visually inspect the rendered PDF for spacing, overflow, and alignment issues [3]. These tasks are tedious, error-prone, and require familiarity with the LaTeX ecosystem that many domain experts lack.

Large language models (LLMs) have demonstrated strong capabilities in text generation, code synthesis, and instruction following [4]. Recent work has applied LLMs to document-related tasks such as summarization, grammar correction, and code generation [5]. However, using a single LLM call to produce publication-ready LaTeX from structured content yields inconsistent results: models frequently introduce compilation errors, mishandle special characters, produce incorrect cross-references, and generate formatting that deviates from target style guides [6].

In this paper, we present PrintShop, a multi-agent pipeline that automates the transformation of markdown manuscripts into professionally typeset PDFs. PrintShop is orchestrated by a LangGraph state graph [7] and comprises three quality-gated stages:

- **Content editing**: An LLM-based agent reviews and refines markdown source for grammar, readability, and academic tone, iterating until a configurable quality threshold is met.
- **LaTeX generation**: A specialist agent converts the edited markdown into LaTeX, guided by content-type-specific rendering instructions and inline reference processing for images, CSV tables, and TikZ diagrams.
- **Visual quality assurance**: The compiled PDF is rendered to images and inspected by a vision-language model that identifies formatting defects and applies targeted LaTeX fixes in a closed feedback loop.

Each stage is gated by a quality score threshold; stages iterate until the threshold is reached or an iteration limit is exceeded. This architecture decomposes the complex document generation task into manageable sub-problems and enables targeted quality improvement at each stage.

We evaluate PrintShop on a benchmark of 120 documents across five content types. Results show that the pipeline achieves 94.7% first-pass formatting accuracy and a 99.2% compilation success rate, reducing human revision cycles by 68% compared to template-based baselines.
