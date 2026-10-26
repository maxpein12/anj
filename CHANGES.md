# Dungeon Conquest: Revisions from the Original Version

This document lists what changed between the **original** version of
`DS_MidtermProject2_Transaction2_BariteJMercadoR.py` (about 2,600 lines) and
the **revised** version in this repository (about 5,400 lines). It covers bug
fixes, new features, balance changes and features that were moved or removed.

---

## At a glance

| Area | Original | Revised |
|------|----------|---------|
| Starting the game | The program loaded the accounts and then exited | The login screen starts normally |
| User roles | Players only | Players and an Administrator |
| Data structures | Queue (lineup) and Stack (battle log) | Queue, Stack and a **Graph** (dungeon map, with BFS travel) |
| Dungeon | A list of enemies with an "area" name | 11 connected rooms; an enemy can only be queued once the way to its room is open |
| Battle actions | Attack and items | Attack, Defend, Potion, Items, Challenge Question, Flee |
| Items | 4 items in fixed slots, no carry limit | 5 items, stored as records with carry limits |
| Losing a battle | No penalty; HP fully restored later | Gold penalty, queue cleared, enemy keeps its wounds |
| Ending the game | No final goal | Defeat the Boss, then choose Escape Dungeon |
| Record files | 3 (accounts, saved game, battle log) | 9 record files plus a `reports/` folder |
| Admin tools | None | Dashboard, CRUD for all records, game setup, 9 reports |
| Screens | Plain text lines | Bordered tables, live status panel, colours and animations |

---

## 1. Bug fixes

1. **The game did not start.** The original ended with only
   `load_accounts()` under `if __name__ == "__main__":`, so the login screen
   was never shown. The revised version loads every record file and then
   calls `login_screen()`.
2. **One bad line in the account file deleted every account.** In the
   original, a `ValueError` while reading `player_accounts.txt` sent the
   program to `create_default_account_file()`, which replaced the whole file
   with the single default account. The revised loader skips only the
   damaged line and keeps every other account.
3. **Some characters broke the save file.** Records are stored with `|`
   between fields, but the original allowed `|` in usernames and passwords.
   Sign-up and every admin form now reject characters that would break a
   record.
4. **Any player could see every other player's account.** "Player Account
   Information" in the player menu listed everyone's stats. Account records
   are now only visible to the Administrator.
5. **Items gave free turns.** In the original, using a Health Potion,
   Strength Tonic or Paralysis Bomb did not let the enemy attack back, so a
   player could heal over and over without risk. Every action now uses the
   player's turn, and the enemy counterattacks unless it is paralysed.
6. **Losing had no consequence.** After a defeat the enemy healed to full
   and the player's HP was fully restored on the next visit. See the new
   defeat rules in section 3.3.
7. **The lineup was lost when leaving.** Leaving the dungeon or logging out
   cleared the Encounter Queue. The queue is now saved with the account and
   restored at the next login.

---

## 2. Data structures

| Structure | Original | Revised |
|-----------|----------|---------|
| **Queue** (Encounter Queue) | Enemies were added by typing an Enemy ID from a list | Still added by Enemy ID, but the list only shows enemies the player can queue now (not defeated, not already queued, unlocked by rank, room reachable). Operations: enqueue, dequeue, peek ("View Next Enemy"), display, empty check |
| **Stack** (Battle Action History) | Push, peek, display and "Undo Last Log Entry" (pop) | Same operations. The pop option is now named **"Remove Latest Log Entry (does not undo the action)"**, so players don't think it reverses HP or gold. The top of the stack is shown on the battle screen |
| **Graph** (Dungeon Map) | Not present | **New.** Rooms are vertices and passages are two-way edges. Uses **BFS** (shortest route and which rooms can be reached) and **DFS** (exploration order). Admins can add and remove rooms and passages |

---

## 3. New and changed player features

### 3.1 Dungeon map (Graph)

- The dungeon has 11 rooms, from the **Dungeon Entrance** to the **Throne of
  Ruin**, joined by 13 named passages (e.g. *Rusted Grate*, *Crimson Gate*).
  Each enemy guards one room.
- **Reachability:** an enemy can only be added to the queue if its room is
  next to the entrance or to a room that is already cleared. BFS from the
  entrance works this out. Enemies waiting in the queue count as planned
  clears, so the player can plan a route several rooms ahead.
- If the player flees from an enemy, any queued enemies beyond it that can
  no longer be reached are removed from the queue.
- **Dungeon Map and Routes** menu:
  - a drawn map of room boxes with lines between them, showing each room's
    status (Entrance, Open, Cleared, Locked) and each enemy's state, with a
    double border around the player's current room
- **Current room:** the camp and battle screens show which room the player
  is in. During a battle it is the enemy's room; otherwise it is the room
  of the last enemy defeated, or the entrance at the start.
  - room details with each room's enemies and passages
  - **Find Route to a Room** (BFS shortest path)
  - **Exploration Order** (DFS traversal)

### 3.2 Battle

