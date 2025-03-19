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
    
    def parse_directory(self):
        """Parse all C# files in the root directory"""
        self.log(f"Parsing C# files in {self.root_dir}...")
        self.files_parsed = self.tracker.parse_directory(self.root_dir)
        self.log(f"Parsed {self.files_parsed} C# files")
        return self.files_parsed
    
    def find_related_files(self, start_files, depth=float('inf')):
        """
        Find all files related to the starting files.
        
        Args:
            start_files: List of files to start analysis from
            depth: Maximum reference depth to traverse
            
        Returns:
            Set of file paths that are related to the starting files
        """
        if not self.files_parsed:
            self.parse_directory()
        
        self.log(f"Finding files related to {len(start_files)} selected files (max depth: {'unlimited' if depth == float('inf') else depth})...")
        related_files = self.tracker.find_related_files(start_files, depth)
        self.log(f"Found {len(related_files)} related files")
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
        
        # Add details about most referenced files
        reference_counts = {}
        for file_path in referenced_files:
            referenced_by, _ = self.tracker.get_reference_details(file_path)
            reference_counts[file_path] = len(referenced_by)
        
        # Sort by reference count
        sorted_files = sorted(reference_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 10 most referenced files
        if sorted_files:
            summary.append("\nMost Referenced Files:")
            for file_path, count in sorted_files[:10]:
                rel_path = os.path.relpath(file_path, self.root_dir)
                summary.append(f" - {rel_path} (referenced by {count} files)")
        
        return "\n".join(summary)
    
    def get_parsed_file_count(self):
        """Get the number of files that have been parsed"""
        return self.files_parsed