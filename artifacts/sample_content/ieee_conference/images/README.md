# IEEE Conference Sample — Figure Guide

All figures for this paper should be generated as **inline TikZ/pgfplots** during LaTeX compilation. Do NOT use pre-rendered image files.

## Figure 1: FedEdge System Architecture
- **Placement**: System Design section
- **Type**: TikZ block diagram
- **Content**: Show aggregation server at top, three device clusters below (Cluster A: Orin Nano, Cluster B: Xavier NX, Cluster C: RPi 5 + Hailo), with arrows indicating model broadcast (downward) and gradient upload (upward). Label each cluster with its converged pruning ratio (0.15, 0.38, 0.62). Show production lines beneath each cluster.
- **Width**: Full column width (`\columnwidth`)
- **Libraries**: `shapes.geometric`, `arrows.meta`, `positioning`, `fit`

## Figure 2: Convergence Curves
- **Placement**: Results and Discussion section
- **Type**: pgfplots line chart
- **Content**: Accuracy (%) vs. Communication Round (0–100) for all methods: Centralized (dashed horizontal at 97.8%), FedEdge (96.3%), FedProx (94.7%), FedAvg (94.1%), PruneFL (94.2%), Local-Only (88.4%). Use distinct colors and a legend.
- **Width**: Full column width (`\columnwidth`)
- **Data points**: See convergence data below

### Convergence Data
```
Round, FedEdge, FedAvg, FedProx, PruneFL, Local-Only
0,     52.3,   51.2,   51.8,    50.5,    50.0
10,    78.1,   71.9,   73.5,    72.4,    64.2
20,    88.9,   82.5,   84.1,    83.0,    73.5
30,    93.1,   88.0,   89.5,    88.2,    79.4
40,    94.9,   90.9,   92.1,    91.0,    83.2
50,    95.6,   92.4,   93.4,    92.5,    85.6
60,    95.9,   93.1,   94.0,    93.3,    86.9
70,    96.1,   93.6,   94.3,    93.7,    87.6
80,    96.2,   93.8,   94.5,    94.0,    88.0
90,    96.3,   94.0,   94.6,    94.1,    88.2
100,   96.3,   94.1,   94.7,    94.2,    88.4
```

## Figure 3: Per-Cluster Latency Comparison (Optional)
- **Placement**: Results and Discussion section
- **Type**: pgfplots grouped bar chart
- **Content**: Inference latency (ms) per cluster for FedEdge vs FedAvg vs PruneFL. Include a horizontal dashed line at 40 ms marking the latency target.
- **Width**: Full column width (`\columnwidth`)
