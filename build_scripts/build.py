import os
import shutil
import subprocess
import sys

# Get the correct paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'build_scripts' else SCRIPT_DIR
SRC_DIR = os.path.join(ROOT_DIR, "src")

def clean_build_folders():
    """Remove build artifacts"""
    folders_to_remove = ['build', 'dist', '__pycache__']
    for folder in folders_to_remove:
        folder_path = os.path.join(ROOT_DIR, folder)
        if os.path.exists(folder_path):
            print(f"Removing {folder_path}...")
            shutil.rmtree(folder_path)
    
    # Remove .spec file if it exists
    spec_file = os.path.join(ROOT_DIR, "file_tree_gui.spec")
    if os.path.exists(spec_file):
        print(f"Removing {spec_file}...")
        os.remove(spec_file)

def build_executable():
    """Build the executable using PyInstaller"""
    # Check if PyInstaller is installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                             stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Navigate to the root directory
    os.chdir(ROOT_DIR)
    print(f"Building from directory: {os.getcwd()}")
    
    # Check if source directory exists
    if not os.path.exists(SRC_DIR):
        print(f"Error: Source directory not found at {SRC_DIR}")
        sys.exit(1)
    
    # Find the main script in the src directory
    main_script = os.path.join(SRC_DIR, "file_tree_gui.py")
    if not os.path.exists(main_script):
        print(f"Error: Main script not found at {main_script}")
        sys.exit(1)
    else:
        print(f"Found main script at {main_script}")
    
    # Check for resources
    icon_path = os.path.join(ROOT_DIR, "resources", "icon.ico")
    if not os.path.exists(icon_path):
        # Try alternative locations
        alt_locations = [
            os.path.join(ROOT_DIR, "icon.ico"),
            os.path.join(SRC_DIR, "icon.ico")
        ]
        
        for loc in alt_locations:
            if os.path.exists(loc):
                icon_path = loc
                break
        
        if not os.path.exists(icon_path):
            print("Warning: icon.ico not found, proceeding without an icon")
            icon_param = []
        else:
            print(f"Found icon at {icon_path}")
            icon_param = ["--icon", icon_path]
    else:
        print(f"Found icon at {icon_path}")
        icon_param = ["--icon", icon_path]
    
    # Check for version info
    version_path = os.path.join(ROOT_DIR, "version_info.txt")
    if os.path.exists(version_path):
        version_param = ["--version-file", version_path]
    else:
        version_param = []
    
    # Add paths to ensure all imports work correctly
    # This is crucial when files are in the src directory
    path_param = ["--paths", SRC_DIR]
    
    # Construct the command
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed"]
    cmd.extend(path_param)
    cmd.extend(icon_param)
    cmd.extend(version_param)
    cmd.append(main_script)
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

def rename_executable():
    """Rename the executable to a more user-friendly name"""
    dist_dir = os.path.join(ROOT_DIR, "dist")
    if os.name == 'nt':  # Windows
        source = os.path.join(dist_dir, "file_tree_gui.exe")
        dest = os.path.join(dist_dir, "FileTreeGenerator.exe")
    else:  # macOS/Linux
        source = os.path.join(dist_dir, "file_tree_gui")
        dest = os.path.join(dist_dir, "FileTreeGenerator")
    
    if os.path.exists(source):
        os.rename(source, dest)
        print(f"Renamed executable to {dest}")
    else:
        print(f"Warning: Could not find {source} to rename")

if __name__ == "__main__":
    clean_build_folders()
    build_executable()
    rename_executable()
    print("\nBuild completed successfully!")
    print("Executable is located in the 'dist' folder.")