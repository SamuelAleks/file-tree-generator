import tkinter as tk
from tkinter import ttk, messagebox

class MethodSelectorDialog(tk.Toplevel):
    """
    Dialog for selecting methods from a file for visualization.
    
    This dialog shows all methods in a file, grouped by class when possible,
    and allows for selection of a method to visualize.
    """
    
    def __init__(self, parent, file_path, reference_tracker, callback=None):
        """
        Initialize the method selector dialog.
        
        Args:
            parent: Parent window
            file_path: Path to the file containing methods
            reference_tracker: Reference tracking manager instance
            callback: Function to call with selected method
        """
        super().__init__(parent)
        self.title("Select Method to Visualize")
        self.geometry("600x500")
        self.minsize(500, 400)
        
        self.file_path = file_path
        self.reference_tracker = reference_tracker
        self.callback = callback
        self.selected_method = None
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Create UI
        self.create_ui()
        
        # Load methods
        self.load_methods()
    
    def create_ui(self):
        """Create the dialog UI"""
        # Main container with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File information
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="File:").grid(row=0, column=0, sticky=tk.W)
        self.file_label = ttk.Label(info_frame, text=self.file_path)
        self.file_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Method tree view
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with columns
        self.tree = ttk.Treeview(tree_frame, columns=("type", "line", "signature"))
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.tree.column("#0", width=200, minwidth=150)
        self.tree.column("type", width=80, minwidth=80)
        self.tree.column("line", width=50, minwidth=50)
        self.tree.column("signature", width=250, minwidth=200)
        
        self.tree.heading("#0", text="Method")
        self.tree.heading("type", text="Type")
        self.tree.heading("line", text="Line")
        self.tree.heading("signature", text="Signature")
        
        # Add filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=5)
        filter_entry.bind("<KeyRelease>", self.apply_filter)
        
        # Visibility filters
        self.show_public = tk.BooleanVar(value=True)
        self.show_private = tk.BooleanVar(value=True)
        self.show_protected = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(filter_frame, text="Public", variable=self.show_public, 
                       command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_frame, text="Private", variable=self.show_private,
                       command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(filter_frame, text="Protected", variable=self.show_protected,
                       command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Visualize", command=self.select).pack(side=tk.RIGHT)
        
        # Method details frame
        details_frame = ttk.LabelFrame(main_frame, text="Method Details", padding="5")
        details_frame.pack(fill=tk.X, pady=10)
        
        # Method details text
        self.details_text = tk.Text(details_frame, height=6, wrap=tk.WORD)
        self.details_text.pack(fill=tk.X)
        self.details_text.config(state=tk.DISABLED)
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)
    
    def load_methods(self):
        """Load methods from the file into the tree view"""
        if not self.reference_tracker:
            self.show_error("No reference tracker available")
            return
        
        # Get methods by class if possible
        try:
            methods_by_class = self.reference_tracker.tracker.get_methods_by_class(self.file_path)
            
            # If no class grouping available, get methods directly
            if not methods_by_class:
                methods = self.reference_tracker.get_methods_in_file(self.file_path)
                if methods:
                    methods_by_class = {'': methods}
                else:
                    methods_by_class = {}
            
            # Add methods to tree view grouped by class
            for class_name, methods in methods_by_class.items():
                # Create class node if it exists
                if class_name:
                    class_node = self.tree.insert("", "end", text=class_name, 
                                              values=("class", "", ""), open=True)
                else:
                    class_node = ""
                
                # Add methods under the class node
                for method in sorted(methods):
                    # Get method details
                    method_info = self.get_method_info(method)
                    
                    # Skip based on visibility filters
                    visibility = method_info.get('visibility', '')
                    if (visibility.startswith('public') and not self.show_public.get() or
                        visibility.startswith('private') and not self.show_private.get() or
                        visibility.startswith('protected') and not self.show_protected.get()):
                        continue
                    
                    # Add to tree
                    self.tree.insert(class_node, "end", text=method, 
                                  values=(visibility, method_info.get('line', ''),
                                         method_info.get('signature', '')))
            
            # If no methods found, show a message
            if not methods_by_class:
                self.show_message("No methods found in this file")
        
        except Exception as e:
            self.show_error(f"Error loading methods: {str(e)}")
    
    def get_method_info(self, method_name):
        """Get detailed information about a method"""
        try:
            # Get method details from reference tracker
            method_details = self.reference_tracker.get_method_details(self.file_path, method_name)
            
            if method_name in method_details:
                info = method_details[method_name]
                
                # Try to extract visibility from signature
                signature = info.get('signature', '')
                visibility = 'unknown'
                line = info.get('start_line', '')
                
                # Extract visibility from signature
                if 'public ' in signature:
                    visibility = 'public'
                elif 'private ' in signature:
                    visibility = 'private'
                elif 'protected ' in signature:
                    visibility = 'protected'
                elif 'internal ' in signature:
                    visibility = 'internal'
                
                return {
                    'name': method_name,
                    'visibility': visibility,
                    'line': line,
                    'signature': signature,
                    'content': info.get('content', ''),
                    'calls': info.get('calls', [])
                }
            
            # If not found in detailed info, return basic info
            return {
                'name': method_name,
                'visibility': 'unknown',
                'line': '',
                'signature': f"{method_name}(...)"
            }
            
        except Exception as e:
            print(f"Error getting method info: {str(e)}")
            return {'name': method_name}
    
    def update_method_details(self, method_name):
        """Update the method details display"""
        # Enable editing
        self.details_text.config(state=tk.NORMAL)
        
        # Clear existing content
        self.details_text.delete('1.0', tk.END)
        
        if not method_name:
            self.details_text.config(state=tk.DISABLED)
            return
        
        # Get method details
        method_info = self.get_method_info(method_name)
        
        # Display details
        if 'content' in method_info and method_info['content']:
            # Show a preview of the method content
            content = method_info['content']
            lines = content.split('\n')
            
            # Limit to first 10 lines with an ellipsis if longer
            if len(lines) > 10:
                preview = '\n'.join(lines[:10]) + '\n...'
            else:
                preview = content
            
            self.details_text.insert(tk.END, preview)
        else:
            self.details_text.insert(tk.END, f"Method: {method_name}\n")
            self.details_text.insert(tk.END, f"Signature: {method_info.get('signature', '')}\n")
            
            if 'calls' in method_info and method_info['calls']:
                self.details_text.insert(tk.END, "\nCalls:\n")
                for call in method_info['calls'][:5]:  # Show first 5 calls
                    if isinstance(call, tuple):
                        obj, method = call
                        self.details_text.insert(tk.END, f"- {obj}.{method}()\n")
                    else:
                        self.details_text.insert(tk.END, f"- {call}\n")
                        
                if len(method_info['calls']) > 5:
                    self.details_text.insert(tk.END, f"... {len(method_info['calls']) - 5} more\n")
        
        # Disable editing
        self.details_text.config(state=tk.DISABLED)
    
    def on_tree_select(self, event=None):
        """Handle selection in the tree view"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get selected item
        item = self.tree.item(selection[0])
        item_type = item['values'][0] if item['values'] else ''
        
        # Only update details for methods, not classes
        if item_type != 'class':
            method_name = item['text']
            self.selected_method = method_name
            self.update_method_details(method_name)
        else:
            self.selected_method = None
            self.update_method_details(None)
    
    def on_double_click(self, event=None):
        """Handle double-click on a tree item"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get selected item
        item = self.tree.item(selection[0])
        item_type = item['values'][0] if item['values'] else ''
        
        # Only select methods, not classes
        if item_type != 'class':
            self.selected_method = item['text']
            self.select()
    
    def apply_filter(self, event=None):
        """Apply filter to the tree view"""
        filter_text = self.filter_var.get().lower()
        
        # Reload methods with the current filter
        self.tree.delete(*self.tree.get_children())
        
        # Get methods by class if possible
        try:
            methods_by_class = self.reference_tracker.tracker.get_methods_by_class(self.file_path)
            
            # If no class grouping available, get methods directly
            if not methods_by_class:
                methods = self.reference_tracker.get_methods_in_file(self.file_path)
                if methods:
                    methods_by_class = {'': methods}
                else:
                    methods_by_class = {}
            
            # Add methods to tree view grouped by class
            for class_name, methods in methods_by_class.items():
                # Filter methods based on text
                filtered_methods = [m for m in methods if filter_text in m.lower()]
                
                # Skip empty classes
                if not filtered_methods:
                    continue
                
                # Create class node if it exists
                if class_name:
                    class_node = self.tree.insert("", "end", text=class_name, 
                                              values=("class", "", ""), open=True)
                else:
                    class_node = ""
                
                # Add methods under the class node
                for method in sorted(filtered_methods):
                    # Get method details
                    method_info = self.get_method_info(method)
                    
                    # Skip based on visibility filters
                    visibility = method_info.get('visibility', '')
                    if (visibility.startswith('public') and not self.show_public.get() or
                        visibility.startswith('private') and not self.show_private.get() or
                        visibility.startswith('protected') and not self.show_protected.get()):
                        continue
                    
                    # Add to tree
                    self.tree.insert(class_node, "end", text=method, 
                                  values=(visibility, method_info.get('line', ''),
                                         method_info.get('signature', '')))
            
        except Exception as e:
            self.show_error(f"Error applying filter: {str(e)}")
    
    def select(self):
        """Select a method and close the dialog"""
        if not self.selected_method:
            self.show_message("Please select a method to visualize")
            return
        
        # Call the callback function with the selected method
        if self.callback:
            self.callback(self.selected_method)
        
        # Close the dialog
        self.destroy()
    
    def cancel(self):
        """Cancel the selection and close the dialog"""
        self.selected_method = None
        
        # Call the callback with None to indicate cancellation
        if self.callback:
            self.callback(None)
        
        # Close the dialog
        self.destroy()
    
    def show_message(self, message):
        """Show an information message"""
        messagebox.showinfo("Information", message, parent=self)
    
    def show_error(self, message):
        """Show an error message"""
        messagebox.showerror("Error", message, parent=self)
    
    def get_selected_method(self):
        """Get the selected method name"""
        return self.selected_method