# utils/utils.py
import json

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"favorites": []}

def save_config(data):
    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)
