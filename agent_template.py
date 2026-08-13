"""
agent_template.py -- fill this in and submit it alongside your weights file.

The tournament will do exactly this:

    agent = Agent(env)              # you load your weights here
    action = agent.get_action(obs)  # obs is (84, 84, 6) uint8, channel-last

Nothing else is called. No training functions are needed.
"""
import os

import numpy as np
import torch
import torch.nn as nn

# ---------------------------------------------------------------------------
# CHANGE THESE to match how you trained.
# ---------------------------------------------------------------------------
IN_CHANNELS = 5          # 4 stacked frames + however many side-indicator planes
NUM_ACTIONS = 18
WEIGHTS_FILE = "policy_ep500.pt"


class QNetwork(nn.Module):
    """COPY THIS VERBATIM from your training script.

    Weights only load into an architecture with exactly the same layer
    shapes, in the same order, with the same attribute names. Retyping it
    from memory is the most common way to break a submission.
    """

    def __init__(self, in_channels, num_actions, img_size=84):
        super().__init__()
        self.img_size = img_size
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4), nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2), nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1), nn.ReLU(inplace=True),
        )
        with torch.no_grad():
            n = self.conv(torch.zeros(1, in_channels, img_size, img_size)).numel()
        self.fc = nn.Sequential(
            nn.Linear(n, 512), nn.ReLU(inplace=True), nn.Linear(512, num_actions))

    def forward(self, x):
        # (batch, H, W, C) uint8  ->  (batch, C, H, W) float in [0, 1]
        x = x.permute(0, 3, 1, 2).float() / 255.0
        return self.fc(self.conv(x).reshape(x.size(0), -1))


def infer_img_size(state_dict, in_channels, num_actions):
    """Work out what frame size the checkpoint was trained at.

    Saves you from decoding a 'size mismatch for fc.0.weight' traceback:
    the first Linear layer's input size is a fingerprint of the frame size.
    """
    want = state_dict["fc.0.weight"].shape[1]
    for size in (84, 64, 48, 42, 32):
        try:
            if QNetwork(in_channels, num_actions, size).fc[0].in_features == want:
                return size
        except Exception:
            continue
    raise ValueError(
        f"Checkpoint expects {want} conv features; no standard img_size "
        f"produces that with IN_CHANNELS={in_channels}. Check IN_CHANNELS.")


def resize_stack(frames, size):
    """Resize an (H, W, C) uint8 stack. Only needed if you trained at a size
    other than the tournament's 84x84."""
    if frames.shape[0] == size:
        return frames
    from PIL import Image
    return np.stack(
        [np.asarray(Image.fromarray(frames[..., c]).resize((size, size)))
         for c in range(frames.shape[-1])], axis=-1)


class Agent(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Resolve the weights relative to THIS file: the grader runs from a
        # different working directory than you do.
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), WEIGHTS_FILE)
        sd = torch.load(path, map_location=self.device)

        self.img_size = infer_img_size(sd, IN_CHANNELS, NUM_ACTIONS)
        self.net = QNetwork(IN_CHANNELS, NUM_ACTIONS, self.img_size)
        self.net.load_state_dict(sd)
        self.net.to(self.device).eval()

    def _to_training_format(self, state):
        """Convert the tournament's (84, 84, 6) into whatever your net wants.

        THIS IS THE PART YOU ADAPT. The example below assumes you trained
        with a single identity plane (0 for first_0, 255 for second_0) at a
        possibly different frame size. If your training pipeline already
        matched the tournament, this whole method is just `return state`.
        """
        state = np.asarray(state)
        frames = state[..., :4]           # 4 stacked grayscale frames
        indicator = state[..., 4:]        # 2 one-hot side channels

        # Channel 4 is hot for first_0, channel 5 for second_0.
        is_second = indicator[..., 1].max() > indicator[..., 0].max()

        frames = resize_stack(frames, self.img_size)
        plane = np.full(frames.shape[:2] + (1,),
                        255 if is_second else 0, dtype=np.uint8)
        return np.concatenate([frames, plane], axis=-1)

    def get_action(self, state=None) -> int:
        if state is None:
            return 0                      # NOOP
        obs = self._to_training_format(state)
        with torch.no_grad():
            q = self.net(torch.as_tensor(obs, device=self.device).unsqueeze(0))
        return int(q.argmax(dim=1).item())
