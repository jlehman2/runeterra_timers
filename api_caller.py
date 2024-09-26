import shutil
import urllib.request
import json
from time import sleep, time
from datetime import datetime
import os
class APICaller:
    def __init__(self, game_durations, refresh_display_callback, champion_deck_file='champion_decks.json', game_durations_file='game_durations.json', champion_code_file='champion_to_code.json'):
        self.game_data_link = "http://127.0.0.1:21337/positional-rectangles"
        self.game_data = {}
        self.deck_link = "http://127.0.0.1:21337/static-decklist"
        self.cards_data = {}
        self.game_result_link = "http://127.0.0.1:21337/game-result"
        self.game_result = {}
        self.champion = "Unknown Champion"
        self.current_champion = "Unknown Champion"
        self.in_game = False
        self.game_start_time = None
        self.game_durations = game_durations
        self.refresh_display_callback = refresh_display_callback
        self.previous_deck = {}

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

                game_result_url = urllib.request.urlopen(self.game_result_link)
                self.game_result = json.loads(game_result_url.read().decode())

                # Identify the champion by the first card in the deck
                cards_in_deck = self.cards_data.get("CardsInDeck")
                if cards_in_deck:
                    first_card_code = next(iter(cards_in_deck.keys()), None)
                    if first_card_code:
                        self.champion = self.find_champion(first_card_code)
                    self.previous_deck = cards_in_deck.copy()

                # Determine if in game or in menus
                if self.game_data.get("Rectangles"):
                    if not self.in_game:
                        # Game has started
                        self.in_game = True
                        self.game_start_time = time()
                        self.current_champion = self.champion
                        print(f"Game started, playing as {self.current_champion}")

                        # Save the image to the specified location
                        # uncomment if you want this script for obs
                        # self.save_champion_image(self.current_champion)

                else:
                    if self.in_game:
                        # Game has ended
                        self.in_game = False

                        # Check if the game result is valid
                        if self.game_result.get("GameID") != -1 and self.game_result.get("LocalPlayerWon") is not None:
                            # Only save the game duration if the local player won
                            if self.game_result["LocalPlayerWon"]:
                                game_duration = time() - self.game_start_time
                                game_record = {
                                    "timestamp": datetime.now().isoformat(),
                                    "duration": game_duration,
                                    "game_id": self.game_result["GameID"],
                                    "DrewChampionTurnOne": False  # Default value, can be updated later
                                }
                                if self.current_champion not in self.game_durations:
                                    self.game_durations[self.current_champion] = []
                                self.game_durations[self.current_champion].append(game_record)
                                self.save_game_durations()
                                print(f"Game ended, played as {self.current_champion}, duration: {game_duration} seconds, GameID: {self.game_result['GameID']}")
                                self.refresh_display_callback()  # Refresh the display after updating the data

            except urllib.error.URLError as e:
                print(f"Failed to connect to the API: {e.reason}")
                sleep(5)  # Wait for a while before trying again
            except json.JSONDecodeError:
                print("Failed to decode the JSON response from the API.")
                sleep(5)  # Wait for a while before trying again
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                sleep(5)  # Wait for a while before trying again

            sleep(2.1)

    def save_champion_image(self, champion_name):
        image_directory = "C:\\Users\\joela\\PycharmProjects\\LoR_Timers\\images"
        destination_path = os.path.join("C:\\Users\\joela\\AppData\\Roaming\\slobs-client\\Media", "current_champ.png")
        default_image = os.path.join(image_directory, "default.png")

        # Handle special case for Lux: Illuminated
        if champion_name.lower() == "lux: illuminated":
            original_image_file = "lux illuminated.png"
        else:
            original_image_file = f"{champion_name}.png"

        # List all files in the images directory
        files_in_directory = os.listdir(image_directory)

        # Perform a case-insensitive match for the champion image
        original_image_file = next((f for f in files_in_directory if f.lower() == original_image_file.lower()), None)

        if original_image_file:
            try:
                # Copy the champion-specific image from the images directory and save it as 'current_champ.png'
                shutil.copy(os.path.join(image_directory, original_image_file), destination_path)
                print(f"Saved {original_image_file} as {destination_path}")
            except Exception as e:
                print(f"An error occurred while saving the image: {e}")
        else:
            try:
                # If the champion image is not found, copy the default image instead
                shutil.copy(default_image, destination_path)
                print(f"{champion_name}.png not found. Saved default image as {destination_path}")
            except FileNotFoundError:
                print(f"Default image {default_image} not found.")
            except Exception as e:
                print(f"An error occurred while saving the default image: {e}")

    def save_game_durations(self):
        with open(self.game_durations_file, 'w') as file:
            json.dump(self.game_durations, file, indent=4)

    def clear_all_data(self):
        self.game_durations.clear()
        self.save_game_durations()
        self.refresh_display_callback()  # Refresh the display after clearing the data
        print("Cleared all game durations data.")

    def update_misc_field(self, champion_name, game_id, field_name, field_value):
        if champion_name in self.game_durations:
            for game_record in self.game_durations[champion_name]:
                if game_record["game_id"] == game_id:
                    game_record[field_name] = field_value
                    self.save_game_durations()
                    print(f"Updated {field_name} for game_id {game_id} of {champion_name} to {field_value}")
                    return
        print(f"Game record not found for champion: {champion_name}, game_id: {game_id}")

    def add_champion_deck(self, champion_name, deck_mapping):
        self.champion_deck_mapping[champion_name] = deck_mapping
        with open(self.champion_deck_file, 'w') as file:
            json.dump(self.champion_deck_mapping, file, indent=4)

    def get_game_data(self):
        return self.game_data

    def get_cards_data(self):
        return self.cards_data

    def get_game_result(self):
        return self.game_result

    def get_champion(self):
        return self.champion

    def remove_all_saved_timers(self):
        self.game_durations = {}
        self.save_game_durations()
        self.refresh_display_callback()  # Refresh the display after removing all timers
        print("Removed all saved timers from game durations.")
