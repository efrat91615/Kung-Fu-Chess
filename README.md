# Kung Fu Chess ♟️⚡

A real-time, simultaneous-move chess engine and WebSocket game server implemented in Python.

Unlike traditional turn-based chess, **Kung Fu Chess** allows both players to move their pieces continuously in real time. Each piece has a movement velocity and incurs a cooldown period after completing a move.

---

## 🌟 Key Features

- **Real-Time Physics & Engine**:
  - Independent piece movement speeds over continuous time.
  - Individual piece cooldown timers preventing instant spamming.
  - Real-time mid-air collisions, path obstruction locks, and airborne captures.
  - Standard & special chess rules (pawn double steps, en passant, promotion, castling, king capture end conditions).

- **Multiplayer WebSocket Server**:
  - Asynchronous network server built with Python `asyncio` and `websockets`.
  - Structured JSON message protocol for client actions.
  - Server-side authoritative player stats store (`PlayerStatsStore`).

- **Win-Rate Based Matchmaking Queue**:
  - Pairs queued players based on minimal win-rate difference.
  - Configurable skill-gap threshold (`MAX_WIN_RATE_GAP = 0.30`) to ensure fair matches.

- **Private Room Codes**:
  - Unique 6-character private room code generation (e.g. `KUNG42`) for custom unranked matches.

- **Multiple Interfaces**:
  - Graphical OpenCV UI (`main_gui.py`) with piece sprites, animations, and cooldown highlights.
  - CLI Text / Console interface (`main.py`).

---

## 🛠️ Installation

### Prerequisites
- Python 3.10 or higher.

### Setup Environment
```bash
git clone https://github.com/efrat91615/Kung-Fu-Chess.git
cd "Kung-Fu-Chess"

# Install required dependencies
pip install -r requirements.txt
```

---

## 🚀 Execution & Usage

### 1. Launch WebSocket Server
```bash
python run_server.py
```
Starts the async WebSocket server listening at `ws://127.0.0.1:8765`.

### 2. Launch Graphical OpenCV GUI
```bash
python main_gui.py
```
Opens the graphical game window for local real-time play.

### 3. Launch CLI Console Interface
```bash
python main.py
```

---

## 🧪 Running Automated Tests

Run the complete test suite (840+ unit and integration tests):

```bash
python -m pytest
```

---

## 📁 Repository Architecture

```text
Kung Fu Chess/
├── server/                     # Async WebSocket server, router, room manager & stats store
├── engine/                     # Real-time game engine, rules, board & snapshot generator
├── realtime/                   # Collision resolver & airborne capture handling
├── input/                      # Input board parsers & coordinate mappers
├── controllers/                # Interactive click controller
├── ui/                         # Observer event classes & OpenCV graphics renderer
├── tests/                      # Automated unit and integration test suite
├── main.py                     # CLI launcher
├── main_gui.py                 # Graphical GUI launcher
└── run_server.py               # WebSocket server launcher
```
