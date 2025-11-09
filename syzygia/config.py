"""
Configuration management for Syzygia
"""
import os
import configparser
from pathlib import Path
from typing import Dict, List, Optional

class Config:
    """Handle configuration and settings for Syzygia."""

    def __init__(self, config_path: str = None):
        """Initialize configuration with default values."""
        self.config = configparser.ConfigParser()
        self.config_path = config_path or os.path.expanduser('~/.config/syzygia/config.ini')
        self.defaults = {
            'general': {
                'architecture': 'x86_64',
                'root_dir': '/',
                'db_path': '/var/lib/syzygia',
                'cache_dir': '/var/cache/syzygia/pkg',
                'log_file': '/var/log/syzygia.log',
                'gpg_dir': '/etc/syzygia/gnupg',
            },
            'mirrors': {
                'servers': 'https://archlinux.org/mirrorlist/?country=all&protocol=https&ip_version=4',
                'mirrorlist': '/etc/syzygia/mirrorlist',
                'mirror_priority': '10',
                'timeout': '10',
            }
        }
        self._load_config()

    def _load_config(self):
        """Load configuration from file or use defaults."""
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self._create_default_config()

        self.config.read(self.config_path)

        # Ensure all default sections and options exist
        for section, options in self.defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                if not self.config.has_option(section, option):
                    self.config.set(section, option, value)

        self._save_config()

    def _create_default_config(self):
        """Create default configuration file."""
        for section, options in self.defaults.items():
            self.config[section] = options
        self._save_config()

    def _save_config(self):
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get(self, section: str, option: str, fallback=None) -> str:
        """Get a configuration value."""
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def set(self, section: str, option: str, value: str):
        """Set a configuration value."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        self._save_config()

    def get_mirrors(self) -> List[str]:
        """Get list of configured mirrors."""
        mirror_file = self.get('mirrors', 'mirrorlist')
        mirrors = []

        if os.path.exists(mirror_file):
            with open(mirror_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        mirrors.append(line)

        return mirrors or [self.defaults['mirrors']['servers']]

    def add_mirror(self, mirror_url: str):
        """Add a new mirror to the mirrorlist."""
        mirror_file = self.get('mirrors', 'mirrorlist')
        os.makedirs(os.path.dirname(mirror_file), exist_ok=True)

        with open(mirror_file, 'a+') as f:
            f.write(f"{mirror_url}\n")

    def remove_mirror(self, mirror_url: str) -> bool:
        """
        Remove a mirror from the mirrorlist.
        
        Args:
            mirror_url: URL of the mirror to remove
            
        Returns:
            bool: True if mirror was removed, False otherwise
        """
        mirror_file = self.get('mirrors', 'mirrorlist')
        if not os.path.exists(mirror_file):
            return False

        try:
            with open(mirror_file, 'r') as f:
                mirrors = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            if mirror_url in mirrors:
                mirrors.remove(mirror_url)
                with open(mirror_file, 'w') as f:
                    f.write('\n'.join(mirrors) + '\n')
                return True
            return False
        except Exception as e:
            print(f"Error removing mirror: {e}")
            return False