The battle now has its own screen with a live panel showing both HP bars,
active effects, the queue and the top of the action stack.

| Action | Original | Revised |
|--------|----------|---------|
| Attack | 5% miss, 15% critical (×2 damage) | 7% miss, 12% critical (×1.75 damage) |
| Defend | — | **New.** Take only 40% damage this turn; the next attack does +30% |
| Health Potion | Separate item menu | Quick option on the battle menu showing how many potions are left |
| Other items | Item submenu | Item submenu listing only the items the player owns |
| Challenge Question | — | **New.** Once per battle: a correct answer is a sure hit with bonus damage; a wrong answer loses the turn. The choices are shuffled every time |
| Flee | — | **New.** 50% chance to escape; a failed attempt gives the enemy a free attack. Not allowed against the Boss |
| Boss Enrage | — | **New.** The Boss hits 30% harder below half health |

Other battle changes:

- **Danger warning:** before a battle, the game estimates the damage the
  player would take if they only attacked. If that is more than their
  current HP, it shows the numbers and asks "Fight anyway? (Y/N)".
- **Animations:** a "VS" intro, attacks that travel across the screen,
  hits that shake, HP bars that drain or refill, effects for items, defend,
  paralysis and enrage, and blinking VICTORY / DEFEAT banners. Animations
  turn off automatically when the output is not a real terminal.
- **Coloured HP bars:** green above 60%, yellow from 30–60%, red below 30%.

### 3.3 Winning, losing and progression

| Rule | Original | Revised |
|------|----------|---------|
| Rank unlocks | Beginner 0–2 wins, Adventurer 3–5, Elite 6–8, Master 9+ | Unchanged |
| Level completion reward | +5 ATK and bonus gold (50 / 100 / 500) | +5 ATK, **+20 Max HP**, bonus gold (40 / 80 / 150) |
| HP after a battle | Restored to full on the next dungeon visit if the player lost | Never refills by itself; rest or use potions |
| Defeat | Enemy healed to full; player restored to full HP later | Lose 25% of gold, wake up with 50% HP, queue cleared. The enemy keeps the damage it took and regains only 25% of its Max HP, so each attempt gets closer |
| Fleeing | — | No rewards; the enemy recovers completely |
| End of the game | None | Defeat the Boss, then choose **Escape Dungeon** for +500 score and the **Victorious** status |
| Player statuses | Active, In Battle, Defeated | Active, In Battle, Defeated, **Escaped**, **Victorious** |

### 3.4 Camp, shop and items

- The **Dungeon Shop** moved from the main player menu into the dungeon
  camp. You can buy several of an item at once and must confirm each
  purchase.
- **Rest at Camp** (new): pay 40 Gold to restore 50% of Max HP.
- Each item now has a **carry limit**.
- Items are stored as records in `item_records.txt`, so the Administrator
  can add, edit or remove them.

| Item | Original | Revised |
|------|----------|---------|
| Health Potion | +30 HP, 25 Gold | Restores 35% of Max HP, 30 Gold, carry 5 |
| Strength Tonic | Next attack +25%, 75 Gold | Next 3 attacks +50%, 70 Gold, carry 3 |
| Paralysis Bomb | 75% chance to block the next counterattack, 150 Gold | 75% chance the enemy loses its next 2 turns, 110 Gold, carry 2 |
| Poison Dagger | 25–35 damage, 250 Gold | 30–40 damage that never misses, 120 Gold, carry 2 |
| Smoke Bomb | — | **New.** Guaranteed escape from a battle, 40 Gold, carry 2 |

### 3.5 Usability

- The camp and battle screens start on a cleared terminal each turn.
- **Camp screen panel:** HP bar, current room, the queue, the top of the
  action stack, and rank with the next goal.
- **Tables:** every list of records is shown as a bordered table. Long text
  wraps inside its cell and numbers line up on the right.
- **Input checking:** numbers must be in range and text must not be blank.
  An invalid menu option shows a message and asks again without an extra
  Enter press.
- **How to Play** rewritten to cover exploring, the queue, every battle
  action, camp, defeat and items.
- The player's main menu shows HP, ATK, Gold, Rank, Status and how many
  enemies are waiting.

---

## 4. New Administrator features

The original had no administrator. Logging in as `admin` (password
`admin123`) now opens the **Admin Menu**.

1. **Dashboard:** number of players, enemies (per difficulty), items, rooms,
   passages and questions; total battles, wins, losses and escapes; who has
   beaten the Boss or escaped the dungeon; top scorer; latest battle.
2. **Profiling (File Maintenance):** Add, View All, Search, Update and Delete
   for:
   - player accounts
   - enemies
   - items
   - rooms, with extra options to add or remove passages and view the map
   - challenge questions

   Safety checks: an admin cannot delete the account they are logged in
   with, the entrance room cannot be deleted, a room with enemies cannot be
   deleted, a deleted enemy is removed from every saved queue, and removing
   a passage warns if some rooms can no longer be reached.
