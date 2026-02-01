# System Design

This section describes the FedEdge framework architecture, including the adaptive pruning scheduler, the heterogeneity-aware aggregation strategy, and the overall training pipeline.

## Overview

FedEdge operates in a standard FL topology with a central aggregation server and $N$ edge clients distributed across factory-floor inspection stations. Each client $i$ holds a local dataset $D_i$ of labeled inspection images and runs a local copy of a shared CNN backbone. The key innovation is that each client maintains a device-specific pruned variant of the global model, tailored to its available compute budget.

The training loop proceeds in communication rounds. At each round $t$:
1. The server broadcasts the current global model parameters $w^t$.
2. Each client $i$ receives $w^t$, applies its local pruning mask $m_i^t$, and trains the pruned model on $D_i$ for $E$ local epochs.
3. Clients report updated parameters and latency telemetry to the server.
4. The server performs heterogeneity-aware weighted aggregation to produce $w^{t+1}$.

## Adaptive Pruning Scheduler

The pruning scheduler on each client $i$ determines a structured pruning ratio $\rho_i^t \in [0, 1)$ at each round $t$ based on a target inference latency $\tau_i$. Given the measured inference latency $\hat{\tau}_i^{t-1}$ of the model at the previous round, the scheduler adjusts $\rho_i^t$ using a proportional controller:

$$\rho_i^t = \rho_i^{t-1} + \alpha \cdot \frac{\hat{\tau}_i^{t-1} - \tau_i}{\tau_i}$$

where $\alpha$ is a step-size hyperparameter. The ratio is clamped to $[\rho_{\min}, \rho_{\max}]$ to prevent excessive pruning that would degrade accuracy below usable thresholds.

Pruning is applied at the filter level: for each convolutional layer, filters are ranked by their $\ell_1$-norm, and the bottom $\rho_i^t$ fraction is masked to zero. This structured approach ensures that the pruned model can leverage hardware-accelerated dense operations without requiring sparse computation support.

## Heterogeneity-Aware Aggregation

Standard FedAvg computes the global model as a weighted average of client updates, weighted by dataset size $|D_i|$. FedEdge extends this with a composite weighting scheme that accounts for three factors:

$$w^{t+1} = \sum_{i=1}^{N} \lambda_i^t \cdot w_i^t$$

where the weight $\lambda_i^t$ combines:

- **Data weight** $\lambda_i^{\text{data}} = |D_i| / \sum_j |D_j|$: proportional to local dataset size.
- **Quality weight** $\lambda_i^{\text{qual}}$: based on local validation accuracy, giving higher influence to clients with better-performing local models.
- **Staleness penalty** $\lambda_i^{\text{stale}}$: a discount factor applied to clients that fail to report updates within the round deadline, reducing straggler impact.

The final weight is: $\lambda_i^t = \lambda_i^{\text{data}} \cdot \lambda_i^{\text{qual}} \cdot \lambda_i^{\text{stale}} / Z^t$, where $Z^t$ is a normalizing constant.

## Communication Protocol

To reduce communication overhead, FedEdge employs top-$k$ gradient sparsification [19] on the upstream channel (client to server). Each client transmits only the top $k\%$ of gradient magnitudes along with their indices. The server reconstructs the sparse updates and applies them during aggregation. This reduces per-round upload bandwidth by approximately 90% at $k = 10$, with negligible impact on convergence in our experiments.
