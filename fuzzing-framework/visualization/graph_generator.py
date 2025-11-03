"""
Graph Generator
Creates comparison graphs for research paper
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List


class GraphGenerator:
    """Generate comparison graphs for AFL++ vs AFL++ + PPO"""

    def __init__(self, metrics_dir: str, output_dir: str = "./graphs"):
        self.metrics_dir = Path(metrics_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load metrics
        self.baseline_df = None
        self.ppo_df = None
        self._load_metrics()

        # Set publication-quality style
        plt.style.use('seaborn-v0_8-paper')
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10

    def _load_metrics(self):
        """Load metrics from CSV files"""
        baseline_file = self.metrics_dir / "metrics_baseline.csv"
        ppo_file = self.metrics_dir / "metrics_ppo.csv"

        if baseline_file.exists():
            self.baseline_df = pd.read_csv(baseline_file)
            print(f"[Viz] Loaded baseline metrics: {len(self.baseline_df)} records")

        if ppo_file.exists():
            self.ppo_df = pd.read_csv(ppo_file)
            print(f"[Viz] Loaded PPO metrics: {len(self.ppo_df)} records")

    def generate_all_graphs(self):
        """Generate all comparison graphs"""
        print("\n[Viz] Generating comparison graphs...")

        if self.baseline_df is None or self.ppo_df is None:
            print("[Viz Error] Missing metrics data")
            return

        self.plot_code_coverage_over_time()
        self.plot_crash_discovery_rate()
        self.plot_execution_speed()
        self.plot_path_exploration()
        self.plot_combined_metrics()

        print(f"[Viz] All graphs saved to {self.output_dir}\n")

    def plot_code_coverage_over_time(self):
        """Generate code coverage over time graph (Fig. 2 in paper)"""
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot baseline
        ax.plot(self.baseline_df['time_hours'],
                self.baseline_df['coverage_rate'],
                marker='o',
                linestyle='-',
                linewidth=2,
                markersize=6,
                label='AFL++',
                color='#2E86AB')

        # Plot PPO
        ax.plot(self.ppo_df['time_hours'],
                self.ppo_df['coverage_rate'],
                marker='s',
                linestyle='--',
                linewidth=2,
                markersize=6,
                label='AFL++ + PPO',
                color='#A23B72')

        ax.set_xlabel('Time (Hours)', fontweight='bold')
        ax.set_ylabel('Code Coverage (%)', fontweight='bold')
        ax.set_title('Code Coverage Over Time', fontweight='bold', pad=20)
        ax.legend(loc='lower right', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        output_file = self.output_dir / "code_coverage_over_time.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")

    def plot_crash_discovery_rate(self):
        """Generate crash discovery rate graph"""
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot baseline
        ax.plot(self.baseline_df['time_hours'],
                self.baseline_df['crash_count'],
                marker='o',
                linestyle='-',
                linewidth=2,
                markersize=6,
                label='AFL++',
                color='#2E86AB')

        # Plot PPO
        ax.plot(self.ppo_df['time_hours'],
                self.ppo_df['crash_count'],
                marker='s',
                linestyle='--',
                linewidth=2,
                markersize=6,
                label='AFL++ + PPO',
                color='#A23B72')

        ax.set_xlabel('Time (Hours)', fontweight='bold')
        ax.set_ylabel('Unique Crashes Discovered', fontweight='bold')
        ax.set_title('Crash Discovery Rate Over Time', fontweight='bold', pad=20)
        ax.legend(loc='upper left', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        output_file = self.output_dir / "crash_discovery_rate.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")

    def plot_execution_speed(self):
        """Generate execution speed comparison bar chart (Fig. 3 in paper)"""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Calculate average speeds
        baseline_speed = self.baseline_df['exec_speed'].mean()
        ppo_speed = self.ppo_df['exec_speed'].mean()

        methods = ['AFL++', 'AFL++ + PPO']
        speeds = [baseline_speed, ppo_speed]
        colors = ['#2E86AB', '#A23B72']

        bars = ax.bar(methods, speeds, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

        # Add value labels on bars
        for bar, speed in zip(bars, speeds):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{speed:.1f}',
                   ha='center', va='bottom', fontweight='bold', fontsize=11)

        # Calculate improvement percentage
        improvement = ((ppo_speed - baseline_speed) / baseline_speed) * 100
        ax.text(0.5, max(speeds) * 0.9,
                f'Improvement: +{improvement:.1f}%',
                ha='center',
                transform=ax.transData,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=11,
                fontweight='bold')

        ax.set_ylabel('Execution Speed (Test Cases/sec)', fontweight='bold')
        ax.set_title('Execution Speed Comparison', fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')

        plt.tight_layout()
        output_file = self.output_dir / "execution_speed_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")

    def plot_path_exploration(self):
        """Generate unique paths exploration comparison"""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Final path counts
        baseline_paths = self.baseline_df['unique_paths'].iloc[-1]
        ppo_paths = self.ppo_df['unique_paths'].iloc[-1]

        methods = ['AFL++', 'AFL++ + PPO']
        paths = [baseline_paths, ppo_paths]
        colors = ['#2E86AB', '#A23B72']

        bars = ax.bar(methods, paths, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

        # Add value labels
        for bar, path_count in zip(bars, paths):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(path_count)}',
                   ha='center', va='bottom', fontweight='bold', fontsize=11)

        # Calculate improvement
        improvement = ((ppo_paths - baseline_paths) / baseline_paths) * 100
        ax.text(0.5, max(paths) * 0.9,
                f'Improvement: +{improvement:.1f}%',
                ha='center',
                transform=ax.transData,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5),
                fontsize=11,
                fontweight='bold')

        ax.set_ylabel('Unique Code Paths Explored', fontweight='bold')
        ax.set_title('Code Path Exploration Comparison', fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')

        plt.tight_layout()
        output_file = self.output_dir / "path_exploration_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")

    def plot_combined_metrics(self):
        """Generate combined 2x2 subplot with all key metrics"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # 1. Code Coverage
        ax1.plot(self.baseline_df['time_hours'], self.baseline_df['coverage_rate'],
                label='AFL++', marker='o', linewidth=2, color='#2E86AB')
        ax1.plot(self.ppo_df['time_hours'], self.ppo_df['coverage_rate'],
                label='AFL++ + PPO', marker='s', linewidth=2, linestyle='--', color='#A23B72')
        ax1.set_xlabel('Time (Hours)', fontweight='bold')
        ax1.set_ylabel('Code Coverage (%)', fontweight='bold')
        ax1.set_title('Code Coverage Over Time', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Crash Discovery
        ax2.plot(self.baseline_df['time_hours'], self.baseline_df['crash_count'],
                label='AFL++', marker='o', linewidth=2, color='#2E86AB')
        ax2.plot(self.ppo_df['time_hours'], self.ppo_df['crash_count'],
                label='AFL++ + PPO', marker='s', linewidth=2, linestyle='--', color='#A23B72')
        ax2.set_xlabel('Time (Hours)', fontweight='bold')
        ax2.set_ylabel('Unique Crashes', fontweight='bold')
        ax2.set_title('Crash Discovery Rate', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Execution Speed
        baseline_speed = self.baseline_df['exec_speed'].mean()
        ppo_speed = self.ppo_df['exec_speed'].mean()
        bars = ax3.bar(['AFL++', 'AFL++ + PPO'], [baseline_speed, ppo_speed],
                      color=['#2E86AB', '#A23B72'], alpha=0.8, edgecolor='black')
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        ax3.set_ylabel('Exec Speed (cases/sec)', fontweight='bold')
        ax3.set_title('Average Execution Speed', fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. Path Exploration
        ax4.plot(self.baseline_df['time_hours'], self.baseline_df['unique_paths'],
                label='AFL++', marker='o', linewidth=2, color='#2E86AB')
        ax4.plot(self.ppo_df['time_hours'], self.ppo_df['unique_paths'],
                label='AFL++ + PPO', marker='s', linewidth=2, linestyle='--', color='#A23B72')
        ax4.set_xlabel('Time (Hours)', fontweight='bold')
        ax4.set_ylabel('Unique Paths', fontweight='bold')
        ax4.set_title('Path Exploration Over Time', fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.suptitle('AFL++ vs AFL++ + PPO: Comprehensive Comparison',
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()

        output_file = self.output_dir / "combined_metrics_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")

    def generate_summary_table_image(self, summary: Dict):
        """Generate summary table as image for paper"""
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('tight')
        ax.axis('off')

        # Prepare table data
        headers = ['Metric', 'AFL++', 'AFL++ + PPO', 'Improvement']
        data = []

        if 'baseline' in summary and 'ppo' in summary:
            b = summary['baseline']
            p = summary['ppo']
            i = summary['improvement']

            data.append([
                'Code Coverage (%)',
                f"{b['final_coverage']:.2f}",
                f"{p['final_coverage']:.2f}",
                f"+{i['coverage_increase_pct']:.1f}%"
            ])
            data.append([
                'Unique Crashes',
                f"{b['total_crashes']}",
                f"{p['total_crashes']}",
                f"+{i['crash_increase_pct']:.1f}%"
            ])
            data.append([
                'Avg Speed (exec/s)',
                f"{b['avg_exec_speed']:.1f}",
                f"{p['avg_exec_speed']:.1f}",
                f"+{i['speed_increase_pct']:.1f}%"
            ])
            data.append([
                'Unique Paths',
                f"{b['total_paths']}",
                f"{p['total_paths']}",
                f"+{i['path_increase_pct']:.1f}%"
            ])

        table = ax.table(cellText=data, colLabels=headers,
                        cellLoc='center', loc='center',
                        colWidths=[0.3, 0.2, 0.25, 0.25])

        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)

        # Style header
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4A90E2')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Style rows
        for i in range(1, len(data) + 1):
            for j in range(len(headers)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#E8F4F8')

        plt.title('Performance Comparison Summary', fontsize=14, fontweight='bold', pad=20)

        output_file = self.output_dir / "summary_table.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[Viz] Saved: {output_file}")


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate comparison graphs")
    parser.add_argument(
        "--metrics-dir",
        default="./data/results/comparison",
        help="Directory containing metrics CSV files"
    )
    parser.add_argument(
        "--output-dir",
        default="./graphs",
        help="Output directory for graphs"
    )

    args = parser.parse_args()

    # Generate graphs
    generator = GraphGenerator(args.metrics_dir, args.output_dir)
    generator.generate_all_graphs()

    # Load and generate summary table
    json_file = Path(args.metrics_dir) / "metrics_history.json"
    if json_file.exists():
        with open(json_file, 'r') as f:
            history = json.load(f)

        # Calculate summary (simplified version)
        summary = {
            'baseline': {'final_coverage': 0, 'total_crashes': 0, 'avg_exec_speed': 0, 'total_paths': 0},
            'ppo': {'final_coverage': 0, 'total_crashes': 0, 'avg_exec_speed': 0, 'total_paths': 0},
            'improvement': {'coverage_increase_pct': 0, 'crash_increase_pct': 0,
                          'speed_increase_pct': 0, 'path_increase_pct': 0}
        }

        # You would populate this from actual data
        # generator.generate_summary_table_image(summary)

    print("\n[Viz] Graph generation complete!")
    print(f"[Viz] Graphs saved to: {args.output_dir}\n")


if __name__ == "__main__":
    main()
