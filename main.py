import urllib.request
import json
from time import sleep, time
import threading
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk

class APICaller:
    def __init__(self, champion_deck_file='champion_decks.json', game_durations_file='game_durations.json'):
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
        self.game_durations = {}
        self.previous_deck = {}

        with open(champion_deck_file, 'r') as file:
            self.champion_deck_mapping = json.load(file)

        self.champion_deck_file = champion_deck_file
        self.game_durations_file = game_durations_file

        # Load existing game durations if the file exists
        if os.path.exists(self.game_durations_file):
            with open(self.game_durations_file, 'r') as file:
                self.game_durations = json.load(file)
        else:
            self.game_durations = {}

    def find_champion(self, cards_in_deck):
        for champion, deck in self.champion_deck_mapping.items():
            if all(cards_in_deck.get(card, 0) >= count for card, count in deck.items()):
                return champion
        return "Unknown Champion"

    def decks_are_similar(self, deck1, deck2):
        if not deck1 or not deck2:
            return False
        common_cards = set(deck1.keys()).intersection(deck2.keys())
        changes = sum(abs(deck1[card] - deck2[card]) for card in common_cards)
        new_cards = len(set(deck1.keys()).difference(deck2.keys())) + len(set(deck2.keys()).difference(deck1.keys()))
        total_changes = changes + new_cards
        return total_changes < len(deck1) * 0.2  # Arbitrary threshold for similarity

    def call_api(self):
        while True:
            try:
                game_url = urllib.request.urlopen(self.game_data_link)
                self.game_data = json.loads(game_url.read().decode())

                deck_url = urllib.request.urlopen(self.deck_link)
                self.cards_data = json.loads(deck_url.read().decode())

                game_result_url = urllib.request.urlopen(self.game_result_link)
                self.game_result = json.loads(game_result_url.read().decode())

                # Identify the champion if CardsInDeck is not None
                cards_in_deck = self.cards_data.get("CardsInDeck")
                if cards_in_deck is not None:
                    if self.decks_are_similar(cards_in_deck, self.previous_deck):
                        self.champion = self.current_champion
                    else:
                        self.champion = self.find_champion(cards_in_deck)
                    self.previous_deck = cards_in_deck.copy()

                # Determine if in game or in menus
                if self.game_data.get("Rectangles"):
                    if not self.in_game:
                        # Game has started
                        self.in_game = True
                        self.game_start_time = time()
                        self.current_champion = self.champion
                        print(f"Game started, playing as {self.current_champion}")
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
                            else:
                                print(f"Game ended, but result was a loss or surrender. Not saving the duration.")
                    print("Currently in menus")

            except urllib.error.URLError as e:
                print(f"Failed to connect to the API: {e.reason}")
                sleep(5)  # Wait for a while before trying again
            except json.JSONDecodeError:
                print("Failed to decode the JSON response from the API.")
                sleep(5)  # Wait for a while before trying again
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                sleep(5)  # Wait for a while before trying again

            sleep(1)

    def save_game_durations(self):
        with open(self.game_durations_file, 'w') as file:
            json.dump(self.game_durations, file, indent=4)

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
        print("Removed all saved timers from game durations.")


class GameDurationsDisplay:
    def __init__(self, game_durations):
        self.game_durations = game_durations

    def display_game_durations_info(self):
        root = tk.Tk()
        root.title("Game Durations Info")

        tree = ttk.Treeview(root)
        tree["columns"] = ("fastest_time", "average_time")
        tree.heading("#0", text="Champion")
        tree.heading("fastest_time", text="Fastest Time")
        tree.heading("average_time", text="Average Time")

        for champion, games in self.game_durations.items():
            if not games:
                continue
            durations = [game['duration'] for game in games]
            fastest_time = min(durations)
            average_time = sum(durations) / len(durations)
            tree.insert("", "end", text=champion, values=(f"{fastest_time:.2f}", f"{average_time:.2f}"))

        tree.pack(expand=True, fill="both")
        root.mainloop()


def main():
    api_caller = APICaller()
    display = GameDurationsDisplay(api_caller.game_durations)

    while True:
        print("\nChoose an action:")
        print("1. Remove all saved timers")
        print("2. Add champion deck")
        print("3. Update misc field")
        print("4. Get game data")
        print("5. Get cards data")
        print("6. Get game result")
        print("7. Get current champion")
        print("8. Display game durations info")
        print("9. Start API call loop")
        print("0. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            api_caller.remove_all_saved_timers()
        elif choice == '2':
            champion_name = input("Enter the champion name: ")
            deck_mapping = input("Enter the deck mapping as a JSON string: ")
            try:
                deck_mapping = json.loads(deck_mapping)
                api_caller.add_champion_deck(champion_name, deck_mapping)
            except json.JSONDecodeError:
                print("Invalid JSON format.")
        elif choice == '3':
            champion_name = input("Enter the champion name: ")
            game_id = int(input("Enter the game ID: "))
            field_name = input("Enter the field name: ")
            field_value = input("Enter the field value: ")
            api_caller.update_misc_field(champion_name, game_id, field_name, field_value)
        elif choice == '4':
            print(api_caller.get_game_data())
        elif choice == '5':
            print(api_caller.get_cards_data())
        elif choice == '6':
            print(api_caller.get_game_result())
        elif choice == '7':
            print(api_caller.get_champion())
        elif choice == '8':
            display.display_game_durations_info()
        elif choice == '9':
            thread = threading.Thread(target=api_caller.call_api)
            thread.start()
            print("API call loop started in a separate thread.")
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
