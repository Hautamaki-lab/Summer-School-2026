# Summer-School-2026: macOS

> [!IMPORTANT]
> This guide is intended for Macs with Apple silicon, such as an Apple M1, M2, M3, M4, or later M-series chip. It was prepared from official documentation and current package availability, but it has not been tested on a physical Mac.
>
> Intel-based Macs are not supported by this guide. Read Section 1 before installing anything.

## Contents

1. [Check the Mac processor and compatibility](#1-check-the-mac-processor-and-compatibility)
2. [Install Miniconda on macOS](#2-install-miniconda-on-macos)
3. [Create a dedicated Conda environment](#3-create-a-dedicated-conda-environment)
4. [Install PettingZoo and Atari support](#4-install-pettingzoo-and-atari-support)
5. [Install the Boxing ROM](#5-install-the-boxing-rom)
6. [Set up the working directory and VS Code](#6-set-up-the-working-directory-and-vs-code)
7. [Run and verify Boxing](#7-run-and-verify-boxing)
8. [References](#8-references)

## 1. Check the Mac processor and compatibility

The PettingZoo Atari dependencies used in this guide are available for Macs with Apple silicon. Before continuing, confirm that the Mac uses an Apple chip and that Terminal is running natively rather than through Rosetta.

### Check the processor using About This Mac

1. Open the Apple menu in the upper-left corner of the screen.

2. Select **About This Mac**.

3. Look for either **Chip** or **Processor**:

   - If the window shows **Chip: Apple M1**, **Apple M2**, **Apple M3**, **Apple M4**, or another Apple M-series chip, continue with this guide.
   - If the window shows **Processor: Intel**, stop here and read the Intel Mac notice below.

### Confirm the architecture in Terminal

4. Open **Terminal**. It can be found using Spotlight Search or under **Applications → Utilities → Terminal**.

5. Run:

   ```console
   uname -m
   ```

   - `uname` displays information about the operating system.
   - `-m` asks it to display the machine architecture.

   On an Apple silicon Mac running natively, the expected output is:

   ```text
   arm64
   ```

### If an Apple silicon Mac reports `x86_64`

If **About This Mac** shows an Apple chip but `uname -m` returns `x86_64`, Terminal is probably running through Rosetta.

1. Close Terminal.

2. Open Finder and go to **Applications → Utilities**.

3. Select **Terminal.app** and press `Command+I` to open its information window.

4. If **Open using Rosetta** is selected, clear that option.

5. Reopen Terminal and run:

   ```console
   uname -m
   ```

   Continue only after it returns:

   ```text
   arm64
   ```

### Intel Mac notice

Anaconda stopped producing new packages for Intel Macs in August 2025. In addition, the current multi-agent Atari dependency required by PettingZoo 1.26.1 does not provide the same ready-to-install Python 3.12 package for Intel macOS.

This guide therefore does not attempt to install the project on an Intel Mac. Building the Atari dependency from source would require a separate compiler-based procedure and is not suitable for a beginner installation guide.

Intel Mac users should use one of these alternatives:

- A Windows or Linux computer that follows the Windows/Linux guide.
- A remote Linux computer provided by the course.
- An Apple silicon Mac.

### Check the macOS version

6. In **About This Mac**, check the installed macOS version.

The current Apple silicon Miniconda installer requires macOS 12.1 or later. Install available macOS updates before continuing if the system is older.

## 2. Install Miniconda on macOS

Miniconda is a lightweight installation of Conda. It provides Python and the Conda environment manager without installing many additional packages.

The commands in this section should be run in the macOS Terminal.

### Check for an existing Conda installation

1. Run:

   ```console
   conda --version
   ```

   If this command displays a Conda version, Conda is already installed. Do not install a second copy. Continue to Section 3.

   If Terminal reports `command not found: conda`, continue with the installation below.

### Download Miniconda

2. Move to your macOS home directory:

   ```console
   cd ~
   ```

   - `cd` means “change directory.”
   - `~` represents the current user's home directory, such as `/Users/nima`.

3. Download the native Apple silicon Miniconda installer:

   ```console
   curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
   ```

   - `curl` downloads the file from the supplied address.
   - `-O` saves the file using its original filename.
   - `MacOSX-arm64` identifies the installer for Apple silicon Macs.
   - macOS includes `curl`, so it does not need to be installed separately.

4. Optional but recommended: calculate the installer's SHA-256 hash:

   ```console
   shasum -a 256 ~/Miniconda3-latest-MacOSX-arm64.sh
   ```

   Compare the displayed value with the SHA-256 value for the same filename in the [official Miniconda installer directory](https://repo.anaconda.com/miniconda/). Matching values confirm that the downloaded file is intact.

### Run the installer

5. Run the Miniconda installer:

   ```console
   bash ~/Miniconda3-latest-MacOSX-arm64.sh
   ```

   - `bash` executes the downloaded shell script.
   - The installer should identify the computer as `arm64`. If it reports an incompatible architecture, return to Section 1 and check for Rosetta.

6. During installation:

   - Press `Return` to begin reviewing the licence.
   - Continue through the licence text.
   - Type `yes` if you accept the licence.
   - Press `Return` to accept the default installation location.
   - Type `yes` when asked whether Conda should be initialized.

   The default installation location should be similar to:

   ```text
   /Users/your-username/miniconda3
   ```

### Reload the shell configuration

7. Reload the default macOS shell configuration:

   ```console
   source ~/.zshrc
   ```

   - Modern macOS versions use Zsh as the default shell.
   - `.zshrc` is the configuration file used by interactive Zsh terminals.
   - `source` reloads the file without requiring Terminal to be closed.

   The Terminal prompt should now begin with:

   ```text
   (base)
   ```

   `(base)` indicates that Conda's default environment is active.

8. Verify the installation:

   ```console
   conda --version
   ```

   You should see output similar to:

   ```text
   conda 26.5.3
   ```

   The exact version number may be different.

### If `conda` is still not found

If `source ~/.zshrc` does not make the `conda` command available, run:

```console
~/miniconda3/bin/conda init zsh
source ~/.zshrc
```

- The first command adds Conda initialization to the Zsh configuration.
- The second command reloads that configuration.

If `~/miniconda3/bin/conda` does not exist, the installation did not finish at the default location. Review the location printed by the installer before continuing.

## 3. Create a dedicated Conda environment

A Conda environment is an isolated workspace with its own Python version and installed packages. Using a separate environment prevents this project's packages from interfering with other Python projects.

1. Accept the Terms of Service for Anaconda's default package channels if you agree to them:

   ```console
   conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
   conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
   ```

   - `conda tos accept` records acceptance of a channel's Terms of Service.
   - `--override-channels` tells Conda to apply the command only to the explicitly specified channel.
   - `--channel` specifies the package repository to which the command applies.
   - `pkgs/main` contains commonly used Python and system packages.
   - `pkgs/r` primarily contains packages for the R programming language but is included in Conda's default channel configuration.

2. Create an environment named `pettingzoo`:

   ```console
   conda create --name pettingzoo python=3.12 pip -y
   ```

   - `conda create` creates a new isolated environment.
   - `--name pettingzoo` gives the environment the name `pettingzoo`.
   - `python=3.12` installs Python 3.12 in the environment.
   - `pip` installs Python's package installer inside the environment.
   - `-y` automatically confirms that Conda may install the required packages.

3. Activate the environment:

   ```console
   conda activate pettingzoo
   ```

   - Activating an environment makes its Python interpreter and installed packages available in the current Terminal session.
   - Commands such as `python` and `pip` will now refer to the versions inside the `pettingzoo` environment.

   The Terminal prompt should now begin with:

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
   /Users/your-username/miniconda3/envs/pettingzoo/bin/python
   ```

Whenever a new Terminal window is opened, reactivate this environment before working on the project:

```console
conda activate pettingzoo
```

## 4. Install PettingZoo and Atari support

All commands in this section should be run with the `pettingzoo` Conda environment active.

1. Update `pip` inside the environment:

   ```console
   python -m pip install --upgrade pip
   ```

   - `python -m pip` runs the copy of `pip` associated with the active Python interpreter.
   - This helps ensure packages are installed inside the `pettingzoo` environment rather than elsewhere on the system.
   - `install --upgrade pip` updates `pip` to its latest available version.

2. Confirm that Python is running natively for Apple silicon:

   ```console
   python -c "import platform; print(platform.machine())"
   ```

   The expected output is:

   ```text
   arm64
   ```

   If it displays `x86_64`, do not continue. The Conda installation is running through Intel emulation. Return to Section 1 and install the native Apple silicon version of Miniconda.

3. Install PettingZoo, its Atari dependencies, and AutoROM:

   ```console
   python -m pip install "pettingzoo[atari]==1.26.1" "autorom==0.6.1"
   ```

   - `pettingzoo` provides environments for multi-agent reinforcement learning.
   - `[atari]` requests the additional dependencies needed for PettingZoo's Atari environments.
   - `==1.26.1` installs the specific PettingZoo version used by this guide.
   - `autorom` provides the command used to install the Atari ROM files.
   - The quotation marks prevent Zsh from interpreting the square brackets as a filename pattern.
   - AutoROM is installed in this step, but the ROM files will be installed in the next section.

4. Verify that PettingZoo and the Boxing environment can be imported:

   ```console
   python -c "import pettingzoo; from pettingzoo.atari import boxing_v2; print('PettingZoo version:', pettingzoo.__version__)"
   ```

   - `python -c` runs a short piece of Python code directly from Terminal.
   - `import pettingzoo` checks that the main package is installed.
   - `from pettingzoo.atari import boxing_v2` checks that the Boxing environment is available.
   - The final part prints the installed PettingZoo version.

   The expected output is:

   ```text
   PettingZoo version: 1.26.1
   ```

### If the Atari dependency cannot be installed

If `pip` reports that it cannot find a compatible version of `multi_agent_ale_py`, run:

```console
uname -m
python -c "import platform; print(platform.machine())"
```

Both commands should display:

```text
arm64
```

If either command displays `x86_64`, the terminal or Python installation is using Intel emulation. Return to Section 1. Do not use `pip` options that force an incompatible package installation.

If both commands display `arm64`, save the complete installation error for the course instructor. Package availability may have changed after this guide was written.

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
   - AutoROM installs the ROM files where PettingZoo's Atari dependency can locate them.

   The command should download and install several ROM files. Near the end of the output, you should see:

   ```text
   Done!
   ```

2. If Terminal reports `command not found: AutoROM`, run the module directly:

   ```console
   python -m AutoROM.AutoROM --accept-license
   ```

   This runs the same installed AutoROM program through the active Python interpreter.

3. Verify that PettingZoo can load the Boxing ROM:

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

   No game window appears during this test because rendering is not enabled. The purpose of the command is only to verify that the ROM can be found and loaded.

### If the Boxing ROM is not found

If the verification command reports that the Boxing ROM is not installed:

1. Confirm that AutoROM and the Atari dependency are installed in the active environment:

   ```console
   python -m pip show autorom multi-agent-ale-py
   ```

2. Run AutoROM again through the active Python interpreter:

   ```console
   python -m AutoROM.AutoROM --accept-license
   ```

3. Repeat the Boxing verification command.

If AutoROM reports a network or download error, check the internet connection and try again. Do not download ROM files from untrusted sources.

## 6. Set up the working directory and VS Code

The project files will be stored in the macOS user's home directory. Finder can access this directory, and VS Code can edit and run the files directly.

### Create the working directory

1. Create a directory for the project:

   ```console
   mkdir -p ~/pettingzoo-boxing
   ```

   - `mkdir` means “make directory.”
   - `-p` creates the directory if it does not already exist and prevents an error if it already exists.
   - `~` represents the current macOS user's home directory.
   - The project directory will be located at `/Users/your-username/pettingzoo-boxing`.

2. Move into the project directory:

   ```console
   cd ~/pettingzoo-boxing
   ```

3. Display the current directory:

   ```console
   pwd
   ```

   - `pwd` means “print working directory.”
   - It displays the full path of the directory currently open in Terminal.

   You should see output similar to:

   ```text
   /Users/your-username/pettingzoo-boxing
   ```

### Open the directory in Finder

4. From inside the project directory, run:

   ```console
   open .
   ```

   - `open` asks macOS to open a file or directory using its standard graphical application.
   - `.` represents the current directory.

   Finder should open the `pettingzoo-boxing` directory. Files can be copied into or out of this directory using the normal Finder interface.

### Install Visual Studio Code

5. Download the macOS version of Visual Studio Code from the [official Visual Studio Code website](https://code.visualstudio.com/).

6. Open the downloaded `.dmg` file.

7. Drag **Visual Studio Code.app** into the **Applications** folder.

8. Open Visual Studio Code from the Applications folder or Spotlight.

   Visual Studio Code supports Apple silicon. The Universal or Apple silicon build can be used. Do not intentionally run the application through Rosetta.

### Add the `code` command to Terminal

9. In Visual Studio Code, press `Command+Shift+P` to open the Command Palette.

10. Search for and select:

    ```text
    Shell Command: Install 'code' command in PATH
    ```

11. Return to Terminal and refresh Zsh's command lookup:

    ```console
    rehash
    ```

    - `rehash` makes the shell look again for newly installed commands.
    - This keeps the currently active Conda environment open.

12. Verify the command:

    ```console
    code --version
    ```

    If it displays a Visual Studio Code version, the command is ready.

### If the `code` command is not available

If `code --version` still reports `command not found`, close Terminal, open it again, and repeat the environment activation from Section 3. The project can also be opened without the command-line shortcut:

```console
cd ~/pettingzoo-boxing
open -a "Visual Studio Code" .
```

- `open -a` opens the specified macOS application.
- `.` asks it to open the current directory.

The official VS Code documentation also provides a manual `PATH` configuration method if needed.

### Find the Conda environment's Python path

13. Return to Terminal and move to the project directory:

    ```console
    cd ~/pettingzoo-boxing
    ```

14. Display the full path of the active Python interpreter:

    ```console
    python -c "import sys; print(sys.executable)"
    ```

    - `sys.executable` contains the full path of the Python interpreter running the command.
    - Because the `pettingzoo` environment is active, the path should point to the environment's copy of Python.

    The output should be similar to:

    ```text
    /Users/your-username/miniconda3/envs/pettingzoo/bin/python
    ```

    Copy or record the complete path. It will be used when configuring Visual Studio Code.

### Open the project in Visual Studio Code

15. Open the current directory in Visual Studio Code:

    ```console
    code .
    ```

    - `code` launches Visual Studio Code.
    - `.` tells Visual Studio Code to open the current directory.

    If the `code` command was not available, use the `open -a` command shown above.

### Configure Python in Visual Studio Code

16. Open the Extensions view by pressing `Command+Shift+X`.

17. Search for **Python** and install the extension published by Microsoft.

18. Press `Command+Shift+P` to open the Command Palette.

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
    - Press `Return`.

    The path should be similar to:

    ```text
    /Users/your-username/miniconda3/envs/pettingzoo/bin/python
    ```

    Use the exact path printed on the Mac rather than copying the example path.

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

4. Save the file by pressing `Command+S`.

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

5. Open the Visual Studio Code integrated terminal using **Terminal → New Terminal**.

6. Run:

   ```console
   python boxing_random.py
   ```

A Boxing window should open. Both the white and black boxers will move and punch randomly.

The window may initially appear behind Visual Studio Code. Check the Dock if it is not immediately visible.

When the game finishes, Terminal will display:

```text
The game has finished.
```

To stop the program before the game finishes, select the integrated terminal and press `Control+C`. Use the Control key, not the Command key.

### Troubleshoot a missing game window

If the program runs but no game window appears:

1. Stop the program with `Control+C`.

2. Close Visual Studio Code.

3. Open the macOS Terminal and run the program directly:

   ```console
   cd ~/pettingzoo-boxing
   python boxing_random.py
   ```

4. Verify that the Pygame rendering package is installed:

   ```console
   python -c "import pygame; print('Pygame version:', pygame.version.ver)"
   ```

5. Verify that Terminal and Python are both running natively:

   ```console
   uname -m
   python -c "import platform; print(platform.machine())"
   ```

   Both commands should display:

   ```text
   arm64
   ```

If a traceback appears, save the complete traceback for the course instructor. Because this guide has not been tested on a physical Mac, the exact error is important for improving the instructions.

## 8. References

This guide was prepared using the following official documentation:

- [Apple: Mac computers with Apple silicon](https://support.apple.com/116943)
- [Apple: Using Intel-based apps on a Mac with Apple silicon](https://support.apple.com/102527)
- [Anaconda: Install Miniconda using the macOS terminal](https://www.anaconda.com/docs/getting-started/miniconda/install/mac-cli-install)
- [Anaconda: Intel Mac package support deprecation](https://www.anaconda.com/blog/intel-mac-package-support-deprecation)
- [PettingZoo: Basic installation](https://pettingzoo.farama.org/main/content/basic_usage/)
- [PettingZoo: Atari environments](https://pettingzoo.farama.org/environments/atari/)
- [AutoROM repository](https://github.com/Farama-Foundation/AutoROM)
- [Visual Studio Code: Install on macOS](https://code.visualstudio.com/docs/setup/mac)
