"""
Setup script for LeanBot-Trader
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="leanbot-trader",
    version="1.0.0",
    author="TechCodinz",
    description="A comprehensive cryptocurrency trading bot - No Limit to Trading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TechCodinz/LeanBot-Trader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "leanbot=main:cli",
        ],
    },
    keywords="cryptocurrency trading bot bitcoin ethereum algorithmic trading",
    project_urls={
        "Bug Reports": "https://github.com/TechCodinz/LeanBot-Trader/issues",
        "Source": "https://github.com/TechCodinz/LeanBot-Trader",
        "Documentation": "https://github.com/TechCodinz/LeanBot-Trader/wiki",
    },
)