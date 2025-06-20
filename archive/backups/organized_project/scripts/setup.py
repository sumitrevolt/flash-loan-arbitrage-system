"""
Setup script for Foundry MCP Server
"""

from setuptools import setup, find_packages

setup(
    name="foundry-mcp-server",
    version="1.0.0",
    description="Model Context Protocol server for Foundry integration with flash loan arbitrage systems",
    author="Flash Loan Arbitrage Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
        "pydantic>=2.0.0",
        "aiofiles>=23.0.0",
        "asyncio-mqtt>=0.16.0",
        "websockets>=12.0",
        "pyyaml>=6.0",
        "toml>=0.10.2",
        "click>=8.0.0",
        "structlog>=23.0.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "security": [
            "slither-analyzer>=0.10.0",
            "mythx-cli>=0.7.0",
            "bandit>=1.7.0",
            "safety>=3.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "foundry-mcp-server=src.server.mcp_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)