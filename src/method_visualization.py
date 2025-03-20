import tkinter as ttk
import tkinter as tk
import os
import re

class CodeVisualizer(tk.Toplevel):
    """Advanced code visualization window with method inspection capabilities"""
    
    def __init__(self, parent, reference_tracker, root_dir=None):
        super().__init__(parent)
        self.title("Code Visualization")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        self.parent = parent
        self.reference_tracker = reference_tracker
        self.root_dir = root_dir
        
        # Track current selection
        self.current_file = None
        self.current_method = None
        
        # Create the UI components
        self.create_menu()
        self.create_main_interface()
        # Add navigation history
        self.navigation_history = []
        self.history_position = -1
        
        # Ensure window is properly centered
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Add keyboard bindings
        self.bind('<Alt-Left>', lambda e: self.navigate_back())
        self.bind('<Alt-Right>', lambda e: self.navigate_forward())
        self.bind('<Control-f>', lambda e: self.show_search_dialog())
        self.bind('<Control-r>', lambda e: self.run_layout())
        self.bind('<Control-1>', lambda e: self.center_view())
        self.bind('<Escape>', lambda e: self.reset_view())
        
    def create_menu(self):
        """Create menu bar for the visualization window"""
        menubar = Menu(self)
        self.config(menu=menubar)
    
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Graph...", command=self.export_graph)
        file_menu.add_command(label="Export Method Map...", command=self.export_method_map)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)
    
        # View menu
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Reset View", command=self.reset_view)
        view_menu.add_command(label="Center Graph", command=self.center_graph)
        view_menu.add_separator()
    
        # Create checkbuttons for toggling panels
        self.show_code_var = tk.BooleanVar(value=True)
        self.show_relationships_var = tk.BooleanVar(value=True)
    
        view_menu.add_checkbutton(label="Show Code Panel", 
                               variable=self.show_code_var,
                               command=self.toggle_code_panel)
        view_menu.add_checkbutton(label="Show Relationships Panel", 
                               variable=self.show_relationships_var,
                               command=self.toggle_relationships_panel)
    
        # Graph menu
        graph_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Graph", menu=graph_menu)
        graph_menu.add_command(label="Run Layout", command=self.run_layout)
        graph_menu.add_command(label="Show All Method Names", 
                              command=lambda: self.set_label_visibility(True))
        graph_menu.add_command(label="Hide Method Names", 
                              command=lambda: self.set_label_visibility(False))
    
        # Add Layout submenu
        layout_menu = Menu(graph_menu, tearoff=0)
        graph_menu.add_cascade(label="Layout Style", menu=layout_menu)
        layout_menu.add_command(label="Force-Directed", 
                               command=lambda: self.graph_canvas.run_force_directed_layout())
        layout_menu.add_command(label="Obsidian-Style", 
                               command=lambda: self.graph_canvas.run_obsidian_layout(self.visualization_config))
        layout_menu.add_command(label="Hierarchical", 
                               command=lambda: self.graph_canvas.run_hierarchical_layout())
        layout_menu.add_command(label="Circular", 
                               command=lambda: self.graph_canvas.run_circular_layout())
    
        # Add settings command
        graph_menu.add_separator()
        graph_menu.add_command(label="Visualization Settings...", command=self.show_visualization_settings)
    
        # Add search functionality
        search_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Search", menu=search_menu)
        search_menu.add_command(label="Find Method...", command=self.show_search_dialog)
        search_menu.add_command(label="Find References...", command=self.find_references)
    
        # Store reference to menubar
        self.menubar = menubar

    
    def show_visualization_settings(self):
        """Show visualization settings dialog"""
        dialog = VisualizationConfigDialog(self, self.visualization_config, self.apply_visualization_config)
        self.wait_window(dialog)

    def apply_visualization_config(self, config):
        """Apply visualization configuration"""
        self.visualization_config = config
    
        # Apply to graph canvas
        self.graph_canvas.apply_config(config)
    
        # Apply other UI settings
        if 'font_size' in config:
            font_size = config['font_size']
            self.code_viewer.code_text.configure(font=('Courier', font_size))
    
    def create_main_interface(self):
        """Create the main UI with resizable panels"""
        # Create main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create horizontal paned window (left: graph, right: details)
        self.h_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.h_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Graph visualization
        self.graph_frame = ttk.LabelFrame(self.h_paned, text="Method Graph")
        self.h_paned.add(self.graph_frame, weight=3)
        
        # Create the interactive graph canvas
        self.graph_canvas = InteractiveGraphCanvas(self.graph_frame)
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Contains code view and relationships
        self.details_frame = ttk.Frame(self.h_paned)
        self.h_paned.add(self.details_frame, weight=2)
        
        # Vertical paned window for code and relationships
        self.v_paned = ttk.PanedWindow(self.details_frame, orient=tk.VERTICAL)
        self.v_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top right panel - Code view
        self.code_frame = ttk.LabelFrame(self.v_paned, text="Method Code")
        self.v_paned.add(self.code_frame, weight=3)
        
        # Create enhanced interactive code viewer
        self.code_viewer = InteractiveCodeViewer(self.code_frame, 
                                               on_reference_click=self.navigate_to_method)
        self.code_viewer.pack(fill=tk.BOTH, expand=True)

        
        # Add documentation panel below code view
        self.doc_panel_frame = ttk.LabelFrame(self.code_frame, text="Method Documentation")
        self.doc_panel_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        self.doc_panel = MethodDocPanel(self.doc_panel_frame)
        self.doc_panel.pack(fill=tk.BOTH, expand=True)
        
        # Bottom right panel - Relationships
        self.relationships_frame = ttk.LabelFrame(self.v_paned, text="Method Relationships")
        self.v_paned.add(self.relationships_frame, weight=2)
        
        # Create relationships viewer
        self.relationships_viewer = self.create_relationships_viewer(self.relationships_frame)
        
        # Status bar
        self.status_bar = ttk.Frame(main_container, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Connect graph selection events
        self.graph_canvas.bind("<ButtonRelease-1>", self.on_graph_selection)
    
    def create_code_viewer(self, parent):
        """Create the code viewer component"""
        # Main container for code viewer
        code_container = ttk.Frame(parent)
        code_container.pack(fill=tk.BOTH, expand=True)
        
        # Method info area (displays signature, etc.)
        method_info_frame = ttk.Frame(code_container)
        method_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.method_name_var = tk.StringVar()
        self.method_signature_var = tk.StringVar()
        
        ttk.Label(method_info_frame, textvariable=self.method_name_var, 
                 font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(method_info_frame, textvariable=self.method_signature_var, 
                 font=('Helvetica', 10)).pack(anchor=tk.W)
        
        # Create horizontal separator
        ttk.Separator(code_container, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)
        
        # Text area with syntax highlighting
        code_text_frame = ttk.Frame(code_container)
        code_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Line numbers canvas
        self.line_canvas = tk.Canvas(code_text_frame, width=40, bg='#f0f0f0')
        self.line_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text widget for code
        self.code_text = tk.Text(code_text_frame, wrap=tk.NONE, font=('Courier', 10),
                                bg='#ffffff', fg='#000000', relief=tk.SUNKEN, borderwidth=1)
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure line numbers
        self.code_text.bind('<KeyRelease>', self.update_line_numbers)
        self.code_text.bind('<MouseWheel>', self.update_line_numbers)
        
        # Configure tag for highlighting
        self.code_text.tag_configure('keyword', foreground='blue')
        self.code_text.tag_configure('string', foreground='green')
        self.code_text.tag_configure('comment', foreground='gray')
        self.code_text.tag_configure('method', foreground='purple')
        self.code_text.tag_configure('type', foreground='teal')
        self.code_text.tag_configure('highlight_line', background='#ffffcc')
        
        # Add scrollbars
        xscrollbar = ttk.Scrollbar(code_container, orient=tk.HORIZONTAL, 
                                  command=self.code_text.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        yscrollbar = ttk.Scrollbar(code_text_frame, command=self.code_text.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.code_text.configure(xscrollcommand=xscrollbar.set, 
                                yscrollcommand=yscrollbar.set)
        
        # Make text read-only initially
        self.code_text.config(state=tk.DISABLED)
        
        return code_container
    
    def create_relationships_viewer(self, parent):
        """Create the relationships viewer component"""
        # Container for relationships
        rel_container = ttk.Frame(parent)
        rel_container.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for different relationship types
        self.rel_notebook = ttk.Notebook(rel_container)
        self.rel_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs for different relationship types
        self.calls_frame = self.create_relationship_tab("Calls")
        self.called_by_frame = self.create_relationship_tab("Called By")
        self.uses_frame = self.create_relationship_tab("Uses")
        self.used_by_frame = self.create_relationship_tab("Used By")
        
        self.rel_notebook.add(self.calls_frame, text="Calls")
        self.rel_notebook.add(self.called_by_frame, text="Called By")
        self.rel_notebook.add(self.uses_frame, text="Uses")
        self.rel_notebook.add(self.used_by_frame, text="Used By")
        
        return rel_container
    
    def create_relationship_tab(self, name):
        """Create a tab for relationship display"""
        frame = ttk.Frame(self.rel_notebook)
        
        # Create treeview for relationships
        columns = ('method', 'class', 'file')
        treeview = ttk.Treeview(frame, columns=columns, show='headings')
        
        # Configure columns
        treeview.heading('method', text='Method')
        treeview.heading('class', text='Class')
        treeview.heading('file', text='File')
        
        treeview.column('method', width=150)
        treeview.column('class', width=150)
        treeview.column('file', width=200)
        
        # Add scrollbars
        yscrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=treeview.yview)
        xscrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=treeview.xview)
        
        treeview.configure(yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)
        
        # Layout
        treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to navigate
        treeview.bind('<Double-1>', lambda e, tv=treeview, name=name: self.on_relationship_double_click(e, tv, name))
        
        # Store treeview reference
        setattr(self, f"{name.lower().replace(' ', '_')}_treeview", treeview)
        
        return frame
    
    def on_graph_selection(self, event):
        """Handle node selection in graph with improved code integration"""
        selected_node = self.graph_canvas.selected_node
        if not selected_node or selected_node not in self.graph_canvas.nodes:
            return
        
        node_data = self.graph_canvas.nodes[selected_node]
        if node_data.get('type') != 'method':
            return
        
        # Extract file and method from node ID
        file_path, method_name = node_data.get('file'), node_data.get('method')
        if not file_path or not method_name:
            return
        
        # Update current selection
        self.current_file = file_path
        self.current_method = method_name
    
        # Get method information
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return
    
        # Find references within the method body
        references = self.find_references_in_method(method_info)
    
        # Update code viewer with references for highlighting
        self.code_viewer.display_method(file_path, method_name, method_info, self.reference_tracker, references)
    
        # Highlight related nodes in the graph
        self.highlight_related_nodes(file_path, method_name, references)
    
        # Update relationships panel with enhanced information
        self.update_relationships_with_context(file_path, method_name, references)
    
        # Update status bar
        rel_path = os.path.relpath(file_path, self.root_dir) if self.root_dir else file_path
        self.status_var.set(f"Selected: {method_name} in {rel_path}")
    
    def update_method_details(self, file_path, method_name):
        """Update code viewer with method details"""
        # Get method info
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return
            
        # Use the enhanced code viewer to display the method
        self.code_viewer.display_method(file_path, method_name, method_info, self.reference_tracker)
        
        # Update documentation panel
        self.doc_panel.update_with_method(method_info)
            
        # Update method info display
        class_name = method_info.get('class', '')
        namespace = method_info.get('namespace', '')
        
        if namespace and class_name:
            self.method_name_var.set(f"{namespace}.{class_name}.{method_name}")
        elif class_name:
            self.method_name_var.set(f"{class_name}.{method_name}")
        else:
            self.method_name_var.set(method_name)
            
        self.method_signature_var.set(method_info.get('signature', ''))
        
        # Update code display
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete('1.0', tk.END)
        
        # Get method body
        method_body = method_info.get('body', '')
        if method_body:
            self.code_text.insert('1.0', method_body)
            
            # Apply syntax highlighting
            self.apply_syntax_highlighting(method_body)
            
        # Make text read-only again
        self.code_text.config(state=tk.DISABLED)
        
        # Update line numbers
        self.update_line_numbers()
    
    def apply_syntax_highlighting(self, code):
        """Apply basic syntax highlighting to code text"""
        # Keywords
        keywords = ['public', 'private', 'protected', 'internal', 'static', 'void', 'class',
                   'int', 'string', 'bool', 'double', 'float', 'return', 'new', 'if', 'else',
                   'for', 'foreach', 'while', 'do', 'switch', 'case', 'default', 'try', 'catch',
                   'finally', 'throw', 'using', 'namespace', 'interface', 'abstract', 'virtual',
                   'override', 'readonly', 'const', 'var', 'delegate', 'event', 'async', 'await']
                   
        for keyword in keywords:
            start_pos = '1.0'
            while True:
                start_pos = self.code_text.search(r'\b' + keyword + r'\b', start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(keyword)}c"
                self.code_text.tag_add('keyword', start_pos, end_pos)
                start_pos = end_pos
                
        # Strings
        start_pos = '1.0'
        while True:
            start_pos = self.code_text.search(r'"[^"]*"', start_pos, tk.END, regexp=True)
            if not start_pos:
                break
            content = self.code_text.get(start_pos, tk.END)
            match = re.search(r'"[^"]*"', content)
            if match:
                end_pos = f"{start_pos}+{len(match.group(0))}c"
                self.code_text.tag_add('string', start_pos, end_pos)
                start_pos = end_pos
            else:
                break
                
        # Comments
        start_pos = '1.0'
        while True:
            start_pos = self.code_text.search(r'//.*$', start_pos, tk.END, regexp=True)
            if not start_pos:
                break
            line = int(float(start_pos))
            end_pos = f"{line}.end"
            self.code_text.tag_add('comment', start_pos, end_pos)
            start_pos = f"{line + 1}.0"
    
    def update_line_numbers(self, event=None):
        """Update line numbers in the canvas"""
        self.line_canvas.delete("all")
        
        # Get visible lines
        first_line = int(float(self.code_text.index("@0,0")))
        last_line = int(float(self.code_text.index(f"@0,{self.code_text.winfo_height()}")))
        
        # Draw line numbers
        for i in range(first_line, last_line + 1):
            y = self.code_text.dlineinfo(f"{i}.0")
            if y:
                self.line_canvas.create_text(20, y[1], anchor="n", text=i, font=('Courier', 10))
    
    def update_relationships(self, file_path, method_name):
        """Update relationships display"""
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return
            
        # Clear existing data
        for treeview_name in ['calls_treeview', 'called_by_treeview', 'uses_treeview', 'used_by_treeview']:
            treeview = getattr(self, treeview_name, None)
            if treeview:
                for item in treeview.get_children():
                    treeview.delete(item)
                    
        # Add method calls
        for call_info in method_info.get('calls', []):
            target_method = call_info.get('method', '')
            target_class = call_info.get('target_class', '')
            target_file = call_info.get('target_file', '')
            
            # Get relative path if root directory is set
            if target_file and self.root_dir:
                try:
                    target_file = os.path.relpath(target_file, self.root_dir)
                except ValueError:
                    pass
                    
            self.calls_treeview.insert('', tk.END, values=(target_method, target_class, target_file))
            
        # Add methods calling this method
        for caller_info in method_info.get('called_by', []):
            caller_method = caller_info.get('method', '')
            caller_file = caller_info.get('file', '')
            
            # Get class from file info if available
            caller_class = ''
            if caller_file in self.reference_tracker.file_info:
                file_info = self.reference_tracker.file_info[caller_file]
                caller_class = file_info.get('types', [''])[0]
                
            # Get relative path if root directory is set
            if caller_file and self.root_dir:
                try:
                    caller_file = os.path.relpath(caller_file, self.root_dir)
                except ValueError:
                    pass
                    
            self.called_by_treeview.insert('', tk.END, values=(caller_method, caller_class, caller_file))
            
        # Add objects used by this method
        for obj in method_info.get('objects', []):
            if isinstance(obj, dict):
                obj_type = obj.get('type', '')
                obj_class = obj.get('class', '')
                self.uses_treeview.insert('', tk.END, values=(obj_class, obj_type, ''))
            else:
                self.uses_treeview.insert('', tk.END, values=(obj, 'variable', ''))
                
        # Add variables used by this method
        for var in method_info.get('variables', []):
            self.uses_treeview.insert('', tk.END, values=(var, 'variable', ''))
    
    def on_relationship_double_click(self, event, treeview, tab_name):
        """Handle double-click on relationship item"""
        # Get selected item
        item = treeview.selection()[0]
        if not item:
            return
            
        # Get data
        values = treeview.item(item, 'values')
        if not values or len(values) < 3:
            return
            
        method_name, class_name, file_path = values
        
        # Convert relative path to absolute if needed
        if self.root_dir and not os.path.isabs(file_path):
            file_path = os.path.join(self.root_dir, file_path)
            
        # Skip if file does not exist
        if not os.path.exists(file_path):
            return
            
        # Navigate to related method
        self.navigate_to_method(file_path, method_name)
    
    def navigate_to_method(self, file_path, method_name):
        """Navigate to specified method in graph and update history"""
        # Check if method exists
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return
            
        # Add to navigation history - first remove any forward history
        if self.history_position < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.history_position + 1]
            
        # Add current method to history
        self.navigation_history.append((file_path, method_name))
        self.history_position = len(self.navigation_history) - 1
        
        # Update navigation menu
        self.update_navigation_menu()
            
        # Check if node exists in graph
        node_id = f"{file_path}::{method_name}"
        if node_id not in self.graph_canvas.nodes:
            # Method not in current graph - ask if user wants to rebuild graph
            if messagebox.askyesno("Method Not Found", 
                                 f"Method {method_name} is not in the current graph view. "
                                 f"Would you like to rebuild the graph starting from this method?"):
                self.build_graph_for_method(file_path, method_name)
            return
            
        # Select the node
        self.graph_canvas.selected_node = node_id
        
        # Center view on the node
        self.graph_canvas.center_on_node(node_id)
        
        # Update UI
        self.on_graph_selection(None)
    
    def navigate_back(self):
        """Navigate back in history"""
        if self.history_position <= 0:
            return
            
        self.history_position -= 1
        file_path, method_name = self.navigation_history[self.history_position]
        
        # Temporarily disable history to avoid adding a new entry
        old_history = self.navigation_history
        old_position = self.history_position
        self.navigation_history = []
        
        # Navigate to the method
        self._navigate_without_history(file_path, method_name)
        
        # Restore history
        self.navigation_history = old_history
        self.history_position = old_position
        
        # Update menu
        self.update_navigation_menu()
    
    def navigate_forward(self):
        """Navigate forward in history"""
        if self.history_position >= len(self.navigation_history) - 1:
            return
            
        self.history_position += 1
        file_path, method_name = self.navigation_history[self.history_position]
        
        # Temporarily disable history to avoid adding a new entry
        old_history = self.navigation_history
        old_position = self.history_position
        self.navigation_history = []
        
        # Navigate to the method
        self._navigate_without_history(file_path, method_name)
        
        # Restore history
        self.navigation_history = old_history
        self.history_position = old_position
        
        # Update menu
        self.update_navigation_menu()
    
    def _navigate_without_history(self, file_path, method_name):
        """Navigate to method without updating history"""
        # Check if method exists
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return
            
        # Check if node exists in graph
        node_id = f"{file_path}::{method_name}"
        if node_id not in self.graph_canvas.nodes:
            # Build graph for this method
            self.build_graph_for_method(file_path, method_name)
            return
            
        # Select the node
        self.graph_canvas.selected_node = node_id
        
        # Center view on the node
        self.graph_canvas.center_on_node(node_id)
        
        # Update UI
        self.on_graph_selection(None)

    def update_navigation_menu(self):
        """Update navigation menu state based on history"""
        # Enable/disable back button
        back_state = "normal" if self.history_position > 0 else "disabled"
        self.navigation_menu.entryconfig("Back", state=back_state)
        
        # Enable/disable forward button
        forward_state = "normal" if self.history_position < len(self.navigation_history) - 1 else "disabled"
        self.navigation_menu.entryconfig("Forward", state=forward_state)
    
    def show_history(self):
        """Show navigation history dialog"""
        if not self.navigation_history:
            messagebox.showinfo("History", "No navigation history available")
            return
            
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Navigation History")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Create listbox with scrollbar
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=('Courier', 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Add history items
        for i, (file_path, method_name) in enumerate(self.navigation_history):
            # Get relative path if possible
            display_path = file_path
            if self.root_dir:
                try:
                    display_path = os.path.relpath(file_path, self.root_dir)
                except ValueError:
                    pass
                    
            # Add prefix to show current position
            prefix = "→ " if i == self.history_position else "  "
            
            listbox.insert(tk.END, f"{prefix}{method_name} ({display_path})")
            
            # Highlight current position
            if i == self.history_position:
                listbox.itemconfig(i, background='#ffffcc')
        
        # Ensure current position is visible
        listbox.see(self.history_position)
        
        # Create buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Function to navigate to selected history item
        def go_to_selected():
            selected = listbox.curselection()
            if not selected:
                return
                
            index = selected[0]
            file_path, method_name = self.navigation_history[index]
            
            # Set history position
            self.history_position = index
            
            # Close dialog
            dialog.destroy()
            
            # Navigate to method
            self._navigate_without_history(file_path, method_name)
            
            # Update menu
            self.update_navigation_menu()
        
        ttk.Button(button_frame, text="Go To Selected", command=go_to_selected).pack(side=tk.RIGHT, padx=5)
        
        # Bind double-click
        listbox.bind('<Double-1>', lambda e: go_to_selected())
    
    def build_graph_for_method(self, file_path, method_name):
        """Build and display graph starting from specified method"""
        try:
            # Get call graph data - make sure to access tracker attribute
            if hasattr(self.reference_tracker, 'tracker'):
                # For ReferenceTrackingManager
                graph_data = self.reference_tracker.tracker.get_method_call_graph(file_path, method_name)
            else:
                # Direct access if it's already a CSharpReferenceTracker
                graph_data = self.reference_tracker.get_method_call_graph(file_path, method_name)
            
            if not graph_data:
                messagebox.showerror("Error", f"Could not build graph for {method_name}")
                return
            
            # Update graph canvas
            self.graph_canvas.set_graph(graph_data['nodes'], graph_data['edges'])
            self.graph_canvas.draw_graph()
        
            # Select the starting node
            node_id = f"{file_path}::{method_name}"
            self.graph_canvas.selected_node = node_id
            self.graph_canvas.center_on_node(node_id)
        
            # Update UI
            self.on_graph_selection(None)
        except Exception as e:
            error_msg = f"Error building graph: {str(e)}"
            print(error_msg)  # Print to console for debugging
            messagebox.showerror("Graph Error", error_msg)
    
    # Additional methods for menu actions
    def export_graph(self):
        """Export current graph as an image"""
        self.graph_canvas.export_as_image()
    
    def export_method_map(self):
        """Export method relationships to a file"""
        # Implementation depends on desired output format
        pass
    
    def reset_view(self):
        """Reset graph view"""
        self.graph_canvas.reset_view()
    
    def center_graph(self):
        """Center graph in view"""
        self.graph_canvas.center_view()
    
    def toggle_code_panel(self):
        """Show/hide code panel"""
        if self.show_code_var.get():
            self.v_paned.add(self.code_frame, weight=3)
        else:
            self.v_paned.forget(self.code_frame)
    
    def toggle_relationships_panel(self):
        """Show/hide relationships panel"""
        if self.show_relationships_var.get():
            self.v_paned.add(self.relationships_frame, weight=2)
        else:
            self.v_paned.forget(self.relationships_frame)
    
    def run_layout(self):
        """Run force-directed layout"""
        self.graph_canvas.run_force_directed_layout()
    
    def set_label_visibility(self, visible):
        """Set label visibility in graph"""
        self.graph_canvas.set_label_visibility(visible)
    
    def show_search_dialog(self):
        """Show dialog to search for methods"""
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Search Methods")
        dialog.geometry("400x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Search frame
        search_frame = ttk.Frame(dialog, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create treeview for results
        results_frame = ttk.Frame(dialog, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('method', 'class', 'file')
        treeview = ttk.Treeview(results_frame, columns=columns, show='headings')
        
        # Configure columns
        treeview.heading('method', text='Method')
        treeview.heading('class', text='Class')
        treeview.heading('file', text='File')
        
        treeview.column('method', width=150)
        treeview.column('class', width=100)
        treeview.column('file', width=200)
        
        # Add scrollbars
        yscrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=treeview.yview)
        
        treeview.configure(yscrollcommand=yscrollbar.set)
        
        # Layout
        treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Navigate", 
                 command=lambda: self.navigate_to_search_result(treeview, dialog)).pack(side=tk.RIGHT, padx=5)
        
        # Function to update search results
        def update_search_results(*args):
            search_text = search_var.get().lower()
            if len(search_text) < 2:
                return
                
            # Clear existing results
            for item in treeview.get_children():
                treeview.delete(item)
                
            # Search all methods
            for file_path, file_info in self.reference_tracker.file_info.items():
                if 'method_details' not in file_info:
                    continue
                    
                for method_name, method_info in file_info['method_details'].items():
                    if search_text in method_name.lower():
                        # Get class name
                        class_name = method_info.get('class', '')
                        
                        # Get relative path if root directory is set
                        display_path = file_path
                        if self.root_dir:
                            try:
                                display_path = os.path.relpath(file_path, self.root_dir)
                            except ValueError:
                                pass
                                
                        # Add to results
                        treeview.insert('', tk.END, values=(method_name, class_name, display_path))
        
        # Connect search variable to update function
        search_var.trace_add('write', update_search_results)
        
        # Bind double-click
        treeview.bind('<Double-1>', lambda e: self.navigate_to_search_result(treeview, dialog))
        
        # Focus search entry
        search_entry.focus_set()
    
    def navigate_to_search_result(self, treeview, dialog):
        """Navigate to selected search result"""
        # Get selected item
        selection = treeview.selection()
        if not selection:
            return
            
        # Get data
        values = treeview.item(selection[0], 'values')
        if not values or len(values) < 3:
            return
            
        method_name, class_name, file_path = values
        
        # Convert relative path to absolute if needed
        if self.root_dir and not os.path.isabs(file_path):
            file_path = os.path.join(self.root_dir, file_path)
            
        # Close dialog
        dialog.destroy()
        
        # Navigate to method
        self.navigate_to_method(file_path, method_name)
    
    def find_references(self):
        """Find all references to a method"""
        # Similar to search but focuses on references
        pass

# Add to method_visualization.py - New VisualizationConfigDialog class

class VisualizationConfigDialog(tk.Toplevel):
    """Dialog for configuring visualization options"""
    
    def __init__(self, parent, config=None, apply_callback=None):
        super().__init__(parent)
        self.title("Visualization Settings")
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()
        
        self.parent = parent
        self.config = config or {}
        self.apply_callback = apply_callback
        
        # Set up notebook with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.appearance_tab = self.create_appearance_tab()
        self.layout_tab = self.create_layout_tab()
        self.behavior_tab = self.create_behavior_tab()
        
        self.notebook.add(self.appearance_tab, text="Appearance")
        self.notebook.add(self.layout_tab, text="Layout")
        self.notebook.add(self.behavior_tab, text="Behavior")
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply", command=self.apply_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=self.save_and_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Initialize values from config
        self.initialize_values()
        
    def create_appearance_tab(self):
        """Create appearance settings tab"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Color scheme
        ttk.Label(frame, text="Color Scheme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.color_scheme_var = tk.StringVar()
        color_combo = ttk.Combobox(frame, textvariable=self.color_scheme_var, width=20)
        color_combo['values'] = ('Default', 'Dark', 'Light', 'Colorful', 'Monochrome')
        color_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Node size
        ttk.Label(frame, text="Node Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.node_size_var = tk.IntVar()
        ttk.Scale(frame, from_=8, to=30, variable=self.node_size_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Edge thickness
        ttk.Label(frame, text="Edge Thickness:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.edge_thickness_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.5, to=5.0, variable=self.edge_thickness_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Font size
        ttk.Label(frame, text="Label Font Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.font_size_var = tk.IntVar()
        ttk.Scale(frame, from_=8, to=16, variable=self.font_size_var).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Label visibility options
        ttk.Label(frame, text="Label Visibility:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.label_visibility_var = tk.StringVar()
        visibility_combo = ttk.Combobox(frame, textvariable=self.label_visibility_var, width=20)
        visibility_combo['values'] = ('Always Show', 'Show on Hover', 'Show Selected', 'Hide All')
        visibility_combo.grid(row=4, column=1, sticky=tk.W, padx=5)
        
        return frame
        
    def create_layout_tab(self):
        """Create layout settings tab"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Auto layout toggle
        self.auto_layout_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Enable Automatic Layout", 
                       variable=self.auto_layout_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Layout algorithm
        ttk.Label(frame, text="Layout Algorithm:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.layout_algorithm_var = tk.StringVar()
        algorithm_combo = ttk.Combobox(frame, textvariable=self.layout_algorithm_var, width=20)
        algorithm_combo['values'] = ('Force-Directed', 'Hierarchical', 'Circular', 'Radial', 'Grid')
        algorithm_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Layout alignment
        ttk.Label(frame, text="Alignment:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.alignment_var = tk.StringVar()
        alignment_combo = ttk.Combobox(frame, textvariable=self.alignment_var, width=20)
        alignment_combo['values'] = ('Center', 'Left-to-Right', 'Top-to-Bottom', 'Bottom-to-Top')
        alignment_combo.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Spacing
        ttk.Label(frame, text="Node Spacing:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.node_spacing_var = tk.IntVar()
        ttk.Scale(frame, from_=50, to=300, variable=self.node_spacing_var).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Edge length
        ttk.Label(frame, text="Edge Length:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.edge_length_var = tk.IntVar()
        ttk.Scale(frame, from_=50, to=300, variable=self.edge_length_var).grid(row=4, column=1, sticky=tk.W, padx=5)
        
        # Obsidian-like settings section
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        ttk.Label(frame, text="Obsidian-like Graph Layout", font=('Helvetica', 10, 'bold')).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Centering force
        ttk.Label(frame, text="Centering Force:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.center_force_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.center_force_var).grid(row=7, column=1, sticky=tk.W, padx=5)
        
        # Repulsion strength
        ttk.Label(frame, text="Node Repulsion:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.repulsion_var = tk.DoubleVar()
        ttk.Scale(frame, from_=50, to=500, variable=self.repulsion_var).grid(row=8, column=1, sticky=tk.W, padx=5)
        
        # Connection strength
        ttk.Label(frame, text="Connection Strength:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.connection_strength_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.01, to=1.0, variable=self.connection_strength_var).grid(row=9, column=1, sticky=tk.W, padx=5)
        
        return frame
        
    def create_behavior_tab(self):
        """Create behavior settings tab"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Animation speed
        ttk.Label(frame, text="Animation Speed:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.animation_speed_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.1, to=2.0, variable=self.animation_speed_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Hover delay
        ttk.Label(frame, text="Tooltip Delay (ms):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tooltip_delay_var = tk.IntVar()
        ttk.Scale(frame, from_=100, to=2000, variable=self.tooltip_delay_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Double click action
        ttk.Label(frame, text="Double-Click Action:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.double_click_var = tk.StringVar()
        double_click_combo = ttk.Combobox(frame, textvariable=self.double_click_var, width=20)
        double_click_combo['values'] = ('Expand Node', 'Go to Definition', 'Show Details', 'Center View')
        double_click_combo.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Selection behavior
        ttk.Label(frame, text="Selection Mode:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.selection_mode_var = tk.StringVar()
        selection_mode_combo = ttk.Combobox(frame, textvariable=self.selection_mode_var, width=20)
        selection_mode_combo['values'] = ('Single', 'Multiple', 'Toggle')
        selection_mode_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Auto-refresh
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Auto-Refresh Graph on Selection", 
                       variable=self.auto_refresh_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        return frame
        
    def initialize_values(self):
        """Initialize values from config"""
        # Appearance
        self.color_scheme_var.set(self.config.get('color_scheme', 'Default'))
        self.node_size_var.set(self.config.get('node_size', 15))
        self.edge_thickness_var.set(self.config.get('edge_thickness', 1.5))
        self.font_size_var.set(self.config.get('font_size', 10))
        self.label_visibility_var.set(self.config.get('label_visibility', 'Show Selected'))
        
        # Layout
        self.auto_layout_var.set(self.config.get('auto_layout', True))
        self.layout_algorithm_var.set(self.config.get('layout_algorithm', 'Force-Directed'))
        self.alignment_var.set(self.config.get('alignment', 'Center'))
        self.node_spacing_var.set(self.config.get('node_spacing', 100))
        self.edge_length_var.set(self.config.get('edge_length', 150))
        self.center_force_var.set(self.config.get('center_force', 0.1))
        self.repulsion_var.set(self.config.get('repulsion', 200))
        self.connection_strength_var.set(self.config.get('connection_strength', 0.3))
        
        # Behavior
        self.animation_speed_var.set(self.config.get('animation_speed', 1.0))
        self.tooltip_delay_var.set(self.config.get('tooltip_delay', 500))
        self.double_click_var.set(self.config.get('double_click_action', 'Go to Definition'))
        self.selection_mode_var.set(self.config.get('selection_mode', 'Single'))
        self.auto_refresh_var.set(self.config.get('auto_refresh', False))
        
    def get_config(self):
        """Get config values from UI"""
        config = {
            # Appearance
            'color_scheme': self.color_scheme_var.get(),
            'node_size': self.node_size_var.get(),
            'edge_thickness': self.edge_thickness_var.get(),
            'font_size': self.font_size_var.get(),
            'label_visibility': self.label_visibility_var.get(),
            
            # Layout
            'auto_layout': self.auto_layout_var.get(),
            'layout_algorithm': self.layout_algorithm_var.get(),
            'alignment': self.alignment_var.get(),
            'node_spacing': self.node_spacing_var.get(),
            'edge_length': self.edge_length_var.get(),
            'center_force': self.center_force_var.get(),
            'repulsion': self.repulsion_var.get(),
            'connection_strength': self.connection_strength_var.get(),
            
            # Behavior
            'animation_speed': self.animation_speed_var.get(),
            'tooltip_delay': self.tooltip_delay_var.get(),
            'double_click_action': self.double_click_var.get(),
            'selection_mode': self.selection_mode_var.get(),
            'auto_refresh': self.auto_refresh_var.get(),
        }
        return config
        
    def apply_settings(self):
        """Apply settings without closing dialog"""
        if self.apply_callback:
            self.apply_callback(self.get_config())
            
    def save_and_close(self):
        """Save settings and close dialog"""
        self.apply_settings()
        self.destroy()