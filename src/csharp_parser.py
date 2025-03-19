import re
import os
from collections import defaultdict

class CSharpReferenceTracker:
    """
    Parser and tracker for C# code references between files.
    Identifies method declarations and references to track relationships between files.
    
    This class provides functionality to:
    1. Parse C# source files to identify declarations and references
    2. Build a reference graph showing how files relate to each other
    3. Find all files related to a set of starting files within a specified depth
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
    
    def parse_directory(self, directory, file_extension=".cs"):
        """Parse all C# files in a directory and its subdirectories"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extension):
                    full_path = os.path.join(root, file)
                    self.parse_file(full_path)
        
        # Build reference graph after parsing all files
        self._build_reference_graph()
        return len(self.file_info)
    
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
                'raw_content': content  # Keep original content for later highlighting
            }
            
            return self.file_info[file_path]
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            return None
    
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
    
    def find_related_files(self, start_files, max_depth=float('inf')):
        """
        Find all files that are related to the starting files within the given depth.
        Includes both files referenced by the starting files and files that reference the starting files.
        
        Args:
            start_files: List of file paths to start from
            max_depth: Maximum reference depth to traverse (unlimited if inf)
            
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
                related_files.add(referenced_file)
                if referenced_file not in visited:
                    visited.add(referenced_file)
                    queue.append((referenced_file, current_depth + 1))
            
            # Add files that reference this file
            for referencing_file in self.reverse_graph.get(current_file, set()):
                related_files.add(referencing_file)
                if referencing_file not in visited:
                    visited.add(referencing_file)
                    queue.append((referencing_file, current_depth + 1))
        
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