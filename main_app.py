import threading
from api_caller import APICaller
from game_durations_display import GameDurationsDisplay

class MainApp:
    def __init__(self):
        self.api_caller = APICaller()
        self.display = GameDurationsDisplay(self.api_caller.game_durations)

    def start(self):
        api_thread = threading.Thread(target=self.api_caller.call_api)
        api_thread.start()

        user_input_thread = threading.Thread(target=self.user_input_loop)
        user_input_thread.start()

        self.display.show()

    def user_input_loop(self):
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
            print("0. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                self.api_caller.remove_all_saved_timers()
            elif choice == '2':
                champion_name = input("Enter the champion name: ")
                deck_mapping = input("Enter the deck mapping as a JSON string: ")
                try:
                    deck_mapping = json.loads(deck_mapping)
                    self.api_caller.add_champion_deck(champion_name, deck_mapping)
                except json.JSONDecodeError:
                    print("Invalid JSON format.")
            elif choice == '3':
                champion_name = input("Enter the champion name: ")
                game_id = int(input("Enter the game ID: "))
                field_name = input("Enter the field name: ")
                field_value = input("Enter the field value: ")
                self.api_caller.update_misc_field(champion_name, game_id, field_name, field_value)
            elif choice == '4':
                print(self.api_caller.get_game_data())
            elif choice == '5':
                print(self.api_caller.get_cards_data())
            elif choice == '6':
                print(self.api_caller.get_game_result())
            elif choice == '7':
                print(self.api_caller.get_champion())
            elif choice == '8':
                self.display.refresh_data()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    app = MainApp()
    app.start()
