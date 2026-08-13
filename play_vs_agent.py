#!/usr/bin/env python3
"""
play_vs_agent.py -- play Atari Boxing against a student agent, or benchmark it.

  # play against it yourself
  python play_vs_agent.py --agent submissions/team_a --side second_0

  # headless scoring on BOTH sides (put this number in your report)
  python play_vs_agent.py --agent submissions/team_a --benchmark 20

  # two submissions against each other
  python play_vs_agent.py --agent submissions/team_a --vs agent \
                          --agent2 submissions/team_b

Controls:  arrow keys = move,  SPACE = punch,  combinations work
           R = restart,  ESC / Q = quit

Requires: pip install pygame
"""
import argparse
import importlib.util
import os
import sys
from collections import Counter

import numpy as np
import supersuit as ss
from pettingzoo.atari import boxing_v2

AGENTS = ["first_0", "second_0"]


# ---------------------------------------------------------------------------
# 1. The environment. This must match the tournament pipeline exactly, or a
#    student's agent will see observations it was never trained on.
# ---------------------------------------------------------------------------
def create_environment(render_mode="rgb_array"):
    """Reproduce the observation pipeline used by the training script."""
    env = boxing_v2.parallel_env(render_mode=render_mode)
    env = ss.max_observation_v0(env, 2)
    env = ss.frame_skip_v0(env, 4)
    env = ss.clip_reward_v0(env, lower_bound=-1, upper_bound=1)
    env = ss.color_reduction_v0(env, mode="B")
    env = ss.resize_v1(env, x_size=84, y_size=84)
    env = ss.frame_stack_v1(env, 4)
    env = ss.agent_indicator_v0(env, type_only=False)
    return env


# ---------------------------------------------------------------------------
# 2. Keyboard -> Atari action.
#
#    Atari has 18 actions: every combination of (up/down) x (left/right) x fire.
#    Rather than memorise the numbers, we look them up from which keys are held.
# ---------------------------------------------------------------------------
ACTION_TABLE = {
    #  (up,    down,  left,  right): (no fire, fire)
    (False, False, False, False): (0, 1),     # NOOP        / FIRE
    (True,  False, False, False): (2, 10),    # UP          / UPFIRE
    (False, True,  False, False): (5, 13),    # DOWN        / DOWNFIRE
    (False, False, True,  False): (4, 12),    # LEFT        / LEFTFIRE
    (False, False, False, True):  (3, 11),    # RIGHT       / RIGHTFIRE
    (True,  False, True,  False): (7, 15),    # UPLEFT      / UPLEFTFIRE
    (True,  False, False, True):  (6, 14),    # UPRIGHT     / UPRIGHTFIRE
    (False, True,  True,  False): (9, 17),    # DOWNLEFT    / DOWNLEFTFIRE
    (False, True,  False, True):  (8, 16),    # DOWNRIGHT   / DOWNRIGHTFIRE
}


def keys_to_action(pressed):
    """Read the currently held keys and return one of the 18 Atari actions."""
    import pygame
    up = pressed[pygame.K_UP]
    down = pressed[pygame.K_DOWN]
    left = pressed[pygame.K_LEFT]
    right = pressed[pygame.K_RIGHT]
    fire = pressed[pygame.K_SPACE]

    # Opposite directions cancel out, so the lookup key is always valid.
    if up and down:
        up = down = False
    if left and right:
        left = right = False

    no_fire_action, fire_action = ACTION_TABLE[(up, down, left, right)]
    return fire_action if fire else no_fire_action


# ---------------------------------------------------------------------------
# 3. Players. Each one just needs a get_action(state) method.
# ---------------------------------------------------------------------------
class HumanPlayer:
    name = "human"

    def get_action(self, state=None):
        import pygame
        pygame.event.pump()
        return keys_to_action(pygame.key.get_pressed())


class RandomPlayer:
    name = "random"

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)

    def get_action(self, state=None):
        return int(self.rng.integers(18))


