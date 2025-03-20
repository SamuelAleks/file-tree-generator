import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from method_relationship_visualizer import MethodRelationshipVisualizer, MethodNode

# Enhancement 1: Improved Node Selection and Highlighting
def enhance_method_node():
    """
    Enhances the MethodNode class with improved selection and drag-and-drop
    """
    # Add these methods to the MethodNode class
    
    def highlight_as_selected(self):
        """Highlight this node as the currently selected node"""
        # Store original colors
        self._original_fill = self.canvas.itemcget(self.canvas_objects[0], "fill")
        self._original_outline = self.canvas.itemcget(self.canvas_objects[0], "outline")
        
        # Apply highlighting
        self.canvas.itemconfig(self.canvas_objects[0], fill="#ffdd99", outline="#ff9900", width=3)
        
        # Call canvas's node selected method if available
        if hasattr(self.canvas, 'on_node_selected'):
            self.canvas.on_node_selected(self)
    
    def remove_highlight(self):
        """Remove the selection highlight"""
        # Restore original colors if stored
        if hasattr(self, '_original_fill') and hasattr(self, '_original_outline'):
            self.canvas.itemconfig(self.canvas_objects[0], 
                                 fill=self._original_fill, 
                                 outline=self._original_outline,
                                 width=2)

    # Override the on_press method to include selection
    def on_press(self, event):
        """Handle mouse press on the node"""
        # Record initial position for drag operation
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
        # Raise this node to the top
        for obj in self.canvas_objects:
            self.canvas.tag_raise(obj)
        
        # Select this node
        if hasattr(self.canvas, 'select_node'):
            self.canvas.select_node(self)
    
    # Replace methods in MethodNode class
    MethodNode.highlight_as_selected = highlight_as_selected
    MethodNode.remove_highlight = remove_highlight
    MethodNode.on_press = on_press


