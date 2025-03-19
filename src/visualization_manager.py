import os
import tkinter as tk
from tkinter import filedialog, messagebox
import importlib.util

class VisualizationManager:
    """
    Central manager for code visualization functionality.
    Provides a unified interface to all visualizers.
    """
    
    def __init__(self, app_instance, reference_tracker=None):
        """
        Initialize the visualization manager.
        
        Args:
            app_instance: Reference to the main application
            reference_tracker: Optional reference tracker instance
        """
        self.app = app_instance
        self.reference_tracker = reference_tracker
        self.current_file = None
        self.current_element = None
        
        # Initialize visualizer classes
        self._load_visualizers()
    
    def _load_visualizers(self):
        """Load visualizer classes dynamically"""
        # Import code_visualizer module
        if importlib.util.find_spec("code_visualizer"):
            from code_visualizer import (
                CodeRelationshipVisualizer,
                CSharpCodeViewer,
                CodeSnippetVisualizer
            )
            
            self.visualizers = {
                "relationship": CodeRelationshipVisualizer,
                "csharp": CSharpCodeViewer,
                "snippet": CodeSnippetVisualizer
            }
            
            # Try to import method visualizer if it exists
            try:
                from code_visualizer import MethodRelationshipVisualizer
                self.visualizers["method"] = MethodRelationshipVisualizer
            except ImportError:
                pass
        else:
            self.visualizers = {}
            if hasattr(self.app, 'log'):
                self.app.log("Warning: code_visualizer module not found")
    
    def ensure_reference_tracker(self, directory=None):
        """Ensure reference tracker is initialized"""
        if not self.reference_tracker:
            if not directory:
                if hasattr(self.app, 'root_dir_var'):
                    directory = self.app.root_dir_var.get()
            
            if not directory:
                return False
                
            # Initialize reference tracker
            if importlib.util.find_spec("reference_tracking"):
                from reference_tracking import ReferenceTrackingManager
                
                log_callback = getattr(self.app, 'log', None)
                self.reference_tracker = ReferenceTrackingManager(directory, log_callback)
                self.reference_tracker.parse_directory()
                return True
            else:
                if hasattr(self.app, 'log'):
                    self.app.log("Warning: reference_tracking module not found")
                return False
        
        return True
    
    def visualize_file(self, file_path=None):
        """
        Entry point for file visualization.
        
        Args:
            file_path: Path to the file to visualize. If None, will prompt user.
            
        Returns:
            True if visualization opened, False otherwise
        """
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select File to Visualize",
                filetypes=[
                    ("C# Files", "*.cs"),
                    ("XAML Files", "*.xaml;*.axaml"),
                    ("All Files", "*.*")
                ]
            )
        
        if not file_path:
            return False
            
        # Ensure reference tracker is initialized
        if not self.ensure_reference_tracker(os.path.dirname(file_path)):
            messagebox.showerror("Error", "Could not initialize reference tracker")
            return False
            
        # Determine which visualizer to use based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.cs' or ext in ['.xaml', '.axaml']:
                # Use C# visualizer
                if "csharp" in self.visualizers:
                    visualizer = self.visualizers["csharp"](
                        self.app.root, 
                        self.reference_tracker, 
                        file_path
                    )
                    return True
            
            # Use generic relationship visualizer for other files
            if "relationship" in self.visualizers:
                visualizer = self.visualizers["relationship"](
                    self.app.root, 
                    self.reference_tracker, 
                    file_path
                )
                return True
                
            return False
        except Exception as e:
            if hasattr(self.app, 'log'):
                self.app.log(f"Error opening visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open visualizer: {str(e)}")
            return False
    
    def visualize_method(self, file_path=None, method_name=None):
        """
        Visualize a specific method.
        
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method to visualize
            
        Returns:
            True if visualization opened, False otherwise
        """
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select File for Method Visualization",
                filetypes=[("C# Files", "*.cs"), ("All Files", "*.*")]
            )
        
        if not file_path:
            return False
            
        # Ensure reference tracker is initialized
        if not self.ensure_reference_tracker(os.path.dirname(file_path)):
            messagebox.showerror("Error", "Could not initialize reference tracker")
            return False
        
        if not method_name:
            # Get methods in file
            methods = self.reference_tracker.get_methods_in_file(file_path)
            
            if not methods:
                messagebox.showinfo("Information", "No methods found in this file")
                return False
                
            # Create a simple dialog to select a method
            dialog = tk.Toplevel(self.app.root)
            dialog.title("Select Method")
            dialog.transient(self.app.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Select a method to visualize:").pack(pady=(10, 5))
            
            method_var = tk.StringVar()
            method_combo = ttk.Combobox(dialog, textvariable=method_var, width=40)
            method_combo['values'] = methods
            method_combo.current(0)
            method_combo.pack(padx=10, pady=5)
            
            result = [None]  # Use list for a non-local reference
            
            def on_select():
                result[0] = method_var.get()
                dialog.destroy()
                
            def on_cancel():
                dialog.destroy()
                
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
            
            # Center dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            self.app.root.wait_window(dialog)
            
            method_name = result[0]
            if not method_name:
                return False
        
        # Open method visualizer
        try:
            if "method" in self.visualizers:
                visualizer = self.visualizers["method"](
                    self.app.root, 
                    self.reference_tracker, 
                    file_path,
                    method_name
                )
                return True
            else:
                messagebox.showinfo("Information", "Method visualizer not available")
                return False
        except Exception as e:
            if hasattr(self.app, 'log'):
                self.app.log(f"Error opening method visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open method visualizer: {str(e)}")
            return False
    
    def show_reference_graph(self, start_files=None):
        """
        Show a reference graph for the given files.
        
        Args:
            start_files: List of files to start from. If None, will prompt user.
            
        Returns:
            True if graph shown, False otherwise
        """
        if not self.ensure_reference_tracker():
            messagebox.showerror("Error", "Could not initialize reference tracker")
            return False
        
        if not start_files:
            # Use app's selected files if available
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                start_files = self.app.selected_files
            else:
                messagebox.showinfo("Information", "Please select files for the reference graph")
                return False
        
        from tkinter import simpledialog
        depth = simpledialog.askinteger(
            "Reference Depth", 
            "Enter maximum reference depth (1-5):",
            minvalue=1, maxvalue=5, initialvalue=2
        )
        
        if not depth:
            return False
        
        try:
            # Find related files
            related_files = self.reference_tracker.find_related_files(start_files, depth)
            
            # Show summary dialog
            self._show_reference_summary(related_files, start_files)
            return True
        except Exception as e:
            if hasattr(self.app, 'log'):
                self.app.log(f"Error showing reference graph: {str(e)}")
            messagebox.showerror("Error", f"Could not show reference graph: {str(e)}")
            return False
    
    def _show_reference_summary(self, related_files, source_files):
        """Show a dialog with reference summary information"""
        # Create a simple summary dialog
        # (You can implement this similar to the existing summary dialogs)
        pass