import os
import math
import random
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

# File names used to save the game records
ACCOUNT_FILE = "player_accounts.txt"
ENEMY_FILE = "enemy_records.txt"
ITEM_FILE = "item_records.txt"
ROOM_FILE = "room_records.txt"
CONNECTION_FILE = "room_connections.txt"
QUESTION_FILE = "question_records.txt"
BATTLE_HISTORY_FILE = "battle_history_records.txt"
GAME_RECORD_FILE = "dungeon_game_records.txt"
BATTLE_LOG_FILE = "battle_activity_log.txt"
REPORT_FOLDER = "reports"

# ---------------------------------------------------------------
# GAME BALANCE
# These values were tuned with a simulation so that simply spamming
# Attack and potions usually fails, while planning purchases, resting,
# defending and timing items lets a careful player clear the dungeon.
# ---------------------------------------------------------------

# Stats given to every new (or reset) player
STARTING_STATS = {"hp": 100, "max_hp": 100, "atk": 14, "gold": 60}
STARTING_ITEMS = {"ITM-001": 2}

# Player attack rules
PLAYER_DAMAGE_SPREAD = 3
PLAYER_MISS_CHANCE = 7
PLAYER_CRIT_CHANCE = 12
PLAYER_CRIT_MULTIPLIER = 1.75

# Enemy attack rules
ENEMY_DAMAGE_SPREAD = 2
ENEMY_CRIT_CHANCE = {"Weak": 5, "Intermediate": 8, "Strong": 10, "Boss": 12}
ENEMY_CRIT_MULTIPLIER = 1.5
BOSS_ENRAGE_MULTIPLIER = 1.3

# Battle action rules
DEFEND_DAMAGE_TAKEN = 0.4
DEFEND_COUNTER_BONUS = 30
FLEE_CHANCE = 50
STUN_CHANCE = 75
BOOST_ATTACKS = 3

# Rewards for clearing a whole difficulty level
ATTACK_BONUS_PER_LEVEL = 5
MAX_HP_BONUS_PER_LEVEL = 20
LEVEL_COMPLETION_GOLD = {"Weak": 40, "Intermediate": 80, "Strong": 150}

# Camp and defeat rules
REST_COST = 40
REST_HEAL_PERCENT = 50
DEFEAT_GOLD_LOSS_PERCENT = 25
DEFEAT_REVIVE_PERCENT = 50
ENEMY_REGEN_PERCENT = 25
ESCAPE_SCORE_BONUS = 500

# The room every expedition starts from
ENTRANCE_ROOM_ID = "ROOM-000"

DIFFICULTY_ORDER = {"Weak": 1, "Intermediate": 2, "Strong": 3, "Boss": 4}
LEVEL_ORDER = ["Weak", "Intermediate", "Strong", "Boss"]
PLAYER_STATUSES = ["Active", "In Battle", "Defeated", "Escaped", "Victorious"]

# What each item effect does with its power value
ITEM_EFFECTS = {
    "heal": "Restores {power}% of Max HP",
    "boost": "+{power}% damage on your next 3 attacks",
    "stun": "75% chance the enemy loses its next {power} turns",
    "damage": "Deals {low}-{high} damage that never misses",
    "escape": "Guaranteed escape from the current battle"
}

# ---------------------------------------------------------------
# DEFAULT RECORDS (written to the text files on the first run)
# ---------------------------------------------------------------

DEFAULT_ACCOUNTS = [
    # username, password, role, hp, max_hp, atk, gold, score, wins, losses,
    # defeated ids, completed levels, inventory
    ("admin", "admin123", "Admin", 100, 100, 14, 0, 0, 0, 0, [], [], {})
]

DEFAULT_ENEMIES = [
    # id, name, type, max_hp, atk, gold, score, room
    ("ENM-001", "Gravefang Rat", "Weak", 55, 7, 25, 40, "ROOM-001"),
    ("ENM-002", "Hollowbone Goblin", "Weak", 70, 9, 30, 60, "ROOM-002"),
    ("ENM-003", "Ashen Ghoul", "Weak", 85, 11, 35, 80, "ROOM-003"),
    ("ENM-004", "Ironjaw Reaver", "Intermediate", 105, 12, 50, 100,
     "ROOM-004"),
    ("ENM-005", "Boneguard Executioner", "Intermediate", 120, 13, 60, 120,
     "ROOM-005"),
    ("ENM-006", "Hellchain Marauder", "Intermediate", 135, 14, 70, 140,
     "ROOM-006"),
    ("ENM-007", "Dreadfang Berserker", "Strong", 150, 16, 85, 180,
     "ROOM-007"),
    ("ENM-008", "Abyssal Death Knight", "Strong", 165, 17, 95, 200,
     "ROOM-008"),
    ("ENM-009", "Soulreaper Wraith", "Strong", 180, 18, 110, 220,
     "ROOM-009"),
    ("ENM-010", "Vharok, the World Eater", "Boss", 320, 22, 300, 600,
     "ROOM-010")
]

DEFAULT_ITEMS = [
    # id, name, effect, power, price, max carry, description
    ("ITM-001", "Health Potion", "heal", 35, 30, 5,
     "A bitter red brew that closes wounds."),
    ("ITM-002", "Strength Tonic", "boost", 50, 70, 3,
     "Fills your arms with burning strength."),
    ("ITM-003", "Paralysis Bomb", "stun", 2, 110, 2,
     "Releases a numbing cloud of spores."),
    ("ITM-004", "Poison Dagger", "damage", 35, 120, 2,
     "A throwing blade coated in venom."),
    ("ITM-005", "Smoke Bomb", "escape", 0, 40, 2,
     "A thick cloud that hides your retreat.")
]

DEFAULT_ROOMS = [
    ("ROOM-000", "Dungeon Entrance", "A cold stone gate where every expedition begins."),
    ("ROOM-001", "Rotting Sewers", "Knee-deep filth and the scratching of claws."),
    ("ROOM-002", "Forsaken Tunnel", "A collapsed mining tunnel littered with bones."),
    ("ROOM-003", "Burial Chambers", "Rows of opened coffins and drifting ash."),
    ("ROOM-004", "Bloodstone Hall", "Red crystals pulse inside the walls."),
    ("ROOM-005", "Execution Pit", "A sunken arena stained by old sentences."),
    ("ROOM-006", "Infernal Prison", "Burning cells that never cool down."),
    ("ROOM-007", "War-Torn Catacombs", "Broken shields of a forgotten army."),
    ("ROOM-008", "Black Iron Citadel", "A fortress forged from black iron."),
    ("ROOM-009", "Hall of Lost Souls", "Whispers of the fallen echo here."),
    ("ROOM-010", "Throne of Ruin", "The seat of the World Eater and the only exit.")
]

DEFAULT_CONNECTIONS = [
    # room a, room b, passage name (connections go both ways)
    ("ROOM-000", "ROOM-001", "Rusted Grate"),
    ("ROOM-000", "ROOM-002", "Collapsed Stairway"),
    ("ROOM-001", "ROOM-003", "Flooded Passage"),
    ("ROOM-002", "ROOM-003", "Bone-Lined Corridor"),
    ("ROOM-003", "ROOM-004", "Crimson Gate"),
    ("ROOM-003", "ROOM-005", "Hangman's Path"),
    ("ROOM-004", "ROOM-006", "Chain Bridge"),
    ("ROOM-005", "ROOM-006", "Cell Block Door"),
    ("ROOM-006", "ROOM-007", "Scorched Tunnel"),
    ("ROOM-006", "ROOM-008", "Iron Drawbridge"),
    ("ROOM-007", "ROOM-009", "Whispering Stair"),
    ("ROOM-008", "ROOM-009", "Shadow Archway"),
    ("ROOM-009", "ROOM-010", "Throne Gate")
]

DEFAULT_QUESTIONS = [
    # id, question, choices, correct choice number, bonus damage
    ("QST-001", "Which data structure follows First-In, First-Out (FIFO)?",
     ["Stack", "Queue", "Tree", "Graph"], 2, 15),
    ("QST-002", "Which data structure follows Last-In, First-Out (LIFO)?",
     ["Queue", "Array", "Stack", "Graph"], 3, 15),
    ("QST-003", "Which operation adds an item to the top of a stack?",
     ["Enqueue", "Push", "Pop", "Peek"], 2, 15),
    ("QST-004", "Which operation removes the front item of a queue?",
     ["Dequeue", "Push", "Pop", "Insert"], 1, 15),
    ("QST-005", "In a graph, what connects two vertices?",
     ["Node", "Root", "Edge", "Leaf"], 3, 20),
    ("QST-006", "Which traversal visits neighbors level by level?",
     ["Depth-First Search", "Breadth-First Search", "Inorder", "Postorder"],
     2, 20),
    ("QST-007", "What is the topmost node of a tree called?",
     ["Leaf", "Branch", "Root", "Edge"], 3, 15),
    ("QST-008", "Which operation views the front of a queue without removing it?",
     ["Peek", "Pop", "Dequeue", "Clear"], 1, 20)
]

# ---------------------------------------------------------------
# LIVE RECORDS
# ---------------------------------------------------------------

# Stores all registered accounts (players and admins)
account_records = {}

# Information of the player who is currently logged in
player = {}

# Enemy, item, room, connection and question records loaded from files
mob_list = []
item_records = {}
room_records = {}
room_connections = []
question_records = []

# QUEUE: enemies are added here in the order chosen by the player
encounter_lineup = []

# STACK: stores the actions that happen during battle (top = last item)
battle_history = []

# Stores the enemy currently being fought
current_enemy_id = None

# Gives each battle action its own ID
action_counter = 0

# Temporary battle effects
boost_turns_left = 0
boost_percent = 0
guard_bonus_ready = False
enemy_stunned_turns = 0
challenge_used = False
boss_enrage_announced = False
battle_turns = 0


# ---------------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------------

def header(txt):
    # Simple title for each screen
    print(f"\n{txt.upper()}")
    print("-" * 50)


def pause():
    input("\nPress Enter to continue...")


def print_menu_row(*options, width=26):
    # Prints menu options side by side in fixed-width columns
    print("".join(f"{option:<{width}}" for option in options).rstrip())


def is_number_text(text):
    # True for values such as 55, 55/100, +30 or 75%
    digits = text.replace("/", "").replace("%", "").replace("+", "")
    return digits.replace("-", "", 1).isdigit()


def table_lines(columns, rows, max_width=24):
    # Builds a bordered text table. Long values wrap onto extra lines,
    # "\n" starts a new line inside a cell, and number columns are
    # aligned to the right.
    rows = [[str(value) for value in row] for row in rows]

    widths = []
    numeric = []

    for index, title in enumerate(columns):
        values = [row[index] for row in rows]
        longest = max(
            [len(part) for value in values for part in value.split("\n")],
            default=0
        )
        widths.append(max(len(title), min(longest, max_width)))
        numeric.append(bool(values) and all(
            is_number_text(value) or value == "-" for value in values
        ))

    def wrap_cell(value, width):
        lines = []

        for part in value.split("\n"):
            lines += textwrap.wrap(part, width) or [""]

        return lines

    def text_row(cells):
        return "| " + " | ".join(cells) + " |"

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = [
        border,
        text_row(f"{title:<{w}}" for title, w in zip(columns, widths)),
        border.replace("-", "=")
    ]

    wrapped_rows = [
        [wrap_cell(value, w) for value, w in zip(row, widths)]
        for row in rows
    ]
    multi_line = any(len(cell) > 1 for row in wrapped_rows for cell in row)

    for number, cells in enumerate(wrapped_rows):
        height = max(len(cell) for cell in cells)

        for line in range(height):
            parts = []

            for cell, w, right in zip(cells, widths, numeric):
                text = cell[line] if line < len(cell) else ""
                parts.append(f"{text:>{w}}" if right else f"{text:<{w}}")

            lines.append(text_row(parts))

        # Rows that wrap get a divider so each record stays readable
        if multi_line and number + 1 < len(wrapped_rows):
            lines.append(border)

    lines.append(border)
    return lines


def print_table(columns, rows, max_width=24):
    for line in table_lines(columns, rows, max_width):
        print(line)


def clear_screen():
    # Clears the console so each menu starts on a fresh screen
    os.system("cls" if os.name == "nt" else "clear")


INVALID_CHOICE_TEXT = "Invalid menu option. Please enter a valid choice."


def invalid_choice():
    # The menu is shown again right away, so no Enter press is needed
    print(f"\n{INVALID_CHOICE_TEXT}")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ask_text(prompt, default=None, banned="|"):
    # Asks for text that must not be blank. During updates, pressing
    # Enter keeps the current value (the default).
    while True:
        value = input(prompt).strip()

        if not value and default is not None:
            return default

        if not value:
            print("Input must not be blank.")
            continue

        if any(ch in value for ch in banned):
            print(f"Input must not contain: {' '.join(banned)}")
            continue

        return value


def ask_int(prompt, minimum=0, maximum=None, default=None):
    # Asks for a whole number inside the allowed range
    while True:
        raw = input(prompt).strip()

        if not raw and default is not None:
            return default

        if not raw:
            print("Input must not be blank.")
            continue

        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if value < minimum:
            print(f"The value must be at least {minimum}.")
            continue

        if maximum is not None and value > maximum:
            print(f"The value must not be greater than {maximum}.")
            continue

        return value


def ask_yes_no(prompt):
    return input(prompt).strip().lower() in ("y", "yes")


def ask_option(title, options, default=None):
    # Lets the user pick one value from a numbered list
    print(title)

    for number, option in enumerate(options, 1):
        print(f"  [{number}] {option}")

    default_number = None

    if default in options:
        default_number = options.index(default) + 1

    suffix = f" [{default_number}]" if default_number else ""
    number = ask_int(
        f"Choose [1-{len(options)}]{suffix}: ",
        1,
        len(options),
        default_number
    )

    return options[number - 1]


def next_record_id(prefix, existing_ids, start=1):
    # Creates the next unique ID such as ENM-011
    highest = start - 1

    for record_id in existing_ids:
        if record_id.startswith(prefix + "-"):
            try:
                highest = max(highest, int(record_id.split("-")[1]))
            except (ValueError, IndexError):
                pass

    return f"{prefix}-{highest + 1:03d}"


def hp_bar(current, maximum, width=20):
    # Draws a small health bar for the battle screen
    if maximum <= 0:
        return "[" + " " * width + "]"

    filled = round(width * max(0, current) / maximum)
    return "[" + "#" * filled + "." * (width - filled) + "]"


# ---------------------------------------------------------------
# BATTLE ANIMATIONS
# Small text animations that make the battle screen feel alive.
# They are skipped when the output is not a real terminal.
# ---------------------------------------------------------------

ANIMATIONS_ON = sys.stdout.isatty()

if os.name == "nt":
    # Turns on colour codes in the Windows console
    os.system("")

COLORS = {
    "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
    "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
    "bold": "\033[1m", "reset": "\033[0m"
}


def hp_color(current, maximum):
    # Green when healthy, yellow when hurt, red when in danger
    percent = current * 100 // maximum if maximum > 0 else 0

    if percent > 60:
        return "green"
    return "yellow" if percent >= 30 else "red"


def color(text, name):
    if not ANIMATIONS_ON:
        return text
    return f"{COLORS[name]}{text}{COLORS['reset']}"


def wait(seconds):
    if ANIMATIONS_ON:
        time.sleep(seconds)


def draw_line(text):
    # Redraws the current console line in place
    sys.stdout.write("\r\033[K" + text)
    sys.stdout.flush()


def type_out(text, delay=0.02, name=None):
    # Prints text one letter at a time
    if not ANIMATIONS_ON:
        print(text)
        return

    for letter in text:
        sys.stdout.write(color(letter, name) if name else letter)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def animate_strike(attacker, target, missed=False, critical=False):
    # A projectile flies from the attacker to the target
    if not ANIMATIONS_ON:
        return

    gap = 24
    shot = "==>>" if critical else "-->"

    for step in range(0, gap - len(shot) + 1, 2):
        lane = " " * step + shot + " " * (gap - len(shot) - step)
        draw_line(f"  {attacker} {color(lane, 'yellow')} {target}")
        time.sleep(0.025)

    if missed:
        draw_line(f"  {attacker} {' ' * gap} {target}  "
                  + color("~ whoosh ~", "cyan"))
        time.sleep(0.35)
    else:
        burst = "*CRITICAL*" if critical else "*SLASH*"
        # The target flashes and shakes when it is hit
        for offset in (0, 2, 0, 2, 0):
            draw_line(f"  {attacker} {' ' * (gap + offset)} "
                      + color(f"{target} {burst}", "red"))
            time.sleep(0.07)
        time.sleep(0.15)

    draw_line("")


def animate_hp_change(label, before, after, maximum, width=20):
    # Drains (or refills) the health bar a little at a time
    if not ANIMATIONS_ON or before == after:
        return

    bar_color = "green" if after > before else "red"
    frames = 12

    for frame in range(1, frames + 1):
        value = round(before + (after - before) * frame / frames)
        draw_line(f"  {label}: "
                  + color(hp_bar(value, maximum, width), bar_color)
                  + f" {value}/{maximum} HP")
        time.sleep(0.04)

    print()


def animate_effect(text, name, symbol="*", frames=6):
    # Short sparkle used for potions, guards and status effects
    if not ANIMATIONS_ON:
        return

    for frame in range(frames):
        pad = symbol * (frame % 3 + 1)
        draw_line(color(f"  {pad} {text} {pad}", name))
        time.sleep(0.09)

    draw_line("")


def animate_battle_intro(mob):
    # "VS" splash shown when a battle starts
    if not ANIMATIONS_ON:
        return

    name = "PLAYER"
    for gap in range(30, 3, -3):
        draw_line(color(name, "cyan") + " " * gap
                  + color("VS", "bold") + " " * gap
                  + color(mob["name"].upper(), "red"))
        time.sleep(0.04)

    for _ in range(3):
        draw_line(color(f"{name}   >>  VS  <<   {mob['name'].upper()}",
                        "yellow"))
        time.sleep(0.12)
        draw_line(f"{name}   >>  VS  <<   {mob['name'].upper()}")
        time.sleep(0.12)

    print()


