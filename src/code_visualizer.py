import os
import tkinter as tk
from tkinter import ttk, Text, messagebox
import re
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
import pygments

# For syntax highlighting
try:
    from pygments import lex
    from pygments.lexers import get_lexer_for_filename, PythonLexer, CSharpLexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

class CodeElement:
    """Represents a code element like a method, class, or variable"""
    def __init__(self, name: str, element_type: str, line_start: int, line_end: int, 
                 file_path: str, parent: Optional['CodeElement'] = None):
        self.name = name
        self.element_type = element_type  # 'class', 'method', 'variable', etc.
        self.line_start = line_start
        self.line_end = line_end
        self.file_path = file_path
        self.parent = parent
        self.children: List[CodeElement] = []
        self.references: List[CodeReference] = []
    
    def add_child(self, child: 'CodeElement'):
        self.children.append(child)
    
    def add_reference(self, reference: 'CodeReference'):
        self.references.append(reference)
    
    def __repr__(self):
        return f"{self.element_type}: {self.name} (lines {self.line_start}-{self.line_end})"

class CodeReference:
    """Represents a reference to a code element"""
    def __init__(self, source_element: CodeElement, target_element: CodeElement, 
                 reference_type: str, line_number: int, context: str):
        self.source_element = source_element
        self.target_element = target_element
        self.reference_type = reference_type  # 'call', 'inherit', 'import', etc.
        self.line_number = line_number
        self.context = context  # The line of code containing the reference
    
    def __repr__(self):
        return f"{self.reference_type} at line {self.line_number}: {self.context}"

