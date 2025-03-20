import os

class CodeVisualizerIntegration:
    """
    Integration class for code visualization features in the main application.
    
    This class bridges the gap between the main application and the visualization
    components, ensuring proper initialization and event handling.
    """
    
    def __init__(self, app_instance):
        """
        Initialize the code visualizer integration.
        
        Args:
            app_instance: Reference to the main application
        """
        self.app = app_instance
        self.reference_tracker = None
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize visualization components"""
        # First check if we already have a reference tracker
        if hasattr(self.app, 'reference_tracker') and self.app.reference_tracker:
            self.reference_tracker = self.app.reference_tracker
        
        # Add methods to app instance for backward compatibility
        if not hasattr(self.app, 'visualize_method'):
            self.app.visualize_method = self.visualize_method
        
        if not hasattr(self.app, 'open_code_visualizer'):
            self.app.open_code_visualizer = self.open_code_visualizer
            
        if not hasattr(self.app, 'show_reference_graph'):
            self.app.show_reference_graph = self.show_reference_graph
            
        if not hasattr(self.app, 'visualize_all_references'):
            self.app.visualize_all_references = self.analyze_all_references
    
    def open_code_visualizer(self, file_path=None):
        """
        Open the code relationship visualizer for a file.
        
        Args:
            file_path: Path to the file to visualize. If None, uses the selected file.
        """
        # Delegate to VisualizationManager if available
        if hasattr(self.app, 'visualization_manager'):
            return self.app.visualization_manager.visualize_file(file_path)
        
        # Fall back to direct implementation
        from tkinter import filedialog, messagebox
        import os
        
        # Get file path if not provided
        if not file_path:
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                file_path = self.app.selected_files[0]
            else:
                file_path = filedialog.askopenfilename(
                    title="Select File to Visualize",
                    filetypes=[("C# Files", "*.cs"), ("XAML Files", "*.xaml;*.axaml"), ("All Files", "*.*")]
                )
        
        if not file_path or not os.path.isfile(file_path):
            self.app.log("No valid file selected for visualization")
            return False
        
        # Ensure reference tracker is initialized
        if not self._ensure_reference_tracker(os.path.dirname(file_path)):
            return False
        
        try:
            # Import the visualizer class
            from code_visualizer import CodeRelationshipVisualizer
            
            # Create and show the visualizer
            visualizer = CodeRelationshipVisualizer(
                self.app.root,
                self.reference_tracker,
                file_path
            )
            
            self.app.log(f"Opened code visualizer for {file_path}")
            return True
            
        except ImportError:
            messagebox.showinfo("Information",
                             "Code visualization module not available.")
            return False
        except Exception as e:
            self.app.log(f"Error opening visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open visualizer: {str(e)}")
            return False
    
    def visualize_method(self, file_path=None, method_name=None):
        """
        Visualize method relationships in a canvas-based view.
        
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method to visualize
        """
        # Delegate to VisualizationManager if available
        if hasattr(self.app, 'visualization_manager'):
            return self.app.visualization_manager.visualize_method(file_path, method_name)
        
        # Fall back to direct implementation
        from tkinter import filedialog, messagebox, simpledialog
        import os
        
        # Get file path if not provided
        if not file_path:
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                file_path = self.app.selected_files[0]
            else:
                file_path = filedialog.askopenfilename(
                    title="Select File for Method Visualization",
                    filetypes=[("C# Files", "*.cs"), ("All Files", "*.*")]
                )
        
        if not file_path or not os.path.isfile(file_path):
            self.app.log("No valid file selected for method visualization")
            return False
        
        # Ensure reference tracker is initialized
        if not self._ensure_reference_tracker(os.path.dirname(file_path)):
            return False
            
        # If method name not provided, prompt for selection
        if not method_name:
            # Get methods in the file
            methods = self.reference_tracker.get_methods_in_file(file_path)
            
            if not methods:
                messagebox.showinfo("Information", "No methods found in this file")
                return False
                
            # Simple prompt for method selection - in a real implementation,
            # we'd use a more sophisticated dialog with method details
            method_name = simpledialog.askstring(
                "Select Method",
                f"Enter method name to visualize from {os.path.basename(file_path)}",
                initialvalue=methods[0] if methods else ""
            )
            
            if not method_name:
                return False
        
        try:
            # Import the method visualizer
            try:
                from method_relationship_visualizer import MethodRelationshipVisualizer
                
                # Create and show the visualizer
                visualizer = MethodRelationshipVisualizer(
                    self.app.root,
                    self.reference_tracker,
                    file_path,
                    method_name
                )
                
                self.app.log(f"Opened method visualizer for {method_name} in {file_path}")
                return True
                
            except ImportError:
                # If method visualizer is not available, fall back to code visualizer
                from code_visualizer import CodeRelationshipVisualizer
                
                visualizer = CodeRelationshipVisualizer(
                    self.app.root,
                    self.reference_tracker,
                    file_path
                )
                
                messagebox.showinfo("Information",
                                 "Method visualization not available. Using file visualizer instead.")
                return True
                
        except Exception as e:
            self.app.log(f"Error opening method visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open method visualizer: {str(e)}")
            return False
    
    def show_reference_graph(self):
        """Show a graph visualization of file references"""
        # Delegate to VisualizationManager if available
        if hasattr(self.app, 'visualization_manager'):
            return self.app.visualization_manager.show_reference_graph()
        
        # Fall back to direct implementation
        from tkinter import messagebox, simpledialog
        
        # Check if we have a reference tracker
        if not self._ensure_reference_tracker():
            return False
            
        # Get selected files
        if hasattr(self.app, 'selected_files') and self.app.selected_files:
            files = self.app.selected_files
        else:
            messagebox.showinfo("Information",
                             "Please select files for the reference graph.")
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
            # Find related files
            self.app.log(f"Finding related files with depth {depth}...")
            related_files = self.reference_tracker.find_related_files(files, depth)
            
            # Show reference graph visualization - in a real implementation,
            # we'd have a more sophisticated graph visualization
            messagebox.showinfo(
                "Reference Graph",
                f"Found {len(related_files)} related files.\n\n" +
                "Full graph visualization will be implemented in a future update."
            )
            
            return True
            
        except Exception as e:
            self.app.log(f"Error showing reference graph: {str(e)}")
            messagebox.showerror("Error", f"Error: {str(e)}")
            return False
    
    def analyze_all_references(self):
        """Analyze all references in the project"""
        # Delegate to VisualizationManager if available
        if hasattr(self.app, 'visualization_manager'):
            return self.app.visualization_manager.visualize_all_references()
        
        # Fall back to direct implementation
        from tkinter import messagebox
        
        # Ensure reference tracker is initialized
        if not self._ensure_reference_tracker():
            return False
            
        try:
            # Show dialog with reference statistics
            if hasattr(self.reference_tracker, 'get_parsed_file_count'):
                file_count = self.reference_tracker.get_parsed_file_count()
                messagebox.showinfo(
                    "Reference Statistics",
                    f"Analyzed {file_count} files.\n\n" +
                    "Please select specific files to visualize their references."
                )
                return True
            else:
                messagebox.showinfo(
                    "Information",
                    "Reference analysis not available in this version."
                )
                return False
                
        except Exception as e:
            self.app.log(f"Error analyzing references: {str(e)}")
            messagebox.showerror("Error", f"Error: {str(e)}")
            return False
    
    def _ensure_reference_tracker(self, directory=None):
        """
        Ensure the reference tracker is initialized.
        
        Args:
            directory: Root directory to use
            
        Returns:
            True if reference tracker is available, False otherwise
        """
        # If we already have a reference tracker, use it
        if self.reference_tracker:
            return True
            
        # If app already has a reference tracker, use that
        if hasattr(self.app, 'reference_tracker') and self.app.reference_tracker:
            self.reference_tracker = self.app.reference_tracker
            return True
        
        # Otherwise, create a new one
        try:
            from tkinter import messagebox
            
            # Get directory
            if not directory:
                if hasattr(self.app, 'root_dir_var'):
                    directory = self.app.root_dir_var.get()
                elif hasattr(self.app, 'selected_files') and self.app.selected_files:
                    directory = os.path.dirname(self.app.selected_files[0])
            
            if not directory or not os.path.isdir(directory):
                messagebox.showerror("Error", "Please select a valid directory first")
                return False
            
            # Create reference tracker
            from reference_tracking import ReferenceTrackingManager
            self.app.log(f"Initializing reference tracker for {directory}...")
            self.reference_tracker = ReferenceTrackingManager(directory, self.app.log)
            self.reference_tracker.parse_directory()
            
            # Share with the main app
            self.app.reference_tracker = self.reference_tracker
                
            return True
            
        except Exception as e:
            self.app.log(f"Error initializing reference tracker: {str(e)}")
            messagebox.showerror("Error", f"Could not initialize reference tracker: {str(e)}")
            return False