def animate_banner(text, name):
    # Big blinking banner for victory and defeat
    border = "+" + "-" * (len(text) + 6) + "+"
    middle = f"|   {text}   |"

    if ANIMATIONS_ON:
        for _ in range(3):
            draw_line(color(middle, name))
            time.sleep(0.15)
            draw_line(" " * len(middle))
            time.sleep(0.1)
        draw_line("")

    print(color(border, name))
    print(color(middle, name))
    print(color(border, name))


# ---------------------------------------------------------------
# FILE HANDLING
# ---------------------------------------------------------------

def read_record_rows(path):
    # Reads a "|" separated text file. Missing files return no rows.
    rows = []

    if not Path(path).exists():
        return rows

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                rows.append([part.strip() for part in line.split("|")])

    except OSError:
        print(f"\nThere was a problem reading {path}.")

    return rows


def write_record_rows(path, title, columns, rows):
    # Writes records into a "|" separated text file. The columns are
    # padded so the file reads like a table (spaces are ignored when
    # the file is loaded again).
    names = columns.split("|")
    texts = [[str(value) for value in row] for row in rows]
    widths = [
        max([len(name)] + [len(row[i]) for row in texts if i < len(row)])
        for i, name in enumerate(names)
    ]

    def padded(values):
        return " | ".join(
            value.ljust(widths[i]) if i < len(widths) else value
            for i, value in enumerate(values)
        ).rstrip()

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(f"# {title}\n")
            file.write(f"# {padded(names)}\n")

            for row in texts:
                file.write(f"  {padded(row)}\n")

        return True

    except OSError:
        print(f"\nUnable to save {path}.")
        return False


def inventory_to_text(inventory):
    return ",".join(
        f"{item_id}:{qty}"
        for item_id, qty in inventory.items()
        if qty > 0
    )


def inventory_from_text(text):
    inventory = {}

    for entry in text.split(","):
        if ":" not in entry:
            continue

        item_id, qty = entry.split(":", 1)

        try:
            qty = int(qty)
        except ValueError:
            continue

        if qty > 0:
            inventory[item_id.strip()] = qty

    return inventory


def id_list_from_text(text):
    return [x.strip() for x in text.split(",") if x.strip()]


# ----- Accounts -----

def new_account_data(player_id, password, role="Player"):
    # Creates an account using the starting player stats
    return {
        "id": player_id,
        "password": password,
        "role": role,
        "hp": STARTING_STATS["hp"],
        "max_hp": STARTING_STATS["max_hp"],
        "atk": STARTING_STATS["atk"],
        "gold": STARTING_STATS["gold"] if role == "Player" else 0,
        "score": 0,
        "wins": 0,
        "losses": 0,
        "status": "Active",
        "defeated_ids": [],
        "completed_levels": [],
        "inventory": dict(STARTING_ITEMS) if role == "Player" else {},
        "lineup": [],
        "wounds": {}
    }


def create_default_accounts():
    # Creates the first account file if none exists yet
    account_records.clear()
    player_number = 0

    for (username, password, role, hp, max_hp, atk, gold, score, wins,
         losses, defeated, completed, inventory) in DEFAULT_ACCOUNTS:

        if role == "Admin":
            player_id = "ADM-001"
        else:
            player_number += 1
            player_id = f"PLY-{player_number:03d}"

        data = new_account_data(player_id, password, role)
        data.update({
            "hp": hp, "max_hp": max_hp, "atk": atk, "gold": gold,
            "score": score, "wins": wins, "losses": losses,
            "defeated_ids": list(defeated),
            "completed_levels": list(completed),
            "inventory": dict(inventory)
        })
        account_records[username] = data

    save_all_accounts()


def parse_account_row(parts):
    # Current format with role, inventory and saved encounter queue
    return parts[0], {
        "id": parts[1],
        "password": parts[2],
        "role": parts[3] if parts[3] in ("Admin", "Player") else "Player",
        "hp": int(parts[4]),
        "max_hp": int(parts[5]),
        "atk": int(parts[6]),
        "gold": int(parts[7]),
        "score": int(parts[8]),
        "wins": int(parts[9]),
        "losses": int(parts[10]),
        "status": parts[11],
        "defeated_ids": id_list_from_text(parts[12]),
        "completed_levels": id_list_from_text(parts[13]),
        "inventory": inventory_from_text(parts[14]),
        "lineup": id_list_from_text(parts[15]) if len(parts) > 15 else [],
        "wounds": inventory_from_text(parts[16]) if len(parts) > 16 else {}
    }


def parse_legacy_account_row(parts):
    # Older save files stored items as four fixed columns
    data = new_account_data(parts[1], parts[2])
    data.update({
        "hp": int(parts[3]),
        "max_hp": int(parts[4]),
        "atk": int(parts[5]),
        "score": int(parts[10]),
        "gold": int(parts[11]),
        "wins": int(parts[12]),
        "losses": int(parts[13]),
        "status": parts[14],
        "defeated_ids": id_list_from_text(parts[15]),
        "completed_levels": (
            id_list_from_text(parts[16]) if len(parts) > 16 else []
        ),
        "inventory": {}
    })

    for column, item_id in zip(range(6, 10), DEFAULT_ITEMS):
        qty = int(parts[column])

        if qty > 0:
            data["inventory"][item_id[0]] = qty

    return parts[0], data


def load_accounts():
    # Loads all saved accounts from the text file
    account_records.clear()

    for parts in read_record_rows(ACCOUNT_FILE):
        try:
            # 18 columns: files saved while players had a current room
            if len(parts) in (15, 16, 17, 18) and not parts[3].isdigit():
                username, data = parse_account_row(parts)
            elif len(parts) in (16, 17):
                username, data = parse_legacy_account_row(parts)
            else:
                continue
        except (ValueError, IndexError):
            continue

        if username and username not in account_records:
            account_records[username] = data

    if not account_records:
        create_default_accounts()
        return

    # Older files have no admin, so the default admin is added
    if not any(d["role"] == "Admin" for d in account_records.values()):
        if "admin" not in account_records:
            account_records["admin"] = new_account_data(
                "ADM-001", "admin123", "Admin"
            )
            save_all_accounts()


def save_all_accounts():
    # Saves all registered accounts into the account file
    rows = []

    for username, data in account_records.items():
        rows.append([
            username, data["id"], data["password"], data["role"],
            data["hp"], data["max_hp"], data["atk"], data["gold"],
            data["score"], data["wins"], data["losses"], data["status"],
            ",".join(data.get("defeated_ids", [])),
            ",".join(data.get("completed_levels", [])),
            inventory_to_text(data.get("inventory", {})),
            ",".join(data.get("lineup", [])),
            inventory_to_text(data.get("wounds", {}))
        ])

    write_record_rows(
        ACCOUNT_FILE,
        "DUNGEON CONQUEST PLAYER ACCOUNTS",
        "username|player_id|password|role|hp|max_hp|atk|gold|score|wins|"
        "losses|status|defeated_enemy_ids|completed_levels|inventory|"
        "encounter_queue|wounded_enemy_hp",
        rows
    )


# ----- Enemies -----

def make_enemy(enemy_id, name, enemy_type, max_hp, atk, gold, score, room):
    return {
        "id": enemy_id,
        "name": name,
        "type": enemy_type,
        "max_hp": max_hp,
        "hp": max_hp,
        "atk": atk,
        "gold_reward": gold,
        "score_reward": score,
        "room": room,
        "defeated": False
    }


def load_enemies():
    mob_list.clear()

    for parts in read_record_rows(ENEMY_FILE):
        if len(parts) != 8 or parts[2] not in DIFFICULTY_ORDER:
            continue

        if get_enemy_by_id(parts[0]) is not None:
            continue

        try:
            mob_list.append(make_enemy(
                parts[0], parts[1], parts[2], int(parts[3]),
                int(parts[4]), int(parts[5]), int(parts[6]), parts[7]
            ))
        except ValueError:
            continue

    if not mob_list:
        for record in DEFAULT_ENEMIES:
            mob_list.append(make_enemy(*record))
        save_enemies()


def save_enemies():
    write_record_rows(
        ENEMY_FILE,
        "DUNGEON CONQUEST ENEMY RECORDS",
        "enemy_id|name|difficulty|max_hp|atk|gold_reward|score_reward|room_id",
        [
            [m["id"], m["name"], m["type"], m["max_hp"], m["atk"],
             m["gold_reward"], m["score_reward"], m["room"]]
            for m in mob_list
        ]
    )


# ----- Items -----

def load_items():
    item_records.clear()

    for parts in read_record_rows(ITEM_FILE):
        if len(parts) != 7 or parts[2] not in ITEM_EFFECTS:
            continue

        if parts[0] in item_records:
            continue

        try:
            item_records[parts[0]] = {
                "id": parts[0],
                "name": parts[1],
                "effect": parts[2],
                "power": int(parts[3]),
                "price": int(parts[4]),
                "max_carry": int(parts[5]),
                "description": parts[6]
            }
        except ValueError:
            continue

    if not item_records:
        for (item_id, name, effect, power, price, carry,
             description) in DEFAULT_ITEMS:
            item_records[item_id] = {
                "id": item_id, "name": name, "effect": effect,
                "power": power, "price": price, "max_carry": carry,
                "description": description
            }
        save_items()


def save_items():
    write_record_rows(
        ITEM_FILE,
        "DUNGEON CONQUEST ITEM RECORDS",
        "item_id|name|effect|power|price|max_carry|description",
        [
            [i["id"], i["name"], i["effect"], i["power"], i["price"],
             i["max_carry"], i["description"]]
            for i in item_records.values()
        ]
    )


# ----- Rooms and connections (graph) -----

def load_rooms():
    room_records.clear()

    for parts in read_record_rows(ROOM_FILE):
        if len(parts) != 3 or parts[0] in room_records:
            continue

        room_records[parts[0]] = {
            "id": parts[0], "name": parts[1], "description": parts[2]
        }

    if ENTRANCE_ROOM_ID not in room_records:
        room_records.clear()

        for room_id, name, description in DEFAULT_ROOMS:
            room_records[room_id] = {
                "id": room_id, "name": name, "description": description
            }
        save_rooms()


def save_rooms():
    write_record_rows(
        ROOM_FILE,
        "DUNGEON CONQUEST ROOM RECORDS (GRAPH VERTICES)",
        "room_id|name|description",
        [[r["id"], r["name"], r["description"]]
         for r in room_records.values()]
    )


def load_connections():
    room_connections.clear()
    file_existed = Path(CONNECTION_FILE).exists()

    for parts in read_record_rows(CONNECTION_FILE):
        if len(parts) != 3:
            continue

        # Only valid links between existing rooms are kept
        if validate_connection(parts[0], parts[1]) is None:
            room_connections.append(
                {"a": parts[0], "b": parts[1], "label": parts[2]}
            )

    if not file_existed:
        for room_a, room_b, label in DEFAULT_CONNECTIONS:
            if validate_connection(room_a, room_b) is None:
                room_connections.append(
                    {"a": room_a, "b": room_b, "label": label}
                )
        save_connections()


def save_connections():
    write_record_rows(
        CONNECTION_FILE,
        "DUNGEON CONQUEST ROOM CONNECTIONS (GRAPH EDGES, TWO-WAY)",
        "room_a|room_b|passage_name",
        [[c["a"], c["b"], c["label"]] for c in room_connections]
    )


# ----- Challenge questions -----

def load_questions():
    question_records.clear()

    for parts in read_record_rows(QUESTION_FILE):
        if len(parts) != 5:
            continue

        choices = [c.strip() for c in parts[2].split(";") if c.strip()]

        try:
            answer = int(parts[3])
            bonus = int(parts[4])
        except ValueError:
            continue

        if len(choices) < 2 or not 1 <= answer <= len(choices):
            continue

        if any(q["id"] == parts[0] for q in question_records):
            continue

        question_records.append({
            "id": parts[0], "question": parts[1], "choices": choices,
            "answer": answer, "bonus": bonus
        })

    if not question_records:
        for qid, question, choices, answer, bonus in DEFAULT_QUESTIONS:
            question_records.append({
                "id": qid, "question": question, "choices": list(choices),
                "answer": answer, "bonus": bonus
            })
        save_questions()


def save_questions():
    write_record_rows(
        QUESTION_FILE,
        "DUNGEON CONQUEST CHALLENGE QUESTIONS",
        "question_id|question|choices_separated_by_semicolon|"
        "correct_choice_number|bonus_damage",
        [[q["id"], q["question"], ";".join(q["choices"]), q["answer"],
          q["bonus"]] for q in question_records]
    )


# ----- Battle history (permanent record of every battle result) -----

def record_battle_result(mob, result, gold_change, score_change, turns=0):
    # Adds one line to the permanent battle history file. The whole file
    # is rewritten so every column stays lined up like a table.
    rows = [
        [r["date_time"], r["player_id"], r["username"], r["enemy_id"],
         r["enemy_name"], r["result"], r["turns"], r["gold"], r["score"]]
        for r in load_battle_results()
    ]
    rows.append([
        now_text(), player["id"], player["name"],
        mob["id"] if mob else "N/A",
        mob["name"] if mob else "Dungeon Exit",
        result, turns, gold_change, score_change
    ])

    write_record_rows(
        BATTLE_HISTORY_FILE,
        "DUNGEON CONQUEST BATTLE HISTORY",
        "date_time|player_id|username|enemy_id|enemy_name|result|turns|"
        "gold|score",
        rows
    )


def load_battle_results():
    results = []

    for parts in read_record_rows(BATTLE_HISTORY_FILE):
        if len(parts) != 9:
            continue

        results.append({
            "date_time": parts[0], "player_id": parts[1],
            "username": parts[2], "enemy_id": parts[3],
            "enemy_name": parts[4], "result": parts[5],
            "turns": parts[6], "gold": parts[7], "score": parts[8]
        })

    return results


def load_all_records():
    # Rooms load before connections so that links can be validated
    load_rooms()
    load_connections()
    load_items()
    load_enemies()
    load_questions()
    load_accounts()


# ---------------------------------------------------------------
# PLAYER SESSION
# ---------------------------------------------------------------

def get_enemy_by_id(enemy_id):
    # Finds an enemy using its ID
    for mob in mob_list:
        if mob["id"].upper() == enemy_id.upper():
            return mob
    return None


def get_current_enemy():
    # Gets the enemy currently being fought
    if current_enemy_id is None:
        return None
    return get_enemy_by_id(current_enemy_id)


def enemy_status(mob):
    return "Defeated" if mob["defeated"] else "Active"


def room_name(room_id):
    room = room_records.get(room_id)
    return room["name"] if room else f"Unknown Room ({room_id})"


def reset_battle_effects():
    # Clears every temporary battle effect
    global boost_turns_left, boost_percent, guard_bonus_ready
    global enemy_stunned_turns, challenge_used, boss_enrage_announced
    global battle_turns

    boost_turns_left = 0
    boost_percent = 0
    guard_bonus_ready = False
    enemy_stunned_turns = 0
    challenge_used = False
    boss_enrage_announced = False
    battle_turns = 0


def reset_session_state():
    # Clears temporary battle information when changing accounts
    global current_enemy_id, action_counter

    encounter_lineup.clear()
    battle_history.clear()
    current_enemy_id = None
    action_counter = 0
    reset_battle_effects()


def load_player_from_account(username):
    # Copies the selected account into the active player data
    data = account_records[username]

    player.clear()
    player.update({
        "id": data["id"],
        "name": username,
        "role": data["role"],
        "hp": data["hp"],
        "max_hp": data["max_hp"],
        "atk": data["atk"],
        "gold": data["gold"],
        "score": data["score"],
        "wins": data["wins"],
        "losses": data["losses"],
        "status": data["status"],
        "defeated_ids": list(data.get("defeated_ids", [])),
        "completed_levels": list(data.get("completed_levels", [])),
        "inventory": dict(data.get("inventory", {})),
        "wounds": dict(data.get("wounds", {}))
    })

    # A battle cannot continue after logging out
    if player["status"] == "In Battle":
        player["status"] = "Active"

    apply_player_enemy_progress()
    sync_completed_levels_without_rewards()
    restore_saved_lineup(data.get("lineup", []))


def restore_saved_lineup(saved_ids):
    # Rebuilds the saved Encounter Queue in the same FIFO order.
    # Enemies that were deleted, defeated or are no longer reachable
    # are skipped so the queue always follows the game rules.
    encounter_lineup.clear()
    skipped = []

    for enemy_id in saved_ids:
        mob = get_enemy_by_id(enemy_id)

        if (
            mob is None
            or mob["defeated"]
            or enemy_id in encounter_lineup
            or not can_player_select_enemy(mob)
            or not is_enemy_reachable(mob)
        ):
            skipped.append(enemy_id)
            continue

        encounter_lineup.append(mob["id"])

    return skipped


def save_current_player_account():
    # Updates the saved information of the current player
    username = player.get("name")

    if not username or username not in account_records:
        return

    record = account_records[username]

    for key in ("id", "hp", "max_hp", "atk", "gold", "score", "wins",
                "losses", "status"):
        record[key] = player[key]

    record["defeated_ids"] = list(player["defeated_ids"])
    record["completed_levels"] = list(player["completed_levels"])
    record["inventory"] = dict(player["inventory"])
    record["lineup"] = list(encounter_lineup)
    record["wounds"] = dict(player["wounds"])

    save_all_accounts()


def apply_player_enemy_progress():
    # Updates enemy status based on which enemies this player defeated.
    # Enemies that beat the player keep the wounds the player dealt.
    defeated = set(player.get("defeated_ids", []))
    wounds = player.get("wounds", {})

    for mob in mob_list:
        mob["defeated"] = mob["id"] in defeated

        if mob["defeated"]:
            mob["hp"] = 0
        else:
            mob["hp"] = min(mob["max_hp"], wounds.get(mob["id"], mob["max_hp"]))


def set_player_status(status):
    # A player who already escaped the dungeon keeps the Victorious status
    if player["status"] != "Victorious":
        player["status"] = status


def item_quantity(item_id):
    return player["inventory"].get(item_id, 0)


