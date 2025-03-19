import re
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

class CSharpReferenceTracker:
    """
    Parser and tracker for C# code references between files.
    Identifies method declarations and references to track relationships between files.
    
    This class provides functionality to:
    1. Parse C# source files to identify declarations and references
    2. Build a reference graph showing how files relate to each other
    3. Find all files related to a set of starting files within a specified depth
    4. Parse XAML/AXAML files and link them to their code-behind files
    """
    
    def __init__(self):
        # Regex patterns for different C# constructs
        self.patterns = {
            # Namespace declarations
            'namespace': re.compile(r'namespace\s+([^\s{;]+)'),
            
            # Using directives
            'using': re.compile(r'using\s+(?:static\s+)?([^;]+);'),
            
            # Type declarations (classes, interfaces, structs, etc.)
            'class_decl': re.compile(r'(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected|file)\s+)?(?:(?:abstract|sealed|static)\s+)?(?:partial\s+)?(?:class|struct|interface|record|enum)\s+(\w+)'),
            
            # Method declarations
            'method_decl': re.compile(r'(?:(?:public|private|protected|internal|protected\s+internal|private\s+protected|file)\s+)?(?:(?:abstract|virtual|override|sealed|static|async|new|extern)\s+)*(?:[\w<>[\],\s]+\s+)(\w+)\s*\([^)]*\)(?:\s*:\s*[^{;]+)?(?:\s*where\s+[^{;]+)?(?:\s*=>|{)'),
            
            # Method calls
            'method_call': re.compile(r'(\w+)\.(\w+)\s*\('),
            
            # Type references and instantiations
            'type_ref': re.compile(r'(?:new|typeof)\s+(\w+)(?:<[^>]*>)?\s*\(?'),
            
            # Inheritance and implementation
            'inheritance': re.compile(r'(?:class|struct|interface|record)\s+\w+\s*(?:<[^>]*>)?\s*:\s*([^{]+)'),
        }
        
        # Store parsed file info
        self.file_info = {}  # file_path -> {'namespace': str, 'types': [], 'methods': [], 'references': []}
        
        # Graph of references between files
        self.reference_graph = defaultdict(set)  # file_path -> {referenced_files}
        self.reverse_graph = defaultdict(set)    # file_path -> {files_referencing_this}
        
        # XAML relationship tracking
        self.xaml_to_cs_mapping = {}  # xaml_file_path -> cs_file_path
        self.cs_to_xaml_mapping = {}  # cs_file_path -> xaml_file_path
    
    def get_method_details(self, file_path, method_name=None):
        """
        Get method details for a specific file or method.
    
        Args:
            file_path: Path to the source file
            method_name: Optional specific method name
        
        Returns:
            Dictionary of method information
        """
        if file_path not in self.file_info:
            return {}
        
        file_data = self.file_info[file_path]
        methods_info = {}
    
        # Extract content for method analysis
        content = file_data.get('raw_content', '')
        if not content:
            return {}
    
        # Find all methods or a specific method
        if method_name:
            # Find a specific method
            methods = [m for m in file_data.get('methods', []) if m == method_name]
            if not methods:
                return {}
        else:
            # Get all methods in the file
            methods = file_data.get('methods', [])
    
        # Extract details for each method
        for method in methods:
            # Find method in content
            pattern = r'(?:public|private|protected|internal)\s+(?:(?:virtual|override|abstract|static|async)\s+)*(?:[\w<>[\],\s]+\s+)' + \
                      re.escape(method) + r'\s*\(([^)]*)\)(?:\s*(?:where\s+.*?)?(?:{|=>))'
            match = re.search(pattern, content)
        
            if match:
                # Find method body
                start_pos = match.start()
            
                # Find method body if using braces
                if '{' in match.group():
                    # Find matching closing brace
                    brace_count = 1
                    end_pos = match.end()
                
                    while brace_count > 0 and end_pos < len(content):
                        if content[end_pos] == '{':
                            brace_count += 1
                        elif content[end_pos] == '}':
                            brace_count -= 1
                        end_pos += 1
                
                    method_content = content[start_pos:end_pos]
                else:
                    # Expression-bodied method
                    semicolon_pos = content.find(';', match.end())
                    method_content = content[start_pos:semicolon_pos+1]
            
                # Extract line numbers
                start_line = content[:start_pos].count('\n') + 1
                end_line = start_line + method_content.count('\n')
            
                # Find method calls within this method
                calls = []
                call_pattern = r'(\w+)\.(\w+)\s*\('
                for call_match in re.finditer(call_pattern, method_content):
                    obj_name = call_match.group(1)
                    called_method = call_match.group(2)
                    calls.append((obj_name, called_method))
            
                # Create method info
                methods_info[method] = {
                    'name': method,
                    'parameters': match.group(1) if match.groups() else '',
                    'content': method_content,
                    'start_line': start_line,
                    'end_line': end_line,
                    'calls': calls,
                    'signature': match.group(0)
                }
    
        return methods_info

    def get_method_references(self, file_path, method_name):
        """
        Find all references to a specific method.
    
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method to find references for
        
        Returns:
            (incoming_refs, outgoing_refs) - Lists of reference information
        """
        incoming_refs = []  # Methods that call this method
        outgoing_refs = []  # Methods that this method calls
    
        # Ensure the file exists in our info
        if file_path not in self.file_info:
            return [], []
    
        # Get containing class/namespace info
        class_name = None
        namespace = self.file_info[file_path].get('namespace', '')
    
        # Find containing class (assuming method is in a class)
        for type_name in self.file_info[file_path].get('types', []):
            # Simple heuristic - in a more thorough solution, we would check method scope
            class_name = type_name
            break
    
        # Create qualified name patterns to search for
        qualified_patterns = []
        if class_name:
            qualified_patterns.append(f"{class_name}.{method_name}")
            if namespace:
                qualified_patterns.append(f"{namespace}.{class_name}.{method_name}")
    
        # Look for references in all files
        for source_file, info in self.file_info.items():
            # Skip the current file for incoming references
            if source_file == file_path:
                # Get outgoing references from this method
                method_info = self.get_method_details(file_path, method_name)
                if method_name in method_info:
                    for obj_name, called_method in method_info[method_name].get('calls', []):
                        # Try to resolve the target class/file
                        target_file = self._find_likely_file_for_class(obj_name)
                        outgoing_refs.append({
                            'method': called_method,
                            'class': obj_name,
                            'file': target_file or "Unknown",
                            'line': 0  # Would need more analysis to find exact line
                        })
                continue
            
            # Look for direct method calls to our target
            for ref_type, *ref_args in info.get('references', []):
                if ref_type == 'method_call':
                    obj_name, called_method = ref_args
                    if called_method == method_name:
                        # Check if this is likely calling our target method
                        if obj_name == class_name or any(pat in info.get('raw_content', '') for pat in qualified_patterns):
                            # Find calling methods
                            calling_methods = []
                            for method_name_in_file, method_details in self.get_method_details(source_file).items():
                                if any(call[1] == method_name for call in method_details.get('calls', [])):
                                    calling_methods.append(method_name_in_file)
                        
                            # If we found specific calling methods, add them
                            if calling_methods:
                                for calling_method in calling_methods:
                                    incoming_refs.append({
                                        'method': calling_method,
                                        'class': info.get('types', ['Unknown'])[0],
                                        'file': source_file,
                                        'line': 0  # Simplified - would need more analysis
                                    })
                            else:
                                # If no specific methods found, add a generic reference
                                incoming_refs.append({
                                    'method': 'Unknown',
                                    'class': info.get('types', ['Unknown'])[0],
                                    'file': source_file,
                                    'line': 0
                                })
    
        return incoming_refs, outgoing_refs

    def _find_likely_file_for_class(self, class_name):
        """Find the most likely file that contains a given class"""
        for file_path, info in self.file_info.items():
            if class_name in info.get('types', []):
                return file_path
        return None

    def parse_directory(self, directory, include_xaml=True):
        """
        Parse all C# files in a directory and its subdirectories
        
        Args:
            directory: Root directory to parse
            include_xaml: Whether to include XAML files in the analysis
            
        Returns:
            Number of files parsed
        """
        # Track the number of files parsed
        files_parsed = 0
        
        # First pass: Parse all C# files to collect type information
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".cs"):
                    full_path = os.path.join(root, file)
                    if self.parse_file(full_path):
                        files_parsed += 1
        
        # Second pass: Parse XAML files if enabled
        if include_xaml:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".xaml") or file.endswith(".axaml"):
                        full_path = os.path.join(root, file)
                        if self.parse_xaml_file(full_path):
                            files_parsed += 1
        
        # Third pass: Analyze code-behind relationships
        self.discover_code_behind_relationships()
        
        # Build reference graph after parsing all files
        self._build_reference_graph()
        return files_parsed
    
    def parse_file(self, file_path):
        """Parse a C# file and extract declarations and references"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Remove comments and string literals to simplify parsing
            clean_content = self._remove_comments_and_strings(content)
            
            # Get namespace
            namespace = self._extract_namespace(clean_content)
            
            # Get using directives
            using_directives = self._extract_using_directives(clean_content)
            
            # Get type declarations (classes, interfaces, etc.)
            types = self._extract_type_declarations(clean_content)
            
            # Get method declarations
            methods = self._extract_method_declarations(clean_content)
            
            # Get method calls and type references
            references = self._extract_references(clean_content)
            
            # Get inheritance and implementation relationships
            inheritance = self._extract_inheritance(clean_content)
            
            # Store the information
            self.file_info[file_path] = {
                'namespace': namespace,
                'using': using_directives,
                'types': types,
                'methods': methods,
                'references': references,
                'inheritance': inheritance,
                'raw_content': content,  # Keep original content for later highlighting
                'is_xaml': False
            }
            
            return True
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            return False
    
    def parse_xaml_file(self, file_path):
        """
        Parse a XAML or AXAML file to extract references to code-behind
        
        Args:
            file_path: Path to the XAML file
            
        Returns:
            Boolean indicating parsing success
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Extract x:Class attribute which points to the code-behind class
            class_name = None
            
            # Use regex for more reliable parsing than XML parsing due to XAML namespaces
            class_match = re.search(r'x:Class="([^"]+)"', content)
            if class_match:
                class_name = class_match.group(1)
            
            # Store the XAML file information
            self.file_info[file_path] = {
                'namespace': '',  # XAML files don't have a namespace in the same way
                'types': [class_name] if class_name else [],
                'methods': [],
                'references': [],
                'inheritance': [],
                'raw_content': content,
                'is_xaml': True,
                'code_behind_class': class_name
            }
            
            return True
        except Exception as e:
            print(f"Error parsing XAML file {file_path}: {str(e)}")
            return False
    
    def discover_code_behind_relationships(self):
        """
        Discover relationships between XAML files and their code-behind CS files
        """
        # Map from class name to C# file that defines it
        class_to_file = {}
        
        # First, build a map of class names to files
        for file_path, info in self.file_info.items():
            if not info.get('is_xaml', False):  # Only for C# files
                for type_name in info.get('types', []):
                    qualified_name = f"{info['namespace']}.{type_name}" if info['namespace'] else type_name
                    class_to_file[qualified_name] = file_path
                    # Also map the unqualified name to handle cases where namespaces might not match
                    class_to_file[type_name] = file_path
        
        # Now find XAML files and link them to their code-behind
        for xaml_file, info in list(self.file_info.items()):
            if info.get('is_xaml', False):
                code_behind_class = info.get('code_behind_class')
                if code_behind_class and code_behind_class in class_to_file:
                    cs_file = class_to_file[code_behind_class]
                    
                    # Create the mapping between XAML and CS files
                    self.xaml_to_cs_mapping[xaml_file] = cs_file
                    self.cs_to_xaml_mapping[cs_file] = xaml_file
                    
                    # Add a "xaml_file" reference to the C# file info
                    if 'xaml_files' not in self.file_info[cs_file]:
                        self.file_info[cs_file]['xaml_files'] = []
                    self.file_info[cs_file]['xaml_files'].append(xaml_file)
                    
                    # Add a reference from the XAML file to its code-behind
                    if 'references' not in self.file_info[xaml_file]:
                        self.file_info[xaml_file]['references'] = []
                    self.file_info[xaml_file]['references'].append(('code_behind', code_behind_class))
    
    def _remove_comments_and_strings(self, content):
        """Remove comments and string literals to simplify parsing"""
        # Remove /* ... */ comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove // comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        # Replace string literals with empty strings (handles both "" and @"")
        content = re.sub(r'(?:@".*?(?:"|$))|(?:"(?:\\.|[^"\\])*")', '""', content, flags=re.DOTALL)
        
        # Replace character literals
        content = re.sub(r"'(?:\\.|[^'\\])*'", "''", content)
        
        return content
    
    def _extract_namespace(self, content):
        """Extract namespace from content"""
        match = self.patterns['namespace'].search(content)
        if match:
            return match.group(1).strip()
        return ''
    
    def _extract_using_directives(self, content):
        """Extract using directives from content"""
        directives = []
        for match in self.patterns['using'].finditer(content):
            directives.append(match.group(1).strip())
        return directives
    
    def _extract_type_declarations(self, content):
        """Extract class, interface, struct, enum declarations from content"""
        types = []
        for match in self.patterns['class_decl'].finditer(content):
            types.append(match.group(1))
        return types
    
    def _extract_method_declarations(self, content):
        """Extract method declarations from content"""
        methods = []
        for match in self.patterns['method_decl'].finditer(content):
            method_name = match.group(1)
            # Filter out obvious C# keywords that might be incorrectly matched
            if method_name not in ['if', 'while', 'for', 'foreach', 'switch', 'using', 'try', 'catch']:
                methods.append(method_name)
        return methods
    
    def _extract_references(self, content):
        """Extract method calls and type references from content"""
        references = []
        
        # Extract method calls
        for match in self.patterns['method_call'].finditer(content):
            object_name = match.group(1)
            method_name = match.group(2)
            # Skip "this" references and obvious C# keywords
            if object_name not in ['this', 'base', 'var', 'if', 'for', 'while']:
                references.append(('method_call', object_name, method_name))
        
        # Extract type references
        for match in self.patterns['type_ref'].finditer(content):
            type_name = match.group(1)
            # Skip primitive types and common .NET types
            if type_name not in ['int', 'string', 'bool', 'double', 'float', 'decimal', 'var', 'object', 'void']:
                references.append(('type_ref', type_name))
        
        return references
    
    def _extract_inheritance(self, content):
        """Extract inheritance and implementation relationships"""
        inheritance = []
        for match in self.patterns['inheritance'].finditer(content):
            # Parse the inheritance/implementation list
            inheritance_list = match.group(1).split(',')
            for base_type in inheritance_list:
                # Extract just the type name, removing generics and whitespace
                base_type = re.sub(r'<.*?>', '', base_type).strip()
                inheritance.append(base_type)
        return inheritance
    
    def _build_reference_graph(self):
        """Build a graph of references between files"""
        # Reset graphs
        self.reference_graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        
        # Build the namespace to file mapping
        namespace_map = {}
        type_map = {}
        
        for file_path, info in self.file_info.items():
            # Skip XAML files for namespace mapping
            if info.get('is_xaml', False):
                continue
                
            # Map namespace to file
            if info['namespace']:
                namespace_map[info['namespace']] = file_path
            
            # Map each type to its file
            for type_name in info['types']:
                qualified_name = f"{info['namespace']}.{type_name}" if info['namespace'] else type_name
                type_map[qualified_name] = file_path
                type_map[type_name] = file_path  # Also map unqualified name (may cause conflicts but good enough for basic matching)
        
        # Now analyze each file for references
        for source_file, info in self.file_info.items():
            # For XAML files, check code-behind relationship
            if info.get('is_xaml', False):
                if source_file in self.xaml_to_cs_mapping:
                    target_file = self.xaml_to_cs_mapping[source_file]
                    self.reference_graph[source_file].add(target_file)
                    self.reverse_graph[target_file].add(source_file)
                continue
                
            # For C# files with XAML
            if source_file in self.cs_to_xaml_mapping:
                xaml_file = self.cs_to_xaml_mapping[source_file]
                self.reference_graph[source_file].add(xaml_file)
                self.reverse_graph[xaml_file].add(source_file)
            
            # Check using directives
            for namespace in info['using']:
                if namespace in namespace_map:
                    target_file = namespace_map[namespace]
                    if target_file != source_file:  # Don't add self-references
                        self.reference_graph[source_file].add(target_file)
                        self.reverse_graph[target_file].add(source_file)
            
            # Check method calls and type references
            for ref_type, *ref_args in info['references']:
                if ref_type == 'method_call':
                    object_name, method_name = ref_args
                    # Try to find the class that defines this method
                    for target_file, target_info in self.file_info.items():
                        if target_info.get('is_xaml', False):
                            continue
                        if object_name in target_info['types'] and method_name in target_info['methods']:
                            if target_file != source_file:  # Don't add self-references
                                self.reference_graph[source_file].add(target_file)
                                self.reverse_graph[target_file].add(source_file)
                
                elif ref_type == 'type_ref':
                    type_name = ref_args[0]
                    # Try to find the file that defines this type
                    if type_name in type_map:
                        target_file = type_map[type_name]
                        if target_file != source_file:  # Don't add self-references
                            self.reference_graph[source_file].add(target_file)
                            self.reverse_graph[target_file].add(source_file)
            
            # Check inheritance relationships
            for base_type in info['inheritance']:
                if base_type in type_map:
                    target_file = type_map[base_type]
                    if target_file != source_file:  # Don't add self-references
                        self.reference_graph[source_file].add(target_file)
                        self.reverse_graph[target_file].add(source_file)
    
    def find_related_files(self, start_files, max_depth=float('inf'), ignore_xaml=False):
        """
        Find all files that are related to the starting files within the given depth.
        Includes both files referenced by the starting files and files that reference the starting files.
        
        Args:
            start_files: List of file paths to start from
            max_depth: Maximum reference depth to traverse (unlimited if inf)
            ignore_xaml: Whether to ignore XAML/AXAML files in the results
            
        Returns:
            Set of file paths that are related to the starting files
        """
        # Make sure graphs are built
        if not self.reference_graph and not self.reverse_graph:
            self._build_reference_graph()
        
        # Set of files that are related to the starting files
        related_files = set(start_files)
        
        # Queue of (file, depth) to process
        queue = [(file, 0) for file in start_files]
        visited = set(start_files)
        
        while queue:
            current_file, current_depth = queue.pop(0)
            
            # Stop if we've reached the maximum depth
            if current_depth >= max_depth:
                continue
            
            # Add files that this file references
            for referenced_file in self.reference_graph.get(current_file, set()):
                # Skip XAML files if they should be ignored
                if ignore_xaml and referenced_file.endswith(('.xaml', '.axaml')) and referenced_file not in start_files:
                    continue
                    
                related_files.add(referenced_file)
                if referenced_file not in visited:
                    visited.add(referenced_file)
                    queue.append((referenced_file, current_depth + 1))
            
            # Add files that reference this file
            for referencing_file in self.reverse_graph.get(current_file, set()):
                # Skip XAML files if they should be ignored
                if ignore_xaml and referencing_file.endswith(('.xaml', '.axaml')) and referencing_file not in start_files:
                    continue
                    
                related_files.add(referencing_file)
                if referencing_file not in visited:
                    visited.add(referencing_file)
                    queue.append((referencing_file, current_depth + 1))
        
        # Add explicitly selected XAML files back to the related_files set
        # even if we're ignoring XAML files in general
        if ignore_xaml:
            for file_path in start_files:
                if file_path.endswith(('.xaml', '.axaml')):
                    related_files.add(file_path)
        
        return related_files
    
    def get_reference_details(self, file_path):
        """
        Get detailed information about references for a specific file
        
        Returns:
            (referenced_by, references_to) tuple of sets
        """
        referenced_by = self.reverse_graph.get(file_path, set())
        references_to = self.reference_graph.get(file_path, set())
        return referenced_by, references_to
    
    def highlight_references(self, file_path):
        """
        Generate a version of the file content with references highlighted
        
        Returns:
            Content with HTML-style highlighting of references
        """
        if file_path not in self.file_info:
            return None
        
        content = self.file_info[file_path]['raw_content']
        # Implementation of highlighting would go here
        # For now, return the raw content
        return content