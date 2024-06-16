import urllib.request
import json
from time import sleep, time
from datetime import datetime
import os

class APICaller:
    def __init__(self, game_durations, refresh_display_callback, champion_deck_file='champion_decks.json', game_durations_file='game_durations.json', champion_code_file='champion_to_code.json', active_menu_durations_file='active_menu_durations.json'):
        self.game_data_link = "http://127.0.0.1:21337/positional-rectangles"
        self.deck_link = "http://127.0.0.1:21337/static-decklist"
        self.game_result_link = "http://127.0.0.1:21337/game-result"
        self.game_data = {}
        self.cards_data = {}
        self.game_result = {}
        self.champion = "Unknown Champion"
        self.in_game = False
        self.game_start_time = None
        self.game_durations = game_durations
        self.refresh_display_callback = refresh_display_callback

        # Active menu tracking variables
        self.in_active_menu = False
        self.active_menu_start_time = None
        self.total_active_menu_time = 0
        self.active_menu_transitions = 0
        self.active_menu_durations = []

        # Load mappings and durations from files
        with open(champion_deck_file, 'r') as file:
            self.champion_deck_mapping = json.load(file)

        with open(champion_code_file, 'r') as file:
            self.champion_code_mapping = json.load(file)

        self.champion_deck_file = champion_deck_file
        self.game_durations_file = game_durations_file
        self.active_menu_durations_file = active_menu_durations_file

        # Load existing game durations if the file exists
        if os.path.exists(self.game_durations_file):
            with open(self.game_durations_file, 'r') as file:
                try:
                    self.game_durations.update(json.load(file))
                except json.JSONDecodeError:
                    print(f"Error: {self.game_durations_file} is empty or not properly formatted. Initializing empty game durations.")
                    self.game_durations = {}

        # Load existing active menu durations if the file exists
        if os.path.exists(self.active_menu_durations_file):
            with open(self.active_menu_durations_file, 'r') as file:
                try:
                    self.active_menu_durations = json.load(file)
                    self.total_active_menu_time = sum(self.active_menu_durations)
                    self.active_menu_transitions = len(self.active_menu_durations)
                except json.JSONDecodeError:
                    print(f"Error: {self.active_menu_durations_file} is empty or not properly formatted. Initializing empty active menu durations.")
                    self.active_menu_durations = []

    def find_champion(self, first_card_code):
        for champion, card_code in self.champion_code_mapping.items():
            if first_card_code == card_code:
                return champion
        return "Unknown Champion"

    def call_api(self, stop_event):
        while not stop_event.is_set():
            try:
                game_url = urllib.request.urlopen(self.game_data_link)
                self.game_data = json.loads(game_url.read().decode())

                deck_url = urllib.request.urlopen(self.deck_link)
                self.cards_data = json.loads(deck_url.read().decode())

                # Determine if in game or in menus
                in_menus = self.game_data.get("GameState") == "Menus"
                cards_in_deck = self.cards_data.get("CardsInDeck")

                if in_menus:
                    if cards_in_deck:
                        first_card_code = next(iter(cards_in_deck.keys()), None)
                        if first_card_code:
                            self.champion = self.find_champion(first_card_code)
                            # Entering active menu
                            if not self.in_active_menu:
                                self.in_active_menu = True
                                self.active_menu_start_time = time()
                                print(f"Entered active menu, playing as {self.champion}")
                    else:
                        self.champion = "In Menus"
                        # Exiting active menu to inactive menu
                        if self.in_active_menu:
                            self.in_active_menu = False
                            print(f"Discarding active menu time as transitioned to inactive menu.")
                else:
                    # Exiting active menu
                    if self.in_active_menu:
                        self.in_active_menu = False
                        active_menu_duration = time() - self.active_menu_start_time
                        self.total_active_menu_time += active_menu_duration
                        self.active_menu_transitions += 1
                        self.active_menu_durations.append(active_menu_duration)
                        self.save_active_menu_durations()
                        self.refresh_display_callback()
                        print(f"Exited active menu, duration: {active_menu_duration} seconds")

                    if not self.in_game:
                        # Game has started
                        self.in_game = True
                        self.game_start_time = time()
                        print(f"Game started, playing as {self.champion}")

                if not in_menus and self.in_game:
                    if not self.game_data.get("Rectangles"):
                        # Game has ended
                        self.in_game = False
                        game_duration = time() - self.game_start_time
                        game_id = self.game_result.get("GameID", -1)
                        if game_id != -1:
                            game_record = {
                                "timestamp": datetime.now().isoformat(),
                                "duration": game_duration,
                                "game_id": game_id,
                                "DrewChampionTurnOne": False
                            }
                            if self.champion not in self.game_durations:
                                self.game_durations[self.champion] = []
                            self.game_durations[self.champion].append(game_record)
                            self.save_game_durations()
                            self.refresh_display_callback()
                            print(f"Game ended, played as {self.champion}, duration: {game_duration} seconds, GameID: {game_id}")

            except urllib.error.URLError as e:
                print(f"Failed to connect to the API: {e.reason}")
                sleep(5)
            except json.JSONDecodeError:
                print("Failed to decode the JSON response from the API.")
                sleep(5)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                sleep(5)

            sleep(1)

    def save_game_durations(self):
        with open(self.game_durations_file, 'w') as file:
            json.dump(self.game_durations, file, indent=4)

    def save_active_menu_durations(self):
        with open(self.active_menu_durations_file, 'w') as file:
            json.dump(self.active_menu_durations, file, indent=4)

    def clear_all_data(self):
        self.game_durations.clear()
        self.active_menu_durations.clear()
        self.total_active_menu_time = 0
        self.active_menu_transitions = 0
        self.save_game_durations()
        self.save_active_menu_durations()
        self.refresh_display_callback()
        print("Cleared all game durations data.")

    def get_champion(self):
        return self.champion

    def get_average_active_menu_time(self):
        if self.active_menu_transitions > 0:
            return self.total_active_menu_time / self.active_menu_transitions
        return 0

    def get_current_active_menu_time(self):
        if self.in_active_menu:
            return time() - self.active_menu_start_time
        return 0
