"""Connect Four Game in Python Arcade - 4-Player Edition with Usernames & Secret Powers.

Features:
- Mandatory Username Input: Each player enters a custom username before joining/hosting.
- Secret Powers / Fog of War: Other players' remaining special move charges are hidden from you!
- 4 Players: RED (P1), YELLOW (P2), GREEN (P3), PURPLE (P4).
- 10x7 Wider Strategic Board Grid.
- 4-in-a-Row Win Condition.
- Rotating Starting Player per Rematch.
- 1 Charge Per Special Move: 1 REMOVE DISC & 1 DOUBLE DROP.
- Single Special Move Per Turn Restriction.
- REMOVE DISC Turn Continuation.
- 4-Player Wi-Fi LAN & Local Pass & Play Modes.
"""

from enum import Enum, IntEnum
import json
import socket
import threading
from typing import Dict, List, Optional, Tuple
import arcade


class Player(IntEnum):
    """Enum representing the 4 players in Connect Four."""
    NONE = 0
    RED = 1
    YELLOW = 2
    GREEN = 3
    PURPLE = 4


class SpecialMode(Enum):
    """Enum for special ability targeting modes."""
    NONE = "NONE"
    REMOVE = "REMOVE"
    DOUBLE_DROP = "DOUBLE_DROP"


class GameState(Enum):
    """Enum for main window states."""
    LOBBY = "LOBBY"
    JOIN_INPUT = "JOIN_INPUT"
    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    PLAYING = "PLAYING"


