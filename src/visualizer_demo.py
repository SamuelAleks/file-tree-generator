import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from code_visualizer import CodeRelationshipVisualizer, CSharpCodeViewer
from reference_tracking import ReferenceTrackingManager

class VisualizerDemo:
    """Demo application for the improved code visualizer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Code Visualizer Demo")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header label
        header_label = ttk.Label(main_frame, text="Code Visualizer Demo", font=("Arial", 16))
        header_label.pack(pady=10)
        
        # Create instructions label
        instructions = "This demo allows you to visualize C# code relationships and structure.\n" + \
                       "Select a directory containing C# files to start."
        instructions_label = ttk.Label(main_frame, text=instructions)
        instructions_label.pack(pady=10)
        
        # Create directory selection frame
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT, padx=(0, 5))
        self.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        browse_button = ttk.Button(dir_frame, text="Browse...", command=self.browse_directory)
        browse_button.pack(side=tk.LEFT)
        
        # Create file listbox frame
        files_frame = ttk.LabelFrame(main_frame, text="C# Files")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create file listbox with scrollbar
        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Add double-click binding
        self.file_listbox.bind("<Double-1>", self.open_file)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Add buttons
        visualize_button = ttk.Button(button_frame, text="Visualize File", command=self.visualize_file)
        visualize_button.pack(side=tk.LEFT, padx=5)
        
        c_sharp_button = ttk.Button(button_frame, text="C# Viewer", command=self.open_csharp_viewer)
        c_sharp_button.pack(side=tk.LEFT, padx=5)
        
        analyze_button = ttk.Button(button_frame, text="Analyze References", command=self.analyze_references)
        analyze_button.pack(side=tk.LEFT, padx=5)
        
        quit_button = ttk.Button(button_frame, text="Quit", command=root.quit)
        quit_button.pack(side=tk.RIGHT, padx=5)
        
        # Create log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.X, pady=10)
        
        self.log_text = tk.Text(log_frame, height=5, wrap=tk.WORD)
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize variables
        self.files = []
        self.reference_tracker = None
    
    def browse_directory(self):
        """Browse for a directory"""
        directory = filedialog.askdirectory(title="Select Directory with C# Files")
        if directory:
            self.dir_var.set(directory)
            self.scan_directory(directory)
    
    def scan_directory(self, directory):
        """Scan directory for C# files"""
        self.log("Scanning directory for C# files...")
        self.files = []
        self.file_listbox.delete(0, tk.END)
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.cs') or file.lower().endswith(('.xaml', '.axaml')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, directory)
                    self.files.append(full_path)
                    self.file_listbox.insert(tk.END, rel_path)
        
        self.log(f"Found {len(self.files)} C# and XAML files")
    
    def open_file(self, event=None):
        """Open the selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a file to open")
            return
        
        index = selection[0]
        file_path = self.files[index]
        
        # Determine appropriate viewer based on file extension
        if file_path.lower().endswith('.cs') or file_path.lower().endswith(('.xaml', '.axaml')):
            self.ensure_reference_tracker()
            CSharpCodeViewer(self.root, self.reference_tracker, file_path)
        else:
            messagebox.showinfo("Information", "Unsupported file type")
    
    def visualize_file(self):
        """Visualize the selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a file to visualize")
            return
        
        index = selection[0]
        file_path = self.files[index]
        
        self.ensure_reference_tracker()
        CodeRelationshipVisualizer(self.root, self.reference_tracker, file_path)
    
    def open_csharp_viewer(self):
        """Open the C# viewer for the selected file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a file to open")
            return
        
        index = selection[0]
        file_path = self.files[index]
        
        if not file_path.lower().endswith('.cs') and not file_path.lower().endswith(('.xaml', '.axaml')):
            messagebox.showinfo("Information", "Please select a C# or XAML file")
            return
        
        self.ensure_reference_tracker()
        CSharpCodeViewer(self.root, self.reference_tracker, file_path)
    
    def analyze_references(self):
        """Analyze references in the project"""
        if not self.dir_var.get():
            messagebox.showinfo("Information", "Please select a directory first")
            return
        
        self.ensure_reference_tracker()
        
        # Get statistics
        file_count = self.reference_tracker.get_parsed_file_count()
        messagebox.showinfo("Reference Analysis", 
                           f"Analyzed {file_count} files.\n\n"
                           "Select a file and click 'Visualize File' to see its references.")
    
    def ensure_reference_tracker(self):
        """Ensure the reference tracker is initialized"""
        if not self.reference_tracker:
            directory = self.dir_var.get()
            if not directory:
                messagebox.showinfo("Information", "Please select a directory first")
                return
            
            self.log("Initializing reference tracker...")
            self.reference_tracker = ReferenceTrackingManager(directory, self.log)
            self.reference_tracker.parse_directory()
    
    def log(self, message):
        """Add a message to the log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

# Run the demo application
if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerDemo(root)
    root.mainloop()