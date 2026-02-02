# Conclusion

We presented FedEdge, a latency-aware federated learning framework for real-time defect detection in smart manufacturing environments. By combining adaptive per-device model pruning with heterogeneity-aware weighted aggregation, FedEdge achieves 96.3% defect detection accuracy while reducing inference latency by 41% compared to standard FedAvg on a heterogeneous testbed of 24 edge devices. The framework maintains convergence within 5% of centralized training baselines and reduces communication overhead by 89% through gradient sparsification.

Our results demonstrate that federated learning can meet the stringent latency and accuracy requirements of inline visual inspection without centralizing sensitive manufacturing data. The adaptive pruning scheduler provides an effective mechanism for balancing the accuracy-latency tradeoff across devices with widely varying compute capabilities.

Future work will explore extending FedEdge to non-visual inspection modalities (vibration, thermal), integrating continual learning to handle concept drift as production processes evolve, and evaluating deployment at larger scales with 100+ devices across geographically distributed facilities.
