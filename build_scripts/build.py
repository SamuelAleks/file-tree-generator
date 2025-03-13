import os
import shutil
import subprocess
import sys

def clean_build_folders():
    """Remove build artifacts"""
    folders_to_remove = ['build', 'dist', '__pycache__']
    for folder in folders_to_remove:
        if os.path.exists(folder):
            print(f"Removing {folder}...")
            shutil.rmtree(folder)
    
    # Remove .spec file if it exists
    spec_file = "file_tree_gui.spec"
    if os.path.exists(spec_file):
        print(f"Removing {spec_file}...")
        os.remove(spec_file)

def build_executable():
    """Build the executable using PyInstaller"""
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build the executable
    print("Building executable...")
    if os.path.exists("version_info.txt"):
        # Use version info if available
        cmd = ["pyinstaller", "--onefile", "--windowed", "--icon=icon.ico", 
               "--version-file=version_info.txt", "file_tree_gui.py"]
    else:
        cmd = ["pyinstaller", "--onefile", "--windowed", "--icon=icon.ico", "file_tree_gui.py"]
    
    subprocess.check_call(cmd)

def rename_executable():
    """Rename the executable to a more user-friendly name"""
    source = os.path.join("dist", "file_tree_gui.exe")
    dest = os.path.join("dist", "FileTreeGenerator.exe")
    if os.path.exists(source):
        os.rename(source, dest)
        print(f"Renamed executable to {dest}")

if __name__ == "__main__":
    clean_build_folders()
    build_executable()
    rename_executable()
    print("\nBuild completed successfully!")
    print("Executable is located in the 'dist' folder.")