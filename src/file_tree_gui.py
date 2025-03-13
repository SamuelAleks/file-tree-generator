import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import webbrowser
from tkinter.scrolledtext import ScrolledText

# Import your existing function and config utilities
from file_tree_generator import (
    create_file_tree, 
    export_as_html, 
    export_as_markdown, 
    export_as_json
)
from config_utils import load_config, save_config
from update_checker import check_updates_at_startup, add_update_check_to_menu, CURRENT_VERSION, GITHUB_REPO

class FileTreeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Tree Generator")
        self.root.geometry("800x600")
        
        # Load saved configuration
        self.config = load_config()
        
        # Create menu bar
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
        # Check for updates at startup (non-blocking)
        check_updates_at_startup(self.root)
        
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
                'export_format': self.export_format_var.get()
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
                priority_folders=priority_folders,
                priority_files=priority_files
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
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Add update check to Help menu
        add_update_check_to_menu(help_menu)
        
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