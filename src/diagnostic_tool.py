import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import traceback

def run_diagnostic():
    """Run diagnostics on the code visualizer modules"""
    print("Running File Tree Generator visualizer diagnostics...")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if src directory is in the path
    src_in_path = any(os.path.basename(p) == 'src' for p in sys.path)
    print(f"'src' directory in sys.path: {src_in_path}")
    
    if not src_in_path:
        # Add the src directory to the path if it's not already there
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(current_dir) != 'src':
            parent_dir = os.path.dirname(current_dir)
            src_dir = os.path.join(parent_dir, 'src')
            if os.path.exists(src_dir):
                sys.path.append(src_dir)
                print(f"Added {src_dir} to sys.path")
    
    # Check if required modules exist
    modules_to_check = [
        'code_visualizer',
        'reference_tracking',
        'csharp_parser',
        'file_tree_generator',
        'file_tree_gui'
    ]
    
    print("\nChecking for required modules:")
    all_modules_found = True
    
    for module_name in modules_to_check:
        module_path = None
        for path_entry in sys.path:
            possible_path = os.path.join(path_entry, f"{module_name}.py")
            if os.path.exists(possible_path):
                module_path = possible_path
                break
        
        if module_path:
            print(f"✓ {module_name} found at {module_path}")
        else:
            print(f"✗ {module_name} not found in sys.path")
            all_modules_found = False
    
    if not all_modules_found:
        print("\nWarning: Some required modules were not found.")
        print("Make sure you're running this script from the project directory.")
    
    # Try to import the code_visualizer module
    print("\nAttempting to import modules:")
    
    try:
        print("Importing code_visualizer...")
        import code_visualizer
        print(f"✓ code_visualizer imported successfully (version: {getattr(code_visualizer, '__version__', 'unknown')})")
        
        # Check for required classes
        required_classes = [
            'SynchronizedTextEditor',
            'CodeElement',
            'CodeReference',
            'CodeRelationshipVisualizer',
            'CodeSnippetVisualizer',
            'CSharpCodeViewer',
            'add_code_visualizer_to_app'
        ]
        
        missing_classes = []
        for cls_name in required_classes:
            if not hasattr(code_visualizer, cls_name):
                missing_classes.append(cls_name)
        
        if missing_classes:
            print(f"✗ The following classes are missing from code_visualizer: {', '.join(missing_classes)}")
        else:
            print("✓ All required classes found in code_visualizer")
        
    except ImportError as e:
        print(f"✗ Failed to import code_visualizer: {str(e)}")
    except Exception as e:
        print(f"✗ Error when importing code_visualizer: {str(e)}")
        traceback.print_exc()
    
    try:
        print("\nImporting reference_tracking...")
        import reference_tracking
        print(f"✓ reference_tracking imported successfully")
        
        # Check for ReferenceTrackingManager class
        if hasattr(reference_tracking, 'ReferenceTrackingManager'):
            print("✓ ReferenceTrackingManager class found")
        else:
            print("✗ ReferenceTrackingManager class not found in reference_tracking")
        
    except ImportError as e:
        print(f"✗ Failed to import reference_tracking: {str(e)}")
    except Exception as e:
        print(f"✗ Error when importing reference_tracking: {str(e)}")
        traceback.print_exc()
    
    try:
        print("\nImporting csharp_parser...")
        import csharp_parser
        print(f"✓ csharp_parser imported successfully")
        
        # Check for CSharpReferenceTracker class
        if hasattr(csharp_parser, 'CSharpReferenceTracker'):
            print("✓ CSharpReferenceTracker class found")
        else:
            print("✗ CSharpReferenceTracker class not found in csharp_parser")
        
    except ImportError as e:
        print(f"✗ Failed to import csharp_parser: {str(e)}")
    except Exception as e:
        print(f"✗ Error when importing csharp_parser: {str(e)}")
        traceback.print_exc()
    
    # Check Tkinter capabilities
    print("\nChecking Tkinter capabilities:")
    
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Check if ttk is available
        ttk_frame = ttk.Frame(root)
        print("✓ ttk module is available")
        
        # Check if filedialog is available
        print("Testing filedialog...")
        # Don't actually open the dialog, just check if the module is available
        print("✓ filedialog module is available")
        
        # Check if messagebox is available
        print("Testing messagebox...")
        # Don't actually show a messagebox, just check if the module is available
        print("✓ messagebox module is available")
        
        root.destroy()
    except Exception as e:
        print(f"✗ Error testing Tkinter: {str(e)}")
        traceback.print_exc()
    
    # Try to create a test visualizer
    print("\nTesting visualizer creation:")
    
    try:
        # Import only when needed to avoid errors stopping the whole diagnostic
        from code_visualizer import CodeRelationshipVisualizer
        
        class MockReferenceTracker:
            def __init__(self):
                self.file_info = {}
                self.tracker = type('MockTracker', (), {})()
        
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create a test file
        test_file = "__test_file__.txt"
        with open(test_file, "w") as f:
            f.write("Test file for visualizer diagnostics\n")
        
        try:
            print(f"Creating test visualizer for {test_file}...")
            mock_tracker = MockReferenceTracker()
            visualizer = CodeRelationshipVisualizer(root, mock_tracker, test_file)
            print("✓ Test visualizer created successfully")
            
            # Clean up
            visualizer.destroy()
        except Exception as e:
            print(f"✗ Error creating test visualizer: {str(e)}")
            traceback.print_exc()
            
        # Clean up
        root.destroy()
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except ImportError as e:
        print(f"✗ Could not import CodeRelationshipVisualizer: {str(e)}")
    except Exception as e:
        print(f"✗ Error during visualizer testing: {str(e)}")
        traceback.print_exc()
    
    print("\nDiagnostic complete. See above for any issues that need to be addressed.")

if __name__ == "__main__":
    run_diagnostic()