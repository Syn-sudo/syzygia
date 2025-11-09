"""Package management for Syzygia."""

import os
import tarfile
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from typing import List, Dict, Optional, Set, Tuple, Any

class Package:
    """Represents a package in the system."""
    
    def __init__(self, name: str, version: str, description: str = "",
                 depends: List[str] = None, provides: List[str] = None,
                 conflicts: List[str] = None, size: int = 0,
                 url: str = "", packager: str = "") -> None:
        self.name = name
        self.version = version
        self.description = description
        self.depends = depends or []
        self.provides = provides or []
        self.conflicts = conflicts or []
        self.size = size
        self.url = url
        self.packager = packager


class PackageManager:
    """Handle package installation, removal, and queries."""
    
    def __init__(self, config: Any, mirror_manager: Any) -> None:
        self.config = config
        self.mirror_manager = mirror_manager
        self.db_path = Path(self.config.get('general', 'db_path', fallback='/var/lib/syzygia'))
        self.cache_dir = Path(self.config.get('general', 'cache_dir', fallback='/var/cache/syzygia'))
        
        # Ensure required directories exist
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory package database
        self.installed_pkgs: Dict[str, Package] = {}
        self.available_pkgs: Dict[str, List[Package]] = {}
        
        self._load_installed_packages()

    def _load_installed_packages(self) -> None:
        """Load installed packages from the database."""
        db_dir = self.db_path / 'local'
        if not db_dir.exists():
            return
            
        for pkg_dir in db_dir.iterdir():
            if pkg_dir.is_dir():
                pkg_file = pkg_dir / 'desc'
                if pkg_file.exists():
                    pkg = self._parse_package_file(pkg_file)
                    if pkg:
                        self.installed_pkgs[pkg.name] = pkg

    def _parse_package_file(self, file_path: Path) -> Optional[Package]:
        """Parse package metadata file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple parsing of package metadata
            pkg_data = {}
            current_field = None
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('#'):
                    continue
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    pkg_data[key.strip().lower()] = value.strip()
            
            if 'name' not in pkg_data or 'version' not in pkg_data:
                return None
                
            return Package(
                name=pkg_data['name'],
                version=pkg_data['version'],
                description=pkg_data.get('description', ''),
                depends=pkg_data.get('depends', '').split(),
                provides=pkg_data.get('provides', '').split(),
                conflicts=pkg_data.get('conflicts', '').split()
            )
            
        except Exception as e:
            print(f"Error parsing package file {file_path}: {str(e)}")
            return None

    def _install_package(self, pkg_file: Path) -> bool:
        """Install a package from a local file."""
        print(f"Installing package from {pkg_file}")
        
        # Extract package name from filename (e.g., 'paket1-1.0.0.pkg.tar.zst' -> 'paket1')
        pkg_name = pkg_file.name.split('-')[0]
        
        # Create package info
        pkg = Package(
            name=pkg_name,
            version="1.0.0",
            description=f"Installed from {pkg_file}",
            depends=[],
            provides=[pkg_name],
            conflicts=[]
        )
        
        # Add to installed packages
        self.installed_pkgs[pkg_name] = pkg
        
        # Create package directory in database
        pkg_dir = self.db_path / 'local' / pkg_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # Save package metadata
        with open(pkg_dir / 'desc', 'w') as f:
            f.write(f"name: {pkg_name}\n")
            f.write(f"version: 1.0.0\n")
            f.write(f"description: Installed from {pkg_file}\n")
            f.write(f"depends: \n")
            f.write(f"provides: {pkg_name}\n")
            f.write(f"conflicts: \n")
        
        print(f"Successfully installed {pkg_name}")
        return True

    def list_installed(self) -> List[Package]:
        """List all installed packages."""
        return list(self.installed_pkgs.values())

    def install(self, package_names: List[str], nodeps: bool = False) -> bool:
        """Install one or more packages."""
        success = True
        
        for pkg_name in package_names:
            if pkg_name in self.installed_pkgs:
                print(f"Package {pkg_name} is already installed")
                continue
                
            # Create a dummy package file path
            pkg_file = self.cache_dir / f"{pkg_name}-1.0.0.pkg.tar.zst"
            pkg_file.touch()  # Create empty file
            
            if self._install_package(pkg_file):
                print(f"Successfully installed {pkg_name}")
            else:
                print(f"Failed to install package: {pkg_name}")
                success = False
                
        return success

    def remove(self, package_names: List[str], nodeps: bool = False) -> bool:
        """Remove one or more packages."""
        success = True
        
        for pkg_name in package_names:
            if pkg_name not in self.installed_pkgs:
                print(f"Package {pkg_name} is not installed")
                continue
                
            # Check dependents if not forcing removal
            if not nodeps:
                dependents = self._find_dependents(pkg_name)
                if dependents:
                    print(f"Cannot remove {pkg_name}: the following packages depend on it:")
                    for dep in dependents:
                        print(f"  {dep}")
                    success = False
                    continue
            
            # Remove package
            if self._remove_package(pkg_name):
                print(f"Successfully removed {pkg_name}")
            else:
                print(f"Failed to remove package: {pkg_name}")
                success = False
                
        return success

    def _find_dependents(self, package_name: str) -> List[str]:
        """Find packages that depend on the given package."""
        dependents = []
        for pkg in self.installed_pkgs.values():
            if package_name in pkg.depends:
                dependents.append(pkg.name)
        return dependents

    def _remove_package(self, package_name: str) -> bool:
        """Remove a package and its files."""
        try:
            pkg_dir = self.db_path / 'local' / package_name
            if pkg_dir.exists():
                import shutil
                shutil.rmtree(pkg_dir)
            
            # Remove from memory
            if package_name in self.installed_pkgs:
                del self.installed_pkgs[package_name]
                
            return True
        except Exception as e:
            print(f"Error removing package {package_name}: {str(e)}")
            return False

    def search(self, query: str) -> List[Package]:
        """Search for packages matching the query."""
        # In a real implementation, this would search through repository databases
        # For now, we'll just search in installed packages
        results = []
        query = query.lower()
        
        for pkg in self.installed_pkgs.values():
            if (query in pkg.name.lower() or 
                query in (pkg.description or "").lower()):
                results.append(pkg)
                
        return results

    def update(self) -> bool:
        """Update the package database from mirrors."""
        print("Updating package databases...")
        # In a real implementation, this would:
        # 1. Get list of mirrors
        # 2. Download package databases
        # 3. Parse and update available_pkgs
        return True

    def upgrade(self, package_names: List[str] = None) -> bool:
        """Upgrade packages."""
        if package_names is None:
            # Upgrade all packages
            package_names = list(self.installed_pkgs.keys())
            
        success = True
        self.update()  # Make sure we have the latest package info
        
        for pkg_name in package_names:
            if pkg_name not in self.installed_pkgs:
                print(f"Package {pkg_name} is not installed")
                continue
                
            # In a real implementation, check for updates
            print(f"Checking for updates for {pkg_name}...")
            # For now, just reinstall the package
            self.install([pkg_name])
            
        return success