import os
import tkinter as tk
from tkinter import ttk

class FileSelector(tk.Toplevel):
    """Dialog for selecting files from a directory tree"""
    
    def __init__(self, parent, root_dir, file_extension=".cs"):
        super().__init__(parent)
        self.title("Select Files for Reference Analysis")
        self.geometry("500x600")
        self.minsize(400, 400)
        self.transient(parent)
        self.grab_set()
        
        self.root_dir = root_dir
        self.file_extension = file_extension
        self.selected_files = []
        
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Select files to analyze for references:").pack(anchor=tk.W, pady=(0, 5))
        
        # File tree display with scrollbars
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create treeview with checkboxes
        self.tree = ttk.Treeview(tree_frame, selectmode="extended", 
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure tree columns
        self.tree["columns"] = ("fullpath", "type")
        self.tree.column("#0", width=250, minwidth=150, stretch=tk.YES)
        self.tree.column("fullpath", width=250, minwidth=200, stretch=tk.YES)
        self.tree.column("type", width=50, minwidth=50, stretch=tk.NO)
        
        # Configure tree headings
        self.tree.heading("#0", text="Directory Structure", anchor=tk.W)
        self.tree.heading("fullpath", text="Full Path", anchor=tk.W)
        self.tree.heading("type", text="Type", anchor=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Selection counter
        self.selection_var = tk.StringVar(value="0 files selected")
        ttk.Label(button_frame, textvariable=self.selection_var).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        ttk.Button(button_frame, text="Invert Selection", command=self.invert_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Select", command=self.select).pack(side=tk.RIGHT, padx=5)
        
        # Populate the tree
        self.populate_tree()
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.update_selection_count)
    
    def populate_tree(self):
        """Populate the tree with files from the root directory"""
        # Insert the root node
        root_node = self.tree.insert("", 0, text=os.path.basename(self.root_dir), 
                                     values=(self.root_dir, "directory"), open=True)
        
        # Recursively add all directories and C# files
        self.add_files_to_tree(self.root_dir, root_node)
    
    def add_files_to_tree(self, parent_dir, parent_node):
        """Add directories and files to the tree"""
        try:
            # Get all items in the directory
            items = sorted(os.listdir(parent_dir))
            
            # First add subdirectories
            for item in items:
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path):
                    # Check if directory contains any matching files before adding
                    if self.has_matching_files(item_path):
                        node = self.tree.insert(parent_node, "end", text=item, 
                                               values=(item_path, "directory"), open=False)
                        self.add_files_to_tree(item_path, node)
            
            # Then add files
            for item in items:
                item_path = os.path.join(parent_dir, item)
                if os.path.isfile(item_path) and item.endswith(self.file_extension):
                    self.tree.insert(parent_node, "end", text=item, 
                                    values=(item_path, "file"))
        except (PermissionError, FileNotFoundError):
            # Handle permission errors or deleted directories
            pass
    
    def has_matching_files(self, directory):
        """Check if a directory contains any matching files (recursively)"""
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(self.file_extension):
                        return True
            return False
        except (PermissionError, FileNotFoundError):
            return False
    
    def update_selection_count(self, event=None):
        """Update the count of selected files"""
        selected_items = self.tree.selection()
        file_count = 0
        
        for item_id in selected_items:
            item_type = self.tree.item(item_id, "values")[1]
            if item_type == "file":
                file_count += 1
        
        self.selection_var.set(f"{file_count} files selected")
    
    def invert_selection(self):
        """Invert the current selection"""
        all_items = self.get_all_files()
        current_selection = self.tree.selection()
        
        # Deselect all items
        for item_id in current_selection:
            self.tree.selection_remove(item_id)
        
        # Select items that weren't previously selected
        for item_id in all_items:
            if item_id not in current_selection:
                self.tree.selection_add(item_id)
        
        self.update_selection_count()
    
    def get_all_files(self):
        """Get all file items in the tree"""
        file_items = []
        
        def get_children(node):
            for child in self.tree.get_children(node):
                item_type = self.tree.item(child, "values")[1]
                if item_type == "file":
                    file_items.append(child)
                get_children(child)
        
        get_children("")
        return file_items
    
    def select(self):
        """Get selected files and close dialog"""
        selected_items = self.tree.selection()
        self.selected_files = []
        
        for item_id in selected_items:
            item_type = self.tree.item(item_id, "values")[1]
            if item_type == "file":
                file_path = self.tree.item(item_id, "values")[0]
                self.selected_files.append(file_path)
        
        self.destroy()
    
    def cancel(self):
        """Cancel selection and close dialog"""
        self.selected_files = []
        self.destroy()
    
    def get_selected_files(self):
        """Get the list of selected files"""
        return self.selected_files