"""
Unit tests for the file_tree_generator module.
"""

import os
import re
import pytest
from pathlib import Path
import file_tree_generator


def test_safe_read_file(sample_project):
    """Test the safe_read_file function."""
    # Test reading a valid file
    file_path = os.path.join(sample_project, "src", "main.py")
    success, lines, error = file_tree_generator.safe_read_file(file_path)
    
    assert success is True, "Reading a valid file should succeed"
    assert len(lines) > 0, "Valid file should have content"
    assert error is None, "Error should be None for successful read"
    
    # Test reading a nonexistent file
    nonexistent_file = os.path.join(sample_project, "nonexistent.py")
    success, lines, error = file_tree_generator.safe_read_file(nonexistent_file)
    
    assert success is False, "Reading a nonexistent file should fail"
    assert len(lines) == 0, "Nonexistent file should have no content"
    assert error is not None, "Error should be provided for failed read"
    
    # Test line limit
    success, lines, error = file_tree_generator.safe_read_file(file_path, max_lines=1)
    
    assert success is True, "Reading with line limit should succeed"
    assert len(lines) == 2, "Should return max_lines + truncation message"
    assert any("truncated" in line for line in lines), "Should include truncation message"


def test_safe_write_file(output_file):
    """Test the safe_write_file function."""
    # Test writing string content
    content = "Test content"
    success, error = file_tree_generator.safe_write_file(output_file, content)
    
    assert success is True, "Writing string content should succeed"
    assert error is None, "Error should be None for successful write"
    assert os.path.exists(output_file), "Output file should exist"
    
    with open(output_file, 'r') as f:
        file_content = f.read()
    assert file_content == content, "File content should match written content"
    
    # Test writing list content
    content_list = ["Line 1", "Line 2", "Line 3"]
    success, error = file_tree_generator.safe_write_file(output_file, content_list)
    
    assert success is True, "Writing list content should succeed"
    assert error is None, "Error should be None for successful write"
    
    with open(output_file, 'r') as f:
        file_content = f.read()
    assert file_content == "\n".join(content_list), "File content should match joined list"
    
    # Test writing to an invalid path
    invalid_path = "/nonexistent_dir/test.txt"
    success, error = file_tree_generator.safe_write_file(invalid_path, content)
    
    assert success is False, "Writing to invalid path should fail"
    assert error is not None, "Error should be provided for failed write"


def test_format_size():
    """Test the format_size function."""
    assert file_tree_generator.format_size(0) == "0.00 B", "0 bytes should format correctly"
    assert file_tree_generator.format_size(1023) == "1023.00 B", "Bytes should format correctly"
    assert file_tree_generator.format_size(1024) == "1.00 KB", "KB should format correctly"
    assert file_tree_generator.format_size(1024 * 1024) == "1.00 MB", "MB should format correctly"
    assert file_tree_generator.format_size(1024 * 1024 * 1024) == "1.00 GB", "GB should format correctly"


def test_clean_file_content():
    """Test the clean_file_content function."""
    # Test Python file with comments and empty lines
    content = [
        "# This is a comment",
        "def hello():",
        "    # Another comment",
        "    print('Hello')",
        "",
        "# Final comment"
    ]
    
    # Test without cleaning
    cleaned = file_tree_generator.clean_file_content("test.py", content, False, False)
    assert len(cleaned) == len(content), "No cleaning should preserve all lines"
    
    # Test removing comments only
    cleaned = file_tree_generator.clean_file_content("test.py", content, True, False)
    assert len(cleaned) == len(content), "Removing comments should preserve line count"
    assert not any("# This is a comment" in line for line in cleaned), "Comments should be removed"
    
    # Test removing empty lines only
    cleaned = file_tree_generator.clean_file_content("test.py", content, False, True)
    assert len(cleaned) == len(content) - 1, "One empty line should be removed"
    
    # Test removing both comments and empty lines
    cleaned = file_tree_generator.clean_file_content("test.py", content, True, True)
    assert len(cleaned) == 2, "Should have only code lines remaining"
    assert all(line.strip() for line in cleaned), "All lines should have content"


def test_create_file_tree(sample_project, output_file):
    """Test the create_file_tree function."""
    # Basic test with all defaults
    result = file_tree_generator.create_file_tree(
        sample_project,
        {".py", ".md"},
        output_file,
        blacklist_folders=set(),
        blacklist_files=set(),
        compact_view=True
    )
    
    assert os.path.exists(output_file), "Output file should be created"
    assert "successfully" in result, "Result should indicate success"
    
    # Read the output and check contents
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "File Structure" in content, "Output should include title"
    assert "main.py" in content, "Output should include main.py"
    assert "utils.py" in content, "Output should include utils.py"
    assert "README.md" in content, "Output should include README.md"
    
    # Test with blacklisting
    result = file_tree_generator.create_file_tree(
        sample_project,
        {".py", ".md"},
        output_file,
        blacklist_folders={"docs"},
        blacklist_files=set(),
        compact_view=True
    )
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "main.py" in content, "Output should include main.py"
    assert "README.md" not in content, "Output should not include README.md (in blacklisted folder)"
    
    # Test with ultra-compact view
    result = file_tree_generator.create_file_tree(
        sample_project,
        {".py", ".md"},
        output_file,
        blacklist_folders=set(),
        blacklist_files=set(),
        compact_view=False,
        ultra_compact_view=True
    )
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "TREE:" in content, "Ultra-compact output should use minimal format"
    
    # Test token estimation
    result = file_tree_generator.create_file_tree(
        sample_project,
        {".py", ".md"},
        output_file,
        blacklist_folders=set(),
        blacklist_files=set(),
        compact_view=True,
        enable_token_estimation=True
    )
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "TOKEN ESTIMATION" in content, "Output should include token estimation"
    assert "Estimated tokens:" in content, "Output should include token counts"


@pytest.mark.parametrize("format_type", ["html", "markdown", "json"])
def test_export_formats(sample_project, output_file, format_type):
    """Test different export formats."""
    # Create a basic text output first
    file_tree_generator.create_file_tree(
        sample_project,
        {".py", ".md"},
        output_file,
        blacklist_folders=set(),
        blacklist_files=set()
    )
    
    # Read the output
    with open(output_file, 'r') as f:
        content = f.readlines()
    
    # Test export function
    export_file = f"{os.path.splitext(output_file)[0]}.{format_type}"
    
    if format_type == "html":
        file_tree_generator.export_as_html(content, export_file)
        assert os.path.exists(export_file), "HTML file should be created"
        with open(export_file, 'r') as f:
            html_content = f.read()
        assert "<!DOCTYPE html>" in html_content, "Should have HTML structure"
        assert "<title>File Tree</title>" in html_content, "Should have title"
        
    elif format_type == "markdown":
        file_tree_generator.export_as_markdown(content, export_file)
        assert os.path.exists(export_file), "Markdown file should be created"
        with open(export_file, 'r') as f:
            md_content = f.read()
        assert "# File Structure" in md_content, "Should have markdown header"
        
    elif format_type == "json":
        file_tree_generator.export_as_json(content, export_file)
        assert os.path.exists(export_file), "JSON file should be created"
        with open(export_file, 'r') as f:
            json_content = f.read()
        assert '"metadata":' in json_content, "Should have metadata structure"
        assert '"tree":' in json_content, "Should have tree structure"