def get_local_ip() -> str:
    """Retrieve the local Wi-Fi / LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class NetworkManager:
    """Manages TCP socket networking for 4-player Wi-Fi LAN multiplayer."""

    def __init__(self, message_callback):
        """Initialize NetworkManager."""
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[socket.socket] = []
        self.conn: Optional[socket.socket] = None
        self.is_host = False
        self.running = False
        self.message_callback = message_callback
        self.local_ip = get_local_ip()
        self.port = 8888

    def start_host(self) -> None:
        """Start TCP server thread to host a 4-player game."""
        self.is_host = True
        self.running = True
        self.clients.clear()
        thread = threading.Thread(target=self._host_thread, daemon=True)
        thread.start()

    def _host_thread(self) -> None:
        """Background thread listening for 3 client connections (4 players total)."""
        try:
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(3)

            while len(self.clients) < 3 and self.running:
                client_conn, _ = self.server_socket.accept()
                self.clients.append(client_conn)
                player_assigned = len(self.clients) + 1  # 2: YELLOW, 3: GREEN, 4: PURPLE

                init_msg = (
                    json.dumps({
                        "type": "ASSIGN_PLAYER",
                        "player": player_assigned
                    })
                    + "\n"
                )
                client_conn.sendall(init_msg.encode("utf-8"))

                t = threading.Thread(
                    target=self._listen_thread, args=(client_conn,), daemon=True
                )
                t.start()

                self.message_callback({
                    "type": "PLAYER_COUNT_UPDATE",
                    "count": len(self.clients) + 1
                })

        except Exception as e:
            print(f"Host error: {e}")

    def connect_to_host(self, host_ip: str) -> bool:
        """Connect to host IP in a background thread."""
        self.is_host = False
        self.running = True
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host_ip, self.port))
            self.conn = client
            thread = threading.Thread(
                target=self._listen_thread, args=(client,), daemon=True
            )
            thread.start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _listen_thread(self, sock: socket.socket) -> None:
        """Listen for incoming network messages and rebroadcast if host."""
        buffer = ""
        while self.running:
            try:
                data = sock.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        msg = json.loads(line.strip())

                        if self.is_host:
                            for c in list(self.clients):
                                if c != sock:
                                    try:
                                        payload = line.strip() + "\n"
                                        c.sendall(payload.encode("utf-8"))
                                    except Exception:
                                        pass

                        self.message_callback(msg)
            except Exception:
                break

    def send(self, data: dict) -> None:
        """Send JSON payload to connected peers."""
        payload = json.dumps(data) + "\n"
        if self.is_host:
            for c in list(self.clients):
                try:
                    c.sendall(payload.encode("utf-8"))
                except Exception:
                    pass
        elif self.conn:
            try:
                self.conn.sendall(payload.encode("utf-8"))
            except Exception:
                pass

    def close(self) -> None:
        """Close all sockets."""
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        for c in self.clients:
            try:
                c.close()
            except Exception:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


# Global configuration constants (Wider 10x7 Grid)
BOARD_ROWS = 7
BOARD_COLS = 10
CELL_SIZE = 70
MARGIN = 10
SIDE_PANEL_WIDTH = 270

WINDOW_WIDTH = (
    (BOARD_COLS * CELL_SIZE)
    + ((BOARD_COLS + 1) * MARGIN)
    + (MARGIN * 4)
    + SIDE_PANEL_WIDTH
)
WINDOW_HEIGHT = (
    ((BOARD_ROWS + 1) * CELL_SIZE)
    + ((BOARD_ROWS + 2) * MARGIN)
    + 100
)
WINDOW_TITLE = "Connect Four - Secret Powers & Usernames Edition"

COLOR_BG = (15, 23, 42)           # Dark slate background
COLOR_BOARD = (30, 58, 138)       # Deep navy blue board
COLOR_PANEL = (30, 41, 59)        # Side panel background
COLOR_SLOT_EMPTY = (15, 23, 42)   # Empty slot background
COLOR_RED = (239, 68, 68)         # Player 1 Vibrant Red
COLOR_YELLOW = (252, 211, 77)     # Player 2 Vibrant Yellow
COLOR_GREEN = (34, 197, 94)       # Player 3 Emerald Green
COLOR_PURPLE = (168, 85, 247)     # Player 4 Vibrant Purple
COLOR_WIN_LINE = (52, 211, 153)   # Mint green for winning highlight
COLOR_BTN = (51, 65, 85)          # Button default color
COLOR_BTN_ACTIVE = (16, 185, 129)  # Button active color
COLOR_BTN_DISABLED = (30, 41, 59)  # Disabled button color


def get_player_color(player: Player):
    """Return Arcade color tuple for given Player."""
    if player == Player.RED:
        return COLOR_RED
    elif player == Player.YELLOW:
        return COLOR_YELLOW
    elif player == Player.GREEN:
        return COLOR_GREEN
    elif player == Player.PURPLE:
        return COLOR_PURPLE
    return (148, 163, 184)


class Disc:
    """Represents a single Connect Four disc piece."""

    def __init__(
        self,
        row: int,
        col: int,
        player: Player,
        x: float,
        start_y: float,
        target_y: float
    ):
        """Initialize a new Disc instance."""
        self.row = row
        self.col = col
        self.player = player
        self.x = x
        self.y = start_y
        self.target_y = target_y
        self.falling = start_y != target_y
        self.drop_speed = 1600.0

    def update(self, delta_time: float) -> None:
        """Update disc position for falling animation."""
        if self.falling:
            if self.y > self.target_y:
                self.y -= self.drop_speed * delta_time
                if self.y <= self.target_y:
                    self.y = self.target_y
                    self.falling = False
            else:
                self.y += self.drop_speed * delta_time
                if self.y >= self.target_y:
                    self.y = self.target_y
                    self.falling = False

    def draw(self, radius: float) -> None:
        """Draw the disc on screen."""
        color = get_player_color(self.player)
        arcade.draw_circle_filled(self.x, self.y, radius, color)
        arcade.draw_circle_outline(
            self.x, self.y, radius - 2, (255, 255, 255, 60), 2
        )


class Board:
    """Manages the 4-player Connect Four game grid matrix and win detection logic."""

    def __init__(self, rows: int = BOARD_ROWS, cols: int = BOARD_COLS):
        """Initialize an empty game board."""
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Player]] = [
            [Player.NONE for _ in range(cols)] for _ in range(rows)
        ]
        self.discs: List[Disc] = []

    def reset(self) -> None:
        """Reset grid and clear all discs."""
        self.grid = [
            [Player.NONE for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.discs.clear()

    def is_valid_column(self, col: int) -> bool:
        """Check if column index is within bounds and not full."""
        if 0 <= col < self.cols:
            return self.grid[self.rows - 1][col] == Player.NONE
        return False

    def drop_disc(
        self, col: int, player: Player
    ) -> Optional[Tuple[int, int]]:
        """Find lowest available row in column and place disc."""
        for r in range(self.rows):
            if self.grid[r][col] == Player.NONE:
                self.grid[r][col] = player
                return (r, col)
        return None

    def remove_disc_at(
        self, row: int, col: int, get_cell_center_fn
    ) -> bool:
        """Remove a disc at (row, col) and apply gravity to discs above it."""
        if self.grid[row][col] == Player.NONE:
            return False

        self.grid[row][col] = Player.NONE
        self.discs = [
            d for d in self.discs if not (d.row == row and d.col == col)
        ]

        for r in range(row, self.rows - 1):
            self.grid[r][col] = self.grid[r + 1][col]
            self.grid[r + 1][col] = Player.NONE

        for disc in self.discs:
            if disc.col == col and disc.row > row:
                disc.row -= 1
                _, new_y = get_cell_center_fn(disc.row, col)
                disc.target_y = new_y
                disc.falling = True

        return True

    def is_full(self) -> bool:
        """Check if the entire board is full (draw condition)."""
        return all(
            self.grid[self.rows - 1][c] != Player.NONE
            for c in range(self.cols)
        )

    def check_win_at_coordinate(
        self, row: int, col: int
    ) -> Optional[List[Tuple[int, int]]]:
        """Check for 4-in-a-row by sampling coordinates around (row, col)."""
        player = self.grid[row][col]
        if player == Player.NONE:
            return None

        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Positive Diagonal
            (1, -1)   # Negative Diagonal
        ]

        for dr, dc in directions:
            winning_coords = [(row, col)]

            r, c = row + dr, col + dc
            while (
                0 <= r < self.rows
                and 0 <= c < self.cols
                and self.grid[r][c] == player
            ):
                winning_coords.append((r, c))
                r += dr
                c += dc

            r, c = row - dr, col - dc
            while (
                0 <= r < self.rows
                and 0 <= c < self.cols
                and self.grid[r][c] == player
            ):
                winning_coords.append((r, c))
                r -= dr
                c -= dc

            # Require 4 in a row to win!
            if len(winning_coords) >= 4:
                return winning_coords[:4]

        return None

    def check_all_wins(self) -> Optional[Tuple[Player, List[Tuple[int, int]]]]:
        """Scan entire grid to check if any player has formed 4-in-a-row."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != Player.NONE:
                    coords = self.check_win_at_coordinate(r, c)
                    if coords:
                        return (self.grid[r][c], coords)
        return None


