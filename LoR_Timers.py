import json
import os
import time  # Import time module

class LoRTimers:
    def __init__(self, api_caller, data_folder="Data"):
        self.api_caller = api_caller
        self.current_champion = None
        self.previous_champion = None
        self.champion_mapping = self.load_champion_mapping(data_folder)

        self.previous_game_ID = None  # Track previous game ID
        self.waiting_for_deck = False  # Track if waiting for deck to return
        self.last_deck_snapshot = None  # Store last known deck
        self.deck_missing_count = 0  # Count how many times deck has been missing
        self.pause = False

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
        deck = self.api_caller.get_deck()
        if not deck:
            print("[WARNING] No deck data available. Champion cannot be determined.")
            return

        print("Determining champion from deck...")
        for card_code in deck.keys():
            if card_code in self.champion_mapping:
                self.current_champion = self.champion_mapping[card_code]
                print(f"[INFO] Champion detected: {self.current_champion}")
                self.deck_missing_count = 0
                return  # Stop iterating after the first champion is found

        print("[WARNING] No champion found in deck. Defaulting to 'Unknown Champion'.")

    def update_game_state(self):
        """Update game state and track champion selection across different game phases."""
        self.api_caller.update_all_data()

        game_result = self.api_caller.get_game_result()
        game_id = game_result.get("GameID", None)
        deck = self.api_caller.get_deck()

        # paused until deck is seen again
        if self.pause and deck is None:
            print("in a loading/victory screen")
            return
        else:
            self.pause = False

        # **Step 1: Detect when a new game starts (GameID increases)**
        if game_id is not None and game_id != self.previous_game_ID:
            print(f"[INFO] GameID changed: {self.previous_game_ID} -> {game_id}")
            self.previous_game_ID = game_id
            self.waiting_for_deck = True  # IGNORE next deck disappearance
            self.last_deck_snapshot = deck if deck else None  # Store last known deck
            self.deck_missing_count = 0  # Reset missing deck counter
            return  # Ignore any further checks in this loop iteration

        # **Step 2: Ignore deck disappearance right after game ID changes**
        if self.waiting_for_deck:
            if deck is None:
                # the deck just became undefined
                # now we need to wait until it is defined again
                self.waiting_for_deck = False
                self.pause = True
                return

        # **Step 3: Handle missing deck logic**
        if deck is None:
            self.deck_missing_count += 1
            print(f"[INFO] Deck is missing ({self.deck_missing_count} loops).")

            # If deck has been missing for multiple loops, assume we left adventure
            if self.deck_missing_count >= 4:
                print("[WARNING] Deck has been missing for too long. Assuming player left adventure.")
                self.current_champion = None  # Reset champion
                self.waiting_for_deck = False  # Reset waiting state
            return  # Wait until deck returns before doing anything

        # **Step 4: Handle deck reappearance**
        if deck is not None:
            self.deck_missing_count = 0  # Reset counter

        # **Step 5: Determine champion from deck if needed**
        if self.current_champion is None:
            self.determine_champion_from_deck()

        print(f"Current Champion: {self.current_champion}")


if __name__ == "__main__":
    from api_caller import APICaller

    api = APICaller(None, None)
    game = LoRTimers(api)

    # Keep running to continuously update game state with a 2-second delay
    while True:
        game.update_game_state()
        time.sleep(2)  # Pause for 2 seconds before the next update
