import os
import shutil
import subprocess
import sys
import time

# Get the correct paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'build_scripts' else SCRIPT_DIR
SRC_DIR = os.path.join(ROOT_DIR, "src")

def rmtree_with_retry(folder_path, max_retries=3, retry_delay=1.0):
    """Remove a directory tree with retry logic for Windows permission issues"""
    # Check if folder exists first
    if not os.path.exists(folder_path):
        print(f"Directory {folder_path} does not exist, no need to remove")
        return True  # Success - nothing to remove
        
    for attempt in range(max_retries):
        try:
            print(f"Removing {folder_path}...")
            shutil.rmtree(folder_path)
            return True  # Success
        except (PermissionError, OSError) as e:
            print(f"Warning: Failed to remove {folder_path} (attempt {attempt+1}/{max_retries})")
            print(f"Error: {str(e)}")
            
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Warning: Could not remove {folder_path}, continuing anyway.")
                return False  # Failed after all retries
    
    return False

def extract_version_for_inno_setup():
    """Extract version from version.py and create a version.iss file for Inno Setup"""
    try:
        # Find the version.py file
        version_file = os.path.join(SRC_DIR, "version.py")
        if not os.path.exists(version_file):
            print(f"Warning: version.py not found at {version_file}")
            return "1.0.0"  # Default version if file not found
            
        # Read the version.py file
        with open(version_file, 'r') as f:
            content = f.read()
            
        # Extract the version using regex
        import re
        match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            print("Warning: VERSION not found in version.py")
            return "1.0.0"  # Default version if version not found
            
        version = match.group(1)
        print(f"Extracted version: {version}")
        
        # Create the version.iss file
        version_iss_path = os.path.join(ROOT_DIR, "version.iss")
        with open(version_iss_path, 'w') as f:
            f.write(f'#define MyAppVersion "{version}"\n')
            
        print(f"Created version.iss with version {version}")
        return version
        
    except Exception as e:
        print(f"Error extracting version: {str(e)}")
        return "1.0.0"  # Default version on error
def clean_build_folders():
    """Remove build artifacts with improved error handling"""
    folders_to_remove = ['build', 'dist', '__pycache__']
    
    for folder in folders_to_remove:
        folder_path = os.path.join(ROOT_DIR, folder)
        rmtree_with_retry(folder_path)
    
    # Remove .spec file if it exists
    spec_file = os.path.join(ROOT_DIR, "file_tree_gui.spec")
    if os.path.exists(spec_file):
        try:
            print(f"Removing {spec_file}...")
            os.remove(spec_file)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not remove {spec_file}: {str(e)}")

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
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {str(e)}")
        return False

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

def create_resources_folder():
    """Create a resources folder if it doesn't exist, and add a default icon"""
    resources_dir = os.path.join(ROOT_DIR, "resources")
    if not os.path.exists(resources_dir):
        print(f"Creating resources directory at {resources_dir}")
        os.makedirs(resources_dir, exist_ok=True)
    
    icon_path = os.path.join(resources_dir, "icon.ico")
    if not os.path.exists(icon_path):
        print("Creating a placeholder icon.ico file")
        # Simple placeholder - just an empty file
        with open(icon_path, 'w') as f:
            f.write("")

if __name__ == "__main__":
    print("Starting build process for File Tree Generator...")
    
    # Ensure resources folder exists
    create_resources_folder()
    
    # Clean build artifacts
    clean_build_folders()

    
    version = extract_version_for_inno_setup()
    
    # Build the executable
    if build_executable():
        rename_executable()
        print("\nBuild completed successfully!")
        print("Executable is located in the 'dist' folder.")
    else:
        print("\nBuild failed. Please check the errors above.")