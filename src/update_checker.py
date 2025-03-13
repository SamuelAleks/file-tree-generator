import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
import webbrowser
import urllib.request
import socket
from packaging.version import Version as StrictVersion

# Current version - update this when you release a new version
CURRENT_VERSION = "1.0.2"
GITHUB_REPO = "SamuelAleks/file-tree-generator"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

def get_latest_version():
    """Get the latest version from GitHub releases with improved error handling"""
    try:
        # Set User-Agent to avoid GitHub API rate limiting
        headers = {'User-Agent': 'FileTreeGenerator UpdateChecker'}
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        
        # Add timeout and better error handling
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                # GitHub release tag format: "v1.0.2"
                latest_version = data.get('tag_name', '').lstrip('v')
                return latest_version, data.get('html_url', GITHUB_RELEASE_URL)
        except urllib.error.URLError as e:
            print(f"Network error checking for updates: {str(e)}")
            return None, None
        except json.JSONDecodeError:
            print("Error parsing GitHub API response")
            return None, None
        except socket.timeout:
            print("Timeout while checking for updates")
            return None, None
    except Exception as e:
        print(f"Unexpected error checking for updates: {str(e)}")
        return None, None

def is_update_available():
    """Check if an update is available"""
    latest_version, download_url = get_latest_version()
    if not latest_version:
        return False, None
    
    try:
        # Compare versions
        if StrictVersion(latest_version) > StrictVersion(CURRENT_VERSION):
            return True, download_url
        return False, None
    except Exception:
        # If there's any issue with version comparison, don't prompt for update
        return False, None

def check_for_updates(silent=False, parent=None):
    """
    Check for updates and optionally show a dialog
    
    Args:
        silent: If True, don't show a dialog if no updates are available
        parent: Parent window for the message box
    """
    update_available, download_url = is_update_available()
    
    if update_available and download_url:
        latest_version, _ = get_latest_version()
        if messagebox.askyesno(
            "Update Available",
            f"A new version of File Tree Generator is available!\n\n"
            f"Current version: {CURRENT_VERSION}\n"
            f"Latest version: {latest_version}\n\n"
            f"Would you like to download the update?",
            parent=parent
        ):
            webbrowser.open(download_url)
        return True
    elif not silent:
        messagebox.showinfo(
            "No Updates",
            f"You're using the latest version ({CURRENT_VERSION}).",
            parent=parent
        )
    
    return False

# You can integrate this function in your application's main menu
def add_update_check_to_menu(menu):
    """Add an update check option to a menu"""
    menu.add_command(label="Check for Updates", command=lambda: check_for_updates(silent=False))

# For automatic update check at startup
def check_updates_at_startup(root):
    """Check for updates at startup without blocking the UI"""
    # Delay the check to ensure the UI is fully loaded
    root.after(2000, lambda: check_for_updates(silent=True, parent=root))