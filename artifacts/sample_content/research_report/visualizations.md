# Visualizations

## Performance Comparison

<!-- IMAGE: images/performance_comparison.png
caption: Performance Comparison Across Model Architectures
label: fig:performance_comparison
-->

The performance comparison chart illustrates the relative accuracy, training efficiency, and inference speed across different model architectures evaluated in this study. Transformer-based models consistently demonstrate superior accuracy metrics while maintaining competitive inference speeds compared to traditional recurrent architectures.

## Training Convergence

<!-- IMAGE: images/training_convergence.png
caption: Training Loss Convergence Over Epochs
label: fig:training_convergence
-->

The training convergence plot tracks loss reduction across training epochs for each model variant. Models leveraging attention mechanisms exhibit faster convergence rates, typically reaching stable loss values within fewer training iterations than baseline approaches.

## Neural Network Architecture

<!-- TIKZ:
caption: Neural Network Architecture
label: fig:neural_net
code:
\node[circle, draw, minimum size=1cm] (input) at (0,0) {Input};
\node[circle, draw, minimum size=1cm] (hidden1) at (3,1) {H1};
\node[circle, draw, minimum size=1cm] (hidden2) at (3,-1) {H2};
\node[circle, draw, minimum size=1cm] (output) at (6,0) {Output};
\draw[->] (input) -- (hidden1);
\draw[->] (input) -- (hidden2);
\draw[->] (hidden1) -- (output);
\draw[->] (hidden2) -- (output);
-->

The neural network architecture diagram illustrates the feed-forward topology used in our baseline model comparison. The architecture consists of an input layer, two hidden units, and an output layer, demonstrating the fundamental structure upon which transformer attention mechanisms are built.