def change_item_quantity(item_id, amount):
    new_qty = item_quantity(item_id) + amount

    if new_qty > 0:
        player["inventory"][item_id] = new_qty
    else:
        player["inventory"].pop(item_id, None)


def describe_item_effect(item):
    text = ITEM_EFFECTS.get(item["effect"], "No effect")
    return text.format(
        power=item["power"],
        low=max(1, item["power"] - 5),
        high=item["power"] + 5
    )


# ---------------------------------------------------------------
# PROGRESSION (rank and level completion)
# ---------------------------------------------------------------

def get_rank_info(wins):
    # Wins determine which enemies the player can fight
    if wins >= 9:
        return {"rank": "Master", "max_difficulty": "Boss",
                "max_order": 4, "next_unlock": "All difficulties unlocked"}
    if wins >= 6:
        return {"rank": "Elite", "max_difficulty": "Strong",
                "max_order": 3, "next_unlock": "Boss unlocks at 9 wins"}
    if wins >= 3:
        return {"rank": "Adventurer", "max_difficulty": "Intermediate",
                "max_order": 2, "next_unlock": "Strong unlocks at 6 wins"}
    return {"rank": "Beginner", "max_difficulty": "Weak",
            "max_order": 1, "next_unlock": "Intermediate unlocks at 3 wins"}


def get_player_rank_info():
    return get_rank_info(player["wins"])


def get_unlocked_difficulties():
    # Creates a list of the difficulty levels currently available
    rank = get_player_rank_info()

    return ", ".join(
        difficulty
        for difficulty, order in DIFFICULTY_ORDER.items()
        if order <= rank["max_order"]
    )


def can_player_select_enemy(mob):
    # Stops the player from selecting an enemy above their rank
    return DIFFICULTY_ORDER[mob["type"]] <= get_player_rank_info()["max_order"]


def is_level_complete(difficulty):
    # Checks if all enemies from the level are defeated
    level_mobs = [mob for mob in mob_list if mob["type"] == difficulty]
    return bool(level_mobs) and all(mob["defeated"] for mob in level_mobs)


def sync_completed_levels_without_rewards():
    # Keeps old saved accounts from getting the same level bonus again
    for difficulty in LEVEL_ORDER:
        if (
            is_level_complete(difficulty)
            and difficulty not in player["completed_levels"]
        ):
            player["completed_levels"].append(difficulty)


def process_level_completion(difficulty, enemy):
    # Gives the level reward only once
    if difficulty in player["completed_levels"]:
        return None

    if not is_level_complete(difficulty):
        return None

    old_atk = player["atk"]
    old_max_hp = player["max_hp"]
    bonus_gold = LEVEL_COMPLETION_GOLD.get(difficulty, 0)

    player["completed_levels"].append(difficulty)
    player["atk"] += ATTACK_BONUS_PER_LEVEL
    player["max_hp"] += MAX_HP_BONUS_PER_LEVEL
    player["hp"] += MAX_HP_BONUS_PER_LEVEL
    player["gold"] += bonus_gold

    display_name = "Easy" if difficulty == "Weak" else difficulty

    description = (
        f"{display_name} level completed. Attack {old_atk} -> "
        f"{player['atk']}, Max HP {old_max_hp} -> {player['max_hp']}."
    )

    if bonus_gold:
        description += f" Level completion bonus: {bonus_gold} Gold."

    push_battle_action("Level Complete", description, enemy=enemy)

    return {
        "difficulty": display_name,
        "old_atk": old_atk,
        "new_atk": player["atk"],
        "old_max_hp": old_max_hp,
        "new_max_hp": player["max_hp"],
        "gold_bonus": bonus_gold
    }


def show_progress_summary():
    # Shows the player's current rank and progress
    rank = get_player_rank_info()

    print(f"Rank                 : {rank['rank']}")
    print(f"Total Wins           : {player['wins']}")
    print(f"Unlocked Difficulties: {get_unlocked_difficulties()}")
    print(f"Next Goal            : {rank['next_unlock']}")
    print(
        f"Completed Levels     : "
        f"{', '.join(player['completed_levels']) or 'None'}"
    )
    print(
        f"Level Clear Bonus    : +{ATTACK_BONUS_PER_LEVEL} ATK, "
        f"+{MAX_HP_BONUS_PER_LEVEL} Max HP"
    )


# ---------------------------------------------------------------
# DUNGEON MAP (GRAPH)
# Rooms are vertices and passages are two-way labelled edges.
# A room can be entered if it touches the entrance or a cleared room,
# so the player has to fight their way through the map.
# ---------------------------------------------------------------

def get_neighbors(room_id):
    # Returns every room connected to the given room
    neighbors = []

    for link in room_connections:
        if link["a"] == room_id:
            neighbors.append((link["b"], link["label"]))
        elif link["b"] == room_id:
            neighbors.append((link["a"], link["label"]))

    return sorted(neighbors)


def get_room_enemies(room_id):
    return [mob for mob in mob_list if mob["room"] == room_id]


def is_room_cleared(room_id, cleared_ids):
    # A room is cleared when every enemy inside it is in cleared_ids
    return all(mob["id"] in cleared_ids for mob in get_room_enemies(room_id))


def player_cleared_ids(include_lineup=True):
    # Enemies waiting in the queue count as "planned" clears, so the
    # player can line up a route through several rooms in advance
    ids = set(player.get("defeated_ids", []))

    if include_lineup:
        ids.update(encounter_lineup)

    return ids


def get_accessible_rooms(cleared_ids=None):
    # Breadth-first search from the entrance. The search only passes
    # through rooms that are already cleared.
    if cleared_ids is None:
        cleared_ids = player_cleared_ids()

    if ENTRANCE_ROOM_ID not in room_records:
        return set()

    visited = {ENTRANCE_ROOM_ID}
    frontier = [ENTRANCE_ROOM_ID]

    while frontier:
        room_id = frontier.pop(0)

        if (
            room_id != ENTRANCE_ROOM_ID
            and not is_room_cleared(room_id, cleared_ids)
        ):
            continue

        for neighbor, _ in get_neighbors(room_id):
            if neighbor not in visited and neighbor in room_records:
                visited.add(neighbor)
                frontier.append(neighbor)

    return visited


def is_enemy_reachable(mob, cleared_ids=None):
    return mob["room"] in get_accessible_rooms(cleared_ids)


def current_room_id():
    # Where the player is on the map: the room of the enemy being fought,
    # otherwise the room of the last enemy defeated, otherwise the entrance
    mob = get_current_enemy()

    if mob and mob["room"] in room_records:
        return mob["room"]

    for enemy_id in reversed(player.get("defeated_ids", [])):
        mob = get_enemy_by_id(enemy_id)

        if mob and mob["room"] in room_records:
            return mob["room"]

    return ENTRANCE_ROOM_ID


def get_room_status(room_id, defeated_ids, accessible):
    if room_id == ENTRANCE_ROOM_ID:
        return "Entrance"
    if room_id not in accessible:
        return "Locked"
    if get_room_enemies(room_id) and is_room_cleared(room_id, defeated_ids):
        return "Cleared"
    return "Open"


def find_route(start_id, target_id):
    # Breadth-first search for the shortest list of rooms between two rooms
    if start_id not in room_records or target_id not in room_records:
        return None

    parents = {start_id: (None, None)}
    frontier = [start_id]

    while frontier:
        room_id = frontier.pop(0)

        if room_id == target_id:
            break

        for neighbor, label in get_neighbors(room_id):
            if neighbor not in parents:
                parents[neighbor] = (room_id, label)
                frontier.append(neighbor)

    if target_id not in parents:
        return None

    route = []
    room_id = target_id

    while room_id is not None:
        parent, label = parents[room_id]
        route.append((room_id, label))
        room_id = parent

    route.reverse()
    return route


def depth_first_traversal(start_id):
    # Visits rooms by going as deep as possible before backtracking
    order = []
    visited = set()
    stack = [start_id]

    while stack:
        room_id = stack.pop()

        if room_id in visited or room_id not in room_records:
            continue

        visited.add(room_id)
        order.append(room_id)

        for neighbor, _ in reversed(get_neighbors(room_id)):
            if neighbor not in visited:
                stack.append(neighbor)

    return order


def dungeon_map_lines(defeated_ids, lineup_ids=()):
    # Builds the map display from the live room and enemy records
    cleared_ids = set(defeated_ids) | set(lineup_ids)
    accessible = get_accessible_rooms(cleared_ids)
    markers = {"Entrance": "E", "Locked": "L", "Cleared": "C", "Open": "O"}

    lines = ["Legend: [E] Entrance  [O] Open  [C] Cleared  [L] Locked", ""]

    for room_id, room in room_records.items():
        status = get_room_status(room_id, set(defeated_ids), accessible)
        lines.append(f"[{markers[status]}] {room_id} {room['name']} ({status})")

        for mob in get_room_enemies(room_id):
            if mob["id"] in defeated_ids:
                state = "Defeated"
            elif mob["id"] in lineup_ids:
                state = "In Queue"
            else:
                state = "Active"
            lines.append(
                f"      Enemy : {mob['id']} {mob['name']} "
                f"({mob['type']}, {state})"
            )

        neighbors = get_neighbors(room_id)

        if not neighbors:
            lines.append("      Links : none")

        for neighbor, label in neighbors:
            lines.append(
                f"      Link  : <-> {neighbor} {room_name(neighbor)} "
                f"via {label}"
            )

    return lines


# Size of the map drawing. Boxes shrink when a row holds many rooms.
MAP_MAX_WIDTH = 80
MAP_MAX_BOX_WIDTH = 31
MAP_BOX_GAP = 3


def get_room_levels():
    # Groups rooms by their distance (in steps) from the entrance using
    # breadth-first search. Each group becomes one row of the drawing.
    if ENTRANCE_ROOM_ID not in room_records:
        return []

    depth = {ENTRANCE_ROOM_ID: 0}
    frontier = [ENTRANCE_ROOM_ID]

    while frontier:
        room_id = frontier.pop(0)

        for neighbor, _ in get_neighbors(room_id):
            if neighbor not in depth and neighbor in room_records:
                depth[neighbor] = depth[room_id] + 1
                frontier.append(neighbor)

    levels = [[] for _ in range(max(depth.values()) + 1)]

    for room_id, level in depth.items():
        levels[level].append(room_id)

    # Orders each row under its parents to reduce crossing lines
    for number in range(1, len(levels)):
        above = levels[number - 1]

        def parent_position(room_id):
            parents = [
                above.index(n) for n, _ in get_neighbors(room_id) if n in above
            ]
            return (sum(parents) / len(parents) if parents else 0, room_id)

        levels[number].sort(key=parent_position)

    return levels


def room_box_lines(room_id, status, defeated_ids, lineup_ids, box_width,
                   here=False):
    # Builds the four text lines of one room box. The player's room is
    # drawn with a double border.
    markers = {"Entrance": "E", "Locked": "L", "Cleared": "C", "Open": "O"}
    inner = box_width - 4

    title = f"[{markers[status]}] {room_name(room_id)}"
    enemies = get_room_enemies(room_id)

    if not enemies:
        detail = "Start here" if room_id == ENTRANCE_ROOM_ID else "(empty)"
    else:
        mob = enemies[0]

        if mob["id"] in defeated_ids:
            tag = "x"
        elif mob["id"] in lineup_ids:
            tag = "Q"
        else:
            tag = mob["type"][0]

        extra = f" +{len(enemies) - 1}" if len(enemies) > 1 else ""
        detail = f"{mob['name'][:inner - 4 - len(extra)]}{extra} ({tag})"

    edge = "+" + ("=" if here else "-") * (box_width - 2) + "+"

    return [
        edge,
        f"| {title[:inner]:<{inner}} |",
        f"| {detail[:inner]:<{inner}} |",
        edge
    ]


