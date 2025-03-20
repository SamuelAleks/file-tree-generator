import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importlib.util
from typing import Dict, List, Optional, Any, Callable

class VisualizationManager:
    """
    Central manager for code visualization functionality.
    
    This class provides a unified interface for all visualization components,
    creating a coherent flow from file selection to method visualization.
    """
    
    def __init__(self, app_instance):
        """
        Initialize the visualization manager.
        
        Args:
            app_instance: Reference to the main application
        """
        self.app = app_instance
        self.reference_tracker = None
        self.current_file = None
        self.current_element = None
        self.visualizer_windows = {}  # Track open visualizer windows
        
        # Initialize available visualizers
        self._load_visualizers()
        
        # Add integration with app's menus
        self._integrate_with_app_menu()
    
    def _load_visualizers(self):
        """Dynamically load visualizer classes based on what's available"""
        # Dictionary to hold visualizer classes
        self.visualizers = {}
    
        # Try to import from code_visualizer module
        try:
            # First check if the module exists
            if importlib.util.find_spec("code_visualizer"):
                from code_visualizer import (
                    CodeRelationshipVisualizer,
                    CodeSnippetVisualizer,
                    CSharpCodeViewer
                )
            
                self.visualizers.update({
                    "relationship": CodeRelationshipVisualizer,
                    "snippet": CodeSnippetVisualizer,
                    "csharp": CSharpCodeViewer,
                })
            
                # Try to import method visualizer from its own module first
                try:
                    if importlib.util.find_spec("method_relationship_visualizer"):
                        from method_relationship_visualizer import MethodRelationshipVisualizer
                        self.visualizers["method"] = MethodRelationshipVisualizer
                        self.log("Loaded MethodRelationshipVisualizer from method_relationship_visualizer module")
                    else:
                        # Fall back to importing from code_visualizer
                        try:
                            from code_visualizer import MethodRelationshipVisualizer
                            self.visualizers["method"] = MethodRelationshipVisualizer
                            self.log("Loaded MethodRelationshipVisualizer from code_visualizer module")
                        except (ImportError, AttributeError):
                            self.log("MethodRelationshipVisualizer not found in any module")
                except (ImportError, AttributeError):
                    self.log("Could not load MethodRelationshipVisualizer module")
            
                self.log("Loaded visualizer components successfully")
            else:
                self.log("Warning: code_visualizer module not available")
        except Exception as e:
            self.log(f"Error loading visualizers: {str(e)}")
    
    def _integrate_with_app_menu(self):
        """Add visualization options to the application menu"""
        # Skip if app doesn't have a menu
        if not hasattr(self.app, 'menubar'):
            return
        
        # Find or create Visualize menu
        visualize_menu = None
    
        # First check if it already exists
        try:
            for i in range(self.app.menubar.index('end') + 1):
                if self.app.menubar.entrycget(i, 'label') == 'Visualize':
                    menu_name = self.app.menubar.entrycget(i, 'menu')
                    visualize_menu = self.app.nametowidget(menu_name)
                    break
        except (tk.TclError, AttributeError):
            # Handle case where menubar is empty or doesn't support these operations
            pass
    
        # Create it if not found
        if not visualize_menu:
            visualize_menu = tk.Menu(self.app.menubar, tearoff=0)
            self.app.menubar.add_cascade(label="Visualize", menu=visualize_menu)
    
        # Clear existing items if any
        try:
            visualize_menu.delete(0, 'end')
        except (tk.TclError, AttributeError):
            # Handle case where menu can't be cleared
            pass
    
        # Add visualization options
        visualize_menu.add_command(
            label="Visualize Selected File",
            command=lambda: self.visualize_file()
        )
    
        visualize_menu.add_command(
            label="Method Relationships...",
            command=lambda: self.visualize_method()
        )
    
        visualize_menu.add_separator()
    
        visualize_menu.add_command(
            label="Reference Graph...",
            command=lambda: self.show_reference_graph()
        )
    
        visualize_menu.add_command(
            label="All References...",
            command=lambda: self.visualize_all_references()
        )
    
        # Add a help entry
        visualize_menu.add_separator()
        visualize_menu.add_command(
            label="About Visualization...",
            command=self.show_visualization_help
        )
    
    def log(self, message):
        """Log a message using the app's logging function if available"""
        if hasattr(self.app, 'log'):
            self.app.log(message)
        else:
            print(f"VisualizationManager: {message}")
    
    def ensure_reference_tracker(self, directory=None):
        """
        Ensure the reference tracker is initialized.
        
        Args:
            directory: Root directory to use (defaults to app's current directory)
            
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
            self.log(f"Initializing reference tracker for {directory}...")
            self.reference_tracker = ReferenceTrackingManager(directory, self.log)
            self.reference_tracker.parse_directory()
            
            # Share with the main app
            if hasattr(self.app, 'reference_tracker'):
                self.app.reference_tracker = self.reference_tracker
                
            return True
            
        except Exception as e:
            self.log(f"Error initializing reference tracker: {str(e)}")
            messagebox.showerror("Error", f"Could not initialize reference tracker: {str(e)}")
            return False
    
    def visualize_file(self, file_path=None):
        """
        Visualize a file's relationships.
        
        Args:
            file_path: Path to the file to visualize. If None, prompts user or uses selected file.
            
        Returns:
            True if successful, False otherwise
        """
        # Get file path if not provided
        if not file_path:
            # First check if there's a selected file in the app
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
        
        # Determine which visualizer to use based on file type
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            self.log(f"Opening visualizer for {file_path}")
            
            # Store current file
            self.current_file = file_path
            self.current_element = None
            
            # Check if we have a dedicated visualizer for this file type
            if ext == '.cs' and 'csharp' in self.visualizers:
                # Use C# specific visualizer
                visualizer = self.visualizers["csharp"](
                    self.app.root,
                    self.reference_tracker,
                    file_path
                )
                return True
                
            elif ext in ('.xaml', '.axaml') and 'csharp' in self.visualizers:
                # Use C# visualizer for XAML (it can handle XAML relationships)
                visualizer = self.visualizers["csharp"](
                    self.app.root,
                    self.reference_tracker,
                    file_path
                )
                return True
                
            elif 'relationship' in self.visualizers:
                # Use generic relationship visualizer
                visualizer = self.visualizers["relationship"](
                    self.app.root,
                    self.reference_tracker,
                    file_path
                )
                return True
                
            else:
                messagebox.showinfo("Information", 
                                   "No suitable visualizer available for this file type.")
                return False
                
        except Exception as e:
            self.log(f"Error opening file visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open visualizer: {str(e)}")
            return False
    
    def visualize_method(self, file_path=None, method_name=None):
        """
        Visualize a method's relationships.
        
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method to visualize
            
        Returns:
            True if successful, False otherwise
        """
        # Get file path if not provided
        if not file_path:
            # Check if we have a current file
            if self.current_file and os.path.isfile(self.current_file):
                file_path = self.current_file
            elif hasattr(self.app, 'selected_files') and self.app.selected_files:
                # Use the first selected file
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
        
        # Ensure we have a reference tracker
        if not self.ensure_reference_tracker(os.path.dirname(file_path)):
            return False
            
        # If method name not provided, let user select one
        if not method_name:
            methods = self.reference_tracker.get_methods_in_file(file_path)
            
            if not methods:
                messagebox.showinfo("Information", "No methods found in this file")
                return False
                
            # Create a method selection dialog
            method_name = self.prompt_for_method_selection(file_path, methods)
            
            if not method_name:
                return False
        
        # Store current state
        self.current_file = file_path
        self.current_element = method_name
        
        try:
            self.log(f"Opening method visualizer for {method_name} in {file_path}")
            
            # Check if we have the method visualizer
            if 'method' in self.visualizers:
                # Use dedicated method visualizer
                visualizer = self.visualizers["method"](
                    self.app.root,
                    self.reference_tracker,
                    file_path,
                    method_name
                )
                
                # Store the window reference
                window_id = f"method:{file_path}:{method_name}"
                self.visualizer_windows[window_id] = visualizer
                
                # When window closes, remove it from our tracking
                visualizer.protocol("WM_DELETE_WINDOW", 
                                   lambda: self.on_visualizer_closed(window_id))
                
                return True
                
            elif 'relationship' in self.visualizers:
                # Fall back to regular relationship visualizer
                visualizer = self.visualizers["relationship"](
                    self.app.root,
                    self.reference_tracker,
                    file_path
                )
                
                messagebox.showinfo("Information", 
                                  "Method-specific visualizer not available. "
                                  "Using file relationship visualizer instead.")
                return True
                
            else:
                messagebox.showinfo("Information", "No suitable visualizer available.")
                return False
                
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
            True if successful, False otherwise
        """
        # Get files if not provided
        if not start_files:
            if hasattr(self.app, 'selected_files') and self.app.selected_files:
                start_files = self.app.selected_files
            else:
                # Let user select files
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
        
        if not start_files:
            messagebox.showinfo("Information", "No files selected for reference graph")
            return False
            
        # Ensure reference tracker is available
        if not self.ensure_reference_tracker():
            return False
            
        # Get reference depth
        from tkinter import simpledialog
        depth = simpledialog.askinteger(
            "Reference Depth",
            "Enter maximum reference depth (1-5):",
            minvalue=1, maxvalue=5, initialvalue=2
        )
        
        if not depth:
            return False
            
        try:
            self.log(f"Generating reference graph for {len(start_files)} files with depth {depth}")
            
            # Find related files
            related_files = self.reference_tracker.find_related_files(start_files, depth)
            
            # Show reference visualization
            if 'relationship' in self.visualizers:
                # For now, just show the first file's relationship view
                # A more complete solution would show a graph of all files
                visualizer = self.visualizers["relationship"](
                    self.app.root,
                    self.reference_tracker,
                    start_files[0]
                )
                
                # Also show a summary dialog
                self.show_reference_summary(related_files)
                
                return True
            else:
                # Just show the summary dialog
                self.show_reference_summary(related_files)
                return True
                
        except Exception as e:
            self.log(f"Error showing reference graph: {str(e)}")
            messagebox.showerror("Error", f"Could not show reference graph: {str(e)}")
            return False
    
    def visualize_all_references(self):
        """
        Visualize all references in the project.
        
        Returns:
            True if successful, False otherwise
        """
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
            self.log(f"Error visualizing all references: {str(e)}")
            messagebox.showerror("Error", f"Could not visualize references: {str(e)}")
            return False
    
    def prompt_for_method_selection(self, file_path, methods):
        """
        Show a dialog to select a method from the file.
    
        Args:
            file_path: Path to the file
            methods: List of method names
        
        Returns:
            Selected method name or None if cancelled
        """
        try:
            # Use the enhanced method selector dialog
            from MethodSelectorDialog import MethodSelectorDialog
        
            # Store result for returning after dialog closes
            result = [None]
        
            # Callback function to receive the selected method
            def on_method_selected(method_name):
                result[0] = method_name
        
            # Create and show dialog
            dialog = MethodSelectorDialog(
                self.app.root,
                file_path,
                self.reference_tracker,
                callback=on_method_selected
            )
        
            # Wait for dialog to close
            self.app.root.wait_window(dialog)
        
            return result[0]
        
        except ImportError:
            # Fall back to simple selection if dialog is not available
            from tkinter import simpledialog
        
            return simpledialog.askstring(
                "Select Method",
                f"Enter method name to visualize from {os.path.basename(file_path)}:",
                parent=self.app.root
            )
    
    def show_reference_summary(self, related_files):
        """
        Show a summary of the reference analysis.
        
        Args:
            related_files: Set of related file paths
        """
        if not related_files:
            messagebox.showinfo("Information", "No related files found")
            return
            
        # Generate summary text
        summary = self.reference_tracker.generate_reference_summary(related_files)
        
        # Create summary dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Reference Analysis Summary")
        dialog.geometry("600x400")
        dialog.transient(self.app.root)
        
        # Add text area with scrollbar
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
        
        # Insert summary text
        text.insert('1.0', summary)
        text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_visualization_help(self):
        """Show help information about the visualization features"""
        help_text = """
        Code Visualization Features
        ==========================
    
        This application includes several tools to help you understand your code structure:
    
        1. File Relationship Visualizer
           - Shows how files connect through references
           - Displays file content with syntax highlighting
           - Navigate between related files
    
        2. Method Relationship Visualizer
           - Visualize method connections in an interactive canvas
           - See which methods call your method and which ones it calls
           - Drag methods to rearrange the view
           - Double-click methods to see their contents
    
        3. Reference Graph
           - Analyze which files connect to your selected files
           - Control the depth of reference tracking
           - Get statistics on the most referenced files
    
        How to use:
        - Select a file or files to analyze
        - Choose the appropriate visualization from the Visualize menu
        - Drag nodes to rearrange the view
        - Double-click on items to see more details
    
        The visualizer uses static analysis to find connections between code elements
        and does not require running the code.
        """
    
        # Create help dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Visualization Help")
        dialog.geometry("600x500")
        dialog.transient(self.app.root)
    
        # Add text area with scrollbar
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        text = tk.Text(frame, wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
    
        # Insert help text
        text.insert('1.0', help_text)
        text.config(state=tk.DISABLED)
    
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def on_visualizer_closed(self, window_id):
        """
        Handle a visualizer window being closed.
        
        Args:
            window_id: ID of the window that was closed
        """
        if window_id in self.visualizer_windows:
            # Destroy the window
            self.visualizer_windows[window_id].destroy()
            # Remove from tracking
            del self.visualizer_windows[window_id]