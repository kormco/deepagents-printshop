# Experimental Setup

## Testbed Configuration

We evaluate FedEdge on a physical testbed comprising 24 edge devices organized into three production-line clusters of 8 devices each. The hardware configuration is intentionally heterogeneous to reflect real factory deployments:

- **Cluster A** (8 devices): NVIDIA Jetson Orin Nano (6-core ARM, 8 GB RAM, 1024-core GPU) — representing high-end edge nodes.
- **Cluster B** (8 devices): NVIDIA Jetson Xavier NX (6-core ARM, 8 GB RAM, 384-core GPU) — representing mid-range edge nodes.
- **Cluster C** (8 devices): Raspberry Pi 5 with Hailo-8L accelerator (4-core ARM, 8 GB RAM, 13 TOPS NPU) — representing lightweight edge nodes.

All devices are connected to the aggregation server over a local network with simulated bandwidth constraints of 100 Mbps per device.

## Dataset

We use the Simulated Manufacturing Visual Inspection (SMVI) dataset, a synthetic benchmark containing 180,000 labeled images across six defect categories (scratch, dent, crack, stain, misalignment, and no-defect). Images are 224x224 RGB captured at simulated inline inspection stations. The dataset is partitioned across clients using a Dirichlet distribution with concentration parameter $\beta = 0.5$ to create realistic non-IID splits, with each production line biased toward certain defect types.

## Model Architecture

The backbone model is EfficientNet-B0 [17] pretrained on ImageNet, with the classification head replaced by a 7-class output layer (six defect types plus no-defect). The full model contains 5.3M parameters with an un-pruned inference latency of approximately 28 ms on Cluster A devices, 52 ms on Cluster B, and 85 ms on Cluster C.

## Baselines

We compare FedEdge against the following baselines:

- **Centralized**: Standard EfficientNet-B0 trained on the combined dataset on a single GPU (upper bound on accuracy).
- **FedAvg** [4]: Standard federated averaging with uniform model across all devices.
- **FedProx** [9]: FedAvg with proximal regularization ($\mu = 0.01$).
- **PruneFL** [14]: Federated learning with static uniform pruning at 50% ratio.
- **Local-Only**: Each device trains independently on its local data (no federation).

## Training Configuration

All federated methods run for 100 communication rounds with $E = 5$ local epochs per round, batch size 32, and SGD with learning rate 0.01 and momentum 0.9. FedEdge uses $\alpha = 0.05$, $\rho_{\min} = 0.1$, $\rho_{\max} = 0.7$, and a target latency of $\tau_i = 40$ ms for all devices. Top-$k$ sparsification uses $k = 10$. All experiments are repeated three times with different random seeds, and we report mean and standard deviation.
