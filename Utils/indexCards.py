import os
import json
from abc import ABC, abstractmethod
import sys
from collections import defaultdict




class IndexCards(ABC):
    """Abstract class for indexing and querying card sets."""

    def __init__(self, folder):
        """Initialize the tool with the folder containing card JSON files."""
        self.folder = folder
        self.code_to_info = {}  # Stores full card info for each cardCode
        self.name_to_codes = defaultdict(list)  # Maps name to cardCodes

    @abstractmethod
    def load_card_sets(self):
        """Abstract method to load card sets."""
        pass

    def get_name_by_code(self, code):
        """Retrieve the name of a card by its cardCode."""
        return self.code_to_info.get(code, {}).get('name', 'No card found with this code.')

    def get_codes_by_name(self, name):
        """Retrieve all cardCodes associated with a card name."""
        return self.name_to_codes.get(name, f"No codes found for card name: {name}")

    def fullInfo(self, code):
        """Retrieve full information for a given cardCode."""
        card_info = self.code_to_info.get(code)
        if card_info:
            print(f"Full information for {code}:")
            for key, value in card_info.items():
                print(f"{key}: {value}")
        else:
            print(f"No information found for card code: {code}")

    def list_all_codes(self):
        """List all loaded card codes."""
        return list(self.code_to_info.keys())

class LocalIndexCards(IndexCards):
    """Concrete class to load and query card sets from local files."""

    def load_card_sets(self):
        """Load card sets from the specified folder."""
        if not os.path.exists(self.folder):
            print(f"[ERROR] Folder '{self.folder}' does not exist.")
            sys.exit(1)

        json_files = [f for f in os.listdir(self.folder) if f.endswith('.json')]
        if not json_files:
            print(f"[ERROR] No JSON files found in '{self.folder}'.")
            sys.exit(1)

        total_cards_loaded = 0

        try:
            for file in json_files:
                path = os.path.join(self.folder, file)
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[INFO] Loaded {len(data)} cards from '{file}'")

                    for card in data:
                        code = card.get('cardCode')
                        name = card.get('name')

                        if code and name:
                            # Store full card info by cardCode
                            self.code_to_info[code] = card
                            # Map name to list of cardCodes
                            self.name_to_codes[name].append(code)
                            total_cards_loaded += 1

            print(f"[INFO] Total cards loaded: {total_cards_loaded}")
            print(f"[INFO] Loaded card sets: {self.list_all_codes()[:5]}... (showing first 5 codes)")

        except Exception as e:
            print(f"[ERROR] Error loading card sets: {e}")
            sys.exit(1)

if __name__ == "__main__":
    folder = '../card_sets'
    print(f"[INFO] Checking folder: {folder}")

    card_query = LocalIndexCards(folder)
    card_query.load_card_sets()

    while True:
        query = input("Enter a card code, name, or 'info:<cardCode>' (or type 'exit' to quit): ").strip()
        if query == 'exit':
            print("[INFO] Exiting program.")
            break

        if query.startswith('info:'):
            card_code = query.split(':', 1)[1].strip()
            card_query.fullInfo(card_code)
        elif query in card_query.code_to_info:
            name = card_query.get_name_by_code(query)
            print(f"[INFO] Card Name: {name}")
        elif query in card_query.name_to_codes:
            codes = card_query.get_codes_by_name(query)
            print(f"[INFO] Card Codes: {', '.join(codes)}")
        else:
            print("[INFO] No matching card code or name found.")
