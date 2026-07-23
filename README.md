# Connect Four - Usernames & Secret Powers Edition

Location: `~/projects/puzzles/connect_four.py`

## New Features

* **Custom Username Input**: Enter your custom username on the lobby screen before hosting or joining a match.
* **Secret Powers (Fog of War)**: Opponents' remaining special move charges are **HIDDEN 🔒** from your screen! You can only see your own remaining charges on your side panel.
* **4 Players**: 🔴 RED (P1), 🟡 YELLOW (P2), 🟢 GREEN (P3), 🟣 PURPLE (P4).
* **Wider 10x7 Grid**: 10 columns by 7 rows for tactical 4-player matches.
* **4 Discs Win Condition**: Connect **4 in a row** (horizontally, vertically, or diagonally) to claim victory.
* **Rotating Rematch Starters**: Every rematch automatically rotates who starts first (**Match 1**: RED -> **Match 2**: YELLOW -> **Match 3**: GREEN -> **Match 4**: PURPLE -> **Match 5**: RED...).
* **1 Special Move Charge Each**: 💣 `REMOVE DISC (x1)` and ⚡ `DOUBLE DROP (x1)`.
* **REMOVE DISC Improvements**: Removing an opponent's disc does not skip your turn—you drop your piece in the same turn.
* **4-Player Wi-Fi LAN & Offline Multiplayer**: Play over Wi-Fi network or locally on the same computer.

## How to Run

```bash
cd ~/projects/puzzles
python3 connect_four.py
```
