import requests

class APICaller:
    def __init__(self, game_durations, refresh_display_callback):
        self.game_durations = game_durations
        self.refresh_display_callback = refresh_display_callback

        # API Endpoints
        self.game_data_link = "http://127.0.0.1:21337/positional-rectangles"
        self.deck_link = "http://127.0.0.1:21337/static-decklist"
        self.game_result_link = "http://127.0.0.1:21337/game-result"

        # Data Storage
        self.game_data = {}
        self.cards_data = {}
        self.game_result = {}

        # Game State Tracking
        self.in_game = False
        self.game_start_time = None
        self.previous_game_state = None  # NEW: Track previous state
        self.deck_loaded = False  # NEW: Track if deck has been detected

    def fetch_game_data(self):
        """Fetch live positional-rectangles game data."""
        try:
            response = requests.get(self.game_data_link, timeout=1)
            if response.status_code == 200:
                self.game_data = response.json()

                # Track game state changes
                current_state = self.get_game_state()
                if current_state != self.previous_game_state:
                    print(f"[INFO] Game state changed: {self.previous_game_state} -> {current_state}")
                    self.previous_game_state = current_state

                self.in_game = current_state == "InProgress"
            else:
                print(f"[ERROR] Failed to fetch game data: {response.status_code}")
        except requests.RequestException as e:
            print(f"[ERROR] Error fetching game data: {e}")

    def fetch_deck_data(self):
        """Fetch the static decklist during an active game."""
        try:
            response = requests.get(self.deck_link, timeout=1)
            if response.status_code == 200:
                self.cards_data = response.json()

                # Check if deck is available
                if self.cards_data.get("CardsInDeck") is not None:
                    if not self.deck_loaded:
                        self.deck_loaded = True
                        print("[INFO] Deck detected! Cards have been loaded.")
                else:
                    self.deck_loaded = False  # Deck is not yet loaded

            else:
                print(f"[ERROR] Failed to fetch deck data: {response.status_code}")
        except requests.RequestException as e:
            print(f"[ERROR] Error fetching deck data: {e}")

    def fetch_game_result(self):
        """Fetch the result of the most recently completed game."""
        try:
            response = requests.get(self.game_result_link, timeout=1)
            if response.status_code == 200:
                self.game_result = response.json()
                print(f"[INFO] Game result updated: {self.game_result}")
            else:
                print(f"[ERROR] Failed to fetch game result: {response.status_code}")
        except requests.RequestException as e:
            print(f"[ERROR] Error fetching game result: {e}")

    def update_all_data(self):
        """Update all API data."""
        self.fetch_game_data()
        self.fetch_deck_data()
        self.fetch_game_result()

        if self.refresh_display_callback:
            self.refresh_display_callback()

    # Game State Methods
    def get_game_state(self):
        """Return the current game state."""
        return self.game_data.get("GameState", "Unknown")

    def get_opponent_name(self):
        """Return the opponent's name if in-game."""
        return self.game_data.get("OpponentName", "Unknown")

    def get_deck(self):
        """Return the deck list if available."""
        return self.cards_data.get("CardsInDeck", {})

    def get_game_result(self):
        """Return game result details."""
        return self.game_result if self.game_result else {"GameID": None, "LocalPlayerWon": None}

    def get_card_positions(self):
        """Return card positions for the local player."""
        return [card for card in self.game_data.get("Rectangles", []) if card.get("LocalPlayer", False)]


if __name__ == "__main__":
    api = APICaller(None, None)
    api.update_all_data()
    print("Game State:", api.get_game_state())
    print("Opponent Name:", api.get_opponent_name())
    print("Deck:", api.get_deck())
    print("Game Result:", api.get_game_result())
