import os
import tkinter as tk
from tkinter import ttk, Text, messagebox, simpledialog, Frame
import re
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
import threading
import time


# Import everything needed in one place
from method_relationship_visualizer import MethodRelationshipVisualizer

# For syntax highlighting
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, PythonLexer, CSharpLexer
    from pygments.formatters import get_formatter_by_name
    from pygments.token import Token
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class SynchronizedTextEditor(ttk.Frame):
    """
    A text editor widget with synchronized line numbers and proper scrolling.
    
    This class handles the synchronization of line numbers and main text content,
    ensuring they remain aligned during scrolling, editing, and resizing.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        
        # Store parameters
        self.line_numbers_enabled = kwargs.pop('line_numbers', True)
        self.syntax_highlighting_enabled = kwargs.pop('syntax_highlighting', True)
        self.style_name = kwargs.pop('style', 'default')
        
        # Get colors from kwargs or use defaults
        self.bg_color = kwargs.pop('bg_color', '#ffffff')
        self.fg_color = kwargs.pop('fg_color', '#000000')
        self.line_number_bg = kwargs.pop('line_number_bg', '#f0f0f0')
        self.line_number_fg = kwargs.pop('line_number_fg', '#606060')
        self.highlight_color = kwargs.pop('highlight_color', '#cce8ff')
        self.selected_bg = kwargs.pop('selected_bg', '#3399ff')
        self.selected_fg = kwargs.pop('selected_fg', '#ffffff')
        
        # Create the main text area
        self.text_frame = ttk.Frame(self)
        self.text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Line numbers (if enabled)
        if self.line_numbers_enabled:
            self.line_numbers = Text(self.text_frame, width=6, bg=self.line_number_bg, fg=self.line_number_fg,
                                    padx=3, pady=3, bd=0, highlightthickness=0, 
                                    state='disabled', wrap='none')
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            
            # Create separator between line numbers and main text
            ttk.Separator(self.text_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y)
        
        # Main text widget
        self.text = Text(self.text_frame, wrap='none', bg=self.bg_color, fg=self.fg_color,
                        insertbackground=self.fg_color, selectbackground=self.selected_bg,
                        selectforeground=self.selected_fg, padx=5, pady=5,
                        undo=True, maxundo=100, font=("Consolas", 10))
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add vertical scrollbar
        self.yscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        self.xscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure text widget scrolling
        self.text.config(xscrollcommand=self.on_text_xscroll,
                        yscrollcommand=self.on_text_yscroll)
        
        # Configure scrollbar commands
        self.yscrollbar.config(command=self.on_y_scrollbar_scroll)
        self.xscrollbar.config(command=self.on_x_scrollbar_scroll)
        
        # Initialize tag configuration for syntax highlighting
        if self.syntax_highlighting_enabled:
            self.initialize_tags()
        
        # Bind events
        self.text.bind('<<Modified>>', self.on_text_modified)
        self.text.bind('<Configure>', self.on_text_configure)
        
        # Initialize line count
        self._line_count = 1
        
        # Create a flag to avoid infinite loops in handlers
        self._updating = False
        
        # Initialize syntax highlighting variables
        self.current_file_path = None
        self.lexer = None
        
        # Element highlighting tags
        self.text.tag_configure("class", foreground="#e5c07b", underline=True)
        self.text.tag_configure("method", foreground="#61afef", underline=True)
        self.text.tag_configure("variable", foreground="#98c379", underline=True)
        self.text.tag_configure("property", foreground="#56b6c2", underline=True)
        self.text.tag_configure("namespace", foreground="#c678dd", underline=True)
        self.text.tag_configure("selected", background="#61afef", foreground="white")
        self.text.tag_configure("current_line", background="#2c323c")
        
        # Search highlight tag
        self.text.tag_configure("search_highlight", background="#ffff00", foreground="#000000")
    
    def initialize_tags(self):
        """Initialize tags for syntax highlighting with proper font handling"""
        # Create font objects for regular and italic text
        import tkinter.font as tkFont
    
        # Get the current font properties
        current_font = tkFont.Font(font=self.text['font'])
        font_family = current_font.actual('family')
        font_size = current_font.actual('size')
    
        # Create italic font
        italic_font = tkFont.Font(family=font_family, size=font_size, slant="italic")
    
        # Configure tags with appropriate fonts
        # Common token types - using fonts for italic instead of direct italic property
        self.text.tag_configure("keyword", foreground="#c678dd")
        self.text.tag_configure("string", foreground="#98c379")
        self.text.tag_configure("comment", foreground="#5c6370", font=italic_font)  # Use italic font
        self.text.tag_configure("number", foreground="#d19a66")
        self.text.tag_configure("operator", foreground="#56b6c2")
        self.text.tag_configure("class_name", foreground="#e5c07b")
        self.text.tag_configure("function_name", foreground="#61afef")
        self.text.tag_configure("namespace", foreground="#c678dd")
        self.text.tag_configure("type", foreground="#e5c07b")
        self.text.tag_configure("attribute", foreground="#d19a66")
        self.text.tag_configure("docstring", foreground="#98c379", font=italic_font)  # Use italic font
    
    def on_text_modified(self, event=None):
        """Handle text modifications and update line numbers"""
        if self._updating:
            return
            
        self._updating = True
        
        # Reset modified flag
        self.text.edit_modified(False)
        
        # Get current line count
        new_line_count = int(self.text.index('end-1c').split('.')[0])
        
        # Update line numbers if they changed
        if new_line_count != self._line_count:
            self._line_count = new_line_count
            self.update_line_numbers()
        
        # Apply syntax highlighting if enabled and the lexer is set
        if self.syntax_highlighting_enabled and self.lexer:
            self.apply_syntax_highlighting()
        
        self._updating = False
    
    def on_text_configure(self, event=None):
        """Handle text widget resize"""
        if self._updating:
            return
            
        self._updating = True
        
        # Update line numbers when text widget is resized
        if self.line_numbers_enabled:
            self.update_line_numbers()
        
        self._updating = False
    
    def on_text_yscroll(self, *args):
        """Handle y-scrolling of the text widget"""
        if self._updating:
            return
            
        self._updating = True
        
        # Update scrollbar position
        self.yscrollbar.set(*args)
        
        # Synchronize line numbers with text
        if self.line_numbers_enabled:
            self.line_numbers.yview_moveto(args[0])
        
        self._updating = False
        
        return args
    
    def on_text_xscroll(self, *args):
        """Handle x-scrolling of the text widget"""
        if self._updating:
            return
            
        self._updating = True
        
        # Update scrollbar position
        self.xscrollbar.set(*args)
        
        self._updating = False
        
        return args
    
    def on_y_scrollbar_scroll(self, *args):
        """Handle y-scrollbar movement"""
        if self._updating:
            return
            
        self._updating = True
        
        # Scroll main text
        self.text.yview(*args)
        
        # Synchronize line numbers with text
        if self.line_numbers_enabled:
            self.line_numbers.yview(*args)
        
        self._updating = False
    
    def on_x_scrollbar_scroll(self, *args):
        """Handle x-scrollbar movement"""
        if self._updating:
            return
            
        self._updating = True
        
        # Scroll main text
        self.text.xview(*args)
        
        self._updating = False
    
    def update_line_numbers(self):
        """Update line numbers in the line number widget"""
        if not self.line_numbers_enabled:
            return
            
        # Enable editing of line numbers
        self.line_numbers.config(state='normal')
        
        # Clear existing line numbers
        self.line_numbers.delete('1.0', 'end')
        
        # Add line numbers
        for i in range(1, self._line_count + 1):
            self.line_numbers.insert('end', f"{i:4d}\n")
        
        # Disable editing of line numbers
        self.line_numbers.config(state='disabled')
        
        # Ensure line numbers are scrolled to match main text
        self.line_numbers.yview_moveto(self.text.yview()[0])
    
    def set_lexer(self, file_path=None, language=None):
        """Set syntax highlighting lexer based on file path or explicit language"""
        if not PYGMENTS_AVAILABLE or not self.syntax_highlighting_enabled:
            return
        
        try:
            if language:
                if language.lower() == 'python':
                    self.lexer = PythonLexer()
                elif language.lower() in ['csharp', 'c#', 'cs']:
                    self.lexer = CSharpLexer()
                else:
                    # Try to get lexer by name
                    try:
                        from pygments.lexers import get_lexer_by_name
                        self.lexer = get_lexer_by_name(language.lower())
                    except:
                        self.lexer = None
            elif file_path:
                try:
                    self.lexer = get_lexer_for_filename(file_path)
                    self.current_file_path = file_path
                except:
                    # Default to Python for unknown files
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext == '.cs':
                        self.lexer = CSharpLexer()
                    else:
                        self.lexer = PythonLexer()
            else:
                self.lexer = None
        except Exception as e:
            print(f"Error setting lexer: {str(e)}")
            self.lexer = None
    
    def apply_syntax_highlighting(self):
        """Apply syntax highlighting to the text"""
        if not PYGMENTS_AVAILABLE or not self.syntax_highlighting_enabled or not self.lexer:
            return
        
        try:
            # Get current content
            content = self.text.get('1.0', 'end-1c')  # Exclude the final newline
            
            # Remember cursor position and selection
            cursor_pos = self.text.index(tk.INSERT)
            try:
                selection_start = self.text.index(tk.SEL_FIRST)
                selection_end = self.text.index(tk.SEL_LAST)
                has_selection = True
            except tk.TclError:
                has_selection = False
            
            # Store the current view position
            yview = self.text.yview()
            
            # Remove existing syntax highlighting tags
            for tag in ["keyword", "string", "comment", "number", "operator", 
                      "class_name", "function_name", "namespace", "type", 
                      "attribute", "docstring"]:
                self.text.tag_remove(tag, '1.0', 'end')
            
            # Use Pygments to tokenize the content
            tokens = self.lexer.get_tokens(content)
            
            # Apply tags for each token
            start_index = "1.0"
            for token_type, token_value in tokens:
                if not token_value:  # Skip empty tokens
                    continue
                
                # Calculate end index based on token value
                end_index = self.text.index(f"{start_index}+{len(token_value)}c")
                
                # Map Pygments token types to our configured tags
                if token_type in Token.Keyword:
                    self.text.tag_add("keyword", start_index, end_index)
                elif token_type in Token.Literal.String:
                    self.text.tag_add("string", start_index, end_index)
                elif token_type in Token.Comment:
                    self.text.tag_add("comment", start_index, end_index)
                elif token_type in Token.Literal.Number:
                    self.text.tag_add("number", start_index, end_index)
                elif token_type in Token.Operator:
                    self.text.tag_add("operator", start_index, end_index)
                elif token_type in Token.Name.Class:
                    self.text.tag_add("class_name", start_index, end_index)
                elif token_type in Token.Name.Function:
                    self.text.tag_add("function_name", start_index, end_index)
                elif token_type in Token.Name.Namespace:
                    self.text.tag_add("namespace", start_index, end_index)
                elif token_type in Token.Name.Builtin:
                    self.text.tag_add("type", start_index, end_index)
                elif token_type in Token.Name.Attribute:
                    self.text.tag_add("attribute", start_index, end_index)
                elif token_type in Token.Literal.String.Doc:
                    self.text.tag_add("docstring", start_index, end_index)
                
                # Move start position for next token
                start_index = end_index
            
            # Restore cursor and selection
            self.text.mark_set(tk.INSERT, cursor_pos)
            if has_selection:
                self.text.tag_add(tk.SEL, selection_start, selection_end)
            
            # Restore view position
            self.text.yview_moveto(yview[0])
        
        except Exception as e:
            print(f"Error applying syntax highlighting: {str(e)}")
    
    def set_content(self, content, file_path=None, language=None):
        """Set content of the text editor with optional syntax highlighting"""
        # Set the lexer first
        self.set_lexer(file_path, language)
        
        # Clear existing content
        self.text.delete('1.0', 'end')
        
        # Insert new content
        if content:
            self.text.insert('1.0', content)
        
        # Update line numbers
        self._line_count = int(self.text.index('end-1c').split('.')[0])
        self.update_line_numbers()
        
        # Apply syntax highlighting if enabled and lexer is set
        if self.syntax_highlighting_enabled and self.lexer:
            self.apply_syntax_highlighting()
    
    def get_content(self):
        """Get current content of the text editor"""
        return self.text.get('1.0', 'end-1c')
    
    def highlight_element(self, element_type, line_start, column_start, length):
        """Highlight an element in the text based on its type and position"""
        try:
            # Calculate positions
            start_pos = f"{line_start}.{column_start}"
            end_pos = f"{line_start}.{column_start + length}"
            
            # Apply appropriate tag based on element type
            if element_type.lower() in ["class", "method", "variable", "property", "namespace"]:
                self.text.tag_add(element_type.lower(), start_pos, end_pos)
        except Exception as e:
            print(f"Error highlighting element: {str(e)}")
    
    def highlight_line(self, line_number):
        """Highlight a specific line"""
        try:
            # Remove previous line highlight
            self.text.tag_remove("current_line", "1.0", "end")
            
            # Add highlight to the specified line
            self.text.tag_add("current_line", f"{line_number}.0", f"{line_number + 1}.0")
            
            # Ensure the line is visible
            self.text.see(f"{line_number}.0")
        except Exception as e:
            print(f"Error highlighting line: {str(e)}")
    
    def search_text(self, search_string, case_sensitive=False, whole_word=False, regex=False, 
                   highlight_all=True):
        """
        Search for text in the editor and highlight matches
        
        Args:
            search_string: Text to search for
            case_sensitive: Whether search is case sensitive
            whole_word: Whether to match whole words only
            regex: Whether search_string is a regular expression
            highlight_all: Whether to highlight all matches
            
        Returns:
            List of match positions (line, column)
        """
        # Clear previous highlights
        self.text.tag_remove("search_highlight", "1.0", "end")
        
        if not search_string:
            return []
            
        content = self.text.get("1.0", "end-1c")
        
        matches = []
        if regex:
            try:
                pattern = re.compile(search_string, 0 if case_sensitive else re.IGNORECASE)
                for match in pattern.finditer(content):
                    start, end = match.span()
                    start_line, start_col = self._get_line_col(content, start)
                    end_line, end_col = self._get_line_col(content, end)
                    matches.append((start_line, start_col, end_line, end_col))
            except re.error:
                # Invalid regex
                pass
        else:
            # Prepare search string for whole word matching
            if whole_word:
                search_pattern = r'\b' + re.escape(search_string) + r'\b'
                pattern = re.compile(search_pattern, 0 if case_sensitive else re.IGNORECASE)
                for match in pattern.finditer(content):
                    start, end = match.span()
                    start_line, start_col = self._get_line_col(content, start)
                    end_line, end_col = self._get_line_col(content, end)
                    matches.append((start_line, start_col, end_line, end_col))
            else:
                # Simple string search
                search_func = str.find if case_sensitive else lambda s, sub: s.lower().find(sub.lower())
                search_content = content
                search_term = search_string
                
                if not case_sensitive:
                    search_content = search_content.lower()
                    search_term = search_term.lower()
                
                pos = 0
                while pos < len(search_content):
                    match_pos = search_content.find(search_term, pos)
                    if match_pos == -1:
                        break
                        
                    start_line, start_col = self._get_line_col(content, match_pos)
                    end_line, end_col = self._get_line_col(content, match_pos + len(search_string))
                    matches.append((start_line, start_col, end_line, end_col))
                    
                    pos = match_pos + len(search_term)
        
        # Highlight matches
        if highlight_all and matches:
            for start_line, start_col, end_line, end_col in matches:
                start_index = f"{start_line + 1}.{start_col}"
                end_index = f"{end_line + 1}.{end_col}"
                self.text.tag_add("search_highlight", start_index, end_index)
        
        # Return match positions (converted to 1-based for consistency with the UI)
        return [(start_line + 1, start_col) for start_line, start_col, _, _ in matches]
    
    def _get_line_col(self, text, pos):
        """Convert a character position to line and column numbers (0-based)"""
        line_start = 0
        for i, char in enumerate(text[:pos]):
            if char == '\n':
                line_start = i + 1
        
        line = text[:pos].count('\n')
        col = pos - line_start
        return line, col
    
    def goto_position(self, line, column=0):
        """Move cursor to the specified position and ensure it's visible"""
        position = f"{line}.{column}"
        self.text.mark_set(tk.INSERT, position)
        self.text.see(position)
        
        # Update UI to reflect the new position
        self.highlight_line(line)
        self.text.focus_set()
    
    def goto_search_match(self, match_index, matches):
        """Go to a specific search match"""
        if matches and 0 <= match_index < len(matches):
            line, col = matches[match_index]
            self.goto_position(line, col)
    
    def clear_highlights(self):
        """Clear all element highlights"""
        for tag in ["class", "method", "variable", "property", "namespace", "selected", "current_line"]:
            self.text.tag_remove(tag, "1.0", "end")
    
    def bind_event(self, event, callback):
        """Bind an event to the text widget"""
        self.text.bind(event, callback)
    pass


