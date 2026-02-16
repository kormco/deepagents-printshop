# Related Work

## Template-Based Document Generation

Template engines such as Jinja2 [8] and Pandoc [9] enable programmatic document generation by filling structured data into pre-defined templates. LaTeX document classes (e.g., IEEEtran, ACM-article) provide publisher-compliant formatting but require authors to write LaTeX directly or use conversion tools that frequently produce suboptimal output [3]. Systems like Overleaf [10] provide collaborative editing environments but do not automate content formatting or quality assurance. These approaches reduce boilerplate but leave the core formatting burden on human authors.

## LLM-Based Writing Assistants

Large language models have been applied to various document preparation tasks. GPT-4 and Claude have demonstrated capabilities in grammar correction, text summarization, and code generation [4], [5]. Tools such as Grammarly and Writefull use language models for style and grammar checking [11]. Recent work has explored using LLMs to generate LaTeX directly from natural language descriptions [6], but single-pass generation suffers from high error rates in compilation, cross-referencing, and style compliance. PrintShop addresses these limitations by decomposing generation into multiple specialized stages with iterative refinement.

## Multi-Agent Systems

Multi-agent architectures have gained traction for complex AI tasks. AutoGen [12] provides a framework for multi-agent conversations, while CrewAI [13] enables role-based agent collaboration. LangGraph [7] extends LangChain with stateful, graph-based workflow orchestration supporting conditional branching and cycles. These frameworks have been applied to software engineering [14], data analysis [15], and research automation [16], but their application to document typesetting has not been explored. PrintShop leverages LangGraph's state graph for quality-gated pipeline orchestration with feedback loops.

## Document Quality Assurance

Automated document quality assessment has focused primarily on accessibility compliance [17] and structural validation [18]. PDF/UA checkers verify tag structure and reading order, while linters such as ChkTeX detect common LaTeX errors. Vision-based document analysis has been applied to layout detection [19] and OCR post-correction [20], but using vision-language models for closed-loop formatting correction in a generation pipeline is, to our knowledge, novel. PrintShop's visual QA stage uses a vision-language model to inspect rendered pages and generate targeted fixes, bridging the gap between source-level linting and visual output quality.