def load_agent(path, env):
    """Load a student submission and build their Agent.

    `path` may be either the agent .py file, or the package directory that
    contains agent_template.py. The agent loads its own weights in __init__,
    so nothing else is needed here.
    """
    path = os.path.abspath(path)
    if os.path.isdir(path):
        candidates = [os.path.join(path, "agent_template.py"),
                      os.path.join(path, "agent.py")]
        found = [c for c in candidates if os.path.exists(c)]
        if not found:
            raise FileNotFoundError(
                f"No agent_template.py or agent.py inside {path}")
        path = found[0]

    # Put the submission's folder on the import path so its own imports work.
    pkg_dir = os.path.dirname(path)
    parent = os.path.dirname(pkg_dir)
    for d in (pkg_dir, parent):
        if d not in sys.path:
            sys.path.insert(0, d)

    spec = importlib.util.spec_from_file_location("student_agent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "Agent"):
        raise AttributeError(f"{path} does not define a class named Agent")

    agent = module.Agent(env)
    if hasattr(agent, "eval"):
        agent.eval()                      # turn off dropout / batchnorm training mode
    agent.name = os.path.basename(pkg_dir) or "agent"
    return agent


# ---------------------------------------------------------------------------
# 4. Display. We render the raw game frame ourselves so we can also draw the
#    scoreboard and read the keyboard from the same window.
# ---------------------------------------------------------------------------
class Display:
    def __init__(self, scale=4):
        import pygame
        pygame.init()
        pygame.display.set_caption("Boxing -- arrows to move, SPACE to punch")
        self.pygame = pygame
        self.scale = scale
        self.screen = None
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.clock = pygame.time.Clock()

    def draw(self, frame, lines, fps):
        pygame = self.pygame
        h, w = frame.shape[:2]
        panel = 60
        if self.screen is None:
            self.screen = pygame.display.set_mode(
                (w * self.scale, h * self.scale + panel))
        # pygame wants (width, height, 3), numpy gives (height, width, 3)
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surf = pygame.transform.scale(surf, (w * self.scale, h * self.scale))
        self.screen.fill((20, 20, 20))
        self.screen.blit(surf, (0, 0))
        for i, line in enumerate(lines):
            text = self.font.render(line, True, (235, 235, 235))
            self.screen.blit(text, (10, h * self.scale + 6 + i * 22))
        pygame.display.flip()
        self.clock.tick(fps)

    def close(self):
        self.pygame.quit()


# ---------------------------------------------------------------------------
# 5. One match (interactive).
# ---------------------------------------------------------------------------
def play_match(env, players, display, fps, seed):
    """players: {"first_0": obj, "second_0": obj}. Returns the final scores."""
    import pygame
    observations, _ = env.reset(seed=seed)
    score = {a: 0.0 for a in AGENTS}
    quit_requested = restart_requested = False

    while env.agents:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    quit_requested = True
                elif event.key == pygame.K_r:
                    restart_requested = True
        if quit_requested or restart_requested:
            break

        # Each player sees only its own observation, exactly as in the tournament.
        actions = {}
        for name in env.agents:
            actions[name] = int(players[name].get_action(observations[name]))

        observations, rewards, terminations, truncations, _ = env.step(actions)
        for name in AGENTS:
            score[name] += float(rewards.get(name, 0.0))

        frame = env.render()
        if frame is not None:
            display.draw(np.asarray(frame), [
                f"first_0  (white)  {players['first_0'].name:<10} {score['first_0']:+.0f}",
                f"second_0 (black)  {players['second_0'].name:<10} {score['second_0']:+.0f}",
            ], fps)

        if any(terminations.values()) or any(truncations.values()):
            break

    return score, quit_requested, restart_requested


# ---------------------------------------------------------------------------
# 6. Benchmark: no window, no keyboard. Scores the agent on BOTH sides.
#
#    This is the number to put in your report. An agent that is strong on one
#    side and weak on the other will score well here on one line and badly on
#    the other -- that gap is the most common reason a submission
#    underperforms in the tournament.
# ---------------------------------------------------------------------------
def benchmark(agent_path, opponent_kind, opponent_path, n_games, seed):
    env = create_environment(render_mode=None)
    agent = load_agent(agent_path, env)

    if opponent_kind == "agent":
        opponent = load_agent(opponent_path, env)
    else:
        opponent = RandomPlayer(seed)

    print(f"benchmarking {agent.name} vs {opponent.name}, "
          f"{n_games} games per side\n")
    print(f"{'side':<10} {'margin':>16} {'wins':>8} {'draws':>7} "
          f"{'actions used':>13} {'most common':>12}")

    results = {}
    for side in AGENTS:
        other = "second_0" if side == "first_0" else "first_0"
        margins, action_counts = [], Counter()

        for g in range(n_games):
            observations, _ = env.reset(seed=seed + 1000 * AGENTS.index(side) + g)
            score = {side: 0.0, other: 0.0}
            while env.agents:
                a = {}
                for name in env.agents:
                    who = agent if name == side else opponent
                    a[name] = int(who.get_action(observations[name]))
                action_counts[a[side]] += 1
                observations, rewards, terms, truncs, _ = env.step(a)
                for k in score:
                    score[k] += float(rewards.get(k, 0.0))
                if any(terms.values()) or any(truncs.values()):
                    break
            margins.append(score[side] - score[other])

        m = np.array(margins, float)
        ci = 1.96 * m.std(ddof=1) / np.sqrt(len(m)) if len(m) > 1 else 0.0
        total = max(sum(action_counts.values()), 1)
        top_a, top_c = action_counts.most_common(1)[0]
        results[side] = m
        print(f"{side:<10} {m.mean():+8.2f} +/- {ci:5.2f} "
              f"{int((m > 0).sum()):>4}/{len(m):<3} {int((m == 0).sum()):>7} "
              f"{len(action_counts):>10}/18 "
              f"{top_a:>7} ({100 * top_c / total:.0f}%)")

    env.close()

    gap = results["first_0"].mean() - results["second_0"].mean()
    print(f"\nside gap (white - black): {gap:+.2f}")
    if abs(gap) > 3.0:
        print("  WARNING: large gap. Your agent plays one side much better "
              "than the other.\n  In the tournament it will play both. "
              "This is a training problem, not a bug here.")
    else:
        print("  Side balance looks reasonable.")
    print("\nNote: rewards are clipped to +/-1 per step by the tournament "
          "pipeline,\nso 'margin' counts scoring events, not Boxing points.")


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--agent", required=True,
                   help="path to the submission folder or its agent .py file")
    p.add_argument("--side", default="second_0", choices=AGENTS,
                   help="which side the agent plays; you get the other one")
    p.add_argument("--vs", default="human", choices=["human", "random", "agent"],
                   help="who the agent plays against")
    p.add_argument("--agent2", default="", help="second submission, for --vs agent")
    p.add_argument("--benchmark", type=int, default=0, metavar="N",
                   help="run N games per side with no window, print scores, exit")
    p.add_argument("--fps", type=int, default=15,
                   help="frame_skip is 4, so 15 here is roughly real-time")
    p.add_argument("--scale", type=int, default=4)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    if args.benchmark:
        if args.vs == "agent" and not args.agent2:
            raise SystemExit("--vs agent requires --agent2")
        benchmark(args.agent, args.vs if args.vs == "agent" else "random",
                  args.agent2, args.benchmark, args.seed)
        return

    env = create_environment(render_mode="rgb_array")

    agent = load_agent(args.agent, env)
    other_side = "first_0" if args.side == "second_0" else "second_0"

    if args.vs == "human":
        opponent = HumanPlayer()
    elif args.vs == "random":
        opponent = RandomPlayer(args.seed)
    else:
        if not args.agent2:
            raise SystemExit("--vs agent requires --agent2")
        opponent = load_agent(args.agent2, env)

    players = {args.side: agent, other_side: opponent}
    print(f"first_0  (white, starts left):  {players['first_0'].name}")
    print(f"second_0 (black, starts right): {players['second_0'].name}")
    print("arrows = move, SPACE = punch, R = restart, ESC/Q = quit")

    import pygame
    display = Display(args.scale)
    seed = args.seed
    try:
        while True:
            score, quit_req, restart_req = play_match(
                env, players, display, args.fps, seed)
            print(f"final: first_0 {score['first_0']:+.0f}  "
                  f"second_0 {score['second_0']:+.0f}")
            if quit_req:
                break
            seed += 1
            if not restart_req:
                print("match over -- press R to play again, ESC to quit")
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            waiting = False
                            quit_req = True
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                waiting = False
                            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                                waiting = False
                                quit_req = True
                    display.clock.tick(30)
                if quit_req:
                    break
    finally:
        display.close()
        env.close()


if __name__ == "__main__":
    main()
