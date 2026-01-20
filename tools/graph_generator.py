"""Graph Generator for Magazine Data Visualizations."""

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Set style for magazine-quality charts
plt.style.use('seaborn-v0_8-whitegrid')


class GraphGenerator:
    """Generate publication-quality graphs from CSV data."""

    def __init__(self, output_dir: str = "artifacts/sample_content/magazine/images"):
        """
        Initialize graph generator.

        Args:
            output_dir: Directory to save generated graphs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Magazine color palette
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'tertiary': '#F18F01',
            'quaternary': '#C73E1D',
            'quinary': '#3B1F2B',
            'light': '#E8E8E8',
            'dark': '#1A1A2E'
        }
        self.color_list = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#5C946E']

    def generate_adoption_chart(self, csv_path: str, output_name: str = "adoption_chart.png") -> str:
        """
        Generate adoption metrics chart showing year-over-year growth.

        Args:
            csv_path: Path to adoption_metrics.csv
            output_name: Output filename

        Returns:
            Path to generated chart
        """
        df = pd.read_csv(csv_path)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

        years = ['2024', '2025', '2026 Projected']
        x = range(len(years))
        width = 0.2

        metrics = df['Metric'].tolist()
        for i, metric in enumerate(metrics):
            values = df.iloc[i, 1:].values.astype(float)
            bars = ax.bar([xi + i * width for xi in x], values, width,
                         label=metric, color=self.color_list[i % len(self.color_list)])
            # Add value labels on bars
            for bar, val in zip(bars, values):
                ax.annotate(f'{val:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                           ha='center', va='bottom', fontsize=8)

        ax.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax.set_ylabel('Percentage / Minutes', fontsize=11, fontweight='bold')
        ax.set_title('AI Agent Adoption Metrics (2024-2026)', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks([xi + width * 1.5 for xi in x])
        ax.set_xticklabels(years)
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.set_ylim(0, 100)

        plt.tight_layout()
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[OK] Generated: {output_path}")
        return str(output_path)

    def generate_framework_comparison(self, csv_path: str, output_name: str = "framework_comparison.png") -> str:
        """
        Generate framework comparison bar chart.

        Args:
            csv_path: Path to framework_comparison.csv
            output_name: Output filename

        Returns:
            Path to generated chart
        """
        df = pd.read_csv(csv_path)

        fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=150)

        frameworks = df['Framework'].tolist()
        colors = [self.color_list[i % len(self.color_list)] for i in range(len(frameworks))]

        # Latency (lower is better)
        ax1 = axes[0]
        bars1 = ax1.barh(frameworks, df['Latency (ms)'], color=colors)
        ax1.set_xlabel('Latency (ms)', fontsize=10, fontweight='bold')
        ax1.set_title('Response Latency', fontsize=11, fontweight='bold')
        ax1.invert_xaxis()  # Lower is better, so invert
        for bar, val in zip(bars1, df['Latency (ms)']):
            ax1.annotate(f'{val}ms', xy=(val - 5, bar.get_y() + bar.get_height()/2),
                        ha='right', va='center', fontsize=8, color='white', fontweight='bold')

        # Token Efficiency
        ax2 = axes[1]
        bars2 = ax2.barh(frameworks, df['Token Efficiency'], color=colors)
        ax2.set_xlabel('Token Efficiency (%)', fontsize=10, fontweight='bold')
        ax2.set_title('Token Efficiency', fontsize=11, fontweight='bold')
        ax2.set_xlim(70, 100)
        for bar, val in zip(bars2, df['Token Efficiency']):
            ax2.annotate(f'{val}%', xy=(val - 1, bar.get_y() + bar.get_height()/2),
                        ha='right', va='center', fontsize=8, color='white', fontweight='bold')

        # Success Rate
        ax3 = axes[2]
        bars3 = ax3.barh(frameworks, df['Success Rate'], color=colors)
        ax3.set_xlabel('Success Rate (%)', fontsize=10, fontweight='bold')
        ax3.set_title('Success Rate', fontsize=11, fontweight='bold')
        ax3.set_xlim(85, 100)
        for bar, val in zip(bars3, df['Success Rate']):
            ax3.annotate(f'{val}%', xy=(val - 0.5, bar.get_y() + bar.get_height()/2),
                        ha='right', va='center', fontsize=8, color='white', fontweight='bold')

        plt.suptitle('Agent Framework Comparison', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()

        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[OK] Generated: {output_path}")
        return str(output_path)

    def generate_model_performance_radar(self, csv_path: str, output_name: str = "model_performance.png") -> str:
        """
        Generate model performance comparison chart.

        Args:
            csv_path: Path to model_performance.csv
            output_name: Output filename

        Returns:
            Path to generated chart
        """
        df = pd.read_csv(csv_path)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

        models = df['Model'].tolist()
        x = range(len(models))
        width = 0.25

        metrics = ['Tool Use Accuracy', 'Multi-Step Planning', 'Code Generation']

        for i, metric in enumerate(metrics):
            values = df[metric].values
            bars = ax.bar([xi + i * width for xi in x], values, width,
                         label=metric, color=self.color_list[i])
            for bar, val in zip(bars, values):
                ax.annotate(f'{val:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                           ha='center', va='bottom', fontsize=7)

        ax.set_xlabel('Model', fontsize=11, fontweight='bold')
        ax.set_ylabel('Score (%)', fontsize=11, fontweight='bold')
        ax.set_title('LLM Performance Comparison for Agent Tasks', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks([xi + width for xi in x])
        ax.set_xticklabels(models, rotation=15, ha='right')
        ax.legend(loc='lower right', fontsize=9)
        ax.set_ylim(80, 100)

        plt.tight_layout()
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[OK] Generated: {output_path}")
        return str(output_path)

    def generate_cost_comparison(self, csv_path: str, output_name: str = "cost_comparison.png") -> str:
        """
        Generate cost comparison chart.

        Args:
            csv_path: Path to model_performance.csv
            output_name: Output filename

        Returns:
            Path to generated chart
        """
        df = pd.read_csv(csv_path)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

        models = df['Model'].tolist()
        costs = df['Cost per 1M Tokens'].values
        colors = [self.color_list[i % len(self.color_list)] for i in range(len(models))]

        bars = ax.bar(models, costs, color=colors)

        # Add value labels
        for bar, cost in zip(bars, costs):
            ax.annotate(f'${cost:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                       ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_xlabel('Model', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cost per 1M Tokens ($)', fontsize=11, fontweight='bold')
        ax.set_title('LLM Cost Comparison', fontsize=14, fontweight='bold', pad=15)
        plt.xticks(rotation=15, ha='right')

        plt.tight_layout()
        output_path = self.output_dir / output_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"[OK] Generated: {output_path}")
        return str(output_path)

    def generate_all_charts(self, data_dir: str) -> List[str]:
        """
        Generate all charts from data directory.

        Args:
            data_dir: Directory containing CSV files

        Returns:
            List of paths to generated charts
        """
        data_path = Path(data_dir)
        generated = []

        print("Generating magazine charts...")
        print("=" * 50)

        # Adoption metrics
        adoption_csv = data_path / "adoption_metrics.csv"
        if adoption_csv.exists():
            generated.append(self.generate_adoption_chart(str(adoption_csv)))

        # Framework comparison
        framework_csv = data_path / "framework_comparison.csv"
        if framework_csv.exists():
            generated.append(self.generate_framework_comparison(str(framework_csv)))

        # Model performance
        model_csv = data_path / "model_performance.csv"
        if model_csv.exists():
            generated.append(self.generate_model_performance_radar(str(model_csv)))
            generated.append(self.generate_cost_comparison(str(model_csv)))

        print("=" * 50)
        print(f"[OK] Generated {len(generated)} charts")

        return generated


def main():
    """Generate charts for magazine."""
    generator = GraphGenerator()
    data_dir = "artifacts/sample_content/magazine/data"

    charts = generator.generate_all_charts(data_dir)

    print("\nGenerated charts:")
    for chart in charts:
        print(f"  - {chart}")


if __name__ == "__main__":
    main()
