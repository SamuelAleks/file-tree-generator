import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import webbrowser
from tkinter.scrolledtext import ScrolledText
from file_selector import FileSelector
from reference_tracking import ReferenceTrackingManager
from token_estimator import get_available_models, get_model_factors

# Import tree generation functions
from file_tree_generator import (
    create_file_tree, 
    export_as_html, 
    export_as_markdown, 
    export_as_json
)
from config_utils import load_config, save_config
import token_estimator
from update_checker import check_updates_at_startup, add_update_check_to_menu, CURRENT_VERSION, GITHUB_REPO

class FileTreeGeneratorApp:
    # Reference tracker for reference tracking export functionality
    reference_tracker = None
    
    def __init__(self, root):
        self.root = root
        self.root.title("File Tree Generator")
        self.root.geometry("800x1000")

        # Load saved configuration
        self.config = load_config()

        # Create menu (all visualization items initially disabled)
        self.create_menu()
    
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        # Create input frame for directory and output file
        input_frame = ttk.LabelFrame(main_frame, text="Input/Output", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
    
        # Root directory selection
        ttk.Label(input_frame, text="Root Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.root_dir_var = tk.StringVar(value=self.config.get('root_dir', ''))
        ttk.Entry(input_frame, textvariable=self.root_dir_var, width=50).grid(row=0, column=1, sticky=tk.W)
        ttk.Button(input_frame, text="Browse...", command=self.browse_root_dir).grid(row=0, column=2, padx=5)
    
        # Output file selection
        ttk.Label(input_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_file_var = tk.StringVar(value=self.config.get('output_file', ''))
        ttk.Entry(input_frame, textvariable=self.output_file_var, width=50).grid(row=1, column=1, sticky=tk.W)
        ttk.Button(input_frame, text="Browse...", command=self.browse_output_file).grid(row=1, column=2, padx=5)
        
        # Create settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # File extensions
        ttk.Label(settings_frame, text="File Extensions:").grid(row=0, column=0, sticky=tk.W, pady=5)
        extensions_str = " ".join(self.config.get('extensions', ['.py', '.txt', '.md', '.json', '.js', '.html', '.css']))
        self.extensions_var = tk.StringVar(value=extensions_str)
        ttk.Entry(settings_frame, textvariable=self.extensions_var, width=50).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(settings_frame, text="(Space-separated, e.g.: .py .txt .md)").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Blacklist folders
        ttk.Label(settings_frame, text="Blacklist Folders:").grid(row=1, column=0, sticky=tk.W, pady=5)
        blacklist_folders_str = " ".join(self.config.get('blacklist_folders', ['bin', 'obj', 'node_modules', '.git']))
        self.blacklist_folders_var = tk.StringVar(value=blacklist_folders_str)
        ttk.Entry(settings_frame, textvariable=self.blacklist_folders_var, width=50).grid(row=1, column=1, sticky=tk.W)
        
        # Blacklist files
        ttk.Label(settings_frame, text="Blacklist Files:").grid(row=2, column=0, sticky=tk.W, pady=5)
        blacklist_files_str = " ".join(self.config.get('blacklist_files', ['desktop.ini', 'thumbs.db']))
        self.blacklist_files_var = tk.StringVar(value=blacklist_files_str)
        ttk.Entry(settings_frame, textvariable=self.blacklist_files_var, width=50).grid(row=2, column=1, sticky=tk.W)
        
        # Priority folders
        ttk.Label(settings_frame, text="Priority Folders:").grid(row=3, column=0, sticky=tk.W, pady=5)
        priority_folders_str = " ".join(self.config.get('priority_folders', ['src', 'public', 'assets', 'components']))
        self.priority_folders_var = tk.StringVar(value=priority_folders_str)
        ttk.Entry(settings_frame, textvariable=self.priority_folders_var, width=50).grid(row=3, column=1, sticky=tk.W)
        
        # Priority files
        ttk.Label(settings_frame, text="Priority Files:").grid(row=4, column=0, sticky=tk.W, pady=5)
        priority_files_str = " ".join(self.config.get('priority_files', ['index.html', 'main.js', 'config.json']))
        self.priority_files_var = tk.StringVar(value=priority_files_str)
        ttk.Entry(settings_frame, textvariable=self.priority_files_var, width=50).grid(row=4, column=1, sticky=tk.W)
        
        # Advanced settings frame
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Settings", padding="10")
        advanced_frame.pack(fill=tk.X, pady=5)

        # Reference tracking frame
        reference_frame = ttk.LabelFrame(main_frame, text="Reference Tracking", padding="10")
        reference_frame.pack(fill=tk.X, pady=5)

        # Enable reference tracking checkbox
        self.reference_tracking_var = tk.BooleanVar(value=self.config.get('reference_tracking', False))
        self.reference_tracking_check = ttk.Checkbutton(reference_frame, text="Enable Reference Tracking", 
                       variable=self.reference_tracking_var,
                       command=self.toggle_reference_options)
        self.reference_tracking_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        # Reference depth options
        ttk.Label(reference_frame, text="Reference Depth:").grid(row=0, column=1, sticky=tk.W, padx=(20, 5), pady=5)
        self.reference_depth_var = tk.IntVar(value=self.config.get('reference_depth', 1))
        self.depth_spinbox = ttk.Spinbox(reference_frame, from_=1, to=10, increment=1, 
                                  textvariable=self.reference_depth_var, width=5)
        self.depth_spinbox.grid(row=0, column=2, sticky=tk.W)

        # Unlimited depth checkbox
        self.unlimited_depth_var = tk.BooleanVar(value=self.config.get('unlimited_depth', False))
        self.unlimited_depth_check = ttk.Checkbutton(reference_frame, text="Unlimited Depth", 
                                              variable=self.unlimited_depth_var,
                                              command=self.toggle_depth_spinner)
        self.unlimited_depth_check.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Add XAML ignore checkbox
        self.ignore_xaml_var = tk.BooleanVar(value=self.config.get('ignore_xaml', False))
        self.ignore_xaml_check = ttk.Checkbutton(reference_frame, text="Ignore XAML/AXAML Files", 
                                         variable=self.ignore_xaml_var,
                                         command=self.toggle_xaml_options)
        self.ignore_xaml_check.grid(row=0, column=4, sticky=tk.W, padx=5)
        self.create_tooltip(self.ignore_xaml_check, 
                         "Ignore XAML/AXAML files during reference tracking (except selected files)")

        # Selected files display
        ttk.Label(reference_frame, text="Selected Files:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.selected_files_var = tk.StringVar(value="No files selected")
        ttk.Label(reference_frame, textvariable=self.selected_files_var).grid(row=1, column=1, 
                                                                           columnspan=2, sticky=tk.W)

        # Select files button
        self.select_files_button = ttk.Button(reference_frame, text="Select Files...", 
                                           command=self.select_reference_files)
        self.select_files_button.grid(row=1, column=3, sticky=tk.W, padx=5)

        # Initialize reference tracking state
        self.selected_files = []
        self.toggle_reference_options()
        self.toggle_depth_spinner()
        
        # Max lines
        ttk.Label(advanced_frame, text="Max Lines:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_lines_var = tk.IntVar(value=self.config.get('max_lines', 1000))
        ttk.Spinbox(advanced_frame, from_=10, to=10000, increment=10, textvariable=self.max_lines_var, width=10).grid(row=0, column=1, sticky=tk.W)
        
        # Max line length
        ttk.Label(advanced_frame, text="Max Line Length:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        self.max_line_length_var = tk.IntVar(value=self.config.get('max_line_length', 300))
        ttk.Spinbox(advanced_frame, from_=10, to=1000, increment=10, textvariable=self.max_line_length_var, width=10).grid(row=0, column=3, sticky=tk.W)
        
        # Compact view checkbox
        self.compact_view_var = tk.BooleanVar(value=self.config.get('compact_view', False))
        ttk.Checkbutton(advanced_frame, text="Compact View", variable=self.compact_view_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Create efficiency options frame
        efficiency_frame = ttk.LabelFrame(main_frame, text="Efficiency Options", padding="10")
        efficiency_frame.pack(fill=tk.X, pady=5)
    
        # Ultra-compact view checkbox (moved from advanced frame to efficiency frame)
        self.ultra_compact_view_var = tk.BooleanVar(value=self.config.get('ultra_compact_view', False))
        ttk.Checkbutton(efficiency_frame, text="Ultra-Compact View", 
                       variable=self.ultra_compact_view_var,
                       command=self.toggle_efficiency_options).grid(row=0, column=0, sticky=tk.W)
    
        # Comment removal checkbox
        self.remove_comments_var = tk.BooleanVar(value=self.config.get('remove_comments', False))
        ttk.Checkbutton(efficiency_frame, text="Remove Comments", 
                       variable=self.remove_comments_var).grid(row=0, column=1, sticky=tk.W)
    
        # Empty line exclusion checkbox
        self.exclude_empty_lines_var = tk.BooleanVar(value=self.config.get('exclude_empty_lines', False))
        ttk.Checkbutton(efficiency_frame, text="Exclude Empty Lines", 
                       variable=self.exclude_empty_lines_var).grid(row=0, column=2, sticky=tk.W)
    
        # Add tooltips for each option
        self.create_tooltip(efficiency_frame.winfo_children()[0], 
                         "Minimizes formatting for maximum efficiency")
        self.create_tooltip(efficiency_frame.winfo_children()[1], 
                         "Removes comments from code files (// /* */ # <!-- --> etc.)")
        self.create_tooltip(efficiency_frame.winfo_children()[2], 
                         "Excludes blank lines from file content")
                     
        # Additional efficiency options in row 1
        # Truncate long lines toggle
        self.smart_truncate_var = tk.BooleanVar(value=self.config.get('smart_truncate', False))
        ttk.Checkbutton(efficiency_frame, text="Smart Line Truncation", 
                       variable=self.smart_truncate_var).grid(row=1, column=0, sticky=tk.W)
    
        # Hide binary files toggle
        self.hide_binary_files_var = tk.BooleanVar(value=self.config.get('hide_binary_files', False))
        ttk.Checkbutton(efficiency_frame, text="Hide Binary Files", 
                       variable=self.hide_binary_files_var).grid(row=1, column=1, sticky=tk.W)
    
        # Hide repeated sections toggle
        self.hide_repeated_sections_var = tk.BooleanVar(value=self.config.get('hide_repeated_sections', False))
        ttk.Checkbutton(efficiency_frame, text="Hide Repeated Sections", 
                        variable=self.hide_repeated_sections_var).grid(row=1, column=2, sticky=tk.W)
    
        # Add tooltips for the additional options
        self.create_tooltip(efficiency_frame.winfo_children()[3], 
                         "Intelligently truncate long lines to preserve important content")
        self.create_tooltip(efficiency_frame.winfo_children()[4], 
                         "Exclude binary file contents from the output")
        self.create_tooltip(efficiency_frame.winfo_children()[5], 
                         "Collapse repeated code sections and show only once")

        # Token estimation frame
        token_frame = ttk.LabelFrame(main_frame, text="Token Estimation", padding="10")
        token_frame.pack(fill=tk.X, pady=5)

        # Enable token estimation checkbox
        self.enable_token_estimation_var = tk.BooleanVar(value=self.config.get('enable_token_estimation', False))
        ttk.Checkbutton(token_frame, text="Enable Token Estimation", 
                       variable=self.enable_token_estimation_var,
                       command=self.toggle_token_options).grid(row=0, column=0, sticky=tk.W, pady=5)

        # Model selection
        ttk.Label(token_frame, text="Estimation Model:").grid(row=0, column=1, sticky=tk.W, padx=(20, 5), pady=5)
        self.token_model_var = tk.StringVar(value=self.config.get('token_estimation_model', 'claude-3.5-sonnet'))
        self.token_model_combo = ttk.Combobox(token_frame, textvariable=self.token_model_var, width=15)

        # Get models list
        available_models = get_available_models()
        model_ids = [m[0] for m in available_models]
        model_names = [m[1] for m in available_models]
        self.token_model_combo['values'] = model_names
        self.token_model_map = dict(zip(model_names, model_ids))  # For lookup
        self.token_model_combo['state'] = 'readonly'
        self.token_model_combo.grid(row=0, column=2, sticky=tk.W)
        self.token_model_combo.bind('<<ComboboxSelected>>', self.on_model_selected)

        # Estimation method
        ttk.Label(token_frame, text="Method:").grid(row=0, column=3, sticky=tk.W, padx=(20, 5), pady=5)
        self.token_method_var = tk.StringVar(value=self.config.get('token_estimation_method', 'char'))
        method_combo = ttk.Combobox(token_frame, textvariable=self.token_method_var, width=10)
        method_combo['values'] = ('char', 'word')
        method_combo['state'] = 'readonly'
        method_combo.grid(row=0, column=4, sticky=tk.W)

        # Show all models toggle
        self.show_all_models_var = tk.BooleanVar(value=self.config.get('show_all_models', False))
        ttk.Checkbutton(token_frame, text="Show All Models", 
                       variable=self.show_all_models_var,
                       command=self.toggle_show_all_models).grid(row=1, column=0, sticky=tk.W, pady=5)

        # Custom model factors (only shown for custom model)
        self.custom_char_factor_var = tk.DoubleVar(value=self.config.get('custom_char_factor', 0.25))
        self.custom_word_factor_var = tk.DoubleVar(value=self.config.get('custom_word_factor', 1.3))

        self.custom_factor_frame = ttk.Frame(token_frame)
        self.custom_factor_frame.grid(row=1, column=1, columnspan=4, sticky=tk.W, pady=5)

        ttk.Label(self.custom_factor_frame, text="Custom Factors - Char:").pack(side=tk.LEFT, padx=(0, 5))
        char_factor_spinbox = ttk.Spinbox(self.custom_factor_frame, from_=0.1, to=1.0, increment=0.05, 
                                        width=5, textvariable=self.custom_char_factor_var)
        char_factor_spinbox.pack(side=tk.LEFT)

        ttk.Label(self.custom_factor_frame, text="Word:").pack(side=tk.LEFT, padx=(10, 5))
        word_factor_spinbox = ttk.Spinbox(self.custom_factor_frame, from_=0.5, to=3.0, increment=0.1, 
                                        width=5, textvariable=self.custom_word_factor_var)
        word_factor_spinbox.pack(side=tk.LEFT)

        # Token count preview
        ttk.Label(token_frame, text="Raw File Token Preview:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.token_preview_var = tk.StringVar(value="No files selected")
        ttk.Label(token_frame, textvariable=self.token_preview_var).grid(row=2, column=1, columnspan=4, sticky=tk.W)

        # Tooltips for token estimation options
        self.create_tooltip(token_frame.winfo_children()[0],
                          "Enable estimation of token counts for language models")
        self.create_tooltip(self.token_model_combo,
                          "Select which language model to estimate tokens for")
        self.create_tooltip(method_combo,
                          "Character-based is faster, word-based may be more accurate for some models")
        self.create_tooltip(token_frame.winfo_children()[4],
                          "Include token estimates for all models in output")

        # Initialize token options state
        self.toggle_token_options()
        self.update_custom_factor_visibility()

        # Create buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Save config button
        ttk.Button(buttons_frame, text="Save as Default", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        
        # Generate button
        ttk.Button(buttons_frame, text="Generate File Tree", command=self.generate_file_tree).pack(side=tk.RIGHT, padx=5)

        # Export format options
        ttk.Label(advanced_frame, text="Export Format:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5), pady=5)
        self.export_format_var = tk.StringVar(value=self.config.get('export_format', 'txt'))
        export_format_combo = ttk.Combobox(advanced_frame, textvariable=self.export_format_var, width=10)
        export_format_combo['values'] = ('txt', 'html', 'markdown', 'json')
        export_format_combo['state'] = 'readonly'
        export_format_combo.grid(row=1, column=3, sticky=tk.W)
        
        # Status log
        log_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        # Initialize reference tracking state
        self.selected_files = []
        self.toggle_reference_options()
        self.toggle_depth_spinner()
    
        # Update visualization menu state now that all variables are initialized
        self.update_visualization_menu()
    
        # Check for updates at startup (non-blocking)
        check_updates_at_startup(self.root)

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            tooltip = tk.Toplevel(widget)
            tooltip.overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+15}+{event.y_root+10}")
        
            label = ttk.Label(tooltip, text=text, background="#FFFFD0", relief="solid", borderwidth=1)
            label.pack()
        
            widget.tooltip = tooltip
        
        def leave(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
            
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    
    def update_visualization_menu(self):
        """Update visualization menu state based on current settings"""
        if hasattr(self, 'visualization_menu'):
            state = "normal" if self.reference_tracking_var.get() else "disabled"
            try:
                self.visualization_menu.entryconfig("File References Graph", state=state)
                self.visualization_menu.entryconfig("Method References Graph", state=state)
                self.visualization_menu.entryconfig("Class Hierarchy Graph", state=state)
            except:
                pass  # Menu items may not exist

    def toggle_efficiency_options(self):
        """Toggle various options based on efficiency settings"""
        # If ultra-compact is enabled, automatically enable compact
        if self.ultra_compact_view_var.get():
            self.compact_view_var.set(True)
    
        # Update UI to reflect the relationship between these options
        # This avoids confusion when both options are enabled
        if self.ultra_compact_view_var.get():
            for widget in self.root.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Checkbutton) and "Compact View" in str(grandchild):
                                    grandchild.configure(state="disabled")
        else:
            for widget in self.root.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Checkbutton) and "Compact View" in str(grandchild):
                                    grandchild.configure(state="normal")

    def toggle_compact_options(self):
        """Disable compact view if ultra-compact is enabled"""
        if self.ultra_compact_view_var.get():
            self.compact_view_var.set(False)
        
    def browse_root_dir(self):
        directory = filedialog.askdirectory(title="Select Root Directory")
        if directory:
            self.root_dir_var.set(directory)
            # Auto-set output file name based on directory
            base_dir_name = os.path.basename(directory)
            self.output_file_var.set(os.path.join(os.path.dirname(directory), f"{base_dir_name}_tree.txt"))
    
    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def save_settings(self):
        """Save current settings as default configuration"""
        try:
            # Get current values from UI
            extensions_str = self.extensions_var.get().strip()
            extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions_str.split()]
        
            blacklist_folders = self.blacklist_folders_var.get().split()
            blacklist_files = self.blacklist_files_var.get().split()
        
            priority_folders = [folder for folder in self.priority_folders_var.get().split() if folder]
            priority_files = [file for file in self.priority_files_var.get().split() if file]
            # Get token estimation settings
            model_name = self.token_model_var.get()
            model_id = self.token_model_map.get(model_name, "claude-3.5-sonnet")
        
            # Create config dictionary
            config = {
                'root_dir': self.root_dir_var.get(),
                'output_file': self.output_file_var.get(),
                'extensions': extensions,
                'blacklist_folders': blacklist_folders,
                'blacklist_files': blacklist_files,
                'priority_folders': priority_folders,
                'priority_files': priority_files,
                'max_lines': self.max_lines_var.get(),
                'max_line_length': self.max_line_length_var.get(),
                'compact_view': self.compact_view_var.get(),
                'export_format': self.export_format_var.get(),
                'reference_tracking': self.reference_tracking_var.get(),
                'reference_depth': self.reference_depth_var.get(),
                'unlimited_depth': self.unlimited_depth_var.get(),
                'ignore_xaml': self.ignore_xaml_var.get(),
                'ultra_compact_view': self.ultra_compact_view_var.get(),
                'remove_comments': self.remove_comments_var.get(),
                'exclude_empty_lines': self.exclude_empty_lines_var.get(),
                'smart_truncate': self.smart_truncate_var.get(),
                'hide_binary_files': self.hide_binary_files_var.get(),
                'hide_repeated_sections': self.hide_repeated_sections_var.get(),
                # Token estimation settings
                'enable_token_estimation': self.enable_token_estimation_var.get(),
                'token_estimation_model': model_id,
                'token_estimation_method': self.token_method_var.get(),
                'custom_char_factor': self.custom_char_factor_var.get(),
                'custom_word_factor': self.custom_word_factor_var.get(),
                'show_all_models': self.show_all_models_var.get()
                }
        
            # Save config
            if save_config(config):
                self.log("Configuration saved successfully as default settings.")
                messagebox.showinfo("Success", "Settings saved as default configuration.")
            else:
                self.log("Failed to save configuration.")
                messagebox.showerror("Error", "Failed to save configuration.")
            
        except Exception as e:
            error_msg = f"Error saving configuration: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def open_file(self, file_path):
        """Open a file with the default application in a cross-platform way"""
        file_path = os.path.normpath(file_path)
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS or Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', file_path], check=True)
                else:  # Linux
                    subprocess.run(['xdg-open', file_path], check=True)
            return True
        except Exception as e:
            print(f"Error opening file: {str(e)}")
            return False
    
    def generate_file_tree(self):
        try:
            # Get values from UI
            root_dir = self.root_dir_var.get()
            output_file = self.output_file_var.get()
            export_format = self.export_format_var.get()

            if not root_dir or not os.path.isdir(root_dir):
                messagebox.showerror("Error", "Please select a valid root directory")
                return
    
            if not output_file:
                messagebox.showerror("Error", "Please specify an output file path")
                return

            # Ensure output file has the correct extension
            output_base, output_ext = os.path.splitext(output_file)
            if export_format == 'txt' and output_ext.lower() != '.txt':
                output_file = output_base + '.txt'
            elif export_format == 'html' and output_ext.lower() != '.html':
                output_file = output_base + '.html'
            elif export_format == 'markdown' and output_ext.lower() not in ['.md', '.markdown']:
                output_file = output_base + '.md'
            elif export_format == 'json' and output_ext.lower() != '.json':
                output_file = output_base + '.json'

            # Update output file path in UI
            self.output_file_var.set(output_file)

            # Parse extensions
            extensions_str = self.extensions_var.get().strip()
            if not extensions_str:
                messagebox.showerror("Error", "Please specify at least one file extension")
                return
    
            extensions = set(ext if ext.startswith(".") else f".{ext}" for ext in extensions_str.split())

            # Parse blacklists
            blacklist_folders = set(self.blacklist_folders_var.get().split())
            blacklist_files = set(self.blacklist_files_var.get().split())

            # Parse priority lists
            priority_folders = [folder for folder in self.priority_folders_var.get().split() if folder]
            priority_files = [file for file in self.priority_files_var.get().split() if file]

            self.log(f"Starting file tree generation from {root_dir}")
            self.log(f"Included extensions: {', '.join(extensions)}")
            self.log(f"Blacklisted folders: {', '.join(blacklist_folders)}")
            self.log(f"Blacklisted files: {', '.join(blacklist_files)}")
            self.log(f"Export format: {export_format}")
    
            # Initialize referenced_files to None (for non-reference tracking mode)
            referenced_files = None
        
            # Handle reference tracking if enabled
            if self.reference_tracking_var.get():
                if not self.selected_files:
                    messagebox.showerror("Error", "Please select at least one file for reference tracking")
                    return
            
                self.log(f"Reference tracking enabled with {len(self.selected_files)} selected files")
            
                # Determine reference depth
                if self.unlimited_depth_var.get():
                    depth = float('inf')
                    self.log("Using unlimited reference depth")
                else:
                    depth = self.reference_depth_var.get()
                    self.log(f"Using reference depth of {depth}")
                
                # Check if XAML files should be ignored
                ignore_xaml = self.ignore_xaml_var.get()
                if ignore_xaml:
                    self.log("Ignoring XAML/AXAML files (except selected ones)")
            
                # Parse and analyze C# files
                self.log("Analyzing C# and XAML references...")
                reference_manager = ReferenceTrackingManager(root_dir, log_callback=self.log)
                reference_manager.parse_directory()
                
                # Store this reference manager for reference tracking use
                self.reference_tracker = reference_manager
            
                # Find related files
                referenced_files = reference_manager.find_related_files(
                    self.selected_files, 
                    depth,
                    ignore_xaml=ignore_xaml
                )
        
                # Add reference summary to log
                summary = reference_manager.generate_reference_summary(referenced_files)
                self.log("\n" + summary)
        
                # Create a file in the output directory with the referenced files
                reference_list_file = output_base + "_references.txt"
                with open(reference_list_file, 'w', encoding='utf-8') as f:
                    f.write("# Referenced Files\n\n")
                    for file_path in sorted(referenced_files):
                        f.write(f"- {os.path.relpath(file_path, root_dir)}\n")
                    
                        # Add reference details if available
                        referenced_by, references_to = reference_manager.get_reference_details(file_path)
                        if referenced_by:
                            f.write(f"  Referenced by ({len(referenced_by)}):\n")
                            for ref in sorted(referenced_by)[:10]:  # Limit to top 10
                                f.write(f"    - {os.path.relpath(ref, root_dir)}\n")
                        if references_to:
                            f.write(f"  References to ({len(references_to)}):\n")
                            for ref in sorted(references_to)[:10]:  # Limit to top 10
                                f.write(f"    - {os.path.relpath(ref, root_dir)}\n")
                        f.write("\n")
        
                self.log(f"Saved list of referenced files to {reference_list_file}")
            
            # Add token estimation parameters
            enable_token_estimation = self.enable_token_estimation_var.get()
            token_model = self.token_model_map.get(self.token_model_var.get(), "claude-3.5-sonnet")
            token_method = self.token_method_var.get()
        
            # Log token estimation settings if enabled
            if enable_token_estimation:
                self.log(f"Token estimation enabled for model: {self.token_model_var.get()}")
                self.log(f"Estimation method: {'Character-based' if token_method == 'char' else 'Word-based'}")
            
                # Update custom model factors if using custom model
                if token_model == "custom":
                    char_factor = self.custom_char_factor_var.get()
                    word_factor = self.custom_word_factor_var.get()
                    token_estimator.save_custom_model_factors(char_factor, word_factor)
                    self.log(f"Using custom factors - Char: {char_factor}, Word: {word_factor}")
            
                # If showing all models is enabled, log that
                if self.show_all_models_var.get():
                    self.log("Including estimates for all models in output")
                    
            # Add this confirmation message before starting generation
            if enable_token_estimation:
                self.log("Token estimation is enabled - both file contents and token statistics will be included in the output")
            # Create a temporary text output file
            temp_output = output_file
            if export_format != 'txt':
                temp_output = output_file + '.temp.txt'
        
            # Generate file tree
            result = create_file_tree(
                root_dir, 
                extensions, 
                temp_output,
                blacklist_folders=blacklist_folders,
                blacklist_files=blacklist_files,
                max_lines=self.max_lines_var.get(),
                max_line_length=self.max_line_length_var.get(),
                compact_view=self.compact_view_var.get(),
                ultra_compact_view=self.ultra_compact_view_var.get(),
                remove_comments=self.remove_comments_var.get(),
                exclude_empty_lines=self.exclude_empty_lines_var.get(),
                smart_truncate=self.smart_truncate_var.get(), 
                hide_binary_files=self.hide_binary_files_var.get(),  # Added this parameter
                hide_repeated_sections=self.hide_repeated_sections_var.get(),
                priority_folders=priority_folders,
                priority_files=priority_files,
                referenced_files=referenced_files,
                enable_token_estimation=enable_token_estimation,
                token_model=token_model,
                token_method=token_method
            )

            # Convert to desired format if needed
            if export_format != 'txt':
                with open(temp_output, 'r', encoding='utf-8') as f:
                    output_lines = f.read().splitlines()
    
                if export_format == 'html':
                    export_as_html(output_lines, output_file)
                elif export_format == 'markdown':
                    export_as_markdown(output_lines, output_file)
                elif export_format == 'json':
                    export_as_json(output_lines, output_file)
    
                # Clean up temporary file
                os.remove(temp_output)
    
                result = f"File tree generated successfully in {export_format.upper()} format at {os.path.abspath(output_file)}"

            self.log(result)
            messagebox.showinfo("Success", result)

            # Ask if user wants to open the file
            if messagebox.askyesno("Open File", "Do you want to open the generated file?"):
                self.open_file(output_file)
    
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        self.menubar = menubar  # Store reference for later use
    
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory...", command=self.browse_root_dir)
        file_menu.add_command(label="Save Output As...", command=self.browse_output_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
        # Settings menu
        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Save as Default", command=self.save_settings)
    
        # Add visualization menu
        self.create_visualization_menu()
    
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
        # Add update check to Help menu
        add_update_check_to_menu(help_menu)

    def create_visualization_menu(self):
        """Create visualization menu items for the GUI"""
        # Add visualization to main menu
        visualization_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Visualization", menu=visualization_menu)
    
        # Add visualization options - initially all disabled, will be updated later
        visualization_menu.add_command(label="File References Graph", 
                                     command=self.show_file_reference_graph,
                                     state="disabled")
        visualization_menu.add_command(label="Method References Graph", 
                                     command=self.show_method_reference_graph,
                                     state="disabled")
        visualization_menu.add_command(label="Class Hierarchy Graph", 
                                     command=self.show_class_hierarchy_graph,
                                     state="disabled")
        visualization_menu.add_separator()
        visualization_menu.add_command(label="Install Visualization Libraries", 
                                     command=self.install_visualization_libraries)
    
        # Store reference to the visualization menu for later updates
        self.visualization_menu = visualization_menu

    def toggle_reference_options(self):
        """Enable or disable reference tracking options based on checkbox"""
        state = "normal" if self.reference_tracking_var.get() else "disabled"
    
        # Use direct widget references for more reliability
        if hasattr(self, 'depth_spinbox'):
            # If unlimited depth is checked, keep spinbox disabled
            if self.unlimited_depth_var.get() and self.reference_tracking_var.get():
                self.depth_spinbox.configure(state="disabled")
            else:
                self.depth_spinbox.configure(state=state)
        
        if hasattr(self, 'unlimited_depth_check'):
            self.unlimited_depth_check.configure(state=state)
    
        if hasattr(self, 'ignore_xaml_check'):
            self.ignore_xaml_check.configure(state=state)
    
        if hasattr(self, 'select_files_button'):
            self.select_files_button.configure(state=state)
    
        # Update selected files label state
        for child in self.root.winfo_children():
            if isinstance(child, ttk.LabelFrame) and "Reference Tracking" in child["text"]:
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Label) and hasattr(grandchild, 'cget'):
                        try:
                            if grandchild.cget('textvariable') == str(self.selected_files_var):
                                grandchild.configure(state=state)
                        except:
                            pass
                        
        # Update visualization menu
        self.update_visualization_menu()

    def ensure_reference_tracker(self):
        """
        Ensures the reference tracker is initialized before visualization.
        Returns True if successful, False if failed.
        """
        if self.reference_tracker is None:
            try:
                root_dir = self.root_dir_var.get()
                if not root_dir or not os.path.isdir(root_dir):
                    messagebox.showerror("Error", "Please select a valid root directory first")
                    return False
                
                if not self.selected_files:
                    messagebox.showerror("Error", "Please select at least one file for reference tracking")
                    return False
                
                # Initialize reference tracker
                self.log("Initializing reference tracking...")
                reference_manager = ReferenceTrackingManager(root_dir, log_callback=self.log)
                # Parse the directory (this may take some time for large projects)
                self.log("Parsing directory structure...")
                files_parsed = reference_manager.parse_directory()
                self.log(f"Parsed {files_parsed} files")
            
                # Store the reference manager
                self.reference_tracker = reference_manager
                return True
            except Exception as e:
                self.log(f"Error initializing reference tracker: {str(e)}")
                messagebox.showerror("Error", f"Could not initialize reference tracking: {str(e)}")
                return False
        return True  # Reference tracker already exists
    
    def show_file_reference_graph(self):
        """Show file reference graph visualization"""
        try:
            # Import here to avoid errors if visualization is not available
            from code_visualization import CodeVisualizer
        
            # Check if reference tracking is enabled
            if not self.reference_tracking_var.get():
                messagebox.showinfo("Information", "Please enable reference tracking first.")
                return
            
            if not self.selected_files:
                messagebox.showinfo("Information", "Please select at least one file to visualize.")
                return
            
            # Ensure reference tracker is initialized
            if not self.ensure_reference_tracker():
                return
            
            # Create visualizer
            visualizer = CodeVisualizer(self.reference_tracker, self.log)
        
            # Determine reference depth
            if self.unlimited_depth_var.get():
                depth = float('inf')
            else:
                depth = self.reference_depth_var.get()
            
            # Create graph
            self.log("Generating file reference graph...")
            graph = visualizer.create_file_reference_graph(self.selected_files, max_depth=depth)
        
            if graph:
                # Show visualization
                visualizer.visualize_graph(graph, "File Reference Graph", self.root)
            else:
                messagebox.showerror("Error", "Failed to create file reference graph.")
            
        except ImportError:
            messagebox.showerror("Error", 
                               "Visualization libraries not found. Use 'Install Visualization Libraries' option.")
        except Exception as e:
            messagebox.showerror("Error", f"Error visualizing file references: {str(e)}")
            self.log(f"Error visualizing file references: {str(e)}")  # Add logging for debugging

    def show_method_reference_graph(self):
        """Show method reference graph visualization"""
        try:
            # Import here to avoid errors if visualization is not available
            from code_visualization import CodeVisualizer
        
            # Check if reference tracking is enabled
            if not self.reference_tracking_var.get():
                messagebox.showinfo("Information", "Please enable reference tracking first.")
                return
            
            # Ensure reference tracker is initialized
            if not self.ensure_reference_tracker():
                return
            
            # Create dialog to select a file and method
            select_dialog = tk.Toplevel(self.root)
            select_dialog.title("Select File and Method")
            select_dialog.geometry("600x400")
            select_dialog.transient(self.root)
            select_dialog.grab_set()
        
            # File selection
            file_frame = ttk.LabelFrame(select_dialog, text="Select File", padding="10")
            file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
            # File list with scrollbar
            file_list_frame = ttk.Frame(file_frame)
            file_list_frame.pack(fill=tk.BOTH, expand=True)
        
            file_scrollbar = ttk.Scrollbar(file_list_frame)
            file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
            file_listbox = tk.Listbox(file_list_frame, yscrollcommand=file_scrollbar.set)
            file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
            file_scrollbar.config(command=file_listbox.yview)
        
            # Add C# files to the list
            cs_files = [f for f in self.selected_files if f.endswith('.cs')]
            for file in sorted(cs_files):
                file_listbox.insert(tk.END, file)
        
            # Method selection
            method_frame = ttk.LabelFrame(select_dialog, text="Select Method", padding="10")
            method_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
            # Method list with scrollbar
            method_list_frame = ttk.Frame(method_frame)
            method_list_frame.pack(fill=tk.BOTH, expand=True)
        
            method_scrollbar = ttk.Scrollbar(method_list_frame)
            method_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
            method_listbox = tk.Listbox(method_list_frame, yscrollcommand=method_scrollbar.set)
            method_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
            method_scrollbar.config(command=method_listbox.yview)
        
            # Function to update method list when file is selected
            def update_method_list(event=None):
                method_listbox.delete(0, tk.END)
            
                selected_indices = file_listbox.curselection()
                if not selected_indices:
                    return
                
                file_path = file_listbox.get(selected_indices[0])
            
                # Get methods in file - using try-except to handle potential errors
                try:
                    methods = self.reference_tracker.get_methods_in_file(file_path)
                    for method in sorted(methods):
                        method_listbox.insert(tk.END, method)
                except Exception as e:
                    self.log(f"Error getting methods: {str(e)}")
                    messagebox.showerror("Error", f"Could not get methods: {str(e)}")
        
            # Bind file selection event
            file_listbox.bind('<<ListboxSelect>>', update_method_list)
        
            # Buttons
            button_frame = ttk.Frame(select_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
        
            cancel_button = ttk.Button(button_frame, text="Cancel", 
                                      command=select_dialog.destroy)
            cancel_button.pack(side=tk.RIGHT, padx=5)
        
            show_all_button = ttk.Button(button_frame, text="Show All Methods", 
                                       command=lambda: visualize_methods(None))
            show_all_button.pack(side=tk.RIGHT, padx=5)
        
            visualize_button = ttk.Button(button_frame, text="Visualize Method", 
                                        command=lambda: visualize_methods())
            visualize_button.pack(side=tk.RIGHT, padx=5)
        
            # Function to handle visualization
            def visualize_methods(method_name=None):
                try:
                    selected_indices = file_listbox.curselection()
                    if not selected_indices:
                        messagebox.showinfo("Information", "Please select a file.")
                        return
                    
                    file_path = file_listbox.get(selected_indices[0])
                
                    if method_name is None:
                        # If we're showing all methods or a specific method
                        method_indices = method_listbox.curselection()
                        if method_indices:
                            method_name = method_listbox.get(method_indices[0])
                
                    # Create visualizer
                    visualizer = CodeVisualizer(self.reference_tracker, self.log)
                
                    # Determine reference depth
                    depth = 1
                
                    # Create graph
                    self.log(f"Generating method reference graph for {os.path.basename(file_path)}...")
                    graph = visualizer.create_method_reference_graph(file_path, method_name, max_depth=depth)
                
                    if graph:
                        # Show visualization
                        title = f"Method References - {os.path.basename(file_path)}"
                        if method_name:
                            title += f" - {method_name}"
                        
                        visualizer.visualize_graph(graph, title, self.root)
                        select_dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to create method reference graph.")
                except Exception as e:
                    self.log(f"Error visualizing methods: {str(e)}")
                    messagebox.showerror("Error", f"Error visualizing methods: {str(e)}")
        
            # Center dialog
            select_dialog.update_idletasks()
            width = select_dialog.winfo_width()
            height = select_dialog.winfo_height()
            x = (select_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (select_dialog.winfo_screenheight() // 2) - (height // 2)
            select_dialog.geometry(f'{width}x{height}+{x}+{y}')
    
        except ImportError:
            messagebox.showerror("Error", 
                               "Visualization libraries not found. Use 'Install Visualization Libraries' option.")
        except Exception as e:
            self.log(f"Error in show_method_reference_graph: {str(e)}")
            messagebox.showerror("Error", f"Error visualizing method references: {str(e)}")

    def show_class_hierarchy_graph(self):
        """Show class hierarchy visualization"""
        try:
            # Import here to avoid errors if visualization is not available
            from code_visualization import CodeVisualizer
        
            # Check if reference tracking is enabled
            if not self.reference_tracking_var.get():
                messagebox.showinfo("Information", "Please enable reference tracking first.")
                return
            
            # Ensure reference tracker is initialized
            if not self.ensure_reference_tracker():
                return
            
            # Create dialog to select classes
            select_dialog = tk.Toplevel(self.root)
            select_dialog.title("Select Classes")
            select_dialog.geometry("600x400")
            select_dialog.transient(self.root)
            select_dialog.grab_set()
        
            # Class selection
            class_frame = ttk.LabelFrame(select_dialog, text="Select Classes", padding="10")
            class_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
            # Class list with scrollbar
            class_list_frame = ttk.Frame(class_frame)
            class_list_frame.pack(fill=tk.BOTH, expand=True)
        
            class_scrollbar = ttk.Scrollbar(class_list_frame)
            class_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
            class_listbox = tk.Listbox(class_list_frame, yscrollcommand=class_scrollbar.set, selectmode=tk.MULTIPLE)
            class_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
            class_scrollbar.config(command=class_listbox.yview)
        
            # Get all classes from reference tracker - using try-except to handle potential errors
            all_classes = set()
            try:
                for file_path, info in self.reference_tracker.tracker.file_info.items():
                    if info.get('is_xaml', False):
                        continue
                    
                    namespace = info.get('namespace', '')
                    for type_name in info.get('types', []):
                        qualified_name = f"{namespace}.{type_name}" if namespace else type_name
                        all_classes.add(qualified_name)
            except Exception as e:
                self.log(f"Error getting classes: {str(e)}")
                # Continue with an empty set - the user will see an empty list
        
            # Add classes to the list
            for class_name in sorted(all_classes):
                class_listbox.insert(tk.END, class_name)
        
            # Search field
            search_frame = ttk.Frame(class_frame)
            search_frame.pack(fill=tk.X, pady=(0, 10))
        
            ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
            # Function to update class list based on search
            def update_class_list(*args):
                search_text = search_var.get().lower()
            
                class_listbox.delete(0, tk.END)
            
                for class_name in sorted(all_classes):
                    if search_text in class_name.lower():
                        class_listbox.insert(tk.END, class_name)
        
            # Bind search field events
            search_var.trace_add("write", update_class_list)
        
            # Buttons
            button_frame = ttk.Frame(select_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
        
            cancel_button = ttk.Button(button_frame, text="Cancel", 
                                      command=select_dialog.destroy)
            cancel_button.pack(side=tk.RIGHT, padx=5)
        
            show_all_button = ttk.Button(button_frame, text="Show All Classes", 
                                       command=lambda: visualize_classes([]))
            show_all_button.pack(side=tk.RIGHT, padx=5)
        
            visualize_button = ttk.Button(button_frame, text="Visualize Selected", 
                                        command=lambda: visualize_classes())
            visualize_button.pack(side=tk.RIGHT, padx=5)
        
            # Function to handle visualization
            def visualize_classes(selected_classes=None):
                try:
                    if selected_classes is None:
                        # Get selected classes
                        selected_indices = class_listbox.curselection()
                        selected_classes = [class_listbox.get(i) for i in selected_indices]
                
                    # Create visualizer
                    visualizer = CodeVisualizer(self.reference_tracker, self.log)
                
                    # Create graph
                    self.log("Generating class hierarchy graph...")
                    graph = visualizer.create_class_reference_graph(
                        self.root_dir_var.get(), 
                        selected_classes,
                        max_depth=2
                    )
                
                    if graph:
                        # Show visualization
                        title = "Class Hierarchy Graph"
                        visualizer.visualize_graph(graph, title, self.root)
                        select_dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to create class hierarchy graph.")
                except Exception as e:
                    self.log(f"Error visualizing classes: {str(e)}")
                    messagebox.showerror("Error", f"Error visualizing classes: {str(e)}")
        
            # Center dialog
            select_dialog.update_idletasks()
            width = select_dialog.winfo_width()
            height = select_dialog.winfo_height()
            x = (select_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (select_dialog.winfo_screenheight() // 2) - (height // 2)
            select_dialog.geometry(f'{width}x{height}+{x}+{y}')
    
        except ImportError:
            messagebox.showerror("Error", 
                               "Visualization libraries not found. Use 'Install Visualization Libraries' option.")
        except Exception as e:
            self.log(f"Error in show_class_hierarchy_graph: {str(e)}")
            messagebox.showerror("Error", f"Error visualizing class hierarchy: {str(e)}")

    def install_visualization_libraries(self):
        """Install required visualization libraries"""
        try:
            import subprocess
            import sys
        
            self.log("Installing visualization libraries (networkx, matplotlib)...")
        
            # Run pip install
            python_exe = sys.executable
            subprocess.check_call([python_exe, "-m", "pip", "install", "networkx", "matplotlib"])
        
            self.log("Libraries installed successfully. Please restart the application.")
            messagebox.showinfo("Success", 
                              "Visualization libraries installed successfully.\n"
                              "Please restart the application to use visualization features.")
        except Exception as e:
            error_msg = f"Error installing libraries: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)

    def toggle_depth_spinner(self):
        """Enable or disable depth spinner based on unlimited depth checkbox"""
        if not hasattr(self, 'depth_spinbox'):
            return
        
        if self.reference_tracking_var.get():
            if self.unlimited_depth_var.get():
                self.depth_spinbox.configure(state="disabled")
            else:
                self.depth_spinbox.configure(state="normal")
        else:
            self.depth_spinbox.configure(state="disabled")
    
    def toggle_xaml_options(self):
        """Update status message when XAML ignore option changes"""
        try:
            if self.reference_tracking_var.get() and self.ignore_xaml_var.get():
                self.log("XAML/AXAML files will be ignored during reference tracking (except selected files)")
            elif self.reference_tracking_var.get():
                self.log("XAML/AXAML files will be included in reference tracking")
        except Exception as e:
            print(f"Error in toggle_xaml_options: {str(e)}")

    def select_reference_files(self):
        """Open dialog to select files for reference tracking"""
        root_dir = self.root_dir_var.get()
        if not root_dir or not os.path.isdir(root_dir):
            messagebox.showerror("Error", "Please select a valid root directory first")
            return
    
        # Ensure extensions are defined before opening the selector
        extensions_str = self.extensions_var.get().strip()
        if not extensions_str:
            messagebox.showwarning("Warning", "No file extensions specified. All files may be shown in the selector.")
    
        # Open file selector dialog with XAML support
        file_selector = FileSelector(
            self.root, 
            root_dir, 
            file_extension=".cs", 
            include_xaml=not self.ignore_xaml_var.get()
        )
        self.root.wait_window(file_selector)
    
        # Get selected files
        selected_files = file_selector.get_selected_files()
    
        # Make sure we got a valid list (not None)
        if selected_files is None:
            selected_files = []
    
        # Update the selected files list
        self.selected_files = selected_files
    
        # Update display
        if not self.selected_files:
            self.selected_files_var.set("No files selected")
        elif len(self.selected_files) == 1:
            self.selected_files_var.set("1 file selected")
        else:
            self.selected_files_var.set(f"{len(self.selected_files)} files selected")
    
        # Count selected file types for better user feedback
        xaml_count = sum(1 for file in self.selected_files 
                        if file.endswith(('.xaml', '.axaml')))
        cs_count = sum(1 for file in self.selected_files 
                      if file.endswith('.cs'))
        other_count = len(self.selected_files) - xaml_count - cs_count
    
        if self.selected_files:
            self.log(f"Selected {cs_count} C# files, {xaml_count} XAML/AXAML files, and {other_count} other files")
    
        # If XAML files are selected but ignore_xaml is enabled, show info message
        if xaml_count > 0 and self.ignore_xaml_var.get():
            self.log("Note: Selected XAML/AXAML files will be included even though 'Ignore XAML/AXAML Files' is enabled")
            messagebox.showinfo(
                "XAML Files Selected", 
                "You've selected XAML/AXAML files. These will be included in the analysis even though 'Ignore XAML/AXAML Files' is enabled.\n\n"
                "The 'Ignore XAML/AXAML Files' option only affects files discovered during reference tracking, not files that you explicitly select."
            )

    def toggle_token_options(self):
        """Enable or disable token estimation options based on checkbox"""
        state = "normal" if self.enable_token_estimation_var.get() else "disabled"
        readonly_state = 'readonly' if self.enable_token_estimation_var.get() else 'disabled'
        
        try:
            # Update token model combo state
            if hasattr(self, 'token_model_combo'):
                self.token_model_combo.configure(state=readonly_state)
            
            # Update method combo state
            for child in self.token_model_combo.master.winfo_children():
                if isinstance(child, ttk.Combobox) and child != self.token_model_combo:
                    child.configure(state=readonly_state)
            
            # Update show all models checkbox
            for child in self.token_model_combo.master.winfo_children():
                if isinstance(child, ttk.Checkbutton) and "Show All Models" in str(child):
                    child.configure(state=state)
            
            # Update custom factor frame
            if hasattr(self, 'custom_factor_frame'):
                for child in self.custom_factor_frame.winfo_children():
                    child.configure(state=state)
            
            # Update visibility of custom factor frame
            self.update_custom_factor_visibility()
            
            # Update token preview if enabled
            if self.enable_token_estimation_var.get():
                self.update_token_preview()
            else:
                self.token_preview_var.set("Token estimation disabled")
                
            # Include a user-friendly message about token estimation
            if self.enable_token_estimation_var.get():
                self.log("Token estimation enabled - file contents will still be included in the output")
        except Exception as e:
            print(f"Error in toggle_token_options: {str(e)}")

    def update_custom_factor_visibility(self):
        """Show or hide custom factor settings based on selected model"""
        try:
            if self.enable_token_estimation_var.get():
                model_name = self.token_model_var.get()
                model_id = self.token_model_map.get(model_name, "claude-3.5-sonnet")
            
                if model_id == "custom":
                    self.custom_factor_frame.grid()
                else:
                    self.custom_factor_frame.grid_remove()
            else:
                self.custom_factor_frame.grid_remove()
        except Exception as e:
            print(f"Error in update_custom_factor_visibility: {str(e)}")

    def on_model_selected(self, event=None):
        """Handle model selection change"""
        self.update_custom_factor_visibility()
        self.update_token_preview()

    def toggle_show_all_models(self):
        """Handle show all models toggle"""
        # This method is called by the GUI when the checkbox state changes
        # The actual toggling is handled by tkinter through the BooleanVar
        # Just need to update UI elements that depend on this setting
    
        # Log the change
        if self.show_all_models_var.get():
            self.log("Token estimates for all models will be included in output")
        else:
            self.log(f"Token estimates will only be shown for {self.token_model_var.get()}")
        
        # Update the preview with current settings
        self.update_token_preview()

    def update_token_preview(self):
        """Update token count preview based on selected files or directory"""
        try:
            if not self.enable_token_estimation_var.get():
                self.token_preview_var.set("Token estimation disabled")
                return
    
            root_dir = self.root_dir_var.get()
            if not root_dir or not os.path.isdir(root_dir):
                self.token_preview_var.set("No valid directory selected")
                return
    
            # Get settings
            model_name = self.token_model_var.get()
            model_id = self.token_model_map.get(model_name, "claude-3.5-sonnet")
            method = self.token_method_var.get()

            # Handle custom model factors
            if model_id == "custom":
                char_factor = self.custom_char_factor_var.get()
                word_factor = self.custom_word_factor_var.get()
                token_estimator.save_custom_model_factors(char_factor, word_factor)
    
            # Parse extensions
            extensions_str = self.extensions_var.get().strip()
            if not extensions_str:
                self.token_preview_var.set("No file extensions specified")
                return
    
            extensions = set(ext if ext.startswith(".") else f".{ext}" for ext in extensions_str.split())

            # Parse blacklists
            blacklist_folders = set(self.blacklist_folders_var.get().split())
            blacklist_files = set(self.blacklist_files_var.get().split())

            # Update preview with quick estimation (limit to 500 files for performance)
            self.token_preview_var.set("Estimating tokens...")
            self.root.update()

            # Run estimation in a separate thread to avoid UI freezing
            import threading

            def estimate_tokens():
                try:
                    result = token_estimator.estimate_tokens_for_directory(
                        root_dir,
                        extensions=extensions,
                        blacklist_folders=blacklist_folders,
                        blacklist_files=blacklist_files,
                        model=model_id,
                        method=method,
                        max_files=500  # Limit for preview
                    )
    
                    # Store results in local variables to avoid lambda capture issues
                    token_count = result['total_tokens']
                    processed_files = result['processed_files']
                    skipped_message = " (limited preview)" if result.get('skipped_files', 0) > 0 else ""
    
                    # Update UI in main thread with a properly defined lambda
                    self.root.after(0, lambda: self.token_preview_var.set(
                        f"Estimated tokens: {token_count:,} in {processed_files} files{skipped_message}"
                    ))
                except Exception as e:
                    # Store error message to avoid lambda scope issues
                    error_msg = str(e)
                    self.root.after(0, lambda: self.token_preview_var.set(f"Error: {error_msg}"))
    
            # Start the thread
            token_thread = threading.Thread(target=estimate_tokens, daemon=True)
            token_thread.start()

        except Exception as e:
            self.token_preview_var.set(f"Error: {str(e)}")


    # Stub methods for visualization functions
    def open_code_visualizer(self, file_path=None):
        """Stub for visualization functionality (removed)"""
        self.log("Visualization functionality has been removed")

    def visualize_method(self, file_path=None, method_name=None):
        """Stub for method visualization (removed)"""
        self.log("Method visualization functionality has been removed")
    
    def show_reference_graph(self):
        """Stub for reference graph visualization (removed)"""
        self.log("Reference graph visualization has been removed")
    
    def visualize_all_references(self):
        """Stub for all references visualization (removed)"""
        self.log("References visualization has been removed")

    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About File Tree Generator")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
    
        # About content
        ttk.Label(about_window, text="File Tree Generator", font=("Helvetica", 16, "bold")).pack(pady=10)
        ttk.Label(about_window, text=f"Version {CURRENT_VERSION}").pack()
        ttk.Label(about_window, text="© 2025 Paape Companies").pack(pady=5)
        ttk.Label(about_window, text="A tool to create visual representations of directory trees").pack(pady=10)
    
        # GitHub link
        github_frame = ttk.Frame(about_window)
        github_frame.pack(pady=10)
        ttk.Label(github_frame, text="GitHub: ").pack(side=tk.LEFT)
        github_link = ttk.Label(github_frame, text="github.com/SamuelAleks/file-tree-generator", 
                                foreground="blue", cursor="hand2")
        github_link.pack(side=tk.LEFT)
        github_link.bind("<Button-1>", lambda e: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
    
        # Close button
        ttk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)
    
        # Center the window
        about_window.update_idletasks()
        width = about_window.winfo_width()
        height = about_window.winfo_height()
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTreeGeneratorApp(root)
    root.mainloop()