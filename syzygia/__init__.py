"""
Syzygia - A custom package manager for Arch Linux
"""

__version__ = '0.1.0'

# Core components
from .cli import main
from .config import Config
from .mirror import MirrorManager
from .package import PackageManager
from .repo import Repository

__all__ = ['main', 'Config', 'MirrorManager', 'PackageManager', 'Repository']
