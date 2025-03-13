# File Tree Generator

A powerful tool to generate visual text representations of directory trees with file contents for documentation, analysis, and code review.

## Overview

File Tree Generator helps developers, project managers, and documentation specialists quickly create comprehensive visual representations of project structures. It recursively traverses directories, generates a tree-like structure, and includes file contents with syntax highlighting.

## Features

- **Visual Directory Structure**: Creates a clean, visual representation of your project's file structure
- **File Content Analysis**: Displays file contents with line numbers
- **Customizable Filtering**: Include/exclude specific file extensions, folders, or files
- **Priority Sorting**: Arrange important folders and files to appear first in the output
- **Compact View**: Toggle between detailed and compact views for cleaner output
- **Configuration Saving**: Save your settings for quick reuse
- **Automatic Updates**: Built-in update checker ensures you always have the latest version

## Installation

### Windows
1. Download the latest `FileTreeGenerator_Setup.exe` from the [Releases](https://github.com/PaapeCompanies/file-tree-generator/releases) page
2. Run the installer and follow the on-screen instructions
3. Launch the application from your Start menu

### From Source
1. Clone the repository:
   ```
   git clone https://github.com/PaapeCompanies/file-tree-generator.git
   ```
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python src/file_tree_gui.py
   ```

## Usage

1. **Select Root Directory**: Choose the starting directory for your tree
2. **Configure Settings**:
   - Specify file extensions to include (e.g., `.py .js .html`)
   - Add folders to exclude (e.g., `node_modules .git bin`)
   - Add files to exclude (e.g., `thumbs.db desktop.ini`)
   - Set priority folders and files to control their order in the tree
3. **Set Advanced Options**:
   - Maximum lines per file to display
   - Maximum line length before truncation
   - Toggle compact view for cleaner output
4. **Generate Tree**: Click "Generate File Tree" to create your visualization
5. **View Output**: The tool will create a text file with the complete tree that you can view, print, or share

## Command Line Interface

For automation or integration with other tools, you can use the command-line interface:

```
python src/file_tree_generator.py <root_directory> <output_file> --extensions .py .js .html --blacklist-folders node_modules .git
```

Run with the `--help` flag for complete documentation of available options.

## Building from Source

To build the executable:

```
python build_scripts/build.py
```

This will create a standalone executable in the `dist` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

license

## Contact

Paape Companies  

---

Made by Paape Companies