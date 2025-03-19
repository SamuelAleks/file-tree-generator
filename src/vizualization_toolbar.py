import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class VisualizationToolbar:
    """
    A specialized toolbar for code visualization functions.
    
    This component provides a unified interface for all visualization features,
    including file relationships, method visualization, and reference tracking.
    """
    
    def __init__(self, parent, app_instance, frame=None):
        """
        Create the visualization toolbar.
        
        Args:
            parent: Parent window or frame
            app_instance: Main application instance
            frame: Optional existing frame to use instead of creating a new one
        """
        self.parent = parent
        self.app = app_instance
        
        # Create a frame if not provided
        if frame:
            self.frame = frame
        else:
            self.frame = ttk.Frame(parent)
            self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add toolbar contents
        self.create_visualization_tools()
    
    def create_visualization_tools(self):
        """Create the visualization toolbar contents"""
        # Create visualization section
        vis_frame = ttk.LabelFrame(self.frame, text="Visualization")
        vis_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # File relationship visualizer button
        self.file_button = ttk.Button(
            vis_frame, 
            text="File Relationships", 
            command=self.open_file_visualizer,
            width=18
        )
        self.file_button.pack(side=tk.TOP, pady=2, padx=5)
        
        # Method visualizer button
        self.method_button = ttk.Button(
            vis_frame, 
            text="Method Relationships", 
            command=self.open_method_visualizer,
            width=18
        )
        self.method_button.pack(side=tk.TOP, pady=2, padx=5)
        
        # Reference graph button
        self.graph_button = ttk.Button(
            vis_frame, 
            text="Reference Graph", 
            command=self.show_reference_graph,
            width=18
        )
        self.graph_button.pack(side=tk.TOP, pady=2, padx=5)
        
        # Configure button styles
        try:
            style = ttk.Style()
            style.configure('Toolbutton', font=('Arial', 9))
        except Exception:
            # Ignore style errors
            pass
        
        # Add tooltips
        self.create_tooltip(self.file_button, "View relationships between files and their contents")
        self.create_tooltip(self.method_button, "View method connections with interactive visualization")
        self.create_tooltip(self.graph_button, "Show a graph of references between files")
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            try:
                # Create tooltip only when mouse enters
                tooltip = tk.Toplevel(widget)
                tooltip.overrideredirect(True)
                tooltip.geometry(f"+{event.x_root+15}+{event.y_root+10}")
            
                label = ttk.Label(tooltip, text=text, background="#FFFFD0", relief="solid", borderwidth=1)
                label.pack()
            
                # Store tooltip reference
                widget.tooltip = tooltip
            except Exception:
                # Ignore tooltip errors
                pass
        
        def leave(event):
            # Remove tooltip when mouse leaves
            if hasattr(widget, "tooltip"):
                try:
                    widget.tooltip.destroy()
                    delattr(widget, "tooltip")
                except Exception:
                    # Ignore tooltip errors
                    pass
            
        # Bind events with try/except to prevent errors
        try:
            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)
        except Exception:
            # Ignore binding errors
            pass
    
    def open_file_visualizer(self):
        """Open the file relationship visualizer"""
        # Check if app has a visualization manager or integration class
        if hasattr(self.app, 'visualization_manager'):
            # Use the visualization manager
            self.app.visualization_manager.visualize_file()
        elif hasattr(self.app, 'visualizer'):
            # Use the visualizer integration
            self.app.visualizer.open_code_visualizer()
        elif hasattr(self.app, 'open_code_visualizer'):
            # Use direct method
            self.app.open_code_visualizer()
        else:
            messagebox.showinfo("Information", "Visualization feature is not available")
    
    def open_method_visualizer(self):
        """Open the method relationship visualizer"""
        # Check if app has a visualization manager or integration class
        if hasattr(self.app, 'visualization_manager'):
            # Use the visualization manager
            self.app.visualization_manager.visualize_method()
        elif hasattr(self.app, 'visualizer'):
            # Use the visualizer integration
            self.app.visualizer.open_method_visualizer()
        elif hasattr(self.app, 'open_method_visualizer'):
            # Use direct method
            self.app.open_method_visualizer()
        else:
            messagebox.showinfo("Information", "Method visualization feature is not available")
    
    def show_reference_graph(self):
        """Show the reference graph visualization"""
        # Check if app has a visualization manager or integration class
        if hasattr(self.app, 'visualization_manager'):
            # Use the visualization manager
            self.app.visualization_manager.show_reference_graph()
        elif hasattr(self.app, 'visualizer'):
            # Use the visualizer integration
            self.app.visualizer.show_reference_graph()
        elif hasattr(self.app, 'show_reference_graph'):
            # Use direct method
            self.app.show_reference_graph()
        else:
            messagebox.showinfo("Information", "Reference graph feature is not available")