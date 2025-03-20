"""
Reference tracking module for the File Tree Generator.
Provides integration between the GUI, parser, and file tree generation.
"""

import os
from csharp_parser import CSharpReferenceTracker

class ReferenceTrackingManager:
    """
    Manager for reference tracking operations.
    Handles parsing, analysis, and result presentation.
    """
    
    def __init__(self, root_dir, log_callback=None):
        """
        Initialize the reference tracking manager.
        
        Args:
            root_dir: Root directory for analysis
            log_callback: Function to call for logging
        """
        self.root_dir = root_dir
        self.log_callback = log_callback or (lambda msg: None)
        self.tracker = CSharpReferenceTracker()
        self.files_parsed = 0
    
    def log(self, message):
        """Log a message using the callback if available"""
        if self.log_callback:
            self.log_callback(message)
    
    def parse_directory(self, include_xaml=True):
        """
        Parse all C# and optionally XAML/AXAML files in the root directory
        
        Args:
            include_xaml: Whether to include XAML/AXAML files in the analysis
        
        Returns:
            Number of files parsed
        """
        self.log(f"Parsing C# files in {self.root_dir}...")
        if include_xaml:
            self.log("Including XAML/AXAML files in analysis")
        else:
            self.log("Excluding XAML/AXAML files from analysis")
            
        self.files_parsed = self.tracker.parse_directory(self.root_dir, include_xaml=include_xaml)
        self.log(f"Parsed {self.files_parsed} files")
        return self.files_parsed
    
    def get_method_details(self, file_path, method_name=None):
        """
        Get detailed information about methods in a file.
    
        Args:
            file_path: Path to the file
            method_name: Optional specific method name
        
        Returns:
            Dictionary of method information
        """
        return self.tracker.get_method_details(file_path, method_name)

    def get_method_references(self, file_path, method_name):
        """
        Get methods that reference a specific method and methods referenced by it.
    
        Args:
            file_path: Path to the file containing the method
            method_name: Name of the method
        
        Returns:
            (incoming_refs, outgoing_refs) tuple of lists
        """
        return self.tracker.get_method_references(file_path, method_name)

    def get_methods_in_file(self, file_path):
        """
        Get a list of all methods in a file.
    
        Args:
            file_path: Path to the file
    
        Returns:
            List of method names
        """
        if file_path not in self.tracker.file_info:
            return []
    
        return self.tracker.file_info[file_path].get('methods', [])

    def find_related_files(self, start_files, depth=float('inf'), ignore_xaml=False):
        """
        Find all files related to the starting files.
        
        Args:
            start_files: List of files to start analysis from
            depth: Maximum reference depth to traverse
            ignore_xaml: Whether to ignore XAML files in the results (except selected ones)
            
        Returns:
            Set of file paths that are related to the starting files
        """
        if not self.files_parsed:
            self.parse_directory()
        
        depth_str = 'unlimited' if depth == float('inf') else depth
        self.log(f"Finding files related to {len(start_files)} selected files (max depth: {depth_str})")
        
        if ignore_xaml:
            self.log("Ignoring XAML/AXAML files (except selected ones)")
            
        related_files = self.tracker.find_related_files(start_files, depth, ignore_xaml=ignore_xaml)
        
        # Count the types of files found
        xaml_count = sum(1 for file in related_files if file.endswith(('.xaml', '.axaml')))
        cs_count = sum(1 for file in related_files if file.endswith('.cs'))
        other_count = len(related_files) - xaml_count - cs_count
        
        self.log(f"Found {len(related_files)} related files "
                f"({cs_count} C#, {xaml_count} XAML/AXAML, {other_count} other)")
        
        return related_files
    
    def get_reference_details(self, file_path):
        """
        Get detailed information about references for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            (referenced_by, references_to) tuple of sets
        """
        return self.tracker.get_reference_details(file_path)
    
    def count_total_lines(self, file_paths):
        """
        Count total lines in the given files with improved memory efficiency.
    
        Args:
            file_paths: List of file paths
        
        Returns:
            Total line count, total non-blank lines
        """
        total_lines = 0
        total_non_blank = 0
    
        for file_path in file_paths:
            try:
                # Use a streaming approach to count lines without loading the entire file
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        total_lines += 1
                        if line.strip():
                            total_non_blank += 1
            except Exception:
                # Skip files we can't read
                pass
                
        return total_lines, total_non_blank
    
    def get_method_statistics(self):
        """
        Get statistics about methods in parsed files
        
        Returns:
            Dictionary with method statistics
        """
        method_count = 0
        methods_by_file = {}
        
        for file_path, info in self.tracker.file_info.items():
            # Skip XAML files for method statistics
            if info.get('is_xaml', False):
                continue
                
            methods = info.get('methods', [])
            method_count += len(methods)
            methods_by_file[file_path] = len(methods)
        
        # Find files with most methods
        top_method_files = sorted(methods_by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_methods': method_count,
            'avg_methods_per_file': method_count / max(1, len([f for f, i in self.tracker.file_info.items() if not i.get('is_xaml', False)])),
            'top_method_files': top_method_files
        }
    
    def get_reference_statistics(self, referenced_files):
        """
        Get statistics about references between files
        
        Args:
            referenced_files: Set of referenced file paths
            
        Returns:
            Dictionary with reference statistics
        """
        # Count incoming and outgoing references for each file
        incoming_refs = {}
        outgoing_refs = {}
        
        for file_path in referenced_files:
            referenced_by, references_to = self.tracker.get_reference_details(file_path)
            incoming_refs[file_path] = len(referenced_by)
            outgoing_refs[file_path] = len(references_to)
        
        # Most referenced files (most incoming references)
        most_referenced = sorted(incoming_refs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Files with most outgoing references
        most_outgoing = sorted(outgoing_refs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'most_referenced': most_referenced,
            'most_outgoing': most_outgoing
        }
    
    def generate_reference_summary(self, referenced_files):
        """
        Generate a text summary of references.
        
        Args:
            referenced_files: Set of referenced file paths
            
        Returns:
            String with summary information
        """
        summary = []
        summary.append("REFERENCE ANALYSIS SUMMARY")
        summary.append("=" * 80)
        summary.append(f"Total files analyzed: {self.files_parsed}")
        summary.append(f"Files with references: {len(referenced_files)}")
        
        # Count file types
        xaml_count = sum(1 for file in referenced_files if file.endswith(('.xaml', '.axaml')))
        cs_count = sum(1 for file in referenced_files if file.endswith('.cs'))
        other_count = len(referenced_files) - xaml_count - cs_count
        
        summary.append(f"C# files: {cs_count}")
        summary.append(f"XAML/AXAML files: {xaml_count}")
        summary.append(f"Other files: {other_count}")
        
        # Get line count statistics
        total_lines, total_non_blank = self.count_total_lines(referenced_files)
        summary.append(f"\nTotal lines of code: {total_lines:,}")
        summary.append(f"Total non-blank lines: {total_non_blank:,}")
        
        # Get method statistics
        method_stats = self.get_method_statistics()
        summary.append(f"\nTotal methods defined: {method_stats['total_methods']:,}")
        summary.append(f"Average methods per file: {method_stats['avg_methods_per_file']:.2f}")
        
        # Get reference statistics
        ref_stats = self.get_reference_statistics(referenced_files)
        
        # Add details about most referenced files
        if ref_stats['most_referenced']:
            summary.append("\nMost Referenced Files:")
            for file_path, count in ref_stats['most_referenced']:
                rel_path = os.path.relpath(file_path, self.root_dir)
                
                # Add (XAML) marker for XAML files
                file_type = ""
                if file_path.endswith(('.xaml', '.axaml')):
                    file_type = " (XAML)"
                
                # Get method count for non-XAML files
                methods = 0
                if not file_path.endswith(('.xaml', '.axaml')):
                    methods = len(self.tracker.file_info.get(file_path, {}).get('methods', []))
                    summary.append(f" - {rel_path}{file_type} (referenced by {count} files, contains {methods} methods)")
                else:
                    summary.append(f" - {rel_path}{file_type} (referenced by {count} files)")
        
        # Add details about files with most outgoing references
        if ref_stats['most_outgoing']:
            summary.append("\nFiles with Most Outgoing References:")
            for file_path, count in ref_stats['most_outgoing']:
                rel_path = os.path.relpath(file_path, self.root_dir)
                
                # Add (XAML) marker for XAML files
                file_type = ""
                if file_path.endswith(('.xaml', '.axaml')):
                    file_type = " (XAML)"
                    
                summary.append(f" - {rel_path}{file_type} (references {count} other files)")
        
        # Add details about file types
        extension_stats = {}
        for file_path in referenced_files:
            _, ext = os.path.splitext(file_path)
            if ext:
                extension_stats[ext] = extension_stats.get(ext, 0) + 1
        
        if extension_stats:
            summary.append("\nFile Types:")
            for ext, count in sorted(extension_stats.items(), key=lambda x: x[1], reverse=True):
                summary.append(f" - {ext}: {count} files")
            
        # Add XAML to C# mapping information if any XAML files were found
        xaml_files = [f for f in referenced_files if f.endswith(('.xaml', '.axaml'))]
        if xaml_files and hasattr(self.tracker, 'xaml_to_cs_mapping'):
            xaml_with_code_behind = 0
            for xaml_file in xaml_files:
                if xaml_file in self.tracker.xaml_to_cs_mapping:
                    xaml_with_code_behind += 1
                    
            summary.append(f"\nXAML/AXAML with code-behind: {xaml_with_code_behind} of {len(xaml_files)} files")
        
        return "\n".join(summary)
    
    def get_parsed_file_count(self):
        """Get the number of files that have been parsed"""
        return self.files_parsed