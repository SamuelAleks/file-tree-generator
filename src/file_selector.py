import os
import tkinter as tk
from tkinter import ttk, messagebox

class FileSelector(tk.Toplevel):
    """Dialog for selecting files and methods from a directory tree"""
    
    def __init__(self, parent, root_dir, file_extension=".cs", include_xaml=True,
               enable_method_selection=False):
        super().__init__(parent)
        self.title("Select Files for Reference Analysis")
        self.geometry("600x700")
        self.minsize(500, 400)
        self.transient(parent)
        self.grab_set()
        
        self.root_dir = root_dir
        self.file_extension = file_extension
        self.include_xaml = include_xaml
        self.enable_method_selection = enable_method_selection
        self.selected_files = []
        self.selected_method = None
        
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
        
        # Method selection frame (only shown when enabled)
        self.method_frame = ttk.LabelFrame(main_frame, text="Method Selection")
        
        if self.enable_method_selection:
            self.method_frame.pack(fill=tk.X, pady=5)
            
            # Method selection tree with scrollbars
            method_tree_frame = ttk.Frame(self.method_frame)
            method_tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Create scrollbars
            method_vsb = ttk.Scrollbar(method_tree_frame, orient="vertical")
            method_vsb.pack(side=tk.RIGHT, fill=tk.Y)
            
            method_hsb = ttk.Scrollbar(method_tree_frame, orient="horizontal")
            method_hsb.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Create method tree
            self.method_tree = ttk.Treeview(method_tree_frame, 
                                         yscrollcommand=method_vsb.set, 
                                         xscrollcommand=method_hsb.set)
            self.method_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Configure scrollbars
            method_vsb.config(command=self.method_tree.yview)
            method_hsb.config(command=self.method_tree.xview)
            
            # Configure method tree
            self.method_tree["columns"] = ("signature", "line")
            self.method_tree.column("#0", width=200, minwidth=150)
            self.method_tree.column("signature", width=300, minwidth=200)
            self.method_tree.column("line", width=50, minwidth=50)
            
            self.method_tree.heading("#0", text="Method", anchor=tk.W)
            self.method_tree.heading("signature", text="Signature", anchor=tk.W)
            self.method_tree.heading("line", text="Line", anchor=tk.W)
            
            # No methods to show initially
            self.update_method_label("No file selected")
            
            # Brief help text
            ttk.Label(self.method_frame, 
                    text="Select a file above to view its methods, then select a method to visualize.",
                    foreground="#666666").pack(pady=5)
        
        # Button frame
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Selection counter
        self.selection_var = tk.StringVar(value="0 files selected")
        ttk.Label(self.button_frame, textvariable=self.selection_var).pack(side=tk.LEFT, padx=5)
        
        # Method info label (only for method selection mode)
        if self.enable_method_selection:
            self.method_label_var = tk.StringVar(value="No method selected")
            self.method_label = ttk.Label(self.button_frame, textvariable=self.method_label_var)
            self.method_label.pack(side=tk.LEFT, padx=(20, 5))
        
        # Buttons
        ttk.Button(self.button_frame, text="Invert Selection", command=self.invert_selection).pack(side=tk.LEFT, padx=5)
        
        # Action buttons depend on mode
        if self.enable_method_selection:
            self.visualize_btn = ttk.Button(self.button_frame, text="Visualize Method", 
                                         command=self.select_method, state=tk.DISABLED)
            self.visualize_btn.pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Button(self.button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(self.button_frame, text="Select", command=self.select).pack(side=tk.RIGHT, padx=5)
        
        # Populate the tree
        self.populate_tree()
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_file_selected)
        
        # Add context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Visualize Code Relationships", 
                                   command=self.visualize_selected)
        
        self.context_menu.add_command(label="Visualize Methods", 
                                   command=self.visualize_methods)
        
        # Bind right-click event
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def update_method_label(self, text):
        """Update the method selection label"""
        if self.enable_method_selection:
            self.method_label_var.set(text)
    
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

    def on_file_selected(self, event=None):
        """Handle file selection event"""
        # Update file selection count
        self.update_selection_count()
        
        # If method selection is enabled, update method tree
        if self.enable_method_selection:
            self.update_methods_for_file()
    
    def update_methods_for_file(self):
        """Update methods list when a file is selected"""
        # Clear existing methods
        for item in self.method_tree.get_children():
            self.method_tree.delete(item)
            
        # Get selected files
        selected = self.tree.selection()
        if not selected:
            self.update_method_label("No file selected")
            if hasattr(self, 'visualize_btn'):
                self.visualize_btn.config(state=tk.DISABLED)
            return
        
        # Only use the first selected file for methods
        item_values = self.tree.item(selected[0], "values")
        if len(item_values) >= 1 and item_values[1] == "file":
            file_path = item_values[0]
            
            # Only process C# files
            if not file_path.lower().endswith('.cs'):
                self.update_method_label("Not a C# file")
                if hasattr(self, 'visualize_btn'):
                    self.visualize_btn.config(state=tk.DISABLED)
                return
            
            # Get methods for this file
            methods = self.get_methods_for_file(file_path)
            
            if not methods:
                self.update_method_label("No methods found in file")
                return
                
            # Group methods by class if possible
            methods_by_class = self.get_methods_by_class(file_path)
            
            # If no grouping available, use flat list
            if not methods_by_class:
                # Add all methods to the tree
                for method_name in sorted(methods):
                    signature = self.get_method_signature(file_path, method_name)
                    line_num = self.get_method_line(file_path, method_name)
                    self.method_tree.insert("", "end", text=method_name, 
                                         values=(signature, line_num))
            else:
                # Add methods grouped by class
                for class_name, class_methods in sorted(methods_by_class.items()):
                    if class_name:
                        class_node = self.method_tree.insert("", "end", text=class_name, open=True)
                    else:
                        class_node = ""  # Root level for methods not in a class
                        
                    for method_name in sorted(class_methods):
                        signature = self.get_method_signature(file_path, method_name)
                        line_num = self.get_method_line(file_path, method_name)
                        self.method_tree.insert(class_node, "end", text=method_name, 
                                             values=(signature, line_num))
            
            self.update_method_label(f"{len(methods)} methods found")
            
            # Enable the visualize button
            if hasattr(self, 'visualize_btn'):
                self.visualize_btn.config(state=tk.NORMAL)
                
            # Bind method selection event
            self.method_tree.bind("<<TreeviewSelect>>", self.on_method_selected)
    
    def on_method_selected(self, event=None):
        """Handle method selection"""
        selected = self.method_tree.selection()
        if not selected:
            self.update_method_label("No method selected")
            return
            
        # Get method name
        item = self.method_tree.item(selected[0])
        method_name = item["text"]
        
        # Skip if this is a class node (no values)
        if not item["values"]:
            self.update_method_label("Please select a method, not a class")
            return
            
        # Update label
        self.update_method_label(f"Selected: {method_name}")
        
        # Store selected method
        self.selected_method = method_name
    
    def get_methods_for_file(self, file_path):
        """Get methods in a file using the reference tracker"""
        # Check if parent app has reference tracker
        parent = self.master
        if hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            # Use reference tracker to get methods
            return parent.reference_tracker.get_methods_in_file(file_path)
        
        # Try to find reference tracker in parent hierarchy
        while parent and not hasattr(parent, 'reference_tracker'):
            if hasattr(parent, 'master'):
                parent = parent.master
            else:
                break
                
        if parent and hasattr(parent, 'reference_tracker') and parent.reference_tracker:
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
    
    def get_methods_by_class(self, file_path):
        """Get methods grouped by their containing class"""
        # Check if parent app has reference tracker with this capability
        parent = self.master
        if hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            
            # Check if the tracker has the method
            if hasattr(tracker.tracker, 'get_methods_by_class'):
                return tracker.tracker.get_methods_by_class(file_path)
        
        # Try to find tracker in parent hierarchy
        while parent and not hasattr(parent, 'reference_tracker'):
            if hasattr(parent, 'master'):
                parent = parent.master
            else:
                break
                
        if parent and hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            if hasattr(tracker.tracker, 'get_methods_by_class'):
                return tracker.tracker.get_methods_by_class(file_path)
        
        # Fallback: just return all methods in a flat structure
        methods = self.get_methods_for_file(file_path)
        if methods:
            return {'': methods}
        return {}
    
    def get_method_signature(self, file_path, method_name):
        """Get the signature of a method"""
        # Check if parent app has reference tracker with this capability
        parent = self.master
        if hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            
            # Check if the tracker has the method
            if hasattr(tracker.tracker, 'get_method_signature'):
                sig_info = tracker.tracker.get_method_signature(file_path, method_name)
                if sig_info:
                    return sig_info.get('signature', '')
        
        # Try to find tracker in parent hierarchy
        while parent and not hasattr(parent, 'reference_tracker'):
            if hasattr(parent, 'master'):
                parent = parent.master
            else:
                break
                
        if parent and hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            if hasattr(tracker.tracker, 'get_method_signature'):
                sig_info = tracker.tracker.get_method_signature(file_path, method_name)
                if sig_info:
                    return sig_info.get('signature', '')
        
        # Fallback: return just the method name
        return f"{method_name}(...)"
    
    def get_method_line(self, file_path, method_name):
        """Get the line number of a method"""
        # Check if parent app has reference tracker with detailed method info
        parent = self.master
        if hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            
            # Check if the tracker has the method details
            method_details = tracker.get_method_details(file_path, method_name)
            if method_details and method_name in method_details:
                return method_details[method_name].get('start_line', 0)
        
        # Try to find tracker in parent hierarchy
        while parent and not hasattr(parent, 'reference_tracker'):
            if hasattr(parent, 'master'):
                parent = parent.master
            else:
                break
                
        if parent and hasattr(parent, 'reference_tracker') and parent.reference_tracker:
            tracker = parent.reference_tracker
            method_details = tracker.get_method_details(file_path, method_name)
            if method_details and method_name in method_details:
                return method_details[method_name].get('start_line', 0)
        
        # Fallback: return 0
        return 0
    
    def visualize_methods(self):
        """Open method visualization for selected file"""
        selected = self.tree.selection()
        if not selected:
            return
            
        # Get the file path
        item = self.tree.item(selected[0])
        values = item["values"]
        if len(values) < 2 or values[1] != "file":
            messagebox.showinfo("Information", "Please select a file to visualize methods")
            return
            
        file_path = values[0]
        
        # Check if it's a C# file
        if not file_path.lower().endswith('.cs'):
            messagebox.showinfo("Information", "Method visualization is only available for C# files")
            return
            
        # Find the visualization manager
        parent = self.master
        visualize_method = None
        
        # First check if parent has the method directly
        if hasattr(parent, 'visualize_method'):
            visualize_method = parent.visualize_method
        else:
            # Try to find it in the parent hierarchy
            while parent and not hasattr(parent, 'visualize_method'):
                if hasattr(parent, 'master'):
                    parent = parent.master
                else:
                    break
                    
            if parent and hasattr(parent, 'visualize_method'):
                visualize_method = parent.visualize_method
        
        # Also check for visualization_manager attribute
        if not visualize_method and hasattr(parent, 'visualization_manager'):
            if hasattr(parent.visualization_manager, 'visualize_method'):
                visualize_method = parent.visualization_manager.visualize_method
        
        # Invoke the visualize method function if found
        if visualize_method:
            # Close this dialog
            self.selected_files = [file_path]
            self.destroy()
            
            # Open the method visualizer
            visualize_method(file_path)
        else:
            messagebox.showinfo("Information", "Method visualization is not available")
    
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
                if hasattr(parent, 'master'):
                    parent = parent.master
                else:
                    break
            
            if parent and hasattr(parent, 'open_code_visualizer'):
                # Close this dialog
                self.selected_files = [file_path]
                self.destroy()
                
                # Open the visualizer
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
    
    def select_method(self):
        """Get selected method and close dialog"""
        if not self.selected_method:
            messagebox.showinfo("Information", "Please select a method from the list")
            return
            
        # Get the file path from the selected file
        selected_files = self.tree.selection()
        if not selected_files:
            messagebox.showinfo("Information", "Please select a file first")
            return
            
        item_values = self.tree.item(selected_files[0], "values")
        if len(item_values) >= 1 and item_values[1] == "file":
            file_path = item_values[0]
            self.selected_files = [file_path]
            
            # Close the dialog
            self.destroy()
            
            # Return via the get_selected_method method
    
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
        self.selected_method = None
        self.destroy()
    
    def get_selected_files(self):
        """Get the list of selected files"""
        return self.selected_files
    
    def get_selected_method(self):
        """Get the selected method name"""
        return self.selected_method