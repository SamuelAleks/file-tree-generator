import tkinter as tk
import os


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
        graph_menu.add_command(label="Show All Method Names", command=lambda: self.set_label_visibility(True))
        graph_menu.add_command(label="Hide Method Names", command=lambda: self.set_label_visibility(False))
        
        # Add search functionality
        search_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Search", menu=search_menu)
        search_menu.add_command(label="Find Method...", command=self.show_search_dialog)
        search_menu.add_command(label="Find References...", command=self.find_references)
        
        # Add navigation menu
        navigation_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Navigation", menu=navigation_menu)
        navigation_menu.add_command(label="Back", command=self.navigate_back, state="disabled")
        navigation_menu.add_command(label="Forward", command=self.navigate_forward, state="disabled")
        navigation_menu.add_separator()
        navigation_menu.add_command(label="History...", command=self.show_history)

        
        # Update menu items with keyboard shortcuts
        file_menu.add_command(label="Export Graph... (Ctrl+E)", command=self.export_graph)
        view_menu.add_command(label="Reset View (Esc)", command=self.reset_view)
        view_menu.add_command(label="Center Graph (Ctrl+1)", command=self.center_graph)
        graph_menu.add_command(label="Run Layout (Ctrl+R)", command=self.run_layout)
        search_menu.add_command(label="Find Method... (Ctrl+F)", command=self.show_search_dialog)
        navigation_menu.add_command(label="Back (Alt+Left)", command=self.navigate_back, state="disabled")
        navigation_menu.add_command(label="Forward (Alt+Right)", command=self.navigate_forward, state="disabled")
        
        
        # Store reference to navigation menu
        self.navigation_menu = navigation_menu
    
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
        """Handle node selection in graph"""
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
        
        # Update UI
        self.update_method_details(file_path, method_name)
        self.update_relationships(file_path, method_name)
        
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