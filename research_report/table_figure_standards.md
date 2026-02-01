# Table and Figure Formatting Standards

## Professional Tables with Booktabs
```latex
\usepackage{booktabs}
\begin{table}[htbp]
\centering
\caption{Descriptive table caption}
\label{tab:example}
\begin{tabular}{lcc}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
Data 1 & Data 2 & Data 3 \\
Data 4 & Data 5 & Data 6 \\
\bottomrule
\end{tabular}
\end{table}
```

## Figure Best Practices
```latex
\usepackage{graphicx}
\usepackage{float}
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{figure.png}
\caption{Clear, descriptive figure caption}
\label{fig:example}
\end{figure}
```

## Caption Guidelines
- Tables: Caption above the table
- Figures: Caption below the figure
- Use descriptive, self-contained captions
- Reference all tables and figures in text
- Use consistent numbering and labeling
