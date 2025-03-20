import tkinter as tk
from tkinter import ttk
import math
import random
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
import os

class InteractiveGraphCanvas(tk.Canvas):
    """
    Interactive canvas for graph visualization with zoom, pan, and node manipulation.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg='white')
        
        # Graph data
        self.nodes = {}  # id -> (x, y, data)
        self.edges = []  # (from_id, to_id, data)
        
        # Display settings
        self.node_radius = 15
        self.selected_node_radius = 18
        self.edge_width = 1.5
        self.arrow_size = 8
        self.font = ('Arial', 10)
        
        # Node colors by type
        self.node_colors = {
            'focus': '#FFD700',  # Gold
            'cs': '#ADD8E6',     # Light blue
            'xaml': '#90EE90',   # Light green
            'other': '#D3D3D3',  # Light gray
            'default': '#B0C4DE'  # Default blue
        }
        
        # Interactive state
        self.selected_node = None
        self.dragged_node = None
        self.highlighted_nodes = set()
        self.hovered_node = None
        self.tooltip = None
        self.tooltip_text = None
        
        # Pan and zoom
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_panning = False
        
        # Simulation parameters
        self.simulation_running = False
        self.simulation_step = 0
        self.simulation_max_steps = 500
        self.cooling_factor = 0.95
        self.repulsion_force = 100
        self.attraction_force = 0.1
        self.center_gravity = 0.01
        
        # Bind events
        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<ButtonRelease-1>", self.on_button_release)
        self.bind("<B1-Motion>", self.on_button_motion)
        self.bind("<ButtonPress-2>", self.on_pan_start)  # Middle button
        self.bind("<B2-Motion>", self.on_pan_motion)
        self.bind("<ButtonPress-3>", self.on_pan_start)  # Right button (alternative)
        self.bind("<B3-Motion>", self.on_pan_motion)
        self.bind("<MouseWheel>", self.on_mouse_wheel)   # Windows/macOS
        self.bind("<Button-4>", self.on_mouse_wheel)     # Linux scroll up
        self.bind("<Button-5>", self.on_mouse_wheel)     # Linux scroll down
        self.bind("<Motion>", self.on_mouse_move)
        
        # Create popup menu
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Run Layout", command=self.run_force_directed_layout)
        self.popup_menu.add_command(label="Reset Zoom", command=self.reset_view)
        self.popup_menu.add_command(label="Center View", command=self.center_view)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Show All Node Labels", command=lambda: self.set_label_visibility(True))
        self.popup_menu.add_command(label="Hide All Node Labels", command=lambda: self.set_label_visibility(False))
        self.bind("<ButtonPress-3>", self.show_popup_menu)
        
        # Initial view
        self.after(100, self.center_view)
    
    def set_graph(self, nodes, edges):
        """Set the graph data and initialize positions"""
        self.nodes = nodes  # {id: {'x': x, 'y': y, 'label': label, 'data': {...}}}
        self.edges = edges  # [(from_id, to_id, {'type': type})]
        
        # Initialize node positions if not set
        for node_id, node_data in self.nodes.items():
            if 'x' not in node_data or 'y' not in node_data:
                # Assign random positions initially
                angle = random.random() * 2 * math.pi
                distance = random.random() * 200
                node_data['x'] = math.cos(angle) * distance
                node_data['y'] = math.sin(angle) * distance
        
        # Run force-directed layout for initial positioning
        self.run_force_directed_layout()
    
    def center_on_node(self, node_id):
        """Center the view on a specific node"""
        if node_id not in self.nodes:
            return
        
        # Get node position
        node_data = self.nodes[node_id]
        node_x = node_data['x']
        node_y = node_data['y']
    
        # Calculate canvas center
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
    
        # Update offset to center node
        self.offset_x = canvas_width / 2 - node_x * self.scale
        self.offset_y = canvas_height / 2 - node_y * self.scale
    
        # Redraw the graph
        self.draw_graph()
    
        # Highlight the node
        self.highlight_node(node_id)

    def highlight_node(self, node_id):
        """Highlight a specific node with animation effect"""
        if node_id not in self.nodes:
            return
        
        # Store current node colors
        original_colors = {}
        for n_id, node in self.nodes.items():
            node_type = node.get('type', 'default')
            original_colors[n_id] = self.node_colors.get(node_type, self.node_colors['default'])
    
        # Highlight animation function
        def animate_highlight(step=0, max_steps=6):
            if step >= max_steps:
                # Restore original colors
                for n_id, color in original_colors.items():
                    node_type = self.nodes[n_id].get('type', 'default')
                    self.node_colors[node_type] = color
                self.draw_graph()
                return
            
            # Toggle highlight
            if step % 2 == 0:
                # Highlight node
                node_type = self.nodes[node_id].get('type', 'default')
                self.node_colors[node_type] = '#FF5500'  # Bright orange
            else:
                # Restore original
                node_type = self.nodes[node_id].get('type', 'default')
                self.node_colors[node_type] = original_colors[node_id]
            
            # Redraw and schedule next step
            self.draw_graph()
            self.after(100, lambda: animate_highlight(step + 1, max_steps))
    
        # Start animation
        animate_highlight()

    def export_as_image(self):
        """Export the canvas as a PNG image"""
        from tkinter import filedialog
        import os
    
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Graph Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
    
        if not filename:
            return
        
        try:
            # Try to use PIL for better quality export
            try:
                from PIL import ImageGrab
            
                # Get canvas coordinates
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                width = self.winfo_width()
                height = self.winfo_height()
            
                # Grab the image
                image = ImageGrab.grab((x, y, x + width, y + height))
            
                # Save the image
                image.save(filename)
            
                messagebox.showinfo("Export Successful", f"Graph exported to {filename}")
            
            except ImportError:
                # Fallback to PostScript export if PIL is not available
                ps_file = os.path.splitext(filename)[0] + ".ps"
                self.postscript(file=ps_file)
                messagebox.showinfo("Export Successful", 
                                  f"Graph exported as PostScript to {ps_file}\n"
                                  f"Install PIL/Pillow for PNG export: pip install pillow")
                
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting graph: {str(e)}")

    def draw_graph(self):
        """Draw the complete graph"""
        self.delete("all")  # Clear canvas
        
        # Draw edges first (so they're behind nodes)
        for source_id, target_id, edge_data in self.edges:
            if source_id in self.nodes and target_id in self.nodes:
                self.draw_edge(source_id, target_id, edge_data)
        
        # Draw nodes
        for node_id, node_data in self.nodes.items():
            self.draw_node(node_id, node_data)
        
        # Draw selected node on top (if any)
        if self.selected_node in self.nodes:
            self.draw_node(self.selected_node, self.nodes[self.selected_node], is_selected=True)
    
    def draw_node(self, node_id, node_data, is_selected=False):
        """Draw a single node"""
        # Apply zoom and pan transformations
        x = node_data['x'] * self.scale + self.offset_x
        y = node_data['y'] * self.scale + self.offset_y
        
        # Determine node color and size
        node_type = node_data.get('type', 'default')
        color = self.node_colors.get(node_type, self.node_colors['default'])
        
        # Adjust color if node is highlighted
        if node_id in self.highlighted_nodes:
            # Make color brighter for highlighting
            color = self.brighten_color(color)
        
        # Adjust radius for selected node
        radius = self.selected_node_radius if is_selected else self.node_radius
        radius *= self.scale  # Scale radius with zoom
        
        # Check if this is a focus node
        is_focus = node_data.get('is_focus', False)
        if is_focus:
            color = self.node_colors['focus']
            radius *= 1.1  # Make focus nodes slightly larger
        
        # Draw node with an outline
        self.create_oval(
            x - radius, y - radius, 
            x + radius, y + radius,
            fill=color, 
            outline='#333333',
            width=2 if is_selected else 1,
            tags=(f"node_{node_id}", "node")
        )
        
        # Draw node label if needed
        if is_selected or is_focus or self.scale > 0.7:
            label = node_data.get('label', str(node_id))
            if len(label) > 20:  # Truncate long labels
                label = label[:17] + "..."
                
            # Calculate text size based on zoom
            font_size = max(8, int(10 * self.scale))
            font = ('Arial', font_size)
            
            self.create_text(
                x, y + radius + 5 * self.scale,
                text=label,
                font=font,
                fill='black',
                tags=(f"label_{node_id}", "label")
            )
    
    def draw_edge(self, source_id, target_id, edge_data):
        """Draw a single edge with an arrow"""
        # Get node positions
        source = self.nodes[source_id]
        target = self.nodes[target_id]
        
        # Apply zoom and pan transformations
        x1 = source['x'] * self.scale + self.offset_x
        y1 = source['y'] * self.scale + self.offset_y
        x2 = target['x'] * self.scale + self.offset_x
        y2 = target['y'] * self.scale + self.offset_y
        
        # Calculate direction vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:  # Avoid division by zero
            return
            
        # Normalize direction vector
        dx /= length
        dy /= length
        
        # Calculate edge start and end points adjusted for node radius
        radius = self.node_radius * self.scale
        startx = x1 + dx * radius
        starty = y1 + dy * radius
        endx = x2 - dx * radius
        endy = y2 - dy * radius
        
        # Determine if this edge connects highlighted nodes
        is_highlighted = (source_id in self.highlighted_nodes and 
                         target_id in self.highlighted_nodes)
        
        # Determine edge color and width based on type and highlighting
        edge_type = edge_data.get('type', 'default')
        if is_highlighted:
            color = '#FF6600'  # Orange for highlighted edges
            width = self.edge_width * 2 * self.scale
        elif edge_type == 'inherits':
            color = '#006600'  # Green for inheritance
            width = self.edge_width * 1.5 * self.scale
        else:
            color = '#666666'  # Default gray
            width = self.edge_width * self.scale
        
        # Draw edge line
        self.create_line(
            startx, starty, endx, endy,
            fill=color,
            width=width,
            arrow=tk.LAST,
            arrowshape=(8 * self.scale, 10 * self.scale, 3 * self.scale),
            tags=(f"edge_{source_id}_{target_id}", "edge")
        )
    
    def run_force_directed_layout(self):
        """Run force-directed layout algorithm (Fruchterman-Reingold)"""
        if self.simulation_running:
            return  # Already running
            
        self.simulation_running = True
        self.simulation_step = 0
        
        # Calculate canvas center
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        center_x = canvas_width / 2 - self.offset_x
        center_y = canvas_height / 2 - self.offset_y
        
        # Initial temperature (for simulated annealing)
        temperature = 1.0
        
        # Create adjacency list for faster neighbor lookup
        adjacency = {node_id: set() for node_id in self.nodes}
        for source_id, target_id, _ in self.edges:
            if source_id in adjacency and target_id in adjacency:
                adjacency[source_id].add(target_id)
                adjacency[target_id].add(source_id)  # Bidirectional for force calculation
        
        def simulation_step():
            nonlocal temperature
            
            if self.simulation_step >= self.simulation_max_steps or not self.simulation_running:
                self.simulation_running = False
                return
                
            # Calculate forces and update positions
            forces = {node_id: [0, 0] for node_id in self.nodes}
            
            # Repulsive forces (between all pairs of nodes)
            node_items = list(self.nodes.items())
            for i, (node_id, node_data) in enumerate(node_items):
                for j in range(i + 1, len(node_items)):
                    other_id, other_data = node_items[j]
                    
                    # Calculate distance
                    dx = node_data['x'] - other_data['x']
                    dy = node_data['y'] - other_data['y']
                    distance = max(0.1, math.sqrt(dx * dx + dy * dy))
                    
                    # Repulsive force inversely proportional to distance
                    if distance > 0:
                        force = self.repulsion_force / (distance * distance)
                        
                        # Normalize direction
                        if distance > 0:
                            dx /= distance
                            dy /= distance
                        
                        # Apply force to both nodes in opposite directions
                        forces[node_id][0] += dx * force
                        forces[node_id][1] += dy * force
                        forces[other_id][0] -= dx * force
                        forces[other_id][1] -= dy * force
            
            # Attractive forces (between connected nodes)
            for source_id, target_id, _ in self.edges:
                if source_id in self.nodes and target_id in self.nodes:
                    source = self.nodes[source_id]
                    target = self.nodes[target_id]
                    
                    # Calculate distance and direction
                    dx = source['x'] - target['x']
                    dy = source['y'] - target['y']
                    distance = max(0.1, math.sqrt(dx * dx + dy * dy))
                    
                    # Attractive force proportional to distance
                    force = self.attraction_force * distance
                    
                    # Normalize direction
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                    
                    # Apply force pulling nodes together
                    forces[source_id][0] -= dx * force
                    forces[source_id][1] -= dy * force
                    forces[target_id][0] += dx * force
                    forces[target_id][1] += dy * force
            
            # Apply center gravity force
            for node_id, node_data in self.nodes.items():
                # Vector from node to center
                dx = center_x - node_data['x']
                dy = center_y - node_data['y']
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Gravity force proportional to distance from center
                if distance > 0:
                    force = self.center_gravity * distance
                    forces[node_id][0] += (dx / distance) * force
                    forces[node_id][1] += (dy / distance) * force
            
            # Update node positions with temperature scaling
            for node_id, force in forces.items():
                # Scale force by temperature
                scale = min(temperature, 10.0)  # Limit max displacement
                
                # Update position
                self.nodes[node_id]['x'] += force[0] * scale
                self.nodes[node_id]['y'] += force[1] * scale
            
            # Update temperature (cool down the system)
            temperature *= self.cooling_factor
            
            # Redraw graph
            self.draw_graph()
            
            # Increment step counter
            self.simulation_step += 1
            
            # Schedule next step
            if self.simulation_step < self.simulation_max_steps and self.simulation_running:
                self.after(10, simulation_step)
            else:
                self.simulation_running = False
        
        # Start simulation
        simulation_step()
    
    def on_button_press(self, event):
        """Handle mouse button press"""
        # Convert screen coordinates to canvas coordinates
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        
        # Check if a node was clicked
        node_id = self.find_node_at(x, y)
        
        if node_id:
            # Remember the node that was clicked for potential dragging
            self.dragged_node = node_id
            
            # Set node as selected
            self.selected_node = node_id
            
            # Highlight connected nodes
            self.highlight_connected_nodes(node_id)
            
            # Redraw graph to show selection
            self.draw_graph()
        else:
            # Clicked empty space
            self.selected_node = None
            self.highlighted_nodes = set()
            self.draw_graph()
    
    def on_button_release(self, event):
        """Handle mouse button release"""
        # Reset drag state
        self.dragged_node = None
    
    def on_button_motion(self, event):
        """Handle mouse motion with button pressed"""
        if self.dragged_node:
            # Calculate position in graph coordinates
            x = (self.canvasx(event.x) - self.offset_x) / self.scale
            y = (self.canvasy(event.y) - self.offset_y) / self.scale
            
            # Update node position
            self.nodes[self.dragged_node]['x'] = x
            self.nodes[self.dragged_node]['y'] = y
            
            # Redraw graph
            self.draw_graph()
    
    def on_pan_start(self, event):
        """Start panning the view"""
        self.is_panning = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_pan_motion(self, event):
        """Pan the view with middle mouse button"""
        if self.is_panning:
            # Calculate how much the mouse has moved
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Update drag start point
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Update canvas offset
            self.offset_x += dx
            self.offset_y += dy
            
            # Redraw graph
            self.draw_graph()
    
    def on_mouse_wheel(self, event):
        """Handle zoom with mouse wheel"""
        # Determine scroll direction based on event type
        if event.num == 4 or event.delta > 0:
            # Zoom in
            zoom_factor = 1.1
        elif event.num == 5 or event.delta < 0:
            # Zoom out
            zoom_factor = 0.9
        else:
            return
        
        # Calculate zoom center (position under cursor)
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        
        # Convert to graph coordinates
        graph_x = (x - self.offset_x) / self.scale
        graph_y = (y - self.offset_y) / self.scale
        
        # Update scale
        self.scale *= zoom_factor
        
        # Ensure scale is within reasonable bounds
        self.scale = max(0.1, min(self.scale, 5.0))
        
        # Adjust offset to zoom toward cursor
        self.offset_x = x - graph_x * self.scale
        self.offset_y = y - graph_y * self.scale
        
        # Redraw graph
        self.draw_graph()
    
    def on_mouse_move(self, event):
        """Handle mouse movement to show tooltips"""
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        
        # Check if mouse is over a node
        node_id = self.find_node_at(x, y)
        
        if node_id != self.hovered_node:
            # Node under cursor has changed
            self.hovered_node = node_id
            
            # Remove existing tooltip
            if self.tooltip:
                self.delete(self.tooltip)
                self.tooltip = None
            
            # Create tooltip for new node
            if node_id:
                node_data = self.nodes[node_id]
                
                # Create tooltip text based on node data
                if 'data' in node_data:
                    tooltip_text = self.create_tooltip_text(node_id, node_data)
                else:
                    tooltip_text = str(node_id)
                
                # Create tooltip background and text
                bg_color = '#FFFFCC'  # Light yellow
                padding = 5
                
                # Create tooltip
                tooltip_x = x + 15  # Offset from cursor
                tooltip_y = y + 15
                
                # Create tooltip background rectangle
                tooltip_bg = self.create_rectangle(
                    tooltip_x, tooltip_y,
                    tooltip_x + 200, tooltip_y + 50,  # Initial size, will be updated
                    fill=bg_color, outline='#666666',
                    tags="tooltip"
                )
                
                # Create tooltip text
                tooltip_text_id = self.create_text(
                    tooltip_x + padding, tooltip_y + padding,
                    text=tooltip_text,
                    anchor=tk.NW,
                    font=('Arial', 9),
                    fill='black',
                    width=190,  # Maximum width
                    tags="tooltip"
                )
                
                # Get text bounding box
                bbox = self.bbox(tooltip_text_id)
                
                # Resize background rectangle to fit text
                self.coords(
                    tooltip_bg,
                    tooltip_x, tooltip_y,
                    bbox[2] + padding, bbox[3] + padding
                )
                
                # Store tooltip IDs
                self.tooltip = [tooltip_bg, tooltip_text_id]
    
    def create_tooltip_text(self, node_id, node_data):
        """Create tooltip text based on node data"""
        lines = []
        
        # Add node ID or label
        label = node_data.get('label', str(node_id))
        lines.append(f"Node: {label}")
        
        # Add node type
        node_type = node_data.get('type', 'default')
        lines.append(f"Type: {node_type}")
        
        # Add file info if available
        if 'file' in node_data:
            file_path = node_data['file']
            file_name = os.path.basename(file_path) if 'os' in globals() else file_path
            lines.append(f"File: {file_name}")
        
        # Add method info if available
        if 'method' in node_data:
            lines.append(f"Method: {node_data['method']}")
        
        # Return multi-line text
        return '\n'.join(lines)
    
    def find_node_at(self, x, y):
        """Find node ID at the given coordinates"""
        # Convert back to graph coordinates
        graph_x = (x - self.offset_x) / self.scale
        graph_y = (y - self.offset_y) / self.scale
        
        # Check each node
        for node_id, node_data in self.nodes.items():
            dx = node_data['x'] - graph_x
            dy = node_data['y'] - graph_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance <= self.node_radius:
                return node_id
        
        return None
    
    def highlight_connected_nodes(self, node_id):
        """Highlight nodes connected to the given node"""
        self.highlighted_nodes = {node_id}
        
        # Find connected nodes
        for source_id, target_id, _ in self.edges:
            if source_id == node_id:
                self.highlighted_nodes.add(target_id)
            elif target_id == node_id:
                self.highlighted_nodes.add(source_id)
    
    def reset_view(self):
        """Reset zoom and pan to default"""
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.draw_graph()
    
    def center_view(self):
        """Center the graph in the canvas"""
        # Calculate bounds of all nodes
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for node_data in self.nodes.values():
            min_x = min(min_x, node_data['x'])
            min_y = min(min_y, node_data['y'])
            max_x = max(max_x, node_data['x'])
            max_y = max(max_y, node_data['y'])
        
        # Check if we have valid bounds
        if min_x == float('inf') or min_y == float('inf') or max_x == float('-inf') or max_y == float('-inf'):
            return
        
        # Calculate center of graph
        graph_center_x = (min_x + max_x) / 2
        graph_center_y = (min_y + max_y) / 2
        
        # Calculate canvas center
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        if canvas_width == 1:  # Not yet drawn
            canvas_width = int(self.cget('width'))
            canvas_height = int(self.cget('height'))
        
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2
        
        # Calculate graph width and height
        graph_width = max_x - min_x
        graph_height = max_y - min_y
        
        # Calculate scale to fit graph in canvas (with some padding)
        if graph_width > 0 and graph_height > 0:
            scale_x = (canvas_width - 100) / graph_width
            scale_y = (canvas_height - 100) / graph_height
            new_scale = min(scale_x, scale_y)
            
            # Ensure we don't zoom in too much for small graphs
            new_scale = min(new_scale, 1.5)
            
            # Update scale
            self.scale = new_scale
        
        # Update offset to center graph
        self.offset_x = canvas_center_x - graph_center_x * self.scale
        self.offset_y = canvas_center_y - graph_center_y * self.scale
        
        # Redraw graph
        self.draw_graph()
    
    def set_label_visibility(self, visible):
        """Set the visibility of all node labels"""
        # Redraw the graph - labels will be shown based on the zoom level
        self.draw_graph()
    
    def show_popup_menu(self, event):
        """Show the popup menu"""
        self.popup_menu.post(event.x_root, event.y_root)
    
    def brighten_color(self, hex_color):
        """Brighten a hex color by 20%"""
        # Remove '#' if present
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Brighten
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'


class InteractiveCanvasVisualizer:
    """
    Visualizer that uses the InteractiveGraphCanvas for graph visualization.
    """
    
    def __init__(self, reference_tracker=None, log_callback=None):
        """
        Initialize the visualizer.
        
        Args:
            reference_tracker: Reference tracking manager
            log_callback: Function to call for logging
        """
        self.reference_tracker = reference_tracker
        self.log_callback = log_callback or (lambda msg: None)
        
        # We don't need networkx or matplotlib now
        self.can_visualize = True
    
    def log(self, message):
        """Log a message using the callback if available"""
        if self.log_callback:
            self.log_callback(message)
    
    def create_file_reference_graph(self, selected_files, max_depth=1):
        """
        Create a graph of file references.
        
        Args:
            selected_files: List of files to start with
            max_depth: Maximum reference depth to include
            
        Returns:
            Dictionary of nodes and edges
        """
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
        
        # Create graph data
        nodes = {}  # id -> {x, y, label, type, is_focus, data}
        edges = []  # (from_id, to_id, {type})
        
        # Track files we've already processed to avoid duplicates
        processed_files = set()
        
        # Process files with BFS to respect max_depth
        queue = [(file_path, 0) for file_path in selected_files]
        queued = set(selected_files)
        
        while queue:
            file_path, depth = queue.pop(0)
            
            if file_path in processed_files or depth > max_depth:
                continue
                
            processed_files.add(file_path)
            
            # Get file name for display (relative to root directory if possible)
            if hasattr(self.reference_tracker, 'root_dir'):
                try:
                    display_name = os.path.relpath(file_path, self.reference_tracker.root_dir)
                except ValueError:
                    display_name = os.path.basename(file_path)
            else:
                display_name = os.path.basename(file_path)
                
            # Determine node type based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.cs':
                node_type = 'cs'
            elif file_ext in ('.xaml', '.axaml'):
                node_type = 'xaml'
            else:
                node_type = 'other'
                
            # Add node with attributes
            nodes[file_path] = {
                'label': display_name,
                'type': node_type,
                'is_focus': file_path in selected_files,
                'file': file_path,
                'data': {
                    'path': file_path,
                    'type': node_type
                }
            }
                
            # Find references from this file
            referenced_by, references_to = self.reference_tracker.get_reference_details(file_path)
            
            # Add edges for references
            for target_file in references_to:
                edges.append((file_path, target_file, {'type': 'references'}))
                
                # Process referenced files if within depth limit
                if depth < max_depth and target_file not in queued:
                    queue.append((target_file, depth + 1))
                    queued.add(target_file)
                    
            # Add edges for files that reference this file
            for source_file in referenced_by:
                edges.append((source_file, file_path, {'type': 'referenced_by'}))
                
                # Process referencing files if within depth limit
                if depth < max_depth and source_file not in queued:
                    queue.append((source_file, depth + 1))
                    queued.add(source_file)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def create_method_reference_graph(self, file_path, method_name=None, max_depth=1):
        """
        Create a graph of method references.
        
        Args:
            file_path: Path to the file containing methods
            method_name: Optional specific method to focus on
            max_depth: Maximum reference depth to include
            
        Returns:
            Dictionary of nodes and edges
        """
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
        
        # Create graph data
        nodes = {}  # id -> {x, y, label, type, is_focus, data}
        edges = []  # (from_id, to_id, {type})
        
        # Get method details
        if method_name:
            # Focus on a specific method
            method_info = self.reference_tracker.get_method_details(file_path, method_name)
            if not method_info:
                self.log(f"Method {method_name} not found in {file_path}")
                return None
                
            # Track methods that have been processed
            processed_methods = set()
            
            # Process method references recursively up to max_depth
            def process_method(file, method, current_depth):
                # Create a unique ID for the method
                method_id = f"{file}::{method}"
                
                if method_id in processed_methods or current_depth > max_depth:
                    return
                    
                processed_methods.add(method_id)
                
                # Get file and method details
                file_basename = os.path.basename(file)
                method_details = self.reference_tracker.get_method_details(file, method)
                
                if not method_details:
                    return
                    
                # Create readable label
                label = f"{method} ({file_basename})"
                
                # Add node for this method
                nodes[method_id] = {
                    'label': label,
                    'type': 'cs',
                    'is_focus': (file == file_path and method == method_name),
                    'file': file,
                    'method': method,
                    'data': {
                        'file': file,
                        'method': method
                    }
                }
                
                # Get incoming and outgoing references
                incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(file, method)
                
                # Add edges for outgoing references
                for ref in outgoing_refs:
                    target_file = ref.get('file')
                    target_method = ref.get('method')
                    
                    if target_file and target_method:
                        target_id = f"{target_file}::{target_method}"
                        edges.append((method_id, target_id, {'type': 'calls'}))
                        
                        # Process target method if within depth limit
                        if current_depth < max_depth:
                            process_method(target_file, target_method, current_depth + 1)
                
                # Add edges for incoming references
                for ref in incoming_refs:
                    source_file = ref.get('file')
                    source_method = ref.get('method')
                    
                    if source_file and source_method:
                        source_id = f"{source_file}::{source_method}"
                        edges.append((source_id, method_id, {'type': 'calls'}))
                        
                        # Process source method if within depth limit
                        if current_depth < max_depth:
                            process_method(source_file, source_method, current_depth + 1)
            
            # Start processing from the specified method
            process_method(file_path, method_name, 0)
        else:
            # Show all methods in the file and their relationships
            methods = self.reference_tracker.get_methods_in_file(file_path)
            
            # Add nodes for all methods in the file
            for method in methods:
                method_id = f"{file_path}::{method}"
                nodes[method_id] = {
                    'label': method,
                    'type': 'cs',
                    'is_focus': True,
                    'file': file_path,
                    'method': method,
                    'data': {
                        'file': file_path,
                        'method': method
                    }
                }
                
                # Get outgoing references
                _, outgoing_refs = self.reference_tracker.get_method_references(file_path, method)
                
                # Add edges for method calls within the same file
                for ref in outgoing_refs:
                    if ref.get('file') == file_path:
                        target_method = ref.get('method')
                        target_id = f"{file_path}::{target_method}"
                        edges.append((method_id, target_id, {'type': 'calls'}))
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def create_class_reference_graph(self, root_dir, selected_classes=None, max_depth=1):
        """
        Create a graph of class references.
        
        Args:
            root_dir: Root directory for analysis
            selected_classes: Optional list of classes to focus on
            max_depth: Maximum reference depth to include
            
        Returns:
            Dictionary of nodes and edges
        """
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
        
        # Create graph data
        nodes = {}  # id -> {x, y, label, type, is_focus, data}
        edges = []  # (from_id, to_id, {type})
        
        # Map from class name to file
        class_to_file = {}
        
        # Build class to file mapping
        for file_path, info in self.reference_tracker.tracker.file_info.items():
            for type_name in info.get('types', []):
                qualified_name = f"{info['namespace']}.{type_name}" if info['namespace'] else type_name
                class_to_file[qualified_name] = file_path
                class_to_file[type_name] = file_path  # Also map simple name for convenience
        
        # Process classes
        processed_classes = set()
        
        def process_class(class_name, current_depth):
            if class_name in processed_classes or current_depth > max_depth:
                return
                
            processed_classes.add(class_name)
            
            # Find the file that defines this class
            file_path = class_to_file.get(class_name)
            if not file_path:
                return
                
            # Add node for this class
            nodes[class_name] = {
                'label': class_name,
                'type': 'cs',
                'is_focus': selected_classes and class_name in selected_classes,
                'file': file_path,
                'data': {
                    'class': class_name,
                    'file': file_path
                }
            }
                
            # Find inheritance relationships
            file_info = self.reference_tracker.tracker.file_info.get(file_path, {})
            
            # Add edges for inheritance
            for base_class in file_info.get('inheritance', []):
                if base_class in class_to_file:
                    edges.append((class_name, base_class, {'type': 'inherits'}))
                    
                    # Process base class if within depth limit
                    if current_depth < max_depth:
                        process_class(base_class, current_depth + 1)
            
            # Find classes that inherit from this class
            for other_class, other_file in class_to_file.items():
                if other_class == class_name:
                    continue
                    
                other_info = self.reference_tracker.tracker.file_info.get(other_file, {})
                if class_name in other_info.get('inheritance', []):
                    edges.append((other_class, class_name, {'type': 'inherits'}))
                    
                    # Process derived class if within depth limit
                    if current_depth < max_depth:
                        process_class(other_class, current_depth + 1)
        
        # Start processing from selected classes or process all
        if selected_classes:
            for class_name in selected_classes:
                process_class(class_name, 0)
        else:
            for class_name in list(class_to_file.keys())[:10]:  # Limit to 10 classes for performance
                process_class(class_name, 0)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def visualize_graph(self, graph_data, title, parent_window=None):
        """
        Visualize a graph in a Tkinter window using the interactive canvas.
        
        Args:
            graph_data: Dict with nodes and edges
            title: Title for the visualization window
            parent_window: Optional parent window
        """
        if not graph_data:
            self.log("No graph data to visualize.")
            return
            
        if not graph_data.get('nodes'):
            self.log("Graph has no nodes to display.")
            return
        
        # Create a new window for the visualization
        viz_window = tk.Toplevel(parent_window)
        viz_window.title(title)
        viz_window.geometry("800x600")
        viz_window.minsize(600, 400)
        
        # Create frames for controls and visualization
        control_frame = ttk.Frame(viz_window, padding="10")
        control_frame.pack(fill=tk.X)
        
        viz_frame = ttk.Frame(viz_window)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add controls
        ttk.Button(control_frame, text="Run Layout", 
                  command=lambda: canvas.run_force_directed_layout()).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset View", 
                  command=lambda: canvas.reset_view()).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Center View", 
                  command=lambda: canvas.center_view()).pack(side=tk.LEFT, padx=5)
        
        # Add export button
        ttk.Button(control_frame, text="Export as PNG", 
                  command=lambda: self.export_graph_image(canvas, title)).pack(side=tk.RIGHT, padx=5)
        
        # Help text
        help_text = "Left-click: Select/drag nodes | Right-click: Pan view | Scroll: Zoom"
        ttk.Label(control_frame, text=help_text).pack(side=tk.RIGHT, padx=20)
        
        # Create the interactive canvas
        canvas = InteractiveGraphCanvas(viz_frame, bg='white')
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Set the graph data
        canvas.set_graph(graph_data['nodes'], graph_data['edges'])
        
        # Draw the graph
        viz_window.update_idletasks()  # Ensure the window is fully created
        canvas.draw_graph()
    
    def export_graph_image(self, canvas, title):
        """
        Export the canvas as a PNG image.
        
        Args:
            canvas: The canvas to export
            title: Title for the image file
        """
        from tkinter import filedialog
        import os
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Graph Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            # Try to use PIL for better quality export
            try:
                from PIL import ImageGrab, Image
                
                # Get canvas coordinates
                x = canvas.winfo_rootx()
                y = canvas.winfo_rooty()
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                
                # Grab the image
                image = ImageGrab.grab((x, y, x + width, y + height))
                
                # Save the image
                image.save(filename)
                
                self.log(f"Graph exported to {filename}")
                
            except ImportError:
                # Fallback to PostScript export if PIL is not available
                ps_file = os.path.splitext(filename)[0] + ".ps"
                canvas.postscript(file=ps_file)
                self.log(f"Graph exported as PostScript to {ps_file}")
                self.log("Install PIL/Pillow for PNG export: pip install pillow")
                
        except Exception as e:
            self.log(f"Error exporting graph: {str(e)}")