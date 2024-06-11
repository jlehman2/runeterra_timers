import tkinter as tk
from tkinter import ttk

class GameDurationsDisplay:
    def __init__(self, game_durations):
        self.game_durations = game_durations
        self.root = tk.Tk()
        self.root.title("Game Durations Info")

        self.tree = ttk.Treeview(self.root)
        self.tree["columns"] = ("fastest_time", "average_time")
        self.tree.heading("#0", text="Champion")
        self.tree.heading("fastest_time", text="Fastest Time")
        self.tree.heading("average_time", text="Average Time")
        self.tree.pack(expand=True, fill="both")

        self.refresh_data()
        self.root.after(5000, self.refresh_data)  # Refresh every 5 seconds

    def refresh_data(self):
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
            self.tree.insert("", "end", text=champion, values=(f"{fastest_time:.2f}", f"{average_time:.2f}"))

        self.root.after(5000, self.refresh_data)  # Schedule the next refresh

    def show(self):
        self.root.mainloop()
