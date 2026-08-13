"""
agent_template.py -- for an agent trained with ppo_pettingzoo_ma_atari.py

Your training pipeline is identical to the tournament pipeline, so the
observation needs no reshaping -- only a dtype conversion.
"""
import os

import numpy as np
import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical

WEIGHTS_FILE = "base_boxing_v2_0.torch"  # your filename
NUM_ACTIONS = 18
SAMPLE_ACTIONS = True     # see the note at the bottom of this file


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class PPOAgent(nn.Module):
    """COPIED VERBATIM from the training script, with two changes:
       - renamed from `Agent` to `PPOAgent` (the template needs the name `Agent`)
       - takes num_actions directly instead of reading envs.single_action_space
    The layer shapes and attribute names are untouched, which is what matters
    for load_state_dict.
    """

    def __init__(self, num_actions):
        super().__init__()
        self.network = nn.Sequential(
            layer_init(nn.Conv2d(6, 32, 8, stride=4)), nn.ReLU(),
            layer_init(nn.Conv2d(32, 64, 4, stride=2)), nn.ReLU(),
            layer_init(nn.Conv2d(64, 64, 3, stride=1)), nn.ReLU(),
            nn.Flatten(),
            layer_init(nn.Linear(64 * 7 * 7, 512)), nn.ReLU(),
        )
        self.actor = layer_init(nn.Linear(512, num_actions), std=0.01)
        self.critic = layer_init(nn.Linear(512, 1), std=1)   # unused at eval,
                                                             # but must exist to load

    def get_action_and_value(self, x, action=None):
        x = x.clone()
        x[:, :, :, [0, 1, 2, 3]] /= 255.0     # ONLY the frame channels
        hidden = self.network(x.permute((0, 3, 1, 2)))
        logits = self.actor(hidden)
        probs = Categorical(logits=logits)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action), probs.entropy(), self.critic(hidden)


class Agent(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # The tournament passes a PettingZoo env, which has action_space(agent)
        # rather than single_action_space. Fall back to the known 18.
        try:
            num_actions = env.action_space("first_0").n
        except Exception:
            num_actions = NUM_ACTIONS

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), WEIGHTS_FILE)
        self.net = PPOAgent(num_actions)
        self.net.load_state_dict(torch.load(path, map_location=self.device))
        self.net.to(self.device).eval()

    def get_action(self, state=None) -> int:
        if state is None:
            return 0                                   # NOOP

        # (84, 84, 6) uint8  ->  (1, 84, 84, 6) float32. No other change needed:
        # the network normalises and permutes internally, and the two indicator
        # channels are already in the format it was trained on.
        obs = torch.as_tensor(
            np.asarray(state, dtype=np.float32), device=self.device).unsqueeze(0)

        with torch.no_grad():
            if SAMPLE_ACTIONS:
                action, _, _, _ = self.net.get_action_and_value(obs)
                return int(action.item())
            # deterministic: take the highest-probability action
            x = obs.clone()
            x[:, :, :, [0, 1, 2, 3]] /= 255.0
            logits = self.net.actor(self.net.network(x.permute((0, 3, 1, 2))))
            return int(logits.argmax(dim=1).item())
