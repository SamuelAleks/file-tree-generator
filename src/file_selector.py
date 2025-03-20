import os
import tkinter as tk
from tkinter import ttk, messagebox

class FileSelector(tk.Toplevel):
    """Dialog for selecting files from a directory tree for reference tracking"""
    
    def __init__(self, parent, root_dir, file_extension=".cs", include_xaml=True):
        super().__init__(parent)
        self.title("Select Files for Reference Analysis")
        self.geometry("600x700")
        self.minsize(500, 400)
        self.transient(parent)
        self.grab_set()
        
        self.root_dir = root_dir
        self.file_extension = file_extension
        self.include_xaml = include_xaml
        self.selected_files = []
        
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Select files to analyze for references:").pack(anchor=tk.W, pady=(0, 5))
        
        # File filter options
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Add XAML file toggle
        self.include_xaml_var = tk.BooleanVar(value=include_xaml)
        ttk.Checkbutton(filter_frame, text="Include XAML/AXAML Files", 
                       variable=self.include_xaml_var,
                       command=self.refresh_tree).grid(row=0, column=0, sticky=tk.W)
        
        # Add quick filter buttons
        ttk.Button(filter_frame, text="C# Files Only", 
                  command=lambda: self.filter_by_extension('.cs')).grid(row=0, column=1, padx=5)
        ttk.Button(filter_frame, text="XAML Files Only", 
                  command=lambda: self.filter_by_extension(('.xaml', '.axaml'))).grid(row=0, column=2, padx=5)
        ttk.Button(filter_frame, text="Show All", 
                  command=self.show_all_files).grid(row=0, column=3, padx=5)
        
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
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Selection counter
        self.selection_var = tk.StringVar(value="0 files selected")
        ttk.Label(self.button_frame, textvariable=self.selection_var).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        ttk.Button(self.button_frame, text="Invert Selection", command=self.invert_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="Select", command=self.select).pack(side=tk.RIGHT, padx=5)
        
        # Populate the tree
        self.populate_tree()
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_file_selected)

    def on_file_selected(self, event=None):
        """Handle file selection event"""
        # Update file selection count
        self.update_selection_count()
    
    def filter_by_extension(self, extensions):
        """Filter the tree to show only files with specific extensions"""
        # Make sure extensions is a tuple or list
        if isinstance(extensions, str):
            extensions = (extensions,)
            
        # First unselect all
        for item_id in self.tree.selection():
            self.tree.selection_remove(item_id)
            
        # Then select files with matching extensions
        for item_id in self.get_all_items():
            item_type = self.tree.item(item_id, "values")[1]
            if item_type == "file":
                file_path = self.tree.item(item_id, "values")[0]
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in extensions:
                    self.tree.see(item_id)  # Scroll to make visible
                    self.tree.selection_add(item_id)
                    
        self.update_selection_count()
    
    def show_all_files(self):
        """Show all files (clear filters)"""
        self.include_xaml_var.set(True)
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the tree when filter options change"""
        # Remember the current selection
        selected_paths = [self.tree.item(item_id, "values")[0] 
                        for item_id in self.tree.selection() 
                        if self.tree.item(item_id, "values")[1] == "file"]
    
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Repopulate the tree
        self.populate_tree()
    
        # Restore selection where possible
        for item_id in self.get_all_items():
            item_type = self.tree.item(item_id, "values")[1]
            if item_type == "file":
                file_path = self.tree.item(item_id, "values")[0]
                if file_path in selected_paths:
                    self.tree.selection_add(item_id)
                
        self.update_selection_count()
    
    def get_all_items(self):
        """Get all items in the tree recursively"""
        def collect_items(parent):
            items = list(self.tree.get_children(parent))
            for item in items.copy():
                items.extend(collect_items(item))
            return items
            
        return collect_items('')
    
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
                if os.path.isfile(item_path):
                    file_ext = os.path.splitext(item)[1].lower()
                    
                    # Check if it's a C# file or a XAML file that should be included
                    if file_ext == self.file_extension or \
                       (self.include_xaml_var.get() and file_ext in ('.xaml', '.axaml')):
                        # Determine icon based on file type
                        icon = "📄"  # Default icon
                        if file_ext in ('.xaml', '.axaml'):
                            icon = "🖼️"  # Special icon for XAML files
                            
                        self.tree.insert(parent_node, "end", text=f"{icon} {item}", 
                                        values=(item_path, "file"))
        except (PermissionError, FileNotFoundError):
            # Handle permission errors or deleted directories
            pass
    
    def has_matching_files(self, directory):
        """Check if a directory contains any matching files (recursively)"""
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext == self.file_extension or \
                       (self.include_xaml_var.get() and file_ext in ('.xaml', '.axaml')):
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
        """Invert the current selection more efficiently"""
        all_items = self.get_all_files()
        current_selection = self.tree.selection()
    
        # Select items that weren't previously selected and deselect those that were
        for item_id in all_items:
            if item_id in current_selection:
                self.tree.selection_remove(item_id)
            else:
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