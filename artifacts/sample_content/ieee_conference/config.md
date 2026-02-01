# Document Configuration

## DISCLAIMER

**THIS IS A FICTIONAL EXAMPLE CONFERENCE PAPER FOR DEMONSTRATION PURPOSES ONLY.**

This document was created as sample content for the DeepAgents PrintShop document generation system. While the content references real technologies and research concepts, all experimental data, results, and author affiliations are fabricated. Any resemblance to actual published research is coincidental.

Do not cite this document as a factual source.

---

## Content Type
ieee_conference

## Project Metadata
- Title: FedEdge: Latency-Aware Federated Learning for Real-Time Defect Detection in Smart Manufacturing
- Authors:
  - Name: J. Chen
    Affiliation: Department of Computer Science, Eastfield Institute of Technology, Portland, OR, USA
    Email: jchen@eit.edu
  - Name: R. Vasquez
    Affiliation: Department of Industrial Engineering, Eastfield Institute of Technology, Portland, OR, USA
    Email: rvasquez@eit.edu
  - Name: M. Okonkwo
    Affiliation: Applied AI Lab, Northgate Systems Research, Austin, TX, USA
    Email: mokonkwo@northgatesys.com
- Conference: 2026 IEEE International Conference on Industrial Informatics (INDIN)
- Funding: This work was supported in part by the National Science Foundation under Grant No. 2055123.

## Abstract
Federated learning (FL) enables collaborative model training across distributed edge devices without centralizing sensitive manufacturing data. However, existing FL frameworks struggle with the strict latency requirements of real-time defect detection on resource-constrained edge hardware. We present FedEdge, a latency-aware federated learning framework that co-optimizes model accuracy and inference latency through adaptive model pruning and heterogeneity-aware aggregation. FedEdge introduces a dynamic pruning scheduler that tailors per-device model complexity based on available compute budgets, and a weighted aggregation strategy that accounts for statistical and hardware heterogeneity across factory-floor nodes. We evaluate FedEdge on a distributed testbed of 24 edge devices processing visual inspection data from three simulated production lines. Results show that FedEdge achieves 96.3% defect detection accuracy while reducing average inference latency by 41% compared to standard FedAvg, and maintains convergence within 5% of centralized training baselines. Our framework demonstrates that production-grade federated learning is viable for latency-critical manufacturing applications.

## Keywords
federated learning, edge computing, smart manufacturing, defect detection, model pruning, industrial IoT

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
