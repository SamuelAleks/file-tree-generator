import os
import sys
import subprocess
import shutil
import time

def run_command(command, description):
    print(f"\n{'='*80}\nTesting: {description}\n{'='*80}")
    print(f"Command: {command}")
    
    # Use arguments list instead of shell=True to avoid path issues
    if isinstance(command, str):
        # Split the command into parts
        args = command.split()
    else:
        args = command
        
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Print output for debugging
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
    if result.returncode != 0:
        print(f"❌ Test failed: {description}")
        return False
    print(f"✅ Test passed: {description}")
    return True

def main():
    # Get the correct paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(script_dir)
    parent_dir = os.path.dirname(src_dir)
    
    # Create test directory structure
    test_dir = os.path.join(src_dir, "test_project")
    output_file = os.path.join(src_dir, "test_output.txt")
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    os.makedirs(test_dir)
    os.makedirs(os.path.join(test_dir, "src"))
    os.makedirs(os.path.join(test_dir, "docs"))
    
    with open(os.path.join(test_dir, "test.py"), "w") as f:
        f.write("# Test Python file\nprint('Hello, world!')\n")
    
    with open(os.path.join(test_dir, "README.md"), "w") as f:
        f.write("# Test Project\n\nThis is a test project.\n")
    
    # Test core functionality using arguments list instead of command string
    python_exe = sys.executable
    generator_path = os.path.join(src_dir, 'file_tree_generator.py')
    
    # Use argument list to avoid path issues
    run_command(
        [
            python_exe,
            generator_path,
            test_dir,
            output_file,
            "--extensions", ".py", ".md",
            "--compact"
        ],
        "Core functionality"
    )
    
    # Test GUI (manual testing required)
    print("\nLaunching GUI for manual testing. Close the window when done.")
    gui_path = os.path.join(src_dir, "file_tree_gui.py")
    gui_process = subprocess.Popen([python_exe, gui_path])
    input("Press Enter when done with GUI testing...")
    
    # Ensure GUI process is terminated
    if gui_process.poll() is None:
        gui_process.terminate()
        gui_process.wait(timeout=5)
    
    # Test building executable from the correct directory
    build_script = os.path.join(parent_dir, "build_scripts", "build.py")
    if os.path.exists(build_script):
        run_command(
            [python_exe, build_script],
            "Building executable"
        )
    else:
        print(f"❌ Build script not found at {build_script}")
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()