class CodeRelationshipVisualizer(tk.Toplevel):
    """
    Window for visualizing code relationships between files, methods, classes, and variables.
    
    Features:
    - Split view with code editor on left, references on right
    - Syntax highlighting for code
    - Clickable code elements to show references
    - Visualization of connection lines between related code elements
    - Reference depth control
    - Snippets of referenced code
    """
    def __init__(self, parent, reference_tracker, file_path: str, theme="light"):
        super().__init__(parent)
        self.title("Code Relationship Visualizer")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.reference_tracker = reference_tracker
        self.file_path = file_path
        self.theme = theme
        self.current_element = None
        self.elements_by_line: Dict[int, CodeElement] = {}
        self.all_elements: List[CodeElement] = []
        self.max_depth = 2  # Default reference depth
        
        # Set theme colors
        self.set_theme(theme)
        
        # Create UI layout
        self.create_ui()
        
        # Load the initial file
        self.load_file(file_path)
        
        # Parse code elements from the file
        self.parse_code_elements()
        
        # Build initial connections
        self.build_connections()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
    def set_theme(self, theme):
        """Set color theme for the visualizer"""
        if theme == "dark":
            self.bg_color = "#282c34"
            self.text_color = "#abb2bf"
            self.highlight_color = "#61afef"
            self.connection_color = "#98c379"
            self.ref_bg_color = "#2c313a"
            self.ref_highlight_color = "#3b4048"
        else:  # light theme
            self.bg_color = "#ffffff"
            self.text_color = "#383a42"
            self.highlight_color = "#4078f2"
            self.connection_color = "#50a14f"
            self.ref_bg_color = "#f0f0f0"
            self.ref_highlight_color = "#d7d7d7"
    
    def create_ui(self):
        """Create the UI components"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # File path display
        ttk.Label(control_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_label = ttk.Label(control_frame, text=self.file_path)
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Depth control
        ttk.Label(control_frame, text="Reference Depth:").pack(side=tk.LEFT, padx=(10, 5))
        self.depth_var = tk.IntVar(value=self.max_depth)
        depth_spinner = ttk.Spinbox(control_frame, from_=1, to=5, textvariable=self.depth_var, width=5)
        depth_spinner.pack(side=tk.LEFT)
        depth_spinner.bind("<<Increment>>", self.update_depth)
        depth_spinner.bind("<<Decrement>>", self.update_depth)
        
        # Filter options
        ttk.Label(control_frame, text="Show:").pack(side=tk.LEFT, padx=(10, 5))
        self.show_methods = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Methods", variable=self.show_methods, 
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_classes = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Classes", variable=self.show_classes,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_variables = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Variables", variable=self.show_variables,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(control_frame, text="Refresh", command=self.refresh_view).pack(side=tk.RIGHT)
        
        # Split pane for main content
        self.paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Code view
        code_frame = ttk.Frame(self.paned)
        self.paned.add(code_frame, weight=3)
        
        # Code editor with line numbers
        code_panel = ttk.Frame(code_frame)
        code_panel.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers
        self.line_numbers = Text(code_panel, width=4, padx=3, pady=3, takefocus=0,
                               bg=self.ref_bg_color, fg=self.text_color,
                               border=0, highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Main code text widget
        self.code_text = Text(code_panel, padx=5, pady=5, wrap=tk.NONE,
                            bg=self.bg_color, fg=self.text_color,
                            insertbackground=self.text_color,
                            selectbackground=self.highlight_color,
                            selectforeground=self.bg_color,
                            font=("Consolas", 10))
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Code text scrollbars
        code_vsb = ttk.Scrollbar(code_panel, orient=tk.VERTICAL, command=self.scroll_both)
        code_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.config(yscrollcommand=code_vsb.set)
        
        code_hsb = ttk.Scrollbar(code_frame, orient=tk.HORIZONTAL, command=self.code_text.xview)
        code_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.code_text.config(xscrollcommand=code_hsb.set)
        
        # Bind events for code text
        self.code_text.bind("<Button-1>", self.handle_code_click)
        self.code_text.bind("<ButtonRelease-1>", self.check_selection)
        
        # Right panel - References view
        ref_frame = ttk.Frame(self.paned)
        self.paned.add(ref_frame, weight=2)
        
        # Element info panel
        self.element_info = ttk.LabelFrame(ref_frame, text="Selected Element")
        self.element_info.pack(fill=tk.X, padx=5, pady=5)
        
        self.element_name = ttk.Label(self.element_info, text="No element selected")
        self.element_name.pack(anchor=tk.W, padx=5, pady=5)
        
        self.element_type = ttk.Label(self.element_info, text="")
        self.element_type.pack(anchor=tk.W, padx=5)
        
        self.element_location = ttk.Label(self.element_info, text="")
        self.element_location.pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # References notebook
        self.ref_notebook = ttk.Notebook(ref_frame)
        self.ref_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Incoming references tab
        self.incoming_frame = ttk.Frame(self.ref_notebook)
        self.ref_notebook.add(self.incoming_frame, text="Referenced By")
        
        # Outgoing references tab
        self.outgoing_frame = ttk.Frame(self.ref_notebook)
        self.ref_notebook.add(self.outgoing_frame, text="References To")
        
        # Create reference treeviews
        self.create_reference_trees()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var.set("Ready")
        
    def create_reference_trees(self):
        """Create treeviews for references"""
        # Incoming references treeview
        incoming_scroll = ttk.Scrollbar(self.incoming_frame)
        incoming_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.incoming_tree = ttk.Treeview(self.incoming_frame, 
                                         yscrollcommand=incoming_scroll.set,
                                         columns=("file", "line", "type"))
        incoming_scroll.config(command=self.incoming_tree.yview)
        
        self.incoming_tree.column("#0", width=250)
        self.incoming_tree.column("file", width=150)
        self.incoming_tree.column("line", width=50)
        self.incoming_tree.column("type", width=80)
        
        self.incoming_tree.heading("#0", text="Element")
        self.incoming_tree.heading("file", text="File")
        self.incoming_tree.heading("line", text="Line")
        self.incoming_tree.heading("type", text="Type")
        
        self.incoming_tree.pack(fill=tk.BOTH, expand=True)
        self.incoming_tree.bind("<Double-1>", self.open_incoming_reference)
        
        # Outgoing references treeview
        outgoing_scroll = ttk.Scrollbar(self.outgoing_frame)
        outgoing_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.outgoing_tree = ttk.Treeview(self.outgoing_frame, 
                                         yscrollcommand=outgoing_scroll.set,
                                         columns=("file", "line", "type"))
        outgoing_scroll.config(command=self.outgoing_tree.yview)
        
        self.outgoing_tree.column("#0", width=250)
        self.outgoing_tree.column("file", width=150)
        self.outgoing_tree.column("line", width=50)
        self.outgoing_tree.column("type", width=80)
        
        self.outgoing_tree.heading("#0", text="Element")
        self.outgoing_tree.heading("file", text="File")
        self.outgoing_tree.heading("line", text="Line")
        self.outgoing_tree.heading("type", text="Type")
        
        self.outgoing_tree.pack(fill=tk.BOTH, expand=True)
        self.outgoing_tree.bind("<Double-1>", self.open_outgoing_reference)
        
    def scroll_both(self, *args):
        """Scroll both code and line number texts together"""
        self.code_text.yview(*args)
        self.line_numbers.yview(*args)
        
    def update_depth(self, event=None):
        """Update the reference depth"""
        self.max_depth = self.depth_var.get()
        if self.current_element:
            self.select_element(self.current_element)
        
    def refresh_view(self):
        """Refresh the current view"""
        # Re-parse code elements with current filters
        self.parse_code_elements()
        
        # Update connections
        self.build_connections()
        
        # Refresh highlighting
        self.highlight_code_elements()
        
        if self.current_element:
            self.select_element(self.current_element)
        
    def load_file(self, file_path):
        """Load a file into the editor"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Set file path display
            self.file_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            
            # Clear existing text
            self.code_text.delete(1.0, tk.END)
            self.line_numbers.delete(1.0, tk.END)
            
            # Insert content with syntax highlighting if available
            self.code_text.insert(tk.END, content)
            
            # Apply syntax highlighting
            if PYGMENTS_AVAILABLE:
                self.apply_syntax_highlighting(file_path)
            
            # Update line numbers
            self.update_line_numbers()
            
            self.status_var.set(f"Loaded: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def apply_syntax_highlighting(self, file_path):
        """Apply syntax highlighting to the code text"""
        self.code_text.tag_remove("all", 1.0, tk.END)
        
        try:
            # Get appropriate lexer for the file
            try:
                lexer = get_lexer_for_filename(file_path)
            except:
                # Default to Python if can't determine
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.cs':
                    lexer = CSharpLexer()
                else:
                    lexer = PythonLexer()
            
            # Get content and tokenize
            code = self.code_text.get(1.0, tk.END)
            tokens = lex(code, lexer)
            
            # Apply tags for each token type
            self.code_text.mark_set("range_start", 1.0)
            for token_type, value in tokens:
                if token_type in Token.Keyword:
                    self.code_text.tag_add("keyword", "range_start", f"range_start + {len(value)}c")
                    self.code_text.tag_config("keyword", foreground="#c678dd")
                elif token_type in Token.Name.Class:
                    self.code_text.tag_add("class", "range_start", f"range_start + {len(value)}c")
                    self.code_text.tag_config("class", foreground="#e5c07b")
                elif token_type in Token.Name.Function:
                    self.code_text.tag_add("function", "range_start", f"range_start + {len(value)}c")
                    self.code_text.tag_config("function", foreground="#61afef")
                elif token_type in Token.String:
                    self.code_text.tag_add("string", "range_start", f"range_start + {len(value)}c")
                    self.code_text.tag_config("string", foreground="#98c379")
                elif token_type in Token.Comment:
                    self.code_text.tag_add("comment", "range_start", f"range_start + {len(value)}c")
                    self.code_text.tag_config("comment", foreground="#5c6370")
                
                # Move the mark to the end of this token
                self.code_text.mark_set("range_start", f"range_start + {len(value)}c")
        except Exception as e:
            # If syntax highlighting fails, just show the plain text
            print(f"Syntax highlighting failed: {str(e)}")
    
    def update_line_numbers(self):
        """Update the line numbers in the editor"""
        self.line_numbers.delete(1.0, tk.END)
        line_count = self.code_text.get(1.0, tk.END).count('\n')
        for i in range(1, line_count + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")
    
    def parse_code_elements(self):
        """
        Parse code elements (classes, methods, variables) from the file.
        This is a simplified parser for demonstration - a real implementation would
        need language-specific parsing.
        """
        # Clear existing elements
        self.elements_by_line.clear()
        self.all_elements.clear()
        
        # Get file content
        content = self.code_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        # Detect the language
        ext = os.path.splitext(self.file_path)[1].lower()
        lang = 'cs' if ext == '.cs' else 'python'  # Simple detection
        
        # Choose patterns based on language
        if lang == 'cs':
            self.parse_csharp_elements(lines)
        else:
            self.parse_python_elements(lines)
            
        # Update UI
        self.highlight_code_elements()
        
    def parse_csharp_elements(self, lines):
        """Parse C# code elements"""
        # Patterns for C# code elements
        class_pattern = r'(?:public|private|protected|internal)?\s*(?:static|abstract)?\s*(?:partial)?\s*class\s+(\w+)'
        method_pattern = r'(?:public|private|protected|internal)?\s*(?:static|virtual|override|abstract)?\s*(?:async)?\s*(?:\w+)\s+(\w+)\s*\('
        var_pattern = r'(?:public|private|protected|internal)?\s*(?:\w+)\s+(\w+)(?:\s*=|;)'
        
        # Track open elements with a stack
        element_stack = []
        current_element = None
        
        for i, line in enumerate(lines):
            line_num = i + 1  # Line numbers are 1-based
            
            # Look for class declarations
            if self.show_classes.get():
                class_match = re.search(class_pattern, line)
                if class_match:
                    name = class_match.group(1)
                    element = CodeElement(name, 'class', line_num, None, self.file_path, 
                                        parent=current_element)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if current_element:
                        current_element.add_child(element)
                    
                    # Push to stack
                    element_stack.append((element, current_element))
                    current_element = element
            
            # Look for method declarations
            if self.show_methods.get():
                method_match = re.search(method_pattern, line)
                if method_match:
                    name = method_match.group(1)
                    element = CodeElement(name, 'method', line_num, None, self.file_path,
                                        parent=current_element)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if current_element:
                        current_element.add_child(element)
                    
                    # Push to stack
                    element_stack.append((element, current_element))
                    current_element = element
            
            # Look for variable declarations
            if self.show_variables.get():
                var_match = re.search(var_pattern, line)
                if var_match:
                    name = var_match.group(1)
                    element = CodeElement(name, 'variable', line_num, line_num, self.file_path,
                                        parent=current_element)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if current_element:
                        current_element.add_child(element)
            
            # Track scope end
            if '{' in line:
                # This might be the start of a scope
                pass
            
            if '}' in line:
                # This might be the end of a scope
                if element_stack:
                    element, prev_element = element_stack.pop()
                    element.line_end = line_num
                    current_element = prev_element
    
    def parse_python_elements(self, lines):
        """Parse Python code elements"""
        # Patterns for Python code elements
        class_pattern = r'^\s*class\s+(\w+)'
        method_pattern = r'^\s*def\s+(\w+)\s*\('
        var_pattern = r'^\s*(\w+)\s*='
        
        # Track indent levels
        indent_stack = [(0, None)]  # (indent_level, element)
        
        for i, line in enumerate(lines):
            line_num = i + 1  # Line numbers are 1-based
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Calculate indent level
            indent = len(line) - len(line.lstrip())
            
            # Pop elements from stack if indent decreases
            while indent_stack and indent < indent_stack[-1][0]:
                popped_indent, popped_element = indent_stack.pop()
                if popped_element:
                    popped_element.line_end = line_num - 1
            
            # Get current parent based on indent
            parent = None
            if indent_stack:
                parent_indent, parent = indent_stack[-1]
            
            # Look for class declarations
            if self.show_classes.get():
                class_match = re.search(class_pattern, line)
                if class_match:
                    name = class_match.group(1)
                    element = CodeElement(name, 'class', line_num, None, self.file_path, parent=parent)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if parent:
                        parent.add_child(element)
                    
                    # Push to stack
                    indent_stack.append((indent, element))
                    continue
            
            # Look for method declarations
            if self.show_methods.get():
                method_match = re.search(method_pattern, line)
                if method_match:
                    name = method_match.group(1)
                    element = CodeElement(name, 'method', line_num, None, self.file_path, parent=parent)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if parent:
                        parent.add_child(element)
                    
                    # Push to stack
                    indent_stack.append((indent, element))
                    continue
            
            # Look for variable declarations
            if self.show_variables.get():
                var_match = re.search(var_pattern, line)
                if var_match:
                    name = var_match.group(1)
                    element = CodeElement(name, 'variable', line_num, line_num, self.file_path, parent=parent)
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update hierarchy
                    if parent:
                        parent.add_child(element)
        
        # Close any remaining open elements
        line_count = len(lines)
        for indent, element in reversed(indent_stack):
            if element and not element.line_end:
                element.line_end = line_count
    
    def build_connections(self):
        """
        Build connections between code elements based on reference tracking.
        In a real implementation, this would use more sophisticated parsing.
        """
        if not self.reference_tracker:
            return
            
        # Process elements to find references
        for element in self.all_elements:
            # For each element, find references in the reference tracker
            
            # This is a simplified example - a real implementation would
            # need to integrate with the actual reference tracker's API
            
            # Example for methods:
            if element.element_type == 'method':
                # Find incoming references (who calls this method)
                # In a real implementation, this would use the reference tracker
                
                # Demonstration code - this should be replaced with actual reference lookup
                for other_element in self.all_elements:
                    if other_element.element_type == 'method' and other_element != element:
                        # Simulate some connections for demo purposes
                        if (hash(other_element.name) + hash(element.name)) % 3 == 0:
                            # Create a reference
                            ref = CodeReference(
                                source_element=other_element,
                                target_element=element,
                                reference_type='call',
                                line_number=other_element.line_start + 1,
                                context=f"{other_element.name} calls {element.name}()"
                            )
                            other_element.add_reference(ref)
    
    def highlight_code_elements(self):
        """Highlight code elements in the editor"""
        # Remove existing tags
        self.code_text.tag_remove("class", 1.0, tk.END)
        self.code_text.tag_remove("method", 1.0, tk.END)
        self.code_text.tag_remove("variable", 1.0, tk.END)
        
        # Configure tags
        self.code_text.tag_configure("class", foreground="#e5c07b", underline=True)
        self.code_text.tag_configure("method", foreground="#61afef", underline=True)
        self.code_text.tag_configure("variable", foreground="#98c379", underline=True)
        
        # Add tags for each element
        for element in self.all_elements:
            start_pos = f"{element.line_start}.0"
            line_content = self.code_text.get(start_pos, f"{element.line_start}.end")
            
            # Find the position of the element name in the line
            name_pos = line_content.find(element.name)
            if name_pos >= 0:
                start = f"{element.line_start}.{name_pos}"
                end = f"{element.line_start}.{name_pos + len(element.name)}"
                
                # Apply the appropriate tag
                self.code_text.tag_add(element.element_type, start, end)
    
    def handle_code_click(self, event=None):
        """Handle clicks in the code editor"""
        # Get the position of the click
        index = self.code_text.index(f"@{event.x},{event.y}")
        line = int(index.split('.')[0])
        
        # Check if this line has an element
        if line in self.elements_by_line:
            self.select_element(self.elements_by_line[line])
    
    def check_selection(self, event=None):
        """Check if text is selected and process it"""
        if self.code_text.tag_ranges(tk.SEL):
            selection = self.code_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selection:
                # Check if the selection matches any element name
                for element in self.all_elements:
                    if element.name == selection:
                        self.select_element(element)
                        break
    
    def select_element(self, element):
        """Select a code element and display its references"""
        self.current_element = element
        
        # Update element info
        self.element_name.config(text=element.name)
        self.element_type.config(text=f"Type: {element.element_type}")
        self.element_location.config(text=f"Location: Lines {element.line_start}-{element.line_end or '?'}")
        
        # Highlight the element in the code
        self.code_text.tag_remove("selected", 1.0, tk.END)
        self.code_text.tag_configure("selected", background=self.highlight_color, foreground="white")
        
        # Find and highlight the element name in its line
        start_pos = f"{element.line_start}.0"
        line_content = self.code_text.get(start_pos, f"{element.line_start}.end")
        name_pos = line_content.find(element.name)
        if name_pos >= 0:
            start = f"{element.line_start}.{name_pos}"
            end = f"{element.line_start}.{name_pos + len(element.name)}"
            self.code_text.tag_add("selected", start, end)
            
            # Ensure the element is visible
            self.code_text.see(start)
        
        # Build and display references
        self.build_reference_trees(element)
        
        self.status_var.set(f"Selected: {element.element_type} {element.name}")
    
    def build_reference_trees(self, element):
        """Build and display reference trees for the selected element"""
        # Clear existing trees
        self.incoming_tree.delete(*self.incoming_tree.get_children())
        self.outgoing_tree.delete(*self.outgoing_tree.get_children())
        
        # Find incoming references (who references this element)
        incoming_refs = []
        for other in self.all_elements:
            for ref in other.references:
                if ref.target_element == element:
                    incoming_refs.append((other, ref))
        
        # Add incoming references to the tree
        for source, ref in incoming_refs:
            self.incoming_tree.insert(
                "", "end", text=source.name, 
                values=(os.path.basename(source.file_path), ref.line_number, source.element_type)
            )
            
        # Add outgoing references to the tree
        for ref in element.references:
            target = ref.target_element
            self.outgoing_tree.insert(
                "", "end", text=target.name,
                values=(os.path.basename(target.file_path), ref.line_number, target.element_type)
            )
        
        # Update tab names with count
        self.ref_notebook.tab(0, text=f"Referenced By ({len(incoming_refs)})")
        self.ref_notebook.tab(1, text=f"References To ({len(element.references)})")
    
    def open_incoming_reference(self, event=None):
        """Open the selected incoming reference"""
        selected_id = self.incoming_tree.focus()
        if not selected_id:
            return
            
        # Get the values from the tree item
        item = self.incoming_tree.item(selected_id)
        element_name = item["text"]
        file_path_short = item["values"][0]
        line_number = item["values"][1]
        
        # Find the actual file path
        file_path = None
        for element in self.all_elements:
            if element.name == element_name and os.path.basename(element.file_path) == file_path_short:
                file_path = element.file_path
                break
        
        if not file_path:
            # This is a simplification - in a real implementation, we would need to find the actual file path
            messagebox.showinfo("Reference", f"Would open {element_name} in {file_path_short} at line {line_number}")
            return
            
        # If it's the same file, just navigate to the line
        if file_path == self.file_path:
            pos = f"{line_number}.0"
            self.code_text.see(pos)
            self.code_text.mark_set(tk.INSERT, pos)
            
            # Highlight the line
            self.code_text.tag_remove("highlight_line", 1.0, tk.END)
            self.code_text.tag_configure("highlight_line", background="#4040ff20")
            self.code_text.tag_add("highlight_line", f"{line_number}.0", f"{line_number}.end")
        else:
            # In a real implementation, we would load the other file
            # For this demo, we'll just show a message
            messagebox.showinfo("Reference", f"Would open {file_path} at line {line_number}")
    
    def open_outgoing_reference(self, event=None):
        """Open the selected outgoing reference"""
        selected_id = self.outgoing_tree.focus()
        if not selected_id:
            return
            
        # Get the values from the tree item
        item = self.outgoing_tree.item(selected_id)
        element_name = item["text"]
        file_path_short = item["values"][0]
        line_number = item["values"][1]
        
        # Find the actual file path
        file_path = None
        for element in self.all_elements:
            if element.name == element_name and os.path.basename(element.file_path) == file_path_short:
                file_path = element.file_path
                break
        
        if not file_path:
            # This is a simplification - in a real implementation, we would need to find the actual file path
            messagebox.showinfo("Reference", f"Would open {element_name} in {file_path_short} at line {line_number}")
            return
            
        # If it's the same file, just navigate to the line
        if file_path == self.file_path:
            pos = f"{line_number}.0"
            self.code_text.see(pos)
            self.code_text.mark_set(tk.INSERT, pos)
            
            # Highlight the line
            self.code_text.tag_remove("highlight_line", 1.0, tk.END)
            self.code_text.tag_configure("highlight_line", background="#4040ff20")
            self.code_text.tag_add("highlight_line", f"{line_number}.0", f"{line_number}.end")
        else:
            # In a real implementation, we would load the other file
            # For this demo, we'll just show a message
            messagebox.showinfo("Reference", f"Would open {file_path} at line {line_number}")

# Helper class to visualize code connections with snippets
class CodeSnippetVisualizer(tk.Toplevel):
    """
    Window for visualizing code snippets and connections between them.
    Shows snippets side by side with connecting lines.
    """
    def __init__(self, parent, source_element, references, theme="light"):
        super().__init__(parent)
        self.title("Code Snippet Connections")
        self.geometry("1000x800")
        self.minsize(800, 600)
        self.source_element = source_element
        self.references = references
        self.theme = theme
        self.canvas = None
        self.snippet_frames = []
        
        # Set theme colors
        self.set_theme(theme)
        
        # Create UI layout
        self.create_ui()
        
        # Add snippets and connections
        self.add_snippets()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
    def set_theme(self, theme):
        """Set color theme for the visualizer"""
        if theme == "dark":
            self.bg_color = "#282c34"
            self.text_color = "#abb2bf"
            self.highlight_color = "#61afef"
            self.connection_color = "#98c379"
            self.snippet_bg_color = "#2c313a"
        else:  # light theme
            self.bg_color = "#ffffff"
            self.text_color = "#383a42"
            self.highlight_color = "#4078f2"
            self.connection_color = "#50a14f"
            self.snippet_bg_color = "#f0f0f0"
    
    def create_ui(self):
        """Create the UI components"""
        # Main container with canvas for custom drawing
        self.canvas = tk.Canvas(self, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for canvas
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Create a frame inside the canvas for content
        self.content_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)
        
        # Configure canvas scrolling
        self.content_frame.bind("<Configure>", self.on_content_configure)
    
    def on_content_configure(self, event=None):
        """Update the canvas scrollregion when the content frame changes size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def add_snippets(self):
        """Add code snippets and connections to the canvas"""
        # Add source element snippet
        source_frame = self.create_snippet_frame(self.source_element)
        source_frame.grid(row=0, column=0, padx=10, pady=10)
        
        # Add reference snippets and connections
        for i, ref in enumerate(self.references):
            target = ref.target_element
            target_frame = self.create_snippet_frame(target)
            target_frame.grid(row=0, column=i+1, padx=10, pady=10)
            
            # Add connection line (will be drawn after the window is updated)
            self.after(100, lambda sf=source_frame, tf=target_frame: 
                      self.draw_connection(sf, tf))
    
    def create_snippet_frame(self, element):
        """Create a frame containing a code snippet"""
        frame = ttk.LabelFrame(self.content_frame, text=f"{element.element_type}: {element.name}")
        
        # Element info
        ttk.Label(frame, text=f"File: {os.path.basename(element.file_path)}").pack(anchor=tk.W, padx=5)
        ttk.Label(frame, text=f"Lines: {element.line_start}-{element.line_end or '?'}").pack(anchor=tk.W, padx=5)
        
        # Code snippet
        text = Text(frame, width=50, height=15, wrap=tk.NONE,
                  bg=self.snippet_bg_color, fg=self.text_color,
                  font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        text.config(xscrollcommand=hsb.set)
        
        # Insert code snippet
        try:
            with open(element.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Show a few lines before and after the element
            start = max(0, element.line_start - 3)
            end = min(len(lines), (element.line_end or element.line_start) + 3)
            
            for i in range(start, end):
                text.insert(tk.END, f"{i+1}: {lines[i]}")
            
            # Highlight the element lines
            text.tag_configure("highlight", background="#4040ff20")
            text.tag_add("highlight", 
                       f"{element.line_start - start + 1}.0", 
                       f"{(element.line_end or element.line_start) - start + 1}.end")
        except Exception as e:
            text.insert(tk.END, f"Error loading snippet: {str(e)}")
        
        # Add to snippet frames list
        self.snippet_frames.append(frame)
        
        return frame
    
    def draw_connection(self, source_frame, target_frame):
        """Draw a connection line between two snippet frames"""
        # Get coordinates in canvas space
        source_x = source_frame.winfo_x() + source_frame.winfo_width()
        source_y = source_frame.winfo_y() + source_frame.winfo_height() // 2
        
        target_x = target_frame.winfo_x()
        target_y = target_frame.winfo_y() + target_frame.winfo_height() // 2
        
        # Create connection line with arrow
        self.canvas.create_line(
            source_x, source_y, target_x, target_y,
            width=2, fill=self.connection_color,
            arrow=tk.LAST, arrowshape=(10, 12, 5),
            tags="connection"
        )
        
        # Add small circle at source point
        self.canvas.create_oval(
            source_x - 4, source_y - 4,
            source_x + 4, source_y + 4,
            fill=self.connection_color, outline=self.connection_color
        )

# Integration with the main application
def add_code_visualizer_to_app(app_class):
    """
    Integrate the code visualizer with the main application.
    This function modifies an existing app class to add code visualization functionality.
    """
    # Add method to open the visualizer
    def open_code_visualizer(self, file_path=None):
        """Open the code relationship visualizer for a file"""
        if not file_path:
            # Use the currently selected file if none is provided
            if hasattr(self, 'selected_files') and self.selected_files:
                file_path = self.selected_files[0]
            else:
                file_path = self.root_dir_var.get()
                if not os.path.isfile(file_path):
                    messagebox.showinfo("Information", "Please select a file to visualize.")
                    return
        
        # Get reference tracker
        if not hasattr(self, 'reference_tracker') or not self.reference_tracker:
            # Create reference tracker if it doesn't exist
            from reference_tracking import ReferenceTrackingManager
            root_dir = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
            self.reference_tracker = ReferenceTrackingManager(root_dir, self.log)
            self.reference_tracker.parse_directory()
        
        # Open the visualizer
        CodeRelationshipVisualizer(self.root, self.reference_tracker, file_path)
    
    # Add method to app class
    app_class.open_code_visualizer = open_code_visualizer
    
    # Add method to integrate with the UI
    def add_visualizer_menu_options(self):
        """Add code visualizer options to the menu"""
        # Find the menu bar
        if hasattr(self, 'root') and hasattr(self.root, 'winfo_children'):
            for child in self.root.winfo_children():
                if isinstance(child, tk.Menu):
                    # Found the menu bar, check if it already has a Visualize menu
                    visualize_menu = None
                    for i in range(child.index('end') + 1):
                        if child.entrycget(i, 'label') == 'Visualize':
                            visualize_menu = child.nametowidget(child.entrycget(i, 'menu'))
                            break
                    
                    if not visualize_menu:
                        # Create Visualize menu
                        visualize_menu = tk.Menu(child, tearoff=0)
                        child.add_cascade(label="Visualize", menu=visualize_menu)
                    
                    # Add options to visualize menu
                    visualize_menu.add_command(label="Code Relationships...", 
                                             command=self.open_code_visualizer)
                    visualize_menu.add_command(label="Visualize Selected File", 
                                             command=lambda: self.open_code_visualizer())
                    visualize_menu.add_separator()
                    visualize_menu.add_command(label="Reference Graph...", 
                                             command=self.show_reference_graph)
                    break
    
    # Add method to show reference graph
    def show_reference_graph(self):
        """Show a graph of file references"""
        # This would be implemented to show a high-level graph visualization
        messagebox.showinfo("Information", "Reference graph visualization coming soon!")
    
    # Add method to app class
    app_class.add_visualizer_menu_options = add_visualizer_menu_options
    app_class.show_reference_graph = show_reference_graph
    
    # Patch the app's __init__ method to add the visualizer menu
    original_init = app_class.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Add visualizer menu options
        self.add_visualizer_menu_options()
    
    # Replace the init method
    app_class.__init__ = patched_init

# Usage example:
# add_code_visualizer_to_app(FileTreeGeneratorApp)