class ConnectFourWindow(arcade.Window):
    """Main Arcade window for 4-player Connect Four visualization and interaction."""

    def __init__(self, fullscreen: bool = False):
        """Initialize window, game board, and UI state."""
        super().__init__(
            WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
            fullscreen=fullscreen, resizable=True
        )
        arcade.set_background_color(COLOR_BG)

        self.state = GameState.LOBBY
        self.net = NetworkManager(self.on_network_message)

        self.board = Board(BOARD_ROWS, BOARD_COLS)
        self.match_starter_player = Player.RED
        self.current_player = Player.RED
        self.my_player: Optional[Player] = None

        # Usernames & Input fields
        self.my_username = "Player1"
        self.active_input_field = "USERNAME"  # "USERNAME" or "IP"
        self.player_usernames: Dict[Player, str] = {
            Player.RED: "Player 1",
            Player.YELLOW: "Player 2",
            Player.GREEN: "Player 3",
            Player.PURPLE: "Player 4"
        }

        self.game_over = False
        self.winner: Optional[Player] = None
        self.winning_coords: Optional[List[Tuple[int, int]]] = None
        self.hover_col: Optional[int] = None
        self.hover_cell: Optional[Tuple[int, int]] = None

        self.input_ip = ""

        # Special moves charges per player (1 charge each)
        self.remove_charges: Dict[Player, int] = {
            Player.RED: 1,
            Player.YELLOW: 1,
            Player.GREEN: 1,
            Player.PURPLE: 1
        }
        self.double_drop_charges: Dict[Player, int] = {
            Player.RED: 1,
            Player.YELLOW: 1,
            Player.GREEN: 1,
            Player.PURPLE: 1
        }

        # Restrictions: One trick per turn & Remove Disc drop state
        self.active_special_mode = SpecialMode.NONE
        self.trick_used_this_turn = False
        self.removed_disc_this_turn = False
        self.double_drop_remaining = 0

    def get_display_name(self, player: Player) -> str:
        """Return formatted string display name (Username + Color) for player."""
        uname = self.player_usernames.get(player, f"Player {player.value}")
        if player == Player.RED:
            return f"{uname} (RED)"
        elif player == Player.YELLOW:
            return f"{uname} (YELLOW)"
        elif player == Player.GREEN:
            return f"{uname} (GREEN)"
        elif player == Player.PURPLE:
            return f"{uname} (PURPLE)"
        return uname

    def on_network_message(self, msg: dict) -> None:
        """Callback for handling incoming network messages."""
        msg_type = msg.get("type")

        if msg_type == "ASSIGN_PLAYER":
            self.my_player = Player(msg["player"])
            # Broadcast my username to peers
            self.net.send({
                "type": "USER_INFO",
                "player": self.my_player.value,
                "username": self.my_username
            })

        elif msg_type == "USER_INFO":
            p = Player(msg["player"])
            uname = msg["username"]
            self.player_usernames[p] = uname
            if self.net.is_host:
                # Host rebroadcasts all known usernames
                self.net.send({
                    "type": "SYNC_USERNAMES",
                    "usernames": {
                        k.value: v for k, v in self.player_usernames.items()
                    }
                })

        elif msg_type == "SYNC_USERNAMES":
            u_dict = msg["usernames"]
            for k_str, v_name in u_dict.items():
                self.player_usernames[Player(int(k_str))] = v_name

        elif msg_type == "PLAYER_COUNT_UPDATE":
            count = msg["count"]
            if count >= 4 and self.net.is_host:
                self.state = GameState.PLAYING
                self.net.send({"type": "START_GAME"})

        elif msg_type == "START_GAME":
            self.state = GameState.PLAYING

        elif msg_type == "DROP":
            if self.game_over:
                return
            col = msg["col"]
            player = Player(msg["player"])
            placed = self.board.drop_disc(col, player)
            if placed:
                row, col = placed
                target_x, target_y = self.get_cell_center(row, col)
                start_y = self.height - 20
                new_disc = Disc(
                    row, col, player, target_x, start_y, target_y
                )
                self.board.discs.append(new_disc)

                winning_line = self.board.check_win_at_coordinate(row, col)
                if winning_line:
                    self.game_over = True
                    self.winner = player
                    self.winning_coords = winning_line
                elif self.board.is_full():
                    self.game_over = True
                    self.winner = None
                else:
                    is_dd = msg.get("double_drop", False)
                    if not is_dd:
                        self.switch_turn()

        elif msg_type == "REMOVE":
            if self.game_over:
                return
            r = msg["row"]
            c = msg["col"]
            p = Player(msg["player"])
            removed = self.board.remove_disc_at(r, c, self.get_cell_center)
            if removed:
                self.remove_charges[p] -= 1
                win_info = self.board.check_all_wins()
                if win_info:
                    self.game_over = True
                    self.winner, self.winning_coords = win_info

        elif msg_type == "REQUEST_RESTART":
            if self.net.is_host:
                if self.match_starter_player == Player.RED:
                    next_s = Player.YELLOW
                elif self.match_starter_player == Player.YELLOW:
                    next_s = Player.GREEN
                elif self.match_starter_player == Player.GREEN:
                    next_s = Player.PURPLE
                else:
                    next_s = Player.RED
                self.restart_game(send_net=True, next_starter=next_s)

        elif msg_type == "RESTART":
            starter_val = msg.get("starter")
            next_p = Player(starter_val) if starter_val else Player.RED
            self.restart_game(send_net=False, next_starter=next_p)

    def get_content_layout(
        self
    ) -> Tuple[float, float, float, float, float, float]:
        """Calculate layout coordinates to center all game elements on screen."""
        board_w = (BOARD_COLS * CELL_SIZE) + ((BOARD_COLS + 1) * MARGIN)
        board_h = (BOARD_ROWS * CELL_SIZE) + ((BOARD_ROWS + 1) * MARGIN)
        total_w = board_w + (MARGIN * 2) + SIDE_PANEL_WIDTH

        start_x = (self.width - total_w) / 2
        start_y = (self.height - board_h) / 2 - 15

        board_cx = start_x + (board_w / 2)
        board_cy = start_y + (board_h / 2)
        panel_cx = start_x + board_w + (MARGIN * 2) + (SIDE_PANEL_WIDTH / 2)
        panel_cy = board_cy

        return (board_cx, board_cy, board_w, board_h, panel_cx, panel_cy)

    def get_cell_center(self, row: int, col: int) -> Tuple[float, float]:
        """Convert grid (row, col) coordinate to screen (x, y) pixels."""
        board_cx, board_cy, board_w, board_h, _, _ = self.get_content_layout()
        left_x = board_cx - (board_w / 2)
        bottom_y = board_cy - (board_h / 2)

        x = left_x + MARGIN + (CELL_SIZE / 2) + col * (CELL_SIZE + MARGIN)
        y = bottom_y + MARGIN + (CELL_SIZE / 2) + row * (CELL_SIZE + MARGIN)
        return (x, y)

    def get_col_from_x(self, x: float) -> Optional[int]:
        """Determine column index from mouse X screen coordinate."""
        for col in range(BOARD_COLS):
            col_x, _ = self.get_cell_center(0, col)
            if abs(x - col_x) <= (CELL_SIZE + MARGIN) / 2:
                return col
        return None

    def get_cell_from_mouse(
        self, x: float, y: float
    ) -> Optional[Tuple[int, int]]:
        """Determine (row, col) grid cell from mouse screen coordinates."""
        col = self.get_col_from_x(x)
        if col is None:
            return None

        radius = (CELL_SIZE / 2) - 5
        for r in range(BOARD_ROWS):
            _, cell_y = self.get_cell_center(r, col)
            if abs(y - cell_y) <= radius:
                return (r, col)
        return None

    def restart_game(
        self, send_net: bool = True, next_starter: Optional[Player] = None
    ) -> None:
        """Reset board and start a new game with rotating starting player."""
        self.board.reset()

        if next_starter is not None:
            self.match_starter_player = next_starter
        else:
            if self.match_starter_player == Player.RED:
                self.match_starter_player = Player.YELLOW
            elif self.match_starter_player == Player.YELLOW:
                self.match_starter_player = Player.GREEN
            elif self.match_starter_player == Player.GREEN:
                self.match_starter_player = Player.PURPLE
            else:
                self.match_starter_player = Player.RED

        self.current_player = self.match_starter_player
        self.game_over = False
        self.winner = None
        self.winning_coords = None
        self.remove_charges = {
            Player.RED: 1, Player.YELLOW: 1, Player.GREEN: 1, Player.PURPLE: 1
        }
        self.double_drop_charges = {
            Player.RED: 1, Player.YELLOW: 1, Player.GREEN: 1, Player.PURPLE: 1
        }
        self.active_special_mode = SpecialMode.NONE
        self.trick_used_this_turn = False
        self.removed_disc_this_turn = False
        self.double_drop_remaining = 0

        if send_net and self.net.running and self.net.is_host:
            self.net.send({
                "type": "RESTART",
                "starter": self.match_starter_player.value
            })

    def switch_turn(self) -> None:
        """Rotate turn sequentially across 4 players: RED -> YELLOW -> GREEN -> PURPLE."""
        if self.current_player == Player.RED:
            self.current_player = Player.YELLOW
        elif self.current_player == Player.YELLOW:
            self.current_player = Player.GREEN
        elif self.current_player == Player.GREEN:
            self.current_player = Player.PURPLE
        else:
            self.current_player = Player.RED

        self.active_special_mode = SpecialMode.NONE
        self.trick_used_this_turn = False
        self.removed_disc_this_turn = False
        self.double_drop_remaining = 0

    def on_draw(self) -> None:
        """Render lobby or playing board HUD with Secret Powers & Usernames."""
        self.clear()

        if self.state == GameState.LOBBY:
            self._draw_lobby()
            return
        elif self.state == GameState.WAITING_FOR_PLAYERS:
            self._draw_waiting()
            return
        elif self.state == GameState.JOIN_INPUT:
            self._draw_join_input()
            return

        board_cx, board_cy, board_w, board_h, panel_cx, panel_cy = (
            self.get_content_layout()
        )

        # 1. Draw Main Board Frame
        arcade.draw_rect_filled(
            arcade.rect.XYWH(board_cx, board_cy, board_w, board_h),
            COLOR_BOARD
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(board_cx, board_cy, board_w, board_h),
            (59, 130, 246), 3
        )

        # 2. Draw Slot Cutouts
        radius = (CELL_SIZE / 2) - 5
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                slot_x, slot_y = self.get_cell_center(r, c)
                arcade.draw_circle_filled(
                    slot_x, slot_y, radius, COLOR_SLOT_EMPTY
                )

        # 3. Draw Placed Discs
        for disc in self.board.discs:
            disc.draw(radius)

        # 4. Highlight Target Opponent Disc in REMOVE Mode
        if (
            self.active_special_mode == SpecialMode.REMOVE
            and self.hover_cell is not None
        ):
            hr, hc = self.hover_cell
            cell_player = self.board.grid[hr][hc]
            if cell_player != Player.NONE and cell_player != self.current_player:
                hx, hy = self.get_cell_center(hr, hc)
                arcade.draw_circle_outline(
                    hx, hy, radius + 2, (239, 68, 68), 4
                )
                arcade.draw_line(hx - 15, hy, hx + 15, hy, (239, 68, 68), 2)
                arcade.draw_line(hx, hy - 15, hx, hy + 15, (239, 68, 68), 2)

        # 5. Highlight Winning Coordinates
        if self.winning_coords:
            for r, c in self.winning_coords:
                win_x, win_y = self.get_cell_center(r, c)
                arcade.draw_circle_outline(
                    win_x, win_y, radius - 2, COLOR_WIN_LINE, 4
                )

        # 6. Draw Hover Disc Preview
        is_my_turn = (
            self.my_player is None or self.my_player == self.current_player
        )
        if (
            not self.game_over
            and is_my_turn
            and self.active_special_mode != SpecialMode.REMOVE
            and self.hover_col is not None
            and self.board.is_valid_column(self.hover_col)
        ):
            preview_x, _ = self.get_cell_center(0, self.hover_col)
            preview_y = board_cy + (board_h / 2) + (CELL_SIZE / 2)
            p_color = get_player_color(self.current_player)
            preview_color = (p_color[0], p_color[1], p_color[2], 160)
            arcade.draw_circle_filled(
                preview_x, preview_y, radius, preview_color
            )

        # 7. Draw Side Control Panel (FOG OF WAR / SECRET POWERS)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(panel_cx, panel_cy, SIDE_PANEL_WIDTH, board_h),
            COLOR_PANEL
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(panel_cx, panel_cy, SIDE_PANEL_WIDTH, board_h),
            (71, 85, 105), 2
        )

        arcade.draw_text(
            "SPECIAL MOVES",
            panel_cx, panel_cy + (board_h / 2) - 30,
            arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_line(
            panel_cx - (SIDE_PANEL_WIDTH / 2) + 15,
            panel_cy + (board_h / 2) - 45,
            panel_cx + (SIDE_PANEL_WIDTH / 2) - 15,
            panel_cy + (board_h / 2) - 45,
            (71, 85, 105), 1
        )

        p_name = self.get_display_name(self.current_player)
        p_col = get_player_color(self.current_player)
        arcade.draw_text(
            f"Turn: {p_name}",
            panel_cx, panel_cy + (board_h / 2) - 75,
            p_col, 10,
            anchor_x="center", anchor_y="center", bold=True
        )

        btn_w = SIDE_PANEL_WIDTH - 40
        btn_h = 50

        # Secret Powers / Fog of War Logic:
        # If in network mode and NOT your turn, opponents' remaining powers are hidden!
        target_view_player = (
            self.my_player if self.my_player is not None else self.current_player
        )
        is_viewing_own_powers = (target_view_player == self.current_player)

        rem_count = self.remove_charges[target_view_player]
        is_rem_active = (
            self.active_special_mode == SpecialMode.REMOVE and is_my_turn
        )
        rem_disabled = (
            self.trick_used_this_turn and not is_rem_active
        ) or (rem_count <= 0) or not is_my_turn

        bg1 = (
            COLOR_BTN_DISABLED
            if rem_disabled
            else COLOR_BTN_ACTIVE if is_rem_active else COLOR_BTN
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(panel_cx, panel_cy + 40, btn_w, btn_h), bg1
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(panel_cx, panel_cy + 40, btn_w, btn_h),
            (239, 68, 68) if is_rem_active else (100, 116, 139), 2
        )

        rem_label = f"1. REMOVE DISC (x{rem_count})"
        arcade.draw_text(
            rem_label,
            panel_cx, panel_cy + 40,
            arcade.color.WHITE if not rem_disabled else (100, 116, 139), 11,
            anchor_x="center", anchor_y="center", bold=True
        )

        dd_count = self.double_drop_charges[target_view_player]
        is_dd_active = (
            self.active_special_mode == SpecialMode.DOUBLE_DROP and is_my_turn
        )
        dd_disabled = (
            self.trick_used_this_turn and not is_dd_active
        ) or (dd_count <= 0) or self.removed_disc_this_turn or not is_my_turn

        bg2 = (
            COLOR_BTN_DISABLED
            if dd_disabled
            else COLOR_BTN_ACTIVE if is_dd_active else COLOR_BTN
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(panel_cx, panel_cy - 30, btn_w, btn_h), bg2
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(panel_cx, panel_cy - 30, btn_w, btn_h),
            (252, 211, 77) if is_dd_active else (100, 116, 139), 2
        )

        dd_label = f"2. DOUBLE DROP (x{dd_count})"
        arcade.draw_text(
            dd_label,
            panel_cx, panel_cy - 30,
            arcade.color.WHITE if not dd_disabled else (100, 116, 139), 11,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Status HUD Text
        if not is_my_turn:
            status_text = "OPPONENT TURN (POWERS HIDDEN 🔒)"
        elif self.active_special_mode == SpecialMode.REMOVE:
            status_text = "REMOVE MODE: Click opponent disc!"
        elif self.removed_disc_this_turn:
            status_text = "DISC REMOVED! Click column to drop piece."
        elif self.active_special_mode == SpecialMode.DOUBLE_DROP:
            status_text = (
                f"DOUBLE DROP: {self.double_drop_remaining} drop(s) left!"
            )
        else:
            status_text = "Connect 4 to Win! Click column to drop disc."

        arcade.draw_text(
            status_text,
            panel_cx, panel_cy - 110,
            (148, 163, 184), 9,
            anchor_x="center", anchor_y="center"
        )

        header_y = board_cy + (board_h / 2) + 30
        if self.game_over:
            if self.winner:
                winner_name = self.get_display_name(self.winner)
                winner_col = get_player_color(self.winner)
                arcade.draw_text(
                    f"VICTORY: {winner_name}!",
                    self.width / 2, header_y,
                    winner_col, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )
            else:
                arcade.draw_text(
                    "GAME OVER - STALEMATE DRAW!",
                    self.width / 2, header_y,
                    arcade.color.WHITE, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )
        else:
            turn_str = f"CONNECT 4 - TURN: {p_name}"
            if is_my_turn:
                turn_str += " (YOUR TURN!)"
            arcade.draw_text(
                turn_str,
                self.width / 2, header_y,
                p_col, 16,
                anchor_x="center", anchor_y="center", bold=True
            )

    def _draw_lobby(self) -> None:
        """Render 4-Player Network Lobby UI with Username Input."""
        cx = self.width / 2
        cy = self.height / 2

        arcade.draw_text(
            "CONNECT FOUR - USERNAME & SECRET POWERS",
            cx, cy + 180,
            arcade.color.WHITE, 18,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Your Local Wi-Fi IP: {self.net.local_ip}",
            cx, cy + 145,
            (52, 211, 153), 12,
            anchor_x="center", anchor_y="center"
        )

        # Username Input Field Box
        arcade.draw_text(
            "Enter Your Username:",
            cx - 180, cy + 95,
            (203, 213, 225), 11,
            anchor_x="left", anchor_y="center", bold=True
        )
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy + 65, 360, 40), (30, 41, 59)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy + 65, 360, 40), (59, 130, 246), 2
        )
        arcade.draw_text(
            self.my_username if self.my_username else "Type Username...",
            cx, cy + 65,
            arcade.color.WHITE if self.my_username else (100, 116, 139), 12,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Button 1: Host Game
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy + 5, 360, 45), COLOR_BTN
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy + 5, 360, 45), (59, 130, 246), 2
        )
        arcade.draw_text(
            "1. HOST 4-PLAYER GAME (Host = P1 RED)",
            cx, cy + 5,
            arcade.color.WHITE, 11,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Button 2: Join Game
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy - 55, 360, 45), COLOR_BTN
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy - 55, 360, 45), (252, 211, 77), 2
        )
        arcade.draw_text(
            "2. JOIN GAME (Client = P2, P3, or P4)",
            cx, cy - 55,
            arcade.color.WHITE, 11,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Button 3: Local Pass & Play
        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy - 115, 360, 45), COLOR_BTN
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy - 115, 360, 45), (148, 163, 184), 2
        )
        arcade.draw_text(
            "3. 4-PLAYER LOCAL PASS & PLAY (Offline)",
            cx, cy - 115,
            arcade.color.WHITE, 11,
            anchor_x="center", anchor_y="center", bold=True
        )

    def _draw_waiting(self) -> None:
        """Render Host Waiting Screen for 4 Players."""
        cx = self.width / 2
        cy = self.height / 2
        connected_count = len(self.net.clients) + 1

        arcade.draw_text(
            f"HOSTING 4-PLAYER MATCH ({self.my_username})",
            cx, cy + 80,
            arcade.color.WHITE, 17,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Players Connected: {connected_count} / 4",
            cx, cy + 35,
            (52, 211, 153), 15,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Tell friends to Join using IP:\n\n{self.net.local_ip}",
            cx, cy - 25,
            (252, 211, 77), 16,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            "Game will start automatically when all 4 players connect...",
            cx, cy - 100,
            (148, 163, 184), 11,
            anchor_x="center", anchor_y="center"
        )

    def _draw_join_input(self) -> None:
        """Render Join Game IP Input Screen."""
        cx = self.width / 2
        cy = self.height / 2

        arcade.draw_text(
            f"CONNECTING AS: {self.my_username}",
            cx, cy + 110,
            (52, 211, 153), 14,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            "ENTER HOST IP ADDRESS TO JOIN",
            cx, cy + 70,
            arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_rect_filled(
            arcade.rect.XYWH(cx, cy, 340, 50), (30, 41, 59)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(cx, cy, 340, 50), (59, 130, 246), 2
        )

        display_ip = (
            self.input_ip
            if self.input_ip
            else "Type IP (e.g. 192.168.1.15)..."
        )
        ip_col = arcade.color.WHITE if self.input_ip else (100, 116, 139)
        arcade.draw_text(
            display_ip,
            cx, cy,
            ip_col, 14,
            anchor_x="center", anchor_y="center"
        )

        arcade.draw_text(
            "Press ENTER to Connect | Press ESC to Cancel",
            cx, cy - 60,
            (148, 163, 184), 11,
            anchor_x="center", anchor_y="center"
        )

    def on_update(self, delta_time: float) -> None:
        """Update animations every frame."""
        for disc in self.board.discs:
            disc.update(delta_time)

    def on_mouse_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        """Track mouse coordinates for hover column and cell selection."""
        self.hover_col = self.get_col_from_x(x)
        self.hover_cell = self.get_cell_from_mouse(x, y)

    def on_mouse_press(
        self, x: float, y: float, button: int, modifiers: int
    ) -> None:
        """Handle player clicks in Lobby or Playing state."""
        cx = self.width / 2
        cy = self.height / 2

        if self.state == GameState.LOBBY:
            # Check Username Input Box click
            if abs(x - cx) <= 180 and abs(y - (cy + 65)) <= 20:
                self.active_input_field = "USERNAME"
                return

            # Button 1: HOST GAME
            if abs(x - cx) <= 180 and abs(y - (cy + 5)) <= 22:
                self.my_player = Player.RED
                self.player_usernames[Player.RED] = self.my_username
                self.net.start_host()
                self.state = GameState.WAITING_FOR_PLAYERS
                return

            # Button 2: JOIN GAME
            if abs(x - cx) <= 180 and abs(y - (cy - 55)) <= 22:
                self.active_input_field = "IP"
                self.state = GameState.JOIN_INPUT
                self.input_ip = ""
                return

            # Button 3: LOCAL PASS & PLAY
            if abs(x - cx) <= 180 and abs(y - (cy - 115)) <= 22:
                self.my_player = None
                self.player_usernames[Player.RED] = f"{self.my_username} (P1)"
                self.state = GameState.PLAYING
                return

        if self.state != GameState.PLAYING:
            return

        if self.game_over:
            if self.net.running:
                if self.net.is_host:
                    if self.match_starter_player == Player.RED:
                        next_s = Player.YELLOW
                    elif self.match_starter_player == Player.YELLOW:
                        next_s = Player.GREEN
                    elif self.match_starter_player == Player.GREEN:
                        next_s = Player.PURPLE
                    else:
                        next_s = Player.RED
                    self.restart_game(send_net=True, next_starter=next_s)
                else:
                    self.net.send({"type": "REQUEST_RESTART"})
            else:
                self.restart_game(send_net=False)
            return

        if any(disc.falling for disc in self.board.discs):
            return

        if self.my_player is not None and self.my_player != self.current_player:
            return

        _, _, _, _, panel_cx, panel_cy = self.get_content_layout()
        btn_w = SIDE_PANEL_WIDTH - 40
        btn_h = 50

        # Check Special Move 1 Button: REMOVE DISC
        btn1_y = panel_cy + 40
        if (
            abs(x - panel_cx) <= btn_w / 2
            and abs(y - btn1_y) <= btn_h / 2
        ):
            if (
                not self.trick_used_this_turn
                and self.remove_charges[self.current_player] > 0
            ):
                if self.active_special_mode == SpecialMode.REMOVE:
                    self.active_special_mode = SpecialMode.NONE
                else:
                    self.active_special_mode = SpecialMode.REMOVE
            return

        # Check Special Move 2 Button: DOUBLE DROP
        btn2_y = panel_cy - 30
        if (
            abs(x - panel_cx) <= btn_w / 2
            and abs(y - btn2_y) <= btn_h / 2
        ):
            if (
                not self.trick_used_this_turn
                and not self.removed_disc_this_turn
                and self.double_drop_charges[self.current_player] > 0
            ):
                if self.active_special_mode == SpecialMode.DOUBLE_DROP:
                    self.active_special_mode = SpecialMode.NONE
                    self.double_drop_remaining = 0
                else:
                    self.active_special_mode = SpecialMode.DOUBLE_DROP
                    self.double_drop_charges[self.current_player] -= 1
                    self.double_drop_remaining = 2
                    self.trick_used_this_turn = True
            return

        # Handle Action: REMOVE DISC MODE
        if self.active_special_mode == SpecialMode.REMOVE:
            cell = self.get_cell_from_mouse(x, y)
            if cell:
                r, c = cell
                cell_player = self.board.grid[r][c]
                if cell_player != Player.NONE and cell_player != self.current_player:
                    removed = self.board.remove_disc_at(
                        r, c, self.get_cell_center
                    )
                    if removed:
                        self.remove_charges[self.current_player] -= 1
                        self.active_special_mode = SpecialMode.NONE
                        self.trick_used_this_turn = True
                        self.removed_disc_this_turn = True

                        if self.net.running:
                            self.net.send({
                                "type": "REMOVE",
                                "row": r,
                                "col": c,
                                "player": self.current_player
                            })

                        win_info = self.board.check_all_wins()
                        if win_info:
                            self.game_over = True
                            self.winner, self.winning_coords = win_info
            return

        # Handle Action: STANDARD / DOUBLE DROP DISC PLACEMENT
        col = self.get_col_from_x(x)
        if col is not None and self.board.is_valid_column(col):
            placed = self.board.drop_disc(col, self.current_player)
            if placed:
                row, col = placed
                target_x, target_y = self.get_cell_center(row, col)
                start_y = self.height - 20

                new_disc = Disc(
                    row, col, self.current_player, target_x, start_y, target_y
                )
                self.board.discs.append(new_disc)

                is_dd = (self.active_special_mode == SpecialMode.DOUBLE_DROP)
                if self.net.running:
                    self.net.send({
                        "type": "DROP",
                        "col": col,
                        "player": self.current_player,
                        "double_drop": is_dd and (self.double_drop_remaining > 1)
                    })

                winning_line = self.board.check_win_at_coordinate(row, col)
                if winning_line:
                    self.game_over = True
                    self.winner = self.current_player
                    self.winning_coords = winning_line
                elif self.board.is_full():
                    self.game_over = True
                    self.winner = None
                else:
                    if is_dd:
                        self.double_drop_remaining -= 1
                        if self.double_drop_remaining <= 0:
                            self.switch_turn()
                    else:
                        self.switch_turn()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle keyboard input for IP typing, username, and shortcuts."""
        if self.state == GameState.JOIN_INPUT:
            if symbol == arcade.key.ENTER:
                if self.input_ip.strip():
                    connected = self.net.connect_to_host(self.input_ip.strip())
                    if connected:
                        self.state = GameState.PLAYING
            elif symbol == arcade.key.BACKSPACE:
                self.input_ip = self.input_ip[:-1]
            elif symbol == arcade.key.ESCAPE:
                self.state = GameState.LOBBY
            return

        if symbol == arcade.key.R:
            if self.net.running:
                if self.net.is_host:
                    if self.match_starter_player == Player.RED:
                        next_s = Player.YELLOW
                    elif self.match_starter_player == Player.YELLOW:
                        next_s = Player.GREEN
                    elif self.match_starter_player == Player.GREEN:
                        next_s = Player.PURPLE
                    else:
                        next_s = Player.RED
                    self.restart_game(send_net=True, next_starter=next_s)
                else:
                    self.net.send({"type": "REQUEST_RESTART"})
            else:
                self.restart_game(send_net=False)
        elif symbol == arcade.key.F:
            self.set_fullscreen(not self.fullscreen)
        elif symbol == arcade.key.Q:
            self.net.close()
            self.close()

    def on_text(self, text: str) -> None:
        """Capture text input for Username or Host IP address."""
        if self.state == GameState.LOBBY:
            if text in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ":
                if len(self.my_username) < 15:
                    self.my_username += text
        elif self.state == GameState.JOIN_INPUT:
            if text in "0123456789.":
                self.input_ip += text

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Handle Backspace for Username input in Lobby."""
        if self.state == GameState.LOBBY:
            if symbol == arcade.key.BACKSPACE:
                self.my_username = self.my_username[:-1]


def main():
    """Main execution entry point."""
    _window = ConnectFourWindow()  # noqa: F841
    arcade.run()


if __name__ == "__main__":
    main()
