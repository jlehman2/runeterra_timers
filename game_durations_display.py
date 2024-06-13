import tkinter as tk
from tkinter import ttk
from tkinter import font
import time
import random
import csv
from datetime import datetime
class GameDurationsDisplay:
    def __init__(self, game_durations, get_current_deck, stop_event, clear_data):
        self.game_durations = game_durations
        self.get_current_deck = get_current_deck
        self.stop_event = stop_event
        self.clear_data = clear_data

        self.root = tk.Tk()
        self.root.title("Game Durations Info")

        # Define custom fonts
        custom_font = font.Font(family="Consolas", size=16, weight="bold")
        small_font = font.Font(family="Consolas", size=10, weight="bold")

        self.current_deck_label = ttk.Label(self.root, text="Current Deck: ", font=custom_font)
        self.current_deck_label.pack()

        self.timer_frame = ttk.Frame(self.root)
        self.timer_frame.pack()

        self.timer_label = ttk.Label(self.timer_frame, text="Timer: 00:00:00", font=custom_font)
        self.timer_label.pack(side=tk.LEFT)

        self.restart_timer_button = ttk.Button(self.timer_frame, text="Reset", command=self.restart_timer)
        self.restart_timer_button.pack(side=tk.LEFT, padx=10)

        self.tree = ttk.Treeview(self.root)
        self.tree["columns"] = ("fastest_time", "average_time")
        self.tree.heading("#0", text="Champion")
        self.tree.heading("fastest_time", text="Fastest Time")
        self.tree.heading("average_time", text="Average Time")
        self.tree.pack(expand=True, fill="both")

        # Apply font to treeview items
        style = ttk.Style()
        style.configure("Treeview.Heading", font=custom_font)
        style.configure("Treeview", font=custom_font)

        self.clear_button = ttk.Button(self.root, text="Clear Data", command=self.clear_data)
        self.clear_button.pack()

        self.save_button = ttk.Button(self.root, text="Save", command=self.save_data)
        self.save_button.pack()

        self.developed_by_label = ttk.Label(self.root, text="Developed by lehmon", font=small_font)
        self.developed_by_label.pack(side=tk.LEFT, anchor='sw', padx=10, pady=10)

        self.start_time = time.time()
        self.update_timer()
        self.refresh_data()
        self.root.after(5000, self.refresh_data)  # Refresh every 5 seconds

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

    def update_timer(self):
        if self.stop_event.is_set():
            return
        elapsed_time = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.config(text=f"Timer: {hours:02}:{minutes:02}:{seconds:02}")
        self.root.after(1000, self.update_timer)  # Update every second

    def restart_timer(self):
        self.start_time = time.time()

    def format_duration(self, duration):
        duration = int(duration)
        minutes, seconds = divmod(duration, 60)
        return f"{minutes}:{seconds:02}"

    def refresh_data(self):
        if self.stop_event.is_set():
            return
        current_deck = self.get_current_deck()
        self.current_deck_label.config(text=f"Current Deck: {current_deck}")

        # Clear the current data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for champion, games in self.game_durations.items():
            if not games:
                continue
            durations = [game['duration'] for game in games]
            fastest_time = min(durations)
            average_time = sum(durations) / len(durations)
            self.tree.insert("", "end", text=champion, values=(self.format_duration(fastest_time), self.format_duration(average_time)))

        self.root.after(5000, self.refresh_data)  # Schedule the next refresh

    def save_data(self):
        # Function to handle saving the data
        date_str = datetime.now().strftime("%Y%m%d")
        random_number = random.randint(1000, 9999)
        filename = f"game_durations_{date_str}_{random_number}.csv"

        # Flatten the JSON structure and write to CSV
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Champion', 'Timestamp', 'Duration', 'GameID', 'DrewChampionTurnOne']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for champion, games in self.game_durations.items():
                for game in games:
                    writer.writerow({
                        'Champion': champion,
                        'Timestamp': game['timestamp'],
                        'Duration': game['duration'],
                        'GameID': game['game_id'],
                        'DrewChampionTurnOne': game.get('DrewChampionTurnOne', False)
                    })

        print(f"Data saved to {filename}")

    def stop(self):
        self.stop_event.set()
        self.root.quit()

    def show(self):
        self.root.mainloop()