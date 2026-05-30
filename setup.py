from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jvclrpctl",
    version="0.1.0",
    author="JVC Projector Control",
    author_email="",
    description="Python library for controlling JVC D-ILA projectors via IP/Network commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jvclrpctl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pyserial>=3.5",  # Required for Lumagen serial communication
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add CLI scripts here if needed
            # "jvctl=jvclrpctl.cli:main",
        ],
    },
)
