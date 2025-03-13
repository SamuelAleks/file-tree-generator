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
    # Create test directory structure
    test_dir = "test_project"
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
        f"python file_tree_generator.py {test_dir} test_output.txt --extensions .py .md --compact",
        "Core functionality"
    )
    
    # Test GUI (manual testing required)
    print("\nLaunching GUI for manual testing. Close the window when done.")
    subprocess.Popen("python file_tree_gui.py")
    input("Press Enter when done with GUI testing...")
    
    # Test building executable
    run_command(
        "python build.py",
        "Building executable"
    )
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()