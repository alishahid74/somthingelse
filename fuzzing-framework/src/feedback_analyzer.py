"""
Feedback Analyzer
Analyzes AFL++ feedback and converts it to PPO state/rewards
"""

from typing import Dict, Tuple


class FeedbackAnalyzer:
    """Analyzes fuzzing feedback for PPO training"""

    def __init__(self):
        self.previous_metrics = None

    def analyze(self, current_metrics: Dict) -> Tuple[Dict, float, bool]:
        """
        Analyze current fuzzing state

        Args:
            current_metrics: Current AFL++ metrics

        Returns:
            Tuple of (state, reward, done)
        """
        # Initialize on first call
        if self.previous_metrics is None:
            self.previous_metrics = current_metrics
            return current_metrics, 0.0, False

        # Calculate reward based on progress
        reward = self._calculate_reward(self.previous_metrics, current_metrics)

        # Check if experiment should terminate
        done = self._check_termination(current_metrics)

        # Update previous metrics
        self.previous_metrics = current_metrics.copy()

        return current_metrics, reward, done

    def _calculate_reward(self, prev: Dict, curr: Dict) -> float:
        """
        Calculate reward signal for PPO

        Reward components:
        - Coverage increase: +1.0 per percentage point
        - New crash: +10.0 per crash
        - Execution speed: +0.1 per 100 exec/sec
        - Path diversity: +0.5 per 100 new paths
        """
        reward = 0.0

        # Coverage reward
        coverage_delta = curr['coverage_rate'] - prev['coverage_rate']
        reward += coverage_delta * 1.0

        # Crash discovery reward
        crash_delta = curr['crash_count'] - prev['crash_count']
        reward += crash_delta * 10.0

        # Execution speed reward (encourages efficiency)
        speed_reward = (curr['exec_speed'] / 100.0) * 0.1
        reward += speed_reward

        # Path diversity reward
        path_delta = curr['unique_paths'] - prev['unique_paths']
        reward += (path_delta / 100.0) * 0.5

        # Penalty for stagnation
        if coverage_delta == 0 and path_delta == 0:
            reward -= 0.1

        return reward

    def _check_termination(self, metrics: Dict) -> bool:
        """
        Check if fuzzing should terminate

        Termination conditions:
        - Coverage plateau (no improvement for extended period)
        - Timeout reached
        """
        # This would be configured based on experiment duration
        # For now, return False to continue indefinitely
        return False

    def get_state_features(self, metrics: Dict) -> Dict:
        """
        Extract relevant features for PPO state

        Features:
        - coverage_rate: Percentage of code covered
        - crash_count: Number of unique crashes
        - exec_speed: Executions per second
        - queue_size: Number of test cases in queue
        - unique_paths: Number of unique paths discovered
        """
        return {
            'coverage_rate': metrics['coverage_rate'],
            'crash_count': metrics['crash_count'],
            'exec_speed': metrics['exec_speed'],
            'queue_size': metrics['queue_size'],
            'unique_paths': metrics['unique_paths']
        }

    def detect_interesting_input(self, metrics: Dict) -> bool:
        """
        Detect if current input is interesting

        An input is interesting if it:
        - Increases coverage
        - Causes a crash
        - Explores new paths
        """
        if self.previous_metrics is None:
            return False

        coverage_increased = metrics['coverage_rate'] > self.previous_metrics['coverage_rate']
        new_crash = metrics['crash_count'] > self.previous_metrics['crash_count']
        new_paths = metrics['unique_paths'] > self.previous_metrics['unique_paths']

        return coverage_increased or new_crash or new_paths

    def reset(self):
        """Reset analyzer state"""
        self.previous_metrics = None