class CodeElement:
    """Represents a code element like a method, class, property, or variable"""
    def __init__(self, name: str, element_type: str, line_start: int, line_end: int, 
                 file_path: str, parent: Optional['CodeElement'] = None, 
                 visibility: str = "", modifiers: List[str] = None,
                 parameters: List[str] = None, return_type: str = "",
                 namespace: str = "", column_start: int = 0, length: int = 0):
        self.name = name
        self.element_type = element_type  # 'class', 'method', 'variable', 'property', etc.
        self.line_start = line_start
        self.line_end = line_end
        self.file_path = file_path
        self.parent = parent
        self.children: List[CodeElement] = []
        self.references: List[CodeReference] = []
        
        # Additional information specific to C# elements
        self.visibility = visibility  # public, private, protected, internal
        self.modifiers = modifiers or []  # static, virtual, abstract, async, etc.
        self.parameters = parameters or []  # For methods
        self.return_type = return_type  # For methods and properties
        self.namespace = namespace  # Fully qualified namespace
        
        # For highlighting in the editor
        self.column_start = column_start  # Column where the element name starts
        self.length = length or len(name)  # Length of the element name
    
    def add_child(self, child: 'CodeElement'):
        """Add a child element"""
        self.children.append(child)
    
    def add_reference(self, reference: 'CodeReference'):
        """Add a reference to this element"""
        self.references.append(reference)
    
    def get_fully_qualified_name(self):
        """Get the fully qualified name of this element"""
        if not self.namespace:
            return self.name
            
        return f"{self.namespace}.{self.name}"
    
    def get_signature(self):
        """Get the signature of this element (for methods and properties)"""
        if self.element_type == 'method':
            params_str = ", ".join(self.parameters)
            return f"{self.visibility} {' '.join(self.modifiers)} {self.return_type} {self.name}({params_str})"
        elif self.element_type == 'property':
            return f"{self.visibility} {' '.join(self.modifiers)} {self.return_type} {self.name} {{ get; set; }}"
        else:
            return self.name
    
    def __repr__(self):
        return f"{self.element_type}: {self.name} (lines {self.line_start}-{self.line_end})"
    pass


