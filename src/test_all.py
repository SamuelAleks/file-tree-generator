import os
import sys
import subprocess
import shutil
import time

def run_command(command, description):
    print(f"\n{'='*80}\nTesting: {description}\n{'='*80}")
    print(f"Command: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Test failed: {description}")
        return False
    print(f"✅ Test passed: {description}")
    return True

def main():
    # Get the correct paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(script_dir)
    
    # Create test directory structure
    test_dir = os.path.join(src_dir, "test_project")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    os.makedirs(test_dir)
    os.makedirs(os.path.join(test_dir, "src"))
    os.makedirs(os.path.join(test_dir, "docs"))
    
    with open(os.path.join(test_dir, "test.py"), "w") as f:
        f.write("# Test Python file\nprint('Hello, world!')\n")
    
    with open(os.path.join(test_dir, "README.md"), "w") as f:
        f.write("# Test Project\n\nThis is a test project.\n")
    
    # Test core functionality
    run_command(
        f"python {os.path.join(src_dir, 'file_tree_generator.py')} {test_dir} {os.path.join(src_dir, 'test_output.txt')} --extensions .py .md --compact",
        "Core functionality"
    )
    
    # Test GUI (manual testing required)
    print("\nLaunching GUI for manual testing. Close the window when done.")
    gui_process = subprocess.Popen([sys.executable, os.path.join(src_dir, "file_tree_gui.py")])
    input("Press Enter when done with GUI testing...")
    
    # Ensure GUI process is terminated
    if gui_process.poll() is None:
        gui_process.terminate()
        gui_process.wait(timeout=5)
    
    # Test building executable from the correct directory
    build_script = os.path.join(os.path.dirname(src_dir), "build_scripts", "build.py")
    if os.path.exists(build_script):
        run_command(
            f"python {build_script}",
            "Building executable"
        )
    else:
        print(f"❌ Build script not found at {build_script}")
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    if os.path.exists(os.path.join(src_dir, "test_output.txt")):
        os.remove(os.path.join(src_dir, "test_output.txt"))
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()