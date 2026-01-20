# DeepAgents PrintShop - Handoff Notes

**Date**: January 19, 2026
**Status**: Pipeline working, ready for magazine styling improvements

---

## What Was Accomplished

### 1. Image Integration
- Updated `artifacts/sample_content/images/README.md` with detailed descriptions and placement guidance for each image
- Fixed `load_figures()` in `agents/research_agent/llm_report_generator.py` to:
  - Use correct relative paths (`../sample_content/images/`) for pdflatex
  - Parse the images README.md to get descriptions, captions, and placement hints
  - Pass rich context to the LLM for intelligent image placement

### 2. LLM Self-Correction Loop
- Added pre-validation to detect truncated LaTeX output (missing `\end{document}`)
- Implemented multi-turn LLM self-correction in `generate_and_compile()`:
  - Detects compilation failures
  - Calls `self_correct_compilation_errors()` to have Claude fix issues
  - Retries compilation up to 3 times
  - Successfully handles truncated output, syntax errors, etc.

### 3. Windows Compatibility Fixes
- Created `run_agent.py` and `run_llm_generator.py` wrapper scripts with UTF-8 encoding
- Fixed symlink issues in `tools/version_manager.py` (falls back to text file on Windows)
- Updated README.md with MiKTeX requirements for Windows users

### 4. Pipeline Run Results
- Full QA pipeline completed successfully (~14 minutes)
- Final quality score: 85.2/100
- Generated 17-page PDF with all images included
- Visual QA ran 2 iterations with LLM improvements

---

## Current Issues / Known Limitations

1. **Research Report Styling**: Output looks like academic paper, not a magazine
   - Title hardcoded as "Advanced AI Research: Transformers and Beyond"
   - Single-column layout
   - No magazine elements (cover page, pull quotes, sidebars)

2. **Some Visual QA Errors**: `Invalid control character` errors on some pages (non-blocking)

3. **No Graph Visualizations**: Magazine would benefit from data visualizations

---

## Setup on New PC

### Prerequisites
```bash
# Python 3.11+
python --version

# MiKTeX (required for PDF compilation)
# Download from: https://miktex.org/download
pdflatex --version

# Poppler (optional, for Visual QA PDF-to-image)
# Download from: https://github.com/oschwartz10612/poppler-windows/releases/
```

### Quick Start
```bash
# Clone the repo
git clone https://github.com/kormco/deepagents-printshop.git
cd deepagents-printshop
git checkout feature-ai-mag-sample

# Create .env with your API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...

# Install Python dependencies
pip install anthropic python-dotenv pillow pdf2image pypdf pandas matplotlib

# Run LLM generator only (faster, ~3 min)
python run_llm_generator.py

# Run full QA pipeline (~14 min)
python run_agent.py
```

---

## Next Steps: Magazine Styling

### 1. Update LLM Generator to Use config.md
File: `agents/research_agent/llm_report_generator.py`

- Read title, subtitle, date from `artifacts/sample_content/config.md`
- Pass magazine metadata to LLM instead of hardcoded values
- Current hardcoded values in `generate_with_patterns()`:
  ```python
  request = LaTeXGenerationRequest(
      title="Advanced AI Research: Transformers and Beyond",  # Change this
      author="Dr. Research Smith",  # Change this
      ...
  )
  ```

### 2. Magazine LaTeX Styling
Add to LLM prompt requirements:
- Two-column layout (`\usepackage{multicol}`)
- Magazine-style cover page with full-bleed image
- Pull quotes (`\begin{quote}` with styling)
- Sidebars for technical details
- Drop caps for article openings
- Better typography (larger headings, magazine fonts)

### 3. Add Graph Visualizations
Options:
- **matplotlib**: Generate PNG charts from data, include as figures
- **pgfplots**: LaTeX-native charts (cleaner but more complex)
- **TikZ**: Custom diagrams and flowcharts

Suggested graphs for the magazine:
- Market growth timeline ($7.8B → $52B by 2030)
- Agent adoption bar chart (12% → 57% → 78%)
- Framework performance comparison (LangGraph vs others)
- MCP adoption curve (SDK downloads over time)

Implementation approach:
```python
# In llm_report_generator.py, add:
def generate_charts(self) -> List[Dict]:
    """Generate matplotlib charts from CSV data."""
    import matplotlib.pyplot as plt

    # Example: Market growth chart
    years = [2024, 2025, 2026, 2027, 2030]
    market_size = [7.8, 12, 18, 25, 52]

    plt.figure(figsize=(8, 4))
    plt.plot(years, market_size, marker='o')
    plt.title('AI Agent Market Growth')
    plt.ylabel('Market Size ($B)')
    plt.savefig(self.images_dir / 'market_growth.png', dpi=150)
    plt.close()

    return [{"path": "../sample_content/images/market_growth.png",
             "caption": "Projected AI agent market growth"}]
```

### 4. Cover Page Design
Create a dedicated cover page with:
- Full-page background image (cover-image.jpg)
- Magazine title overlay: "Deep Agents"
- Subtitle: "The Definitive Guide to Autonomous AI"
- Issue info: "Volume 1, Issue 1 | January 2026"
- Headline teasers

---

## File Locations

| File | Purpose |
|------|---------|
| `run_agent.py` | UTF-8 wrapper for QA orchestrator |
| `run_llm_generator.py` | UTF-8 wrapper for LLM generator |
| `agents/research_agent/llm_report_generator.py` | Main LLM generation logic |
| `tools/llm_latex_generator.py` | Claude-powered LaTeX generation |
| `artifacts/sample_content/config.md` | Magazine configuration |
| `artifacts/sample_content/images/README.md` | Image descriptions & placement |
| `artifacts/output/research_report.pdf` | Generated PDF |

---

## Git Status

Uncommitted changes:
- `agents/research_agent/llm_report_generator.py` (image loading + self-correction)
- `tools/version_manager.py` (Windows symlink fix)
- `artifacts/sample_content/images/README.md` (image descriptions)
- `artifacts/sample_content/config.md` (images section)
- `run_agent.py`, `run_llm_generator.py` (new wrapper scripts)
- `HANDOFF.md` (this file)

Consider committing before switching PCs:
```bash
git add -A
git commit -m "Add LLM self-correction, image integration, and Windows fixes"
git push origin feature-ai-mag-sample
```

---

## Quick Test Commands

```bash
# Test just the LLM generator (fastest)
python run_llm_generator.py

# Test full pipeline
python run_agent.py

# Manual LaTeX compilation (if needed)
cd artifacts/output
pdflatex research_report.tex
```

---

**Questions?** Check CLAUDE.md for project documentation or README.md for full setup instructions.
