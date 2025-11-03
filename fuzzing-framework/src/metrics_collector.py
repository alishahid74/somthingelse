"""
Metrics Collector
Collects and stores fuzzing metrics over time for comparison
"""

import json
import time
from typing import Dict, List
from pathlib import Path
import pandas as pd


class MetricsCollector:
    """Collects metrics from both baseline and PPO fuzzing runs"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_history = {
            'baseline': [],
            'ppo': []
        }

        self.start_time = time.time()

    def record_metrics(self, mode: str, metrics: Dict):
        """
        Record metrics snapshot

        Args:
            mode: "baseline" or "ppo"
            metrics: Dictionary of current metrics
        """
        timestamp = time.time() - self.start_time

        record = {
            'timestamp': timestamp,
            'time_hours': timestamp / 3600,
            **metrics
        }

        self.metrics_history[mode].append(record)

    def get_history(self, mode: str) -> List[Dict]:
        """Get metrics history for a mode"""
        return self.metrics_history[mode]

    def save_metrics(self):
        """Save metrics to JSON and CSV files"""
        # Save as JSON
        json_file = self.output_dir / "metrics_history.json"
        with open(json_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)

        print(f"[Metrics] Saved to {json_file}")

        # Save as CSV for easy analysis
        for mode in ['baseline', 'ppo']:
            if self.metrics_history[mode]:
                df = pd.DataFrame(self.metrics_history[mode])
                csv_file = self.output_dir / f"metrics_{mode}.csv"
                df.to_csv(csv_file, index=False)
                print(f"[Metrics] Saved {mode} metrics to {csv_file}")

    def load_metrics(self, json_file: str):
        """Load previously saved metrics"""
        with open(json_file, 'r') as f:
            self.metrics_history = json.load(f)

    def get_summary(self) -> Dict:
        """Get summary statistics for comparison"""
        summary = {}

        for mode in ['baseline', 'ppo']:
            if not self.metrics_history[mode]:
                continue

            history = self.metrics_history[mode]
            final_metrics = history[-1]

            summary[mode] = {
                'final_coverage': final_metrics['coverage_rate'],
                'total_crashes': final_metrics['crash_count'],
                'avg_exec_speed': sum(m['exec_speed'] for m in history) / len(history),
                'max_exec_speed': max(m['exec_speed'] for m in history),
                'total_paths': final_metrics['unique_paths'],
                'runtime_hours': final_metrics['time_hours']
            }

        # Calculate improvements
        if 'baseline' in summary and 'ppo' in summary:
            baseline = summary['baseline']
            ppo = summary['ppo']

            summary['improvement'] = {
                'coverage_increase_pct': (
                    (ppo['final_coverage'] - baseline['final_coverage']) /
                    max(baseline['final_coverage'], 0.01) * 100
                ),
                'crash_increase_pct': (
                    (ppo['total_crashes'] - baseline['total_crashes']) /
                    max(baseline['total_crashes'], 1) * 100
                ),
                'speed_increase_pct': (
                    (ppo['avg_exec_speed'] - baseline['avg_exec_speed']) /
                    max(baseline['avg_exec_speed'], 1) * 100
                ),
                'path_increase_pct': (
                    (ppo['total_paths'] - baseline['total_paths']) /
                    max(baseline['total_paths'], 1) * 100
                )
            }

        return summary

    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("FUZZING COMPARISON SUMMARY")
        print("="*60)

        for mode in ['baseline', 'ppo']:
            if mode not in summary:
                continue

            mode_name = "AFL++ (Baseline)" if mode == "baseline" else "AFL++ + PPO"
            print(f"\n{mode_name}:")
            print(f"  Coverage: {summary[mode]['final_coverage']:.2f}%")
            print(f"  Crashes: {summary[mode]['total_crashes']}")
            print(f"  Avg Speed: {summary[mode]['avg_exec_speed']:.2f} exec/sec")
            print(f"  Unique Paths: {summary[mode]['total_paths']}")
            print(f"  Runtime: {summary[mode]['runtime_hours']:.2f} hours")

        if 'improvement' in summary:
            print(f"\nImprovements (PPO vs Baseline):")
            print(f"  Coverage: +{summary['improvement']['coverage_increase_pct']:.1f}%")
            print(f"  Crashes: +{summary['improvement']['crash_increase_pct']:.1f}%")
            print(f"  Speed: +{summary['improvement']['speed_increase_pct']:.1f}%")
            print(f"  Paths: +{summary['improvement']['path_increase_pct']:.1f}%")

        print("="*60 + "\n")

    def export_for_paper(self, filename: str = "paper_results.txt"):
        """Export formatted results for research paper"""
        summary = self.get_summary()
        output_file = self.output_dir / filename

        with open(output_file, 'w') as f:
            f.write("EXPERIMENTAL RESULTS\n")
            f.write("="*60 + "\n\n")

            # Table 1: Performance Comparison
            f.write("Table: Performance Comparison\n")
            f.write("-"*60 + "\n")
            f.write(f"{'Metric':<25} {'AFL++':<15} {'AFL++ + PPO':<15} {'Improvement':<15}\n")
            f.write("-"*60 + "\n")

            if 'baseline' in summary and 'ppo' in summary:
                b = summary['baseline']
                p = summary['ppo']
                i = summary['improvement']

                f.write(f"{'Code Coverage (%)':<25} {b['final_coverage']:<15.2f} "
                       f"{p['final_coverage']:<15.2f} {i['coverage_increase_pct']:<15.1f}%\n")
                f.write(f"{'Unique Crashes':<25} {b['total_crashes']:<15} "
                       f"{p['total_crashes']:<15} {i['crash_increase_pct']:<15.1f}%\n")
                f.write(f"{'Exec Speed (exec/s)':<25} {b['avg_exec_speed']:<15.1f} "
                       f"{p['avg_exec_speed']:<15.1f} {i['speed_increase_pct']:<15.1f}%\n")
                f.write(f"{'Unique Paths':<25} {b['total_paths']:<15} "
                       f"{p['total_paths']:<15} {i['path_increase_pct']:<15.1f}%\n")

            f.write("-"*60 + "\n")

        print(f"[Metrics] Paper results exported to {output_file}")
