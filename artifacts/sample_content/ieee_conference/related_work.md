# Related Work

## Federated Learning in Industrial Settings

Federated learning was introduced by McMahan et al. [4] as a privacy-preserving distributed training paradigm. Subsequent work has adapted FL for industrial applications, including predictive maintenance [6], quality control [7], and anomaly detection in IoT networks [8]. Li et al. [9] proposed FedProx to handle systems heterogeneity by adding a proximal term to the local objective, while Karimireddy et al. [10] introduced SCAFFOLD to correct for client drift in non-IID settings. However, these methods primarily optimize for model convergence and accuracy without explicitly considering inference latency constraints on heterogeneous edge hardware.

## Model Compression for Edge Deployment

Model pruning [11], quantization [12], and knowledge distillation [13] are well-established techniques for reducing inference cost on resource-constrained devices. Recent work has explored integrating compression with federated learning: PruneFL [14] applies structured pruning during FL training, and FedMask [15] learns personalized binary masks for each client. These approaches treat compression as a static or globally uniform operation. In contrast, FedEdge dynamically adapts pruning ratios per device based on real-time compute budget feedback, enabling heterogeneous model configurations within a single federation.

## Defect Detection in Manufacturing

Vision-based defect detection has benefited enormously from deep learning [2]. Architectures such as ResNet [16], EfficientNet [17], and YOLO variants [18] have been deployed for surface inspection, dimensional measurement, and assembly verification. Most production deployments rely on centralized training with on-premise inference [5]. Recent efforts to combine FL with manufacturing inspection [7] have shown promising accuracy results but have not addressed the latency requirements of inline inspection, where inference must complete within fixed production cycle times.
