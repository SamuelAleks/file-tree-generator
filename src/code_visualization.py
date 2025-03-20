import tkinter as tk
from tkinter import ttk
import math
import random
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
import os
import re

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
    
    # Add to InteractiveGraphCanvas class

    def draw_node(self, node_id, node_data, is_selected=False):
        """Draw a single node with enhanced visual information"""
        # Apply zoom and pan transformations
        x = node_data['x'] * self.scale + self.offset_x
        y = node_data['y'] * self.scale + self.offset_y
    
        # Determine node color and shape based on type
        node_type = node_data.get('type', 'default')
        color = self.node_colors.get(node_type, self.node_colors['default'])
    
        # Get node information
        method_name = node_data.get('method', '')
        class_name = node_data.get('class', '')
    
        # Determine node size based on complexity or importance
        complexity = node_data.get('complexity', 1)
        base_radius = self.node_radius * min(1.0 + (complexity * 0.05), 1.5)
    
        # Adjust radius for selected node
        radius = self.selected_node_radius if is_selected else base_radius
        radius *= self.scale  # Scale radius with zoom
    
        # Calculate visual attributes
        if is_selected:
            outline_color = '#FF6600'  # Bright orange for selected node
            outline_width = 3
        else:
            outline_color = '#333333'
            outline_width = 1
    
        # Draw node with enhanced styling
        self.create_oval(
            x - radius, y - radius, 
            x + radius, y + radius,
            fill=color, 
            outline=outline_color,
            width=outline_width,
            tags=(f"node_{node_id}", "node")
        )
    
        # Add method signature snippet if available
        if 'signature' in node_data and self.scale > 0.7:
            signature = node_data['signature']
            # Truncate signature to fit
            if len(signature) > 30:
                signature = signature[:27] + "..."
        
            # Calculate text size based on zoom
            font_size = max(8, int(9 * self.scale))
            font = ('Courier', font_size)
        
            self.create_text(
                x, y,
                text=signature,
                font=font,
                fill='black',
                tags=(f"signature_{node_id}", "signature")
            )
        else:
            # Just show the method name
            label = method_name
            if class_name and self.scale > 0.9:
                label = f"{class_name}.{method_name}"
            
            if len(label) > 25:
                label = label[:22] + "..."
            
            # Calculate text size based on zoom
            font_size = max(8, int(10 * self.scale))
            font = ('Arial', font_size)
        
            self.create_text(
                x, y,
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

    
    def run_obsidian_layout(self, config=None):
        """Run Obsidian-like force-directed layout with configurable parameters"""
        if self.simulation_running:
            return  # Already running
        
        # Use provided config or default values
        config = config or {}
        center_force = config.get('center_force', 0.1)
        repulsion = config.get('repulsion', 200)
        connection_strength = config.get('connection_strength', 0.3)
        edge_length = config.get('edge_length', 150)
    
        self.simulation_running = True
        self.simulation_step = 0
    
        # Calculate canvas center
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        center_x = canvas_width / 2 - self.offset_x
        center_y = canvas_height / 2 - self.offset_y
    
        # Initial temperature (for simulated annealing)
        temperature = 1.0
    
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
                        force = repulsion / (distance * distance)
                    
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
            for source_id, target_id, edge_data in self.edges:
                if source_id in self.nodes and target_id in self.nodes:
                    source = self.nodes[source_id]
                    target = self.nodes[target_id]
                
                    # Calculate distance and direction
                    dx = source['x'] - target['x']
                    dy = source['y'] - target['y']
                    distance = max(0.1, math.sqrt(dx * dx + dy * dy))
                
                    # Calculate optimal length based on edge type
                    optimal_length = edge_length
                    if 'type' in edge_data:
                        # Adjust length based on relationship type
                        if edge_data['type'] == 'calls':
                            optimal_length *= 0.8  # Shorter for calls
                        elif edge_data['type'] == 'inherits':
                            optimal_length *= 1.2  # Longer for inheritance
                
                    # Attractive/repulsive force based on optimal length
                    # (Hooke's law: force proportional to displacement from optimal length)
                    force = connection_strength * (distance - optimal_length)
                
                    # Normalize direction
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                
                    # Apply force pulling nodes together or pushing them apart
                    forces[source_id][0] -= dx * force
                    forces[source_id][1] -= dy * force
                    forces[target_id][0] += dx * force
                    forces[target_id][1] += dy * force
        
            # Apply center gravity force (Obsidian-like behavior)
            for node_id, node_data in self.nodes.items():
                # Vector from node to center
                dx = center_x - node_data['x']
                dy = center_y - node_data['y']
                distance = math.sqrt(dx * dx + dy * dy)
            
                # Gravity force proportional to distance from center
                if distance > 0:
                    force = center_force * distance
                    forces[node_id][0] += (dx / distance) * force
                    forces[node_id][1] += (dy / distance) * force
        
            # Add some randomness for better distribution (particularly useful
            # when nodes are stacked on top of each other)
            if self.simulation_step < 10:  # Only add jitter in early steps
                for node_id in forces:
                    forces[node_id][0] += (random.random() - 0.5) * temperature * 10
                    forces[node_id][1] += (random.random() - 0.5) * temperature * 10
        
            # Update node positions with temperature scaling
            for node_id, force in forces.items():
                # Scale force by temperature
                scale = min(temperature, 5.0)  # Limit max displacement
            
                # Update position
                self.nodes[node_id]['x'] += force[0] * scale
                self.nodes[node_id]['y'] += force[1] * scale
        
            # Update temperature (cool down the system)
            temperature *= 0.95
        
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

    def apply_config(self, config):
        """Apply configuration settings to the graph canvas"""
        if not config:
            return
        
        # Apply appearance settings
        if 'node_size' in config:
            self.node_radius = config['node_size']
            self.selected_node_radius = config['node_size'] * 1.2
        
        if 'edge_thickness' in config:
            self.edge_width = config['edge_thickness']
        
        if 'font_size' in config:
            self.font_size = config['font_size']
        
        # Apply color scheme
        if 'color_scheme' in config:
            scheme = config['color_scheme']
            if scheme == 'Dark':
                self.configure(bg='#2E2E2E')
                self.node_colors = {
                    'focus': '#FFD700',     # Gold
                    'cs': '#5A9BD5',        # Blue
                    'xaml': '#70AD47',      # Green
                    'other': '#9E9E9E',     # Gray
                    'default': '#7030A0'    # Purple
                }
            elif scheme == 'Light':
                self.configure(bg='#FFFFFF')
                self.node_colors = {
                    'focus': '#FFC000',     # Gold
                    'cs': '#ADD8E6',        # Light blue
                    'xaml': '#90EE90',      # Light green
                    'other': '#D3D3D3',     # Light gray
                    'default': '#B0C4DE'    # Blue
                }
            elif scheme == 'Colorful':
                self.configure(bg='#F5F5F5')
                self.node_colors = {
                    'focus': '#FFD700',     # Gold
                    'cs': '#4472C4',        # Blue
                    'xaml': '#70AD47',      # Green
                    'method': '#ED7D31',    # Orange
                    'class': '#5B9BD5',     # Light blue
                    'other': '#A5A5A5',     # Gray
                    'default': '#FFC000'    # Yellow
                }
            elif scheme == 'Monochrome':
                self.configure(bg='#FFFFFF')
                self.node_colors = {
                    'focus': '#404040',     # Dark gray
                    'cs': '#595959',        # Medium gray
                    'xaml': '#7F7F7F',      # Gray
                    'other': '#A5A5A5',     # Light gray
                    'default': '#D9D9D9'    # Very light gray
                }
        
        # Apply layout settings if auto-layout is enabled
        if config.get('auto_layout', False):
            algorithm = config.get('layout_algorithm', 'Force-Directed')
        
            if algorithm == 'Force-Directed':
                self.run_force_directed_layout()
            elif algorithm == 'Radial':
                self.run_obsidian_layout(config)
            elif algorithm == 'Hierarchical':
                self.run_hierarchical_layout()
            elif algorithm == 'Circular':
                self.run_circular_layout()
            elif algorithm == 'Grid':
                self.run_grid_layout()
    
        # Redraw with new settings
        self.draw_graph()


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

class InteractiveCodeViewer(ttk.Frame):
    """Interactive code viewer with syntax highlighting and clickable references"""
    
    def __init__(self, parent, on_reference_click=None):
        super().__init__(parent)
        
        self.parent = parent
        self.on_reference_click = on_reference_click
        
        # Create UI components
        self.create_ui()
        
        # Current file/method being displayed
        self.current_file = None
        self.current_method = None
        
        # Track all method references for click handling
        self.method_references = []  # List of (start_pos, end_pos, target_file, target_method)
        
    def create_ui(self):
        """Create the UI components"""
        # Method info area (displays signature, etc.)
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.method_name_var = tk.StringVar()
        self.method_signature_var = tk.StringVar()
        
        ttk.Label(self.info_frame, textvariable=self.method_name_var, 
                 font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(self.info_frame, textvariable=self.method_signature_var, 
                 font=('Helvetica', 10)).pack(anchor=tk.W)
        
        # Create horizontal separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)
        
        # Create code view area with line numbers
        self.code_frame = ttk.Frame(self)
        self.code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Line numbers canvas
        self.line_canvas = tk.Canvas(self.code_frame, width=40, bg='#f0f0f0')
        self.line_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text widget for code
        self.code_text = tk.Text(self.code_frame, wrap=tk.NONE, font=('Courier', 10),
                                bg='#ffffff', fg='#000000')
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for syntax highlighting
        self.configure_tags()
        
        # Add scrollbars
        self.yscrollbar = ttk.Scrollbar(self.code_frame, orient=tk.VERTICAL, 
                                       command=self.code_text.yview)
        self.yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.xscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, 
                                       command=self.code_text.xview)
        self.xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.code_text.configure(xscrollcommand=self.xscrollbar.set, 
                                yscrollcommand=self.yscrollbar.set)
        
        # Bind events
        self.code_text.bind('<KeyRelease>', self.update_line_numbers)
        self.code_text.bind('<MouseWheel>', self.update_line_numbers)
        self.code_text.bind('<Button-1>', self.on_text_click)
        
        # Make text read-only initially
        self.code_text.config(state=tk.DISABLED)
    
    def configure_tags(self):
        """Configure tags for syntax highlighting"""
        # Basic syntax highlighting
        self.code_text.tag_configure('keyword', foreground='blue')
        self.code_text.tag_configure('string', foreground='green')
        self.code_text.tag_configure('comment', foreground='gray')
        self.code_text.tag_configure('type', foreground='teal')
        
        # Method references
        self.code_text.tag_configure('method_call', foreground='purple')
        self.code_text.tag_configure('clickable', foreground='purple', underline=True)
        self.code_text.tag_configure('current_method', foreground='red', underline=True)
        
        # Highlight selected line
        self.code_text.tag_configure('highlight_line', background='#ffffcc')
    

    def display_method(self, file_path, method_name, method_info, reference_tracker, references=None):
        """Display a method with enhanced reference highlighting"""
        # Store current method info
        self.current_file = file_path
        self.current_method = method_name
    
        # Clear reference tracking
        self.method_references = []
    
        # Update method info labels
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
        
            # Highlight method calls with clickable references
            self.highlight_method_calls(method_body, method_info, reference_tracker)
        
            # Add additional reference highlighting if provided
            if references:
                self.highlight_references(references)
        
        # Make text read-only again
        self.code_text.config(state=tk.DISABLED)
    
        # Update line numbers
        self.update_line_numbers()

    def highlight_references(self, references):
        """Highlight specific references in the code with enhanced styling"""
        for ref in references:
            ref_type = ref.get('type', 'call')
            start_pos = ref.get('start_pos')
            end_pos = ref.get('end_pos')
            target = ref.get('target', {})
        
            if not start_pos or not end_pos:
                continue
            
            # Add appropriate tag based on reference type
            if ref_type == 'call':
                # Method call reference
                self.code_text.tag_add('method_call', start_pos, end_pos)
                self.code_text.tag_add('clickable', start_pos, end_pos)
            elif ref_type == 'definition':
                # Method definition reference
                self.code_text.tag_add('definition', start_pos, end_pos)
            elif ref_type == 'usage':
                # Variable usage reference
                self.code_text.tag_add('usage', start_pos, end_pos)
        
            # Store reference for click handling
            self.method_references.append({
                'start': start_pos,
                'end': end_pos,
                'type': ref_type,
                'file': target.get('file'),
                'method': target.get('method'),
                'class': target.get('class')
            })
    
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
    
    def highlight_method_calls(self, code, method_info, reference_tracker):
        """Highlight method calls with clickable references"""
        # Highlight calls to other methods
        for call_info in method_info.get('calls', []):
            # Get call details
            target_method = call_info.get('method', '')
            target_file = call_info.get('target_file', '')
            
            if not target_method:
                continue
                
            # Find all occurrences of this method call in the code
            pattern = r'\b' + re.escape(call_info.get('object', '')) + r'\.' + re.escape(target_method) + r'\s*\('
            
            start_pos = '1.0'
            while True:
                start_pos = self.code_text.search(pattern, start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                    
                # Get positions of object and method
                dot_pos = self.code_text.search(r'\.', start_pos, f"{start_pos}+{len(pattern)}c")
                if not dot_pos:
                    start_pos = f"{start_pos}+1c"
                    continue
                    
                method_start = f"{dot_pos}+1c"
                method_end = f"{method_start}+{len(target_method)}c"
                
                # Highlight method name
                self.code_text.tag_add('method_call', method_start, method_end)
                
                # Make clickable if target file exists
                if target_file:
                    self.code_text.tag_add('clickable', method_start, method_end)
                    
                    # Store reference for click handling
                    self.method_references.append({
                        'start': method_start,
                        'end': method_end,
                        'file': target_file,
                        'method': target_method
                    })
                
                start_pos = method_end
        
        # Also highlight other references that might be in the code
        # (e.g., method calls without object references)
        self.highlight_additional_references(code, reference_tracker)
    
    def highlight_additional_references(self, code, reference_tracker):
        """Find and highlight additional method references in the code"""
        # Get all method names in the project
        all_methods = set()
        for file_info in reference_tracker.file_info.values():
            if 'methods' in file_info:
                all_methods.update(file_info['methods'])
        
        # Highlight method names that are not already highlighted
        for method_name in all_methods:
            # Skip very short method names to avoid false positives
            if len(method_name) < 3:
                continue
                
            # Skip if it's the current method
            if method_name == self.current_method:
                continue
                
            # Search for method name followed by parenthesis
            pattern = r'\b' + re.escape(method_name) + r'\s*\('
            
            start_pos = '1.0'
            while True:
                start_pos = self.code_text.search(pattern, start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                    
                # Check if this position is already tagged
                tags = self.code_text.tag_names(start_pos)
                if 'method_call' in tags or 'string' in tags or 'comment' in tags:
                    # Skip if already highlighted or in string/comment
                    start_pos = f"{start_pos}+1c"
                    continue
                    
                method_end = f"{start_pos}+{len(method_name)}c"
                
                # Highlight as a potential method reference
                self.code_text.tag_add('method_call', start_pos, method_end)
                
                # Try to find the method in the codebase
                target_file = None
                for file_path, file_info in reference_tracker.file_info.items():
                    if 'methods' in file_info and method_name in file_info['methods']:
                        target_file = file_path
                        break
                
                if target_file:
                    self.code_text.tag_add('clickable', start_pos, method_end)
                    
                    # Store reference for click handling
                    self.method_references.append({
                        'start': start_pos,
                        'end': method_end,
                        'file': target_file,
                        'method': method_name
                    })
                
                start_pos = method_end
    
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
    
    def on_text_click(self, event):
        """Handle click on text - check if a method reference was clicked"""
        # Get click position
        index = self.code_text.index(f"@{event.x},{event.y}")
        
        # Check if the position is within any method reference
        for ref in self.method_references:
            start = ref['start']
            end = ref['end']
            
            # Convert to float values for comparison
            start_val = float(start)
            end_val = float(end)
            click_val = float(index)
            
            if start_val <= click_val <= end_val:
                # Reference was clicked
                if self.on_reference_click:
                    self.on_reference_click(ref['file'], ref['method'])
                return
    
    def highlight_line(self, line_number):
        """Highlight a specific line number"""
        # Remove existing line highlights
        self.code_text.tag_remove('highlight_line', '1.0', tk.END)
        
        # Highlight the specified line
        self.code_text.tag_add('highlight_line', f"{line_number}.0", f"{line_number + 1}.0")
        
        # Ensure the line is visible
        self.code_text.see(f"{line_number}.0")

class MethodDocPanel(ttk.Frame):
    """Panel to show method documentation and additional info"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create UI components
        self.create_ui()
    
    def create_ui(self):
        """Create UI components"""
        # Create notebook for different sections
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create documentation tab
        self.doc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.doc_frame, text="Documentation")
        
        # Documentation text
        self.doc_text = tk.Text(self.doc_frame, wrap=tk.WORD, height=10,
                              font=('Helvetica', 10))
        self.doc_text.pack(fill=tk.BOTH, expand=True)
        
        # Parameters tab
        self.param_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.param_frame, text="Parameters")
        
        # Parameters treeview
        self.param_tree = ttk.Treeview(self.param_frame, columns=('type', 'name', 'desc'),
                                     show='headings')
        self.param_tree.pack(fill=tk.BOTH, expand=True)
        
        self.param_tree.heading('type', text='Type')
        self.param_tree.heading('name', text='Name')
        self.param_tree.heading('desc', text='Description')
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        
        # Statistics display - grid layout
        self.stats_grid = ttk.Frame(self.stats_frame)
        self.stats_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Complexity
        ttk.Label(self.stats_grid, text="Complexity:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.complexity_var = tk.StringVar()
        ttk.Label(self.stats_grid, textvariable=self.complexity_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Lines
        ttk.Label(self.stats_grid, text="Lines:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lines_var = tk.StringVar()
        ttk.Label(self.stats_grid, textvariable=self.lines_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Called by
        ttk.Label(self.stats_grid, text="Called by:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.called_by_var = tk.StringVar()
        ttk.Label(self.stats_grid, textvariable=self.called_by_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Calls
        ttk.Label(self.stats_grid, text="Calls:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.calls_var = tk.StringVar()
        ttk.Label(self.stats_grid, textvariable=self.calls_var).grid(row=3, column=1, sticky=tk.W, pady=2)
    
    def update_with_method(self, method_info):
        """Update panel with method information"""
        # Update documentation tab
        self.doc_text.config(state=tk.NORMAL)
        self.doc_text.delete('1.0', tk.END)
        
        # Extract documentation from method body
        doc_text = self.extract_documentation(method_info.get('body', ''))
        if doc_text:
            self.doc_text.insert('1.0', doc_text)
        else:
            self.doc_text.insert('1.0', "No documentation available.")
            
        self.doc_text.config(state=tk.DISABLED)
        
        # Update parameters tab
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
            
        # Add parameters
        for param in method_info.get('parameters', []):
            param_type = param.get('type', '')
            param_name = param.get('name', '')
            param_desc = ''  # Extract from documentation if available
            
            self.param_tree.insert('', tk.END, values=(param_type, param_name, param_desc))
        
        # Update statistics
        # Calculate complexity (simple estimate based on control structures)
        body = method_info.get('body', '')
        complexity = 1  # Base complexity
        complexity += body.count('if ') 
        complexity += body.count('for ') 
        complexity += body.count('foreach ') 
        complexity += body.count('while ') 
        complexity += body.count('case ') 
        complexity += body.count('catch ')
        
        self.complexity_var.set(str(complexity))
        
        # Count lines
        lines = body.count('\n') + 1
        self.lines_var.set(str(lines))
        
        # Count references
        calls_count = len(method_info.get('calls', []))
        self.calls_var.set(str(calls_count))
        
        called_by_count = len(method_info.get('called_by', []))
        self.called_by_var.set(str(called_by_count))
    
    def extract_documentation(self, method_body):
        """Extract documentation comments from method body"""
        # Look for C# XML documentation comments
        lines = method_body.split('\n')
        doc_lines = []
        in_doc = False
        
        for line in lines:
            line = line.strip()
            if '///' in line:
                # Remove /// and trim
                doc_line = line.replace('///', '').strip()
                doc_lines.append(doc_line)
                in_doc = True
            elif in_doc and not line:
                # Keep blank lines in documentation
                doc_lines.append('')
            elif in_doc:
                # End of documentation block
                break
                
        # Process XML tags if present
        doc_text = '\n'.join(doc_lines)
        
        # Replace common XML tags with formatted text
        doc_text = re.sub(r'<summary>(.*?)</summary>', r'\1', doc_text, flags=re.DOTALL)
        doc_text = re.sub(r'<param name="(\w+)">(.*?)</param>', r'Parameter \1: \2', doc_text, flags=re.DOTALL)
        doc_text = re.sub(r'<returns>(.*?)</returns>', r'Returns: \1', doc_text, flags=re.DOTALL)
        doc_text = re.sub(r'<exception cref="(\w+)">(.*?)</exception>', r'Exception \1: \2', doc_text, flags=re.DOTALL)
        
        return doc_text

    def create_node_context_menu(self):
        """Create context menu for nodes"""
        self.node_menu = tk.Menu(self, tearoff=0)
        self.node_menu.add_command(label="Go To Definition", command=self.go_to_definition)
        self.node_menu.add_command(label="Find All References", command=self.find_all_references)
        self.node_menu.add_command(label="Show Call Hierarchy", command=self.show_call_hierarchy)
        self.node_menu.add_separator()
        self.node_menu.add_command(label="Focus On This Node", command=self.focus_on_node)
        self.node_menu.add_command(label="Expand Graph From Here", command=self.expand_graph)
    
        # Bind right-click on nodes
        self.tag_bind("node", "<Button-3>", self.show_node_menu)

    def show_node_menu(self, event):
        """Show context menu on right-click"""
        # Find node under cursor
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        node_id = self.find_node_at(x, y)
    
        if node_id:
            # Set this as the selected node
            self.selected_node = node_id
            self.draw_graph()  # Redraw to show selection
        
            # Update menu state based on node type
            node_data = self.nodes[node_id]
            node_type = node_data.get('type', 'default')
        
            # Enable/disable menu items based on node type
            if node_type == 'method':
                self.node_menu.entryconfig("Go To Definition", state="normal")
                self.node_menu.entryconfig("Find All References", state="normal")
                self.node_menu.entryconfig("Show Call Hierarchy", state="normal")
            else:
                self.node_menu.entryconfig("Go To Definition", state="disabled")
                self.node_menu.entryconfig("Find All References", state="disabled")
                self.node_menu.entryconfig("Show Call Hierarchy", state="disabled")
        
            # Display the menu
            self.node_menu.post(event.x_root, event.y_root)