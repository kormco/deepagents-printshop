# Results and Discussion

## Overall Performance

Table I summarizes the performance of PrintShop and all baselines across the full 120-document benchmark. PrintShop achieves 94.7% formatting accuracy and a 99.2% compilation success rate, requiring an average of 0.7 human revision cycles to reach publication quality. This represents a 68% reduction in revision cycles compared to the Template-Only baseline (2.2 cycles) and a 56% reduction compared to Single-Pass LLM (1.6 cycles).

<!-- CSV_TABLE: path=data/overall_performance.csv, caption=Overall performance comparison across 120 documents (mean $\pm$ std over 3 runs), label=tab:overall -->

The Human Expert baseline achieves 98.9% formatting accuracy with zero revision cycles by definition, but requires an average of 42.5 minutes per document. PrintShop processes documents in 4.3 minutes on average, a 9.9x speedup. The Template-Only baseline is fastest (0.8 minutes) but produces the lowest formatting accuracy (61.4%) due to its inability to handle inline references, figure placement, or style-specific formatting beyond what the document class provides.

## Per-Content-Type Analysis

Table II presents a breakdown of formatting accuracy by content type. PrintShop performs most consistently on conference papers (96.8%) and research reports (95.4%), which have well-defined structure and relatively constrained formatting requirements. Magazine articles present the greatest challenge (90.3%), as their complex layouts with pull quotes, sidebars, and variable column widths require fine-grained visual adjustments that are difficult to achieve through source-level generation alone.

<!-- CSV_TABLE: path=data/per_cluster_results.csv, caption=Formatting accuracy (\%) by content type and method, label=tab:per_type -->

The Single-Pass LLM baseline shows high variance across content types: it achieves 82.1% on conference papers (where LaTeX conventions are well-represented in training data) but only 54.7% on magazine articles. PrintShop's iterative refinement and visual QA substantially reduce this variance, demonstrating that the multi-stage architecture provides consistent quality across diverse document types.

## Ablation Study

To isolate the contribution of each pipeline stage, we evaluate four ablation variants on the full benchmark.

<!-- CSV_TABLE: path=data/ablation_study.csv, caption=Ablation study results across 120 documents (mean $\pm$ std over 3 runs), label=tab:ablation -->

Removing the visual QA stage produces the largest accuracy drop (94.7% to 87.3%), confirming that closed-loop visual feedback is the primary driver of formatting quality. Without visual QA, defects such as figure overflow, orphaned headings, and column imbalance persist because they are undetectable at the source level. Removing the content editor reduces accuracy to 91.5%, primarily due to grammatical issues and inconsistent tone that propagate into the LaTeX source and occasionally trigger formatting artifacts. Disabling quality gates (running each stage exactly once) reduces accuracy to 89.1%, demonstrating that iterative refinement provides meaningful improvement over single-pass execution.

## Convergence Behavior

<!-- TIKZ:
caption: Formatting accuracy vs. quality gate threshold. Higher thresholds improve accuracy but increase processing time.
label: fig:convergence
code:
\begin{axis}[
    xlabel={Quality Gate Threshold},
    ylabel={Formatting Accuracy (\%)},
    xmin=60, xmax=95,
    ymin=80, ymax=98,
    legend pos=south east,
    grid=major,
    width=\columnwidth,
    height=5cm,
    legend style={font=\scriptsize},
    tick label style={font=\scriptsize},
    label style={font=\small}
]
\addplot[blue, mark=square*, thick] coordinates {
    (60,85.2) (65,87.8) (70,89.9) (75,91.6) (80,93.4) (85,94.7) (90,95.1) (95,95.3)
};
\addlegendentry{PrintShop}
\addplot[red, mark=triangle*, thick, dashed] coordinates {
    (60,68.1) (65,68.1) (70,68.1) (75,68.1) (80,68.1) (85,68.1) (90,68.1) (95,68.1)
};
\addlegendentry{Single-Pass LLM}
\addplot[gray, mark=o, thick, dotted] coordinates {
    (60,61.4) (65,61.4) (70,61.4) (75,61.4) (80,61.4) (85,61.4) (90,61.4) (95,61.4)
};
\addlegendentry{Template-Only}
\end{axis}
-->

The relationship between quality gate threshold and formatting accuracy shows diminishing returns above threshold 85. Increasing the threshold from 60 to 85 improves accuracy by 9.5 percentage points, but raising it further from 85 to 95 yields only 0.6 additional points while substantially increasing processing time due to additional iterations. The default thresholds (80/85/80) represent a practical operating point that balances quality and throughput.

## Accuracy by Content Type

<!-- TIKZ:
caption: Formatting accuracy by content type for each method.
label: fig:accuracy_by_type
code:
\begin{axis}[
    ybar,
    bar width=5pt,
    xlabel={Content Type},
    ylabel={Formatting Accuracy (\%)},
    ymin=40, ymax=100,
    symbolic x coords={Report, Conference, Magazine, Manual, Thesis},
    xtick=data,
    x tick label style={font=\scriptsize, rotate=15, anchor=east},
    legend pos=north east,
    legend style={font=\scriptsize},
    grid=major,
    width=\columnwidth,
    height=5.5cm,
    tick label style={font=\scriptsize},
    label style={font=\small},
    enlarge x limits=0.15
]
\addplot coordinates {(Report,95.4) (Conference,96.8) (Magazine,90.3) (Manual,93.1) (Thesis,94.2)};
\addplot coordinates {(Report,72.5) (Conference,82.1) (Magazine,54.7) (Manual,66.3) (Thesis,70.8)};
\addplot coordinates {(Report,65.2) (Conference,71.8) (Magazine,48.1) (Manual,59.4) (Thesis,62.5)};
\legend{PrintShop, Single-Pass LLM, Template-Only}
\end{axis}
-->

The grouped bar chart confirms that PrintShop maintains above 90% accuracy across all content types, while baseline methods show significant degradation on complex layouts such as magazine articles. The consistency of PrintShop's performance across diverse document types demonstrates the generalizability of the multi-agent approach.
