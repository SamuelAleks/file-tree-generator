"""
Code visualization module for the File Tree Generator.

This module provides functionality to visualize code references graphically,
including file-to-file, class-to-class, and method-to-method relationships.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Set, Tuple, Optional, Any, Union, Callable

# For graph visualization
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

class CodeVisualizer:
    """
    Class for generating and displaying code reference visualizations.
    """
    
    def __init__(self, reference_tracker=None, log_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the code visualizer.
        
        Args:
            reference_tracker: Reference tracking manager
            log_callback: Function to call for logging
        """
        self.reference_tracker = reference_tracker
        self.log_callback = log_callback or (lambda msg: None)
        
        # Check if visualization libraries are available
        self.can_visualize = VISUALIZATION_AVAILABLE
        if not self.can_visualize:
            self.log("Visualization libraries (networkx, matplotlib) not found. "
                     "Install them using: pip install networkx matplotlib")
    
    def log(self, message: str) -> None:
        """Log a message using the callback if available"""
        if self.log_callback:
            self.log_callback(message)
    
    def create_file_reference_graph(self, 
                                   selected_files: List[str], 
                                   max_depth: int = 1) -> Optional[nx.DiGraph]:
        """
        Create a directed graph of file references.
        
        Args:
            selected_files: List of files to start with
            max_depth: Maximum reference depth to include
            
        Returns:
            NetworkX directed graph or None if libraries not available
        """
        if not self.can_visualize:
            self.log("Visualization libraries not available. Cannot create graph.")
            return None
            
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
            
        # Create directed graph
        G = nx.DiGraph()
        
        # Track files we've already processed to avoid duplicates
        processed_files = set()
        
        # Process files with BFS to respect max_depth
        def process_file(file_path: str, current_depth: int) -> None:
            if file_path in processed_files or current_depth > max_depth:
                return
                
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
            G.add_node(file_path, 
                      label=display_name, 
                      type=node_type, 
                      is_selected=file_path in selected_files)
                
            # Find references from this file
            referenced_by, references_to = self.reference_tracker.get_reference_details(file_path)
            
            # Add edges for references
            for target_file in references_to:
                G.add_edge(file_path, target_file, type='references')
                
                # Process referenced files if within depth limit
                if current_depth < max_depth:
                    process_file(target_file, current_depth + 1)
                    
            # Add edges for files that reference this file
            for source_file in referenced_by:
                G.add_edge(source_file, file_path, type='referenced_by')
                
                # Process referencing files if within depth limit
                if current_depth < max_depth:
                    process_file(source_file, current_depth + 1)
        
        # Start processing from selected files
        for file_path in selected_files:
            process_file(file_path, 0)
            
        return G
    
    def create_method_reference_graph(self, 
                                    file_path: str, 
                                    method_name: Optional[str] = None, 
                                    max_depth: int = 1) -> Optional[nx.DiGraph]:
        """
        Create a directed graph of method references.
        
        Args:
            file_path: Path to the file containing methods
            method_name: Optional specific method to focus on
            max_depth: Maximum reference depth to include
            
        Returns:
            NetworkX directed graph or None if libraries not available
        """
        if not self.can_visualize:
            self.log("Visualization libraries not available. Cannot create graph.")
            return None
            
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
            
        # Create directed graph
        G = nx.DiGraph()
        
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
            def process_method(file: str, method: str, current_depth: int) -> None:
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
                G.add_node(method_id, 
                          label=label, 
                          file=file, 
                          method=method, 
                          is_focus=(file == file_path and method == method_name))
                
                # Get incoming and outgoing references
                incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(file, method)
                
                # Add edges for outgoing references
                for ref in outgoing_refs:
                    target_file = ref.get('file')
                    target_method = ref.get('method')
                    
                    if target_file and target_method:
                        target_id = f"{target_file}::{target_method}"
                        G.add_edge(method_id, target_id, type='calls')
                        
                        # Process target method if within depth limit
                        if current_depth < max_depth:
                            process_method(target_file, target_method, current_depth + 1)
                
                # Add edges for incoming references
                for ref in incoming_refs:
                    source_file = ref.get('file')
                    source_method = ref.get('method')
                    
                    if source_file and source_method:
                        source_id = f"{source_file}::{source_method}"
                        G.add_edge(source_id, method_id, type='calls')
                        
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
                G.add_node(method_id, label=method, file=file_path, method=method, is_focus=True)
                
                # Get outgoing references
                _, outgoing_refs = self.reference_tracker.get_method_references(file_path, method)
                
                # Add edges for method calls within the same file
                for ref in outgoing_refs:
                    if ref.get('file') == file_path:
                        target_method = ref.get('method')
                        target_id = f"{file_path}::{target_method}"
                        G.add_edge(method_id, target_id, type='calls')
        
        return G
    
    def create_class_reference_graph(self, 
                                   root_dir: str, 
                                   selected_classes: Optional[List[str]] = None, 
                                   max_depth: int = 1) -> Optional[nx.DiGraph]:
        """
        Create a directed graph of class references.
        
        Args:
            root_dir: Root directory for analysis
            selected_classes: Optional list of classes to focus on
            max_depth: Maximum reference depth to include
            
        Returns:
            NetworkX directed graph or None if libraries not available
        """
        if not self.can_visualize:
            self.log("Visualization libraries not available. Cannot create graph.")
            return None
            
        if not self.reference_tracker:
            self.log("Reference tracker not available. Cannot create graph.")
            return None
            
        # Create directed graph
        G = nx.DiGraph()
        
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
        
        def process_class(class_name: str, current_depth: int) -> None:
            if class_name in processed_classes or current_depth > max_depth:
                return
                
            processed_classes.add(class_name)
            
            # Find the file that defines this class
            file_path = class_to_file.get(class_name)
            if not file_path:
                return
                
            # Add node for this class
            G.add_node(class_name, 
                      label=class_name, 
                      file=file_path, 
                      is_focus=selected_classes and class_name in selected_classes)
                
            # Find inheritance relationships
            file_info = self.reference_tracker.tracker.file_info.get(file_path, {})
            
            # Add edges for inheritance
            for base_class in file_info.get('inheritance', []):
                if base_class in class_to_file:
                    G.add_edge(class_name, base_class, type='inherits')
                    
                    # Process base class if within depth limit
                    if current_depth < max_depth:
                        process_class(base_class, current_depth + 1)
            
            # Find classes that inherit from this class
            for other_class, other_file in class_to_file.items():
                if other_class == class_name:
                    continue
                    
                other_info = self.reference_tracker.tracker.file_info.get(other_file, {})
                if class_name in other_info.get('inheritance', []):
                    G.add_edge(other_class, class_name, type='inherits')
                    
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
        
        return G
    
    def visualize_graph(self, graph: nx.DiGraph, title: str, parent_window: Optional[tk.Toplevel] = None) -> None:
        """
        Visualize a graph in a Tkinter window.
        
        Args:
            graph: NetworkX graph to visualize
            title: Title for the visualization window
            parent_window: Optional parent window
        """
        if not self.can_visualize:
            messagebox.showerror("Error", 
                                "Visualization libraries (networkx, matplotlib) not found.\n"
                                "Install them using: pip install networkx matplotlib")
            return
            
        if not graph or len(graph.nodes()) == 0:
            messagebox.showinfo("Information", "No nodes to display in the graph.")
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
        ttk.Label(control_frame, text="Layout:").pack(side=tk.LEFT, padx=(0, 5))
        
        layout_var = tk.StringVar(value="spring")
        layout_combo = ttk.Combobox(control_frame, textvariable=layout_var, width=15)
        layout_combo['values'] = ('spring', 'circular', 'kamada_kawai', 'planar', 'random', 'shell', 'spectral')
        layout_combo['state'] = 'readonly'
        layout_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add export button
        export_button = ttk.Button(control_frame, text="Export as PNG", 
                                  command=lambda: self.export_graph_image(graph, title))
        export_button.pack(side=tk.RIGHT)
        
        # Function to update the visualization
        def update_visualization():
            # Clear previous plot
            for widget in viz_frame.winfo_children():
                widget.destroy()
                
            # Create a new figure
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Get the layout algorithm
            layout_name = layout_var.get()
            if layout_name == "spring":
                pos = nx.spring_layout(graph)
            elif layout_name == "circular":
                pos = nx.circular_layout(graph)
            elif layout_name == "kamada_kawai":
                try:
                    pos = nx.kamada_kawai_layout(graph)
                except:
                    pos = nx.spring_layout(graph)  # Fallback if kamada_kawai fails
            elif layout_name == "planar":
                try:
                    pos = nx.planar_layout(graph)
                except:
                    pos = nx.spring_layout(graph)  # Fallback if planar fails
            elif layout_name == "random":
                pos = nx.random_layout(graph)
            elif layout_name == "shell":
                pos = nx.shell_layout(graph)
            elif layout_name == "spectral":
                try:
                    pos = nx.spectral_layout(graph)
                except:
                    pos = nx.spring_layout(graph)  # Fallback if spectral fails
            else:
                pos = nx.spring_layout(graph)
                
            # Create node lists by type
            focus_nodes = [n for n, attr in graph.nodes(data=True) if attr.get('is_focus', False)]
            
            if all('type' in graph.nodes[n] for n in graph.nodes):
                # For file references
                cs_nodes = [n for n, attr in graph.nodes(data=True) 
                           if attr.get('type') == 'cs' and n not in focus_nodes]
                xaml_nodes = [n for n, attr in graph.nodes(data=True) 
                             if attr.get('type') == 'xaml' and n not in focus_nodes]
                other_nodes = [n for n, attr in graph.nodes(data=True) 
                              if attr.get('type') not in ('cs', 'xaml') and n not in focus_nodes]
                
                # Draw nodes by type
                nx.draw_networkx_nodes(graph, pos, nodelist=focus_nodes, node_color='gold', 
                                      node_size=700, alpha=0.8)
                nx.draw_networkx_nodes(graph, pos, nodelist=cs_nodes, node_color='lightblue', 
                                      node_size=500, alpha=0.8)
                nx.draw_networkx_nodes(graph, pos, nodelist=xaml_nodes, node_color='lightgreen', 
                                      node_size=500, alpha=0.8)
                nx.draw_networkx_nodes(graph, pos, nodelist=other_nodes, node_color='lightgray', 
                                      node_size=500, alpha=0.8)
            else:
                # For method or class references
                regular_nodes = [n for n in graph.nodes if n not in focus_nodes]
                
                # Draw nodes
                nx.draw_networkx_nodes(graph, pos, nodelist=focus_nodes, node_color='gold', 
                                      node_size=700, alpha=0.8)
                nx.draw_networkx_nodes(graph, pos, nodelist=regular_nodes, node_color='lightblue', 
                                      node_size=500, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(graph, pos, edge_color='gray', arrows=True)
            
            # Add labels
            labels = {n: graph.nodes[n].get('label', str(n)) for n in graph.nodes}
            nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10)
            
            # Remove axis
            ax.axis('off')
            
            # Add the plot to the frame
            canvas = FigureCanvasTkAgg(fig, master=viz_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Update when layout changes
        layout_combo.bind('<<ComboboxSelected>>', lambda e: update_visualization())
        
        # Initial visualization
        update_visualization()
    
    def export_graph_image(self, graph: nx.DiGraph, title: str) -> None:
        """
        Export the graph visualization as a PNG image.
        
        Args:
            graph: NetworkX graph to export
            title: Title for the image file
        """
        from tkinter import filedialog
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Graph Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        # Create a new figure for export (higher resolution)
        plt.figure(figsize=(12, 10), dpi=300)
        
        # Create layout
        pos = nx.spring_layout(graph)
        
        # Create node lists by type
        focus_nodes = [n for n, attr in graph.nodes(data=True) if attr.get('is_focus', False)]
        
        if all('type' in graph.nodes[n] for n in graph.nodes):
            # For file references
            cs_nodes = [n for n, attr in graph.nodes(data=True) 
                       if attr.get('type') == 'cs' and n not in focus_nodes]
            xaml_nodes = [n for n, attr in graph.nodes(data=True) 
                         if attr.get('type') == 'xaml' and n not in focus_nodes]
            other_nodes = [n for n, attr in graph.nodes(data=True) 
                          if attr.get('type') not in ('cs', 'xaml') and n not in focus_nodes]
            
            # Draw nodes by type
            nx.draw_networkx_nodes(graph, pos, nodelist=focus_nodes, node_color='gold', 
                                  node_size=700, alpha=0.8)
            nx.draw_networkx_nodes(graph, pos, nodelist=cs_nodes, node_color='lightblue', 
                                  node_size=500, alpha=0.8)
            nx.draw_networkx_nodes(graph, pos, nodelist=xaml_nodes, node_color='lightgreen', 
                                  node_size=500, alpha=0.8)
            nx.draw_networkx_nodes(graph, pos, nodelist=other_nodes, node_color='lightgray', 
                                  node_size=500, alpha=0.8)
        else:
            # For method or class references
            regular_nodes = [n for n in graph.nodes if n not in focus_nodes]
            
            # Draw nodes
            nx.draw_networkx_nodes(graph, pos, nodelist=focus_nodes, node_color='gold', 
                                  node_size=700, alpha=0.8)
            nx.draw_networkx_nodes(graph, pos, nodelist=regular_nodes, node_color='lightblue', 
                                  node_size=500, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, edge_color='gray', arrows=True)
        
        # Add labels
        labels = {n: graph.nodes[n].get('label', str(n)) for n in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10)
        
        # Remove axis
        plt.axis('off')
        
        # Add title
        plt.title(title)
        
        # Save the figure
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        self.log(f"Graph exported to {filename}")