3. **Transactions (Game Setup and Management):**
   - View Player Progress, including that player's map
   - Reset Player Game Data
   - Assign Starting Items
   - Set Enemy Difficulty, optionally scaling HP and attack by a percentage
   - View Battle History, filtered by player
4. **Report Generation:** nine reports, each of which can be exported to a
   text file in `reports/`:
   - Player Statistics
   - Battle Wins and Losses
   - Enemies Defeated
   - Player Score Ranking
   - Boss Defeat Status
   - Battle History
   - Available Items
   - Enemy Difficulty
   - Dungeon Map

---

## 5. Records and files

| File | Original | Revised |
|------|----------|---------|
| `player_accounts.txt` | Accounts with 4 fixed item columns | Accounts with role, inventory, saved queue and enemy wounds |
| `enemy_records.txt` | — (enemies were written in the code) | **New** |
| `item_records.txt` | — (items were written in the code) | **New** |
| `room_records.txt` | — | **New** (graph vertices) |
| `room_connections.txt` | — | **New** (graph edges) |
| `question_records.txt` | — | **New** |
| `battle_history_records.txt` | — | **New:** a permanent record of every battle result |
| `dungeon_game_records.txt` | Written by Save Game | Written by Save Game, now including the dungeon map |
| `battle_activity_log.txt` | Written by Save Game | Unchanged |
| `reports/` | — | **New:** exported reports |

- **Default data:** if a record file is missing, the game creates it again
  with the default records.
- **Readable columns:** the record files are written with padded columns
  and a header line, so they can be read like a table. Spaces are ignored
  when the files are loaded.
- **Old saves still work:** accounts saved by the original version load
  correctly. The four item columns become the new inventory, and a default
  admin account is added if there is none.
- **No demo players:** the game starts with only the admin account. Players
  create their own accounts with "Create New Account".

---

## 6. Game balance

The original enemies all had 100 HP (the Boss 200), so only their attack
told them apart. The Boss's attack of 50 could take half of a new player's
HP in one hit. The revised values were tuned with a simulation, so that
simply spamming Attack and potions usually fails, while planning purchases,
resting, defending and timing items lets a careful player clear the
dungeon.

### Starting player

| Stat | Original | Revised |
|------|----------|---------|
| HP / Max HP | 100 / 100 | 100 / 100 |
| Attack | 15 | 14 |
| Gold | 0 | 60 |
| Items | None | 2 Health Potions |

### Enemies (HP / ATK / Gold / Score)

| Enemy | Difficulty | Original | Revised |
|-------|------------|----------|---------|
| Gravefang Rat | Weak | 100 / 3 / 30 / 40 | 55 / 7 / 25 / 40 |
| Hollowbone Goblin | Weak | 100 / 6 / 50 / 80 | 70 / 9 / 30 / 60 |
| Ashen Ghoul | Weak | 100 / 9 / 60 / 100 | 85 / 11 / 35 / 80 |
| Ironjaw Reaver | Intermediate | 100 / 12 / 120 / 70 | 105 / 12 / 50 / 100 |
| Boneguard Executioner | Intermediate | 100 / 15 / 150 / 80 | 120 / 13 / 60 / 120 |
| Hellchain Marauder | Intermediate | 100 / 18 / 180 / 90 | 135 / 14 / 70 / 140 |
| Dreadfang Berserker | Strong | 100 / 21 / 210 / 110 | 150 / 16 / 85 / 180 |
| Abyssal Death Knight | Strong | 100 / 24 / 240 / 120 | 165 / 17 / 95 / 200 |
| Soulreaper Wraith | Strong | 100 / 27 / 270 / 130 | 180 / 18 / 110 / 220 |
| Vharok, the World Eater | Boss | 200 / 50 / 500 / 250 | 320 / 22 / 300 / 600 |

Other changes:

- **Enemy critical chance:** Weak 5%, Intermediate 8%, Strong 10%, Boss
  12%. Original: 8 / 8 / 10 / 15%.
- **Enemy critical damage:** ×1.5. Original: ×2.
- **Score rewards** now rise with difficulty. In the original, some
  Intermediate enemies gave less score than Weak ones.
- **Code layout:** all balance values are named constants at the top of
  the file, so they can be adjusted in one place.

---

## 7. Moved or removed

| Original feature | What happened |
|------------------|---------------|
| "Add Enemy to Lineup" by typing an Enemy ID | Kept as **Add Enemy to Queue**; the list is a table of only the enemies that can be queued now |
| "Attack Current Enemy" and "Use Item" in the dungeon menu | Moved to the separate **battle menu** |
| "Dungeon Shop" in the player main menu | Moved into the **dungeon camp** |
| "Player Account Information" in the player menu | Moved to **Admin → Profiling → Player Account Maintenance** |
| "Undo Last Log Entry" | Renamed **Remove Latest Log Entry (does not undo the action)** |
| Separate `potions`, `tonics`, `bombs`, `daggers` fields | Replaced by one inventory linked to the item records |
| Enemy and item lists written in the code | Moved to editable record files |
| Default `player` test account | Removed; only the admin account is built in |
