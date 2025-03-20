import os
import datetime
import argparse
import sys
import re
import token_estimator

import tkinter as tk
from tkinter import ttk, messagebox

from reference_tracking import ReferenceTrackingManager

def parse_args():
    """Parse command line arguments for file tree generator"""
    parser = argparse.ArgumentParser(
        description="Generate a text-based visual representation of a directory tree with file contents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument("root_dir", help="Root directory to start scanning")
    parser.add_argument("output_file", help="Output file path")
    
    # Optional arguments
    parser.add_argument("--extensions", "-e", nargs="+", default=[".py", ".txt", ".md", ".json", ".js", ".html", ".css"],
                        help="File extensions to include (e.g., .py .js .html)")
    parser.add_argument("--blacklist-folders", "-bf", nargs="+", default=["bin", "obj", "node_modules", ".git"],
                        help="Folders to exclude")
    parser.add_argument("--blacklist-files", "-bff", nargs="+", default=["desktop.ini", "thumbs.db"],
                        help="Files to exclude")
    parser.add_argument("--priority-folders", "-pf", nargs="+", default=[],
                        help="Folders to prioritize in the output")
    parser.add_argument("--priority-files", "-pff", nargs="+", default=[],
                        help="Files to prioritize in the output")
    parser.add_argument("--max-lines", "-ml", type=int, default=1000,
                        help="Maximum number of lines to display per file")
    parser.add_argument("--max-line-length", "-mll", type=int, default=300,
                        help="Maximum length of each line to display")
    parser.add_argument("--compact", "-c", action="store_true",
                        help="Use compact view for cleaner output")
    parser.add_argument("--format", "-f", choices=["txt", "html", "markdown", "json"], default="txt",
                        help="Output format")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Recursively process all subdirectories")
    parser.add_argument("--verbose", "-v", action="store_true",
                    help="Show verbose output during processing")
    parser.add_argument("--ultra-compact", "-uc", action="store_true",
                        help="Use ultra-compact view for maximum token efficiency")
    # Add new arguments
    parser.add_argument("--remove-comments", "-rc", action="store_true",
                        help="Remove comments from file content")
    parser.add_argument("--exclude-empty-lines", "-eel", action="store_true",
                        help="Exclude empty lines from file content")
    parser.add_argument("--enable-token-estimation", "-et", action="store_true",
                        help="Enable token estimation")
    parser.add_argument("--token-model", "-tm", default="claude-3.5-sonnet",
                        help="Token estimation model to use")
    parser.add_argument("--token-method", "-tmt", choices=["char", "word"], default="char",
                        help="Token estimation method (character or word based)")
    
    return parser.parse_args()

"""
Modifications to file_tree_generator.py to add an ultra-compact export mode
that maximizes token efficiency while preserving all data.
"""
def create_file_tree(root_dir, extensions, output_file, blacklist_folders=None, blacklist_files=None, 
                  max_lines=1000, max_line_length=300, compact_view=False, ultra_compact_view=False,
                  remove_comments=False, exclude_empty_lines=False,
                  smart_truncate=False, hide_binary_files=False, hide_repeated_sections=False,
                  priority_folders=None, priority_files=None, referenced_files=None,
                  enable_token_estimation=False, token_model="claude-3.5-sonnet", token_method="char"):
    """
    Generate a text-based visual representation of a directory tree and file contents.
    
    Parameters:
    root_dir (str): Root directory to start scanning
    extensions (set): File extensions to include
    output_file (str): Output file path
    blacklist_folders (set): Folders to exclude
    blacklist_files (set): Files to exclude
    max_lines (int): Maximum number of lines to display per file
    max_line_length (int): Maximum length of each line to display
    compact_view (bool): Use compact view for cleaner output
    ultra_compact_view (bool): Use ultra-compact view for maximum token efficiency
    remove_comments (bool): Remove comments from file content
    exclude_empty_lines (bool): Exclude empty lines from file content
    hide_binary_files (bool): Hide binary file contents
    smart_truncate (bool): Use smart line truncation
    hide_repeated_sections (bool): Collapse repeated code sections
    priority_folders (list): Folders to prioritize in the output
    priority_files (list): Files to prioritize in the output
    referenced_files (set): Set of files that are referenced (for reference tracking mode)
    enable_token_estimation (bool): Whether to include token estimates
    token_model (str): Model to use for token estimation
    token_method (str): Method for token estimation (char or word)
    """
    # Initialize lists and options
    blacklist_folders = set(blacklist_folders or [])
    blacklist_files = set(blacklist_files or [])
    priority_folders = priority_folders or []
    priority_files = priority_files or []
    
    # Use ultra-compact mode format for highest efficiency
    # (overrides compact_view if both are True)
    if ultra_compact_view:
        compact_view = False
    
    # Check if we're in reference tracking mode
    reference_tracking_mode = referenced_files is not None
    
    # Initialize the output string
    output = []
    
    # Perform token estimation if enabled
    token_info = None
    token_results = None
    token_output_estimate = None
    
    if enable_token_estimation:
        # Create a set of files to analyze
        files_to_analyze = set()
        
        if reference_tracking_mode and referenced_files:
            # If in reference tracking mode, use referenced files
            files_to_analyze = referenced_files
        else:
            # Otherwise, walk the directory tree to find matching files
            for root, dirs, files in os.walk(root_dir):
                # Skip blacklisted directories
                if os.path.basename(root) in blacklist_folders:
                    continue
                    
                for file in files:
                    # Skip blacklisted files
                    if file in blacklist_files:
                        continue
                        
                    # Check extensions
                    if any(file.endswith(ext) for ext in extensions):
                        file_path = os.path.join(root, file)
                        files_to_analyze.add(file_path)
        
        # Perform token estimation on selected files
        token_results = token_estimator.estimate_tokens_for_directory(
            root_dir,
            extensions=extensions,
            blacklist_folders=blacklist_folders,
            blacklist_files=blacklist_files,
            model=token_model,
            method=token_method
        )
        
        # Format token estimation summary
        token_info = token_estimator.format_token_summary(token_results, root_dir)
    
    # Minimal header in ultra-compact mode
    if ultra_compact_view:
        output.append(f"TREE:{os.path.abspath(root_dir)}")
        output.append(f"DATE:{datetime.datetime.now().strftime('%Y-%m-%d')}")
        output.append(f"EXT:{','.join(extensions)}")
        if reference_tracking_mode:
            output.append(f"REF:{len(referenced_files)}")
        if enable_token_estimation and token_results:
            output.append(f"TOKENS:{token_results['total_tokens']}")
    else:
        output.append(f"File Structure - {os.path.abspath(root_dir)}")
        output.append(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Extensions: {', '.join(extensions)}")
        if reference_tracking_mode:
            output.append(f"Reference Tracking: Enabled (tracking {len(referenced_files)} files)")
        if enable_token_estimation and token_results:
            output.append(f"Token Estimation: Enabled (Model: {token_results['model_name']}, Est. Tokens: {token_results['total_tokens']:,})")
        output.append("=" * 80)
    
    output.append("")
    
    # Generate barebones tree structure first
    output.append("DIRECTORY STRUCTURE SUMMARY")
    output.append("-" * 80)
    
    relevant_files_cache = {}
    def has_relevant_files(dir_path, ext_set, referenced_files=None):
        """
        Check if directory or its subdirectories contain relevant files
    
        Args:
            dir_path: Directory path to check
            ext_set: Set of file extensions to include
            referenced_files: Optional set of files for reference tracking mode
        
        Returns:
            Boolean indicating if relevant files are found
        """
        # Check cache first
        if dir_path in relevant_files_cache:
            return relevant_files_cache[dir_path]
    
        try:
            # Check if directory is blacklisted
            dir_name = os.path.basename(dir_path)
            if dir_name in blacklist_folders:
                relevant_files_cache[dir_path] = False
                return False
        
            # If in reference tracking mode and no files in this folder are referenced,
            # we can exit early
            if referenced_files is not None:
                # Check if any file in directory or subdirectories is in referenced_files
                dir_prefix = dir_path + os.sep
                has_any_referenced = any(
                    f.startswith(dir_prefix) for f in referenced_files
                )
                if not has_any_referenced:
                    relevant_files_cache[dir_path] = False
                    return False
        
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if os.path.isfile(full_path):
                    if item in blacklist_files:
                        continue
                
                    # Check if file has relevant extension
                    is_relevant_extension = any(item.endswith(ext) for ext in ext_set)
                
                    if is_relevant_extension:
                        # If in reference tracking mode, only count referenced files
                        if referenced_files is not None:
                            if full_path in referenced_files:
                                relevant_files_cache[dir_path] = True
                                return True
                        else:
                            # In normal mode, any file with matching extension counts
                            relevant_files_cache[dir_path] = True
                            return True
                    
                elif os.path.isdir(full_path):
                    if has_relevant_files(full_path, ext_set, referenced_files):
                        relevant_files_cache[dir_path] = True
                        return True
        
            relevant_files_cache[dir_path] = False
            return False
        
        except (PermissionError, OSError):
            relevant_files_cache[dir_path] = False
            return False




    def process_directory(current_dir, prefix=""):
        try:
            # Check if directory is blacklisted
            dir_name = os.path.basename(current_dir)
            if dir_name in blacklist_folders:
                return False

            # First check if this directory should be included
            if not has_relevant_files(current_dir, extensions):
                return False

            # Add directory to tree with simpler format in ultra-compact mode
            rel_path = os.path.relpath(current_dir, root_dir)
            if rel_path == ".":
                if ultra_compact_view:
                    output.append(f"{prefix}D {dir_name} (root)")
                else:
                    output.append(f"{prefix}📁 {dir_name} (root)")
            else:
                if ultra_compact_view:
                    output.append(f"{prefix}D {dir_name}")
                else:
                    output.append(f"{prefix}📁 {dir_name}")

            # Process all items in current directory
            items = sorted(os.listdir(current_dir))
            dirs = []
            files = []
            
            # Separate files and directories for better organization
            for item in items:
                full_path = os.path.join(current_dir, item)
                if os.path.isfile(full_path):
                    # If in reference tracking mode, only include referenced files
                    if reference_tracking_mode:
                        if full_path in referenced_files and item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
                            files.append(item)
                    elif item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
                        files.append(item)
                elif os.path.isdir(full_path) and item not in blacklist_folders:
                    dirs.append(item)
            
            # Sort directories and files based on priority
            def get_folder_priority(folder_name):
                try:
                    return priority_folders.index(folder_name)
                except ValueError:
                    return len(priority_folders)
                    
            def get_file_priority(file_name):
                try:
                    return priority_files.index(file_name)
                except ValueError:
                    return len(priority_files)
            
            # Sort directories by priority first, then alphabetically
            dirs.sort(key=lambda x: (get_folder_priority(x), x))
            
            # Sort files by priority first, then alphabetically
            files.sort(key=lambda x: (get_file_priority(x), x))
            
            # Process all directories first, then files
            for i, item in enumerate(dirs):
                full_path = os.path.join(current_dir, item)
                
                # Determine if this is the last item in the directory
                is_last = (i == len(dirs) - 1 and len(files) == 0)
                
                # Update prefix for child items - simpler in ultra-compact mode
                if ultra_compact_view:
                    child_prefix = prefix + ("L " if is_last else "| ")
                    next_prefix = prefix + ("  " if is_last else "| ")
                else:
                    child_prefix = prefix + ("└── " if is_last else "├── ")
                    next_prefix = prefix + ("    " if is_last else "│   ")
                
                # Recursively process subdirectory
                process_directory(full_path, next_prefix)
            
            # Now process all files
            for i, item in enumerate(files):
                full_path = os.path.join(current_dir, item)
                
                # Determine if this is the last item
                is_last = (i == len(files) - 1)
                
                # Update prefix for file - simpler in ultra-compact mode
                if ultra_compact_view:
                    file_prefix = prefix + ("L " if is_last else "| ")
                    content_prefix = prefix + ("  " if is_last else "| ")
                else:
                    file_prefix = prefix + ("└── " if is_last else "├── ")
                    content_prefix = prefix + ("    " if is_last else "│   ")
                
                # Add file to tree with minimal metadata in ultra-compact mode
                file_size = os.path.getsize(full_path)
                last_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d %H:%M:%S")
                
                # Check if this file is referenced (for reference tracking mode)
                is_referenced = reference_tracking_mode and full_path in referenced_files
                
                # Add special marker for referenced files with minimal format in ultra-compact mode
                if ultra_compact_view:
                    size_str = format_size(file_size)
                    if reference_tracking_mode:
                        if is_referenced:
                            output.append(f"{file_prefix}F {item} [{size_str}]*")  # * indicates referenced
                        else:
                            output.append(f"{file_prefix}F {item} [{size_str}]")
                    else:
                        output.append(f"{file_prefix}F {item} [{size_str}]")
                else:
                    if reference_tracking_mode:
                        if is_referenced:
                            output.append(f"{file_prefix}📄 {item} ({format_size(file_size)}, {last_modified}) [REFERENCED]")
                        else:
                            output.append(f"{file_prefix}📄 {item} ({format_size(file_size)}, {last_modified})")
                    else:
                        output.append(f"{file_prefix}📄 {item} ({format_size(file_size)}, {last_modified})")
                
                # Add file content with formatting based on view mode
                try:
                    # Skip content for non-referenced files when in reference tracking mode
                    if reference_tracking_mode and not is_referenced:
                        continue
                    
                    success, lines, error = safe_read_file(full_path, max_lines, remove_comments, exclude_empty_lines)

                    if not success:
                        # Make sure content_prefix is not None (safety check)
                        prefix_to_use = content_prefix if content_prefix is not None else ""
                        if ultra_compact_view:
                            output.append(f"{prefix_to_use}ERR:{error}")
                        elif compact_view:
                            output.append(f"{prefix_to_use}---[ERROR: {error}]---")
                        else:
                            output.append(f"{prefix_to_use}│ ERROR: {error}")
                            output.append(f"{prefix_to_use}└{'─' * 70}")
                        continue

                    
                    # Apply additional efficiency processing
                    lines = process_file_content(
                        full_path, 
                        lines, 
                        #hide_binary=hide_binary_files,
                        smart_truncate=smart_truncate,
                        hide_repeated=hide_repeated_sections,
                        max_line_length=max_line_length
                    )
                        
                    # Make sure content_prefix is not None (safety check)
                    prefix_to_use = content_prefix if content_prefix is not None else ""
                    if ultra_compact_view:
                        # Ultra-compact view with absolute minimal formatting
                        # Just display line number and content with no decorative elements
                        is_small_file = len(lines) <= 3
                        for line_num, line in enumerate(lines, 1):
                            if line_num > max_lines:
                                output.append(f"{prefix_to_use}+{len(lines)-max_lines}more")
                                break
                            truncated_line = line[:max_line_length] + ".." if len(line) > max_line_length else line
                            # For very small files, skip line numbers to save space
                            if is_small_file:
                                output.append(f"{prefix_to_use}{truncated_line}")
                            else:
                                output.append(f"{prefix_to_use}{line_num}:{truncated_line}")
                    elif compact_view:
                        # Compact view with minimal decorative characters
                        output.append(f"{prefix_to_use}---[FILE: {item}]---")
                        for line_num, line in enumerate(lines, 1):
                            if line_num > max_lines:
                                output.append(f"{prefix_to_use}...(+{len(lines)-max_lines} more lines)")
                                break
                            truncated_line = line[:max_line_length] + "..." if len(line) > max_line_length else line
                            output.append(f"{prefix_to_use}{line_num}:{truncated_line}")
                        output.append(f"{prefix_to_use}---[END]---")
                    else:
                        # Standard view with full formatting
                        # Add content header
                        output.append(f"{prefix_to_use}┌{'─' * 70}")
                        output.append(f"{prefix_to_use}│ FILE CONTENT: {item}")
                        output.append(f"{prefix_to_use}├{'─' * 70}")
                            
                        # Add content with line numbers
                        for line_num, line in enumerate(lines, 1):
                            if line_num > max_lines:
                                output.append(f"{prefix_to_use}│ ... (truncated after {max_lines} lines, {len(lines)-max_lines} more lines)")
                                break
                            truncated_line = line[:max_line_length] + "..." if len(line) > max_line_length else line
                            output.append(f"{prefix_to_use}│ {line_num:4d} │ {truncated_line}")
                            
                        # Add content footer
                        output.append(f"{prefix_to_use}└{'─' * 70}")
                except Exception as e:
                    # Make sure content_prefix is not None (safety check)
                    prefix_to_use = content_prefix if content_prefix is not None else ""
                    if ultra_compact_view:
                        output.append(f"{prefix_to_use}ERR:{str(e)[:50]}")
                    elif compact_view:
                        output.append(f"{prefix_to_use}---[ERROR: {str(e)}]---")
                    else:
                        output.append(f"{prefix_to_use}│ ERROR reading file: {str(e)}")
                        output.append(f"{prefix_to_use}└{'─' * 70}")

            return True

        except PermissionError:
            if ultra_compact_view:
                output.append(f"{prefix}! Permission denied: {current_dir}")
            else:
                output.append(f"{prefix}❌ Permission denied accessing {current_dir}")
            return False
        except Exception as e:
            if ultra_compact_view:
                output.append(f"{prefix}! Error: {str(e)[:50]}")
            else:
                output.append(f"{prefix}❌ Error processing {current_dir}: {str(e)}")
            return False


    # Generate barebones tree structure first
    output.append("DIRECTORY STRUCTURE SUMMARY")
    output.append("-" * 80)
    
    def generate_barebones_tree(current_dir, prefix=""):
        try:
            # Check if directory is blacklisted
            dir_name = os.path.basename(current_dir)
            if dir_name in blacklist_folders:
                return False

            # First check if this directory should be included
            if not has_relevant_files(current_dir, extensions):
                return False

            # Add directory to tree
            rel_path = os.path.relpath(current_dir, root_dir)
            if rel_path == ".":
                output.append(f"{prefix}📁 {dir_name} (root)")
            else:
                output.append(f"{prefix}📁 {dir_name}")

            # Process all items in current directory
            items = sorted(os.listdir(current_dir))
            dirs = []
            files = []
            
            # Separate files and directories for better organization
            for item in items:
                full_path = os.path.join(current_dir, item)
                if os.path.isfile(full_path):
                    # If in reference tracking mode, only include referenced files
                    if reference_tracking_mode:
                        if full_path in referenced_files and item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
                            files.append(item)
                    elif item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
                        files.append(item)
                elif os.path.isdir(full_path) and item not in blacklist_folders:
                    dirs.append(item)
            
            # Process all directories first, then files
            for i, item in enumerate(dirs):
                full_path = os.path.join(current_dir, item)
                
                # Determine if this is the last item in the directory
                is_last = (i == len(dirs) - 1 and len(files) == 0)
                
                # Update prefix for child items
                child_prefix = prefix + ("└── " if is_last else "├── ")
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                # Recursively process subdirectory
                generate_barebones_tree(full_path, next_prefix)
            
            # Now process all files (just show file names, no content)
            for i, item in enumerate(files):
                full_path = os.path.join(current_dir, item)
                # Determine if this is the last item
                is_last = (i == len(files) - 1)
                
                # Update prefix for file
                file_prefix = prefix + ("└── " if is_last else "├── ")
                
                # If in reference tracking mode, mark referenced files
                if reference_tracking_mode and full_path in referenced_files:
                    output.append(f"{file_prefix}📄 {item} [REFERENCED]")
                else:
                    output.append(f"{file_prefix}📄 {item}")

            return True

        except Exception:
            return False
    
    # Generate the barebones tree structure
    generate_barebones_tree(root_dir)
    
    # Add separator between barebones tree and detailed tree
    if priority_folders:
        output.append("\nPrioritized Folders (in order):")
        for i, folder in enumerate(priority_folders):
            output.append(f"  {i+1}. {folder}")
    
    if priority_files:
        output.append("\nPrioritized Files (in order):")
        for i, file in enumerate(priority_files):
            output.append(f"  {i+1}. {file}")
    
    # Always process the directory content regardless of token estimation
    output.append("\nDETAILED FILE TREE WITH CONTENTS")
    output.append("-" * 80)
    process_directory(root_dir)
    
    # Add token information at the end if enabled
    if enable_token_estimation and token_info:
        output.append("\n" + "=" * 80 + "\n")
        output.append("TOKEN ESTIMATION DETAILS")
        output.append("-" * 80)
        output.append(token_info)
        
        # Estimate tokens in the output file too
        output_text = "\n".join(output)
        output_tokens = token_estimator.estimate_tokens_for_text(output_text, token_model, token_method)
        
        output.append("\nToken Estimation for Output File:")
        output.append(f"Estimated tokens in this file: {output_tokens:,}")
        
        if token_results and token_results['total_tokens'] > 0:
            # Calculate and display the ratio
            ratio = output_tokens / token_results['total_tokens']
            change = output_tokens - token_results['total_tokens']
            change_pct = (change / token_results['total_tokens']) * 100
            
            output.append(f"Change from raw files: {change:+,} tokens ({change_pct:+.1f}%)")
            output.append(f"Output/Raw ratio: {ratio:.2f}")
            
            # Create a dict to mimic format expected by compare_token_estimates
            token_output_estimate = {
                "total_tokens": output_tokens,
                "processed_files": 1  # Just one output file
            }
            
            # Add comparison summary
            comparison = token_estimator.compare_token_estimates(token_results, token_output_estimate)
            output.append("\n" + comparison)
    
    # Write to output file
    success, error = safe_write_file(output_file, output)
    if not success:
        return f"Error: {error}"

    result = f"Text tree file generated successfully at {os.path.abspath(output_file)}"
    
    # Add token information to the result message
    if enable_token_estimation and token_results:
        result += f"\nEstimated tokens in raw files: {token_results['total_tokens']:,}"
        if token_output_estimate:
            result += f"\nEstimated tokens in output file: {token_output_estimate['total_tokens']:,}"
    
    return result


def process_file_content(file_path, lines, hide_binary=False, smart_truncate=False, 
                       hide_repeated=False, max_line_length=300):
    """Process file content with efficiency options"""
    
    # Check if it's a binary file and we should hide binary content
    if hide_binary and is_binary_file(file_path):
        return ["[Binary file content not shown]"]
    
    # Apply smart truncation if enabled
    if smart_truncate:
        lines = [smart_truncate_line(line, max_line_length) for line in lines]
    
    # Collapse repeated sections if enabled
    if hide_repeated:
        lines = collapse_repeated_sections(lines)
    
    return lines
def clean_file_content(file_path, content_lines, remove_comments=False, exclude_empty_lines=False):
    """
    Clean file content by removing comments and empty lines if enabled.
    
    Args:
        file_path: Path to the file
        content_lines: List of content lines
        remove_comments: Whether to remove comments
        exclude_empty_lines: Whether to exclude empty lines
        
    Returns:
        List of cleaned content lines
    """
    if not (remove_comments or exclude_empty_lines):
        return content_lines
        
    # Get file extension
    _, ext = os.path.splitext(file_path.lower())
    
    # Process content based on settings and file type
    processed_lines = content_lines.copy()
    
    # Step 1: Remove comments if enabled
    if remove_comments:
        processed_lines = remove_code_comments(processed_lines, ext)
    
    # Step 2: Exclude empty lines if enabled
    if exclude_empty_lines:
        processed_lines = [line for line in processed_lines if line.strip()]
        
    return processed_lines

def remove_code_comments(lines, ext):
    """
    Remove comments from code based on file extension.
    
    Args:
        lines: List of content lines
        ext: File extension
        
    Returns:
        List of lines with comments removed
    """
    # Join lines to handle multi-line comments
    content = '\n'.join(lines)
    
    # C-style languages (C, C++, C#, Java, JavaScript, etc.)
    if ext in ['.c', '.cpp', '.cs', '.h', '.hpp', '.java', '.js', '.ts', '.php', '.swift']:
        # Remove multi-line comments (/* */)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        # Remove single-line comments (// and ///)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    
    # Python, Ruby, Bash, etc.
    elif ext in ['.py', '.rb', '.sh', '.bash', '.yml', '.yaml']:
        # Remove single-line comments (#)
        content = re.sub(r'#.*?$', '', content, flags=re.MULTILINE)
    
    # HTML/XML
    elif ext in ['.html', '.htm', '.xml', '.svg', '.jsp', '.aspx']:
        # Remove HTML/XML comments (<!-- -->)
        content = re.sub(r'<!--[\s\S]*?-->', '', content)
    
    # CSS
    elif ext in ['.css', '.scss', '.less']:
        # Remove CSS comments (/* */)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    
    # SQL
    elif ext in ['.sql']:
        # Remove SQL single-line comments (--)
        content = re.sub(r'--.*?$', '', content, flags=re.MULTILINE)
        # Remove SQL multi-line comments (/* */)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    
    # Return the content split back into lines
    return content.split('\n')

def export_as_html(output_lines, output_file):
    """
    Export the file tree as HTML with basic syntax highlighting
    
    Args:
        output_lines: List of text lines
        output_file: Path to save the HTML file
    """
    html_output = ['<!DOCTYPE html>',
                  '<html>',
                  '<head>',
                  '    <title>File Tree</title>',
                  '    <style>',
                  '        body { font-family: monospace; background-color: #f5f5f5; padding: 20px; }',
                  '        .tree { white-space: pre; }',
                  '        .dir { color: #0066cc; font-weight: bold; }',
                  '        .file { color: #333; }',
                  '        .referenced { color: #008800; font-weight: bold; }',
                  '        .content { margin-left: 20px; border-left: 1px solid #ccc; padding-left: 10px; }',
                  '        .content-header { color: #666; }',
                  '        .line-number { color: #999; margin-right: 10px; }',
                  '        .code { color: #333; }',
                  '        .separator { color: #999; }',
                  '    </style>',
                  '</head>',
                  '<body>',
                  '    <div class="tree">']
    
    for line in output_lines:
        if line.strip().startswith("📁"):
            # Directory line
            html_line = f'<div class="dir">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        elif "[REFERENCED]" in line and line.strip().startswith("📄"):
            # Referenced file line
            html_line = f'<div class="referenced">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        elif line.strip().startswith("📄"):
            # File line
            html_line = f'<div class="file">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        elif "│ FILE CONTENT:" in line:
            # Content header
            html_line = f'<div class="content-header">{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        elif "│" in line and "│" in line[line.find("│")+1:]:
            # Line with content
            parts = line.split("│", 2)
            if len(parts) >= 3 and parts[1].strip().isdigit():
                # Line with line number
                indent = parts[0]
                line_num = parts[1].strip()
                code = parts[2].replace("<", "&lt;").replace(">", "&gt;")
                html_line = f'<div><span>{indent}</span><span class="line-number">│ {line_num} │</span><span class="code">{code}</span></div>'
            else:
                html_line = f'<div>{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        elif "=" * 10 in line or "-" * 10 in line:
            # Separator line
            html_line = f'<div class="separator">{line}</div>'
        else:
            # Regular line
            html_line = f'<div>{line.replace("<", "&lt;").replace(">", "&gt;")}</div>'
        
        html_output.append("        " + html_line)
    
    html_output.extend([
        '    </div>',
        '</body>',
        '</html>'
    ])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_output))

