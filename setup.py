#!/usr/bin/env python3
"""
Setup script for PBIXRay MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pbixray-mcp-server",
    version="0.1.0",
    author="PBIXRay Contributors",
    author_email="your.email@example.com",
    description="An MCP server for analyzing Power BI files using PBIXRay",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/pbixray-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.9",
    install_requires=[
        "mcp>=1.2.0",
        "pbixray>=0.1.0",
        "numpy>=1.20.0",
        # Different pandas versions depending on Python version
        "pandas>=1.0.0,<2.0.0; python_version < '3.10'",
        "pandas>=1.0.0; python_version >= '3.10'",
    ],
    entry_points={
        "console_scripts": [
            "pbixray-mcp-server=pbixray_server:main",
        ],
    },
)
