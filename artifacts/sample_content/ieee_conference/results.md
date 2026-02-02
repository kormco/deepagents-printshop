# Results and Discussion

## Overall Performance

Table I summarizes the defect detection accuracy and average inference latency across all methods after 100 communication rounds. FedEdge achieves 96.3% accuracy with an average inference latency of 34.2 ms across the heterogeneous testbed, compared to 94.1% accuracy and 57.8 ms latency for standard FedAvg. The centralized upper bound achieves 97.8% accuracy.

Notably, FedEdge is the only federated method that meets the 40 ms latency target across all device clusters. FedAvg and FedProx use the full un-pruned model and thus exceed the latency budget on Cluster B and C devices. PruneFL's static 50% pruning achieves lower latency than FedAvg but sacrifices 2.1% accuracy compared to FedEdge because its uniform pruning ratio is suboptimal for both high-end and low-end devices.

## Per-Cluster Analysis

The adaptive pruning scheduler produces distinct pruning ratios per cluster at convergence: Cluster A averages $\rho = 0.15$, Cluster B averages $\rho = 0.38$, and Cluster C averages $\rho = 0.62$. This heterogeneous pruning allows Cluster A devices to retain most of the model capacity (achieving 97.1% local accuracy) while Cluster C devices operate within latency budgets at 94.8% local accuracy — a graceful accuracy-latency tradeoff rather than the all-or-nothing choice imposed by uniform approaches.

## Convergence Behavior

FedEdge converges within 5% of its final accuracy by round 35, comparable to FedAvg (round 30) and faster than FedProx (round 42). The heterogeneity-aware aggregation weights stabilize after approximately 20 rounds as the staleness penalties adapt to consistent straggler patterns. The quality weighting provides a modest but consistent improvement of 0.4% accuracy compared to data-only weighting in an ablation study.

## Communication Efficiency

Top-$k$ gradient sparsification at $k = 10$ reduces per-round upload bandwidth from 21.2 MB to 2.3 MB per client, a 89% reduction. Over 100 rounds with 24 clients, this translates to a total upstream transfer of 5.5 GB compared to 50.9 GB without sparsification. We observe no statistically significant impact on final accuracy (p = 0.73 in a paired t-test across three seeds).

## Ablation Study

To isolate the contribution of each FedEdge component, we evaluate three ablation variants:

- **FedEdge w/o pruning**: Uses heterogeneity-aware aggregation but no adaptive pruning. Accuracy matches full FedEdge (96.1%) but latency remains high on Clusters B and C.
- **FedEdge w/o quality weighting**: Uses adaptive pruning with data-only aggregation weights. Accuracy drops to 95.9%, confirming the benefit of quality-aware weighting.
- **FedEdge w/o sparsification**: Full framework without gradient sparsification. Accuracy is unchanged (96.4%) but communication cost increases by 9x.

These results confirm that adaptive pruning is the primary driver of latency reduction, quality weighting provides a meaningful accuracy boost in non-IID settings, and gradient sparsification significantly reduces communication cost without accuracy penalty.
