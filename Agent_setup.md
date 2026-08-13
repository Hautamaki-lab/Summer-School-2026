# Connecting Your Agent — Setup Guide

You have trained a policy. This guide gets it running inside the tournament
interface so you can play against it, score it, and start experimenting.

Budget about 20 minutes for the first working run.

---

## 1. The three pieces

| File | Who writes it | What it does |
|---|---|---|
| `agent_template.py` | **You** | Wraps your trained network in the interface the tournament calls |
| `play_vs_agent.py` | Provided | Loads your agent, lets you play it or score it |
| `policy_*.pt` | **You** | Your trained weights |

Your submission is a folder:

```
submissions/my_team/
    __init__.py            # provided, don't change
    agent_template.py      # you fill this in
    policy_ep500.pt        # your weights
```

---

## 2. The contract

The tournament does exactly two things with your code:

```python
agent = Agent(env)                 # your constructor loads your weights
action = agent.get_action(state)   # returns an int in 0..17
```

That's it. No training functions, no reset hook, no access to the raw game.
Three obligations follow:

**Load your own weights in `__init__`.** The only argument is `env`. Resolve
the checkpoint path relative to your own file:

```python
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), WEIGHTS_FILE)
```

The grader runs from a different working directory than you do. A relative
path like `"policy_ep500.pt"` will not be found.

**Your network class must match the checkpoint exactly.** Same layers, same
shapes, same order, same attribute names. Copy the class verbatim from your
training script — do not retype it.

**`get_action` does all conversion.** The harness hands you the observation
untouched. Transposing, normalising, resizing, remapping channels: all yours.

---

## 3. What the observation looks like

```
shape  (84, 84, 6)     dtype  uint8     layout  channel-LAST
```

| Channels | Contents |
|---|---|
| 0–3 | The last 4 grayscale game frames, oldest first |
| 4 | 255 if you are `first_0` (white boxer), else 0 |
| 5 | 255 if you are `second_0` (black boxer), else 0 |

Two things to notice.

**Channel-last.** PyTorch convolutions want channel-first. You need a
`permute` somewhere — either inside your network's `forward` (as the course
training script does) or in `get_action`.

**Channels 4 and 5 are how you know which boxer you control.** Both players
receive the *same picture*. There is no other signal. An agent that ignores
these channels cannot tell which boxer is its own, and will play one side
competently and the other one badly.

---

## 4. Bridging a pipeline mismatch

If your training preprocessing differs from the tournament's, `get_action`
is where you reconcile it. Common cases:

| Mismatch | Fix, inside `get_action` |
|---|---|
| You trained at 42×42 or 64×64 | Resize channels 0–3 down before feeding the net |
| You used **one** side plane, not two | Read channels 4–5, rebuild your single plane |
| You used no side signal at all | Drop channels 4–5 (and accept the side-blindness) |
| Different channel order | Reorder before the forward pass |

**One mismatch you cannot fix here: frame skip.** The tournament advances
four game frames per step. If you trained without `frame_skip_v0`, your
policy learned to react four times faster than it will be allowed to. No
inference-time trick recovers this — it requires retraining. Check your
training pipeline for this before anything else.

The provided `agent_template.py` includes a working example of the
size-and-plane bridge. If your training pipeline already matched the
tournament exactly, `_to_training_format` becomes `return state`.

---

## 5. Get it running

```bash
# score it headlessly on both sides -- start here
python play_vs_agent.py --agent submissions/my_team --benchmark 20

# play it yourself
python play_vs_agent.py --agent submissions/my_team --side second_0

# two submissions against each other
python play_vs_agent.py --agent submissions/my_team --vs agent \
                        --agent2 submissions/other_team
```

Controls: **arrow keys** move, **SPACE** punches, combinations work.
**R** restarts, **ESC** or **Q** quits.

---

## 6. Required check before you submit

Run the benchmark and look at the **side gap** line.

```
side          margin     wins   draws   actions used   most common
first_0       +4.20 +/- 1.31    14/20        1              12/18      3 (24%)
second_0      -0.85 +/- 1.09     8/20        3               9/18      0 (41%)

side gap (white - black): +5.05
```

A large gap means your agent is good at one side and weak at the other. In
the tournament it plays **both**, so the weak side caps your result. This is
a training problem, not a harness problem — the usual causes are:

- Your learning policy was always assigned the same side during training,
  so the replay buffer barely contains the other side's experience.
- Your side encoding is asymmetric (e.g. one side is an all-zero plane, so
  it is the network's silent default and the other side has to be learned as
  a correction on top).
- Your evaluation during training only measured one side, so you never saw
  the problem.

Also watch **actions used**. An agent stuck on 1–2 distinct actions has
collapsed, whatever its margin says.

---

## 7. Common errors

**`size mismatch for fc.0.weight: copying a param with shape [512, 64]`**
Your checkpoint was trained at a different frame size than the network you
just built. The template's `infer_img_size` handles this automatically — if
you see this error, you removed or bypassed it.

**`Error(s) in loading state_dict: Missing key(s)` / `Unexpected key(s)`**
Your network class does not match the one you trained with. Copy it verbatim
from the training script.

**`FileNotFoundError` on the weights**
You used a relative path. Resolve against `os.path.dirname(__file__)`.

**`No agent_template.py or agent.py inside ...`**
Point `--agent` at your submission folder, or directly at the `.py` file.

**Agent does nothing / always returns the same action**
Check the shape and dtype reaching your network, and confirm you called
`.eval()`. Then check whether it is reading channels 4–5 at all.

---

## 8. Things worth experimenting with

Once it runs, the interesting questions are yours to explore:

- Play it yourself on both sides. Where does it fall apart? Does it chase,
  retreat, or spam punches?
- Benchmark against random, then against an earlier checkpoint of your own.
  Is later actually better?
- Feed it a hand-modified observation with the side channels swapped. Does
  the chosen action change? If not, it is ignoring which boxer it controls.
- Pit your checkpoints against each other with `--vs agent`. Self-play can
  cycle: a newer policy is not automatically stronger than an older one.

Note: the tournament pipeline clips rewards to ±1 per step, so the "margin"
you see counts scoring events rather than Boxing's own point total.
