from setuptools import setup, find_packages

setup(
    name="file-tree-generator",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[],
    author="Paape Companies",
    author_email="contact@website.com",
    description="Generate visual text representation of directory trees",
    keywords="file, directory, tree, visualization",
    url="https://github.com/SamuelAleks/file-tree-generator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)