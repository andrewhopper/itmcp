"""
itmcp package - MCP server for executing terminal commands

This package provides tools for AI assistants to execute shell commands on the system.
"""

__version__ = "0.1.0"

from . import server
import asyncio

def main():
    """Main entry point for the package."""
    asyncio.run(server.main())

__all__ = ['main', 'server']
