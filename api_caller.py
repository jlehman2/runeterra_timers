import urllib.request
import json
from time import sleep, time
from datetime import datetime
import os


class APICaller:
    def __init__(self, game_durations, refresh_display_callback, champion_deck_file='champion_decks.json', game_durations_file='game_durations.json', champion_code_file='champion_to_code.json'):
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

        with open(champion_deck_file, 'r') as file:
            self.champion_deck_mapping = json.load(file)

        with open(champion_code_file, 'r') as file:
            self.champion_code_mapping = json.load(file)

        self.champion_deck_file = champion_deck_file
        self.game_durations_file = game_durations_file

        # Load existing game durations if the file exists
        if os.path.exists(self.game_durations_file):
            with open(self.game_durations_file, 'r') as file:
                self.game_durations.update(json.load(file))

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
                    else:
                        self.champion = "In Menus"
                else:
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

    def clear_all_data(self):
        self.game_durations.clear()
        self.save_game_durations()
        self.refresh_display_callback()
        print("Cleared all game durations data.")

    def get_champion(self):
        return self.champion
