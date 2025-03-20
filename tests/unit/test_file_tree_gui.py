"""
GUI tests for the File Tree Generator application.

These tests require pytest-xvfb for headless testing on Linux systems:
pip install pytest-xvfb

The tests also require the PyAutoGUI library:
pip install pyautogui
"""

import os
import sys
import time
import pytest
import threading
import tkinter as tk
from pathlib import Path
import file_tree_gui

# Skip tests if not running with xvfb
pytestmark = pytest.mark.skipif("DISPLAY" not in os.environ and sys.platform.startswith('linux'),
                              reason="GUI tests require a display")


@pytest.fixture
def gui_app():
    """Create and run the GUI application in a separate thread."""
    # Create a root window
    root = tk.Tk()
    root.geometry("800x1000")
    
    # Create the app
    app = file_tree_gui.FileTreeGeneratorApp(root)
    
    # Run the app in a separate thread
    thread = threading.Thread(target=root.mainloop)
    thread.daemon = True
    thread.start()
    
    # Wait for the app to initialize
    time.sleep(1)
    
    yield app
    
    # Clean up
    root.quit()
    time.sleep(0.5)


def test_initial_state(gui_app):
    """Test the initial state of the GUI."""
    # Check some basic properties
    assert gui_app.root.winfo_exists(), "Root window should exist"
    assert gui_app.root.title() == "File Tree Generator", "Window title should be set"
    
    # Check that menu exists
    assert hasattr(gui_app, 'menubar'), "Menu bar should exist"
    
    # Check log widget
    assert hasattr(gui_app, 'log_text'), "Log text widget should exist"
    
    # Verify some initial values
    assert isinstance(gui_app.extensions_var, tk.StringVar), "Extensions variable should exist"
    assert isinstance(gui_app.blacklist_folders_var, tk.StringVar), "Blacklist folders variable should exist"
    assert isinstance(gui_app.max_lines_var, tk.IntVar), "Max lines variable should exist"
    assert isinstance(gui_app.compact_view_var, tk.BooleanVar), "Compact view variable should exist"


def test_log_function(gui_app):
    """Test the log function."""
    # Initial state of log
    initial_state = gui_app.log_text.get("1.0", tk.END).strip()
    
    # Log a message
    test_message = "Test log message"
    gui_app.log(test_message)
    
    # Get updated log content
    updated_log = gui_app.log_text.get("1.0", tk.END).strip()
    
    # Verify the message was added
    assert test_message in updated_log, "Log message should be added to log text widget"
    assert len(updated_log) > len(initial_state), "Log should be longer after adding message"


def test_browse_functions(gui_app, sample_project):
    """Test the directory and file browsing functions."""
    # Set the root directory value programmatically
    gui_app.root_dir_var.set(sample_project)
    
    # Verify output file is updated
    assert gui_app.root_dir_var.get() == sample_project, "Root directory should be set"
    
    # Set output file programmatically
    output_file = os.path.join(sample_project, "output.txt")
    gui_app.output_file_var.set(output_file)
    
    # Verify output file is set
    assert gui_app.output_file_var.get() == output_file, "Output file should be set"


def test_save_settings(gui_app, sample_project, monkeypatch):
    """Test saving settings."""
    # Mock the save_config function to avoid writing to disk
    mock_result = [True]  # Using list to allow modification in nested function
    
    def mock_save_config(config_dict):
        # Just return success without writing to disk
        return mock_result[0]
    
    monkeypatch.setattr('file_tree_gui.save_config', mock_save_config)
    
    # Set some values
    gui_app.root_dir_var.set(sample_project)
    gui_app.output_file_var.set(os.path.join(sample_project, "output.txt"))
    gui_app.extensions_var.set(".py .txt")
    gui_app.max_lines_var.set(500)
    gui_app.compact_view_var.set(True)
    
    # Call save_settings with successful save
    gui_app.save_settings()
    
    # Verify a success message was logged
    log_content = gui_app.log_text.get("1.0", tk.END)
    assert "Configuration saved" in log_content, "Success message should be logged"
    
    # Test failure case
    mock_result[0] = False
    gui_app.log_text.delete("1.0", tk.END)  # Clear log
    
    # Call save_settings with failed save
    gui_app.save_settings()
    
    # Verify failure message was logged
    log_content = gui_app.log_text.get("1.0", tk.END)
    assert "Failed to save" in log_content, "Failure message should be logged"


def test_toggle_reference_options(gui_app):
    """Test toggling reference tracking options."""
    # Initially, reference tracking should be disabled
    initial_state = gui_app.reference_tracking_var.get()
    
    # Toggle it on
    gui_app.reference_tracking_var.set(True)
    gui_app.toggle_reference_options()
    
    # Check that depth spinbox is enabled
    depth_spinbox_state = "disabled"
    if hasattr(gui_app, 'depth_spinbox'):
        depth_spinbox_state = gui_app.depth_spinbox.cget("state")
        
    if not gui_app.unlimited_depth_var.get():
        assert depth_spinbox_state == "normal", "Depth spinbox should be enabled"
    
    # Toggle unlimited depth
    gui_app.unlimited_depth_var.set(True)
    gui_app.toggle_depth_spinner()
    
    # Check that depth spinbox is disabled with unlimited depth
    if hasattr(gui_app, 'depth_spinbox'):
        assert gui_app.depth_spinbox.cget("state") == "disabled", "Depth spinbox should be disabled with unlimited depth"
    
    # Toggle reference tracking off
    gui_app.reference_tracking_var.set(False)
    gui_app.toggle_reference_options()
    
    # Check that options are disabled
    if hasattr(gui_app, 'depth_spinbox'):
        assert gui_app.depth_spinbox.cget("state") == "disabled", "Depth spinbox should be disabled when reference tracking is off"


def test_token_estimation_options(gui_app):
    """Test token estimation options."""
    # Initial state
    initial_state = gui_app.enable_token_estimation_var.get()
    
    # Enable token estimation
    gui_app.enable_token_estimation_var.set(True)
    gui_app.toggle_token_options()
    
    # Check that token model combo is enabled
    if hasattr(gui_app, 'token_model_combo'):
        assert gui_app.token_model_combo.cget("state") != "disabled", "Token model combo should be enabled"
    
    # Select a different model
    if hasattr(gui_app, 'token_model_combo') and gui_app.token_model_combo['values']:
        gui_app.token_model_var.set(gui_app.token_model_combo['values'][0])
        gui_app.on_model_selected()
    
    # Check custom factor visibility
    if hasattr(gui_app, 'custom_factor_frame'):
        # If "custom" model is selected, frame should be visible
        if "custom" in gui_app.token_model_var.get().lower():
            assert gui_app.custom_factor_frame.winfo_ismapped(), "Custom factor frame should be visible with custom model"
        else:
            assert not gui_app.custom_factor_frame.winfo_ismapped(), "Custom factor frame should be hidden with non-custom model"
    
    # Disable token estimation
    gui_app.enable_token_estimation_var.set(False)
    gui_app.toggle_token_options()
    
    # Check that options are disabled
    if hasattr(gui_app, 'token_model_combo'):
        assert gui_app.token_model_combo.cget("state") == "disabled", "Token model combo should be disabled"


# More advanced tests would use pymock to simulate button clicks and user interaction