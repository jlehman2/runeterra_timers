import threading
from api_caller import APICaller
from game_durations_display import GameDurationsDisplay

class MainApp:
    def __init__(self):
        self.game_durations = {}
        self.stop_event = threading.Event()

        # Initialize APICaller first
        self.api_caller = APICaller(self.game_durations, self.refresh_display)

        # Initialize GameDurationsDisplay after APICaller
        self.display = GameDurationsDisplay(self.game_durations, self.get_current_deck, self.stop_event, self.clear_all_data)

    def start(self):
        self.api_thread = threading.Thread(target=self.api_caller.call_api, args=(self.stop_event,))
        self.api_thread.start()

        self.display.show()
        self.stop_event.set()  # Ensure that threads are stopped if the Tkinter main loop ends

        # Wait for threads to finish
        self.api_thread.join()

    def get_current_deck(self):
        return self.api_caller.get_champion()  # Assuming this method returns the current deck or champion

    def clear_all_data(self):
        self.api_caller.clear_all_data()

    def refresh_display(self):
        self.display.refresh_data()

if __name__ == "__main__":
    app = MainApp()
    app.start()
