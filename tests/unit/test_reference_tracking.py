"""
Tests for the reference tracking functionality.
"""

import os
import pytest
import reference_tracking


def test_reference_tracking_manager_initialization(csharp_project):
    """Test initializing the reference tracking manager."""
    # Create with a basic log callback
    log_messages = []
    log_callback = lambda msg: log_messages.append(msg)
    
    manager = reference_tracking.ReferenceTrackingManager(csharp_project, log_callback)
    
    assert manager.root_dir == csharp_project, "Root directory should be set correctly"
    assert manager.log_callback is log_callback, "Log callback should be set correctly"
    assert manager.files_parsed == 0, "Files parsed should be initialized to 0"
    
    # Test logging
    manager.log("Test message")
    assert "Test message" in log_messages, "Log callback should be called"


def test_parse_directory(csharp_project):
    """Test parsing a directory with C# and XAML files."""
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    
    # Parse with XAML files included
    files_parsed = manager.parse_directory(include_xaml=True)
    
    assert files_parsed > 0, "Should parse some files"
    assert manager.files_parsed == files_parsed, "Files parsed should be updated"
    
    # Verify the tracker has file information
    assert len(manager.tracker.file_info) > 0, "Tracker should have file information"
    
    # Check if XAML files were parsed
    xaml_files = [f for f in manager.tracker.file_info.keys() if f.endswith('.xaml')]
    assert len(xaml_files) > 0, "Should have parsed XAML files"
    
    # Parse with XAML files excluded
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    files_parsed = manager.parse_directory(include_xaml=False)
    
    # Verify the tracker doesn't have XAML files
    xaml_files = [f for f in manager.tracker.file_info.keys() if f.endswith('.xaml')]
    assert len(xaml_files) == 0, "Should not have parsed XAML files"


def test_get_method_details(csharp_project):
    """Test getting method details."""
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    manager.parse_directory()
    
    # Find the User.cs file
    user_file = None
    for file_path in manager.tracker.file_info.keys():
        if "User.cs" in file_path:
            user_file = file_path
            break
    
    assert user_file is not None, "Should find User.cs file"
    
    # Get all methods in the file
    methods = manager.get_methods_in_file(user_file)
    assert "GetGreeting" in methods, "Should find GetGreeting method"
    
    # Get specific method details
    method_details = manager.get_method_details(user_file, "GetGreeting")
    assert len(method_details) > 0, "Should get method details"
    
    greeting_details = next(iter(method_details.values()))
    assert greeting_details.get('name') == "GetGreeting", "Method name should match"
    assert "$\"Hello, {Name}!" in greeting_details.get('content', ''), "Method content should match"


def test_find_related_files(csharp_project):
    """Test finding related files."""
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    manager.parse_directory()
    
    # Find the UserController.cs file
    controller_file = None
    for file_path in manager.tracker.file_info.keys():
        if "UserController.cs" in file_path:
            controller_file = file_path
            break
    
    assert controller_file is not None, "Should find UserController.cs file"
    
    # Find related files with depth 1
    related_files = manager.find_related_files([controller_file], depth=1)
    
    assert len(related_files) > 1, "Should find at least one related file"
    assert controller_file in related_files, "Original file should be included"
    
    # Find users.cs through reference
    user_files = [f for f in related_files if "User.cs" in f]
    assert len(user_files) > 0, "Should find User.cs through reference"
    
    # Test with unlimited depth
    related_files_unlimited = manager.find_related_files([controller_file], depth=float('inf'))
    assert len(related_files_unlimited) >= len(related_files), "Unlimited depth should find at least as many files"
    
    # Test with XAML ignore
    xaml_file = None
    for file_path in manager.tracker.file_info.keys():
        if file_path.endswith('.xaml'):
            xaml_file = file_path
            break
            
    if xaml_file:
        # Find related files including XAML
        related_with_xaml = manager.find_related_files([xaml_file], depth=1)
        assert xaml_file in related_with_xaml, "XAML file should be included"
        
        # Find related files ignoring XAML
        related_without_xaml = manager.find_related_files([xaml_file], depth=1, ignore_xaml=True)
        xaml_files = [f for f in related_without_xaml if f.endswith('.xaml')]
        assert len(xaml_files) == 1, "Only selected XAML file should be included"


def test_generate_reference_summary(csharp_project):
    """Test generating a reference summary."""
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    manager.parse_directory()
    
    # Find all files
    all_files = set(manager.tracker.file_info.keys())
    
    # Generate summary
    summary = manager.generate_reference_summary(all_files)
    
    assert "REFERENCE ANALYSIS SUMMARY" in summary, "Summary should have title"
    assert f"Total files analyzed: {manager.files_parsed}" in summary, "Should show total files"
    assert f"Files with references: {len(all_files)}" in summary, "Should show files with references"
    assert "C# files:" in summary, "Should include C# file count"
    assert "XAML/AXAML files:" in summary, "Should include XAML file count"
    
    # Check for method statistics
    assert "Total methods defined:" in summary, "Should include method count"
    
    # Check for reference statistics
    if "Most Referenced Files:" in summary:
        assert "referenced by" in summary, "Should include reference counts"


def test_improved_line_counting(csharp_project):
    """Test the improved line counting function."""
    manager = reference_tracking.ReferenceTrackingManager(csharp_project)
    
    # Find all C# files
    cs_files = [os.path.join(root, f) for root, _, files in os.walk(csharp_project) 
               for f in files if f.endswith('.cs')]
    
    assert len(cs_files) > 0, "Should find C# files"
    
    # Count lines using the improved method
    total_lines, total_non_blank = manager.count_total_lines(cs_files)
    
    assert total_lines > 0, "Should count lines"
    assert total_non_blank > 0, "Should count non-blank lines"
    assert total_lines >= total_non_blank, "Total lines should be >= non-blank lines"
    
    # Try with nonexistent files (should handle gracefully)
    total_lines, total_non_blank = manager.count_total_lines(cs_files + ["nonexistent.cs"])
    assert total_lines > 0, "Should still count lines despite nonexistent file"