# Enhancement 2: Improved Canvas with Drag-and-Drop Support
class EnhancedMethodCanvas(tk.Canvas):
    """Enhanced canvas with better support for method visualization"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.nodes = {}  # Dictionary of method_name -> MethodNode
        self.connections = []  # List of connection lines
        self.selected_node = None
        self.reference_tracker = None
        
        # Bind events for drag-and-drop
        self.bind("<ButtonPress-1>", self.on_canvas_press)
        self.bind("<B1-Motion>", self.on_canvas_drag)
        self.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Right-click context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Add Related Methods", command=self.add_related_methods)
        self.context_menu.add_command(label="Remove Selected Node", command=self.remove_selected_node)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Auto Layout", command=self.auto_layout)
        self.context_menu.add_command(label="Clear All", command=self.clear_all)
        
        self.bind("<Button-3>", self.show_context_menu)
        
        # Drag-and-drop state
        self._drag_data = {"x": 0, "y": 0, "item": None}
        self._dragging = False
        
    def set_reference_tracker(self, reference_tracker):
        """Set the reference tracker for this canvas"""
        self.reference_tracker = reference_tracker
        
    def add_method_node(self, method_name, file_path, x=None, y=None):
        """Add a method node to the canvas"""
        # Skip if already added
        if method_name in self.nodes:
            return self.nodes[method_name]
            
        # Get method details from reference tracker
        method_info = {}
        if self.reference_tracker:
            method_details = self.reference_tracker.get_method_details(file_path, method_name)
            if method_name in method_details:
                method_info = method_details[method_name]
        
        # Use provided position or calculate a new one
        if x is None or y is None:
            # Place in the center if this is the first node
            if not self.nodes:
                x = self.winfo_width() // 2 - 100
                y = self.winfo_height() // 2 - 50
            else:
                # Otherwise, offset from the selected node
                if self.selected_node:
                    x = self.selected_node.x + 250
                    y = self.selected_node.y
                else:
                    # Place in a grid pattern
                    x = 100 + (len(self.nodes) % 3) * 250
                    y = 100 + (len(self.nodes) // 3) * 150
        
        # Create the node
        node = MethodNode(
            self, x, y,
            method_name, file_path,
            method_info.get('signature', f"{method_name}(...)"),
            method_info.get('content', "// No content available")
        )
        
        # Store in nodes dictionary
        self.nodes[method_name] = node
        
        # Select the new node
        self.select_node(node)
        
        return node
    
    def add_connection(self, source_node, target_node, is_incoming=False):
        """Add a connection between two nodes"""
        if is_incoming:
            # Incoming reference: target -> source
            src_x, src_y = target_node.get_right_center()
            dst_x, dst_y = source_node.get_left_center()
            arrow_color = "#FF5722"  # Orange for incoming
        else:
            # Outgoing reference: source -> target
            src_x, src_y = source_node.get_right_center()
            dst_x, dst_y = target_node.get_left_center()
            arrow_color = "#4CAF50"  # Green for outgoing
        
        # Create the line with arrow
        conn = self.create_line(
            src_x, src_y, dst_x, dst_y,
            width=2, 
            fill=arrow_color, 
            arrow=tk.LAST,
            arrowshape=(10, 12, 5),
            smooth=True,
            tags="connection"
        )
        
        # Store source and target nodes with the connection
        self.connections.append((conn, source_node, target_node, is_incoming))
        
        # Ensure the line is below the nodes
        self.tag_lower(conn)
        
        return conn
    
    def update_connections(self):
        """Update all connections between nodes"""
        # Remove existing connections
        for conn, _, _, _ in self.connections:
            self.delete(conn)
        
        # Create new connections
        new_connections = []
        for conn, source, target, is_incoming in self.connections:
            new_conn = self.add_connection(source, target, is_incoming)
            new_connections.append((new_conn, source, target, is_incoming))
        
        # Update the connections list
        self.connections = new_connections
    
    def select_node(self, node):
        """Select a node and deselect the previously selected one"""
        # Deselect previously selected node
        if self.selected_node and self.selected_node != node:
            self.selected_node.remove_highlight()
        
        # Select the new node
        self.selected_node = node
        node.highlight_as_selected()
        
        # Notify parent if needed
        if hasattr(self, "on_node_selected"):
            self.on_node_selected(node)
    
    def on_canvas_press(self, event):
        """Handle mouse press on the canvas"""
        # Record the coordinates for potential drag operation
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._dragging = False
    
    def on_canvas_drag(self, event):
        """Handle mouse drag on the canvas"""
        # Calculate the distance moved
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        
        # If drag distance is significant, start dragging
        if abs(dx) > 5 or abs(dy) > 5:
            self._dragging = True
            
            # Move all nodes
            for node in self.nodes.values():
                node.x += dx
                node.y += dy
                for obj in node.canvas_objects:
                    self.move(obj, dx, dy)
            
            # Update connections
            self.update_connections()
            
            # Update drag data
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
    
    def on_canvas_release(self, event):
        """Handle mouse release on the canvas"""
        # Reset drag data
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0
        self._drag_data["item"] = None
        self._dragging = False
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Update context menu based on selection
        if self.selected_node:
            self.context_menu.entryconfig(0, state=tk.NORMAL)  # Add Related Methods
            self.context_menu.entryconfig(1, state=tk.NORMAL)  # Remove Selected Node
        else:
            self.context_menu.entryconfig(0, state=tk.DISABLED)
            self.context_menu.entryconfig(1, state=tk.DISABLED)
        
        # Show the menu
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def add_related_methods(self):
        """Add methods related to the selected node"""
        if not self.selected_node or not self.reference_tracker:
            return
            
        # Get references for the selected method
        incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(
            self.selected_node.file_path, self.selected_node.method_name)
        
        # Add incoming references
        for ref in incoming_refs:
            method_name = ref.get('method', 'Unknown')
            file_path = ref.get('file', 'Unknown')
            
            # Skip if the method name is unknown or already in the canvas
            if method_name == 'Unknown' or method_name in self.nodes:
                continue
                
            # Add the node with a position to the left of the selected node
            x = self.selected_node.x - 250
            y = self.selected_node.y - 50 + len(self.nodes) * 20
            node = self.add_method_node(method_name, file_path, x, y)
            
            # Add connection
            self.add_connection(self.selected_node, node, is_incoming=True)
        
        # Add outgoing references
        for ref in outgoing_refs:
            method_name = ref.get('method', 'Unknown')
            file_path = ref.get('file', 'Unknown')
            
            # Skip if the method name is unknown or already in the canvas
            if method_name == 'Unknown' or method_name in self.nodes:
                continue
                
            # Add the node with a position to the right of the selected node
            x = self.selected_node.x + 250
            y = self.selected_node.y - 50 + len(self.nodes) * 20
            node = self.add_method_node(method_name, file_path, x, y)
            
            # Add connection
            self.add_connection(self.selected_node, node, is_incoming=False)
    
    def remove_selected_node(self):
        """Remove the selected node"""
        if not self.selected_node:
            return
            
        # Remove connections involving this node
        connections_to_remove = []
        for i, (conn, source, target, _) in enumerate(self.connections):
            if source == self.selected_node or target == self.selected_node:
                self.delete(conn)
                connections_to_remove.append(i)
        
        # Remove connections from the list (in reverse order to maintain indices)
        for i in sorted(connections_to_remove, reverse=True):
            self.connections.pop(i)
        
        # Remove the node
        for obj in self.selected_node.canvas_objects:
            self.delete(obj)
        
        # Remove from nodes dictionary
        del self.nodes[self.selected_node.method_name]
        
        # Clear selection
        self.selected_node = None
    
    def auto_layout(self):
        """Automatically layout the nodes in a readable pattern"""
        if not self.nodes:
            return
            
        # Use a simple layout algorithm - arrange in a circle
        import math
        
        # Get canvas center
        center_x = self.winfo_width() // 2
        center_y = self.winfo_height() // 2
        
        # Determine radius based on node count
        radius = min(center_x, center_y) * 0.6
        
        # Arrange nodes in a circle
        node_count = len(self.nodes)
        i = 0
        for method_name, node in self.nodes.items():
            # Calculate angle
            angle = (2 * math.pi * i) / node_count
            
            # Calculate new position
            new_x = center_x + radius * math.cos(angle) - node.width // 2
            new_y = center_y + radius * math.sin(angle) - node.height // 2
            
            # Move the node
            dx = new_x - node.x
            dy = new_y - node.y
            
            node.x = new_x
            node.y = new_y
            
            for obj in node.canvas_objects:
                self.move(obj, dx, dy)
                
            i += 1
        
        # Update connections
        self.update_connections()
    
    def clear_all(self):
        """Clear all nodes and connections"""
        # Ask for confirmation
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all nodes?"):
            # Remove all nodes
            for node in list(self.nodes.values()):
                for obj in node.canvas_objects:
                    self.delete(obj)
            
            # Remove all connections
            for conn, _, _, _ in self.connections:
                self.delete(conn)
            
            # Clear data structures
            self.nodes = {}
            self.connections = []
            self.selected_node = None


# Enhancement 3: Improvements to MethodRelationshipVisualizer
def enhance_method_visualizer():
    """
    Add enhancements to the MethodRelationshipVisualizer class
    """
    # Improved handling of references with a depth control mechanism
    
    # Replace the update_display method to use the enhanced canvas
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
                self.add_reference_nodes(incoming_refs, main_node, is_incoming=True, 
                                      angle_start=0, angle_end=180, depth=depth)
            
            # Process outgoing references if enabled
            if show_outgoing and outgoing_refs:
                self.add_reference_nodes(outgoing_refs, main_node, is_incoming=False, 
                                      angle_start=180, angle_end=360, depth=depth)
            
            # Update connections
            self.update_all_connections()
        
        self.status_var.set(f"Display updated. Showing {len(self.nodes)} methods.")
    
    # Add this new method to support recursive reference visualization
    def add_reference_nodes(self, refs, parent_node, is_incoming=True, radius=200, 
                         angle_start=0, angle_end=360, depth=1, level=1):
        """
        Add reference nodes around the parent node with recursive support.
        
        Args:
            refs: List of reference dictionaries
            parent_node: The parent node to connect to
            is_incoming: Whether these are incoming references
            radius: Radius distance from parent
            angle_start: Starting angle for placement
            angle_end: Ending angle for placement
            depth: Maximum depth to visualize
            level: Current recursion level
        """
        import math
        
        if not refs or level > depth:
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
            
            # Recursively add references if we have more levels to go
            if level < depth:
                # Get references for this method
                try:
                    child_incoming, child_outgoing = self.reference_tracker.get_method_references(
                        ref_file, ref_method)
                    
                    # Only add outgoing references from incoming nodes (to avoid explosion)
                    if is_incoming and child_outgoing:
                        self.add_reference_nodes(
                            child_outgoing[:3],  # Limit to 3 to avoid clutter
                            node, 
                            is_incoming=False,
                            radius=radius * 0.8,  # Reduce radius for each level
                            angle_start=angle_start + 45,
                            angle_end=angle_end - 45,
                            depth=depth,
                            level=level + 1
                        )
                    
                    # Only add incoming references from outgoing nodes
                    elif not is_incoming and child_incoming:
                        self.add_reference_nodes(
                            child_incoming[:3],  # Limit to 3 to avoid clutter
                            node, 
                            is_incoming=True,
                            radius=radius * 0.8,
                            angle_start=angle_start + 45,
                            angle_end=angle_end - 45,
                            depth=depth,
                            level=level + 1
                        )
                except Exception as e:
                    print(f"Error getting references for {ref_method}: {str(e)}")
    
    # Replace methods in MethodRelationshipVisualizer
    MethodRelationshipVisualizer.update_display = update_display
    MethodRelationshipVisualizer.add_reference_nodes = add_reference_nodes


# Function to integrate everything
def integrate_method_visualization_enhancements():
    """Integrate all method visualization enhancements"""
    enhance_method_node()
    enhance_method_visualizer()
    
    # This line would need to be run by the main application
    # when initializing its visualization components
    print("Method visualization enhancements integrated successfully")
    
    
# If this file is run directly, test the integration
if __name__ == "__main__":
    integrate_method_visualization_enhancements()
    print("Run this from the main application to apply the enhancements")