class CodeReference:
    """Represents a reference between code elements"""
    def __init__(self, source_element: CodeElement, target_element: CodeElement, 
                 reference_type: str, line_number: int, context: str,
                 column: int = 0):
        self.source_element = source_element
        self.target_element = target_element
        self.reference_type = reference_type  # 'call', 'inherit', 'implement', 'use', etc.
        self.line_number = line_number
        self.column = column  # Column where the reference occurs
        self.context = context  # The line of code containing the reference
    
    def __repr__(self):
        return f"{self.reference_type} at line {self.line_number}: {self.context}"
    pass


class CodeRelationshipVisualizer(tk.Toplevel):
    """
    Window for visualizing code relationships between files, methods, classes, and variables.
    
    Features:
    - Split view with improved code editor on left, references on right
    - Enhanced syntax highlighting for C# code
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
        
        # Search bar
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<Return>", self.search_code)
        
        # Search options
        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Case Sensitive", 
                       variable=self.case_sensitive_var).pack(side=tk.LEFT)
        
        self.whole_word_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Whole Word", 
                       variable=self.whole_word_var).pack(side=tk.LEFT)
        
        self.regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Regex", 
                       variable=self.regex_var).pack(side=tk.LEFT)
        
        # Search buttons
        ttk.Button(control_frame, text="Find", command=self.search_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Next", command=self.find_next).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Previous", command=self.find_previous).pack(side=tk.LEFT, padx=5)
        
        # Depth control
        ttk.Label(control_frame, text="Reference Depth:").pack(side=tk.LEFT, padx=(10, 5))
        self.depth_var = tk.IntVar(value=self.max_depth)
        depth_spinner = ttk.Spinbox(control_frame, from_=1, to=5, textvariable=self.depth_var, width=5)
        depth_spinner.pack(side=tk.LEFT)
        depth_spinner.bind("<<Increment>>", self.update_depth)
        depth_spinner.bind("<<Decrement>>", self.update_depth)
        
        # Filter options frame in the second row
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, side=tk.TOP, padx=5, pady=2)
        
        ttk.Label(filter_frame, text="Show:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Element type filters
        self.show_namespaces = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Namespaces", variable=self.show_namespaces, 
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_classes = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Classes", variable=self.show_classes,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_methods = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Methods", variable=self.show_methods, 
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_properties = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Properties", variable=self.show_properties,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_variables = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Variables", variable=self.show_variables,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        # Visibility filters
        ttk.Separator(filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(filter_frame, text="Visibility:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.show_public = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Public", variable=self.show_public,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_private = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Private", variable=self.show_private,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_protected = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Protected", variable=self.show_protected,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        self.show_internal = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Internal", variable=self.show_internal,
                       command=self.refresh_view).pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_view).pack(side=tk.RIGHT)
        
        # Split pane for main content
        self.paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Code view
        code_frame = ttk.Frame(self.paned)
        self.paned.add(code_frame, weight=3)
        
        # Create improved code editor
        self.code_editor = SynchronizedTextEditor(
            code_frame,
            bg_color=self.bg_color,
            fg_color=self.text_color,
            line_number_bg=self.ref_bg_color,
            line_number_fg=self.text_color,
            highlight_color=self.highlight_color,
            selected_bg=self.highlight_color,
            selected_fg="white"
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Bind events for code editor
        self.code_editor.bind_event("<Button-1>", self.handle_code_click)
        self.code_editor.bind_event("<ButtonRelease-1>", self.check_selection)
        
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
        
        # Methods tab
        self.methods_frame = ttk.Frame(self.ref_notebook)
        self.ref_notebook.add(self.methods_frame, text="Methods")
        
        # Properties tab
        self.properties_frame = ttk.Frame(self.ref_notebook)
        self.ref_notebook.add(self.properties_frame, text="Properties")
        
        # Create reference treeviews
        self.create_reference_trees()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var.set("Ready")
        
        # Initialize search variables
        self.search_matches = []
        self.current_match = -1
        
    def create_reference_trees(self):
        """Create treeviews for references and code elements"""
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
        
        # Methods treeview
        methods_scroll = ttk.Scrollbar(self.methods_frame)
        methods_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.methods_tree = ttk.Treeview(self.methods_frame, 
                                        yscrollcommand=methods_scroll.set,
                                        columns=("visibility", "line", "signature"))
        methods_scroll.config(command=self.methods_tree.yview)
        
        self.methods_tree.column("#0", width=200)
        self.methods_tree.column("visibility", width=80)
        self.methods_tree.column("line", width=50)
        self.methods_tree.column("signature", width=300)
        
        self.methods_tree.heading("#0", text="Method")
        self.methods_tree.heading("visibility", text="Visibility")
        self.methods_tree.heading("line", text="Line")
        self.methods_tree.heading("signature", text="Signature")
        
        self.methods_tree.pack(fill=tk.BOTH, expand=True)
        self.methods_tree.bind("<Double-1>", self.navigate_to_method)
        
        # Properties treeview
        properties_scroll = ttk.Scrollbar(self.properties_frame)
        properties_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.properties_tree = ttk.Treeview(self.properties_frame, 
                                          yscrollcommand=properties_scroll.set,
                                          columns=("visibility", "type", "line"))
        properties_scroll.config(command=self.properties_tree.yview)
        
        self.properties_tree.column("#0", width=200)
        self.properties_tree.column("visibility", width=80)
        self.properties_tree.column("type", width=100)
        self.properties_tree.column("line", width=50)
        
        self.properties_tree.heading("#0", text="Property")
        self.properties_tree.heading("visibility", text="Visibility")
        self.properties_tree.heading("type", text="Type")
        self.properties_tree.heading("line", text="Line")
        
        self.properties_tree.pack(fill=tk.BOTH, expand=True)
        self.properties_tree.bind("<Double-1>", self.navigate_to_property)
    
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
        
        # Highlight updated elements
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
            
            # Set content in the editor
            self.code_editor.set_content(content, file_path)
            
            self.status_var.set(f"Loaded: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def parse_code_elements(self):
        """
        Parse code elements (namespaces, classes, methods, properties, variables) from the file.
        Enhanced for C# with better pattern matching.
        """
        # Clear existing elements
        self.elements_by_line.clear()
        self.all_elements.clear()
        
        # Get file content
        content = self.code_editor.get_content()
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
        """
        Parse C# code elements with enhanced pattern matching for modern C# features.
        
        Recognizes:
        - Namespaces
        - Classes (including generic classes)
        - Interfaces
        - Methods (including async methods, generic methods)
        - Properties (including auto-properties)
        - Fields/Variables
        """
        # Enhanced regex patterns for C# code elements
        patterns = {
            # Namespace declarations
            'namespace': re.compile(r'^\s*(?:(?:public|internal)\s+)?namespace\s+([^\s{;]+)', re.MULTILINE),
            
            # Using directives (for reference tracking)
            'using': re.compile(r'^\s*using(?:\s+static)?\s+([^;]+);', re.MULTILINE),
            
            # Class declarations (with enhanced support for generic types and modifiers)
            'class': re.compile(r'^\s*(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected)\s+)?(?:(?:abstract|sealed|static|partial)\s+)*class\s+(\w+)(?:<[^>]+>)?(?:\s*:\s*[^{]+)?', re.MULTILINE),
            
            # Interface declarations
            'interface': re.compile(r'^\s*(?:(?:public|private|protected|internal)\s+)?interface\s+(\w+)(?:<[^>]+>)?(?:\s*:\s*[^{]+)?', re.MULTILINE),
            
            # Method declarations with enhanced support for modifiers, generics, and return types
            'method': re.compile(r'^\s*(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected)\s+)?(?:(?:abstract|virtual|override|sealed|static|async|new|extern|partial)\s+)*(?:(?:\w+(?:<[^>]+>)?)|(?:void))\s+(\w+)(?:<[^>]+>)?\s*\([^)]*\)', re.MULTILINE),
            
            # Property declarations
            'property': re.compile(r'^\s*(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected)\s+)?(?:(?:virtual|override|abstract|new|static)\s+)*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:\{(?:\s*get\s*(?:=>|{)|\s*set\s*(?:=>|{)|\s*init\s*(?:=>|{)|\s*;)[^}]*\})', re.MULTILINE),
            
            # Field/Variable declarations
            'variable': re.compile(r'^\s*(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected)\s+)?(?:(?:readonly|const|static|volatile)\s+)*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=|;)', re.MULTILINE),
            
            # Auto-property declarations
            'auto_property': re.compile(r'^\s*(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected)\s+)?(?:(?:virtual|override|abstract|new|static)\s+)*(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\{\s*get;\s*(?:private\s+)?set;\s*\}', re.MULTILINE),
        }
        
        # Extract visibility regex to be reused
        visibility_pattern = re.compile(r'(public|private|protected|internal|protected\s+internal|private\s+protected)')
        
        # Track the current namespace
        current_namespace = ""
        
        # Track open elements with a stack
        element_stack = []
        current_element = None
        
        # Process line by line with context tracking
        for i, line in enumerate(lines):
            line_num = i + 1  # Line numbers are 1-based
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('//'):
                continue
            
            # Check for namespace
            if self.show_namespaces.get():
                namespace_match = patterns['namespace'].search(line)
                if namespace_match:
                    name = namespace_match.group(1)
                    current_namespace = name
                    
                    # Find the column where the name starts
                    col_start = line.find(name)
                    
                    # Create namespace element
                    element = CodeElement(
                        name=name,
                        element_type='namespace',
                        line_start=line_num,
                        line_end=None,
                        file_path=self.file_path,
                        parent=None,
                        namespace=current_namespace,
                        column_start=col_start,
                        length=len(name)
                    )
                    
                    self.all_elements.append(element)
                    self.elements_by_line[line_num] = element
                    
                    # Update element stack
                    element_stack.append((element, current_element))
                    current_element = element
                    continue
            
            # Check for class declarations
            if self.show_classes.get():
                # Check for class
                class_match = patterns['class'].search(line)
                if class_match:
                    # Get class name
                    name = class_match.group(1)
                    
                    # Get visibility (if present)
                    visibility_match = visibility_pattern.search(line)
                    visibility = visibility_match.group(1) if visibility_match else "internal"  # Default visibility in C#
                    
                    # Check if visibility should be included based on filters
                    should_include = False
                    if visibility == "public" and self.show_public.get():
                        should_include = True
                    elif visibility == "private" and self.show_private.get():
                        should_include = True
                    elif visibility == "protected" and self.show_protected.get():
                        should_include = True
                    elif visibility == "internal" and self.show_internal.get():
                        should_include = True
                    
                    if should_include:
                        # Find modifiers
                        modifiers = []
                        if "static" in line:
                            modifiers.append("static")
                        if "abstract" in line:
                            modifiers.append("abstract")
                        if "sealed" in line:
                            modifiers.append("sealed")
                        if "partial" in line:
                            modifiers.append("partial")
                        
                        # Find the column where the name starts
                        col_start = line.find(name)
                        
                        # Create element
                        element = CodeElement(
                            name=name,
                            element_type='class',
                            line_start=line_num,
                            line_end=None,
                            file_path=self.file_path,
                            parent=current_element,
                            visibility=visibility,
                            modifiers=modifiers,
                            namespace=current_namespace,
                            column_start=col_start,
                            length=len(name)
                        )
                        
                        self.all_elements.append(element)
                        self.elements_by_line[line_num] = element
                        
                        # Update hierarchy
                        if current_element:
                            current_element.add_child(element)
                        
                        # Push to stack
                        element_stack.append((element, current_element))
                        current_element = element
                        continue
                
                # Check for interface
                interface_match = patterns['interface'].search(line)
                if interface_match:
                    # Process similar to class
                    name = interface_match.group(1)
                    
                    # Get visibility
                    visibility_match = visibility_pattern.search(line)
                    visibility = visibility_match.group(1) if visibility_match else "internal"
                    
                    # Check visibility filter
                    should_include = False
                    if visibility == "public" and self.show_public.get():
                        should_include = True
                    elif visibility == "private" and self.show_private.get():
                        should_include = True
                    elif visibility == "protected" and self.show_protected.get():
                        should_include = True
                    elif visibility == "internal" and self.show_internal.get():
                        should_include = True
                    
                    if should_include:
                        # Find the column where the name starts
                        col_start = line.find(name)
                        
                        # Create element
                        element = CodeElement(
                            name=name,
                            element_type='interface',
                            line_start=line_num,
                            line_end=None,
                            file_path=self.file_path,
                            parent=current_element,
                            visibility=visibility,
                            namespace=current_namespace,
                            column_start=col_start,
                            length=len(name)
                        )
                        
                        self.all_elements.append(element)
                        self.elements_by_line[line_num] = element
                        
                        # Update hierarchy
                        if current_element:
                            current_element.add_child(element)
                        
                        # Push to stack
                        element_stack.append((element, current_element))
                        current_element = element
                        continue
            
            # Check for method declarations
            if self.show_methods.get():
                method_match = patterns['method'].search(line)
                if method_match:
                    name = method_match.group(1)
                    
                    # Extract method details
                    visibility_match = visibility_pattern.search(line)
                    visibility = visibility_match.group(1) if visibility_match else ""
                    
                    # Check visibility filter
                    should_include = False
                    if not visibility or visibility == "public" and self.show_public.get():
                        should_include = True
                    elif visibility == "private" and self.show_private.get():
                        should_include = True
                    elif visibility == "protected" and self.show_protected.get():
                        should_include = True
                    elif visibility == "internal" and self.show_internal.get():
                        should_include = True
                    
                    if should_include:
                        # Extract return type (everything between visibility/modifiers and method name)
                        parts = line.split(name)[0].strip()
                        # Remove visibility
                        if visibility:
                            parts = parts.replace(visibility, "", 1).strip()
                        # Remove common modifiers
                        for modifier in ["static", "virtual", "override", "abstract", "async", "sealed", "new", "extern", "partial"]:
                            parts = parts.replace(modifier, "", 1).strip()
                        # What's left should be the return type
                        return_type = parts.strip()
                        
                        # Extract parameters
                        params_start = line.find('(', line.find(name))
                        params_end = line.find(')', params_start)
                        params_str = line[params_start+1:params_end].strip()
                        parameters = [p.strip() for p in params_str.split(',')] if params_str else []
                        
                        # Extract modifiers
                        modifiers = []
                        for modifier in ["static", "virtual", "override", "abstract", "async", "sealed", "new", "extern", "partial"]:
                            if re.search(fr'\b{modifier}\b', line):
                                modifiers.append(modifier)
                        
                        # Find the column where the name starts
                        col_start = line.find(name)
                        
                        # Create element
                        element = CodeElement(
                            name=name,
                            element_type='method',
                            line_start=line_num,
                            line_end=None,
                            file_path=self.file_path,
                            parent=current_element,
                            visibility=visibility,
                            modifiers=modifiers,
                            parameters=parameters,
                            return_type=return_type,
                            namespace=current_namespace,
                            column_start=col_start,
                            length=len(name)
                        )
                        
                        self.all_elements.append(element)
                        self.elements_by_line[line_num] = element
                        
                        # Update hierarchy
                        if current_element:
                            current_element.add_child(element)
                        
                        # Push to stack if this is a method with a body (not an interface method)
                        if "{" in line and ";" not in line:
                            element_stack.append((element, current_element))
                            current_element = element
                        continue
            
            # Check for property declarations
            if self.show_properties.get():
                property_match = patterns['property'].search(line) or patterns['auto_property'].search(line)
                if property_match:
                    name = property_match.group(1)
                    
                    # Extract property details
                    visibility_match = visibility_pattern.search(line)
                    visibility = visibility_match.group(1) if visibility_match else ""
                    
                    # Check visibility filter
                    should_include = False
                    if not visibility or visibility == "public" and self.show_public.get():
                        should_include = True
                    elif visibility == "private" and self.show_private.get():
                        should_include = True
                    elif visibility == "protected" and self.show_protected.get():
                        should_include = True
                    elif visibility == "internal" and self.show_internal.get():
                        should_include = True
                    
                    if should_include:
                        # Extract property type
                        parts = line.split(name)[0].strip()
                        # Remove visibility
                        if visibility:
                            parts = parts.replace(visibility, "", 1).strip()
                        # Remove common modifiers
                        for modifier in ["virtual", "override", "abstract", "new", "static"]:
                            parts = parts.replace(modifier, "", 1).strip()
                        # What's left should be the property type
                        property_type = parts.strip()
                        
                        # Extract modifiers
                        modifiers = []
                        for modifier in ["virtual", "override", "abstract", "new", "static"]:
                            if re.search(fr'\b{modifier}\b', line):
                                modifiers.append(modifier)
                        
                        # Find the column where the name starts
                        col_start = line.find(name)
                        
                        # Create element
                        element = CodeElement(
                            name=name,
                            element_type='property',
                            line_start=line_num,
                            line_end=None,
                            file_path=self.file_path,
                            parent=current_element,
                            visibility=visibility,
                            modifiers=modifiers,
                            return_type=property_type,
                            namespace=current_namespace,
                            column_start=col_start,
                            length=len(name)
                        )
                        
                        self.all_elements.append(element)
                        self.elements_by_line[line_num] = element
                        
                        # Update hierarchy
                        if current_element:
                            current_element.add_child(element)
                        
                        # Push to stack for non-auto properties
                        if "{" in line and ";" not in line and not "{ get; set; }" in line:
                            element_stack.append((element, current_element))
                            current_element = element
                        continue
            
            # Check for variable declarations
            if self.show_variables.get():
                variable_match = patterns['variable'].search(line)
                if variable_match:
                    name = variable_match.group(1)
                    
                    # Extract variable details
                    visibility_match = visibility_pattern.search(line)
                    visibility = visibility_match.group(1) if visibility_match else ""
                    
                    # Check visibility filter
                    should_include = False
                    if not visibility or visibility == "public" and self.show_public.get():
                        should_include = True
                    elif visibility == "private" and self.show_private.get():
                        should_include = True
                    elif visibility == "protected" and self.show_protected.get():
                        should_include = True
                    elif visibility == "internal" and self.show_internal.get():
                        should_include = True
                    
                    if should_include:
                        # Extract modifiers
                        modifiers = []
                        for modifier in ["readonly", "const", "static", "volatile"]:
                            if re.search(fr'\b{modifier}\b', line):
                                modifiers.append(modifier)
                        
                        # Find the column where the name starts
                        col_start = line.find(name)
                        
                        # Create element
                        element = CodeElement(
                            name=name,
                            element_type='variable',
                            line_start=line_num,
                            line_end=line_num,  # Variables are typically single line
                            file_path=self.file_path,
                            parent=current_element,
                            visibility=visibility,
                            modifiers=modifiers,
                            namespace=current_namespace,
                            column_start=col_start,
                            length=len(name)
                        )
                        
                        self.all_elements.append(element)
                        self.elements_by_line[line_num] = element
                        
                        # Update hierarchy
                        if current_element:
                            current_element.add_child(element)
                        continue
            
            # Track scope end with brace counting
            if "{" in line:
                # This might be the start of a scope
                pass
            
            if "}" in line:
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
                    
                    # Find the column where the name starts
                    col_start = line.find(name)
                    
                    element = CodeElement(
                        name=name,
                        element_type='class',
                        line_start=line_num,
                        line_end=None,
                        file_path=self.file_path,
                        parent=parent,
                        column_start=col_start,
                        length=len(name)
                    )
                    
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
                    
                    # Extract parameters
                    params_start = line.find('(', line.find(name))
                    params_end = line.find(')', params_start)
                    params_str = line[params_start+1:params_end].strip()
                    parameters = [p.strip() for p in params_str.split(',')] if params_str else []
                    
                    # Find the column where the name starts
                    col_start = line.find(name)
                    
                    element = CodeElement(
                        name=name,
                        element_type='method',
                        line_start=line_num,
                        line_end=None,
                        file_path=self.file_path,
                        parent=parent,
                        parameters=parameters,
                        column_start=col_start,
                        length=len(name)
                    )
                    
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
                    
                    # Find the column where the name starts
                    col_start = line.find(name)
                    
                    element = CodeElement(
                        name=name,
                        element_type='variable',
                        line_start=line_num,
                        line_end=line_num,
                        file_path=self.file_path,
                        parent=parent,
                        column_start=col_start,
                        length=len(name)
                    )
                    
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
        Uses enhanced C# parsing from the reference tracker.
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
        # Clear existing element highlights
        self.code_editor.clear_highlights()
        
        # Add highlighting for each element
        for element in self.all_elements:
            # Skip elements with missing position information
            if element.line_start is None or element.column_start is None:
                continue
                
            # Add tag based on element type
            self.code_editor.highlight_element(
                element.element_type,
                element.line_start,
                element.column_start,
                element.length
            )
    
    def handle_code_click(self, event=None):
        """Handle clicks in the code editor"""
        # Get the position of the click
        index = self.code_editor.text.index(f"@{event.x},{event.y}")
        line = int(index.split('.')[0])
        
        # Check if this line has an element
        if line in self.elements_by_line:
            self.select_element(self.elements_by_line[line])
    
    def check_selection(self, event=None):
        """Check if text is selected and process it"""
        try:
            selection = self.code_editor.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selection:
                # Check if the selection matches any element name
                for element in self.all_elements:
                    if element.name == selection:
                        self.select_element(element)
                        break
        except tk.TclError:
            # No selection
            pass
    
    def select_element(self, element):
        """Select a code element and display its references"""
        self.current_element = element
        
        # Update element info
        self.element_name.config(text=element.name)
        
        # Build element type description
        type_desc = element.element_type.capitalize()
        if element.visibility:
            type_desc = f"{element.visibility} {type_desc}"
        if element.modifiers:
            type_desc = f"{type_desc} ({' '.join(element.modifiers)})"
        
        self.element_type.config(text=f"Type: {type_desc}")
        self.element_location.config(text=f"Location: Lines {element.line_start}-{element.line_end or '?'}")
        
        # Highlight the element in the code
        self.code_editor.clear_highlights()
        self.highlight_code_elements()
        
        # Add the "selected" tag to the current element
        if element.line_start and element.column_start:
            start_pos = f"{element.line_start}.{element.column_start}"
            end_pos = f"{element.line_start}.{element.column_start + element.length}"
            self.code_editor.text.tag_add("selected", start_pos, end_pos)
            
            # Ensure the element is visible
            self.code_editor.goto_position(element.line_start)
        
        # Build and display references
        self.build_reference_trees(element)
        
        self.status_var.set(f"Selected: {element.element_type} {element.name}")
    
    def build_reference_trees(self, element):
        """Build and display reference trees and related code elements for the selected element"""
        # Clear existing trees
        self.incoming_tree.delete(*self.incoming_tree.get_children())
        self.outgoing_tree.delete(*self.outgoing_tree.get_children())
        self.methods_tree.delete(*self.methods_tree.get_children())
        self.properties_tree.delete(*self.properties_tree.get_children())
        
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
        
        # For classes, show methods and properties
        if element.element_type in ['class', 'interface']:
            # Add methods
            methods = [child for child in element.children if child.element_type == 'method']
            for method in methods:
                signature = method.get_signature()
                self.methods_tree.insert(
                    "", "end", text=method.name,
                    values=(method.visibility, method.line_start, signature)
                )
            
            # Add properties
            properties = [child for child in element.children if child.element_type == 'property']
            for prop in properties:
                self.properties_tree.insert(
                    "", "end", text=prop.name,
                    values=(prop.visibility, prop.return_type, prop.line_start)
                )
            
            # Update tab names with counts
            self.ref_notebook.tab(2, text=f"Methods ({len(methods)})")
            self.ref_notebook.tab(3, text=f"Properties ({len(properties)})")
        else:
            # For non-class elements, use generic tab names
            self.ref_notebook.tab(2, text="Methods")
            self.ref_notebook.tab(3, text="Properties")
        
        # Update reference tab names with count
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
            self.code_editor.goto_position(line_number)
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
            self.code_editor.goto_position(line_number)
        else:
            # In a real implementation, we would load the other file
            # For this demo, we'll just show a message
            messagebox.showinfo("Reference", f"Would open {file_path} at line {line_number}")
    
    def navigate_to_method(self, event=None):
        """Navigate to the selected method"""
        selected_id = self.methods_tree.focus()
        if not selected_id:
            return
            
        # Get the values from the tree item
        item = self.methods_tree.item(selected_id)
        method_name = item["text"]
        line_number = item["values"][1]
        
        # Navigate to the line
        self.code_editor.goto_position(line_number)
    
    def navigate_to_property(self, event=None):
        """Navigate to the selected property"""
        selected_id = self.properties_tree.focus()
        if not selected_id:
            return
            
        # Get the values from the tree item
        item = self.properties_tree.item(selected_id)
        property_name = item["text"]
        line_number = item["values"][2]
        
        # Navigate to the line
        self.code_editor.goto_position(line_number)
    
    def search_code(self, event=None):
        """Search the code"""
        search_text = self.search_var.get()
        if not search_text:
            return
            
        # Get search options
        case_sensitive = self.case_sensitive_var.get()
        whole_word = self.whole_word_var.get()
        regex = self.regex_var.get()
        
        # Perform search
        self.search_matches = self.code_editor.search_text(
            search_text,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            regex=regex,
            highlight_all=True
        )
        
        # Reset current match index
        self.current_match = -1
        
        # Go to first match if any
        if self.search_matches:
            self.current_match = 0
            line, col = self.search_matches[0]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Found {len(self.search_matches)} matches")
        else:
            self.status_var.set("No matches found")
    
    def find_next(self, event=None):
        """Go to next search match"""
        if not self.search_matches:
            self.search_code()
            return
            
        if self.search_matches:
            # Move to next match
            self.current_match = (self.current_match + 1) % len(self.search_matches)
            line, col = self.search_matches[self.current_match]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Match {self.current_match + 1} of {len(self.search_matches)}")
    
    def find_previous(self, event=None):
        """Go to previous search match"""
        if not self.search_matches:
            self.search_code()
            return
            
        if self.search_matches:
            # Move to previous match
            self.current_match = (self.current_match - 1) % len(self.search_matches)
            line, col = self.search_matches[self.current_match]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Match {self.current_match + 1} of {len(self.search_matches)}")
    pass


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
        
        # Create text editor for code snippet
        text_editor = SynchronizedTextEditor(
            frame,
            bg_color=self.snippet_bg_color,
            fg_color=self.text_color,
            line_number_bg=self.bg_color,
            line_number_fg=self.text_color,
            highlight_color=self.highlight_color,
            selected_bg=self.highlight_color,
            selected_fg="white"
        )
        text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Insert code snippet
        try:
            with open(element.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Show a few lines before and after the element
            start = max(0, element.line_start - 3)
            end = min(len(lines), (element.line_end or element.line_start) + 3)
            
            # Create snippet content
            snippet_content = ''.join(lines[start:end])
            text_editor.set_content(snippet_content, element.file_path)
            
            # Highlight the element lines
            highlight_start = element.line_start - start
            highlight_end = (element.line_end or element.line_start) - start
            for line in range(highlight_start, highlight_end + 1):
                text_editor.highlight_line(line + 1)  # +1 because we need 1-based line numbers
        except Exception as e:
            text_editor.set_content(f"Error loading snippet: {str(e)}")
        
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
    pass


class CSharpCodeViewer(tk.Toplevel):
    """
    A specialized viewer for C# code with enhanced features:
    - Navigation between code behind and XAML files
    - Syntax highlighting for C# and XAML
    - Code outline tree view
    - Reference tracking integration
    """
    def __init__(self, parent, reference_tracker, file_path: str, theme="light"):
        super().__init__(parent)
        self.title("C# Code Viewer")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.reference_tracker = reference_tracker
        self.file_path = file_path
        self.theme = theme
        
        # Set theme colors
        self.set_theme(theme)
        
        # Create UI layout
        self.create_ui()
        
        # Load the initial file
        self.load_file(file_path)
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
    
    def set_theme(self, theme):
        """Set color theme for the viewer"""
        if theme == "dark":
            self.bg_color = "#282c34"
            self.text_color = "#abb2bf"
            self.highlight_color = "#61afef"
            self.tree_bg_color = "#21252b"
            self.tree_fg_color = "#abb2bf"
        else:  # light theme
            self.bg_color = "#ffffff"
            self.text_color = "#383a42"
            self.highlight_color = "#4078f2"
            self.tree_bg_color = "#f5f5f5"
            self.tree_fg_color = "#333333"
    
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
        
        # Add XAML/Code-behind toggle buttons
        self.xaml_button = ttk.Button(control_frame, text="View XAML", command=self.toggle_xaml_view, state=tk.DISABLED)
        self.xaml_button.pack(side=tk.LEFT, padx=5)
        
        self.code_behind_button = ttk.Button(control_frame, text="View Code-Behind", command=self.toggle_code_behind_view, state=tk.DISABLED)
        self.code_behind_button.pack(side=tk.LEFT, padx=5)
        
        # Search and navigation
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<Return>", self.search_code)
        
        ttk.Button(control_frame, text="Find", command=self.search_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Next", command=self.find_next).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Prev", command=self.find_previous).pack(side=tk.LEFT, padx=5)
        
        # Split pane between outline tree and code editor
        self.paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Outline tree
        outline_frame = ttk.Frame(self.paned)
        self.paned.add(outline_frame, weight=1)
        
        # Create outline tree
        outline_label = ttk.Label(outline_frame, text="Code Outline")
        outline_label.pack(fill=tk.X, pady=5)
        
        # Tree with scrollbar
        tree_frame = ttk.Frame(outline_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.outline_tree = ttk.Treeview(tree_frame)
        
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.outline_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.outline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.outline_tree.configure(yscrollcommand=vsb.set)
        
        # Configure tree columns
        self.outline_tree["columns"] = ("type", "line")
        self.outline_tree.column("#0", width=200)
        self.outline_tree.column("type", width=100)
        self.outline_tree.column("line", width=50)
        
        self.outline_tree.heading("#0", text="Name")
        self.outline_tree.heading("type", text="Type")
        self.outline_tree.heading("line", text="Line")
        
        # Bind double-click to navigate to element
        self.outline_tree.bind("<Double-1>", self.navigate_to_element)
        
        # Right panel - Code editor
        editor_frame = ttk.Frame(self.paned)
        self.paned.add(editor_frame, weight=3)
        
        # Create improved code editor
        self.code_editor = SynchronizedTextEditor(
            editor_frame,
            bg_color=self.bg_color,
            fg_color=self.text_color,
            line_number_bg=self.tree_bg_color,
            line_number_fg=self.text_color,
            highlight_color=self.highlight_color,
            selected_bg=self.highlight_color,
            selected_fg="white"
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X)
        
        # Initialize search variables
        self.search_matches = []
        self.current_match = -1
        
        # Store related file paths
        self.xaml_file = None
        self.code_behind_file = None
    
    def load_file(self, file_path):
        """Load a file into the editor and update UI accordingly"""
        if not file_path or not os.path.exists(file_path):
            self.status_var.set(f"Error: File not found - {file_path}")
            return
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update file path and label
            self.file_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            
            # Update editor content
            self.code_editor.set_content(content, file_path)
            
            # Parse code elements and update outline tree
            self.update_outline_tree()
            
            # Check for related XAML or code-behind file
            self.check_related_files()
            
            self.status_var.set(f"Loaded: {file_path}")
        except Exception as e:
            self.status_var.set(f"Error loading file: {str(e)}")
    
    def update_outline_tree(self):
        """Parse code and update the outline tree"""
        # Clear existing items
        self.outline_tree.delete(*self.outline_tree.get_children())
        
        # Determine file type
        is_xaml = self.file_path.lower().endswith(('.xaml', '.axaml'))
        is_csharp = self.file_path.lower().endswith('.cs')
        
        if is_csharp:
            self.parse_csharp_outline()
        elif is_xaml:
            self.parse_xaml_outline()
    
    def parse_csharp_outline(self):
        """Parse C# code and build outline tree"""
        content = self.code_editor.get_content()
        lines = content.split('\n')
        
        # Patterns for C# elements
        patterns = {
            'namespace': re.compile(r'^\s*(?:(?:public|internal)\s+)?namespace\s+([^\s{;]+)', re.MULTILINE),
            'class': re.compile(r'^\s*(?:(?:public|private|protected|internal)\s+)?(?:(?:abstract|sealed|static|partial)\s+)*class\s+(\w+)', re.MULTILINE),
            'interface': re.compile(r'^\s*(?:(?:public|private|protected|internal)\s+)?interface\s+(\w+)', re.MULTILINE),
            'method': re.compile(r'^\s*(?:(?:public|private|protected|internal)\s+)?(?:(?:abstract|virtual|override|sealed|static|async)\s+)*(?:[\w<>[\],\s]+\s+)(\w+)\s*\(', re.MULTILINE),
            'property': re.compile(r'^\s*(?:(?:public|private|protected|internal)\s+)?(?:(?:virtual|override|abstract|new|static)\s+)*(?:[\w<>[\],\s]+\s+)(\w+)\s*\{', re.MULTILINE),
        }
        
        # Track outline tree structure
        current_namespace = None
        current_class = None
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Check for namespace
            match = patterns['namespace'].search(line)
            if match:
                name = match.group(1)
                current_namespace = self.outline_tree.insert("", "end", text=name, values=("namespace", line_num))
                continue
            
            # Check for class
            match = patterns['class'].search(line)
            if match:
                name = match.group(1)
                parent = current_namespace if current_namespace else ""
                current_class = self.outline_tree.insert(parent, "end", text=name, values=("class", line_num))
                continue
            
            # Check for interface
            match = patterns['interface'].search(line)
            if match:
                name = match.group(1)
                parent = current_namespace if current_namespace else ""
                self.outline_tree.insert(parent, "end", text=name, values=("interface", line_num))
                continue
            
            # Check for method
            match = patterns['method'].search(line)
            if match:
                name = match.group(1)
                parent = current_class if current_class else current_namespace if current_namespace else ""
                self.outline_tree.insert(parent, "end", text=name, values=("method", line_num))
                continue
            
            # Check for property
            match = patterns['property'].search(line)
            if match:
                name = match.group(1)
                parent = current_class if current_class else current_namespace if current_namespace else ""
                self.outline_tree.insert(parent, "end", text=name, values=("property", line_num))
                continue
        
        # Expand all items
        for item in self.outline_tree.get_children():
            self.outline_tree.item(item, open=True)
    
    def parse_xaml_outline(self):
        """Parse XAML code and build outline tree"""
        content = self.code_editor.get_content()
        
        # Extract x:Class attribute
        class_match = re.search(r'x:Class="([^"]+)"', content)
        if class_match:
            class_name = class_match.group(1)
            class_node = self.outline_tree.insert("", "end", text=class_name, values=("class", 1))
        else:
            class_node = self.outline_tree.insert("", "end", text="XAML Root", values=("root", 1))
        
        # Extract XAML elements
        # This is a simplified approach - a real implementation would do proper XML parsing
        element_pattern = re.compile(r'<(\w+)[^>]*?(?:x:Name|Name)="([^"]+)"', re.DOTALL)
        for i, (match) in enumerate(element_pattern.finditer(content)):
            element_type = match.group(1)
            element_name = match.group(2)
            # Approximate line number
            line_num = content[:match.start()].count('\n') + 1
            self.outline_tree.insert(class_node, "end", text=element_name, values=(element_type, line_num))
        
        # Expand the root
        self.outline_tree.item(class_node, open=True)
    
    def navigate_to_element(self, event=None):
        """Navigate to the selected element in the outline tree"""
        selected_id = self.outline_tree.focus()
        if not selected_id:
            return
        
        # Get line number
        item = self.outline_tree.item(selected_id)
        line_num = item["values"][1]
        
        # Go to line
        if line_num:
            self.code_editor.goto_position(int(line_num))
    
    def check_related_files(self):
        """Check for related XAML and code-behind files"""
        # Reset button states
        self.xaml_button.config(state=tk.DISABLED)
        self.code_behind_button.config(state=tk.DISABLED)
        self.xaml_file = None
        self.code_behind_file = None
        
        if not self.reference_tracker:
            return
        
        # Check if this is a C# file that might have XAML
        if self.file_path.lower().endswith('.cs'):
            # Check if this file is in the C# to XAML mapping
            if hasattr(self.reference_tracker.tracker, 'cs_to_xaml_mapping'):
                if self.file_path in self.reference_tracker.tracker.cs_to_xaml_mapping:
                    self.xaml_file = self.reference_tracker.tracker.cs_to_xaml_mapping[self.file_path]
                    self.xaml_button.config(state=tk.NORMAL)
        
        # Check if this is a XAML file that might have code-behind
        elif self.file_path.lower().endswith(('.xaml', '.axaml')):
            # Check if this file is in the XAML to C# mapping
            if hasattr(self.reference_tracker.tracker, 'xaml_to_cs_mapping'):
                if self.file_path in self.reference_tracker.tracker.xaml_to_cs_mapping:
                    self.code_behind_file = self.reference_tracker.tracker.xaml_to_cs_mapping[self.file_path]
                    self.code_behind_button.config(state=tk.NORMAL)
    
    def toggle_xaml_view(self):
        """Switch to XAML view"""
        if self.xaml_file and os.path.exists(self.xaml_file):
            self.load_file(self.xaml_file)
    
    def toggle_code_behind_view(self):
        """Switch to code-behind view"""
        if self.code_behind_file and os.path.exists(self.code_behind_file):
            self.load_file(self.code_behind_file)
    
    def search_code(self, event=None):
        """Search for text in the editor"""
        search_text = self.search_var.get()
        if not search_text:
            return
        
        # Perform the search
        self.search_matches = self.code_editor.search_text(
            search_text,
            case_sensitive=False,
            whole_word=False,
            regex=False
        )
        
        # Reset current match
        self.current_match = -1
        
        # Go to first match if any
        if self.search_matches:
            self.current_match = 0
            line, col = self.search_matches[0]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Found {len(self.search_matches)} matches")
        else:
            self.status_var.set("No matches found")
    
    def find_next(self):
        """Go to next search match"""
        if not self.search_matches:
            self.search_code()
            return
        
        if self.search_matches:
            self.current_match = (self.current_match + 1) % len(self.search_matches)
            line, col = self.search_matches[self.current_match]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Match {self.current_match + 1} of {len(self.search_matches)}")
    
    def find_previous(self):
        """Go to previous search match"""
        if not self.search_matches:
            self.search_code()
            return
        
        if self.search_matches:
            self.current_match = (self.current_match - 1) % len(self.search_matches)
            line, col = self.search_matches[self.current_match]
            self.code_editor.goto_position(line, col)
            self.status_var.set(f"Match {self.current_match + 1} of {len(self.search_matches)}")
    pass


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
    
        # Import the visualizer class directly
        try:
            from code_visualizer import CodeRelationshipVisualizer
        
            # Initialize reference tracker if needed
            if not hasattr(self, 'reference_tracker') or not self.reference_tracker:
                from reference_tracking import ReferenceTrackingManager
                root_dir = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
                self.reference_tracker = ReferenceTrackingManager(root_dir, self.log)
                self.reference_tracker.parse_directory()
        
            # Open the visualizer
            CodeRelationshipVisualizer(self.root, self.reference_tracker, file_path)
        
        except ImportError:
            self.log("Error: Could not import visualization modules")
            messagebox.showerror("Error", "Visualization modules could not be loaded")
        except Exception as e:
            self.log(f"Error opening visualizer: {str(e)}")
            messagebox.showerror("Error", f"Could not open visualizer: {str(e)}")
    
    # Add method to show reference graph
    def show_reference_graph(self):
        """Show a graph visualization of file references"""
        # Check if we have a reference tracker
        if not hasattr(self, 'reference_tracker') or not self.reference_tracker:
            if hasattr(self, 'root_dir_var'):
                root_dir = self.root_dir_var.get()
                if not root_dir:
                    messagebox.showinfo("Information", "Please select a root directory first.")
                    return
                
                # Create reference tracker
                from reference_tracking import ReferenceTrackingManager
                self.log("Analyzing code for reference graph...")
                self.reference_tracker = ReferenceTrackingManager(root_dir, self.log)
                self.reference_tracker.parse_directory()
            else:
                messagebox.showinfo("Information", "Reference tracking not initialized.")
                return
        
        # Get all files with references
        if hasattr(self, 'selected_files') and self.selected_files:
            # Use selected files as starting points
            files = self.selected_files
        else:
            # Use all parsed files
            messagebox.showinfo("Information", "Please select files for the reference graph or use 'Visualize All References'.")
            return
        
        # Show input dialog for reference depth
        depth = simpledialog.askinteger("Reference Depth", 
                                      "Enter maximum reference depth (1-5):",
                                      minvalue=1, maxvalue=5, initialvalue=2)
        if not depth:
            return
        
        # Find related files
        self.log(f"Finding related files with depth {depth}...")
        related_files = self.reference_tracker.find_related_files(files, depth)
        
        # Show graph visualization (simplified version)
        self.show_reference_graph_visualization(related_files)
    
    def show_reference_graph_visualization(self, related_files):
        """Show a visualization of the reference graph"""
        # This is a placeholder where a more sophisticated graph visualization would go
        # For example, using a library like NetworkX + matplotlib, or a custom canvas visualization
        
        # For now, just show a dialog with the count of related files
        messagebox.showinfo("Reference Graph", 
                          f"Found {len(related_files)} related files.\n\n"
                          "Full graph visualization will be implemented in a future update.")
    
    # Add visualize all references method
    def visualize_all_references(self):
        """Visualize all references in the project"""
        if not hasattr(self, 'reference_tracker') or not self.reference_tracker:
            if hasattr(self, 'root_dir_var'):
                root_dir = self.root_dir_var.get()
                if not root_dir:
                    messagebox.showinfo("Information", "Please select a root directory first.")
                    return
                
                # Create reference tracker
                from reference_tracking import ReferenceTrackingManager
                self.log("Analyzing code for all references...")
                self.reference_tracker = ReferenceTrackingManager(root_dir, self.log)
                self.reference_tracker.parse_directory()
            else:
                messagebox.showinfo("Information", "Reference tracking not initialized.")
                return
        
        # Show dialog with reference statistics
        if hasattr(self.reference_tracker, 'get_parsed_file_count'):
            file_count = self.reference_tracker.get_parsed_file_count()
            messagebox.showinfo("Reference Statistics", 
                              f"Analyzed {file_count} files.\n\n"
                              "Please select specific files to visualize their references.")
    
    # Add method to app class
    app_class.open_code_visualizer = open_code_visualizer
    app_class.show_reference_graph = show_reference_graph
    app_class.show_reference_graph_visualization = show_reference_graph_visualization
    app_class.visualize_all_references = visualize_all_references
    
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
                    visualize_menu.add_command(label="All References...",
                                            command=self.visualize_all_references)
                    break
    
    # Add method to app class
    app_class.add_visualizer_menu_options = add_visualizer_menu_options
    
    # Patch the app's __init__ method to add the visualizer menu
    original_init = app_class.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Add visualizer menu options
        self.add_visualizer_menu_options()
    
    # Replace the init method
    app_class.__init__ = patched_init
    pass