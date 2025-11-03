"""
AFL++ + PPO Fuzzing Framework

A comprehensive framework for comparing AFL++ fuzzing with and without
Proximal Policy Optimization (PPO) reinforcement learning enhancement.
"""

__version__ = "1.0.0"
__author__ = "Research Team"

from .afl_wrapper import AFLWrapper
from .ppo_agent import PPOAgent
from .feedback_analyzer import FeedbackAnalyzer
from .metrics_collector import MetricsCollector
from .experiment_runner import ExperimentRunner

__all__ = [
    'AFLWrapper',
    'PPOAgent',
    'FeedbackAnalyzer',
    'MetricsCollector',
    'ExperimentRunner'
]
