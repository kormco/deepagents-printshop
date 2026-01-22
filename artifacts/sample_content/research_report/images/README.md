# Image Assets

This directory contains image assets for the LaTeX report.

## Available Images

**performance_comparison.png**
- Description: A dual-panel chart showing (1) Accuracy and F1 Score comparison across models as grouped bar chart, and (2) Speed-Accuracy trade-off as scatter plot
- Placement: Results section, after discussing the performance metrics comparison
- Caption suggestion: "Model Performance Comparison: (a) Accuracy and F1 Score metrics for each model, (b) Speed-accuracy trade-off showing inference time vs accuracy"
- Width: Full page width recommended (0.9\textwidth)

## Sample Images Needed

To fully demonstrate the LaTeX report capabilities, place the following types of images in this directory:

1. **sample_architecture.png** - A diagram showing neural network architecture
2. **results_graph.jpg** - A graph or chart showing experimental results
3. **logo.png** - An organization or project logo

## Supported Formats

- PNG (recommended for diagrams and screenshots)
- JPG/JPEG (recommended for photographs)
- EPS (vector graphics, recommended for publication)
- SVG (vector graphics, will be converted to PDF/EPS)

## Usage in Reports

Images will be included in the LaTeX document using:
- `\includegraphics` for standard figures
- `wrapfig` environment for text-wrapped images
- `subfigure` environment for multiple related images

## Note

For testing purposes, the agent can work without actual image files by commenting out image inclusion commands in the LaTeX output.
