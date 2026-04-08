# dqn_agent.py
import torch # type: ignore
import torch.nn as nn # type: ignore
import torch.optim as optim # type: ignore
import numpy as np # type: ignore
import random
from collections import deque
import os

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models_store", "dqn.pth")


# ---------------------------------------
# NETWORK
# ---------------------------------------
class DQNNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        # ✅ FIXED: LayerNorm instead of BatchNorm1d — works with batch_size=1
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.net(x)


# ---------------------------------------
# AGENT
# ---------------------------------------
class DQNAgent:

    def __init__(self, state_dim, action_dim):
        self.state_dim    = state_dim
        self.action_dim   = action_dim

        # Hyperparameters
        self.gamma         = 0.95
        self.epsilon       = 1.0
        self.epsilon_min   = 0.01
        self.epsilon_decay = 0.995
        self.batch_size    = 32
        self.lr            = 0.001

        # Experience replay buffer
        self.memory = deque(maxlen=2000)

        # Online + target networks
        self.model        = DQNNetwork(state_dim, action_dim)
        self.target_model = DQNNetwork(state_dim, action_dim)
        self.update_target()

        self.target_update_freq = 10
        self.train_step         = 0

        self.optimizer = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-5)
        self.criterion = nn.MSELoss()

        self.model.eval()
        self.target_model.eval()

    # ---------------------------------------
    # UPDATE TARGET NETWORK
    # ---------------------------------------
    def update_target(self):
        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()

    # ---------------------------------------
    # ACT — epsilon-greedy
    # ---------------------------------------
    def act(self, state: np.ndarray) -> int:
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        self.model.eval()
        with torch.no_grad():
            q = self.model(torch.FloatTensor(state).unsqueeze(0))
        return int(torch.argmax(q).item())

    # ---------------------------------------
    # REMEMBER — store in replay buffer
    # ---------------------------------------
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((
            np.array(state,      dtype=np.float32),
            int(action),
            float(reward),
            np.array(next_state, dtype=np.float32),
            bool(done)
        ))

    # ---------------------------------------
    # REPLAY — sample and train
    # ---------------------------------------
    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        batch       = random.sample(self.memory, self.batch_size)
        states      = torch.FloatTensor(np.array([e[0] for e in batch]))
        actions     = torch.LongTensor( np.array([e[1] for e in batch]))
        rewards     = torch.FloatTensor(np.array([e[2] for e in batch]))
        next_states = torch.FloatTensor(np.array([e[3] for e in batch]))
        dones       = torch.FloatTensor(np.array([e[4] for e in batch], dtype=np.float32))

        self.model.train()

        current_q = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q   = self.target_model(next_states).max(1)[0]
            target_q = rewards + self.gamma * next_q * (1 - dones)

        if not torch.isfinite(target_q).all():
            self.model.eval()
            return

        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        self.model.eval()

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Sync target network
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.update_target()

    # ---------------------------------------
    # SAVE
    # ---------------------------------------
    def save(self):
        try:
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            torch.save({
                'model_state':        self.model.state_dict(),
                'target_model_state': self.target_model.state_dict(),
                'epsilon':            self.epsilon,
                'train_step':         self.train_step,
            }, MODEL_PATH)
            print("DQN model saved")
        except Exception as e:
            print(f"DQN save error: {e}")

    # ---------------------------------------
    # LOAD
    # ---------------------------------------
    def load(self):
        try:
            if not os.path.exists(MODEL_PATH):
                print("No saved DQN — will train fresh")
                return False

            ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)

            if isinstance(ckpt, dict) and 'model_state' in ckpt:
                self.model.load_state_dict(ckpt['model_state'])
                self.target_model.load_state_dict(ckpt['target_model_state'])
                self.epsilon    = ckpt.get('epsilon', self.epsilon_min)
                self.train_step = ckpt.get('train_step', 0)
            else:
                self.model.load_state_dict(ckpt)
                self.update_target()

            self.model.eval()
            self.target_model.eval()
            print(f"DQN loaded (epsilon={self.epsilon:.4f}, steps={self.train_step})")
            return True

        except Exception as e:
            print(f"DQN load error: {e}")
            return False

    # ---------------------------------------
    # PREDICT — portfolio weights
    # ---------------------------------------
    def predict(self, state_tensor: torch.Tensor) -> np.ndarray:
        try:
            self.model.eval()
            with torch.no_grad():
                weights = torch.softmax(self.model(state_tensor), dim=-1)
            w = weights.cpu().numpy().flatten()
            if not np.isfinite(w).all():
                return np.ones(self.action_dim) / self.action_dim
            return w
        except Exception as e:
            print(f"DQN predict error: {e}")
            return np.ones(self.action_dim) / self.action_dim