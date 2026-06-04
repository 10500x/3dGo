# 3DGo

3DGo is a Python and Panda3D-based project designed to fill the niche for players who want to experience the traditional game of Go (Weiqi) in 3D or experimental shapes beyond the classic 2D grid. Currently supports single-player only.

<p align="center">
  <img width="48%" alt="3DGo Gameplay 1" src="https://github.com/user-attachments/assets/87152088-4380-45a7-838f-125b616ab7a3" />
  <img width="50%" alt="3DGo Gameplay 2" src="https://github.com/user-attachments/assets/84db3f95-0ea8-466a-ba3a-1da0a8235206" />
</p>

> **Note on Development:** This game is fully playable but remains in active development. The codebase is AI-assisted ("vibe-coded") and heavily human-reviewed.

## Features

* **Board Generation:** Supports any 2D or 3D grid size as a rectangular prism.
* **Strict Weiqi (Go) Rule Enforcement:** 
  * Full 3D liberty checking and chain capture processing.
  * Virtual move simulation to prevent suicide plays.
  * Positional **Ko rule** detection implemented via cryptographic MD5 board state hashing.
* **Advanced 3D Visualization Tools:**
  * **Layer Peeling (Shrink View):** Isolate or shrink outer shell layers dynamically to access and review hidden coordinates inside dense 3D boards.
  * **Floor-by-Floor Navigation:** Seamlessly isolate and cycle through horizontal planes or display the entire architecture at once.
* **Professional Timing Systems:** Fully integrated game clocks supporting international tournament standards: **Absolute**, **Fischer increments**, and traditional **Byo-yomi** periods.
* **Flawless State Rewinding:** Infinite turn undo/rewind capabilities that accurately roll back captures, turn color, and score history without state corruption.
* **Dynamic Territory & Score Evaluation:** Built-in geometric flood-fill calculator that accurately counts captured stones, adjusts for custom **Komi**, and evaluates territory strictly bounded by a single color.
* **Robust Match Persistence:** Save and load system using reliable JSON serialization to store and reconstruct the complete match history seamlessly.
* **On-the-fly Customization:** Modify grid lines, background color, Komi, and time controls dynamically from the UI settings panel without resetting the environment. *(Note: Changing the board dimensions will reset the current match).*

## Installation

### Option 1: Pre-compiled Release (Recommended)
1. Navigate to the **Releases** tab on GitHub.
2. Download the package for your respective operating system.
3. Extract the files and run `3DGo.exe`.

### Option 2: Run from Source
**Prerequisites:**
* **Python 3.x**
* **Panda3d**
* **Tkinter** (Only required if running the 2D module. Built-in on Windows/macOS. For Linux/Arch, install via your package manager: e.g., `sudo pacman -S tk`).

**Setup:**
Clone the repository, navigate into the directory, and install the required 3D engine dependencies via `pip`:

```bash
git clone [https://github.com/10500x/3dGo.git](https://github.com/10500x/3dGo.git)
cd 3dGo
pip install panda3d

## Usage
For the 3d version, just change directory into the folder and write
```python
python main.py
```
## Keybinds
## Controls & Keybindings

### Camera & Navigation
* **`Space` / `Right Click` + Mouse Move:** Drag to rotate the 3D camera freely.
* **`Scroll Wheel`:** Zoom in or zoom out of the board.
* **`Middle Click (Scroll Click)`:** Click any node/stone to change the camera's center of focus (ideal for exploring inside large grids).
* **`Arrow Keys`:** Fine-tuned camera rotation (Left/Right/Up/Down).
* **`R`:** Reset camera center and focus directly back to the absolute middle of the grid.

### Gameplay Mechanics
* **`Left Click`:** Interact with a node to place a stone.
* **`Z`:** Pass the current turn.
* **`D`:** Undo / Rewind turn (infinite rollbacks for score, captures, and stone states).
* **`A`:** Manually evaluate and refresh territory calculations and capture scores.

### 3D Layer Tools
* **`E`:** Step one horizontal plane/floor up.
* **`Q`:** Step one horizontal plane/floor down.
* **`W`:** Restore visibility to show all overlapping 3D layers at once].
* **`S`:** Cut/Shrink outer layer shells sequentially to interact inside dense board volumes.

### Interface Panels
* **`X`:** Toggle the quick in-game keybindings overlay.
* **`C`:** Toggle the game configuration sidebar (Time controls, Komi adjustments, and colors).

### To-do
* Custom Grids: Support importing externally created grids (e.g., via CSV files) to enable complex, arbitrary shapes inside the game.
* Settings Menu: Add options for players to change stone models (e.g., switching to basic cubes for better performance) and adjust visual settings like grid anti-aliasing.
* Custom Adjacency Rules: Implement flexible adjacency logic (e.g., toroidal/wrap-around adjacency).

<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/10500x/3dGo">3dGo</a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://github.com/10500x">10500</a>, <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://github.com/Barrios-maker">Barrios-maker</a> is licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Creative Commons Attribution-NonCommercial 4.0 International<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1" alt=""></a></p>
