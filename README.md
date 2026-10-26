# Dungeon Conquest

A text-based dungeon battle game for the Data Structures Laboratory. It uses a
**queue** (Encounter Queue), a **stack** (Battle Action History) and a
**graph** (the dungeon map of rooms and passages).

## How to run

Requires Python 3.8 or newer. No extra packages are needed.

```bash
python3 DS_MidtermProject2_Transaction2_BariteJMercadoR.py
```

Run it from this folder so it uses the `.txt` record files here. If a file is
missing, the game recreates it with the default records.

## Default login

| Role  | Username | Password   |
|-------|----------|------------|
| Admin | `admin`  | `admin123` |

There are no player accounts at first. Players create their own account
with "Create New Account" on the login screen.

## Sections

- **Dashboard**: live totals for players, enemies, battles and boss progress.
- **Profiling**: add, view, search, update and delete players, enemies, items,
  rooms, passages and challenge questions.
- **Transactions**: the player's dungeon expedition (queue enemies, battle,
  shop, rest, escape) and the admin's game setup tools.
- **Report Generation**: nine reports, each exportable to the `reports/` folder.

## Data structures

| Structure | Where it is used | Operations |
|-----------|------------------|------------|
| Queue | Encounter Queue of enemies to fight | enqueue, dequeue, peek, display, empty check |
| Stack | Battle Action History | push, pop (remove latest log entry), peek, display, empty check |
| Graph | Dungeon map: rooms are vertices, passages are two-way edges | add/remove passage, BFS shortest route, DFS traversal, reachability |

## Record files

| File | Contents |
|------|----------|
| `player_accounts.txt` | accounts, stats, inventory, saved queue |
| `enemy_records.txt` | enemies and the room each one guards |
| `item_records.txt` | shop items and their effects |
| `room_records.txt` | dungeon rooms (graph vertices) |
| `room_connections.txt` | passages between rooms (graph edges) |
| `question_records.txt` | challenge questions |

The game also creates `battle_history_records.txt`,
`dungeon_game_records.txt` and `battle_activity_log.txt` while you play.
