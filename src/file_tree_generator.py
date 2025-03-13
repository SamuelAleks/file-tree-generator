import os
import datetime

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

    def has_relevant_files(dir_path, ext_set):
        """Check if directory or its subdirectories contain relevant files"""
        try:
            # Check if directory is blacklisted
            dir_name = os.path.basename(dir_path)
            if dir_name in blacklist_folders:
                return False
                
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if os.path.isfile(full_path):
                    if item in blacklist_files:
                        continue
                    if any(item.endswith(ext) for ext in ext_set):
                        return True
                elif os.path.isdir(full_path):
                    if has_relevant_files(full_path, ext_set):
                        return True
            return False
        except (PermissionError, OSError):
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
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.splitlines()
                        
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
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    return f"Text tree file generated successfully at {os.path.abspath(output_file)}"

# Example usage
if __name__ == "__main__":
    # Specify your parameters
    target_extensions = {'.cs', '.xaml', '.axaml', '.csproj', '.sln', '.log'}
    root_directory = "C:/Users/SamuelA/source/repos/PaapeConversionKitRefactor/test"
    output_txt = "file_structure.txt"
    
    # Define blacklists
    blacklisted_folders = {'bin', 'obj', 'node_modules', '.git'} #, 'Core', 'Data'
    blacklisted_files = {'desktop.ini', 'thumbs.db', 'README.md'}
    
    use_compact_view = False
    priority_folder_list = ['Views', 'ViewModels', 'Models', 'Services', 'Helpers', 'Converters']
    priority_file_list = ['App.xaml', 'App.xaml.cs', 'MainWindow.xaml', 'MainWindow.xaml.cs']

    try:
        result = create_file_tree(
            root_directory, 
            target_extensions, 
            output_txt,
            blacklist_folders=blacklisted_folders,
            blacklist_files=blacklisted_files,
            compact_view=use_compact_view,
            priority_folders=priority_folder_list,
            priority_files=priority_file_list
        )
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")