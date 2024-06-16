import tkinter as tk
from tkinter import ttk
from tkinter import font, filedialog
import time
import random
import csv
from datetime import datetime
import json

class GameDurationsDisplay:
    def __init__(self, game_durations, get_current_deck, stop_event, clear_data):
        self.game_durations = game_durations
        self.get_current_deck = get_current_deck
        self.stop_event = stop_event
        self.clear_data = clear_data

        self.root = tk.Tk()
        self.root.title("Game Durations Info")

        # Define custom fonts
        arcade_font = font.Font(family="Arcade", size=16, weight="bold")
        small_font = font.Font(family="Arcade", size=10, weight="bold")

        # Set styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#2c3e50")
        style.configure("TLabel", background="#2c3e50", foreground="white", font=arcade_font)
        style.configure("TButton", background="#2c3e50", foreground="white", font=arcade_font)
        style.configure("Treeview.Heading", background="#2E0854", foreground="white", font=arcade_font)
        style.configure("Treeview", background="charcoal", foreground="white", fieldbackground="charcoal", font=arcade_font)

        self.root.configure(background="#2c3e50")

        self.current_deck_label = ttk.Label(self.root, text="Current Deck: ", style="TLabel")
        self.current_deck_label.pack()

        self.timer_frame = ttk.Frame(self.root, style="TFrame")
        self.timer_frame.pack()

        self.timer_label = ttk.Label(self.timer_frame, text="Timer: 00:00:00", style="TLabel")
        self.timer_label.pack(side=tk.LEFT)

        self.restart_timer_button = ttk.Button(self.timer_frame, text="Restart Timer", command=self.restart_timer, style="TButton")
        self.restart_timer_button.pack(side=tk.LEFT, padx=10)

        self.last_game_duration_label = ttk.Label(self.root, text="Last Game Duration: 00:00", style="TLabel")
        self.last_game_duration_label.pack()

        self.tree = ttk.Treeview(self.root, style="Treeview")
        self.tree["columns"] = ("fastest_time", "average_time")
        self.tree.heading("#0", text="Champion")
        self.tree.heading("fastest_time", text="Fastest Time")
        self.tree.heading("average_time", text="Average Time")
        self.tree.pack(expand=True, fill="both")

        # Create a frame for the buttons
        self.button_frame = ttk.Frame(self.root, style="TFrame")
        self.button_frame.pack(pady=10)

        self.clear_button = ttk.Button(self.button_frame, text="Clear Data", command=self.clear_data, style="TButton")
        self.clear_button.grid(row=0, column=0, padx=5)

        # Create a menubar
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # Create the File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save", command=self.save_data)
        self.file_menu.add_command(label="Upload CSV", command=self.upload_csv)

        self.developed_by_label = ttk.Label(self.root, text="Developed by lehmon", font=small_font, style="TLabel")
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
        last_game_duration = 0
        for champion, games in self.game_durations.items():
            if not games:
                continue
            durations = [game['duration'] for game in games]
            fastest_time = min(durations)
            average_time = sum(durations) / len(durations)
            self.tree.insert("", "end", text=champion,
                             values=(self.format_duration(fastest_time), self.format_duration(average_time)))
            last_game_duration = durations[-1]  # Get the duration of the last game

        # Update last game duration label
        self.last_game_duration_label.config(text=f"Last Game Duration: {self.format_duration(last_game_duration)}")

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

    def upload_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.load_csv_to_game_durations(file_path)
            print(f"Data loaded from {file_path}")

    def load_csv_to_game_durations(self, file_path):
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    champion = row['Champion']
                    game_record = {
                        "timestamp": row['Timestamp'],
                        "duration": float(row['Duration']),
                        "game_id": int(row['GameID']),
                        "DrewChampionTurnOne": row['DrewChampionTurnOne'].lower() == 'true'
                    }
                    if champion not in self.game_durations:
                        self.game_durations[champion] = []
                    self.game_durations[champion].append(game_record)

            # Save the updated game durations to the JSON file
            with open('game_durations.json', 'w') as file:
                json.dump(self.game_durations, file, indent=4)

            self.refresh_data()  # Refresh the display to show the new data
        except Exception as e:
            print(f"Failed to load CSV file: {e}")