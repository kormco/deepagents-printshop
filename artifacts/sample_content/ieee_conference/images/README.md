# IEEE Conference Sample — Figure Guide

All figures for this paper should be generated as **inline TikZ/pgfplots** during LaTeX compilation. Do NOT use pre-rendered image files.

## Figure 1: PrintShop Pipeline Architecture
- **Placement**: System Design section
- **Type**: TikZ block diagram
- **Content**: Show three pipeline stages (Content Editor, LaTeX Specialist, Visual QA) as rounded rectangles connected by arrows. Between each pair of stages, place a diamond-shaped quality gate node labeled with the threshold score (80, 85, 80). Include feedback arrows from each gate back to its preceding stage labeled "iterate". Input node (Markdown + Config) on the left, output node (PDF + Report) on the right.
- **Width**: Full column width (`\columnwidth`)
- **Libraries**: `shapes.geometric`, `arrows.meta`, `positioning`

## Figure 2: Formatting Accuracy by Content Type
- **Placement**: Results and Discussion section
- **Type**: pgfplots grouped bar chart
- **Content**: Formatting accuracy (%) per content type (Research Report, Conference Paper, Magazine Article, Technical Manual, Thesis) for three methods (PrintShop, Single-Pass LLM, Template-Only). Use distinct colors per method with a legend.
- **Width**: Full column width (`\columnwidth`)
- **Data points**:
```
Content Type,    PrintShop, Single-Pass LLM, Template-Only
Research Report, 95.4,      72.5,            65.2
Conference Paper,96.8,      82.1,            71.8
Magazine Article,90.3,      54.7,            48.1
Technical Manual,93.1,      66.3,            59.4
Thesis,          94.2,      70.8,            62.5
```

## Figure 3: Revision Cycle Convergence
- **Placement**: Results and Discussion section
- **Type**: pgfplots line chart
- **Content**: Formatting accuracy (%) vs. quality gate threshold (60–95) for PrintShop (increasing curve with diminishing returns), Single-Pass LLM (flat line at 68.1%), and Template-Only (flat line at 61.4%). Shows that PrintShop's iterative approach benefits from higher thresholds up to a point.
- **Width**: Full column width (`\columnwidth`)
- **Data points**:
```
Threshold, PrintShop, Single-Pass LLM, Template-Only
60,        85.2,      68.1,            61.4
65,        87.8,      68.1,            61.4
70,        89.9,      68.1,            61.4
75,        91.6,      68.1,            61.4
80,        93.4,      68.1,            61.4
85,        94.7,      68.1,            61.4
90,        95.1,      68.1,            61.4
95,        95.3,      68.1,            61.4
```
