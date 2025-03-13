import json
import os

# Store config in user's home directory
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".file_tree_config.json")

def save_config(config_dict):
    """Save configuration to a JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        return False

def load_config():
    """Load configuration from JSON file"""
    default_config = {
        "root_dir": "",
        "output_file": "",
        "extensions": [".py", ".txt", ".md", ".json", ".js", ".html", ".css"],
        "blacklist_folders": ["bin", "obj", "node_modules", ".git"],
        "blacklist_files": ["desktop.ini", "thumbs.db"],
        "priority_folders": ["src", "public", "assets", "components"],
        "priority_files": ["index.html", "main.js", "config.json"],
        "max_lines": 1000,
        "max_line_length": 300,
        "compact_view": False
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return default_config
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return default_config