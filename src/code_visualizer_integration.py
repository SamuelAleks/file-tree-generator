# Update to code_visualizer_integration.py to fix integration issues

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import importlib

class CodeVisualizerIntegration:
    """
    Integration class that connects all visualization components with the main application.
    Provides a cohesive API for code visualization features.
    """
    
    def __init__(self, app_instance):
        """Initialize the visualizer integration with the parent application"""
        self.app = app_instance
        self.reference_tracker = None
        self.visualization_manager = None
        
        # Link directly to visualization manager if available
        if hasattr(app_instance, 'visualization_manager'):
            self.visualization_manager = app_instance.visualization_manager
            self.log("Connected to existing visualization manager")
        else:
            # Try to initialize the visualization manager
            self.init_visualization_manager()
        
        # Add toolbar integration
        self.add_visualize_toolbar()
        
        # Add direct method references to the app for convenience
        self.setup_convenience_methods()
    
    def init_visualization_manager(self):
        """Initialize visualization manager if needed"""
        try:
            # See if visualization_manager module is available
            if importlib.util.find_spec("visualization_manager"):
                from visualization_manager import VisualizationManager
                self.visualization_manager = VisualizationManager(self.app)
                
                # Add reference to the app
                if hasattr(self.app, 'visualization_manager'):
                    self.app.visualization_manager = self.visualization_manager
                self.log("Visualization manager initialized")
            else:
                self.log("visualization_manager module not available")
        except Exception as e:
            self.log(f"Error initializing visualization manager: {str(e)}")
    
    def setup_convenience_methods(self):
        """Set up direct method references for convenience and backward compatibility"""
        # We'll only add these methods if they don't already exist on the app
        
        # File visualization
        if not hasattr(self.app, 'open_code_visualizer'):
            self.app.open_code_visualizer = self.open_code_visualizer
            
        # Method visualization
        if not hasattr(self.app, 'open_method_visualizer'):
            self.app.open_method_visualizer = self.open_method_visualizer
            
        # Reference graph
        if not hasattr(self.app, 'show_reference_graph'):
            self.app.show_reference_graph = self.show_reference_graph
            
        # All references visualization
        if not hasattr(self.app, 'visualize_all_references'):
            self.app.visualize_all_references = self.analyze_all_references
    
    def log(self, message):
        """Log a message using the app's logging function if available"""
        if hasattr(self.app, 'log'):
            self.app.log(message)
        else:
            print(f"CodeVisualizerIntegration: {message}")
    
    def ensure_reference_tracker(self, directory=None):
        """
        Ensure reference tracker is available.
        
        Args:
            directory: Root directory to use if creating a new tracker
            
        Returns:
            True if reference tracker is available, False otherwise
        """
        # First check if the app already has one
        if hasattr(self.app, 'reference_tracker') and self.app.reference_tracker:
            self.reference_tracker = self.app.reference_tracker
            return True
            
        # Check if visualization manager has one
        if self.visualization_manager and hasattr(self.visualization_manager, 'reference_tracker'):
            self.reference_tracker = self.visualization_manager.reference_tracker
            if self.reference_tracker:
                return True
                
        # Otherwise create a new one
        try:
            if not directory:
                if hasattr(self.app, 'root_dir_var'):
                    directory = self.app.root_dir_var.get()
                elif hasattr(self.app, 'selected_files') and self.app.selected_files:
                    directory = os.path.dirname(self.app.selected_files[0])
                    
            if not directory or not os.path.isdir(directory):
                messagebox.showerror("Error", "Please select a valid root directory first")
                return False
                
            # Create reference tracker
            from reference_tracking import ReferenceTrackingManager
            self.log(f"Initializing reference tracker for {directory}...")
            self.reference_tracker = ReferenceTrackingManager(directory, self.log)
            self.reference_tracker.parse_directory()
            
            # Share with the app
            if hasattr(self.app, 'reference_tracker'):
                self.app.reference_tracker = self.reference_tracker
                
            # Share with visualization manager
            if self.visualization_manager:
                self.visualization_manager.reference_tracker = self.reference_tracker
                
            return True
        except Exception as e:
            self.log(f"Error creating reference tracker: {str(e)}")
            return False
    
    def add_visualize_toolbar(self):
        """Add visualization section to the toolbar if available"""
        # Only proceed if the app has a toolbar frame
        if not hasattr(self.app, 'root'):
            return
    
        # Try to find or create a toolbar frame
        toolbar_frame = None
    
        # First check if we have a visualization toolbar module
        try:
            # Try to find the module without importing it first
            import importlib.util
            if importlib.util.find_spec("vizualization_toolbar"):
                from vizualization_toolbar import VisualizationToolbar
                # Create the toolbar
                self.toolbar = VisualizationToolbar(self.app.root, self.app)
                self.log("Added visualization toolbar")
                return
            else:
                self.log("Visualization toolbar module not available")
        except ImportError:
            # No toolbar module, so we'll try to add tools to existing toolbar
            self.log("Visualization toolbar import failed, adding to existing toolbar")
        except Exception as e:
            self.log(f"Error creating visualization toolbar: {str(e)}")
    
        # Look for existing toolbar or similar component
        if hasattr(self.app, 'toolbar_frame'):
            toolbar_frame = self.app.toolbar_frame
        else:
            # Try to find a frame that looks like a toolbar
            for child in self.app.root.winfo_children():
                if isinstance(child, ttk.Frame) and hasattr(child, 'winfo_children'):
                    # If frame has buttons, it's probably a toolbar
                    if any(isinstance(grandchild, ttk.Button) for grandchild in child.winfo_children()):
                        toolbar_frame = child
                        break
    
        # If we found a toolbar, add buttons to it
        if toolbar_frame:
            try:
                # Use proper Tkinter button creation
                file_button = ttk.Button(toolbar_frame, text="Code Visualizer", 
                                     command=self.open_code_visualizer)
                file_button.pack(side=tk.LEFT, padx=5)
            
                # Method visualizer button
                method_button = ttk.Button(toolbar_frame, text="Method Visualizer", 
                                        command=self.open_method_visualizer)
                method_button.pack(side=tk.LEFT, padx=5)
            
                self.log("Added visualization buttons to existing toolbar")
            except Exception as e:
                self.log(f"Error adding toolbar buttons: {str(e)}")
    
    def open_code_visualizer(self, file_path=None):
        """
        Open the code relationship visualizer.
        
        Args:
            file_path: Path to the file to visualize (prompts if None)
            
        Returns:
            True if visualizer opened successfully, False otherwise
        """
        # Use visualization manager if available
        if self.visualization_manager:
            return self.visualization_manager.visualize_file(file_path)
            
        # Otherwise handle it directly
        if not file_path:
            # Check if there's a selected file in the app
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                file_path = self.app.selected_files[0]
            else:
                # Prompt user to select a file
                file_path = filedialog.askopenfilename(
                    title="Select File to Visualize",
                    filetypes=[
                        ("C# Files", "*.cs"), 
                        ("XAML Files", "*.xaml;*.axaml"),
                        ("All Files", "*.*")
                    ]
                )
                
        if not file_path or not os.path.isfile(file_path):
            self.log("No valid file selected for visualization")
            return False
        
        # Ensure reference tracker is available
        if not self.ensure_reference_tracker(os.path.dirname(file_path)):
            return False
        
        # Create visualizer
        try:
            self.log(f"Opening code visualizer for {file_path}")
            
            # Import the necessary class
            from code_visualizer import CodeRelationshipVisualizer
            
            # Create the visualizer
            visualizer = CodeRelationshipVisualizer(
                self.app.root,
                self.reference_tracker,
                file_path
            )
            
            return True
        except ImportError:
            messagebox.showinfo("Information", "CodeRelationshipVisualizer is not available")
            return False
        except Exception as e:
            self.log(f"Error opening code visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open visualizer: {str(e)}")
            return False
    
    def open_method_visualizer(self, file_path=None, method_name=None):
        """
        Open the method relationship visualizer.
        
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method to visualize
            
        Returns:
            True if visualizer opened successfully, False otherwise
        """
        # Use visualization manager if available
        if self.visualization_manager:
            return self.visualization_manager.visualize_method(file_path, method_name)
            
        # Otherwise handle it directly
        if not file_path:
            # Check if there's a current file in the app
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                file_path = self.app.selected_files[0]
            else:
                # Prompt user to select a file
                file_path = filedialog.askopenfilename(
                    title="Select File for Method Visualization",
                    filetypes=[("C# Files", "*.cs"), ("All Files", "*.*")]
                )
                
        if not file_path or not os.path.isfile(file_path):
            self.log("No valid file selected for method visualization")
            return False
        
        # Ensure reference tracker is available
        if not self.ensure_reference_tracker(os.path.dirname(file_path)):
            return False
            
        # Get method name if not provided
        if not method_name:
            # Get methods in file
            methods = self.reference_tracker.get_methods_in_file(file_path)
            
            if not methods:
                messagebox.showinfo("Information", "No methods found in this file")
                return False
                
            # Prompt user to select a method
            method_name = simpledialog.askstring(
                "Select Method",
                "Enter method name:",
                initialvalue=methods[0] if methods else ""
            )
            
            if not method_name:
                return False
        
        # Try to open method visualizer
        try:
            self.log(f"Opening method visualizer for {method_name} in {file_path}")
            
            # Try to import the specialized method visualizer
            try:
                from method_relationship_visualizer import MethodRelationshipVisualizer
                
                # Create the visualizer
                visualizer = MethodRelationshipVisualizer(
                    self.app.root,
                    self.reference_tracker,
                    file_path,
                    method_name
                )
                
                return True
            except ImportError:
                # Fall back to general code visualizer
                self.log("MethodRelationshipVisualizer not available, using general visualizer")
                return self.open_code_visualizer(file_path)
                
        except Exception as e:
            self.log(f"Error opening method visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open method visualizer: {str(e)}")
            return False
    
    def show_reference_graph(self, start_files=None):
        """
        Show a graph of references between files.
        
        Args:
            start_files: List of files to include (defaults to app's selected files)
            
        Returns:
            True if graph shown successfully, False otherwise
        """
        # Use visualization manager if available
        if self.visualization_manager:
            return self.visualization_manager.show_reference_graph(start_files)
            
        # Otherwise handle it directly
        if not start_files:
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                start_files = self.app.selected_files
            else:
                # Let user select files
                try:
                    from file_selector import FileSelector
                    
                    # Get root directory
                    root_dir = None
                    if hasattr(self.app, 'root_dir_var'):
                        root_dir = self.app.root_dir_var.get()
                    
                    if not root_dir or not os.path.isdir(root_dir):
                        messagebox.showerror("Error", "Please select a valid root directory first")
                        return False
                    
                    # Open file selector
                    file_selector = FileSelector(self.app.root, root_dir)
                    self.app.root.wait_window(file_selector)
                    
                    # Get selected files
                    start_files = file_selector.get_selected_files()
                except ImportError:
                    messagebox.showinfo("Information", "File selector not available")
                    return False
        
        if not start_files:
            messagebox.showinfo("Information", "No files selected for reference graph")
            return False
            
        # Ensure reference tracker is available
        if not self.ensure_reference_tracker():
            return False
            
        # Get reference depth
        depth = simpledialog.askinteger(
            "Reference Depth",
            "Enter maximum reference depth (1-5):",
            minvalue=1, maxvalue=5, initialvalue=2
        )
        
        if not depth:
            return False
            
        try:
            self.log(f"Analyzing references for {len(start_files)} files with depth {depth}")
            
            # Find related files
            related_files = self.reference_tracker.find_related_files(start_files, depth)
            
            # Generate a summary
            summary = self.reference_tracker.generate_reference_summary(related_files)
            
            # Create a dialog to show the summary
            dialog = tk.Toplevel(self.app.root)
            dialog.title("Reference Analysis Summary")
            dialog.geometry("600x400")
            dialog.transient(self.app.root)
            
            # Create scrolled text area for summary
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text = tk.Text(text_frame, wrap=tk.WORD)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            text.configure(yscrollcommand=scroll.set)
            
            # Insert summary
            text.insert('1.0', summary)
            text.config(state=tk.DISABLED)
            
            # Close button
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
            
            # Ask if user wants to visualize the first file
            if messagebox.askyesno("Visualization", 
                                "Would you like to open the visualizer for the first file?"):
                self.open_code_visualizer(start_files[0])
            
            return True
        except Exception as e:
            self.log(f"Error analyzing references: {str(e)}")
            messagebox.showerror("Error", f"Could not analyze references: {str(e)}")
            return False
    
    def analyze_all_references(self):
        """
        Analyze all references in the project.
        
        Returns:
            True if analysis completed successfully, False otherwise
        """
        # Use visualization manager if available
        if self.visualization_manager:
            return self.visualization_manager.visualize_all_references()
            
        # Otherwise handle it directly
        # Ensure reference tracker is available
        if not self.ensure_reference_tracker():
            return False
            
        try:
            # Get statistics about the references
            file_count = self.reference_tracker.get_parsed_file_count()
            
            messagebox.showinfo(
                "Reference Statistics",
                f"Analyzed {file_count} files.\n\n"
                f"Please select specific files to visualize their references."
            )
            
            return True
            
        except Exception as e:
            self.log(f"Error analyzing all references: {str(e)}")
            messagebox.showerror("Error", f"Could not analyze references: {str(e)}")
            return False