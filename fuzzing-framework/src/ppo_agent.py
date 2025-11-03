"""
PPO Agent for Fuzzing Optimization
Implements Proximal Policy Optimization for mutation strategy selection
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import List, Tuple, Dict


class PolicyNetwork(nn.Module):
    """Actor-Critic network for PPO"""

    def __init__(self, state_dim: int, action_dim: int, hidden_layers: List[int]):
        super(PolicyNetwork, self).__init__()

        # Build actor network
        actor_layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_layers:
            actor_layers.append(nn.Linear(prev_dim, hidden_dim))
            actor_layers.append(nn.ReLU())
            prev_dim = hidden_dim
        actor_layers.append(nn.Linear(prev_dim, action_dim))
        actor_layers.append(nn.Softmax(dim=-1))
        self.actor = nn.Sequential(*actor_layers)

        # Build critic network
        critic_layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_layers:
            critic_layers.append(nn.Linear(prev_dim, hidden_dim))
            critic_layers.append(nn.ReLU())
            prev_dim = hidden_dim
        critic_layers.append(nn.Linear(prev_dim, 1))
        self.critic = nn.Sequential(*critic_layers)

    def forward(self, state):
        action_probs = self.actor(state)
        state_value = self.critic(state)
        return action_probs, state_value


class PPOAgent:
    """PPO Agent for mutation strategy optimization"""

    def __init__(self, config: Dict):
        self.config = config

        # State: [coverage_rate, crash_count, exec_speed, queue_size, unique_paths]
        self.state_dim = 5

        # Actions: Different mutation strategies
        # 0: Bit flips, 1: Byte flips, 2: Arithmetic, 3: Havoc, 4: Splice
        self.action_dim = 5

        # Initialize networks
        self.policy = PolicyNetwork(
            self.state_dim,
            self.action_dim,
            config['hidden_layers']
        )

        self.optimizer = optim.Adam(
            self.policy.parameters(),
            lr=config['learning_rate']
        )

        # PPO parameters
        self.gamma = config['gamma']
        self.epsilon_clip = config['epsilon_clip']
        self.epochs = config['epochs']
        self.entropy_coef = config['entropy_coefficient']

        # Experience buffer
        self.buffer = {
            'states': [],
            'actions': [],
            'rewards': [],
            'log_probs': [],
            'values': [],
            'dones': []
        }

    def get_state_vector(self, metrics: Dict) -> np.ndarray:
        """Convert fuzzing metrics to state vector"""
        state = np.array([
            metrics.get('coverage_rate', 0.0),
            metrics.get('crash_count', 0.0) / 100.0,  # Normalize
            metrics.get('exec_speed', 0.0) / 1000.0,  # Normalize
            metrics.get('queue_size', 0.0) / 1000.0,  # Normalize
            metrics.get('unique_paths', 0.0) / 10000.0  # Normalize
        ], dtype=np.float32)
        return state

    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """Select mutation strategy based on current state"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)

        with torch.no_grad():
            action_probs, state_value = self.policy(state_tensor)

        # Sample action from distribution
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)

        return action.item(), log_prob.item(), state_value.item()

    def compute_reward(self, prev_metrics: Dict, curr_metrics: Dict) -> float:
        """Calculate reward based on fuzzing progress"""
        weights = self.config['reward_weights']

        # Coverage increase reward
        coverage_delta = curr_metrics['coverage_rate'] - prev_metrics.get('coverage_rate', 0)
        coverage_reward = weights['coverage_increase'] * coverage_delta

        # Crash discovery reward
        crash_delta = curr_metrics['crash_count'] - prev_metrics.get('crash_count', 0)
        crash_reward = weights['unique_crash'] * crash_delta

        # Execution speed reward
        speed_reward = weights['execution_speed'] * (curr_metrics['exec_speed'] / 1000.0)

        # Path diversity reward
        path_delta = curr_metrics['unique_paths'] - prev_metrics.get('unique_paths', 0)
        path_reward = weights['path_diversity'] * (path_delta / 100.0)

        total_reward = coverage_reward + crash_reward + speed_reward + path_reward
        return total_reward

    def store_transition(self, state, action, reward, log_prob, value, done):
        """Store experience in buffer"""
        self.buffer['states'].append(state)
        self.buffer['actions'].append(action)
        self.buffer['rewards'].append(reward)
        self.buffer['log_probs'].append(log_prob)
        self.buffer['values'].append(value)
        self.buffer['dones'].append(done)

    def update(self):
        """Update policy using PPO algorithm"""
        if len(self.buffer['states']) < self.config['batch_size']:
            return 0.0

        # Convert buffer to tensors
        states = torch.FloatTensor(np.array(self.buffer['states']))
        actions = torch.LongTensor(self.buffer['actions'])
        old_log_probs = torch.FloatTensor(self.buffer['log_probs'])

        # Compute returns and advantages
        returns = self._compute_returns()
        returns = torch.FloatTensor(returns)
        values = torch.FloatTensor(self.buffer['values'])
        advantages = returns - values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update for multiple epochs
        total_loss = 0.0
        for _ in range(self.epochs):
            # Get current policy predictions
            action_probs, state_values = self.policy(states)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            # Compute ratio and surrogate loss
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon_clip, 1 + self.epsilon_clip) * advantages

            # PPO loss
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(state_values.squeeze(), returns)
            loss = actor_loss + 0.5 * critic_loss - self.entropy_coef * entropy

            # Update
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
            self.optimizer.step()

            total_loss += loss.item()

        # Clear buffer
        self.clear_buffer()

        return total_loss / self.epochs

    def _compute_returns(self) -> List[float]:
        """Compute discounted returns"""
        returns = []
        R = 0
        for reward, done in zip(reversed(self.buffer['rewards']),
                               reversed(self.buffer['dones'])):
            if done:
                R = 0
            R = reward + self.gamma * R
            returns.insert(0, R)
        return returns

    def clear_buffer(self):
        """Clear experience buffer"""
        for key in self.buffer:
            self.buffer[key] = []

    def save_model(self, path: str):
        """Save model checkpoint"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)

    def load_model(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path)
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
