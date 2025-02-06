import tkinter as tk
from tkinter import ttk, filedialog, font
import time
import csv
import threading


class GameDurationsDisplay:
    def __init__(self, root, game_durations, get_current_deck, get_current_champion_time, get_menu_time, stop_event, clear_data, champion_data):
        self.root = root  # Pass root from LoR_Timers.py
        self.game_durations = game_durations  # Store game durations
        self.get_current_deck = get_current_deck
        self.get_current_champion_time = get_current_champion_time  # ✅ New
        self.get_menu_time = get_menu_time  # ✅ New
        self.stop_event = stop_event
        self.clear_data = clear_data
        self.champion_data = champion_data

        self.root.title("Game Durations Info")

        # Define custom fonts
        arcade_font = font.Font(family="Arcade", size=16, weight="bold")

        # Set styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#2c3e50")
        style.configure("TLabel", background="#2c3e50", foreground="white", font=arcade_font)
        style.configure("TButton", background="#2c3e50", foreground="white", font=arcade_font)
        style.configure("Treeview.Heading", background="#2E0854", foreground="white", font=arcade_font)
        style.configure("Treeview", background="charcoal", foreground="white", fieldbackground="charcoal")

        self.root.configure(background="#2c3e50")

        # Current Deck Label
        self.current_deck_label = ttk.Label(self.root, text="Current Deck: Unknown", style="TLabel")
        self.current_deck_label.pack()

        # ✅ Champion Timer Label
        self.champion_timer_label = ttk.Label(self.root, text="Champion Time: 00:00", style="TLabel")
        self.champion_timer_label.pack()

        # ✅ Menu Timer Label
        self.menu_timer_label = ttk.Label(self.root, text="Menu Time: 00:00", style="TLabel")
        self.menu_timer_label.pack()

        # Timer & Restart Button
        self.timer_frame = ttk.Frame(self.root, style="TFrame")
        self.timer_frame.pack()

        self.timer_label = ttk.Label(self.timer_frame, text="Timer: 00:00:00", style="TLabel")
        self.timer_label.pack(side=tk.LEFT)

        self.restart_timer_button = ttk.Button(self.timer_frame, text="Restart Timer", command=self.restart_timer, style="TButton")
        self.restart_timer_button.pack(side=tk.LEFT, padx=10)

        # Last Game Duration Label
        self.last_game_duration_label = ttk.Label(self.root, text="Last Game Duration: 00:00", style="TLabel")
        self.last_game_duration_label.pack()

        # Treeview for Champion Times
        self.tree = ttk.Treeview(self.root, style="Treeview")
        self.tree["columns"] = ("fastest_time", "average_time")
        self.tree.heading("#0", text="Champion")
        self.tree.heading("fastest_time", text="Fastest Time")
        self.tree.heading("average_time", text="Average Time")
        self.tree.pack(expand=True, fill="both")

        # Start the timer & refresh loop
        self.start_time = time.time()
        self.update_timer()
        self.refresh_data()
        self.root.after(5000, self.refresh_data)

        # Handle Escape Key & Window Close
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.bind("<Escape>", lambda event: self.stop())

    def update_timer(self):
        """Updates the timer every second."""
        if self.stop_event.is_set():
            return
        elapsed_time = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.config(text=f"Timer: {hours:02}:{minutes:02}:{seconds:02}")
        self.root.after(1000, self.update_timer)

    def restart_timer(self):
        """Restarts the game timer."""
        self.start_time = time.time()

    def format_duration(self, duration):
        duration = int(duration)
        minutes, seconds = divmod(duration, 60)
        return f"{minutes}:{seconds:02}"

    def clear_data_memory(self):
        """Clear the data in memory (without writing to disk)."""
        self.game_durations.clear()
        print("cleared data")
        self.refresh_data()

    def refresh_data(self):
        """Refresh UI elements including timers."""
        if self.stop_event.is_set():
            return

        current_deck = self.get_current_deck()
        self.current_deck_label.config(text=f"Current Deck: {current_deck}")

        # ✅ Get the latest timers
        champion_time = self.format_duration(self.get_current_champion_time())
        menu_time = self.format_duration(self.get_menu_time())

        # ✅ Update champion & menu timers
        self.champion_timer_label.config(text=f"Champion Time: {champion_time}")
        self.menu_timer_label.config(text=f"Menu Time: {menu_time}")

        # ✅ Clear existing data in Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        last_game_duration = 0
        for champion, games in self.game_durations.items():
            if not games:
                continue
            durations = [game["duration"] if isinstance(game, dict) else game for game in
                         games]  # ✅ Handle float values safely
            fastest_time = min(durations)
            average_time = sum(durations) / len(durations)
            self.tree.insert("", "end", text=champion,
                             values=(self.format_duration(fastest_time), self.format_duration(average_time)))
            last_game_duration = durations[-1]

        # ✅ Update last game duration
        self.last_game_duration_label.config(text=f"Last Game Duration: {self.format_duration(last_game_duration)}")

        self.root.after(1000, self.refresh_data)

    def toggle_details(self):
        """Toggle details visibility."""
        if self.details_visible:
            self.details_frame.pack_forget()
            self.toggle_button.config(text="Show Details")
        else:
            self.details_frame.pack()
            self.toggle_button.config(text="Hide Details")
        self.details_visible = not self.details_visible

    def upload_csv(self):
        """Upload game data from a CSV file."""
        file_path = filedialog.askopenfilename(defaultextension=".csv",
                                               filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip the header
                for row in reader:
                    champion, duration, game_id = row
                    game_record = {
                        'duration': float(duration),
                        'game_id': int(game_id),
                    }
                    if champion not in self.game_durations:
                        self.game_durations[champion] = []
                    self.game_durations[champion].append(game_record)
            self.refresh_data()

    def save_data(self):
        """Save all game durations to a CSV file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_path:
            return  # User canceled file save

        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Champion', 'Duration', 'GameID'])

            for champion, games in self.game_durations.items():
                for game in games:
                    writer.writerow([champion, game['duration'], game['game_id']])

        print(f"[INFO] Data saved to {file_path}")

    def stop(self):
        """Stop the application cleanly."""
        print("[INFO] Stopping application...")
        self.stop_event.set()  # Signal other threads to stop
        self.root.quit()  # Stop tkinter main loop
        self.root.destroy()  # Close the GUI window
        print("[INFO] Application closed successfully.")

    def run(self):
        """Runs the GUI event loop."""
        self.root.mainloop()