def export_as_markdown(output_lines, output_file):
    """
    Export the file tree as Markdown
    
    Args:
        output_lines: List of text lines
        output_file: Path to save the Markdown file
    """
    md_output = []
    
    # Add header
    if output_lines and "File Structure" in output_lines[0]:
        md_output.append(f"# {output_lines[0]}")
        md_output.append("")
    
    # Add metadata
    metadata_lines = []
    for line in output_lines[1:5]:
        if "=" * 10 in line:
            continue
        if line.strip():
            metadata_lines.append(line)
    
    if metadata_lines:
        md_output.append("## Metadata")
        md_output.append("")
        for line in metadata_lines:
            md_output.append(f"{line}")
        md_output.append("")
    
    # Process directory structure
    in_directory_section = False
    in_detailed_section = False
    in_file_content = False
    
    for line in output_lines:
        if "DIRECTORY STRUCTURE SUMMARY" in line:
            md_output.append("## Directory Structure")
            md_output.append("")
            in_directory_section = True
            continue
        
        if "DETAILED FILE TREE WITH CONTENTS" in line:
            md_output.append("## Detailed File Tree")
            md_output.append("")
            in_directory_section = False
            in_detailed_section = True
            continue
        
        if "REFERENCE TRACKING SUMMARY" in line:
            md_output.append("## Reference Tracking Summary")
            md_output.append("")
            in_directory_section = False
            continue
            
        if "=" * 10 in line or "-" * 10 in line:
            continue
            
        if in_directory_section or in_detailed_section:
            if line.strip().startswith("📁"):
                # Directory line - count indentation to determine level
                indent_level = line.find("📁") // 4
                spaces = "    " * indent_level
                dir_name = line.strip().replace("📁 ", "")
                md_output.append(f"{spaces}- **{dir_name}**")
                
            elif line.strip().startswith("📄"):
                # File line
                indent_level = line.find("📄") // 4
                spaces = "    " * indent_level
                file_parts = line.strip().replace("📄 ", "").split(" (", 1)
                file_name = file_parts[0]
                file_info = f" ({file_parts[1]}" if len(file_parts) > 1 else ""
                
                # Check if it's a referenced file
                if "[REFERENCED]" in line:
                    md_output.append(f"{spaces}- **{file_name}{file_info}** (Referenced)")
                else:
                    md_output.append(f"{spaces}- {file_name}{file_info}")
                
            elif "FILE CONTENT:" in line:
                # Start of file content
                file_name = line.split("FILE CONTENT:", 1)[1].strip()
                md_output.append(f"### File: {file_name}")
                md_output.append("")
                md_output.append("```")
                in_file_content = True
                
            elif "└─" in line and in_file_content:
                # End of file content
                md_output.append("```")
                md_output.append("")
                in_file_content = False
                
            elif in_file_content and "│" in line:
                # File content line - extract the actual content
                parts = line.split("│", 2)
                if len(parts) >= 3:
                    content = parts[2]
                    md_output.append(content)
        else:
            # Include other lines like reference summaries
            md_output.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_output))


