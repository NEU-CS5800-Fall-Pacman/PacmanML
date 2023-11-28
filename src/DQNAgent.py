import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import namedtuple, deque
from Agent import *
from MazeObject import *

batch_size = 128
target_update = 1000

# Q-learning agent class
class DQNAgent(Agent):
    def __init__(self, color, is_hostile, position, state_size, action_size, n_actions):
        super().__init__(color, is_hostile, position)
        self.state_size = state_size
        self.action_size = action_size
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        self.gamma = 0.99
        self.learning_rate = 0.1
        self.valid_actions = None
        self.n_actions = n_actions
        self.update_counter = 0

        # Q-network
        self.q_network = nn.Sequential(
            nn.Linear(state_size, 256),
            nn.ReLU(),
            nn.Linear(256, action_size)
        )
        self.q_network[-1].apply(lambda x: nn.init.zeros_(x.weight))

        self.target_network = nn.Sequential(
            nn.Linear(state_size, 256),
            nn.ReLU(),
            nn.Linear(256, action_size)
        )
        self.target_network[-1].apply(lambda x: nn.init.zeros_(x.weight))

        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)

        # Experience replay buffer
        self.replay_buffer = ReplayBuffer()

    # def init_weights(self, model):
    #     for m in model.modules():
    #         if isinstance(m, nn.Linear):
    #             nn.init.constant_(m.weight, 0)
    #             nn.init.constant_(m.bias, 0)

    def set_valid_actions(self, valid_actions):
        self.valid_actions = valid_actions

    def choose_action(self, state):
        if np.random.rand() <= self.epsilon:
            return self.valid_actions[np.random.choice(len(self.valid_actions))]
        q_values = self.q_network(torch.tensor(state, dtype=torch.float32))
        return self.n_actions[torch.argmax(q_values).item()]

    def update_q_network(self):
        if len(self.replay_buffer.buffer) < batch_size:
            return

        batch = self.replay_buffer.sample_batch(batch_size)
        states, actions, next_states, rewards, dones = batch

        q_values = self.q_network(states).gather(1, actions.unsqueeze(1))

        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        loss = nn.functional.mse_loss(q_values, target_q_values.unsqueeze(1))
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update the target network every target_update steps
        if self.update_counter % target_update == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # Decay exploration rate
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

        # Increment the update counter
        self.update_counter += 1

# Replay buffer class
class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.seen_states_actions = set()

    def add_experience(self, experience):
        state, action, _, _, _ = experience
        state_action_hash = hash((tuple(state.flatten()), action))

        if state_action_hash not in self.seen_states_actions:
            self.buffer.append(experience)
            self.seen_states_actions.add(state_action_hash)

        if len(self.buffer) == self.capacity:
            # If capacity is reached, remove the oldest experience
            removed_experience = self.buffer.popleft()
            removed_state, removed_action, _, _, _ = removed_experience
            removed_state_action_hash = hash((tuple(removed_state.flatten()), removed_action))
            self.seen_states_actions.remove(removed_state_action_hash)

    def sample_batch(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, next_states, rewards, dones = zip(*batch)
        states = np.array(states)
        next_states = np.array([np.array(next_state) for next_state in next_states])

        # Convert Enum actions to their integer values
        actions = np.array([action.value for action in actions])
        return (
            torch.tensor(states, dtype=torch.float32),
            torch.tensor(actions, dtype=torch.int64),
            torch.tensor(next_states, dtype=torch.float32),
            torch.tensor(rewards, dtype=torch.float32),
            torch.tensor(dones, dtype=torch.float32)
        )