﻿import os
import tkinter as tk
from tkinter import ttk, messagebox

class FileSelector(tk.Toplevel):
    """Dialog for selecting files from a directory tree"""
    
    def __init__(self, parent, root_dir, file_extension=".cs", include_xaml=True):
        super().__init__(parent)
        self.title("Select Files for Reference Analysis")
        self.geometry("500x600")
        self.minsize(400, 400)
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
        
        # Add context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Visualize Code Relationships", 
                                   command=self.visualize_selected)
        
        # Bind right-click event
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Get item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            # Select the item
            self.tree.selection_set(item)
            # Show context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def add_method_selection(self):
        """Add method selection to the dialog"""
        method_frame = ttk.Frame(self)
        method_frame.pack(fill=tk.X, padx=10, pady=5, before=self.button_frame)
    
        ttk.Label(method_frame, text="Select Method:").pack(side=tk.LEFT, padx=(0, 5))
    
        self.method_var = tk.StringVar()
        self.method_combo = ttk.Combobox(method_frame, textvariable=self.method_var, width=40)
        self.method_combo.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
    
        # Add visualization button
        self.method_viz_button = ttk.Button(method_frame, text="Visualize Method", 
                                          command=self.visualize_method, state=tk.DISABLED)
        self.method_viz_button.pack(side=tk.RIGHT, padx=5)
    
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.update_methods_for_file)

    def update_methods_for_file(self, event=None):
        """Update methods list when a file is selected"""
        selected = self.tree.selection()
        if not selected:
            self.method_combo.set('')
            self.method_combo['values'] = []
            self.method_viz_button.config(state=tk.DISABLED)
            return
        
        # Get the file path
        item_values = self.tree.item(selected[0], "values")
        if len(item_values) >= 1 and item_values[1] == "file":
            file_path = item_values[0]
        
            # Only update for .cs files
            if not file_path.lower().endswith('.cs'):
                self.method_combo.set('')
                self.method_combo['values'] = []
                self.method_viz_button.config(state=tk.DISABLED)
                return
            
            # Get methods for this file
            methods = self.get_methods_for_file(file_path)
        
            if methods:
                self.method_combo['values'] = methods
                self.method_combo.current(0)
                self.method_viz_button.config(state=tk.NORMAL)
            else:
                self.method_combo.set('')
                self.method_combo['values'] = []
                self.method_viz_button.config(state=tk.DISABLED)

    def get_methods_for_file(self, file_path):
        """Get methods in a file using the reference tracker"""
        # Check if parent app has reference tracker
        parent = self.master
        while parent and not hasattr(parent, 'reference_tracker'):
            parent = parent.master
    
        if parent and hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            # Use reference tracker to get methods
            return parent.reference_tracker.get_methods_in_file(file_path)
    
        # Fallback: parse methods from file content directly
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            # Basic method detection regex
            method_pattern = r'(?:public|private|protected|internal)\s+(?:(?:virtual|override|abstract|static|async)\s+)*(?:[\w<>[\],\s]+\s+)(\w+)\s*\('
            methods = re.findall(method_pattern, content)
            return methods
        except Exception:
            return []

    def visualize_method(self):
        """Visualize the selected method"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # Get the file path
        item_values = self.tree.item(selected[0], "values")
        if len(item_values) >= 1 and item_values[1] == "file":
            file_path = item_values[0]
            method_name = self.method_var.get()
        
            if not method_name:
                return
        
            # Check if parent app has visualizer method
            parent = self.master
            while parent and not hasattr(parent, 'open_method_visualizer'):
                parent = parent.master
        
            if parent and hasattr(parent, 'open_method_visualizer'):
                parent.open_method_visualizer(file_path, method_name)
            else:
                # Try to find visualizer in the code_visualizer_integration
                if hasattr(parent, 'visualizer') and hasattr(parent.visualizer, 'open_method_visualizer'):
                    parent.visualizer.open_method_visualizer(file_path, method_name)
                else:
                    messagebox.showinfo("Information", "Method visualizer not available in this context.")
    
    def visualize_selected(self):
        """Visualize selected file"""
        selected = self.tree.selection()
        if not selected:
            return
            
        # Get the file path
        item_values = self.tree.item(selected[0], "values")
        if len(item_values) >= 1 and item_values[1] == "file":
            file_path = item_values[0]
            
            # Check if parent app has visualizer method
            parent = self.master
            while parent and not hasattr(parent, 'open_code_visualizer'):
                parent = parent.master
            
            if parent and hasattr(parent, 'open_code_visualizer'):
                parent.open_code_visualizer(file_path)
            else:
                messagebox.showinfo("Information", "Code visualizer not available in this context.")
    
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