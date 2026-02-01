# Introduction

The rapid adoption of Industry 4.0 principles has driven a surge in sensor-equipped production lines capable of generating vast quantities of visual inspection data. Real-time defect detection is critical in these environments: identifying surface cracks, dimensional deviations, and assembly errors within milliseconds can prevent costly downstream failures and reduce scrap rates by up to 30% [1]. Deep learning models, particularly convolutional neural networks (CNNs), have demonstrated strong performance on these tasks when trained on large, centralized datasets [2].

However, centralizing manufacturing data raises significant concerns. Proprietary process data is commercially sensitive, and transferring high-resolution image streams from factory floors to cloud servers introduces bandwidth bottlenecks and latency penalties incompatible with real-time requirements [3]. Federated learning (FL) offers an attractive alternative by training a shared global model across distributed devices while keeping raw data local [4].

Despite its promise, deploying FL in manufacturing environments presents challenges that standard frameworks such as FedAvg [4] do not adequately address. First, edge devices on factory floors exhibit substantial hardware heterogeneity — ranging from embedded GPUs to lightweight accelerators — leading to stragglers that delay synchronous aggregation rounds. Second, production lines generate statistically non-IID data distributions, as defect types and frequencies vary across facilities. Third, inference latency constraints in real-time inspection pipelines demand models that are not only accurate but also fast enough to operate within fixed cycle times, often under 50 ms per frame [5].

In this paper, we present FedEdge, a latency-aware federated learning framework designed to address these challenges. FedEdge makes three key contributions:

- **Adaptive model pruning scheduler**: A dynamic pruning mechanism that adjusts per-device model complexity based on local compute budgets, ensuring that each edge node runs the largest model it can within its latency constraint.
- **Heterogeneity-aware weighted aggregation**: An aggregation strategy that weights client updates by both data quality and hardware capability, reducing the impact of stragglers and statistical skew.
- **Production-validated evaluation**: A comprehensive evaluation on a distributed testbed of 24 edge devices processing visual inspection data from three simulated production lines, demonstrating practical viability for manufacturing deployment.

Our results show that FedEdge achieves 96.3% defect detection accuracy while reducing inference latency by 41% compared to standard FedAvg, closing the gap to within 5% of centralized training baselines.