def format_size(size_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def export_as_json(output_lines, output_file):
    """
    Export the file tree as JSON
    
    Args:
        output_lines: List of text lines
        output_file: Path to save the JSON file
    """
    import json
    
    # Extract root directory from output
    root_dir = ""
    if output_lines and "File Structure -" in output_lines[0]:
        root_dir = output_lines[0].replace("File Structure -", "").strip()
    
    # Build tree structure
    file_tree = {
        "metadata": {
            "root": root_dir,
            "scan_date": "",
            "extensions": []
        },
        "tree": {},
        "reference_tracking": {
            "enabled": False,
            "files": []
        }
    }
    
    # Extract metadata
    for line in output_lines[1:5]:
        if "Scan Date:" in line:
            file_tree["metadata"]["scan_date"] = line.replace("Scan Date:", "").strip()
        elif "Extensions:" in line:
            extensions = line.replace("Extensions:", "").strip()
            file_tree["metadata"]["extensions"] = [ext.strip() for ext in extensions.split(",")]
        elif "Reference Tracking: Enabled" in line:
            file_tree["reference_tracking"]["enabled"] = True
    
    # Process tree structure
    current_path = []
    current_node = file_tree["tree"]
    
    in_detailed_section = False
    in_file_content = False
    current_file = None
    current_file_content = []
    
    for line in output_lines:
        if "DETAILED FILE TREE WITH CONTENTS" in line:
            in_detailed_section = True
            continue
            
        if not in_detailed_section:
            # Try to extract reference tracking info
            if "Total referenced files:" in line:
                count = line.replace("Total referenced files:", "").strip()
                file_tree["reference_tracking"]["count"] = int(count)
            continue
            
        if in_file_content:
            if "└─" in line:
                # End of file content
                current_node[current_file]["content"] = "\n".join(current_file_content)
                in_file_content = False
                current_file = None
                current_file_content = []
            elif "│" in line:
                # File content line - extract the actual content
                parts = line.split("│", 2)
                if len(parts) >= 3:
                    # Remove line number, keep only the content
                    content = parts[2].strip()
                    current_file_content.append(content)
            continue
            
        # Process directory and file lines
        if line.strip().startswith("📁"):
            # Directory line
            indent = line.find("📁")
            level = indent // 4
            
            # Update current path based on level
            current_path = current_path[:level]
            dir_name = line.strip().replace("📁 ", "").split(" (")[0]
            current_path.append(dir_name)
            
            # Navigate to current node
            current_node = file_tree["tree"]
            for path_part in current_path:
                if path_part not in current_node:
                    current_node[path_part] = {}
                current_node = current_node[path_part]
                
        elif line.strip().startswith("📄"):
            # File line
            file_parts = line.strip().replace("📄 ", "").split(" (", 1)
            file_name = file_parts[0]
            file_info = file_parts[1].rstrip(")") if len(file_parts) > 1 else ""
            
            # Check if it's a referenced file
            is_referenced = "[REFERENCED]" in line
            
            # Add file to current node
            current_node[file_name] = {
                "type": "file",
                "info": file_info,
                "referenced": is_referenced,
                "content": ""
            }
            
            # Add to reference tracking list if referenced
            if is_referenced:
                file_path = "/".join(current_path + [file_name])
                file_tree["reference_tracking"]["files"].append(file_path)
            
        elif "FILE CONTENT:" in line:
            # Start of file content
            current_file = line.split("FILE CONTENT:", 1)[1].strip()
            in_file_content = True
            current_file_content = []
    
    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(file_tree, f, indent=2)
def is_binary_file(file_path):
    """
    Check if a file is binary by reading the first few bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file appears to be binary, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first 8KB of the file
            chunk = f.read(8192)
            # Check for null bytes which typically indicate binary content
            if b'\x00' in chunk:
                return True
                
            # Count printable vs non-printable characters
            printable_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in (9, 10, 13))  # tab, LF, CR
            if printable_chars < len(chunk) * 0.8:  # If less than 80% printable, consider it binary
                return True
                
        return False
    except Exception:
        # If there's an error, assume it's not binary
        return False

def smart_truncate_line(line, max_length=80):
    """
    Intelligently truncate a line to preserve important content.
    
    Args:
        line: The line to truncate
        max_length: Maximum desired length
        
    Returns:
        Truncated line with ellipsis if needed
    """
    if len(line) <= max_length:
        return line
        
    # Special handling for different line types
    
    # 1. Try to preserve function definitions and declarations
    if re.match(r'^\s*(public|private|protected|internal|static|void|function|def|class|interface|struct|enum)\s+\w+', line):
        # Find opening parenthesis
        paren_pos = line.find('(')
        if paren_pos > 0:
            # Find position of last parenthesis
            last_paren = line.rfind(')')
            if last_paren > paren_pos:
                # Calculate what we can show
                prefix_end = min(paren_pos + 1, max_length - 10)
                prefix = line[:prefix_end]
                
                suffix_start = max(last_paren - 5, prefix_end)
                suffix = line[suffix_start:]
                
                if len(prefix) + len(suffix) < max_length:
                    return prefix + "..." + suffix
                else:
                    return prefix + "..."
    
    # 2. Try to preserve imports, using statements, etc.
    if re.match(r'^\s*(import|using|require|include|from)\s+', line):
        return line[:max_length-3] + "..."
    
    # 3. Preserve assignment statements by showing beginning and end
    if '=' in line:
        pos = line.find('=')
        if pos > 0 and pos < max_length - 10:
            prefix = line[:pos+1]
            suffix = line[-(max_length-len(prefix)-3):]
            if len(prefix) + len(suffix) < max_length:
                return prefix + "..." + suffix
    
    # 4. Default truncation with ellipsis
    return line[:max_length-3] + "..."

def collapse_repeated_sections(lines, threshold=4):
    """
    Identify and collapse repeated sections of code.
    
    Args:
        lines: List of content lines
        threshold: Minimum number of identical lines to trigger collapse
        
    Returns:
        List of lines with repeated sections collapsed
    """
    if not lines or len(lines) < threshold * 2:
        return lines
        
    result = []
    i = 0
    
    while i < len(lines):
        # Check for repeating patterns starting from this line
        repeated = False
        
        # Try different pattern lengths
        for pattern_len in range(1, min(10, len(lines) - i)):
            # Extract pattern
            pattern = lines[i:i+pattern_len]
            
            # Count repetitions
            repetitions = 1
            j = i + pattern_len
            
            while j + pattern_len <= len(lines) and lines[j:j+pattern_len] == pattern:
                repetitions += 1
                j += pattern_len
            
            # If pattern repeats enough times, collapse it
            if repetitions >= threshold and pattern_len * repetitions >= threshold:
                result.extend(pattern)  # Add pattern once
                result.append(f"... [above pattern repeated {repetitions-1} more times]")
                i = j  # Skip to end of repeated section
                repeated = True
                break
        
        if not repeated:
            # If no repeating pattern found, add the line and continue
            result.append(lines[i])
            i += 1
    
    return result

def safe_read_file(file_path, max_lines=None, remove_comments=False, exclude_empty_lines=False):
    """
    Safely read a file with proper error handling and content preprocessing.
    
    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read (None for all)
        remove_comments: Whether to remove comments
        exclude_empty_lines: Whether to exclude empty lines
            
    Returns:
        Tuple of (success, content_lines, error_message)
    """
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... (truncated after {max_lines} lines)")
                        break
                    lines.append(line.rstrip('\r\n'))
            else:
                lines = f.read().splitlines()
            
            # Clean file content (remove comments and/or empty lines)
            lines = clean_file_content(file_path, lines, remove_comments, exclude_empty_lines)
            
            # If the file is now empty after processing, add a note
            if not lines:
                lines = ["[File content empty after processing]"]
                
            return True, lines, None
    except UnicodeDecodeError:
        try:
            # Try with system default encoding
            with open(file_path, 'r') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"... (truncated after {max_lines} lines)")
                            break
                        lines.append(line.rstrip('\r\n'))
                    return True, lines, None
                else:
                    return True, f.read().splitlines(), None
        except UnicodeDecodeError:
            # Try binary mode and decode as far as possible
            try:
                with open(file_path, 'rb') as f:
                    binary_data = f.read()
                    # Try to decode binary data, ignoring errors
                    text = binary_data.decode('utf-8', errors='replace')
                    lines = text.splitlines()
                    if max_lines and len(lines) > max_lines:
                        lines = lines[:max_lines]
                        lines.append(f"... (truncated after {max_lines} lines)")
                    return True, lines, "Warning: Binary file or encoding issues, some characters may be replaced"
            except Exception as e:
                return False, [], f"Error reading file: {str(e)}"
    except PermissionError:
        return False, [], "Permission denied when trying to read file"
    except FileNotFoundError:
        return False, [], "File not found"
    except Exception as e:
        return False, [], f"Error reading file: {str(e)}"

def safe_write_file(file_path, content, mode='w'):
    """
    Safely write content to a file with proper error handling
    
    Args:
        file_path: Path to the file
        content: Content to write (string or list of lines)
        mode: File mode ('w' for write, 'a' for append)
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, mode, encoding='utf-8') as f:
            if isinstance(content, list):
                f.write('\n'.join(content))
            else:
                f.write(content)
        return True, None
    except PermissionError:
        return False, "Permission denied when trying to write file"
    except FileNotFoundError:
        return False, "Cannot create file in the specified location"
    except Exception as e:
        return False, f"Error writing file: {str(e)}"


