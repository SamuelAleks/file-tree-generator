import os
import datetime
import argparse

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
    
    return parser.parse_args()

def create_file_tree(root_dir, extensions, output_file, blacklist_folders=None, blacklist_files=None, 
                  max_lines=1000, max_line_length=300, compact_view=False,
                  priority_folders=None, priority_files=None):
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
    """
    # Initialize lists
    blacklist_folders = set(blacklist_folders or [])
    blacklist_files = set(blacklist_files or [])
    priority_folders = priority_folders or []
    priority_files = priority_files or []
    
    # Initialize the output string
    output = []
    output.append(f"File Structure - {os.path.abspath(root_dir)}")
    output.append(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"Extensions: {', '.join(extensions)}")
    output.append("=" * 80)
    output.append("")
    
    relevant_files_cache = {}
    def has_relevant_files(dir_path, ext_set):
        """Check if directory or its subdirectories contain relevant files (with caching)"""
        # Check cache first
        if dir_path in relevant_files_cache:
            return relevant_files_cache[dir_path]
        
        try:
            # Check if directory is blacklisted
            dir_name = os.path.basename(dir_path)
            if dir_name in blacklist_folders:
                relevant_files_cache[dir_path] = False
                return False
            
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if os.path.isfile(full_path):
                    if item in blacklist_files:
                        continue
                    if any(item.endswith(ext) for ext in ext_set):
                        relevant_files_cache[dir_path] = True
                        return True
                elif os.path.isdir(full_path):
                    if has_relevant_files(full_path, ext_set):
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
                    if item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
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
                
                # Update prefix for child items
                child_prefix = prefix + ("└── " if is_last else "├── ")
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                # Recursively process subdirectory
                process_directory(full_path, next_prefix)
            
            # Now process all files
            for i, item in enumerate(files):
                full_path = os.path.join(current_dir, item)
                
                # Determine if this is the last item
                is_last = (i == len(files) - 1)
                
                # Update prefix for file
                file_prefix = prefix + ("└── " if is_last else "├── ")
                content_prefix = prefix + ("    " if is_last else "│   ")
                
                # Add file to tree
                file_size = os.path.getsize(full_path)
                last_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d %H:%M:%S")
                
                output.append(f"{file_prefix}📄 {item} ({format_size(file_size)}, {last_modified})")
                
                # Add file content with formatting based on compact_view flag
                try:
                    success, lines, error = safe_read_file(full_path, max_lines)
                    if not success:
                        if compact_view:
                            output.append(f"---[ERROR: {error}]---")
                        else:
                            output.append(f"{content_prefix}│ ERROR: {error}")
                            output.append(f"{content_prefix}└{'─' * 70}")
                        continue
                        
                        if compact_view:
                            # Compact view with minimal decorative characters
                            output.append(f"---[FILE: {item}]---")
                            for line_num, line in enumerate(lines, 1):
                                if line_num > max_lines:
                                    output.append(f"...(+{len(lines)-max_lines} more lines)")
                                    break
                                truncated_line = line[:max_line_length] + "..." if len(line) > max_line_length else line
                                output.append(f"{line_num}:{truncated_line}")
                            output.append("---[END]---")
                        else:
                            # Standard view with full formatting
                            # Add content header
                            output.append(f"{content_prefix}┌{'─' * 70}")
                            output.append(f"{content_prefix}│ FILE CONTENT: {item}")
                            output.append(f"{content_prefix}├{'─' * 70}")
                            
                            # Add content with line numbers
                            for line_num, line in enumerate(lines, 1):
                                if line_num > max_lines:
                                    output.append(f"{content_prefix}│ ... (truncated after {max_lines} lines, {len(lines)-max_lines} more lines)")
                                    break
                                truncated_line = line[:max_line_length] + "..." if len(line) > max_line_length else line
                                output.append(f"{content_prefix}│ {line_num:4d} │ {truncated_line}")
                            
                            # Add content footer
                            output.append(f"{content_prefix}└{'─' * 70}")
                except Exception as e:
                    if compact_view:
                        output.append(f"---[ERROR: {str(e)}]---")
                    else:
                        output.append(f"{content_prefix}│ ERROR reading file: {str(e)}")
                        output.append(f"{content_prefix}└{'─' * 70}")

            return True

        except PermissionError:
            output.append(f"{prefix}❌ Permission denied accessing {current_dir}")
            return False
        except Exception as e:
            output.append(f"{prefix}❌ Error processing {current_dir}: {str(e)}")
            return False

    def format_size(size_bytes):
        """Format file size in a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

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
                    if item not in blacklist_files and any(item.endswith(ext) for ext in extensions):
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
                # Determine if this is the last item
                is_last = (i == len(files) - 1)
                
                # Update prefix for file
                file_prefix = prefix + ("└── " if is_last else "├── ")
                
                # Add file to tree (just the name, no details)
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
            
    output.append("\n" + "=" * 80 + "\n")
    output.append("DETAILED FILE TREE WITH CONTENTS")
    output.append("-" * 80)
    
    # Process the root directory
    process_directory(root_dir)

    # Write to output file
    success, error = safe_write_file(output_file, output)
    if not success:
        return f"Error: {error}"

    return f"Text tree file generated successfully at {os.path.abspath(output_file)}"
# Add this to file_tree_generator.py

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
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_output))

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
        "tree": {}
    }
    
    # Extract metadata
    for line in output_lines[1:5]:
        if "Scan Date:" in line:
            file_tree["metadata"]["scan_date"] = line.replace("Scan Date:", "").strip()
        elif "Extensions:" in line:
            extensions = line.replace("Extensions:", "").strip()
            file_tree["metadata"]["extensions"] = [ext.strip() for ext in extensions.split(",")]
    
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
            
            # Add file to current node
            current_node[file_name] = {
                "type": "file",
                "info": file_info,
                "content": ""
            }
            
        elif "FILE CONTENT:" in line:
            # Start of file content
            current_file = line.split("FILE CONTENT:", 1)[1].strip()
            in_file_content = True
            current_file_content = []
    
    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(file_tree, f, indent=2)


def safe_read_file(file_path, max_lines=None):
    """
    Safely read a file with proper error handling
    
    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read (None for all)
        
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
                return True, lines, None
            else:
                return True, f.read().splitlines(), None
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
            priority_folders=args.priority_folders,
            priority_files=args.priority_files
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