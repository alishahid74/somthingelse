"""
AFL++ Wrapper
Interface for controlling AFL++ fuzzer and collecting feedback
"""

import subprocess
import os
import time
import json
import psutil
from typing import Dict, Optional
from pathlib import Path


class AFLWrapper:
    """Wrapper for AFL++ fuzzer"""

    def __init__(self, config: Dict):
        self.config = config
        self.process = None
        self.output_dir = None
        self.stats_file = None
        self.start_time = None

    def setup(self, target_binary: str, mode: str = "baseline"):
        """
        Setup AFL++ fuzzing environment

        Args:
            target_binary: Path to target binary
            mode: "baseline" or "ppo"
        """
        timestamp = int(time.time())
        self.output_dir = Path(self.config['output_dir']) / f"{mode}_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats_file = self.output_dir / "fuzzer_stats"

        print(f"[AFL Setup] Output directory: {self.output_dir}")
        print(f"[AFL Setup] Target binary: {target_binary}")
        print(f"[AFL Setup] Mode: {mode}")

    def start_fuzzing(self, target_binary: str, target_args: str = "@@"):
        """Start AFL++ fuzzing process"""
        if self.process is not None:
            print("[AFL] Fuzzing already running")
            return

        afl_cmd = [
            self.config['binary_path'],
            "-i", self.config['input_dir'],
            "-o", str(self.output_dir),
            "-t", str(self.config['timeout']),
            "-m", str(self.config['memory_limit'])
        ]

        # Add QEMU mode if enabled
        if self.config.get('qemu_mode', False):
            afl_cmd.append("-Q")

        # Add target binary and arguments
        afl_cmd.extend(["--", target_binary])
        if target_args:
            afl_cmd.append(target_args)

        print(f"[AFL] Starting fuzzer: {' '.join(afl_cmd)}")

        try:
            self.process = subprocess.Popen(
                afl_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.start_time = time.time()
            print(f"[AFL] Fuzzer started (PID: {self.process.pid})")
        except Exception as e:
            print(f"[AFL Error] Failed to start fuzzer: {e}")
            self.process = None

    def stop_fuzzing(self):
        """Stop AFL++ fuzzing process"""
        if self.process is None:
            return

        print("[AFL] Stopping fuzzer...")
        try:
            self.process.terminate()
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("[AFL] Force killing fuzzer...")
            self.process.kill()

        self.process = None
        print("[AFL] Fuzzer stopped")

    def get_stats(self) -> Dict:
        """Read AFL++ fuzzer statistics"""
        if not self.stats_file or not self.stats_file.exists():
            return {}

        stats = {}
        try:
            with open(self.stats_file, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        stats[key.strip()] = value.strip()
        except Exception as e:
            print(f"[AFL] Error reading stats: {e}")

        return stats

    def get_metrics(self) -> Dict:
        """
        Extract key metrics from AFL++ stats

        Returns:
            Dictionary with normalized metrics
        """
        stats = self.get_stats()

        if not stats:
            return {
                'coverage_rate': 0.0,
                'crash_count': 0,
                'exec_speed': 0.0,
                'queue_size': 0,
                'unique_paths': 0,
                'pending_paths': 0,
                'runtime': 0
            }

        # Parse relevant metrics
        metrics = {
            'coverage_rate': self._parse_coverage(stats),
            'crash_count': int(stats.get('unique_crashes', 0)),
            'exec_speed': float(stats.get('execs_per_sec', 0)),
            'queue_size': int(stats.get('paths_total', 0)),
            'unique_paths': int(stats.get('paths_found', 0)),
            'pending_paths': int(stats.get('pending_total', 0)),
            'runtime': int(time.time() - self.start_time) if self.start_time else 0
        }

        return metrics

    def _parse_coverage(self, stats: Dict) -> float:
        """Calculate coverage percentage from AFL++ bitmap"""
        # AFL++ tracks coverage via bitmap density
        bitmap_cvg = stats.get('bitmap_cvg', '0.00%')
        try:
            return float(bitmap_cvg.rstrip('%'))
        except:
            return 0.0

    def get_queue_files(self) -> list:
        """Get list of test cases in queue"""
        queue_dir = self.output_dir / "queue"
        if not queue_dir.exists():
            return []

        return list(queue_dir.glob("id:*"))

    def get_crashes(self) -> list:
        """Get list of crashes found"""
        crashes_dir = self.output_dir / "crashes"
        if not crashes_dir.exists():
            return []

        crashes = list(crashes_dir.glob("id:*"))
        # Filter out README.txt
        return [c for c in crashes if c.name != "README.txt"]

    def apply_mutation_strategy(self, strategy: int):
        """
        Apply specific mutation strategy (for PPO mode)

        Args:
            strategy: Mutation strategy ID
                0: Bit flips
                1: Byte flips
                2: Arithmetic
                3: Havoc
                4: Splice
        """
        # In a real implementation, this would communicate with AFL++
        # to adjust mutation strategies dynamically
        # For now, this is a placeholder for the interface
        strategy_names = [
            "bitflip", "byteflip", "arithmetic", "havoc", "splice"
        ]

        if 0 <= strategy < len(strategy_names):
            print(f"[AFL] Applying mutation strategy: {strategy_names[strategy]}")
            # TODO: Implement custom mutator or AFL++ fork for dynamic strategy

    def is_running(self) -> bool:
        """Check if fuzzer is still running"""
        if self.process is None:
            return False

        return self.process.poll() is None

    def get_runtime(self) -> int:
        """Get fuzzing runtime in seconds"""
        if self.start_time is None:
            return 0
        return int(time.time() - self.start_time)

    def export_results(self) -> Dict:
        """Export final results summary"""
        metrics = self.get_metrics()
        crashes = self.get_crashes()
        queue_files = self.get_queue_files()

        results = {
            'metrics': metrics,
            'total_crashes': len(crashes),
            'total_test_cases': len(queue_files),
            'runtime': self.get_runtime(),
            'output_directory': str(self.output_dir)
        }

        # Save to JSON
        results_file = self.output_dir / "results_summary.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"[AFL] Results exported to {results_file}")
        return results
