from setuptools import setup, find_packages
from src.version import VERSION

setup(
    name="file-tree-generator",
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        "pygments",
        "pillow",  # Added for visualization capabilities
    ],
    author="Paape Companies",
    author_email="contact@website.com",
    description="Generate visual text representation of directory trees with code visualization",
    keywords="file, directory, tree, visualization, code, references",
    url="https://github.com/SamuelAleks/file-tree-generator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)