def dungeon_drawing_lines(defeated_ids, lineup_ids=(), here=None):
    # Draws the dungeon graph as rows of room boxes joined by lines.
    # Everything is generated from the live room and passage records.
    levels = get_room_levels()

    if not levels:
        return ["The dungeon has no entrance."]

    cleared_ids = set(defeated_ids) | set(lineup_ids)
    accessible = get_accessible_rooms(cleared_ids)
    most_rooms = max(len(level) for level in levels)
    box_width = max(
        14, min(MAP_MAX_BOX_WIDTH, MAP_MAX_WIDTH // most_rooms - MAP_BOX_GAP)
    )
    step = box_width + MAP_BOX_GAP
    width = most_rooms * step

    # Works out the centre column of every room box
    centre = {}

    for level in levels:
        offset = (width - len(level) * step) // 2

        for index, room_id in enumerate(level):
            centre[room_id] = offset + index * step + step // 2

    lines = []
    drawn = set()

    for number, level in enumerate(levels):
        boxes = [
            room_box_lines(
                room_id,
                get_room_status(room_id, set(defeated_ids), accessible),
                defeated_ids,
                lineup_ids,
                box_width,
                room_id == here
            )
            for room_id in level
        ]

        for row in range(4):
            text = [" "] * width

            for room_id, box in zip(level, boxes):
                start = centre[room_id] - box_width // 2
                text[start:start + box_width] = box[row]

            lines.append("".join(text).rstrip())

        if number + 1 == len(levels):
            break

        # Two rows of / | \ lines towards the rooms in the next row
        links = [
            (room_id, neighbor)
            for room_id in level
            for neighbor, _ in get_neighbors(room_id)
            if neighbor in levels[number + 1]
        ]

        for row in (1, 2):
            text = [" "] * width

            for room_id, neighbor in links:
                start_x, end_x = centre[room_id], centre[neighbor]
                x = round(start_x + (end_x - start_x) * row / 3)

                if end_x == start_x:
                    text[x] = "|"
                else:
                    text[x] = "\\" if end_x > start_x else "/"

            lines.append("".join(text).rstrip())

        drawn.update(frozenset(link) for link in links)

    # Passages that do not go to the next row are listed underneath
    extra = [
        link for link in room_connections
        if frozenset((link["a"], link["b"])) not in drawn
    ]

    lines.append("")
    lines.append("Rooms  : [E] Entrance  [O] Open  [C] Cleared  [L] Locked")
    lines.append("Enemies: (W)eak (I)ntermediate (S)trong (B)oss "
                 "(Q) In Queue (x) Defeated")

    if here in room_records:
        lines.append(f"You    : +====+ box = you are here "
                     f"({room_name(here)})")

    if extra:
        lines.append("Other passages:")

        for link in extra:
            lines.append(f"  {room_name(link['a'])} <-> "
                         f"{room_name(link['b'])} via {link['label']}")

    unreachable = [r for r in room_records if r not in centre]

    if unreachable:
        lines.append("Rooms with no passage from the entrance: "
                     + ", ".join(room_name(r) for r in unreachable))

    return lines


def display_dungeon_map(pause_after=True):
    header("Dungeon Map (Graph)")

    for line in dungeon_drawing_lines(
        player["defeated_ids"], encounter_lineup, current_room_id()
    ):
        print(line)

    if pause_after:
        pause()


def display_room_details():
    header("Room Details and Passages")

    for line in dungeon_map_lines(player["defeated_ids"], encounter_lineup):
        print(line)

    pause()


def choose_room(prompt="Enter Room ID: ", allow_entrance=True):
    room_id = input(prompt).strip().upper()

    if not room_id:
        print("\nRoom ID must not be blank.")
        return None

    if room_id not in room_records:
        print("\nRoom record not found.")
        return None

    if not allow_entrance and room_id == ENTRANCE_ROOM_ID:
        print("\nThe Dungeon Entrance cannot be used here.")
        return None

    return room_id


def show_route_to_room():
    # Shortest path search (BFS) from the entrance to a chosen room
    header("Find Route to Room")

    for room_id, room in room_records.items():
        print(f"{room_id} | {room['name']}")

    target = choose_room("\nEnter destination Room ID: ")

    if target is None:
        pause()
        return

    route = find_route(ENTRANCE_ROOM_ID, target)

    if route is None:
        print("\nThere is no passage leading to that room.")
        pause()
        return

    accessible = get_accessible_rooms()

    print(f"\nShortest route to {room_name(target)} ({len(route) - 1} steps):")

    for step, (room_id, label) in enumerate(route):
        status = get_room_status(
            room_id, set(player["defeated_ids"]), accessible
        )
        via = f" via {label}" if label else ""
        enemies = ", ".join(m["name"] for m in get_room_enemies(room_id))
        guard = f" | Guarded by: {enemies}" if enemies else ""
        print(f"  {step}. {room_id} {room_name(room_id)}{via} "
              f"[{status}]{guard}")

    blocked = [
        room_id for room_id, _ in route[:-1]
        if room_id != ENTRANCE_ROOM_ID
        and not is_room_cleared(room_id, player_cleared_ids())
    ]

    if blocked:
        print("\nYou must clear these rooms first: "
              + ", ".join(room_name(r) for r in blocked))
    else:
        print("\nThe route is open.")

    pause()


def show_traversal():
    # Depth-first traversal of the whole dungeon from the entrance
    header("Dungeon Exploration Order (DFS)")

    order = depth_first_traversal(ENTRANCE_ROOM_ID)

    for step, room_id in enumerate(order, 1):
        print(f"{step:2}. {room_id} {room_name(room_id)}")

    unreachable = [r for r in room_records if r not in order]

    if unreachable:
        print("\nRooms with no path from the entrance: "
              + ", ".join(unreachable))

    pause()


def dungeon_map_menu():
    while True:
        header("Dungeon Map and Routes")
        print("[1] View Dungeon Map")
        print("[2] Room Details and Passages")
        print("[3] Find Route to a Room (BFS)")
        print("[4] Exploration Order (DFS Traversal)")
        print("[5] Back")

        choice = input("\nEnter choice [1-5]: ").strip()

        if choice == "1":
            display_dungeon_map()
        elif choice == "2":
            display_room_details()
        elif choice == "3":
            show_route_to_room()
        elif choice == "4":
            show_traversal()
        elif choice == "5":
            break
        else:
            invalid_choice()


# ---------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------

def register_new_account(username, password):
    # Creates a new player account using the starting player stats
    player_id = next_record_id(
        "PLY", [d["id"] for d in account_records.values()]
    )
    account_records[username] = new_account_data(player_id, password)
    save_all_accounts()


def login_screen():
    # Main screen before entering the game
    while True:
        header("Dungeon Conquest")

        print("[1] Login")
        print("[2] Create New Account")
        print("[3] Exit Game")

        choice = input("\nEnter choice [1-3]: ").strip()

        if choice == "1":
            username = input("Enter Username: ").strip()
            password = input("Enter Password: ").strip()

            if not username or not password:
                print("\nUsername and password must not be blank.")
                pause()
                continue

            if (
                username in account_records
                and account_records[username]["password"] == password
            ):
                # Clears the previous player's temporary battle data
                reset_session_state()
                load_player_from_account(username)

                print(f"\nWelcome back, {username}!")

                if player["role"] == "Admin":
                    print("Role: Administrator")
                    pause()
                    admin_menu()
                else:
                    print("Your saved progress has been loaded.")

                    if encounter_lineup:
                        print(
                            f"Your Encounter Queue was restored "
                            f"({len(encounter_lineup)} enemies waiting)."
                        )

                    pause()
                    open_adventure_menu()

            else:
                print("\nInvalid username or password.")

                if ask_yes_no(
                    "Would you like to create a new account? (Y/N): "
                ):
                    signup_screen()
                else:
                    print("\nReturning to the main menu.")
                    pause()

        elif choice == "2":
            signup_screen()

        elif choice == "3":
            print("\nThank you for playing Dungeon Conquest!")
            print("Goodbye.")
            break

        else:
            invalid_choice()


def signup_screen():
    # Creates a new player account after checking the input
    header("Create Account")

    username = input("Enter New Username: ").strip()

    if not username:
        print("\nUsername must not be blank.")
        pause()
        return

    if "|" in username or "," in username:
        print("\nUsername must not contain | or , characters.")
        pause()
        return

    if username in account_records:
        print("\nThat username already exists.")
        pause()
        return

    password = input("Enter New Password: ").strip()

    if not password:
        print("\nPassword must not be blank.")
        pause()
        return

    if "|" in password:
        print("\nPassword must not contain the | character.")
        pause()
        return

    register_new_account(username, password)

    print(f"\nAccount created successfully for {username}!")
    print(f"Your Player ID is {account_records[username]['id']}.")
    print("You can now log in using your new account.")

    pause()


# ---------------------------------------------------------------
# PLAYER MENU
# ---------------------------------------------------------------

def open_adventure_menu():
    # Main menu after a player logs in
    while True:
        header("Dungeon Conquest")

        rank = get_player_rank_info()

        print(f"Welcome, Warrior {player['name']}!")
        print(
            f"HP {player['hp']}/{player['max_hp']} | ATK {player['atk']} | "
            f"Gold {player['gold']} | Rank {rank['rank']} | "
            f"Status {player['status']}"
        )

        if encounter_lineup:
            print(f"Enemies waiting in your queue: {len(encounter_lineup)}")

        print("\n[1] Enter Dungeon")
        print("[2] View Player Statistics")
        print("[3] Dungeon Map and Routes")
        print("[4] Enemy Information")
        print("[5] How to Play")
        print("[6] Logout")

        choice = input("\nEnter choice [1-6]: ").strip()

        if choice == "1":
            dungeon_menu()
        elif choice == "2":
            view_stats()
        elif choice == "3":
            dungeon_map_menu()
        elif choice == "4":
            view_enemy_records()
        elif choice == "5":
            show_instructions()
        elif choice == "6":
            # Saves the player (including the queue) before logging out
            save_current_player_account()
            reset_session_state()

            print("\nYour progress has been saved.")
            print("Logging out...")
            break
        else:
            invalid_choice()


def view_stats(pause_after=True):
    # Shows the player's current information
    header("Player Statistics")

    print(f"Player ID         : {player['id']}")
    print(f"Player Name       : {player['name']}")
    print(f"Health Points     : {player['hp']}/{player['max_hp']}")
    print(f"Attack Power      : {player['atk']}")
    print(f"Current Score     : {player['score']}")
    print(f"Gold              : {player['gold']}")
    print(f"Wins              : {player['wins']}")
    print(f"Losses            : {player['losses']}")
    print(f"Status            : {player['status']}")

    print()
    show_progress_summary()
    print()
    view_inventory(pause_after=False, show_header=False)

    if pause_after:
        pause()


def view_inventory(pause_after=True, show_header=True):
    # Shows how many items the player currently has
    if show_header:
        header("Inventory")
    else:
        print("INVENTORY")

    rows = [
        [item["name"], f"{item_quantity(item_id)}/{item['max_carry']}",
         describe_item_effect(item)]
        for item_id, item in item_records.items()
        if item_quantity(item_id) > 0
    ]

    if rows:
        print_table(["Item", "Owned", "Effect"], rows, max_width=40)
    else:
        print("Your inventory is empty.")

    if pause_after:
        pause()


def view_enemy_records(pause_after=True, only_available=False):
    # Shows information about all enemies
    header("Enemy Information")

    rank = get_player_rank_info()
    accessible = get_accessible_rooms()

    print(f"Current Rank    : {rank['rank']}")
    print(f"Unlocked Levels : {get_unlocked_difficulties()}")
    print(f"Next Goal       : {rank['next_unlock']}")
    print()

    rows = []

    for mob in mob_list:
        # When choosing an enemy to queue, only show available choices
        if only_available and (
            mob["defeated"]
            or mob["id"] in encounter_lineup
            or not can_player_select_enemy(mob)
            or mob["room"] not in accessible
        ):
            continue

        if mob["defeated"]:
            status = "Defeated"
        elif mob["id"] in encounter_lineup:
            status = "In Queue"
        else:
            status = "Active"

        if not can_player_select_enemy(mob):
            access = "Rank locked"
        elif mob["room"] not in accessible:
            access = "Room locked"
        else:
            access = "Unlocked"

        rows.append([
            mob["id"], mob["name"], mob["type"],
            f"{mob['hp']}/{mob['max_hp']}", mob["atk"],
            f"{mob['gold_reward']}/{mob['score_reward']}",
            room_name(mob["room"]), status, access
        ])

    if rows:
        print_table(
            ["ID", "Name", "Difficulty", "HP", "ATK", "Gold/Score", "Room",
             "Status", "Access"],
            rows,
            max_width=18
        )
    else:
        print("No available enemies match your current progress.")

    if pause_after:
        pause()


def show_instructions():
    # Gives the player the basic rules of the game
    header("How to Play")

    print("GOAL")
    print("- Fight through the dungeon map, defeat the World Eater,")
    print("  then choose Escape the Dungeon to win the game.")

    print("\nPROGRESSION")
    print("- Beginner (0-2 wins): Weak enemies")
    print("- Adventurer (3-5 wins): Weak and Intermediate")
    print("- Elite (6-8 wins): Weak, Intermediate, and Strong")
    print("- Master (9+ wins): All enemies including the Boss")
    print(f"- Clearing a whole level gives +{ATTACK_BONUS_PER_LEVEL} ATK "
          f"and +{MAX_HP_BONUS_PER_LEVEL} Max HP")

    print("\nDUNGEON MAP")
    print("- Rooms connect through passages. You can only reach a room")
    print("  next to the entrance or next to a room you have cleared.")
    print("- Enemies in your queue count as planned clears, so you can")
    print("  plan a route several rooms ahead.")

    print("\nENCOUNTER QUEUE")
    print("- The first enemy added is the first one you face (FIFO).")
    print("- Your queue is saved when you leave the dungeon or log out.")

    print("\nBATTLE (every action uses your turn)")
    print("- Attack  : can miss or land a critical hit")
    print(f"- Defend  : take {int(DEFEND_DAMAGE_TAKEN * 100)}% damage, "
          f"next attack +{DEFEND_COUNTER_BONUS}%")
    print("- Items   : using an item also lets the enemy strike back")
    print("- Question: one per battle, correct = sure hit with bonus damage,")
    print("            wrong = you lose the turn")
    print(f"- Flee    : {FLEE_CHANCE}% chance, the enemy keeps full HP")
    print("- The Boss becomes ENRAGED below half health.")

    print("\nCAMP (between battles)")
    print("- HP does NOT refill after a battle.")
    print(f"- Rest at Camp heals {REST_HEAL_PERCENT}% Max HP "
          f"for {REST_COST} Gold.")
    print("- The Dungeon Shop sells items. Each item has a carry limit.")

    print("\nDEFEAT")
    print(f"- You lose {DEFEAT_GOLD_LOSS_PERCENT}% of your Gold, wake up "
          f"with {DEFEAT_REVIVE_PERCENT}% HP and your queue is cleared.")
    print(f"- The enemy keeps its wounds but regenerates "
          f"{ENEMY_REGEN_PERCENT}% of its Max HP.")
    print("- Fleeing lets the enemy recover completely.")

    print("\nITEMS")
    for item in item_records.values():
        print(f"- {item['name']} ({item['price']} Gold, carry "
              f"{item['max_carry']}): {describe_item_effect(item)}")

    pause()


# ---------------------------------------------------------------
# ENCOUNTER QUEUE (FIFO)
# ---------------------------------------------------------------

def display_encounter_lineup(pause_after=False):
    # Shows the enemies from front to rear
    header("Dungeon Encounter Queue")

    if not encounter_lineup:
        print("No enemy is available in the Encounter Queue.")
    else:
        print("FRONT")

        for position, enemy_id in enumerate(encounter_lineup, 1):
            mob = get_enemy_by_id(enemy_id)
            marker = " <- CURRENT BATTLE" if enemy_id == current_enemy_id else ""

            print(
                f"{position}. {mob['id']} | {mob['name']} | {mob['type']} | "
                f"HP {mob['hp']}/{mob['max_hp']}{marker}"
            )

        print("REAR")

    if pause_after:
        pause()


def lineup_line():
    # One-line view of the queue from front to rear
    if not encounter_lineup:
        return "(empty)"

    names = " -> ".join(get_enemy_by_id(e)["name"] for e in encounter_lineup)
    return f"FRONT [{names}] REAR"


def add_enemy_to_lineup():
    # ENQUEUE: lets the player choose an enemy for the expedition
    header("Add Enemy to Encounter Queue")

    view_enemy_records(pause_after=False, only_available=True)

    enemy_id = input("\nEnter Enemy ID: ").strip().upper()

    if not enemy_id:
        print("\nEnemy ID must not be blank.")
        pause()
        return

    mob = get_enemy_by_id(enemy_id)

    if mob is None:
        print("\nEnemy record not found.")
        pause()
        return

    if mob["defeated"]:
        print("\nEnemy has already been defeated and cannot be added "
              "to the Queue.")
        pause()
        return

    if mob["id"] in encounter_lineup:
        print("\nEnemy is already waiting in the Encounter Queue.")
        pause()
        return

    if not can_player_select_enemy(mob):
        rank = get_player_rank_info()

        print("\nThat enemy is still locked.")
        print(f"Your Rank: {rank['rank']}")
        print(f"Enemy Level: {mob['type']}")
        print(f"Next Goal: {rank['next_unlock']}")
        pause()
        return

    if not is_enemy_reachable(mob):
        print(f"\n{room_name(mob['room'])} cannot be reached yet.")
        print("Clear (or queue) an enemy in a connected room first.")
        print("Tip: use Dungeon Map and Routes to plan your path.")
        pause()
        return

    # Adds the selected enemy to the rear of the queue
    encounter_lineup.append(mob["id"])
    save_current_player_account()

    print("\nEnemy successfully added to the Dungeon Encounter Queue.")
    print(f"Enemy: {mob['name']} ({mob['type']})")

    display_encounter_lineup()
    pause()


def view_next_enemy():
    # PEEK: shows the next enemy without removing it from the queue
    header("Next Enemy Encounter")

    if not encounter_lineup:
        print("No enemy is available in the Encounter Queue.")
        pause()
        return

    mob = get_enemy_by_id(encounter_lineup[0])

    print(f"Next enemy: {mob['name']}.")
    print(f"Enemy ID     : {mob['id']}")
    print(f"Health       : {mob['hp']}/{mob['max_hp']}")
    print(f"Attack Power : {mob['atk']}")
    print(f"Difficulty   : {mob['type']}")
    print(f"Gold Reward  : {mob['gold_reward']}")
    print(f"Score Reward : {mob['score_reward']}")
    print(f"Room         : {room_name(mob['room'])}")

    if mob["type"] == "Boss":
        print("Warning      : becomes ENRAGED below half health!")

    pause()


def remove_front_enemy():
    # DEQUEUE: removes the enemy at the front after its battle ends
    if not encounter_lineup:
        return None

    return encounter_lineup.pop(0)


def revalidate_lineup():
    # After an escape, later queued enemies may no longer be reachable
    # because the escaped enemy's room is still not cleared
    planned = set(player["defeated_ids"])
    kept = []
    removed = []

    for enemy_id in encounter_lineup:
        mob = get_enemy_by_id(enemy_id)

        if mob is not None and is_enemy_reachable(mob, planned | set(kept)):
            kept.append(enemy_id)
        else:
            removed.append(enemy_id)

    encounter_lineup[:] = kept

    for enemy_id in removed:
        mob = get_enemy_by_id(enemy_id)
        name = mob["name"] if mob else enemy_id
        print(f"{name} left the queue because its room is unreachable.")


# ---------------------------------------------------------------
# BATTLE ACTION HISTORY (STACK, LIFO)
# ---------------------------------------------------------------

def push_battle_action(
    action_type,
    description,
    enemy=None,
    player_hp_before=None,
    player_hp_after=None,
    enemy_hp_before=None,
    enemy_hp_after=None
):
    # PUSH: saves one action on top of the battle history stack
    global action_counter

    action_counter += 1

    if enemy is None:
        enemy = get_current_enemy()

    action = {
        "action_id": f"ACT-{action_counter:03d}",
        "player_id": player["id"],
        "enemy_id": enemy["id"] if enemy else "N/A",
        "action_type": action_type,
        "description": description,
        "player_hp_before": (
            player["hp"] if player_hp_before is None else player_hp_before
        ),
        "player_hp_after": (
            player["hp"] if player_hp_after is None else player_hp_after
        ),
        "enemy_hp_before": (
            enemy["hp"] if enemy and enemy_hp_before is None
            else enemy_hp_before
        ),
        "enemy_hp_after": (
            enemy["hp"] if enemy and enemy_hp_after is None
            else enemy_hp_after
        ),
        "date_time": now_text()
    }

    battle_history.append(action)


def display_battle_history(pause_after=False, limit=None):
    # Shows the newest battle action first (top to bottom)
    header("Battle Action History Stack")

    if not battle_history:
        print("No battle actions have been recorded.")
    else:
        shown = list(reversed(battle_history))

        if limit is not None:
            shown = shown[:limit]

        print("TOP")

        for action in shown:
            print(f"{action['action_id']} | {action['action_type']} | "
                  f"{action['description']}")

        if limit is not None and len(battle_history) > limit:
            print(f"... {len(battle_history) - limit} older actions")

        print("BOTTOM")

    if pause_after:
        pause()


def view_latest_battle_action():
    # PEEK: shows the latest action without removing it
    header("Latest Battle Action")

    if not battle_history:
        print("No battle actions have been recorded.")
        pause()
        return

    action = battle_history[-1]

    print(f"Action ID : {action['action_id']}")
    print(f"Action    : {action['action_type']}")
    print(f"Details   : {action['description']}")
    print(f"Player HP : {action['player_hp_before']} -> "
          f"{action['player_hp_after']}")
    print(f"Enemy HP  : {action['enemy_hp_before']} -> "
          f"{action['enemy_hp_after']}")
    print(f"Time      : {action['date_time']}")

    pause()


def remove_latest_log_entry():
    # POP: removes only the latest entry from the battle history stack.
    # It edits the log only; HP, gold and enemies are not rolled back.
    header("Remove Latest Log Entry")

    print("This removes the newest entry from the Action History Stack.")
    print("It only edits the log. It does NOT undo the action itself:")
    print("your HP, gold and the enemy stay exactly as they are.\n")

    if not battle_history:
        print("The log is empty. There is nothing to remove.")
        pause()
        return

    latest = battle_history[-1]

    print("Latest Log Entry:")
    print(latest["description"])

    if not ask_yes_no("\nRemove this entry from the Stack? (Y/N): "):
        print("\nNothing was removed.")
        pause()
        return

    battle_history.pop()

    print("\nLatest log entry removed from the Stack.")
    print("Your actual game progress was not changed.")

    display_battle_history()
    pause()


def battle_log_menu():
    # Keeps all battle stack options inside one submenu
    while True:
        header("Battle Action History Stack")

        print("[1] View Battle Action History Stack")
        print("[2] View Latest Battle Action")
        print("[3] Remove Latest Log Entry (does not undo the action)")
        print("[4] Back")

        choice = input("\nEnter choice [1-4]: ").strip()

        if choice == "1":
            display_battle_history(pause_after=True)
        elif choice == "2":
            view_latest_battle_action()
        elif choice == "3":
            remove_latest_log_entry()
        elif choice == "4":
            break
        else:
            invalid_choice()


# ---------------------------------------------------------------
# BATTLE
# ---------------------------------------------------------------

def start_battle_with_next_enemy():
    # Starts a battle with the enemy at the front of the queue
    global current_enemy_id

    header("Start Battle with Next Enemy")

    if current_enemy_id is not None:
        print(f"You are already fighting {get_current_enemy()['name']}.")
        pause()
        return

    if not encounter_lineup:
        print("No enemy is available in the Encounter Queue.")
        pause()
        return

    if player["hp"] <= 0:
        print("Your health must be above 0. Rest at camp first.")
        pause()
        return

    display_encounter_lineup()

    mob = get_enemy_by_id(encounter_lineup[0])

    if mob is None or mob["defeated"]:
        remove_front_enemy()
        save_current_player_account()
        print("\nThe front enemy is no longer available and was removed.")
        pause()
        return

    if not confirm_risky_battle(mob):
        print("\nYou stay back. Rest at camp, buy potions or use the Shop "
              "first.")
        pause()
        return

    current_enemy_id = mob["id"]
    reset_battle_effects()
    set_player_status("In Battle")

    print()
    animate_battle_intro(mob)

    print(f"\nNext enemy: {mob['name']}.")
    print(f"Enemy HP     : {mob['hp']}/{mob['max_hp']}")
    print(f"Enemy Attack : {mob['atk']}")
    print(f"Difficulty   : {mob['type']}")
    print(f"Room         : {room_name(mob['room'])}")
    print(f"\nYour HP      : {player['hp']}/{player['max_hp']}")
    print(f"Your Attack  : {player['atk']}")

    push_battle_action(
        "Battle Start",
        f"Battle started with {mob['name']}.",
        enemy=mob
    )

    print("\nBattle started successfully.")
    pause()


def estimate_battle(mob):
    # Rough forecast if the player only attacks: how many attacks it
    # takes to win and how much damage the enemy deals meanwhile
    average_hit = (
        player["atk"]
        * (100 - PLAYER_MISS_CHANCE) / 100
        * (1 + PLAYER_CRIT_CHANCE / 100 * (PLAYER_CRIT_MULTIPLIER - 1))
    )
    attacks = max(1, math.ceil(mob["hp"] / max(1, average_hit)))
    enemy_hit = get_enemy_attack_power(mob)

    # The enemy does not strike back after the killing blow
    return attacks, enemy_hit, (attacks - 1) * enemy_hit


def confirm_risky_battle(mob):
    # Returns False if the player decides not to start a likely loss
    attacks, enemy_hit, damage = estimate_battle(mob)

    if damage < player["hp"]:
        return True

    print()
    print(color("WARNING: this fight looks dangerous.", "red"))
    print(f"  {mob['name']} hits for about {enemy_hit} per turn.")
    print(f"  You need about {attacks} attacks to win and would take "
          f"about {damage} damage.")
    print(f"  You have {player['hp']}/{player['max_hp']} HP.")
    print("  Defending, potions and items can still turn it around.")

    return ask_yes_no("\nFight anyway? (Y/N): ")


def validate_battle_action():
    # Returns the current enemy if the player can act, otherwise None
    mob = get_current_enemy()

    if mob is None:
        print("\nNo active battle is available.")
        pause()
        return None

    if player["hp"] <= 0:
        print("\nYou cannot act with 0 HP.")
        pause()
        return None

    return mob


def calculate_player_attack(sure_hit=False):
    # Calculates the damage for the player's attack
    global boost_turns_left, guard_bonus_ready

    multiplier = 1.0
    notes = []

    if boost_turns_left > 0:
        multiplier += boost_percent / 100
        boost_turns_left -= 1
        notes.append(f"Tonic +{boost_percent}%")

    if guard_bonus_ready:
        multiplier += DEFEND_COUNTER_BONUS / 100
        guard_bonus_ready = False
        notes.append(f"Counter +{DEFEND_COUNTER_BONUS}%")

    # Small chance for the player's attack to miss
    if not sure_hit and random.randint(1, 100) <= PLAYER_MISS_CHANCE:
        return 0, False, True, notes

    atk = player["atk"]
    strike = random.randint(
        max(1, atk - PLAYER_DAMAGE_SPREAD),
        atk + PLAYER_DAMAGE_SPREAD
    )
    strike = int(strike * multiplier)

    critical = random.randint(1, 100) <= PLAYER_CRIT_CHANCE

    if critical:
        strike = int(strike * PLAYER_CRIT_MULTIPLIER)

    return strike, critical, False, notes


def get_enemy_attack_power(mob):
    # The Boss hits harder once it drops below half health
    if mob["type"] == "Boss" and mob["hp"] <= mob["max_hp"] // 2:
        return int(mob["atk"] * BOSS_ENRAGE_MULTIPLIER)
    return mob["atk"]


def calculate_enemy_attack(mob, guarding=False):
    # Calculates the enemy's damage
    atk = get_enemy_attack_power(mob)

    damage = random.randint(
        max(1, atk - ENEMY_DAMAGE_SPREAD),
        atk + ENEMY_DAMAGE_SPREAD
    )

    critical = (
        random.randint(1, 100) <= ENEMY_CRIT_CHANCE.get(mob["type"], 5)
    )

    if critical:
        damage = int(damage * ENEMY_CRIT_MULTIPLIER)

    if guarding:
        damage = max(1, int(damage * DEFEND_DAMAGE_TAKEN))

    return damage, critical


def process_enemy_counterattack(mob, guarding=False):
    # The enemy attacks after every player action unless it is stunned
    global enemy_stunned_turns, boss_enrage_announced

    if enemy_stunned_turns > 0:
        enemy_stunned_turns -= 1

        print()
        animate_effect(f"{mob['name']} twitches... zzzt!", "yellow", "~")
        print(f"{mob['name']} is paralyzed and cannot attack!")

        push_battle_action(
            "Paralysis",
            f"{mob['name']} was paralyzed and lost its turn.",
            enemy=mob
        )
        return

    if (
        mob["type"] == "Boss"
        and mob["hp"] <= mob["max_hp"] // 2
        and not boss_enrage_announced
    ):
        boss_enrage_announced = True
        print()
        animate_effect(f"{mob['name']} ROARS", "red", "!", frames=9)
        print(color(f"{mob['name']} becomes ENRAGED! "
                    "Its attacks grow stronger.", "red"))
        push_battle_action(
            "Enrage", f"{mob['name']} became enraged.", enemy=mob
        )

    hp_before = player["hp"]
    damage, critical = calculate_enemy_attack(mob, guarding)

    player["hp"] = max(0, player["hp"] - damage)

    print()
    wait(0.3)
    animate_strike(mob["name"], "Player", critical=critical)

    if guarding:
        animate_effect("CLANG! Your guard holds", "blue", "#", frames=4)

    animate_hp_change("PLAYER", hp_before, player["hp"], player["max_hp"])

    if critical:
        print(color(f"Critical hit from {mob['name']}!", "red"))

    guard_text = " (blocked by your guard)" if guarding else ""

    print(f"{mob['name']} attacked Player for {damage} damage{guard_text}. "
          f"Player HP: {player['hp']}/{player['max_hp']}")

    push_battle_action(
        "Enemy Attack",
        f"{mob['name']} attacked Player for {damage} damage{guard_text}.",
        enemy=mob,
        player_hp_before=hp_before,
        player_hp_after=player["hp"],
        enemy_hp_before=mob["hp"],
        enemy_hp_after=mob["hp"]
    )

    print("Enemy attack recorded in the Battle Action History Stack.")

    if player["hp"] <= 0:
        resolve_player_defeat(mob)


def finish_player_turn(mob, guarding=False):
    # After every player action the enemy either falls or strikes back
    if mob["hp"] <= 0:
        resolve_enemy_victory(mob)
    else:
        process_enemy_counterattack(mob, guarding)

    save_current_player_account()
    pause()


def attack_current_enemy():
    # Handles one complete attack turn
    global battle_turns

    mob = validate_battle_action()

    if mob is None:
        return

    battle_turns += 1
    enemy_hp_before = mob["hp"]
    print()

    strike, critical, missed, notes = calculate_player_attack()
    bonus_text = f" ({', '.join(notes)})" if notes else ""

    animate_strike("Player", mob["name"], missed, critical)

    if missed:
        print(f"You attacked {mob['name']} but missed!")
        description = f"Player attacked {mob['name']} but missed."
    else:
        mob["hp"] = max(0, mob["hp"] - strike)

        animate_hp_change("ENEMY ", enemy_hp_before, mob["hp"], mob["max_hp"])

        crit_text = color("CRITICAL! ", "yellow") if critical else ""

        print(f"{crit_text}Player attacked {mob['name']} for {strike} damage"
              f"{bonus_text}. {mob['name']} HP: {mob['hp']}/{mob['max_hp']}")
        description = (
            f"Player attacked {mob['name']} for {strike} damage"
            f"{' (critical)' if critical else ''}."
        )

    push_battle_action(
        "Attack",
        description,
        enemy=mob,
        enemy_hp_before=enemy_hp_before,
        enemy_hp_after=mob["hp"]
    )

    print("Player attack recorded in the Battle Action History Stack.")

    finish_player_turn(mob)


def defend_against_enemy():
    # Raises the guard: less damage now, stronger counterattack next
    global battle_turns, guard_bonus_ready

    mob = validate_battle_action()

    if mob is None:
        return

    battle_turns += 1
    guard_bonus_ready = True

    print()
    animate_effect("[ ] You raise your shield [ ]", "blue", "#")
    print(f"You raise your guard. Next attack +{DEFEND_COUNTER_BONUS}% damage.")

    push_battle_action(
        "Defend",
        f"Player defended against {mob['name']}.",
        enemy=mob
    )

    finish_player_turn(mob, guarding=True)


def use_health_potion():
    # Uses the first healing item the player owns
    mob = validate_battle_action()

    if mob is None:
        return

    for item_id, item in item_records.items():
        if item["effect"] == "heal" and item_quantity(item_id) > 0:
            apply_item_effect(item, mob)
            return

    print("\nInsufficient potion quantity. No potion is available.")
    print("Buy Health Potions at the Dungeon Shop between battles.")
    pause()


def use_item():
    # Lets the player choose any item from the inventory
    mob = validate_battle_action()

    if mob is None:
        return

    while True:
        header("Use Item")

        owned = [
            item_id for item_id in item_records
            if item_quantity(item_id) > 0
        ]

        if not owned:
            print("Your inventory is empty.")
            print("Buy items at the Dungeon Shop between battles.")
            pause()
            return

        for number, item_id in enumerate(owned, 1):
            item = item_records[item_id]
            print(f"[{number}] {item['name']} x{item_quantity(item_id)} - "
                  f"{describe_item_effect(item)}")

        print("[0] Back")

        choice = input(f"\nChoose an item [0-{len(owned)}]: ").strip()

        if choice == "0":
            return

        if not choice.isdigit() or not 1 <= int(choice) <= len(owned):
            invalid_choice()
            continue

        # One item per turn, so the menu closes after a successful use
        if apply_item_effect(item_records[owned[int(choice) - 1]], mob):
            return


def apply_item_effect(item, mob):
    # Applies one item. Returns True if the player's turn was used.
    global battle_turns, boost_turns_left, boost_percent
    global enemy_stunned_turns

    effect = item["effect"]

    if effect == "heal" and player["hp"] >= player["max_hp"]:
        print("\nYour HP is already full.")
        pause()
        return False

    if effect == "boost" and boost_turns_left > 0:
        print(f"\nA tonic is still active ({boost_turns_left} attacks left).")
        pause()
        return False

    if effect == "stun" and enemy_stunned_turns > 0:
        print(f"\n{mob['name']} is already paralyzed.")
        pause()
        return False

    battle_turns += 1
    change_item_quantity(item["id"], -1)
    remaining = item_quantity(item["id"])

    print()

    if effect == "heal":
        hp_before = player["hp"]
        heal = max(1, player["max_hp"] * item["power"] // 100)
        player["hp"] = min(player["max_hp"], player["hp"] + heal)

        animate_effect("glug glug... healing light", "green", "+")
        animate_hp_change("PLAYER", hp_before, player["hp"], player["max_hp"])

        print("Potion used successfully. Player health has been restored.")
        print(f"HP: {hp_before} -> {player['hp']} | "
              f"{item['name']} left: {remaining}")

        push_battle_action(
            "Potion Use",
            f"Player used one {item['name']} and restored "
            f"{player['hp'] - hp_before} HP.",
            enemy=mob,
            player_hp_before=hp_before,
            player_hp_after=player["hp"]
        )

    elif effect == "boost":
        boost_turns_left = BOOST_ATTACKS
        boost_percent = item["power"]

        animate_effect("Power surges through you", "magenta", "^")
        print(f"{item['name']} used! Next {BOOST_ATTACKS} attacks "
              f"+{boost_percent}% damage. ({remaining} left)")

        push_battle_action(
            "Item Use",
            f"Player used {item['name']} (+{boost_percent}% damage).",
            enemy=mob
        )

    elif effect == "stun":
        animate_strike("Player", mob["name"])

        if random.randint(1, 100) <= STUN_CHANCE:
            animate_effect("zzzt! ZZZT!", "yellow", "~")
            enemy_stunned_turns = item["power"]
            message = (
                f"{mob['name']} was paralyzed for {item['power']} turns."
            )
            print(f"Success! {message}")
        else:
            message = f"{item['name']} failed against {mob['name']}."
            print(f"{mob['name']} resisted the {item['name']}!")

        print(f"({remaining} {item['name']} left)")
        push_battle_action("Item Use", message, enemy=mob)

    elif effect == "damage":
        enemy_hp_before = mob["hp"]
        damage = random.randint(max(1, item["power"] - 5), item["power"] + 5)
        mob["hp"] = max(0, mob["hp"] - damage)

        animate_strike("Player", mob["name"], critical=True)
        animate_effect("BOOM!", "red", "*")
        animate_hp_change("ENEMY ", enemy_hp_before, mob["hp"], mob["max_hp"])

        print(f"{item['name']} dealt {damage} damage! "
              f"{mob['name']} HP: {mob['hp']}/{mob['max_hp']} "
              f"({remaining} left)")

        push_battle_action(
            "Item Use",
            f"Player dealt {damage} damage to {mob['name']} "
            f"using {item['name']}.",
            enemy=mob,
            enemy_hp_before=enemy_hp_before,
            enemy_hp_after=mob["hp"]
        )

    elif effect == "escape":
        animate_effect("poof! smoke everywhere", "cyan", "~")
        print(f"You throw the {item['name']} and slip away!")
        resolve_escape(mob, item["name"])
        save_current_player_account()
        pause()
        return True

    finish_player_turn(mob)
    return True


def answer_challenge_question():
    # Once per battle: a correct answer is a sure hit with bonus damage
    global battle_turns, challenge_used

    mob = validate_battle_action()

    if mob is None:
        return

    if challenge_used:
        print("You already answered a challenge in this battle.")
        pause()
        return

    if not question_records:
        print("There are no challenge questions available.")
        pause()
        return

    question = random.choice(question_records)
    correct_text = question["choices"][question["answer"] - 1]

    # The choices are shuffled so players cannot memorise the numbers
    choices = list(question["choices"])
    random.shuffle(choices)

    print(f"\nCHALLENGE: {question['question']}")

    for number, choice in enumerate(choices, 1):
        print(f"  [{number}] {choice}")

    picked = ask_int(f"\nYour answer [1-{len(choices)}]: ", 1, len(choices))

    battle_turns += 1
    challenge_used = True

    if choices[picked - 1] == correct_text:
        enemy_hp_before = mob["hp"]
        strike, critical, _, _ = calculate_player_attack(sure_hit=True)
        strike += question["bonus"]
        mob["hp"] = max(0, mob["hp"] - strike)

        print()
        animate_effect("Correct! Knowledge is power", "green", "?")
        animate_strike("Player", mob["name"], critical=True)
        animate_hp_change("ENEMY ", enemy_hp_before, mob["hp"], mob["max_hp"])

        crit_text = " CRITICAL!" if critical else ""

        print(f"Correct!{crit_text} Player attacked {mob['name']} for "
              f"{strike} damage (+{question['bonus']} bonus). "
              f"{mob['name']} HP: {mob['hp']}/{mob['max_hp']}")

        push_battle_action(
            "Challenge",
            f"Player answered {question['id']} correctly and dealt "
            f"{strike} damage to {mob['name']}.",
            enemy=mob,
            enemy_hp_before=enemy_hp_before,
            enemy_hp_after=mob["hp"]
        )
    else:
        print(f"\nWrong! The answer was {correct_text}. You lose your turn.")

        push_battle_action(
            "Challenge",
            f"Player answered {question['id']} incorrectly.",
            enemy=mob
        )

    finish_player_turn(mob)


def attempt_flee():
    # Tries to run away. A failed attempt gives the enemy a free attack.
    global battle_turns

    mob = validate_battle_action()

    if mob is None:
        return

    if mob["type"] == "Boss":
        print("\nThe throne room doors are sealed. You cannot flee the Boss!")
        pause()
        return

    battle_turns += 1

    print()
    animate_effect("You make a run for it", "cyan", ">", frames=5)

    if random.randint(1, 100) <= FLEE_CHANCE:
        print("You escaped from the battle!")
        resolve_escape(mob, "running away")
        save_current_player_account()
        pause()
        return

    print(f"{mob['name']} blocks your escape!")
    push_battle_action(
        "Escape Failed",
        f"Player failed to escape from {mob['name']}.",
        enemy=mob
    )

    finish_player_turn(mob)


def end_current_battle():
    global current_enemy_id

    current_enemy_id = None
    reset_battle_effects()


def resolve_escape(mob, method):
    # Ends the battle without rewards. The enemy recovers its health.
    turns = battle_turns

    push_battle_action(
        "Escape",
        f"Player escaped from {mob['name']} using {method}.",
        enemy=mob
    )

    remove_front_enemy()
    mob["hp"] = mob["max_hp"]
    player["wounds"].pop(mob["id"], None)
    set_player_status("Escaped")

    end_current_battle()
    record_battle_result(mob, "Escaped", 0, 0, turns)

    print(f"{mob['name']} recovers its health and returns to "
          f"{room_name(mob['room'])}.")

    revalidate_lineup()
    print(f"Queue: {lineup_line()}")


def resolve_enemy_victory(mob):
    # Gives rewards and removes the defeated enemy from the queue
    old_rank = get_player_rank_info()
    turns = battle_turns

    mob["hp"] = 0
    mob["defeated"] = True

    if mob["id"] not in player["defeated_ids"]:
        player["defeated_ids"].append(mob["id"])

    player["wounds"].pop(mob["id"], None)
    player["wins"] += 1
    player["gold"] += mob["gold_reward"]
    player["score"] += mob["score_reward"]
    set_player_status("Active")

    push_battle_action("Victory", f"Player defeated {mob['name']}.",
                       enemy=mob, enemy_hp_after=0)
    push_battle_action("Reward", f"Player received {mob['gold_reward']} gold.",
                       enemy=mob)
    push_battle_action("Reward",
                       f"Player earned {mob['score_reward']} score points.",
                       enemy=mob)

    level_reward = process_level_completion(mob["type"], mob)
    new_rank = get_player_rank_info()

    if old_rank["rank"] != new_rank["rank"]:
        push_battle_action(
            "Progression",
            f"Rank increased from {old_rank['rank']} to {new_rank['rank']}.",
            enemy=mob
        )

    print()
    animate_banner("V I C T O R Y !", "green")
    print(f"Enemy defeated successfully: {mob['name']}")
    print(f"Gold and score rewards have been added: "
          f"+{mob['gold_reward']} Gold, +{mob['score_reward']} Score")

    if level_reward is not None:
        print(f"LEVEL COMPLETE ({level_reward['difficulty']})! "
              f"ATK {level_reward['old_atk']} -> {level_reward['new_atk']}, "
              f"Max HP {level_reward['old_max_hp']} -> "
              f"{level_reward['new_max_hp']}, "
              f"+{level_reward['gold_bonus']} Gold")

    # Shows the queue before and after the defeated enemy is dequeued
    print(f"Queue before dequeue: {lineup_line()}")

    removed_id = remove_front_enemy()

    if removed_id != mob["id"]:
        print("\nThe lineup could not be updated correctly.")

    end_current_battle()
    record_battle_result(
        mob, "Victory",
        mob["gold_reward"] + (level_reward["gold_bonus"] if level_reward else 0),
        mob["score_reward"],
        turns
    )

    print(f"Queue after dequeue : {lineup_line()}")

    print(f"Progress: HP {player['hp']}/{player['max_hp']} | "
          f"Wins {player['wins']} | Score {player['score']} | "
          f"Gold {player['gold']} | ATK {player['atk']}")

    if old_rank["rank"] != new_rank["rank"]:
        print(f"RANK UP: {old_rank['rank']} -> {new_rank['rank']}. "
              f"You can now fight {new_rank['max_difficulty']} enemies.")

    if mob["type"] == "Boss":
        print("\nThe World Eater has fallen! The dungeon exit is open.")
        print("Choose 'Escape the Dungeon' at camp to win the game.")

    save_current_player_account()


def resolve_player_defeat(mob):
    # Ends the battle when the player's HP reaches zero
    turns = battle_turns
    gold_lost = player["gold"] * DEFEAT_GOLD_LOSS_PERCENT // 100

    player["losses"] += 1
    player["gold"] -= gold_lost
    set_player_status("Defeated")

    push_battle_action(
        "Player Defeat",
        f"Player was defeated by {mob['name']} and lost {gold_lost} gold.",
        enemy=mob,
        player_hp_after=0
    )

    print()
    animate_banner("D E F E A T", "red")
    print(f"{mob['name']} defeated you. "
          f"You dropped {gold_lost} Gold. Losses: {player['losses']}")

    # The expedition ends, so the whole queue is cleared
    encounter_lineup.clear()
    print("Your expedition is over. The Encounter Queue was cleared.")

    # The enemy keeps the wounds you dealt but regenerates a little,
    # so every attempt brings the player closer to winning
    mob["hp"] = min(
        mob["max_hp"],
        mob["hp"] + mob["max_hp"] * ENEMY_REGEN_PERCENT // 100
    )
    mob["defeated"] = False

    if mob["hp"] < mob["max_hp"]:
        player["wounds"][mob["id"]] = mob["hp"]
        print(f"{mob['name']} is still wounded: "
              f"{mob['hp']}/{mob['max_hp']} HP.")
    else:
        player["wounds"].pop(mob["id"], None)

    # The player wakes up at the entrance with part of their health
    player["hp"] = max(1, player["max_hp"] * DEFEAT_REVIVE_PERCENT // 100)
    print(f"You wake up at the entrance with {player['hp']} HP.")

    end_current_battle()
    record_battle_result(mob, "Defeat", -gold_lost, 0, turns)

    save_current_player_account()


# ---------------------------------------------------------------
# CAMP ACTIONS (shop, rest, dungeon exit)
# ---------------------------------------------------------------

def dungeon_shop():
    # The player can buy items here using Gold between battles
    if current_enemy_id is not None:
        print("\nYou cannot shop during a battle.")
        pause()
        return

    while True:
        header("Dungeon Shop")

        print(f"Gold: {player['gold']}\n")

        items = list(item_records.values())

        for number, item in enumerate(items, 1):
            print(f"[{number}] {item['name']} - {item['price']} Gold "
                  f"(owned {item_quantity(item['id'])}/{item['max_carry']})")
            print(f"    {describe_item_effect(item)}")

        print("[0] Leave Shop")

        choice = input(f"\nChoose an item [0-{len(items)}]: ").strip()

        if choice == "0":
            print("\nYou leave the Dungeon Shop.")
            break

        if not choice.isdigit() or not 1 <= int(choice) <= len(items):
            invalid_choice()
            continue

        item = items[int(choice) - 1]
        space = item["max_carry"] - item_quantity(item["id"])
        affordable = player["gold"] // item["price"] if item["price"] else space

        if space <= 0:
            print(f"\nYou cannot carry more than {item['max_carry']} "
                  f"{item['name']}.")
            pause()
            continue

        if affordable <= 0:
            print("\nYou do not have enough Gold.")
            print(f"Price: {item['price']} Gold")
            print(f"Your Gold: {player['gold']} Gold")
            pause()
            continue

        most = min(space, affordable)
        qty = ask_int(f"How many? [1-{most}] (default 1): ", 1, most, 1)
        total = item["price"] * qty

        if not ask_yes_no(f"Buy {qty} {item['name']} for {total} Gold? (Y/N): "):
            print("\nPurchase cancelled.")
            pause()
            continue

        player["gold"] -= total
        change_item_quantity(item["id"], qty)

        push_battle_action(
            "Purchase", f"Player bought {qty} {item['name']} for {total} gold."
        )
        save_current_player_account()

        print("\nPurchase successful!")
        print(f"Item: {item['name']} x{qty}")
        print(f"Gold left: {player['gold']}")
        print(f"Quantity: {item_quantity(item['id'])}")

        pause()


def rest_at_camp():
    # Pays gold to recover part of the player's health
    header("Rest at Camp")

    if current_enemy_id is not None:
        print("You cannot rest during a battle.")
        pause()
        return

    if player["hp"] >= player["max_hp"]:
        print("Your HP is already full.")
        pause()
        return

    if player["gold"] < REST_COST:
        print(f"Resting costs {REST_COST} Gold. You only have "
              f"{player['gold']} Gold.")
        pause()
        return

    heal = player["max_hp"] * REST_HEAL_PERCENT // 100
    hp_before = player["hp"]

    print(f"Resting restores up to {heal} HP for {REST_COST} Gold.")

    if not ask_yes_no("Rest now? (Y/N): "):
        print("\nYou keep moving.")
        pause()
        return

    player["gold"] -= REST_COST
    player["hp"] = min(player["max_hp"], player["hp"] + heal)

    push_battle_action(
        "Camp Rest",
        f"Player rested and restored {player['hp'] - hp_before} HP.",
        player_hp_before=hp_before
    )
    save_current_player_account()

    print(f"\nHP: {hp_before} -> {player['hp']}")
    print(f"Gold left: {player['gold']}")
    pause()


def all_bosses_defeated(defeated_ids):
    bosses = [mob for mob in mob_list if mob["type"] == "Boss"]
    return bool(bosses) and all(m["id"] in defeated_ids for m in bosses)


def escape_dungeon():
    # Wins the game. Only possible after the Boss is defeated.
    header("Escape the Dungeon")

    if current_enemy_id is not None:
        print("Finish the current battle first.")
        pause()
        return False

    if player["status"] == "Victorious":
        print("You have already escaped the dungeon. Well done!")
        pause()
        return False

    if not all_bosses_defeated(player["defeated_ids"]):
        print("The exit is sealed by the World Eater's power.")
        print("Defeat the Boss in the Throne of Ruin to open it.")
        pause()
        return False

    player["score"] += ESCAPE_SCORE_BONUS
    player["status"] = "Victorious"

    push_battle_action(
        "Dungeon Escape",
        f"Player escaped the dungeon and earned {ESCAPE_SCORE_BONUS} score."
    )
    record_battle_result(None, "Escaped Dungeon", 0, ESCAPE_SCORE_BONUS)
    save_current_player_account()

    print("Sunlight floods the stairway as the exit opens...")
    print("YOU ESCAPED THE DUNGEON!")
    print(f"Escape bonus: +{ESCAPE_SCORE_BONUS} Score")
    print(f"Final Score: {player['score']}")
    print(f"Wins / Losses: {player['wins']} / {player['losses']}")
    pause()
    return True


# ---------------------------------------------------------------
# SAVE GAME TRANSACTION
# ---------------------------------------------------------------

def save_game_transaction():
    # Creates readable files containing the current game information
    try:
        now = now_text()

        with open(GAME_RECORD_FILE, "w", encoding="utf-8") as game_file:
            game_file.write("DUNGEON CONQUEST - SAVED GAME\n")
            game_file.write(f"Saved At: {now}\n\n")

            game_file.write("PLAYER INFORMATION\n")

            for key, value in player.items():
                game_file.write(f"{key}: {value}\n")

            rank = get_player_rank_info()

            game_file.write("\nPROGRESSION\n")
            game_file.write(f"Rank: {rank['rank']}\n")
            game_file.write(
                f"Unlocked Difficulties: {get_unlocked_difficulties()}\n"
            )
            game_file.write(f"Next Goal: {rank['next_unlock']}\n")
            game_file.write(
                "Completed Levels: "
                + (", ".join(player["completed_levels"]) or "None") + "\n"
            )

            game_file.write("\nINVENTORY\n")

            for item_id, qty in player["inventory"].items():
                name = item_records.get(item_id, {}).get("name", item_id)
                game_file.write(f"{item_id} | {name} | {qty}\n")

            game_file.write("\nENEMY INFORMATION\n")

            for mob in mob_list:
                game_file.write(
                    f"{mob['id']} | {mob['name']} | "
                    f"HP {mob['hp']}/{mob['max_hp']} | ATK {mob['atk']} | "
                    f"Difficulty {mob['type']} | Status {enemy_status(mob)} | "
                    f"Gold {mob['gold_reward']} | Score {mob['score_reward']} | "
                    f"Room {room_name(mob['room'])}\n"
                )

            game_file.write("\nDUNGEON ENCOUNTER QUEUE (FRONT TO REAR)\n")

            if encounter_lineup:
                for enemy_id in encounter_lineup:
                    mob = get_enemy_by_id(enemy_id)
                    game_file.write(
                        f"{mob['id']} | {mob['name']} | "
                        f"HP {mob['hp']}/{mob['max_hp']}\n"
                    )
            else:
                game_file.write("NO ENEMIES WAITING\n")

            game_file.write("\nCURRENT BATTLE\n")

            if current_enemy_id:
                mob = get_current_enemy()
                game_file.write(f"{mob['id']} | {mob['name']}\n")
            else:
                game_file.write("NO ACTIVE BATTLE\n")

            game_file.write("\nDUNGEON MAP\n")

            for line in dungeon_map_lines(
                player["defeated_ids"], encounter_lineup
            ):
                game_file.write(line + "\n")

        with open(BATTLE_LOG_FILE, "w", encoding="utf-8") as log_file:
            log_file.write("DUNGEON BATTLE LOG\n")
            log_file.write(f"Saved At: {now}\n\n")

            if not battle_history:
                log_file.write("NO BATTLE ACTIONS RECORDED\n")
            else:
                # Saves the battle history in the order it happened
                for action in battle_history:
                    log_file.write(
                        f"{action['action_id']} | {action['date_time']} | "
                        f"{action['action_type']} | "
                        f"Player {action['player_id']} | "
                        f"Enemy {action['enemy_id']} | "
                        f"{action['description']}\n"
                    )
                    log_file.write(
                        f"    Player HP: {action['player_hp_before']} -> "
                        f"{action['player_hp_after']} | "
                        f"Enemy HP: {action['enemy_hp_before']} -> "
                        f"{action['enemy_hp_after']}\n"
                    )

        save_current_player_account()

        print("\nGame transaction records successfully saved.")

    except OSError as error:
        print("\nThe game could not be saved.")
        print(f"Reason: {error}")

    pause()


# ---------------------------------------------------------------
# DUNGEON MENUS
# ---------------------------------------------------------------

def restore_player_for_new_transaction():
    # Prepares the player when entering the dungeon
    if player["hp"] <= 0:
        player["hp"] = max(1, player["max_hp"] * DEFEAT_REVIVE_PERCENT // 100)

    if player["status"] in ("Defeated", "Escaped", "In Battle"):
        player["status"] = "Active"

    save_current_player_account()


def show_live_panel():
    # Live view of the player, the queue and the top of the stack
    mob = get_current_enemy()

    player_bar = color(hp_bar(player["hp"], player["max_hp"]),
                       hp_color(player["hp"], player["max_hp"]))
    print(f"PLAYER : {player_bar} "
          f"{player['hp']}/{player['max_hp']} HP | ATK {player['atk']} | "
          f"Gold {player['gold']}")

    if mob:
        enraged = (
            " ENRAGED" if mob["type"] == "Boss"
            and mob["hp"] <= mob["max_hp"] // 2 else ""
        )
        enemy_bar = color(hp_bar(mob["hp"], mob["max_hp"]),
                          hp_color(mob["hp"], mob["max_hp"]))
        print(f"ENEMY  : {enemy_bar} "
              f"{mob['hp']}/{mob['max_hp']} HP | {mob['name']} | "
              f"ATK {get_enemy_attack_power(mob)}{enraged}")

        effects = []

        if boost_turns_left:
            effects.append(f"Tonic +{boost_percent}% ({boost_turns_left} left)")
        if guard_bonus_ready:
            effects.append("Counter ready")
        if enemy_stunned_turns:
            effects.append(f"Enemy paralyzed ({enemy_stunned_turns})")
        if challenge_used:
            effects.append("Challenge used")

        print(f"EFFECTS: {', '.join(effects) or 'None'}")

    print(f"ROOM   : {room_name(current_room_id())}")
    print(f"QUEUE  : {lineup_line()}")

    if battle_history:
        top = battle_history[-1]
        print(f"STACK  : TOP -> {top['description']} "
              f"({len(battle_history)} actions)")
    else:
        print("STACK  : (empty)")


def battle_menu():
    # Actions available while fighting the enemy at the queue front
    notice = ""

    while current_enemy_id is not None:
        clear_screen()
        header(f"Battle: {get_current_enemy()['name']}")
        show_live_panel()

        potions = sum(
            item_quantity(i) for i, item in item_records.items()
            if item["effect"] == "heal"
        )
        question = "used" if challenge_used else "ready"

        print()
        print_menu_row("[1] Attack", "[2] Defend", f"[3] Potion (x{potions})",
                       width=22)
        print_menu_row("[4] Other Item", f"[5] Challenge ({question})",
                       "[6] Flee", width=22)
        print_menu_row("[7] View Queue", "[8] Action Stack", "[9] Stats",
                       "[10] Save", width=22)

        if notice:
            print(f"\n{notice}")
            notice = ""

        choice = input("\nEnter choice [1-10]: ").strip()

        if choice == "1":
            attack_current_enemy()
        elif choice == "2":
            defend_against_enemy()
        elif choice == "3":
            use_health_potion()
        elif choice == "4":
            use_item()
        elif choice == "5":
            answer_challenge_question()
        elif choice == "6":
            attempt_flee()
        elif choice == "7":
            display_encounter_lineup(pause_after=True)
        elif choice == "8":
            battle_log_menu()
        elif choice == "9":
            view_stats()
        elif choice == "10":
            save_game_transaction()
        else:
            notice = INVALID_CHOICE_TEXT


def dungeon_menu():
    # Camp menu between battles. Battles open the battle menu.
    restore_player_for_new_transaction()
    notice = ""

    while True:
        clear_screen()
        header("Dungeon Expedition - Camp")
        show_live_panel()

        rank = get_player_rank_info()

        print(f"RANK   : {rank['rank']} | Next Goal: {rank['next_unlock']}")

        print("\nEXPLORE AND ENCOUNTER QUEUE")
        print_menu_row("[1] Add Enemy to Queue", "[2] View Queue",
                       "[3] View Next Enemy")
        print("[4] Start Battle with Next Enemy")
        print("CAMP")
        print_menu_row("[5] Dungeon Shop", f"[6] Rest ({REST_COST} Gold)",
                       "[7] Dungeon Map")
        print_menu_row("[8] Action History Stack", "[9] Player Stats",
                       "[10] Inventory")
        print_menu_row("[11] Save Game", "[12] Escape Dungeon",
                       "[13] Leave Dungeon")

        if notice:
            print(f"\n{notice}")
            notice = ""

        choice = input("\nEnter choice [1-13]: ").strip()

        if choice == "1":
            add_enemy_to_lineup()
        elif choice == "2":
            display_encounter_lineup(pause_after=True)
        elif choice == "3":
            view_next_enemy()
        elif choice == "4":
            start_battle_with_next_enemy()
            battle_menu()
        elif choice == "5":
            dungeon_shop()
        elif choice == "6":
            rest_at_camp()
        elif choice == "7":
            dungeon_map_menu()
        elif choice == "8":
            battle_log_menu()
        elif choice == "9":
            view_stats()
        elif choice == "10":
            view_inventory()
        elif choice == "11":
            save_game_transaction()
        elif choice == "12":
            if escape_dungeon():
                break
        elif choice == "13":
            # The queue is kept so the expedition can continue later
            save_current_player_account()

            print("\nYou leave the dungeon. Your Encounter Queue is saved.")
            break
        else:
            notice = INVALID_CHOICE_TEXT


# ---------------------------------------------------------------
# ADMIN: DASHBOARD
# ---------------------------------------------------------------

def player_accounts():
    # Only player accounts (admins are excluded from game reports)
    return {
        username: data
        for username, data in account_records.items()
        if data["role"] == "Player"
    }


def admin_dashboard():
    header("Administrator Dashboard")

    players = player_accounts()
    results = load_battle_results()

    print("RECORD SUMMARY")
    print(f"Player Accounts   : {len(players)}")
    print(f"Admin Accounts    : {len(account_records) - len(players)}")

    tier_counts = ", ".join(
        f"{tier} {sum(1 for m in mob_list if m['type'] == tier)}"
        for tier in LEVEL_ORDER
    )
    print(f"Enemies           : {len(mob_list)} ({tier_counts})")
    print(f"Items             : {len(item_records)}")
    print(f"Rooms / Passages  : {len(room_records)} / {len(room_connections)}")
    print(f"Challenge Quizzes : {len(question_records)}")

    print("\nGAME ACTIVITY")
    print(f"Battles Recorded  : {len(results)}")
    print(f"Total Wins        : {sum(d['wins'] for d in players.values())}")
    print(f"Total Losses      : {sum(d['losses'] for d in players.values())}")
    print(f"Escapes (fled)    : "
          f"{sum(1 for r in results if r['result'] == 'Escaped')}")

    boss_beaten = [
        u for u, d in players.items() if all_bosses_defeated(d["defeated_ids"])
    ]
    victorious = [u for u, d in players.items() if d["status"] == "Victorious"]

    print(f"Boss Defeated By  : {', '.join(boss_beaten) or 'Nobody yet'}")
    print(f"Escaped Dungeon   : {', '.join(victorious) or 'Nobody yet'}")

    if players:
        top = max(players.items(), key=lambda pair: pair[1]["score"])
        print(f"Top Scorer        : {top[0]} ({top[1]['score']} score)")

    if results:
        last = results[-1]
        print(f"Latest Battle     : {last['date_time']} - {last['username']} "
              f"vs {last['enemy_name']} ({last['result']})")

    pause()


# ---------------------------------------------------------------
# ADMIN: PROFILING (FILE MAINTENANCE / CRUD)
# ---------------------------------------------------------------

def crud_menu(title, actions, extra=None):
    # Shows the standard CRUD options for one type of record
    extra = extra or []

    while True:
        header(title)

        print("[1] Add Record")
        print("[2] View All Records")
        print("[3] Search Record")
        print("[4] Update Record")
        print("[5] Delete Record")

        for number, (label, _) in enumerate(extra, 6):
            print(f"[{number}] {label}")

        back = 6 + len(extra)
        print(f"[{back}] Back")

        choice = input(f"\nEnter choice [1-{back}]: ").strip()

        if choice in ("1", "2", "3", "4", "5"):
            actions[int(choice) - 1]()
        elif choice.isdigit() and 6 <= int(choice) < back:
            extra[int(choice) - 6][1]()
        elif choice == str(back):
            break
        else:
            invalid_choice()


def profiling_menu():
    while True:
        header("Profiling (File Maintenance)")

        print("[1] Player Account Maintenance")
        print("[2] Enemy Maintenance")
        print("[3] Item Maintenance")
        print("[4] Room and Passage Maintenance")
        print("[5] Question and Challenge Maintenance")
        print("[6] Back")

        choice = input("\nEnter choice [1-6]: ").strip()

        if choice == "1":
            crud_menu("Player Account Maintenance", [
                add_account_record, view_account_records,
                search_account_record, update_account_record,
                delete_account_record
            ])
        elif choice == "2":
            crud_menu("Enemy Maintenance", [
                add_enemy_record, view_enemy_record_table,
                search_enemy_record, update_enemy_record, delete_enemy_record
            ])
        elif choice == "3":
            crud_menu("Item Maintenance", [
                add_item_record, view_item_records, search_item_record,
                update_item_record, delete_item_record
            ])
        elif choice == "4":
            crud_menu("Room and Passage Maintenance", [
                add_room_record, view_room_records, search_room_record,
                update_room_record, delete_room_record
            ], extra=[
                ("Add Passage (Graph Edge)", add_connection_record),
                ("Remove Passage", remove_connection_record),
                ("View Dungeon Map", admin_view_map)
            ])
        elif choice == "5":
            crud_menu("Question and Challenge Maintenance", [
                add_question_record, view_question_records,
                search_question_record, update_question_record,
                delete_question_record
            ])
        elif choice == "6":
            break
        else:
            invalid_choice()


# ----- Player accounts -----

def print_account_table(accounts):
    # accounts is a list of (username, data) pairs
    print_table(
        ["ID", "Username", "Role", "HP", "ATK", "Gold", "Score", "W/L",
         "Status"],
        [
            [data["id"], username, data["role"],
             f"{data['hp']}/{data['max_hp']}", data["atk"], data["gold"],
             data["score"], f"{data['wins']}/{data['losses']}",
             data["status"]]
            for username, data in accounts
        ]
    )


def find_account(prompt="Enter Username or Player ID: ", show_list=True):
    # Lists the existing accounts, then asks which one to use
    if show_list:
        print("EXISTING ACCOUNTS")

        for username, data in account_records.items():
            print(f"  {data['id']} | {username} ({data['role']})")

        print()

    key = input(prompt).strip()

    if not key:
        print("\nInput must not be blank.")
        return None

    for username, data in account_records.items():
        if username == key or data["id"].upper() == key.upper():
            return username

    print("\nPlayer record not found.")
    return None


def add_account_record():
    header("Add Account")

    username = ask_text("Username: ", banned="|,")

    if username in account_records:
        print("\nThat username already exists.")
        pause()
        return

    password = ask_text("Password: ")
    role = ask_option("Role:", ["Player", "Admin"], "Player")

    prefix = "ADM" if role == "Admin" else "PLY"
    record_id = next_record_id(
        prefix, [d["id"] for d in account_records.values()]
    )

    account_records[username] = new_account_data(record_id, password, role)
    save_all_accounts()

    print(f"\nAccount {username} ({record_id}) added successfully.")
    pause()


def view_account_records():
    header("All Accounts")

    print_account_table(account_records.items())

    print(f"\nTotal records: {len(account_records)}")
    pause()


def search_account_record():
    header("Search Account")

    key = ask_text("Enter part of a username or Player ID: ").lower()
    matches = [
        (u, d) for u, d in account_records.items()
        if key in u.lower() or key in d["id"].lower()
    ]

    if not matches:
        print("\nPlayer record not found.")
    else:
        print_account_table(matches)

        rows = []

        for username, data in matches:
            items = "\n".join(
                f"{item_records.get(i, {}).get('name', i)} x{q}"
                for i, q in data["inventory"].items()
            )
            rows.append([
                username,
                ", ".join(data["defeated_ids"]) or "None",
                items or "Empty",
                ", ".join(data["lineup"]) or "Empty"
            ])

        print()
        print_table(["Username", "Defeated", "Inventory", "Queue"], rows)

    pause()


def update_account_record():
    header("Update Account")

    username = find_account()

    if username is None:
        pause()
        return

    data = account_records[username]

    if username == player.get("name") and data["role"] == "Admin":
        print("Note: you are editing your own admin account.")

    print("Press Enter to keep the current value.\n")

    data["password"] = ask_text(f"Password [{data['password']}]: ",
                                data["password"])

    if data["role"] == "Player":
        data["max_hp"] = ask_int(f"Max HP [{data['max_hp']}]: ", 1,
                                 default=data["max_hp"])
        data["hp"] = ask_int(f"HP [{min(data['hp'], data['max_hp'])}]: ",
                             0, data["max_hp"],
                             min(data["hp"], data["max_hp"]))
        data["atk"] = ask_int(f"Attack [{data['atk']}]: ", 1,
                              default=data["atk"])
        data["gold"] = ask_int(f"Gold [{data['gold']}]: ", 0,
                               default=data["gold"])
        data["score"] = ask_int(f"Score [{data['score']}]: ", 0,
                                default=data["score"])
        data["wins"] = ask_int(f"Wins [{data['wins']}]: ", 0,
                               default=data["wins"])
        data["losses"] = ask_int(f"Losses [{data['losses']}]: ", 0,
                                 default=data["losses"])
        data["status"] = ask_option("Status:", PLAYER_STATUSES,
                                    data["status"])

    save_all_accounts()
    print(f"\nAccount {username} updated successfully.")
    pause()


def delete_account_record():
    header("Delete Account")

    username = find_account()

    if username is None:
        pause()
        return

    if username == player.get("name"):
        print("\nYou cannot delete the account you are logged in with.")
        pause()
        return

    print_account_table([(username, account_records[username])])

    if not ask_yes_no("\nDelete this account permanently? (Y/N): "):
        print("\nNothing was deleted.")
        pause()
        return

    del account_records[username]
    save_all_accounts()

    print(f"\nAccount {username} deleted.")
    pause()


# ----- Enemies -----

def print_enemy_table(mobs):
    print_table(
        ["ID", "Name", "Difficulty", "HP", "ATK", "Gold", "Score", "Room"],
        [
            [mob["id"], mob["name"], mob["type"], mob["max_hp"], mob["atk"],
             mob["gold_reward"], mob["score_reward"],
             f"{mob['room']} {room_name(mob['room'])}"]
            for mob in mobs
        ]
    )


def find_enemy_record(show_list=True):
    # Lists the existing enemies, then asks which one to use
    if show_list:
        print("EXISTING ENEMIES")

        for mob in mob_list:
            print(f"  {mob['id']} | {mob['name']} ({mob['type']})")

        print()

    enemy_id = input("Enter Enemy ID: ").strip().upper()

    if not enemy_id:
        print("\nEnemy ID must not be blank.")
        return None

    mob = get_enemy_by_id(enemy_id)

    if mob is None:
        print("\nEnemy record not found.")

    return mob


def ask_enemy_room(default=None):
    rooms = [r for r in room_records if r != ENTRANCE_ROOM_ID]

    for room_id in rooms:
        print(f"  {room_id} {room_name(room_id)}")

    while True:
        room_id = input(
            f"Room ID{f' [{default}]' if default else ''}: "
        ).strip().upper()

        if not room_id and default:
            return default

        if room_id in rooms:
            return room_id

        print("Room record not found (the entrance cannot hold enemies).")


def add_enemy_record():
    header("Add Enemy")

    enemy_id = next_record_id("ENM", [m["id"] for m in mob_list])
    print(f"New Enemy ID: {enemy_id}")

    name = ask_text("Name: ")
    enemy_type = ask_option("Difficulty:", LEVEL_ORDER)
    max_hp = ask_int("Max HP: ", 1)
    atk = ask_int("Attack Power: ", 1)
    gold = ask_int("Gold Reward: ", 0)
    score = ask_int("Score Reward: ", 0)
    room = ask_enemy_room()

    mob_list.append(make_enemy(enemy_id, name, enemy_type, max_hp, atk,
                               gold, score, room))
    save_enemies()

    print(f"\nEnemy {enemy_id} {name} added successfully.")
    pause()


def view_enemy_record_table():
    header("All Enemies")

    print_enemy_table(mob_list)

    print(f"\nTotal records: {len(mob_list)}")
    pause()


def search_enemy_record():
    header("Search Enemy")

    key = ask_text("Enter part of an Enemy ID, name or difficulty: ").lower()
    matches = [
        m for m in mob_list
        if key in m["id"].lower() or key in m["name"].lower()
        or key in m["type"].lower()
    ]

    if not matches:
        print("\nEnemy record not found.")

    if matches:
        print_enemy_table(matches)

    pause()


def update_enemy_record():
    header("Update Enemy")

    mob = find_enemy_record()

    if mob is None:
        pause()
        return

    print("Press Enter to keep the current value.\n")

    mob["name"] = ask_text(f"Name [{mob['name']}]: ", mob["name"])
    mob["type"] = ask_option("Difficulty:", LEVEL_ORDER, mob["type"])
    mob["max_hp"] = ask_int(f"Max HP [{mob['max_hp']}]: ", 1,
                            default=mob["max_hp"])
    mob["atk"] = ask_int(f"Attack [{mob['atk']}]: ", 1, default=mob["atk"])
    mob["gold_reward"] = ask_int(f"Gold Reward [{mob['gold_reward']}]: ", 0,
                                 default=mob["gold_reward"])
    mob["score_reward"] = ask_int(f"Score Reward [{mob['score_reward']}]: ",
                                  0, default=mob["score_reward"])
    mob["room"] = ask_enemy_room(mob["room"])
    mob["hp"] = mob["max_hp"]

    save_enemies()
    print(f"\nEnemy {mob['id']} updated successfully.")
    pause()


def delete_enemy_record():
    header("Delete Enemy")

    mob = find_enemy_record()

    if mob is None:
        pause()
        return

    print_enemy_table([mob])

    if not ask_yes_no("\nDelete this enemy permanently? (Y/N): "):
        print("\nNothing was deleted.")
        pause()
        return

    mob_list.remove(mob)

    # Removes the enemy from every saved queue
    for data in account_records.values():
        data["lineup"] = [e for e in data["lineup"] if e != mob["id"]]

    save_enemies()
    save_all_accounts()

    print(f"\nEnemy {mob['id']} deleted.")
    pause()


# ----- Items -----

def print_item_table(items):
    print_table(
        ["ID", "Name", "Effect", "Power", "Price", "Carry", "Description"],
        [
            [item["id"], item["name"], item["effect"], item["power"],
             item["price"], item["max_carry"], describe_item_effect(item)]
            for item in items
        ],
        max_width=30
    )


def find_item_record():
    # Lists the existing items, then asks which one to use
    print("EXISTING ITEMS")

    for item in item_records.values():
        print(f"  {item['id']} | {item['name']} ({item['effect']})")

    print()

    item_id = input("Enter Item ID: ").strip().upper()

    if not item_id:
        print("\nItem ID must not be blank.")
        return None

    if item_id not in item_records:
        print("\nItem record not found.")
        return None

    return item_records[item_id]


def keep_hint(value):
    # Shows the current value in update prompts, e.g. "Name [Potion]: "
    return f" [{value}]" if value is not None else ""


def ask_item_fields(item=None):
    item = item or {}

    name = ask_text(f"Name{keep_hint(item.get('name'))}: ", item.get("name"))
    effect = ask_option("Effect:", list(ITEM_EFFECTS), item.get("effect"))

    hints = {
        "heal": "percent of Max HP healed",
        "boost": "percent extra damage",
        "stun": "enemy turns skipped",
        "damage": "average damage dealt",
        "escape": "not used, enter 0"
    }
    power = ask_int(f"Power ({hints[effect]}){keep_hint(item.get('power'))}: ",
                    0, default=item.get("power"))
    price = ask_int(f"Price{keep_hint(item.get('price'))}: ",
                    0, default=item.get("price"))
    carry = ask_int(f"Max Carry{keep_hint(item.get('max_carry'))}: ",
                    1, default=item.get("max_carry"))
    description = ask_text(
        f"Description{keep_hint(item.get('description'))}: ",
        item.get("description")
    )

    return {"name": name, "effect": effect, "power": power, "price": price,
            "max_carry": carry, "description": description}


def add_item_record():
    header("Add Item")

    item_id = next_record_id("ITM", list(item_records))
    print(f"New Item ID: {item_id}")

    fields = ask_item_fields()
    item_records[item_id] = {"id": item_id, **fields}
    save_items()

    print(f"\nItem {item_id} {fields['name']} added successfully.")
    pause()


def view_item_records():
    header("All Items")

    print_item_table(item_records.values())

    print(f"\nTotal records: {len(item_records)}")
    pause()


def search_item_record():
    header("Search Item")

    key = ask_text("Enter part of an Item ID, name or effect: ").lower()
    matches = [
        i for i in item_records.values()
        if key in i["id"].lower() or key in i["name"].lower()
        or key in i["effect"]
    ]

    if not matches:
        print("\nItem record not found.")

    if matches:
        print_item_table(matches)

    pause()


def update_item_record():
    header("Update Item")

    item = find_item_record()

    if item is None:
        pause()
        return

    print("Press Enter to keep the current value.\n")
    item.update(ask_item_fields(item))

    # Players may now carry more than the new limit, so trim inventories
    for data in account_records.values():
        if data["inventory"].get(item["id"], 0) > item["max_carry"]:
            data["inventory"][item["id"]] = item["max_carry"]

    save_items()
    save_all_accounts()

    print(f"\nItem {item['id']} updated successfully.")
    pause()


def delete_item_record():
    header("Delete Item")

    item = find_item_record()

    if item is None:
        pause()
        return

    print_item_table([item])

    if not ask_yes_no("\nDelete this item? It is removed from every "
                      "inventory. (Y/N): "):
        print("\nNothing was deleted.")
        pause()
        return

    del item_records[item["id"]]

    for data in account_records.values():
        data["inventory"].pop(item["id"], None)

    save_items()
    save_all_accounts()

    print(f"\nItem {item['id']} deleted.")
    pause()


# ----- Rooms and passages -----

def print_room_table(rooms):
    rows = []

    for room in rooms:
        enemies = "\n".join(m["name"] for m in get_room_enemies(room["id"]))
        links = "\n".join(n for n, _ in get_neighbors(room["id"]))
        rows.append([room["id"], room["name"], room["description"],
                     enemies or "None", links or "None"])

    print_table(["ID", "Name", "Description", "Enemies", "Links"], rows)


def find_room_record():
    # Lists the existing rooms, then asks which one to use
    print("EXISTING ROOMS")

    for room in room_records.values():
        print(f"  {room['id']} | {room['name']}")

    print()

    room_id = choose_room()
    return room_records[room_id] if room_id else None


def add_room_record():
    header("Add Room")

    room_id = next_record_id("ROOM", list(room_records), start=0)
    print(f"New Room ID: {room_id}")

    name = ask_text("Name: ")
    description = ask_text("Description: ")

    room_records[room_id] = {"id": room_id, "name": name,
                             "description": description}
    save_rooms()

    print(f"\nRoom {room_id} {name} added successfully.")
    print("Remember to add a passage so players can reach it.")
    pause()


def view_room_records():
    header("All Rooms")

    print_room_table(room_records.values())

    print(f"\nTotal records: {len(room_records)}")
    pause()


def search_room_record():
    header("Search Room")

    key = ask_text("Enter part of a Room ID or name: ").lower()
    matches = [
        r for r in room_records.values()
        if key in r["id"].lower() or key in r["name"].lower()
    ]

    if not matches:
        print("\nRoom record not found.")

    if matches:
        print_room_table(matches)

    pause()


def update_room_record():
    header("Update Room")

    room = find_room_record()

    if room is None:
        pause()
        return

    print("Press Enter to keep the current value.\n")
    room["name"] = ask_text(f"Name [{room['name']}]: ", room["name"])
    room["description"] = ask_text(
        f"Description{keep_hint(room['description'])}: ", room["description"]
    )

    save_rooms()
    print(f"\nRoom {room['id']} updated successfully.")
    pause()


def delete_room_record():
    header("Delete Room")

    room = find_room_record()

    if room is None:
        pause()
        return

    if room["id"] == ENTRANCE_ROOM_ID:
        print("\nThe Dungeon Entrance cannot be deleted.")
        pause()
        return

    if get_room_enemies(room["id"]):
        print("\nThis room still holds enemies. Move or delete them first.")
        pause()
        return

    print_room_table([room])

    if not ask_yes_no("\nDelete this room and all its passages? (Y/N): "):
        print("\nNothing was deleted.")
        pause()
        return

    del room_records[room["id"]]
    room_connections[:] = [
        c for c in room_connections
        if room["id"] not in (c["a"], c["b"])
    ]

    save_rooms()
    save_connections()

    print(f"\nRoom {room['id']} deleted.")
    pause()


def validate_connection(room_a, room_b):
    # Returns an error message, or None if the passage is allowed
    if room_a not in room_records or room_b not in room_records:
        return "Room record not found."

    if room_a == room_b:
        return "A room cannot be connected to itself."

    for link in room_connections:
        if {link["a"], link["b"]} == {room_a, room_b}:
            return "These rooms are already connected."

    return None


def add_connection_record():
    header("Add Passage")

    for room_id in room_records:
        print(f"  {room_id} {room_name(room_id)}")

    room_a = input("\nFirst Room ID: ").strip().upper()
    room_b = input("Second Room ID: ").strip().upper()

    error = validate_connection(room_a, room_b)

    if error:
        print(f"\n{error}")
        pause()
        return

    label = ask_text("Passage name: ")
    room_connections.append({"a": room_a, "b": room_b, "label": label})
    save_connections()

    print(f"\nPassage added: {room_name(room_a)} <-> {room_name(room_b)} "
          f"via {label}")
    pause()


def remove_connection_record():
    header("Remove Passage")

    if not room_connections:
        print("There are no passages.")
        pause()
        return

    for number, link in enumerate(room_connections, 1):
        print(f"[{number}] {link['a']} {room_name(link['a'])} <-> "
              f"{link['b']} {room_name(link['b'])} via {link['label']}")

    number = ask_int(f"\nPassage to remove [1-{len(room_connections)}]: ",
                     1, len(room_connections))
    link = room_connections[number - 1]

    if not ask_yes_no(f"Remove the {link['label']}? (Y/N): "):
        print("\nNothing was removed.")
        pause()
        return

    room_connections.pop(number - 1)
    save_connections()

    unreachable = [
        r for r in room_records if r not in
        depth_first_traversal(ENTRANCE_ROOM_ID)
    ]

    print("\nPassage removed.")

    if unreachable:
        print("Warning: these rooms can no longer be reached: "
              + ", ".join(room_name(r) for r in unreachable))
    pause()


def admin_view_map():
    header("Dungeon Map (Graph)")

    for line in dungeon_drawing_lines([]):
        print(line)

    print()

    for line in dungeon_map_lines([]):
        print(line)

    pause()


# ----- Questions -----

def print_question_table(questions):
    rows = []

    for question in questions:
        choices = "\n".join(
            f"[{number}] {choice}"
            + (" *" if number == question["answer"] else "")
            for number, choice in enumerate(question["choices"], 1)
        )
        rows.append([question["id"], question["question"], choices,
                     f"+{question['bonus']}"])

    print_table(["ID", "Question", "Choices (* = correct)", "Bonus"], rows,
                max_width=30)


def find_question_record():
    # Lists the existing questions, then asks which one to use
    print("EXISTING QUESTIONS")

    for question in question_records:
        print(f"  {question['id']} | {question['question']}")

    print()

    qid = input("Enter Question ID: ").strip().upper()

    if not qid:
        print("\nQuestion ID must not be blank.")
        return None

    for question in question_records:
        if question["id"] == qid:
            return question

    print("\nQuestion record not found.")
    return None


def ask_question_fields(question=None):
    question = question or {"choices": []}
    old_choices = question["choices"] + [None] * (4 - len(question["choices"]))

    text = ask_text(f"Question{keep_hint(question.get('question'))}: ",
                    question.get("question"))
    choices = [
        ask_text(f"Choice {n}{keep_hint(old)}: ", old, "|;")
        for n, old in enumerate(old_choices[:4], 1)
    ]
    answer = ask_int(
        f"Correct choice number [1-4]{keep_hint(question.get('answer'))}: ",
        1, 4, question.get("answer")
    )
    bonus = ask_int(f"Bonus damage{keep_hint(question.get('bonus'))}: ",
                    0, default=question.get("bonus"))

    return {"question": text, "choices": choices, "answer": answer,
            "bonus": bonus}


def add_question_record():
    header("Add Question")

    qid = next_record_id("QST", [q["id"] for q in question_records])
    print(f"New Question ID: {qid}")

    question_records.append({"id": qid, **ask_question_fields()})
    save_questions()

    print(f"\nQuestion {qid} added successfully.")
    pause()


def view_question_records():
    header("All Questions")

    print_question_table(question_records)

    print(f"\nTotal records: {len(question_records)}")
    pause()


def search_question_record():
    header("Search Question")

    key = ask_text("Enter part of a Question ID or text: ").lower()
    matches = [
        q for q in question_records
        if key in q["id"].lower() or key in q["question"].lower()
    ]

    if not matches:
        print("\nQuestion record not found.")

    if matches:
        print_question_table(matches)

    pause()


def update_question_record():
    header("Update Question")

    question = find_question_record()

    if question is None:
        pause()
        return

    print("Press Enter to keep the current value.\n")
    question.update(ask_question_fields(question))
    save_questions()

    print(f"\nQuestion {question['id']} updated successfully.")
    pause()


def delete_question_record():
    header("Delete Question")

    question = find_question_record()

    if question is None:
        pause()
        return

    print_question_table([question])

    if not ask_yes_no("\nDelete this question? (Y/N): "):
        print("\nNothing was deleted.")
        pause()
        return

    question_records.remove(question)
    save_questions()

    print(f"\nQuestion {question['id']} deleted.")
    pause()


# ---------------------------------------------------------------
# ADMIN: TRANSACTIONS (GAME SETUP AND MANAGEMENT)
# ---------------------------------------------------------------

def choose_player_account():
    for username, data in player_accounts().items():
        print(f"  {data['id']} {username}")

    username = find_account("\nEnter Username or Player ID: ", show_list=False)

    if username is not None and account_records[username]["role"] != "Player":
        print("\nThat account is not a Player account.")
        return None

    return username


def view_player_progress():
    header("View Player Progress")

    username = choose_player_account()

    if username is None:
        pause()
        return

    data = account_records[username]
    rank = get_rank_info(data["wins"])

    print()
    print_account_table([(username, data)])
    print(f"Rank            : {rank['rank']} ({rank['next_unlock']})")
    print(f"Completed Levels: {', '.join(data['completed_levels']) or 'None'}")
    print(f"Defeated Enemies: {len(data['defeated_ids'])}/{len(mob_list)}")
    print(f"Saved Queue     : {', '.join(data['lineup']) or 'Empty'}")
    print(f"Boss Defeated   : "
          f"{'Yes' if all_bosses_defeated(data['defeated_ids']) else 'No'}")

    print("\nDUNGEON MAP FOR THIS PLAYER")

    for line in dungeon_map_lines(data["defeated_ids"], data["lineup"]):
        print(line)

    pause()


def reset_player_game_data():
    header("Reset Player Game Data")

    username = choose_player_account()

    if username is None:
        pause()
        return

    if not ask_yes_no(f"\nReset all progress of {username}? (Y/N): "):
        print("\nNothing was changed.")
        pause()
        return

    data = account_records[username]
    fresh = new_account_data(data["id"], data["password"])
    account_records[username] = fresh
    save_all_accounts()

    print(f"\n{username} has been reset to the starting stats.")
    pause()


def assign_starting_items():
    header("Assign Items to Player")

    username = choose_player_account()

    if username is None:
        pause()
        return

    data = account_records[username]
    items = list(item_records.values())

    print()

    for number, item in enumerate(items, 1):
        print(f"[{number}] {item['name']} (has "
              f"{data['inventory'].get(item['id'], 0)}/{item['max_carry']})")

    number = ask_int(f"Choose item [1-{len(items)}]: ", 1, len(items))
    item = items[number - 1]

    qty = ask_int(f"New quantity for {item['name']} "
                  f"[0-{item['max_carry']}]: ", 0, item["max_carry"])

    if qty > 0:
        data["inventory"][item["id"]] = qty
    else:
        data["inventory"].pop(item["id"], None)

    save_all_accounts()
    print(f"\n{username} now has {qty} {item['name']}.")
    pause()


def set_enemy_difficulty():
    header("Set Enemy Difficulty")

    print_enemy_table(mob_list)

    print()
    mob = find_enemy_record(show_list=False)

    if mob is None:
        pause()
        return

    mob["type"] = ask_option("New difficulty:", LEVEL_ORDER, mob["type"])
    percent = ask_int("Scale HP and Attack by percent (100 = unchanged): ",
                      10, 500, 100)

    mob["max_hp"] = max(1, mob["max_hp"] * percent // 100)
    mob["atk"] = max(1, mob["atk"] * percent // 100)
    mob["hp"] = mob["max_hp"]

    save_enemies()

    print("\nEnemy updated:")
    print_enemy_table([mob])
    pause()


def battle_history_lines(username=None):
    results = load_battle_results()

    if username:
        results = [r for r in results if r["username"] == username]

    if not results:
        return ["No battle results have been recorded."]

    lines = table_lines(
        ["Date/Time", "Player", "Enemy", "Result", "Turns", "Gold", "Score"],
        [
            [r["date_time"], r["username"], r["enemy_name"], r["result"],
             r["turns"], r["gold"], r["score"]]
            for r in results
        ]
    )

    lines.append(f"\nTotal battles: {len(results)}")
    return lines


def view_battle_history():
    header("View Battle History")

    username = input("Filter by username (Enter for all): ").strip()

    print()

    for line in battle_history_lines(username or None):
        print(line)

    pause()


def game_setup_menu():
    while True:
        header("Transactions (Game Setup and Management)")

        print("[1] View Player Progress")
        print("[2] Reset Player Game Data")
        print("[3] Assign Starting Items")
        print("[4] Set Enemy Difficulty")
        print("[5] View Battle History")
        print("[6] Back")

        choice = input("\nEnter choice [1-6]: ").strip()

        if choice == "1":
            view_player_progress()
        elif choice == "2":
            reset_player_game_data()
        elif choice == "3":
            assign_starting_items()
        elif choice == "4":
            set_enemy_difficulty()
        elif choice == "5":
            view_battle_history()
        elif choice == "6":
            break
        else:
            invalid_choice()


# ---------------------------------------------------------------
# ADMIN: REPORT GENERATION
# Every report is built from the live records, displayed, and can be
# exported to a text file inside the reports folder.
# ---------------------------------------------------------------

def report_player_statistics():
    lines = table_lines(
        ["ID", "Username", "HP", "ATK", "Gold", "Score", "Rank", "Status"],
        [
            [d["id"], username, f"{d['hp']}/{d['max_hp']}", d["atk"],
             d["gold"], d["score"], get_rank_info(d["wins"])["rank"],
             d["status"]]
            for username, d in player_accounts().items()
        ]
    )

    lines.append(f"\nTotal players: {len(player_accounts())}")
    return lines


def report_wins_losses():
    rows = []
    total_w = total_l = 0

    for username, d in player_accounts().items():
        battles = d["wins"] + d["losses"]
        rate = f"{d['wins'] * 100 / battles:.0f}%" if battles else "-"
        total_w += d["wins"]
        total_l += d["losses"]
        rows.append([username, d["wins"], d["losses"], battles, rate])

    lines = table_lines(
        ["Username", "Wins", "Losses", "Battles", "Win Rate"], rows
    )
    lines.append(f"\nTotal wins: {total_w} | Total losses: {total_l}")
    return lines


def report_enemies_defeated():
    players = player_accounts()
    rows = []

    for mob in mob_list:
        who = [u for u, d in players.items() if mob["id"] in d["defeated_ids"]]
        rows.append([mob["id"], mob["name"], mob["type"], len(who),
                     ", ".join(who) or "none"])

    lines = table_lines(
        ["ID", "Enemy", "Difficulty", "Times", "Defeated By"], rows,
        max_width=30
    )
    lines.append("")
    lines += table_lines(
        ["Username", "Enemies Defeated"],
        [
            [username, f"{len(d['defeated_ids'])}/{len(mob_list)}"]
            for username, d in players.items()
        ]
    )
    return lines


def report_score_ranking():
    ranked = sorted(player_accounts().items(),
                    key=lambda pair: pair[1]["score"], reverse=True)

    return table_lines(
        ["Place", "Username", "Score", "Wins", "Rank"],
        [
            [place, username, d["score"], d["wins"],
             get_rank_info(d["wins"])["rank"]]
            for place, (username, d) in enumerate(ranked, 1)
        ]
    )


def report_boss_status():
    bosses = [m for m in mob_list if m["type"] == "Boss"]
    lines = ["Bosses: " + (", ".join(m["name"] for m in bosses) or "None"), ""]

    lines += table_lines(
        ["Username", "Boss Defeated", "Dungeon Escaped"],
        [
            [username,
             "Yes" if all_bosses_defeated(d["defeated_ids"]) else "No",
             "Yes" if d["status"] == "Victorious" else "No"]
            for username, d in player_accounts().items()
        ]
    )
    return lines


def report_available_items():
    rows = []

    for item in item_records.values():
        owned = sum(
            d["inventory"].get(item["id"], 0)
            for d in player_accounts().values()
        )
        rows.append([item["id"], item["name"], item["effect"], item["price"],
                     item["max_carry"], owned, describe_item_effect(item)])

    return table_lines(
        ["ID", "Name", "Effect", "Price", "Carry", "Owned", "Description"],
        rows,
        max_width=30
    )


def report_enemy_difficulty():
    lines = []

    for tier in LEVEL_ORDER:
        mobs = [m for m in mob_list if m["type"] == tier]
        lines.append(f"{tier.upper()} ({len(mobs)} enemies)")

        if mobs:
            lines += table_lines(
                ["ID", "Name", "HP", "ATK", "Gold", "Score", "Room"],
                [
                    [mob["id"], mob["name"], mob["max_hp"], mob["atk"],
                     mob["gold_reward"], mob["score_reward"],
                     room_name(mob["room"])]
                    for mob in mobs
                ]
            )

            avg_hp = sum(m["max_hp"] for m in mobs) // len(mobs)
            avg_atk = sum(m["atk"] for m in mobs) // len(mobs)
            lines.append(f"Average HP {avg_hp}, average ATK {avg_atk}")

        lines.append("")

    return lines


def report_dungeon_map():
    lines = ["MAP DRAWING"]
    lines += dungeon_drawing_lines([])
    lines.append("")
    lines.append("ROOMS AND PASSAGES")
    lines += dungeon_map_lines([])
    lines.append("")
    lines.append("EXPLORATION ORDER FROM THE ENTRANCE (DFS)")
    lines += [f"  {n}. {room_name(r)}" for n, r in
              enumerate(depth_first_traversal(ENTRANCE_ROOM_ID), 1)]
    return lines


REPORTS = [
    ("Player Statistics Report", report_player_statistics),
    ("Battle Wins and Losses Report", report_wins_losses),
    ("Enemies Defeated Report", report_enemies_defeated),
    ("Player Score Ranking Report", report_score_ranking),
    ("Boss Defeat Status Report", report_boss_status),
    ("Battle History Report", battle_history_lines),
    ("Available Items Report", report_available_items),
    ("Enemy Difficulty Report", report_enemy_difficulty),
    ("Dungeon Map Report", report_dungeon_map)
]


def show_report(title, lines):
    header(title)
    print(f"Generated: {now_text()}\n")

    for line in lines:
        print(line)

    if ask_yes_no("\nExport this report to a text file? (Y/N): "):
        try:
            Path(REPORT_FOLDER).mkdir(exist_ok=True)
            file_name = title.lower().replace(" ", "_") + ".txt"
            path = Path(REPORT_FOLDER) / file_name

            with open(path, "w", encoding="utf-8") as file:
                file.write(f"{title.upper()}\nGenerated: {now_text()}\n\n")
                file.write("\n".join(lines) + "\n")

            print(f"\nReport saved to {path}")
        except OSError as error:
            print(f"\nThe report could not be saved: {error}")

    pause()


def report_menu():
    while True:
        header("Report Generation")

        for number, (title, _) in enumerate(REPORTS, 1):
            print(f"[{number}] {title}")

        back = len(REPORTS) + 1
        print(f"[{back}] Back")

        choice = input(f"\nEnter choice [1-{back}]: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(REPORTS):
            title, builder = REPORTS[int(choice) - 1]
            show_report(title, builder())
        elif choice == str(back):
            break
        else:
            invalid_choice()


def admin_menu():
    # Main menu for administrators
    while True:
        header("Admin Menu")

        print(f"Logged in as: {player['name']} | Role: Admin")

        print("\n[1] Dashboard")
        print("[2] Profiling (File Maintenance)")
        print("[3] Transactions (Game Setup and Management)")
        print("[4] Report Generation")
        print("[5] Logout")

        choice = input("\nEnter choice [1-5]: ").strip()

        if choice == "1":
            admin_dashboard()
        elif choice == "2":
            profiling_menu()
        elif choice == "3":
            game_setup_menu()
        elif choice == "4":
            report_menu()
        elif choice == "5":
            reset_session_state()
            print("\nLogging out...")
            break
        else:
            invalid_choice()


if __name__ == "__main__":
    # Load saved records first, then show the login screen
    load_all_records()
    login_screen()
