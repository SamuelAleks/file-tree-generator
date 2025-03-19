import os
import tkinter as tk
from tkinter import ttk, messagebox, Canvas, simpledialog
import re
from typing import Dict, List, Set, Tuple, Optional, Any

class MethodNode:
    """Represents a method node in the visualization canvas"""
    def __init__(self, canvas, x, y, method_name, file_path, signature="", content=""):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.method_name = method_name
        self.file_path = file_path
        self.signature = signature
        self.content = content
        self.width = 200
        self.height = 100
        self.canvas_objects = []
        self.referenced_by = []  # Methods that reference this one
        self.references_to = []  # Methods that this method references
        
        # Create visual representation
        self.create_node()
        
    def create_node(self):
        """Create the visual representation of the node"""
        # Create node rectangle
        rect = self.canvas.create_rectangle(
            self.x, self.y, 
            self.x + self.width, self.y + self.height,
            fill="#e1f5fe", outline="#0288d1", width=2,
            tags=("method_node", self.method_name)
        )
        self.canvas_objects.append(rect)
        
        # Create title bar
        title_rect = self.canvas.create_rectangle(
            self.x, self.y,
            self.x + self.width, self.y + 25,
            fill="#0288d1", outline="#0288d1",
            tags=("method_node", self.method_name)
        )
        self.canvas_objects.append(title_rect)
        
        # Method name text
        text = self.canvas.create_text(
            self.x + 10, self.y + 12,
            text=self.method_name,
            anchor=tk.W,
            fill="white",
            font=("Arial", 10, "bold"),
            tags=("method_node", self.method_name)
        )
        self.canvas_objects.append(text)
        
        # Show file path
        file_text = self.canvas.create_text(
            self.x + 10, self.y + 35,
            text=os.path.basename(self.file_path),
            anchor=tk.W,
            fill="#333333",
            font=("Arial", 8),
            tags=("method_node", self.method_name)
        )
        self.canvas_objects.append(file_text)
        
        # Show short snippet of content
        content_preview = self.get_content_preview(self.content, 3)
        content_text = self.canvas.create_text(
            self.x + 10, self.y + 55,
            text=content_preview,
            anchor=tk.NW,
            fill="#333333",
            font=("Consolas", 8),
            width=self.width - 20,
            tags=("method_node", self.method_name)
        )
        self.canvas_objects.append(content_text)
        
        # Make node draggable
        for obj in self.canvas_objects:
            self.canvas.tag_bind(obj, "<ButtonPress-1>", self.on_press)
            self.canvas.tag_bind(obj, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(obj, "<Double-1>", self.on_double_click)
    
    def get_content_preview(self, content, max_lines=3):
        """Get a short preview of the method content"""
        if not content:
            return "// No content available"
            
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
            
        # Return first few lines
        return '\n'.join(lines[:max_lines]) + "\n..."
    
    def on_press(self, event):
        """Handle mouse press on the node"""
        # Record initial position for drag operation
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
        # Raise this node to the top
        for obj in self.canvas_objects:
            self.canvas.tag_raise(obj)
    
    def on_drag(self, event):
        """Handle dragging the node"""
        # Calculate movement delta
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        
        # Move all objects in the node
        for obj in self.canvas_objects:
            self.canvas.move(obj, dx, dy)
        
        # Update node position
        self.x += dx
        self.y += dy
        
        # Update drag start position
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
        # Update connection lines if any
        if hasattr(self.canvas, 'update_connections'):
            self.canvas.update_connections(self)
    
    def on_double_click(self, event):
        """Handle double-click on the node"""
        # Show detailed view of the method
        if hasattr(self.canvas, 'show_method_details'):
            self.canvas.show_method_details(self)
        
    def get_center(self):
        """Get the center point of the node for connection lines"""
        return (self.x + self.width // 2, self.y + self.height // 2)
        
    def get_top_center(self):
        """Get the top center point for incoming connections"""
        return (self.x + self.width // 2, self.y)
        
    def get_bottom_center(self):
        """Get the bottom center point for outgoing connections"""
        return (self.x + self.width // 2, self.y + self.height)
        
    def get_left_center(self):
        """Get the left center point for connections"""
        return (self.x, self.y + self.height // 2)
        
    def get_right_center(self):
        """Get the right center point for connections"""
        return (self.x + self.width, self.y + self.height // 2)


class MethodRelationshipVisualizer(tk.Toplevel):
    """
    Visualizer for method relationships with canvas-based interactive display.
    
    Features:
    - Canvas for visualizing method nodes
    - Drag-and-drop rearrangement of nodes
    - Connection lines between related methods
    - Method content display
    - Navigation between referenced methods
    """
    def __init__(self, parent, reference_tracker, file_path: str, method_name: str, theme="light"):
        super().__init__(parent)
        self.title(f"Method Relationship Visualizer - {method_name}")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.reference_tracker = reference_tracker
        self.file_path = file_path
        self.method_name = method_name
        self.theme = theme
        self.nodes = {}  # Map of method_name -> MethodNode
        self.connections = []  # List of connection lines
        
        # Set theme colors
        self.set_theme(theme)
        
        # Create UI
        self.create_ui()
        
        # Load the method data
        self.load_method_data(file_path, method_name)
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
    
    def set_theme(self, theme):
        """Set color theme for the visualizer"""
        if theme == "dark":
            self.bg_color = "#282c34"
            self.canvas_bg = "#21252b"
            self.text_color = "#abb2bf"
            self.highlight_color = "#61afef"
            self.node_bg = "#333842"
            self.node_title_bg = "#4d78cc"
        else:  # light theme
            self.bg_color = "#f5f5f5"
            self.canvas_bg = "#ffffff"
            self.text_color = "#383a42"
            self.highlight_color = "#4078f2"
            self.node_bg = "#e1f5fe"
            self.node_title_bg = "#0288d1"
    
    def create_ui(self):
        """Create the UI components"""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Method info
        ttk.Label(self.toolbar, text="Method:").pack(side=tk.LEFT, padx=(0, 5))
        self.method_label = ttk.Label(self.toolbar, text=self.method_name)
        self.method_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(self.toolbar, text="File:").pack(side=tk.LEFT, padx=(10, 5))
        self.file_label = ttk.Label(self.toolbar, text=os.path.basename(self.file_path))
        self.file_label.pack(side=tk.LEFT)
        
        # Depth control
        ttk.Label(self.toolbar, text="Depth:").pack(side=tk.LEFT, padx=(20, 5))
        self.depth_var = tk.IntVar(value=1)
        depth_spinner = ttk.Spinbox(self.toolbar, from_=0, to=3, textvariable=self.depth_var, 
                                   width=5, command=self.on_depth_changed)
        depth_spinner.pack(side=tk.LEFT)
        
        # Display options
        self.show_incoming_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.toolbar, text="Show Incoming", variable=self.show_incoming_var,
                       command=self.update_display).pack(side=tk.LEFT, padx=(20, 5))
        
        self.show_outgoing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.toolbar, text="Show Outgoing", variable=self.show_outgoing_var,
                       command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        # Layout options
        ttk.Button(self.toolbar, text="Auto Layout", 
                  command=self.auto_layout).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(self.toolbar, text="Reset Zoom", 
                  command=self.reset_zoom).pack(side=tk.RIGHT, padx=5)
        
        # Split frame for canvas and details panel
        self.split_frame = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for visualization
        self.canvas_frame = ttk.Frame(self.split_frame)
        self.split_frame.add(self.canvas_frame, weight=3)
        
        self.canvas = Canvas(self.canvas_frame, bg=self.canvas_bg)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Canvas scrollbars
        self.hscrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hscrollbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.vscrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vscrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        
        self.canvas.configure(xscrollcommand=self.hscrollbar.set, yscrollcommand=self.vscrollbar.set)
        
        # Make canvas scrollable with mouse wheel
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        
        # Configure canvas for zoom and pan
        self.canvas.bind("<ButtonPress-2>", self.on_canvas_press)
        self.canvas.bind("<B2-Motion>", self.on_canvas_drag)
        
        # Details panel
        self.details_frame = ttk.Frame(self.split_frame)
        self.split_frame.add(self.details_frame, weight=1)
        
        # Method details
        self.details_notebook = ttk.Notebook(self.details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Details tab
        self.details_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.details_tab, text="Details")
        
        # Add code display with scrolling
        self.code_frame = ttk.LabelFrame(self.details_tab, text="Method Code")
        self.code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Code text widget
        self.code_text = tk.Text(self.code_frame, wrap=tk.NONE, font=("Consolas", 10))
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add code scrollbars
        code_vscroll = ttk.Scrollbar(self.code_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        code_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.configure(yscrollcommand=code_vscroll.set)
        
        code_hscroll = ttk.Scrollbar(self.details_tab, orient=tk.HORIZONTAL, command=self.code_text.xview)
        code_hscroll.pack(fill=tk.X)
        self.code_text.configure(xscrollcommand=code_hscroll.set)
        
        # Incoming references tab
        self.incoming_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.incoming_tab, text="Incoming (0)")
        
        # Incoming references list
        self.incoming_frame = ttk.Frame(self.incoming_tab)
        self.incoming_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # List of methods that reference this method
        self.incoming_tree = ttk.Treeview(self.incoming_frame, columns=("file", "line"))
        self.incoming_tree.heading("#0", text="Method")
        self.incoming_tree.heading("file", text="File")
        self.incoming_tree.heading("line", text="Line")
        self.incoming_tree.column("#0", width=150)
        self.incoming_tree.column("file", width=150)
        self.incoming_tree.column("line", width=50)
        self.incoming_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        incoming_scroll = ttk.Scrollbar(self.incoming_frame, orient=tk.VERTICAL, command=self.incoming_tree.yview)
        incoming_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.incoming_tree.configure(yscrollcommand=incoming_scroll.set)
        
        self.incoming_tree.bind("<Double-1>", self.on_incoming_selected)
        
        # Outgoing references tab
        self.outgoing_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.outgoing_tab, text="Outgoing (0)")
        
        # Outgoing references list
        self.outgoing_frame = ttk.Frame(self.outgoing_tab)
        self.outgoing_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # List of methods this method references
        self.outgoing_tree = ttk.Treeview(self.outgoing_frame, columns=("file", "line"))
        self.outgoing_tree.heading("#0", text="Method")
        self.outgoing_tree.heading("file", text="File")
        self.outgoing_tree.heading("line", text="Line")
        self.outgoing_tree.column("#0", width=150)
        self.outgoing_tree.column("file", width=150)
        self.outgoing_tree.column("line", width=50)
        self.outgoing_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        outgoing_scroll = ttk.Scrollbar(self.outgoing_frame, orient=tk.VERTICAL, command=self.outgoing_tree.yview)
        outgoing_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.outgoing_tree.configure(yscrollcommand=outgoing_scroll.set)
        
        self.outgoing_tree.bind("<Double-1>", self.on_outgoing_selected)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def load_method_data(self, file_path, method_name):
        """Load data for the main method"""
        if not self.reference_tracker:
            self.status_var.set("Error: No reference tracker available")
            return
            
        # Get method details
        self.status_var.set(f"Loading method details for {method_name}...")
        method_details = self.reference_tracker.get_method_details(file_path, method_name)
        
        if not method_details or method_name not in method_details:
            self.status_var.set(f"Error: Could not find method {method_name} in {file_path}")
            return
        
        method_info = method_details[method_name]
        self.method_signature = method_info.get('signature', method_name)
        self.method_content = method_info.get('content', '')
        
        # Update details display
        self.code_text.delete('1.0', tk.END)
        self.code_text.insert('1.0', self.method_content)
        
        # Apply basic syntax highlighting to code
        self.apply_syntax_highlighting()
        
        # Get references
        self.status_var.set("Loading method references...")
        incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(file_path, method_name)
        
        # Create the main method node at the center
        center_x = self.canvas.winfo_width() // 2 - 100
        center_y = self.canvas.winfo_height() // 2 - 50
        
        if center_x < 100:  # Ensure a reasonable default if width is not yet known
            center_x = 300
        if center_y < 50:  # Ensure a reasonable default if height is not yet known
            center_y = 200
            
        main_node = MethodNode(
            self.canvas, center_x, center_y, 
            method_name, file_path, 
            self.method_signature, self.method_content
        )
        self.nodes[method_name] = main_node
        
        # Update references lists
        self.update_references_lists(incoming_refs, outgoing_refs)
        
        # Show initial nodes based on depth setting
        self.update_display()
        
        self.status_var.set(f"Method {method_name} loaded successfully.")
    
    def update_references_lists(self, incoming_refs, outgoing_refs):
        """Update the references list displays"""
        # Clear existing items
        for item in self.incoming_tree.get_children():
            self.incoming_tree.delete(item)
            
        for item in self.outgoing_tree.get_children():
            self.outgoing_tree.delete(item)
        
        # Add incoming references
        for ref in incoming_refs:
            ref_method = ref.get('method', 'Unknown')
            ref_file = os.path.basename(ref.get('file', 'Unknown'))
            ref_line = ref.get('line', 0)
            
            self.incoming_tree.insert("", "end", text=ref_method, values=(ref_file, ref_line))
        
        # Add outgoing references
        for ref in outgoing_refs:
            ref_method = ref.get('method', 'Unknown')
            ref_file = os.path.basename(ref.get('file', 'Unknown'))
            ref_line = ref.get('line', 0)
            
            self.outgoing_tree.insert("", "end", text=ref_method, values=(ref_file, ref_line))
        
        # Update tab labels with counts
        self.details_notebook.tab(1, text=f"Incoming ({len(incoming_refs)})")
        self.details_notebook.tab(2, text=f"Outgoing ({len(outgoing_refs)})")
    
    def apply_syntax_highlighting(self):
        """Apply simple syntax highlighting to the code text"""
        # This is a basic implementation - you might want to use a more sophisticated
        # syntax highlighting library in production
        
        # Configure tags for highlighting
        self.code_text.tag_configure("keyword", foreground="#0000FF")
        self.code_text.tag_configure("string", foreground="#008000")
        self.code_text.tag_configure("comment", foreground="#808080", font=("Consolas", 10, "italic"))
        
        # Find keywords
        keywords = ["public", "private", "protected", "internal", "static", "void", "class", 
                   "int", "string", "bool", "var", "new", "return", "if", "else", "for", 
                   "foreach", "while", "using", "namespace", "try", "catch", "throw"]
        
        for keyword in keywords:
            start = "1.0"
            while True:
                start = self.code_text.search(r'\b' + keyword + r'\b', start, tk.END, regexp=True)
                if not start:
                    break
                    
                end = f"{start}+{len(keyword)}c"
                self.code_text.tag_add("keyword", start, end)
                start = end
        
        # Find strings (basic approximation)
        start = "1.0"
        while True:
            start = self.code_text.search(r'"[^"]*"', start, tk.END, regexp=True)
            if not start:
                break
                
            content = self.code_text.get(start, tk.END)
            match = re.search(r'^"[^"]*"', content)
            if match:
                end = f"{start}+{len(match.group(0))}c"
                self.code_text.tag_add("string", start, end)
                start = end
            else:
                break
        
        # Find comments
        start = "1.0"
        while True:
            start = self.code_text.search(r'//.*', start, tk.END, regexp=True)
            if not start:
                break
                
            line_end = self.code_text.search(r'\n', start, tk.END)
            if not line_end:
                line_end = tk.END
                
            self.code_text.tag_add("comment", start, line_end)
            start = line_end
    
    def update_display(self):
        """Update the display based on the depth setting"""
        # Clear existing nodes except the main one
        main_node = self.nodes.get(self.method_name)
        
        if not main_node:
            self.status_var.set("Error: Main method node not found")
            return
            
        # Clear all nodes and connections
        for node_name, node in list(self.nodes.items()):
            if node_name != self.method_name:
                for obj in node.canvas_objects:
                    self.canvas.delete(obj)
                del self.nodes[node_name]
        
        for conn in self.connections:
            self.canvas.delete(conn)
        self.connections = []
        
        # Get the current depth setting
        depth = self.depth_var.get()
        
        # Whether to show incoming and/or outgoing references
        show_incoming = self.show_incoming_var.get()
        show_outgoing = self.show_outgoing_var.get()
        
        if depth > 0:
            # Get references
            incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(
                self.file_path, self.method_name)
            
            # Process incoming references if enabled
            if show_incoming and incoming_refs:
                self.add_reference_nodes(incoming_refs, main_node, is_incoming=True, angle_start=0, angle_end=180)
            
            # Process outgoing references if enabled
            if show_outgoing and outgoing_refs:
                self.add_reference_nodes(outgoing_refs, main_node, is_incoming=False, angle_start=180, angle_end=360)
            
            # Update connections
            self.update_all_connections()
        
        self.status_var.set(f"Display updated. Showing {len(self.nodes)} methods.")
    
    def add_reference_nodes(self, refs, parent_node, is_incoming=True, radius=200, 
                          angle_start=0, angle_end=360):
        """Add reference nodes around the parent node"""
        import math
        
        if not refs:
            return
            
        # Number of nodes to place
        node_count = len(refs)
        
        # Calculate the placement of each node around the parent
        parent_x, parent_y = parent_node.get_center()
        
        # Calculate angle step
        angle_range = angle_end - angle_start
        angle_step = angle_range / max(1, node_count)
        
        for i, ref in enumerate(refs):
            ref_method = ref.get('method', 'Unknown')
            ref_file = ref.get('file', 'Unknown')
            
            # Skip if method name is unknown or already exists
            if ref_method == 'Unknown' or ref_method in self.nodes:
                continue
                
            # Calculate position
            angle = math.radians(angle_start + i * angle_step)
            x = parent_x + radius * math.cos(angle) - 100  # Offset by half node width
            y = parent_y + radius * math.sin(angle) - 50   # Offset by half node height
            
            # Create the node
            node = MethodNode(
                self.canvas, x, y,
                ref_method, ref_file
            )
            self.nodes[ref_method] = node
            
            # Create connection
            self.create_connection(parent_node, node, is_incoming)
    
    def create_connection(self, source_node, target_node, is_incoming):
        """Create a visual connection between two nodes"""
        if is_incoming:
            # Incoming reference: target -> source
            src_x, src_y = target_node.get_bottom_center()
            dst_x, dst_y = source_node.get_top_center()
            # Calculate arrow points
            arrow_color = "#FF5722"  # Orange for incoming
        else:
            # Outgoing reference: source -> target
            src_x, src_y = source_node.get_bottom_center()
            dst_x, dst_y = target_node.get_top_center()
            # Calculate arrow points
            arrow_color = "#4CAF50"  # Green for outgoing
        
        # Create the line with arrow
        conn = self.canvas.create_line(
            src_x, src_y, dst_x, dst_y,
            width=2, 
            fill=arrow_color, 
            arrow=tk.LAST,
            arrowshape=(10, 12, 5),
            smooth=True
        )
        self.connections.append(conn)
        
        # Ensure the line is below the nodes
        self.canvas.tag_lower(conn)
        
        return conn
    
    def update_connections(self, node):
        """Update all connections associated with a node"""
        # For simplicity, just redraw all connections
        self.update_all_connections()
    
    def update_all_connections(self):
        """Update all connection lines"""
        # Clear existing connections
        for conn in self.connections:
            self.canvas.delete(conn)
        self.connections = []
        
        # Get the main node
        main_node = self.nodes.get(self.method_name)
        if not main_node:
            return
            
        # Get all other nodes
        other_nodes = {name: node for name, node in self.nodes.items() if name != self.method_name}
        
        # Get references
        incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(
            self.file_path, self.method_name)
            
        # Create incoming connections
        if self.show_incoming_var.get():
            for ref in incoming_refs:
                ref_method = ref.get('method', 'Unknown')
                if ref_method in other_nodes:
                    self.create_connection(main_node, other_nodes[ref_method], True)
        
        # Create outgoing connections
        if self.show_outgoing_var.get():
            for ref in outgoing_refs:
                ref_method = ref.get('method', 'Unknown')
                if ref_method in other_nodes:
                    self.create_connection(main_node, other_nodes[ref_method], False)
    
    def on_depth_changed(self):
        """Handle depth value changes"""
        self.update_display()
    
    def on_mousewheel(self, event):
        """Handle mousewheel events for scrolling"""
        # Determine scroll direction based on platform
        if event.num == 4 or event.delta > 0:
            # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            # Scroll down
            self.canvas.yview_scroll(1, "units")
    
    def on_canvas_press(self, event):
        """Handle canvas press for panning"""
        self.canvas.scan_mark(event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag for panning"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def auto_layout(self):
        """Apply an automatic layout to the nodes"""
        # Get the main node
        main_node = self.nodes.get(self.method_name)
        if not main_node:
            return
            
        # Center the main node
        center_x = self.canvas.winfo_width() // 2 - 100
        center_y = self.canvas.winfo_height() // 2 - 50
        
        # Move the main node
        dx = center_x - main_node.x
        dy = center_y - main_node.y
        
        for obj in main_node.canvas_objects:
            self.canvas.move(obj, dx, dy)
        
        main_node.x = center_x
        main_node.y = center_y
        
        # Arrange other nodes in a circle
        self.update_display()
    
    def reset_zoom(self):
        """Reset the canvas view"""
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
    
    def on_incoming_selected(self, event):
        """Handle selection of an incoming reference"""
        selection = self.incoming_tree.selection()
        if not selection:
            return
            
        selected_item = self.incoming_tree.item(selection[0])
        method_name = selected_item['text']
        file_path = selected_item['values'][0]
        
        # Highlight the node if it exists in the canvas
        if method_name in self.nodes:
            node = self.nodes[method_name]
            # Flash the node to highlight it
            for obj in node.canvas_objects:
                self.canvas.itemconfig(obj, width=3)
                self.after(500, lambda o=obj: self.canvas.itemconfig(o, width=1))
        else:
            # Ask if the user wants to navigate to this method
            if messagebox.askyesno("Navigation", 
                                 f"Method '{method_name}' is not displayed in the current view. "
                                 f"Do you want to open it in a new visualizer?"):
                self.show_method_details_by_name(method_name, file_path)
    
    def on_outgoing_selected(self, event):
        """Handle selection of an outgoing reference"""
        selection = self.outgoing_tree.selection()
        if not selection:
            return
            
        selected_item = self.outgoing_tree.item(selection[0])
        method_name = selected_item['text']
        file_path = selected_item['values'][0]
        
        # Highlight the node if it exists in the canvas
        if method_name in self.nodes:
            node = self.nodes[method_name]
            # Flash the node to highlight it
            for obj in node.canvas_objects:
                self.canvas.itemconfig(obj, width=3)
                self.after(500, lambda o=obj: self.canvas.itemconfig(o, width=1))
        else:
            # Ask if the user wants to navigate to this method
            if messagebox.askyesno("Navigation", 
                                 f"Method '{method_name}' is not displayed in the current view. "
                                 f"Do you want to open it in a new visualizer?"):
                self.show_method_details_by_name(method_name, file_path)
    
    def show_method_details(self, node):
        """Show detailed view of a method"""
        # For now, just navigate to a new visualizer for the method
        self.show_method_details_by_name(node.method_name, node.file_path)
    
    def show_method_details_by_name(self, method_name, file_path):
        """Open a new visualizer for the specified method"""
        # Find the full file path based on the file name
        # This is a simplified approach - in a real app, you'd have a better way to map
        # file names to full paths
        full_path = file_path
        if os.path.exists(file_path):
            full_path = file_path
        elif os.path.isfile(os.path.join(os.path.dirname(self.file_path), file_path)):
            full_path = os.path.join(os.path.dirname(self.file_path), file_path)
        else:
            # Try to find the file in the reference tracker's known files
            for known_file in self.reference_tracker.tracker.file_info:
                if os.path.basename(known_file) == file_path:
                    full_path = known_file
                    break
        
        # Open a new visualizer
        try:
            MethodRelationshipVisualizer(
                self.master, 
                self.reference_tracker, 
                full_path, 
                method_name, 
                theme=self.theme
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not open method visualizer: {str(e)}")