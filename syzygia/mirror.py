"""
Mirror management for Syzygia
"""
import os
import time
import random
import requests
from typing import List, Optional, Dict, Tuple
from urllib.parse import urlparse
from pathlib import Path

class MirrorManager:
    """Manage package mirrors and handle mirror selection."""

    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.mirrors = self._load_mirrors()
        self.mirror_stats = {}
        self._timeout = int(self.config.get('mirrors', 'timeout', '10'))

    def _load_mirrors(self) -> List[str]:
        """Load mirrors from configuration."""
        return self.config.get_mirrors()

    def add_mirror(self, mirror_url: str, priority: int = 10) -> bool:
        """Add a new mirror with given priority.
        
        Args:
            mirror_url: URL of the mirror to add
            priority: Priority of the mirror (not used yet)
            
        Returns:
            bool: True if mirror was added successfully
        """
        if not self._validate_mirror(mirror_url):
            return False

        self.config.add_mirror(mirror_url)
        self.mirrors = self._load_mirrors()
        return True

    def remove_mirror(self, mirror_url: str) -> bool:
        """Remove a mirror.
        
        Args:
            mirror_url: URL of the mirror to remove
            
        Returns:
            bool: True if mirror was removed successfully
        """
        success = self.config.remove_mirror(mirror_url)
        if success:
            self.mirrors = self._load_mirrors()
        return success

    def _validate_mirror(self, mirror_url: str) -> bool:
        """Check if a mirror URL is valid.
        
        Args:
            mirror_url: URL of the mirror to validate
            
        Returns:
            bool: True if mirror is valid and reachable
        """
        try:
            parsed = urlparse(mirror_url)
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check if it's a local file path
            if parsed.scheme == 'file':
                return os.path.exists(parsed.path)

            # Check if it's a remote URL
            if parsed.scheme in ('http', 'https'):
                test_url = f"{parsed.scheme}://{parsed.netloc}/"
                try:
                    response = requests.head(test_url, timeout=5)
                    return response.status_code == 200
                except requests.RequestException:
                    return False

            return False
        except Exception:
            return False

    def get_best_mirror(self) -> Optional[str]:
        """Get the best available mirror based on response time and priority.
        
        Returns:
            Optional[str]: URL of the best mirror, or None if no mirrors available
        """
        if not self.mirrors:
            return None

        # Simple round-robin for now
        # TODO: Implement better mirror ranking based on response time and success rate
        return random.choice(self.mirrors)

    def download_file(self, file_path: str, destination: str) -> bool:
        """Download a file from the best available mirror.
        
        Args:
            file_path: Relative path of the file to download
            destination: Local path where to save the file
            
        Returns:
            bool: True if download was successful
        """
        for mirror in self.mirrors:
            try:
                if mirror.startswith('file://'):
                    return self._download_local(mirror, file_path, destination)
                else:
                    return self._download_remote(mirror, file_path, destination)
            except Exception as e:
                print(f"Failed to download from {mirror}: {str(e)}")
                continue

        return False

    def _download_remote(self, base_url: str, file_path: str, destination: str) -> bool:
        """Download a file from a remote mirror.
        
        Args:
            base_url: Base URL of the mirror
            file_path: Relative path of the file
            destination: Local path to save the file
            
        Returns:
            bool: True if download was successful
        """
        url = f"{base_url.rstrip('/')}/{file_path.lstrip('/')}"

        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        with requests.get(url, stream=True, timeout=self._timeout) as r:
            r.raise_for_status()
            with open(destination, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return True

    def _download_local(self, base_path: str, file_path: str, destination: str) -> bool:
        """Copy a file from a local mirror.
        
        Args:
            base_path: Base filesystem path of the mirror
            file_path: Relative path of the file
            destination: Local path to save the file
            
        Returns:
            bool: True if copy was successful
        """
        import shutil

        src_path = os.path.join(base_path.replace('file://', ''), file_path.lstrip('/'))

        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        shutil.copy2(src_path, destination)
        return True

    def update_mirror_list(self) -> bool:
        """Update the mirror list from the configured source.
        
        Returns:
            bool: True if mirror list was updated successfully
        """
        mirrorlist_url = self.config.get('mirrors', 'servers')
        if not mirrorlist_url:
            return False

        try:
            response = requests.get(mirrorlist_url, timeout=10)
            if response.status_code == 200:
                mirror_file = self.config.get('mirrors', 'mirrorlist')
                os.makedirs(os.path.dirname(mirror_file), exist_ok=True)

                with open(mirror_file, 'w') as f:
                    f.write(response.text)

                self.mirrors = self._load_mirrors()
                return True
        except Exception as e:
            print(f"Failed to update mirror list: {str(e)}")

        return False
