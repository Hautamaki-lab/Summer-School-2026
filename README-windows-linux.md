# Summer-School-2026

## Contents

1. [Install Ubuntu through WSL](#1-install-ubuntu-through-wsl)
2. [Install Miniconda inside Ubuntu](#2-install-miniconda-inside-ubuntu)
3. [Create a dedicated Conda environment](#3-create-a-dedicated-conda-environment)
4. [Install PettingZoo and Atari support](#4-install-pettingzoo-and-atari-support)
5. [Install the Boxing ROM](#5-install-the-boxing-rom)
6. [Set up the working directory and VS Code](#6-set-up-the-working-directory-and-vs-code)
7. [Run and verify Boxing](#7-run-and-verify-boxing)


## 1. Install Ubuntu through WSL
> [!IMPORTANT]
> This step is for windows machines only, if you have a linux machine jump to step 2.
> 
1. Open **Command Prompt as administrator**.

2. Run the following command:

   ```console
   wsl --install -d Ubuntu
   ```

3. If Windows requests a restart, restart the computer. A restart is not required if the command completes without requesting one.

4. If the download remains near 0% for several minutes, press Ctrl+C to cancel it. Then run:
   
    ```console
    wsl --shutdown
    wsl --install --web-download -d Ubuntu
    ```

    The --web-download option downloads Ubuntu directly instead of using the Microsoft Store delivery route.

5. After the installation finishes or the computer restarts, open PowerShell and verify that Ubuntu is installed:

    ```console
    wsl --list --verbose
    ```
    You should see an entry similar to:
    ```
    NAME      STATE     VERSION
    Ubuntu    Stopped   2
    ```
6. If the command reports that there are no installed distributions, run:
    ```console
    wsl --install --web-download -d Ubuntu
    ```

7. Launch Ubuntu using either of these methods:

    - Open Ubuntu from the Start menu.
    
    - Run the following command in PowerShell:
        ```console
        wsl -d Ubuntu
        ```
8. When prompted, enter a new Linux username. Use something simple and lowercase.

9. Create a password. Nothing will appear on the screen while you type the password. This is normal.

    You should eventually see a prompt similar to this:
    
    ```console
    nima@computername:~$
    ```


## 2. Install Miniconda inside Ubuntu

Miniconda is a lightweight installation of Conda. It provides Python and the Conda environment manager without installing many additional packages.

1. Open the **Ubuntu terminal**.

2. Update Ubuntu’s information about available software packages:

   ```console
   sudo apt update
   ```

   - `sudo` runs the command with administrator privileges.
   - `apt` is Ubuntu’s package manager.
   - `update` refreshes the list of available packages. It does not upgrade the installed packages.

3. Install `curl`:

   ```console
   sudo apt install -y curl
   ```

   - `install` tells Ubuntu to install a package.
   - `curl` is a command-line tool for downloading files from the internet.
   - `-y` automatically answers “yes” when Ubuntu asks for confirmation.

4. Move to your Linux home directory:

   ```console
   cd ~
   ```

   - `cd` means “change directory.”
   - `~` represents the current user’s home directory, such as `/home/nima`.

5. Download the Miniconda installer:

   ```console
   curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   ```

   - `curl` downloads the file from the supplied address.
   - `-O` saves it using its original filename.
   - The downloaded `.sh` file is a Linux shell script containing the installation commands.

6. Run the Miniconda installer:

   ```console
   bash Miniconda3-latest-Linux-x86_64.sh
   ```

   - `bash` is the command-line shell used to execute the installer script.

7. During installation:

   - Press `Enter` to begin reviewing the licence.
   - Continue through the licence text.
   - Type `yes` if you accept the licence.
   - Press `Enter` to accept the default installation location.
   - Type `yes` when asked whether Conda should be initialized.

8. Reload the terminal configuration:

   ```console
   source ~/.bashrc
   ```

   - `.bashrc` is a configuration file used by the Bash terminal.
   - The installer adds Conda’s initialization settings to this file.
   - `source` reloads the file without requiring the terminal to be closed.

   The terminal prompt should now begin with:

   ```text
   (base)
   ```

   `(base)` indicates that Conda’s default environment is active.

9. Verify the installation:

   ```console
   conda --version
   ```

   - `conda` runs the Conda environment manager.
   - `--version` displays the installed Conda version.

   You should see output similar to:

   ```text
   conda 26.5.3
   ```

   The exact version number may be different.

## 3. Create a dedicated Conda environment

A Conda environment is an isolated workspace with its own Python version and installed packages. Using a separate environment prevents this project’s packages from interfering with other Python projects.

1. Accept the Terms of Service for Anaconda’s default package channels if you agree to them:

   ```console
   conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
   conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
   ```

   - `conda tos accept` records acceptance of a channel’s Terms of Service.
   - `--override-channels` tells Conda to apply the command only to the explicitly specified channel.
   - `--channel` specifies the package repository to which the command applies.
   - `pkgs/main` contains commonly used Python and system packages.
   - `pkgs/r` primarily contains packages for the R programming language but is also included in Conda’s default channel configuration.

2. Create an environment named `pettingzoo`:

   ```console
   conda create --name pettingzoo python=3.12 pip -y
   ```

   - `conda create` creates a new isolated environment.
   - `--name pettingzoo` gives the environment the name `pettingzoo`.
   - `python=3.12` installs Python 3.12 in the environment.
   - `pip` installs Python’s standard package installer inside the environment.
   - `-y` automatically confirms that Conda may install the required packages.

3. Activate the environment:

   ```console
   conda activate pettingzoo
   ```

   - Activating an environment makes its Python interpreter and installed packages available in the current terminal.
   - Commands such as `python` and `pip` will now refer to the versions inside the `pettingzoo` environment.

   The terminal prompt should now begin with:

   ```text
   (pettingzoo)
   ```

4. Verify the Python version:

   ```console
   python --version
   ```

   You should see output similar to:

   ```text
   Python 3.12.12
   ```

   The final version number may be different, but it should begin with `3.12`.

5. Verify that Python is coming from the new environment:

   ```console
   which python
   ```

   - `which` displays the location of the program that will run when a command is entered.
   - The output should contain `miniconda3/envs/pettingzoo`, confirming that the isolated environment is active.

   Example:

   ```text
   /home/your-username/miniconda3/envs/pettingzoo/bin/python
   ```

Whenever a new Ubuntu terminal is opened, reactivate this environment before working on the project:

```console
conda activate pettingzoo
```

## 4. Install PettingZoo and Atari support

All commands in this section should be run inside the Ubuntu terminal with the `pettingzoo` Conda environment active.

1. Activate the environment if it is not already active:

   ```console
   conda activate pettingzoo
   ```

   The terminal prompt should begin with:

   ```text
   (pettingzoo)
   ```

2. Update `pip` inside the environment:

   ```console
   python -m pip install --upgrade pip
   ```

   - `python -m pip` runs the copy of `pip` associated with the active Python interpreter.
   - This helps ensure packages are installed inside the `pettingzoo` Conda environment rather than somewhere else on the system.
   - `install --upgrade pip` updates `pip` to its latest available version.

3. Install PettingZoo, its Atari dependencies, and AutoROM:

   ```console
   python -m pip install "pettingzoo[atari]==1.26.1" "autorom==0.6.1"
   ```

   - `pettingzoo` provides environments for multi-agent reinforcement learning.
   - `[atari]` requests the additional dependencies needed to run PettingZoo’s Atari environments.
   - `==1.26.1` installs the specific PettingZoo version tested for this guide.
   - `autorom` provides the command used to install the Atari ROM files.
   - The quotation marks prevent the shell from interpreting the square brackets as a filename pattern.
   - AutoROM is installed in this step, but the ROM files will be installed in the next section.

4. Verify that PettingZoo and the Boxing environment can be imported:

   ```console
   python -c "import pettingzoo; from pettingzoo.atari import boxing_v2; print('PettingZoo version:', pettingzoo.__version__)"
   ```

   - `python -c` runs a short piece of Python code directly from the terminal.
   - `import pettingzoo` checks that the main package is installed.
   - `from pettingzoo.atari import boxing_v2` checks that the Boxing environment is available.
   - The final part prints the installed PettingZoo version.

   The expected output is:

   ```text
   PettingZoo version: 1.26.1
   ```

## 5. Install the Boxing ROM

PettingZoo provides the Boxing environment code, but the Atari game data is stored separately in a ROM file. AutoROM downloads and installs the supported Atari ROM collection, including Boxing.

All commands in this section should be run with the `pettingzoo` Conda environment active.


1. Install the Atari ROMs:

   ```console
   AutoROM --accept-license
   ```

   - `AutoROM` runs the ROM installation tool installed in the previous section.
   - `--accept-license` confirms acceptance of the Atari ROM licence without showing an interactive confirmation prompt.
   - Run this command only if you have reviewed and agree to the applicable licence terms.
   - AutoROM installs the ROM files where PettingZoo’s Atari dependency can locate them.

   The command should download and install several ROM files. Near the end of the output, you should see:

   ```text
   Done!
   ```

2. Verify that PettingZoo can load the Boxing ROM:

   ```console
   python -c "from pettingzoo.atari import boxing_v2; env = boxing_v2.parallel_env(); env.reset(seed=42); print('Boxing loaded successfully:', env.agents); env.close()"
   ```

   This command:

   - Imports the Boxing environment.
   - Creates a parallel two-player Boxing environment.
   - Resets the environment to begin a new game.
   - Prints the active agents.
   - Closes the environment cleanly.

   You should see:

   ```text
   Boxing loaded successfully: ['first_0', 'second_0']
   ```

   No game window appears during this test because rendering is not enabled. The purpose of this command is only to verify that the ROM can be found and loaded.

## 6. Set up the working directory and VS Code

The project files will be stored inside Ubuntu’s Linux filesystem. Windows File Explorer can access this directory, while VS Code can edit and run the files directly inside WSL.

### Create the working directory

1. Create a directory for the project:

   ```console
   mkdir -p ~/pettingzoo-boxing
   ```

   - `mkdir` means “make directory.”
   - `-p` creates the directory if it does not already exist and prevents an error if it already exists.
   - `~` represents the current Linux user’s home directory.
   - The project directory will therefore be located at `/home/your-username/pettingzoo-boxing`.

2. Move into the project directory:

   ```console
   cd ~/pettingzoo-boxing
   ```

3. Display the current directory:

   ```console
   pwd
   ```

   - `pwd` means “print working directory.”
   - It displays the full path of the directory currently open in the terminal.

   You should see output similar to:

   ```text
   /home/your-username/pettingzoo-boxing
   ```

### Open the directory in Windows File Explorer

4. From inside the project directory, run:

   ```console
   explorer.exe .
   ```

   - `explorer.exe` launches Windows File Explorer.
   - `.` represents the current directory.
   - WSL translates the Linux directory into a location that Windows File Explorer can access.

   File Explorer should open the `pettingzoo-boxing` directory. Files can be copied into or out of this directory using the normal Windows interface.

### Install Visual Studio Code

5. Download the Windows version of Visual Studio Code from the [official Visual Studio Code website](https://code.visualstudio.com/).

6. Run the Windows installer.

7. During installation, keep the default options and ensure that the option to add Visual Studio Code to `PATH` is enabled.

   Visual Studio Code should be installed on Windows. Do not install a separate Linux copy of Visual Studio Code inside Ubuntu.

### Install the WSL extension

8. Open Visual Studio Code.

9. Open the Extensions view by pressing `Ctrl+Shift+X`.

10. Search for:

    ```text
    WSL
    ```

11. Install the extension named **WSL**, published by Microsoft.

    This extension allows the Windows version of Visual Studio Code to edit files and run programs inside Ubuntu.

12. Close Visual Studio Code after the extension is installed.

### Find the Conda environment’s Python path

13. Return to the Ubuntu terminal and move to the project directory:

    ```console
    cd ~/pettingzoo-boxing
    ```

14. Display the full path of the active Python interpreter:

    ```console
    python -c "import sys; print(sys.executable)"
    ```

    - `sys.executable` contains the full path of the Python interpreter running the command.
    - Because the `pettingzoo` environment is active, this path should point to the environment’s copy of Python.

    The output should be similar to:

    ```text
    /home/your-username/miniconda3/envs/pettingzoo/bin/python
    ```

    Copy or record the complete path. It will be used when configuring Visual Studio Code.

### Open the project in Visual Studio Code

15. Open the current directory in Visual Studio Code:

    ```console
    code .
    ```

    - `code` launches Visual Studio Code.
    - `.` tells Visual Studio Code to open the current directory.
    - During the first launch, Visual Studio Code may install a small VS Code Server component inside WSL. Wait for this process to finish.

    The bottom-left corner of the Visual Studio Code window should display:

    ```text
    WSL: Ubuntu
    ```

    If `code .` produces a `command not found` error, close and reopen the Ubuntu terminal after installing Visual Studio Code, then try the command again.

### Configure Python in Visual Studio Code

16. In the WSL-connected Visual Studio Code window, open the Extensions view with `Ctrl+Shift+X`.

17. Search for **Python** and install the extension published by Microsoft.

18. Press `Ctrl+Shift+P` to open the Command Palette.

19. Search for and select:

    ```text
    Python: Select Interpreter
    ```

20. If the `pettingzoo` environment appears in the list, select it. It should look similar to:

    ```text
    Python 3.12.x ('pettingzoo': conda)
    ```

21. If the environment does not appear:

    - Select **Enter interpreter path...**.
    - Paste the Python path found in Step 14.
    - Press `Enter`.

    The path should be similar to:

    ```text
    /home/your-username/miniconda3/envs/pettingzoo/bin/python
    ```

    Use the exact path printed on your system rather than copying the example path.

22. Open an integrated terminal using **Terminal → New Terminal**.

23. Verify the selected Python interpreter:

    ```console
    python --version
    python -c "import sys; print(sys.executable)"
    ```

    The Python version should begin with `3.12`, and the interpreter path should contain:

    ```text
    miniconda3/envs/pettingzoo
    ```

The project directory is now ready. Python files created in the Visual Studio Code Explorer will be stored inside `~/pettingzoo-boxing` and will run using the `pettingzoo` Conda environment.

## 7. Run and verify Boxing

In this section, both boxers will select random actions. The purpose is to verify that the environment, ROM, rendering, and PettingZoo API are working correctly.

### Create the Python file

1. In the Visual Studio Code Explorer, select the **New File** button.

2. Name the file:

   ```text
   boxing_random.py
   ```

3. Add the following code:

   ```python
   import time

   from pettingzoo.atari import boxing_v2


   # Create the Boxing environment.
   env = boxing_v2.parallel_env(render_mode="human")

   # Start a new game.
   env.reset(seed=42)

   # Continue while the game has active players.
   while len(env.agents) > 0:

       # Create an empty dictionary for the players' actions.
       actions = {}

       # Select a random action for each player.
       for agent in env.agents:
           random_action = env.action_space(agent).sample()
           actions[agent] = random_action

       # Send the actions to the game.
       env.step(actions)

       # Slow the program down so that the game can be watched.
       time.sleep(1 / 60)

   # Close the game window after the game finishes.
   env.close()

   print("The game has finished.")
   ```

4. Save the file by pressing `Ctrl+S`.

### Understand the code

- The following line imports Python's time-related functions:

  ```python
  import time
  ```

- The following line imports PettingZoo's Boxing environment:

  ```python
  from pettingzoo.atari import boxing_v2
  ```

- This line creates the Boxing environment:

  ```python
  env = boxing_v2.parallel_env(render_mode="human")
  ```

  - `parallel_env` allows both players to provide their actions during each game step.
  - `render_mode="human"` tells PettingZoo to display the game in a window.

- This line starts a new game:

  ```python
  env.reset(seed=42)
  ```

  - `reset` places both players at the beginning of a new game.
  - `seed=42` makes the initial conditions reproducible when possible.

- The following loop continues while the game has active players:

  ```python
  while len(env.agents) > 0:
  ```

- `env.agents` contains the players that are currently active.
- `len(env.agents)` tells us how many active players remain.
- This line creates an empty dictionary:

  ```python
  actions = {}
  ```

- The dictionary will store one action for each player.
- The following loop visits each active player:

  ```python
  for agent in env.agents:
  ```

- This line selects a random valid action for the current player:

  ```python
  random_action = env.action_space(agent).sample()
  ```

- The action is then placed in the `actions` dictionary:

  ```python
  actions[agent] = random_action
  ```

- This line sends both players' actions to the game:

  ```python
  env.step(actions)
  ```

  The game processes the actions and moves forward by one step.

- The following line adds a short delay:

  ```python
  time.sleep(1 / 60)
  ```

- Without the delay, the program may run too quickly to watch comfortably.
- After the game finishes, this line closes the game window:

  ```python
  env.close()
  ```

- Finally, the program prints a message:

  ```python
  print("The game has finished.")
  ```

### Run the program

5. Open the Visual Studio Code integrated terminal using **Terminal â†’ New Terminal**.

6. Run:

   ```console
   python boxing_random.py
   ```

A Boxing window should open. Both the white and black boxers will move and punch randomly.

When the game finishes, the terminal will display:

```text
The game has finished.
```

To stop the program before the game finishes, select the terminal and press `Ctrl+C`.

### Troubleshoot a missing game window

If the program runs but no game window appears, close Visual Studio Code and Ubuntu. Then open PowerShell and run:

```console
wsl --update
wsl --shutdown
```

Reopen Ubuntu, return to the project directory, and open it again:

```console
cd ~/pettingzoo-boxing
code .
```

Then rerun:

```console
python boxing_random.py
```

## 8. Run and verify Breakout

Boxing is a two-player game, so it uses PettingZoo. Breakout is a single-player game, so it uses Gymnasium.

Both games use the Arcade Learning Environment to run Atari games.

### Install Gymnasium's Atari support

1. Make sure the `pettingzoo` Conda environment is active.

2. Install Gymnasium's Atari dependencies:

   ```console
   python -m pip install "gymnasium[atari]"
   ```

   - `gymnasium` provides environments for reinforcement learning.
   - `[atari]` installs the additional Arcade Learning Environment dependencies.
   - The quotation marks prevent the shell from interpreting the square brackets.

3. Verify that Breakout can be loaded:

   ```console
   python -c "import gymnasium as gym; import ale_py; gym.register_envs(ale_py); env = gym.make('ALE/Breakout-v5'); print('Breakout loaded successfully:', env.action_space); env.close()"
   ```

   You should see output similar to:

   ```text
   Breakout loaded successfully: Discrete(4)
   ```

### Breakout programming exercise

In the previous section, the Boxing code was provided in full. In this exercise, some parts of the Breakout code are missing.

Students should use the word bank to complete the program.

4. Create a new Python file named:

   ```text
   breakout_random.py
   ```

5. Add the following incomplete code:

   ```python
   import time

   import ale_py
   import gymnasium as gym


   # Make the Atari environments available to Gymnasium.
   gym.register_envs(ale_py)

   # Create the Breakout environment.
   env = gym.make(
       "________________________",
       render_mode="________________________",
   )

   # Start a new game.
   observation, info = env.reset(seed=42)

   # The game has not finished yet.
   game_finished = False

   # Continue until the game finishes.
   while not game_finished:

       # Select a random action.
       action = ________________________________

       # Send the action to the game.
       observation, reward, terminated, truncated, info = (
           ________________________________
       )

       # Check whether the game has finished.
       game_finished = ________________________________

       # Slow the program down so that the game can be watched.
       time.sleep(1 / 60)

   # Close the game window.
   env.close()

   print("The game has finished.")
   ```

### Word bank

Use each of the following items once:

```text
env.action_space.sample()
ALE/Breakout-v5
terminated or truncated
env.step(action)
human
```

6. Save the file:

   - On Windows and Linux, press `Ctrl+S`.
   - On macOS, press `Command+S`.

7. Open the Visual Studio Code integrated terminal and run:

   ```console
   python breakout_random.py
   ```

A Breakout window should open. The paddle will perform random actions.

Because the actions are random, the agent will probably play poorly. The purpose of this exercise is only to verify that the environment works and understand the basic interaction loop.

When the game finishes, the terminal should display:

```text
The game has finished.
```

### Exercise solution

Try to complete the exercise before opening the solution.

<details>
<summary>Show the completed code</summary>

```python
import time

import ale_py
import gymnasium as gym


# Make the Atari environments available to Gymnasium.
gym.register_envs(ale_py)

# Create the Breakout environment.
env = gym.make(
    "ALE/Breakout-v5",
    render_mode="human",
)

# Start a new game.
observation, info = env.reset(seed=42)

# The game has not finished yet.
game_finished = False

# Continue until the game finishes.
while not game_finished:

    # Select a random action.
    action = env.action_space.sample()

    # Send the action to the game.
    observation, reward, terminated, truncated, info = (
        env.step(action)
    )

    # Check whether the game has finished.
    game_finished = terminated or truncated

    # Slow the program down so that the game can be watched.
    time.sleep(1 / 60)

# Close the game window.
env.close()

print("The game has finished.")
```

</details>

### Understand the important parts

This line creates the Breakout environment:

```python
env = gym.make(
    "ALE/Breakout-v5",
    render_mode="human",
)
```

- `"ALE/Breakout-v5"` identifies the game.
- `render_mode="human"` displays the game in a window.

This line starts a new game:

```python
observation, info = env.reset(seed=42)
```

- `observation` contains the current game image.
- `info` contains additional information about the environment.

This line selects a random valid action:

```python
action = env.action_space.sample()
```

Unlike Boxing, only one action is required because Breakout has only one player.

This code sends the action to the environment:

```python
observation, reward, terminated, truncated, info = (
    env.step(action)
)
```

It returns:

- `observation`: the new game image.
- `reward`: the reward produced by the action.
- `terminated`: whether the game ended naturally.
- `truncated`: whether the game ended because of an external limit.
- `info`: additional information.

This line checks both possible ways the game can finish:

```python
game_finished = terminated or truncated
```

The loop stops when either value becomes `True`.

### Optional challenge: calculate the total reward

Add this line before the `while` loop:

```python
total_reward = 0
```

Add this line inside the loop after `env.step(action)`:

```python
total_reward = total_reward + reward
```

Replace the final `print` with:

```python
print("The game has finished.")
print("Total reward:", total_reward)
```

### Troubleshoot Breakout

If Gymnasium reports that the Atari environment cannot be found, confirm that the required packages are installed:

```console
python -m pip show gymnasium ale-py
```

Then reinstall the Atari dependencies if necessary:

```console
python -m pip install "gymnasium[atari]"
```

If it reports that the Breakout ROM cannot be found, run AutoROM again:

```console
python -m AutoROM.AutoROM --accept-license
```

Then repeat the Breakout verification command.
