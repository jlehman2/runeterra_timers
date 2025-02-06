import json
import os
import time
import threading
import tkinter as tk

from api_caller import APICaller
from gui import GameDurationsDisplay

class GameState:
    MENU = "Menus"
    IN_PROGRESS = "InProgress"

class LoRTimers:
    def __init__(self, api_caller, stop_event, data_folder="Data"):
        self.deck_missing_count = None

        self.previous_game_ID = None
        self.game_id = None

        self.player_won = None
        self.previous_game_result = None

        self.api_caller = api_caller

        self.current_champion = None
        self.previous_champion = None

        self.champion_mapping = self.load_champion_mapping(data_folder)

        self.previous_game_ID = None  # Track previous game ID
        self.previous_game_state = None  # Track previous game state
        self.current_state = None
        self.waiting_for_deck = False
        self.last_deck_snapshot = None
        self.pause = False
        self.stop_event = stop_event

        self.menu_start_time = None
        self.champion_start_time = None
        self.menu_duration = 0
        self.champion_duration = 0
        self.game_durations = {}

        self.pending_champion_time = None

        self.deck = None
        self.previous_deck = None
        self.deck_missing_count = 0

    @property
    def current_champion_time(self):
        """Returns the currently running champion timer duration."""
        if self.champion_start_time:
            return time.time() - self.champion_start_time
        return self.champion_duration  # If stopped, return last recorded time

    @property
    def total_menu_time(self):
        """Returns the total menu duration."""
        if self.menu_start_time:
            return self.menu_duration + (time.time() - self.menu_start_time)
        return self.menu_duration

    def load_champion_mapping(self, data_folder):
        """Load champion mapping from JSON file."""
        champion_mapping_path = os.path.join(data_folder, "champion_mapping.json")
        if not os.path.exists(champion_mapping_path):
            print(f"[ERROR] Champion mapping file '{champion_mapping_path}' not found.")
            return {}

        with open(champion_mapping_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("[ERROR] Could not decode champion mapping JSON.")
                return {}

    def determine_champion_from_deck(self):
        """Determine the champion being played from the static decklist."""
        if self.deck is None:
            print("[WARNING] No deck data available. Champion cannot be determined.")
            return
        for card_code in self.deck.keys():
            if card_code in self.champion_mapping:
                found = self.champion_mapping[card_code]
                if self.current_champion == found:
                    # dont need to do anything
                    return
                else:
                    print("[Info] Updated previous champion")
                    self.previous_champion = self.current_champion
                self.current_champion = found
                print(f"[INFO] Champion detected: {self.current_champion}")
                self.deck_missing_count = 0
                return  # Stop iterating after the first champion is found

        print("[WARNING] No champion found in deck'.")

    def update_fields(self):
        self.api_caller.update_all_data()
        self.player_won = self.api_caller.game_result.get("LocalPlayerWon", None)
        self.game_id = self.api_caller.game_result.get("GameID", None)

        self.previous_deck = self.deck
        self.deck = self.api_caller.get_deck()

        self.current_state = self.api_caller.get_game_state()

    def track_state_changes(self):
        """Track changes in game state, deck, and game ID before handling them."""
        self.update_fields()  # Get latest API data

        # Detect changes
        state_changed = self.current_state != self.previous_game_state
        game_id_changed = self.game_id is not None and self.game_id != self.previous_game_ID
        deck_changed = self.deck != self.previous_deck

        # Log detected changes
        if state_changed:
            print(f"[Tracker] Game state changed: {self.previous_game_state} -> {self.current_state}")

            # start champ timers right away
            if self.current_champion and self.current_state == GameState.IN_PROGRESS:
                self.start_champion_timer()


        if game_id_changed:
            print(f"[Tracker] GameID changed: {self.previous_game_ID} -> {self.game_id}")
            print(f"[Tracker] player won: {self.player_won}")
            if self.player_won is not None:
                self.start_menu_timer()
            if self.previous_game_ID is not None:
                self.waiting_for_deck = True
                self.deck_missing_count = 0

        if deck_changed:
            print("[Handled] Deck changed")
            self.determine_champion_from_deck()


        return state_changed, game_id_changed, deck_changed

    def handle_timers(self, state_changed, game_id_changed, deck_changed):
        """Handles timers based on tracked changes but does NOT modify state tracking variables."""

        if state_changed and self.previous_game_state == GameState.IN_PROGRESS:
            print("[INFO] Game ended. Transitioning to menu...")
            self.start_menu_timer()

        # Transition: MENU → IN-GAME (New Game Started)
        elif state_changed and self.previous_game_state == GameState.MENU and self.current_state == GameState.IN_PROGRESS:
            print("[INFO] Entering a game...")
            self.start_champion_timer()

        ## Deck changed in MENU (Switched deck or exited adventure)
        #elif deck_changed and self.current_state == GameState.MENU:
        #    print("[INFO] Deck changed or adventure ended. Resetting champion timer.")
        #    self.champion_start_time = None
        #    self.champion_duration = 0  # Reset invalid champion times
        #    self.start_menu_timer()

        elif state_changed and self.current_state == GameState.IN_PROGRESS and self.previous_game_state is None:

            # speed timers started in the middle of a game already running
            self.start_champion_timer()

    def start_champion_timer(self):
        """Start champion timer and ensure the menu timer stops."""
        # Starting champion timer should always stop menu timer
        clock = time.time()
        if self.menu_start_time:
            self.stop_menu_timer(clock)

        if not self.champion_start_time:
            print(f"[TIMER] Champion timer started for {self.current_champion}.")
            self.champion_start_time = clock

            # Restore pending time if a loss happened before
            if self.pending_champion_time:
                print(f"[INFO] Restoring {self.pending_champion_time:.2f} sec from previous loss.")
                self.champion_start_time -= self.pending_champion_time  # Offset start time
                self.pending_champion_time = None  # Clear pending time


    def stop_champion_timer(self, clock):
        """Stop champion timer, store the time, and decide what to do next."""
        if self.champion_start_time:
            session_duration = clock - self.champion_start_time
            self.champion_duration += session_duration
            self.champion_start_time = None
            print(f"[TIMER] {self.current_champion} session ended. Duration: {self.champion_duration:.2f} sec")

            if self.current_champion:
                if self.player_won:
                    # Save duration to game session list if won
                    print(f"[Saving] {self.current_champion} time for game {self.game_id}.")
                    self.game_durations.setdefault(self.current_champion, []).append(
                        {"duration": self.champion_duration})
                    self.champion_duration = 0  # Reset for next game
                else:
                    # If lost, carry over duration to the next session
                    print(f"[INFO] Loss detected. Carrying {self.champion_duration:.2f} sec to next game.")
                    self.pending_champion_time = self.champion_duration  # Store for next round
        else:
            print("[ERROR] champion timer stopped with no champion.]")

    def start_menu_timer(self):
        """Start menu timer and ensure the champion timer stops."""
        # Starting menu timer should always stop champion timer
        clock = time.time()
        if self.champion_start_time:
            self.stop_champion_timer(clock)

        if not self.menu_start_time:
            print("[TIMER] Menu timer started.")
            self.menu_start_time = clock

    def stop_menu_timer(self, end=time.time()):
        """Stop menu timer and add the duration to total menu time."""
        if self.menu_start_time:
            self.menu_duration += end - self.menu_start_time
            self.menu_start_time = None
            print(f"[TIMER] Menu session ended. Total menu time: {self.menu_duration:.2f} sec")

    def update_game_state(self):
        """Update game state and track champion selection across different game phases."""
        if self.stop_event.is_set():
            return

        state_changed, game_id_changed, deck_changed = self.track_state_changes()


        if state_changed:
            print(f"[Handle] Game state changed: {self.previous_game_state} -> {self.current_state}")

            # TODO add any menu state change handling
            self.handle_timers(state_changed, game_id_changed, deck_changed)

            self.previous_game_state = self.current_state

        # might not need this anymore
        #  Step 2: Handle Pause & Deck Tracking
        # we are waiting because of the menu pause after winning or losing a game
        if self.pause and self.deck is None:
            # start menu timer if it isnt already
            self.start_menu_timer()
            print("In a loading/victory screen")
            return
        else:
            self.pause = False

        if game_id_changed:
            print(f"[Handle] GameID changed: {self.previous_game_ID} -> {self.game_id}")

            # this is specifically the case that we were in a game when the game updates

            # TODO add any gameID handling we need


            # update prev champ
            self.previous_champion = self.current_champion
            self.previous_game_won = self.player_won
            self.previous_game_ID = self.game_id
            return

        if self.waiting_for_deck:
            if self.deck is None:
                self.waiting_for_deck = False
                self.pause = True
                return

        if self.deck is None and self.current_champion:
            self.deck_missing_count += 1
            print(f"[INFO] Deck is missing ({self.deck_missing_count} loops).")

            # this number is expirimental think of it like the watchdog for resetting everything
            if self.deck_missing_count >= 3:
                print("[WARNING] Deck has been missing for too long. Assuming player left adventure.")
                self.previous_champion = self.current_champion
                self.current_champion = None
                self.waiting_for_deck = False
                self.pause = False
                self.champion_start_time = None
                self.champion_duration = 0  # Reset invalid champion times
                self.start_menu_timer()
            return

    def run_game_loop(self):
        """Runs the main game loop continuously until stopped."""
        while not self.stop_event.is_set():
            self.update_game_state()

            # TODO update sleep as prefer although riot recomends no more then 1 per sec
            # but I have done 0.001 and been completely okay
            time.sleep(0.5)

    def stop(self):
        """Stops the loop and exits the application."""
        print("[INFO] Stopping application...")
        self.stop_event.set()


if __name__ == "__main__":
    stop_event = threading.Event()  # Shared stop event between game logic and GUI
    api = APICaller(None, None)
    game = LoRTimers(api, stop_event)

    # Start game state loop in a separate thread
    game_thread = threading.Thread(target=game.run_game_loop, daemon=True)
    game_thread.start()

    # Initialize GUI
    root = tk.Tk()
    # Bind Escape key to stop
    root.bind("<Escape>", lambda event: game.stop())
    root.protocol("WM_DELETE_WINDOW", game.stop)  # Handle window close event

    gui = GameDurationsDisplay(
        root=root,
        game_durations=game.game_durations,
        get_current_deck=lambda: game.current_champion,
        get_current_champion_time=lambda: game.current_champion_time,  # ✅ New
        get_menu_time=lambda: game.total_menu_time,  # ✅ New
        stop_event=stop_event,
        clear_data=lambda: game.champion_mapping.clear(),
        champion_data={}
    )
    gui.run()  # Run the GUI
