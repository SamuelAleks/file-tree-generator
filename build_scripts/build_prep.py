# build_prep.py
import os
import shutil

def prepare_for_installer():
    """Prepare files for the installer"""
    
    # Create docs directory if it doesn't exist
    os.makedirs("docs", exist_ok=True)
    
    # Convert README.md to README.txt if needed
    if os.path.exists("README.md") and not os.path.exists("docs/README.txt"):
        print("Converting README.md to README.txt...")
        with open("README.md", "r", encoding="utf-8") as md_file:
            content = md_file.read()
            # Simple markdown to text conversion
            content = content.replace("# ", "").replace("## ", "").replace("### ", "")
            
            with open("docs/README.txt", "w", encoding="utf-8") as txt_file:
                txt_file.write(content)
    
    # Copy LICENSE to LICENSE.txt if needed
    if os.path.exists("LICENSE") and not os.path.exists("docs/LICENSE.txt"):
        print("Copying LICENSE to LICENSE.txt...")
        shutil.copy("LICENSE", "docs/LICENSE.txt")
    
    # Create installer directory
    os.makedirs("installer", exist_ok=True)
    
    print("Files prepared for installer")

if __name__ == "__main__":
    prepare_for_installer()