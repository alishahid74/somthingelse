"""
Experiment Runner
Main orchestrator for running fuzzing experiments with and without PPO
"""

import yaml
import time
import argparse
from pathlib import Path
from typing import Dict

from afl_wrapper import AFLWrapper
from ppo_agent import PPOAgent
from feedback_analyzer import FeedbackAnalyzer
from metrics_collector import MetricsCollector


class ExperimentRunner:
    """Main experiment orchestrator"""

    def __init__(self, afl_config_path: str, ppo_config_path: str):
        # Load configurations
        with open(afl_config_path, 'r') as f:
            self.afl_config = yaml.safe_load(f)['afl']

        with open(ppo_config_path, 'r') as f:
            self.ppo_config = yaml.safe_load(f)['ppo']

        self.metrics_collector = MetricsCollector("./data/results/comparison")

    def run_baseline(self, target_binary: str, duration: int):
        """
        Run baseline AFL++ fuzzing without PPO

        Args:
            target_binary: Path to target binary
            duration: Experiment duration in seconds
        """
        print("\n" + "="*60)
        print("RUNNING BASELINE EXPERIMENT (AFL++ only)")
        print("="*60 + "\n")

        afl = AFLWrapper(self.afl_config)
        afl.setup(target_binary, mode="baseline")
        afl.start_fuzzing(target_binary)

        if not afl.is_running():
            print("[Error] Failed to start AFL++ fuzzer")
            return

        # Monitor and collect metrics
        start_time = time.time()
        update_interval = 60  # Update every minute

        try:
            while (time.time() - start_time) < duration:
                time.sleep(update_interval)

                metrics = afl.get_metrics()
                self.metrics_collector.record_metrics('baseline', metrics)

                # Print progress
                print(f"[Baseline] Runtime: {metrics['runtime']}s | "
                      f"Coverage: {metrics['coverage_rate']:.2f}% | "
                      f"Crashes: {metrics['crash_count']} | "
                      f"Speed: {metrics['exec_speed']:.1f} exec/s")

        except KeyboardInterrupt:
            print("\n[Baseline] Interrupted by user")

        finally:
            afl.stop_fuzzing()
            results = afl.export_results()
            print(f"\n[Baseline] Experiment completed")
            print(f"[Baseline] Results saved to {afl.output_dir}")

        return results

    def run_ppo_enhanced(self, target_binary: str, duration: int):
        """
        Run PPO-enhanced AFL++ fuzzing

        Args:
            target_binary: Path to target binary
            duration: Experiment duration in seconds
        """
        print("\n" + "="*60)
        print("RUNNING PPO-ENHANCED EXPERIMENT (AFL++ + PPO)")
        print("="*60 + "\n")

        # Initialize components
        afl = AFLWrapper(self.afl_config)
        ppo = PPOAgent(self.ppo_config)
        analyzer = FeedbackAnalyzer()

        afl.setup(target_binary, mode="ppo")
        afl.start_fuzzing(target_binary)

        if not afl.is_running():
            print("[Error] Failed to start AFL++ fuzzer")
            return

        # PPO training loop
        start_time = time.time()
        update_interval = 60  # Check every minute
        ppo_update_counter = 0

        prev_metrics = None

        try:
            while (time.time() - start_time) < duration:
                time.sleep(update_interval)

                # Get current metrics
                curr_metrics = afl.get_metrics()
                self.metrics_collector.record_metrics('ppo', curr_metrics)

                # PPO decision making
                if prev_metrics is not None:
                    # Get state
                    state = ppo.get_state_vector(curr_metrics)

                    # Select mutation strategy
                    action, log_prob, value = ppo.select_action(state)

                    # Apply mutation strategy to AFL++
                    afl.apply_mutation_strategy(action)

                    # Calculate reward
                    reward = ppo.compute_reward(prev_metrics, curr_metrics)

                    # Store transition
                    done = (time.time() - start_time) >= duration
                    ppo.store_transition(state, action, reward, log_prob, value, done)

                    # Update PPO periodically
                    ppo_update_counter += 1
                    if ppo_update_counter >= self.ppo_config['update_interval']:
                        loss = ppo.update()
                        print(f"[PPO] Model updated | Loss: {loss:.4f}")
                        ppo_update_counter = 0

                prev_metrics = curr_metrics.copy()

                # Print progress
                print(f"[PPO] Runtime: {curr_metrics['runtime']}s | "
                      f"Coverage: {curr_metrics['coverage_rate']:.2f}% | "
                      f"Crashes: {curr_metrics['crash_count']} | "
                      f"Speed: {curr_metrics['exec_speed']:.1f} exec/s")

        except KeyboardInterrupt:
            print("\n[PPO] Interrupted by user")

        finally:
            # Final PPO update
            if len(ppo.buffer['states']) > 0:
                loss = ppo.update()
                print(f"[PPO] Final model update | Loss: {loss:.4f}")

            # Save PPO model
            model_path = Path(self.afl_config['output_dir']) / "ppo_model.pt"
            ppo.save_model(str(model_path))
            print(f"[PPO] Model saved to {model_path}")

            afl.stop_fuzzing()
            results = afl.export_results()
            print(f"\n[PPO] Experiment completed")
            print(f"[PPO] Results saved to {afl.output_dir}")

        return results

    def run_comparison(self, target_binary: str, duration: int):
        """
        Run both experiments sequentially for comparison

        Args:
            target_binary: Path to target binary
            duration: Duration for each experiment in seconds
        """
        print("\n" + "="*70)
        print(" FUZZING COMPARISON EXPERIMENT: AFL++ vs AFL++ + PPO")
        print("="*70 + "\n")

        print(f"Target Binary: {target_binary}")
        print(f"Duration per experiment: {duration / 3600:.2f} hours")
        print(f"Total estimated time: {duration * 2 / 3600:.2f} hours\n")

        # Run baseline first
        baseline_results = self.run_baseline(target_binary, duration)

        print("\n" + "-"*70)
        print(" Baseline experiment completed. Starting PPO experiment...")
        print("-"*70 + "\n")

        time.sleep(5)  # Brief pause between experiments

        # Run PPO-enhanced
        ppo_results = self.run_ppo_enhanced(target_binary, duration)

        # Save all metrics
        self.metrics_collector.save_metrics()

        # Print comparison summary
        self.metrics_collector.print_summary()

        # Export results for paper
        self.metrics_collector.export_for_paper()

        print("\n" + "="*70)
        print(" EXPERIMENTS COMPLETED")
        print("="*70)
        print(f"\nResults saved to: {self.metrics_collector.output_dir}")
        print("\nNext steps:")
        print("  1. Run visualization script to generate graphs")
        print("  2. Review metrics in CSV files")
        print("  3. Analyze crashes in output directories\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run AFL++ fuzzing experiments with and without PPO"
    )

    parser.add_argument(
        "target_binary",
        help="Path to target binary to fuzz"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=3600,
        help="Duration for each experiment in seconds (default: 3600 = 1 hour)"
    )

    parser.add_argument(
        "--mode",
        choices=["baseline", "ppo", "comparison"],
        default="comparison",
        help="Experiment mode: baseline, ppo, or comparison (default: comparison)"
    )

    parser.add_argument(
        "--afl-config",
        default="./config/afl_config.yaml",
        help="Path to AFL++ configuration file"
    )

    parser.add_argument(
        "--ppo-config",
        default="./config/ppo_config.yaml",
        help="Path to PPO configuration file"
    )

    args = parser.parse_args()

    # Validate target binary
    if not Path(args.target_binary).exists():
        print(f"Error: Target binary not found: {args.target_binary}")
        return 1

    # Create runner
    runner = ExperimentRunner(args.afl_config, args.ppo_config)

    # Run experiment(s)
    if args.mode == "baseline":
        runner.run_baseline(args.target_binary, args.duration)
    elif args.mode == "ppo":
        runner.run_ppo_enhanced(args.target_binary, args.duration)
    else:
        runner.run_comparison(args.target_binary, args.duration)

    return 0


if __name__ == "__main__":
    exit(main())