# Example usage
if __name__ == "__main__":
    args = parse_args()
    
    # Convert args to the expected format
    extensions = set(args.extensions)
    blacklist_folders = set(args.blacklist_folders)
    blacklist_files = set(args.blacklist_files)
    
    try:
        # Generate the file tree
        result = create_file_tree(
            args.root_dir,
            extensions,
            args.output_file,
            blacklist_folders=blacklist_folders,
            blacklist_files=blacklist_files,
            max_lines=args.max_lines,
            max_line_length=args.max_line_length,
            compact_view=args.compact,
            ultra_compact_view=args.ultra_compact if hasattr(args, 'ultra_compact') else False,
            remove_comments=args.remove_comments if hasattr(args, 'remove_comments') else False,
            exclude_empty_lines=args.exclude_empty_lines if hasattr(args, 'exclude_empty_lines') else False,
            priority_folders=args.priority_folders,
            priority_files=args.priority_files,
            enable_token_estimation=args.enable_token_estimation if hasattr(args, 'enable_token_estimation') else False,
            token_model=args.token_model if hasattr(args, 'token_model') else "claude-3.5-sonnet",
            token_method=args.token_method if hasattr(args, 'token_method') else "char"
        )
        
        # If format is not txt, convert to the desired format
        if args.format != 'txt':
            with open(args.output_file, 'r', encoding='utf-8') as f:
                output_lines = f.read().splitlines()
            
            # Change output file extension
            output_base, _ = os.path.splitext(args.output_file)
            if args.format == 'html':
                new_output = f"{output_base}.html"
                export_as_html(output_lines, new_output)
            elif args.format == 'markdown':
                new_output = f"{output_base}.md"
                export_as_markdown(output_lines, new_output)
            elif args.format == 'json':
                new_output = f"{output_base}.json"
                export_as_json(output_lines, new_output)
            
            # Delete the temporary text file
            if args.verbose:
                print(f"Converting {args.output_file} to {new_output}")
            os.remove(args.output_file)
            result = f"File tree generated successfully in {args.format.upper()} format at {os.path.abspath(new_output)}"
        
        print(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)