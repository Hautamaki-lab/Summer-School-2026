# Multi-Agent Reinforcement Learning with PettingZoo and MPE2

This tutorial builds a complete multi-agent reinforcement-learning exercise with Simple Spread. You work through four stages:

```text
Simple Spread with random agents
            ↓
   Independent Q-Learning (IQL)
            ↓
   Centralized Q-Learning (CQL)
            ↓
   Evaluation: Random vs IQL vs CQL
```

## Contents

1. [Part 1 — Setup, Simple Spread, and Random Agents](#part-1--setup-simple-spread-and-random-agents)
2. [Part 2 — Independent Q-Learning](#part-2--independent-q-learning)
3. [Part 3 — Centralized Q-Learning](#part-3--centralized-q-learning)
4. [Part 4 — Evaluation: Random vs IQL vs CQL](#part-4--evaluation-random-vs-iql-vs-cql)

## Files created during the tutorial

```text
pettingzoo-marl/
├── spread_random.py
├── dqn.py
├── spread_iql.py
├── spread_cql.py
├── spread_evaluate.py
│
└── checkpoints/
    ├── spread_iql_agent_0.pth
    ├── spread_iql_agent_1.pth
    └── spread_cql.pth
```

Each part builds on the files from the previous part.

---


# Part 1 — Setup, Simple Spread, and Random Agents

### 1.1 Before you begin

From the setup guide you should already have:

- the Conda environment named `pettingzoo`;
- Visual Studio Code configured to use that environment;
- PettingZoo and PyTorch installed.

You do not need a new environment. Activate the existing one:

```console
conda activate pettingzoo
```

The prompt should begin with `(pettingzoo)`.

---

### 1.2 Install MPE2

The setup guide used a PettingZoo Atari environment. This tutorial uses MPE2, which provides multi-agent environments with the PettingZoo API.

1. Install it:

   ```console
   python -m pip install mpe2
   ```

2. Verify it:

   ```console
   python -c "from mpe2 import simple_spread_v3; print('MPE2 loaded successfully')"
   ```

   You should see `MPE2 loaded successfully`.

---

### 1.3 Create the project directory

```console
mkdir -p ~/pettingzoo-marl
cd ~/pettingzoo-marl
code .
```

Open an integrated terminal with **Terminal → New Terminal**, then confirm the interpreter path contains `miniconda3/envs/pettingzoo`:

```console
python -c "import sys; print(sys.executable)"
```

---

### 1.4 Simple Spread

Simple Spread is a cooperative environment with `N` agents and `N` landmarks. The agents must spread out so that every landmark is covered. This tutorial uses `N=2`: two agents (`agent_0`, `agent_1`) and two landmarks.

- **Actions:** each agent has 5 discrete actions — no action, left, right, down, up.
- **Observations:** a numeric vector (own velocity and position, relative landmark positions, relative position of the other agent). Unlike the Atari game, it is not an image.
- **Reward:** a shared team reward based on how close the agents are to the landmarks. `local_ratio=0.0` gives both agents the same global reward. The reward is negative because it is based on distance, so a value closer to zero is better — `-10` is better than `-30`.
- **Episode length:** `max_cycles=25`, so one game lasts at most 25 steps.

---

### 1.5 Create the random-agent program

Create `spread_random.py` and add:

```python
import time

from mpe2 import simple_spread_v3


# Create the environment.
env = simple_spread_v3.parallel_env(
    render_mode="human",
    N=2,
    local_ratio=0.0,
    max_cycles=25,
    continuous_actions=False,
)

# Start a new game.
observations, infos = env.reset(seed=42)

team_reward = 0.0

# Continue while the game has active agents.
while len(env.agents) > 0:

    # Agent 0 selects a random action.
    action_0 = env.action_space("agent_0").sample()

    # Agent 1 selects a random action.
    action_1 = env.action_space("agent_1").sample()

    # Both agents act at the same environment step.
    actions = {
        "agent_0": action_0,
        "agent_1": action_1,
    }

    (
        observations,
        rewards,
        terminations,
        truncations,
        infos,
    ) = env.step(actions)

    # Both agents receive the shared team reward.
    team_reward += rewards["agent_0"]

    # Slow down the game so that it is easy to watch.
    time.sleep(1 / 10)

env.close()

print(f"Team reward: {team_reward:.3f}")
```

Save the file.

---

### 1.6 Run it

```console
python spread_random.py
```

A Simple Spread window opens and the agents move randomly. When the game ends, the terminal prints something like `Team reward: -42.731` (the exact value varies).

The important part is the interaction loop: each agent picks its own action, both actions are sent together in one dictionary, and `env.step(actions)` advances both agents at once. The learned agents in the next parts reuse this same loop.

---


# Part 2 — Independent Q-Learning

### 2.1 Goal

The random agents ignore their observations. Independent Q-Learning (IQL) replaces the random choice with a learned one: each agent gets its own Deep Q-Network that maps its observation to an action.

```text
observation → Q-network → action   (one per agent)
```

Both agents still cooperate, because the environment gives them a shared team reward. You first build the reusable DQN code once, in `dqn.py`.

---

### 2.2 Create `dqn.py`

`dqn.py` contains four pieces:

| Component | Purpose |
| --- | --- |
| `QNetwork` | Predict Q-values and pick the best action |
| `ReplayBuffer` | Store past experiences and sample random batches |
| `train_dqn()` | Run one DQN learning update |
| `update_target()` | Copy the Q-network into the target network |

Create `dqn.py` and add:

```python
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class QNetwork(nn.Module):
    def __init__(self, observation_size, action_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(observation_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_size),
        )

    def forward(self, observation):
        return self.network(observation.float())

    @torch.no_grad()
    def action(self, observation, device):
        observation = torch.as_tensor(
            observation,
            dtype=torch.float32,
            device=device,
        ).unsqueeze(0)

        q_values = self(observation)
        return int(q_values.argmax(dim=1).item())


class ReplayBuffer:
    def __init__(self, size, observation_size, device, seed):
        self.size = size
        self.device = device
        self.rng = np.random.default_rng(seed)

        self.observations = np.empty(
            (size, observation_size), dtype=np.float32
        )
        self.actions = np.empty(size, dtype=np.int64)
        self.rewards = np.empty(size, dtype=np.float32)
        self.next_observations = np.empty(
            (size, observation_size), dtype=np.float32
        )
        self.dones = np.empty(size, dtype=np.float32)

        self.position = 0
        self.length = 0

    def add(self, observation, action, reward, next_observation, done):
        self.observations[self.position] = observation
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_observations[self.position] = next_observation
        self.dones[self.position] = float(done)

        self.position = (self.position + 1) % self.size
        self.length = min(self.length + 1, self.size)

    def sample(self, batch_size):
        indices = self.rng.integers(0, self.length, size=batch_size)

        observations = torch.as_tensor(
            self.observations[indices], device=self.device
        )
        actions = torch.as_tensor(
            self.actions[indices], dtype=torch.long, device=self.device
        )
        rewards = torch.as_tensor(
            self.rewards[indices], device=self.device
        )
        next_observations = torch.as_tensor(
            self.next_observations[indices], device=self.device
        )
        dones = torch.as_tensor(
            self.dones[indices], device=self.device
        )

        return observations, actions, rewards, next_observations, dones

    def __len__(self):
        return self.length


def train_dqn(
    q_network,
    target_network,
    replay_buffer,
    optimizer,
    batch_size,
    gamma,
):
    observations, actions, rewards, next_observations, dones = (
        replay_buffer.sample(batch_size)
    )

    with torch.no_grad():
        next_q_values = target_network(next_observations)
        next_values = next_q_values.max(dim=1).values
        targets = rewards + gamma * next_values * (1.0 - dones)

    q_values = q_network(observations)
    chosen_q_values = q_values.gather(
        1, actions.unsqueeze(1)
    ).squeeze(1)

    loss = F.smooth_l1_loss(chosen_q_values, targets)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()


def update_target(q_network, target_network):
    target_network.load_state_dict(q_network.state_dict())
```

Save the file.

---

### 2.3 Why DQN uses a target network

DQN trains the Q-network by pushing its prediction toward a target:

```text
Q(s, a)  →  reward + gamma × max Q(s', a')
```

Without a target network, the same rapidly changing network would be used to estimate both the current Q-value and the bootstrap target. Every gradient step could therefore change the target at the same time as the prediction being trained.

```text
Problem in basic neural Q-learning
        ↓
target moves too rapidly
        ↓
DQN target network
        ↓
temporarily stable target
```

The fix is a **target network**: a frozen copy of the Q-network used only for the right-hand side. It stays fixed for several hundred steps, so the target holds still while the Q-network learns. Every `TARGET_UPDATE_FREQUENCY` steps the code copies the Q-network into it and repeats. Only the Q-network is trained and saved; the target network is a temporary aid, so one learner still has just one policy.

<details>
<summary><strong>Optional — how <code>dqn.py</code> works</strong></summary>

**QNetwork** — a small MLP: observation → two hidden layers of 64 units → one Q-value per action (5 for Simple Spread). `forward()` returns all five Q-values. `action()` runs the network under `@torch.no_grad()` and returns the `argmax`, i.e. the highest-valued action.

**ReplayBuffer** — DQN does not learn only from the latest step. It stores past transitions `(observation, action, reward, next_observation, done)` in fixed NumPy arrays and later samples random batches. The buffer is circular (`position = (position + 1) % size`), so once full it overwrites the oldest transitions. `sample()` returns a random batch as tensors on the training device.

**train_dqn()** — one gradient update:

1. Sample a batch from the buffer.
2. Under `torch.no_grad()`, compute the target `reward + gamma × max Q_target(next_state)`. When `done` is true, the `(1 - done)` factor drops the future term, so the target is just the reward.
3. Gather the Q-value of the action actually taken.
4. Compare the two with the smooth L1 (Huber) loss.
5. `zero_grad()` → `backward()` → `step()` to update the Q-network.

**update_target()** — copies all parameters from the Q-network into the target network with `load_state_dict`. This full copy is a *hard* target update.

</details>

---

### 2.4 The IQL program

IQL creates one full DQN learner — Q-network, target network, replay buffer, optimizer — for each agent. With two agents there are four network objects but still only two learned policies. Each agent uses its own observation and never reads the other's Q-values; cooperation comes from the shared reward, not from shared networks.

Create `spread_iql.py` and add:

```python
import random
from collections import deque
from pathlib import Path

import numpy as np
import torch
from mpe2 import simple_spread_v3

from dqn import QNetwork, ReplayBuffer, train_dqn, update_target


SEED = 42
TOTAL_TIMESTEPS = 50_000

LEARNING_RATE = 1e-3
GAMMA = 0.95

BUFFER_SIZE = 10_000
BATCH_SIZE = 64
LEARNING_STARTS = 1_000
TARGET_UPDATE_FREQUENCY = 500

START_EPSILON = 1.0
END_EPSILON = 0.05
EPSILON_DECAY_STEPS = 10_000


random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


env = simple_spread_v3.parallel_env(
    N=2,
    local_ratio=0.0,
    max_cycles=25,
    continuous_actions=False,
)

observations, infos = env.reset(seed=SEED)


# Agent 0
observation_size_0 = env.observation_space("agent_0").shape[0]
action_size_0 = env.action_space("agent_0").n

q_network_0 = QNetwork(
    observation_size_0,
    action_size_0,
).to(device)

target_network_0 = QNetwork(
    observation_size_0,
    action_size_0,
).to(device)

update_target(q_network_0, target_network_0)

optimizer_0 = torch.optim.Adam(
    q_network_0.parameters(),
    lr=LEARNING_RATE,
)

replay_buffer_0 = ReplayBuffer(
    BUFFER_SIZE,
    observation_size_0,
    device,
    seed=SEED,
)


# Agent 1
observation_size_1 = env.observation_space("agent_1").shape[0]
action_size_1 = env.action_space("agent_1").n

q_network_1 = QNetwork(
    observation_size_1,
    action_size_1,
).to(device)

target_network_1 = QNetwork(
    observation_size_1,
    action_size_1,
).to(device)

update_target(q_network_1, target_network_1)

optimizer_1 = torch.optim.Adam(
    q_network_1.parameters(),
    lr=LEARNING_RATE,
)

replay_buffer_1 = ReplayBuffer(
    BUFFER_SIZE,
    observation_size_1,
    device,
    seed=SEED + 1,
)


game = 0
game_reward = 0.0
recent_rewards = deque(maxlen=100)


try:
    for timestep in range(TOTAL_TIMESTEPS):

        if not env.agents:
            game += 1
            recent_rewards.append(game_reward)

            if game % 100 == 0:
                print(
                    f"Game {game:4d} | "
                    f"mean reward {np.mean(recent_rewards):7.3f}"
                )

            observations, infos = env.reset(
                seed=SEED + game
            )

            game_reward = 0.0


        epsilon = max(
            END_EPSILON,
            START_EPSILON
            - (START_EPSILON - END_EPSILON)
            * timestep
            / EPSILON_DECAY_STEPS,
        )


        # Agent 0 chooses its own action.
        if random.random() < epsilon:
            action_0 = env.action_space("agent_0").sample()
        else:
            action_0 = q_network_0.action(
                observations["agent_0"],
                device,
            )


        # Agent 1 chooses its own action.
        if random.random() < epsilon:
            action_1 = env.action_space("agent_1").sample()
        else:
            action_1 = q_network_1.action(
                observations["agent_1"],
                device,
            )


        actions = {
            "agent_0": action_0,
            "agent_1": action_1,
        }


        old_observation_0 = observations["agent_0"]
        old_observation_1 = observations["agent_1"]


        (
            observations,
            rewards,
            terminations,
            truncations,
            infos,
        ) = env.step(actions)


        # With local_ratio=0.0, both agents receive the team reward.
        game_reward += rewards["agent_0"]


        done_0 = (
            terminations["agent_0"]
            or truncations["agent_0"]
        )

        done_1 = (
            terminations["agent_1"]
            or truncations["agent_1"]
        )


        if done_0:
            next_observation_0 = np.zeros(
                observation_size_0,
                dtype=np.float32,
            )
        else:
            next_observation_0 = observations["agent_0"]


        if done_1:
            next_observation_1 = np.zeros(
                observation_size_1,
                dtype=np.float32,
            )
        else:
            next_observation_1 = observations["agent_1"]


        replay_buffer_0.add(
            old_observation_0,
            action_0,
            rewards["agent_0"],
            next_observation_0,
            done_0,
        )


        replay_buffer_1.add(
            old_observation_1,
            action_1,
            rewards["agent_1"],
            next_observation_1,
            done_1,
        )


        if (
            timestep >= LEARNING_STARTS
            and len(replay_buffer_0) >= BATCH_SIZE
        ):
            train_dqn(
                q_network_0,
                target_network_0,
                replay_buffer_0,
                optimizer_0,
                BATCH_SIZE,
                GAMMA,
            )

            train_dqn(
                q_network_1,
                target_network_1,
                replay_buffer_1,
                optimizer_1,
                BATCH_SIZE,
                GAMMA,
            )


        if (
            timestep >= LEARNING_STARTS
            and timestep % TARGET_UPDATE_FREQUENCY == 0
        ):
            update_target(
                q_network_0,
                target_network_0,
            )

            update_target(
                q_network_1,
                target_network_1,
            )


finally:
    env.close()


Path("checkpoints").mkdir(exist_ok=True)

torch.save(
    q_network_0.state_dict(),
    "checkpoints/spread_iql_agent_0.pth",
)

torch.save(
    q_network_1.state_dict(),
    "checkpoints/spread_iql_agent_1.pth",
)

print("Training complete.")
```

Save the file. Your directory now has `spread_random.py`, `dqn.py`, and `spread_iql.py`.

---

### 2.5 Train the agents

```console
python spread_iql.py
```

Training runs without a window so it is fast. Every 100 games it prints the mean reward over the last 100 games:

```text
Game  100 | mean reward -41.181
Game  200 | mean reward -33.517
Game  300 | mean reward -28.628
Game  400 | mean reward -26.607
```

The reward should trend toward zero as training improves. RL is noisy, so do not expect every block to improve — watch the overall trend. When training finishes, the program saves the two policies (the online Q-networks only, not the target networks):

```text
checkpoints/spread_iql_agent_0.pth
checkpoints/spread_iql_agent_1.pth
```

<details>
<summary><strong>Optional — how <code>spread_iql.py</code> works</strong></summary>

**Hyperparameters** — `TOTAL_TIMESTEPS = 50_000` steps (about 2,000 games of 25 steps). `GAMMA = 0.95` weights future reward. `BUFFER_SIZE = 10_000`, `BATCH_SIZE = 64`. `LEARNING_STARTS = 1_000` fills the buffers before training begins. `TARGET_UPDATE_FREQUENCY = 500` steps. Epsilon decays from `1.0` to `0.05` over the first 10,000 steps.

**Two learners** — Agent 0 and Agent 1 each build a Q-network, a target network (synced immediately with `update_target`), an Adam optimizer, and a replay buffer. Nothing is shared between them.

**The loop** — at each step:

- Compute `epsilon`. For each agent, with probability `epsilon` take a random action (explore); otherwise take the network's best action (exploit).
- Send both actions to `env.step()`.
- Track the team reward via `rewards["agent_0"]` — both agents receive the same value.
- Store each agent's transition in its own buffer. If the episode ended, store a zero next-observation; `done` then stops the target from bootstrapping past the end.
- Once past `LEARNING_STARTS`, call `train_dqn` once per agent. Every 500 steps, refresh each target network.

Because each agent has its own buffer, network, and optimizer, the two updates never share parameters — this is what makes the method *independent*.

**Saving the policies** — a PyTorch model's learned weights live in its *state dict*, a dictionary that maps each layer to its tensors. After the loop, `Path("checkpoints").mkdir(exist_ok=True)` creates the output folder if it does not exist, and `torch.save(q_network_0.state_dict(), "checkpoints/spread_iql_agent_0.pth")` writes Agent 0's weights to a `.pth` file (the same is done for Agent 1). Only the online Q-networks are saved; the target networks were just training aids.

</details>

---


# Part 3 — Centralized Q-Learning

### 3.1 Goal

Centralized Q-Learning (CQL here means *Centralized*, not Conservative) replaces the two independent learners with a single network that sees both agents and chooses their actions together:

```text
observation 0 ─┐
               ├→ one Q-network → joint action → (action 0, action 1)
observation 1 ─┘
```

There is now one Q-network, one target network, one replay buffer, and one optimizer.

**Joint observation** — the two observations are concatenated into one input vector.

**Joint action** — each agent has 5 actions, so there are `5 × 5 = 25` action pairs, and the network has 25 outputs. A pair is encoded as one index and decoded back:

```python
joint_action = action_0 * action_size_1 + action_1   # encode
action_0 = joint_action // action_size_1              # decode
action_1 = joint_action %  action_size_1
```

Create `spread_cql.py` and add:

```python
import random
from collections import deque
from pathlib import Path

import numpy as np
import torch
from mpe2 import simple_spread_v3

from dqn import QNetwork, ReplayBuffer, train_dqn, update_target


# Training settings
SEED = 42
TOTAL_TIMESTEPS = 50_000

LEARNING_RATE = 1e-3
GAMMA = 0.95

BUFFER_SIZE = 10_000
BATCH_SIZE = 64
LEARNING_STARTS = 1_000
TARGET_UPDATE_FREQUENCY = 500

START_EPSILON = 1.0
END_EPSILON = 0.05
EPSILON_DECAY_STEPS = 10_000


random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# Two agents and two landmarks.
# local_ratio=0.0 means both agents use the global team reward.
env = simple_spread_v3.parallel_env(
    N=2,
    local_ratio=0.0,
    max_cycles=25,
    continuous_actions=False,
)

observations, infos = env.reset(seed=SEED)


# ------------------------------------------------------------
# Centralized Q-Learning
#
# Instead of one Q-network per agent, there is one Q-network.
#
# Input:
#   observation of agent_0 + observation of agent_1
#
# Output:
#   Q-value for every joint action
#
# Each agent has 5 actions, so there are:
#   5 x 5 = 25 joint actions
# ------------------------------------------------------------

observation_size_0 = env.observation_space("agent_0").shape[0]
observation_size_1 = env.observation_space("agent_1").shape[0]

action_size_0 = env.action_space("agent_0").n
action_size_1 = env.action_space("agent_1").n

joint_observation_size = (
    observation_size_0 + observation_size_1
)

joint_action_size = action_size_0 * action_size_1


q_network = QNetwork(
    joint_observation_size,
    joint_action_size,
).to(device)

target_network = QNetwork(
    joint_observation_size,
    joint_action_size,
).to(device)

update_target(q_network, target_network)

optimizer = torch.optim.Adam(
    q_network.parameters(),
    lr=LEARNING_RATE,
)

replay_buffer = ReplayBuffer(
    BUFFER_SIZE,
    joint_observation_size,
    device,
    seed=SEED,
)


game = 0
game_reward = 0.0
recent_rewards = deque(maxlen=100)


try:
    for timestep in range(TOTAL_TIMESTEPS):

        # Start a new game after the previous one ends.
        if not env.agents:
            game += 1
            recent_rewards.append(game_reward)

            if game % 100 == 0:
                print(
                    f"Game {game:4d} | "
                    f"mean reward {np.mean(recent_rewards):7.3f}"
                )

            observations, infos = env.reset(
                seed=SEED + game
            )

            game_reward = 0.0


        # Epsilon decreases from 1.0 to 0.05.
        epsilon = max(
            END_EPSILON,
            START_EPSILON
            - (START_EPSILON - END_EPSILON)
            * timestep
            / EPSILON_DECAY_STEPS,
        )


        # Combine both agents' observations into one joint state.
        joint_observation = np.concatenate(
            [
                observations["agent_0"],
                observations["agent_1"],
            ]
        )


        # Choose one joint action.
        if random.random() < epsilon:
            action_0 = env.action_space("agent_0").sample()
            action_1 = env.action_space("agent_1").sample()

            joint_action = (
                action_0 * action_size_1
                + action_1
            )

        else:
            joint_action = q_network.action(
                joint_observation,
                device,
            )

            # Convert the joint action back into the two
            # individual agent actions.
            action_0 = joint_action // action_size_1
            action_1 = joint_action % action_size_1


        actions = {
            "agent_0": action_0,
            "agent_1": action_1,
        }


        (
            observations,
            rewards,
            terminations,
            truncations,
            infos,
        ) = env.step(actions)


        # Both agents receive the same team reward.
        reward = rewards["agent_0"]
        game_reward += reward


        done = (
            terminations["agent_0"]
            or truncations["agent_0"]
        )


        if done:
            next_joint_observation = np.zeros(
                joint_observation_size,
                dtype=np.float32,
            )
        else:
            next_joint_observation = np.concatenate(
                [
                    observations["agent_0"],
                    observations["agent_1"],
                ]
            )


        # Store one centralized transition.
        replay_buffer.add(
            joint_observation,
            joint_action,
            reward,
            next_joint_observation,
            done,
        )


        # Train the centralized Q-network.
        if (
            timestep >= LEARNING_STARTS
            and len(replay_buffer) >= BATCH_SIZE
        ):
            train_dqn(
                q_network,
                target_network,
                replay_buffer,
                optimizer,
                BATCH_SIZE,
                GAMMA,
            )


        # Periodically copy the Q-network to the target network.
        if (
            timestep >= LEARNING_STARTS
            and timestep % TARGET_UPDATE_FREQUENCY == 0
        ):
            update_target(
                q_network,
                target_network,
            )


finally:
    env.close()


# Save the centralized Q-network.
Path("checkpoints").mkdir(exist_ok=True)

torch.save(
    q_network.state_dict(),
    "checkpoints/spread_cql.pth",
)

print("Training complete.")
```

Save the file. The training settings match IQL on purpose, so the only real difference is the centralized structure.

---

### 3.2 Train the centralized learner

```console
python spread_cql.py
```

As before, the terminal prints the mean team reward (higher is better). When training finishes it saves one model:

```text
checkpoints/spread_cql.pth
```

Only one model is saved, because CQL learns a single centralized Q-function. You now have all three policies — Random, IQL, and CQL — ready to compare.

<details>
<summary><strong>Optional — how <code>spread_cql.py</code> works</strong></summary>

The structure mirrors one IQL learner, with three differences:

- **Input size** is `observation_size_0 + observation_size_1` (the joint observation).
- **Output size** is `action_size_0 × action_size_1 = 25` (one Q-value per action pair).
- **One transition per step** — each step stores a single centralized transition `(joint_observation, joint_action, team_reward, next_joint_observation, done)` in one buffer, and calls `train_dqn` once.

During exploration the code samples two random actions and encodes them into a joint index. During exploitation the network picks a joint index, which is decoded back into the two environment actions before `env.step()`. The environment still receives the usual `{"agent_0": ..., "agent_1": ...}` dictionary.

</details>

---


# Part 4 — Evaluation: Random vs IQL vs CQL

### 4.1 Goal

You now have three ways to control Simple Spread. The evaluation program compares them fairly in two ways:

- **Numerically** — it plays 100 unseen games per method and reports the mean reward and standard deviation. All three methods use the same seeds, so they face identical starting positions.
- **Visually** — it then shows Random, IQL, and CQL side by side in one window, again from the same starting states.

---

### 4.2 Before you run

Your directory should contain the four programs plus the three checkpoints:

```text
checkpoints/
├── spread_iql_agent_0.pth
├── spread_iql_agent_1.pth
└── spread_cql.pth
```

If a checkpoint is missing, rerun `python spread_iql.py` or `python spread_cql.py`. The evaluation program only loads and tests the saved models — it does not train.

Create `spread_evaluate.py` and add:

```python
import time

import numpy as np
import pygame
import torch
from mpe2 import simple_spread_v3

from dqn import QNetwork


EVALUATION_GAMES = 100
WATCH_GAMES = 5
SEED = 10_000
FPS = 10


device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def make_env(render_mode=None):
    return simple_spread_v3.parallel_env(
        render_mode=render_mode,
        N=2,
        local_ratio=0.0,
        max_cycles=25,
        continuous_actions=False,
    )


# ------------------------------------------------------------
# Load IQL and CQL networks.
# ------------------------------------------------------------

env = make_env()

observation_size_0 = env.observation_space("agent_0").shape[0]
observation_size_1 = env.observation_space("agent_1").shape[0]

action_size_0 = env.action_space("agent_0").n
action_size_1 = env.action_space("agent_1").n


# IQL: one Q-network per agent.
iql_network_0 = QNetwork(
    observation_size_0,
    action_size_0,
).to(device)

iql_network_1 = QNetwork(
    observation_size_1,
    action_size_1,
).to(device)

iql_network_0.load_state_dict(
    torch.load(
        "checkpoints/spread_iql_agent_0.pth",
        map_location=device,
        weights_only=True,
    )
)

iql_network_1.load_state_dict(
    torch.load(
        "checkpoints/spread_iql_agent_1.pth",
        map_location=device,
        weights_only=True,
    )
)

iql_network_0.eval()
iql_network_1.eval()


# CQL: one centralized Q-network.
joint_observation_size = (
    observation_size_0 + observation_size_1
)

joint_action_size = action_size_0 * action_size_1

cql_network = QNetwork(
    joint_observation_size,
    joint_action_size,
).to(device)

cql_network.load_state_dict(
    torch.load(
        "checkpoints/spread_cql.pth",
        map_location=device,
        weights_only=True,
    )
)

cql_network.eval()

env.close()


# ------------------------------------------------------------
# Policy helpers.
# ------------------------------------------------------------

def random_actions(env):
    return {
        "agent_0": env.action_space("agent_0").sample(),
        "agent_1": env.action_space("agent_1").sample(),
    }


def iql_actions(observations):
    action_0 = iql_network_0.action(
        observations["agent_0"],
        device,
    )

    action_1 = iql_network_1.action(
        observations["agent_1"],
        device,
    )

    return {
        "agent_0": action_0,
        "agent_1": action_1,
    }


def cql_actions(observations):
    joint_observation = np.concatenate(
        [
            observations["agent_0"],
            observations["agent_1"],
        ]
    )

    joint_action = cql_network.action(
        joint_observation,
        device,
    )

    action_0 = joint_action // action_size_1
    action_1 = joint_action % action_size_1

    return {
        "agent_0": action_0,
        "agent_1": action_1,
    }


# ------------------------------------------------------------
# Play one complete game without rendering.
# ------------------------------------------------------------

def play_random_game(env, seed):
    observations, infos = env.reset(seed=seed)

    env.action_space("agent_0").seed(seed)
    env.action_space("agent_1").seed(seed + 1)

    total_reward = 0.0

    while env.agents:
        actions = random_actions(env)

        (
            observations,
            rewards,
            terminations,
            truncations,
            infos,
        ) = env.step(actions)

        total_reward += rewards["agent_0"]

    return total_reward


def play_iql_game(env, seed):
    observations, infos = env.reset(seed=seed)

    total_reward = 0.0

    while env.agents:
        actions = iql_actions(observations)

        (
            observations,
            rewards,
            terminations,
            truncations,
            infos,
        ) = env.step(actions)

        total_reward += rewards["agent_0"]

    return total_reward


def play_cql_game(env, seed):
    observations, infos = env.reset(seed=seed)

    total_reward = 0.0

    while env.agents:
        actions = cql_actions(observations)

        (
            observations,
            rewards,
            terminations,
            truncations,
            infos,
        ) = env.step(actions)

        total_reward += rewards["agent_0"]

    return total_reward


# ============================================================
# 1. NUMERICAL COMPARISON
# ============================================================

env = make_env()

random_rewards = []
iql_rewards = []
cql_rewards = []

try:
    for game in range(EVALUATION_GAMES):
        seed = SEED + game

        random_rewards.append(
            play_random_game(env, seed)
        )

        iql_rewards.append(
            play_iql_game(env, seed)
        )

        cql_rewards.append(
            play_cql_game(env, seed)
        )

finally:
    env.close()


random_mean = np.mean(random_rewards)
random_std = np.std(random_rewards)

iql_mean = np.mean(iql_rewards)
iql_std = np.std(iql_rewards)

cql_mean = np.mean(cql_rewards)
cql_std = np.std(cql_rewards)


print(
    f"Evaluation over {EVALUATION_GAMES} unseen games"
)
print()

print(
    f"Random: {random_mean:7.3f} "
    f"+/- {random_std:.3f}"
)

print(
    f"IQL:    {iql_mean:7.3f} "
    f"+/- {iql_std:.3f}"
)

print(
    f"CQL:    {cql_mean:7.3f} "
    f"+/- {cql_std:.3f}"
)

print()

print(
    f"IQL improvement over random: "
    f"{iql_mean - random_mean:.3f}"
)

print(
    f"CQL improvement over random: "
    f"{cql_mean - random_mean:.3f}"
)

print(
    f"CQL difference from IQL:      "
    f"{cql_mean - iql_mean:.3f}"
)


# ============================================================
# 2. SIDE-BY-SIDE VISUAL COMPARISON
# ============================================================

print()
print("Showing Random, IQL, and CQL side by side...")


random_env = make_env(render_mode="rgb_array")
iql_env = make_env(render_mode="rgb_array")
cql_env = make_env(render_mode="rgb_array")


pygame.init()
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

window = None
running = True


try:
    for game in range(WATCH_GAMES):
        if not running:
            break

        seed = SEED + EVALUATION_GAMES + game

        random_observations, _ = random_env.reset(seed=seed)
        iql_observations, _ = iql_env.reset(seed=seed)
        cql_observations, _ = cql_env.reset(seed=seed)

        random_env.action_space("agent_0").seed(seed)
        random_env.action_space("agent_1").seed(seed + 1)

        random_reward = 0.0
        iql_reward = 0.0
        cql_reward = 0.0


        while (
            random_env.agents
            and iql_env.agents
            and cql_env.agents
            and running
        ):

            # Random policy.
            random_action = random_actions(random_env)

            (
                random_observations,
                random_rewards_step,
                _,
                _,
                _,
            ) = random_env.step(random_action)

            random_reward += random_rewards_step["agent_0"]


            # IQL policy.
            iql_action = iql_actions(iql_observations)

            (
                iql_observations,
                iql_rewards_step,
                _,
                _,
                _,
            ) = iql_env.step(iql_action)

            iql_reward += iql_rewards_step["agent_0"]


            # CQL policy.
            cql_action = cql_actions(cql_observations)

            (
                cql_observations,
                cql_rewards_step,
                _,
                _,
                _,
            ) = cql_env.step(cql_action)

            cql_reward += cql_rewards_step["agent_0"]


            # Render all three environments.
            random_frame = random_env.render()
            iql_frame = iql_env.render()
            cql_frame = cql_env.render()


            # All three environments have the same frame size.
            height, width, _ = random_frame.shape
            label_height = 80

            if window is None:
                window = pygame.display.set_mode(
                    (
                        width * 3,
                        height + label_height,
                    )
                )

                pygame.display.set_caption(
                    "Simple Spread: Random vs IQL vs CQL"
                )


            # Convert NumPy RGB arrays to Pygame surfaces.
            random_surface = pygame.surfarray.make_surface(
                np.transpose(random_frame, (1, 0, 2))
            )

            iql_surface = pygame.surfarray.make_surface(
                np.transpose(iql_frame, (1, 0, 2))
            )

            cql_surface = pygame.surfarray.make_surface(
                np.transpose(cql_frame, (1, 0, 2))
            )


            window.fill((255, 255, 255))

            window.blit(
                random_surface,
                (0, label_height),
            )

            window.blit(
                iql_surface,
                (width, label_height),
            )

            window.blit(
                cql_surface,
                (width * 2, label_height),
            )


            # Game counter, centered across the whole window.
            game_text = font.render(
                f"Game {game + 1} / {WATCH_GAMES}",
                True,
                (0, 0, 0),
            )

            window.blit(
                game_text,
                (
                    (width * 3) // 2
                    - game_text.get_width() // 2,
                    10,
                ),
            )

            # Method labels, one above each environment.
            random_text = font.render(
                "RANDOM",
                True,
                (0, 0, 0),
            )

            iql_text = font.render(
                "IQL",
                True,
                (0, 0, 0),
            )

            cql_text = font.render(
                "CQL",
                True,
                (0, 0, 0),
            )

            window.blit(
                random_text,
                (
                    width // 2
                    - random_text.get_width() // 2,
                    45,
                ),
            )

            window.blit(
                iql_text,
                (
                    width
                    + width // 2
                    - iql_text.get_width() // 2,
                    45,
                ),
            )

            window.blit(
                cql_text,
                (
                    width * 2
                    + width // 2
                    - cql_text.get_width() // 2,
                    45,
                ),
            )


            pygame.display.flip()


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


            clock.tick(FPS)


        print(
            f"Game {game + 1} | "
            f"Random {random_reward:7.3f} | "
            f"IQL {iql_reward:7.3f} | "
            f"CQL {cql_reward:7.3f}"
        )


finally:
    random_env.close()
    iql_env.close()
    cql_env.close()
    pygame.quit()
```

Save the file.

---

### 4.3 Run the evaluation

```console
python spread_evaluate.py
```

First the numerical comparison prints, for example:

```text
Evaluation over 100 unseen games

Random: -40.361 +/- 12.750
IQL:    -18.683 +/- 6.904
CQL:    -17.460 +/- 8.028

IQL improvement over random: 21.678
CQL improvement over random: 22.901
CQL difference from IQL:      1.223
```

Then a Pygame window opens showing `RANDOM | IQL | CQL` side by side, and per-game rewards print to the terminal. Your exact numbers will differ.

<details>
<summary><strong>Optional — how <code>spread_evaluate.py</code> works</strong></summary>

**Setup** — `make_env()` builds the same environment used in training, as a helper so every copy matches.

**Loading the models** — a saved `.pth` file holds only the weights (the state dict), not the network code, so the program first recreates each `QNetwork` with the same shape used in training and then fills it with the saved values. `torch.load(path, map_location=device, weights_only=True)` reads the state dict — `map_location` puts the tensors on the current CPU or GPU, and `weights_only=True` loads only the tensors, which is the safe default — and `load_state_dict(...)` copies them into the network. IQL reloads two networks, CQL one. `.eval()` then switches each network to evaluation mode; this small network has no dropout or batch-norm, so it does not change the output here, but it is good practice.

**Three policies** — `random_actions`, `iql_actions`, and `cql_actions` each return an action dictionary. There is no epsilon-greedy exploration during evaluation; the trained networks always take their best action. `cql_actions` concatenates the observations, picks a joint index, and decodes it into the two actions.

**Numerical comparison** — for each of 100 games, all three methods are played from the *same* seed, so the comparison is not confounded by different starting states. Each game's total team reward is stored, then reduced to a mean and standard deviation. The mean is the average performance (higher is better); the standard deviation measures how much games vary.

**Visual comparison** — three environments run with `render_mode="rgb_array"` so their frames can be captured as NumPy arrays, transposed to Pygame's axis order, and drawn into one wide window. A `Game X / N` counter at the top shows which game is playing, with `RANDOM`, `IQL`, and `CQL` labels above their columns. The same seed is used across the three so their layouts match, and `clock.tick(FPS)` limits playback speed.

</details>

---

### 4.4 What to take away

| Method | Learned Q-functions | Action selection |
| --- | ---: | --- |
| Random | 0 | Two random actions |
| IQL | 2 | Each agent picks its own action |
| CQL | 1 | One network picks the action pair |

At evaluation time, the three methods mainly differ in how they choose their actions. Their training structures are different: IQL learns two independent Q-functions, while CQL learns one centralized Q-function over joint actions. In the example run, both learned methods beat random by a wide margin, while IQL and CQL were close:

```text
Random  <<  IQL  ≈  CQL
```

Do not conclude from this small exercise that CQL is always better than IQL. The reliable takeaway is that both learning approaches clearly improve on the random baseline: the numerical results show whether the policies improve the team reward, and the side-by-side viewer shows what they are doing.
