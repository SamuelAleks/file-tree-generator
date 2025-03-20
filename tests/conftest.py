"""
Pytest configuration and fixtures for File Tree Generator tests.
"""

import os
import sys
import shutil
import pytest
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Constants
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_PROJECTS_DIR = os.path.join(FIXTURES_DIR, "sample_projects")
EXPECTED_OUTPUTS_DIR = os.path.join(FIXTURES_DIR, "expected_outputs")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment once per test session."""
    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Make sure fixtures directories exist
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    os.makedirs(SAMPLE_PROJECTS_DIR, exist_ok=True)
    os.makedirs(EXPECTED_OUTPUTS_DIR, exist_ok=True)
    
    yield
    
    # Clean up after tests
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)


@pytest.fixture
def sample_project():
    """Create a sample test project."""
    project_dir = os.path.join(TEMP_DIR, "sample_project")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
    
    # Create test files
    with open(os.path.join(project_dir, "src", "main.py"), "w") as f:
        f.write("# Main Python file\ndef main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()")
    
    with open(os.path.join(project_dir, "src", "utils.py"), "w") as f:
        f.write("# Utility functions\ndef add(a, b):\n    return a + b")
    
    with open(os.path.join(project_dir, "docs", "README.md"), "w") as f:
        f.write("# Sample Project\n\nThis is a sample project for testing File Tree Generator.")
    
    yield project_dir
    
    # Clean up
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)


@pytest.fixture
def csharp_project():
    """Create a sample C# project for reference tracking tests."""
    project_dir = os.path.join(TEMP_DIR, "csharp_project")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "Models"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "Controllers"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "Views"), exist_ok=True)
    
    # Create a class file
    with open(os.path.join(project_dir, "Models", "User.cs"), "w") as f:
        f.write("""
using System;

namespace SampleApp.Models
{
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        
        public string GetGreeting()
        {
            return $"Hello, {Name}!";
        }
    }
}
""")
    
    # Create a controller file
    with open(os.path.join(project_dir, "Controllers", "UserController.cs"), "w") as f:
        f.write("""
using System;
using SampleApp.Models;

namespace SampleApp.Controllers
{
    public class UserController
    {
        public string GetUserGreeting(int userId)
        {
            var user = new User { Id = userId, Name = "Test User" };
            return user.GetGreeting();
        }
    }
}
""")
    
    # Create a XAML view file
    with open(os.path.join(project_dir, "Views", "UserView.xaml"), "w") as f:
        f.write("""
<UserControl x:Class="SampleApp.Views.UserView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <Grid>
        <TextBlock Text="User View" />
    </Grid>
</UserControl>
""")
    
    # Create the code-behind file
    with open(os.path.join(project_dir, "Views", "UserView.xaml.cs"), "w") as f:
        f.write("""
using System;
using SampleApp.Controllers;

namespace SampleApp.Views
{
    public partial class UserView
    {
        private UserController _controller;
        
        public UserView()
        {
            InitializeComponent();
            _controller = new UserController();
        }
        
        public void ShowGreeting(int userId)
        {
            var greeting = _controller.GetUserGreeting(userId);
            Console.WriteLine(greeting);
        }
    }
}
""")
    
    yield project_dir
    
    # Clean up
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)


@pytest.fixture
def output_file():
    """Create a temporary output file path."""
    file_path = os.path.join(TEMP_DIR, "output.txt")
    
    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)