"""Command-line interface for Syzygia."""

import argparse
import sys
from typing import List, Optional, Any, Dict

from .config import Config
from .mirror import MirrorManager
from .package import PackageManager, Package
from .repo import RepositoryManager

class SyzygiaCLI:
    """Command-line interface for Syzygia package manager."""
    
    def __init__(self):
        """Initialize the CLI with configuration and managers."""
        self.config = Config()
        self.mirror_manager = MirrorManager(self.config)
        self.repo_manager = RepositoryManager(self.config)
        self.pkg_manager = PackageManager(self.config, self.mirror_manager)
        
        # Set up argument parser
        self.parser = argparse.ArgumentParser(
            description='Syzygia - A custom package manager for Arch Linux',
            usage='''syzygia <command> [<args>]

Available commands:
  install     Install packages
  remove      Remove packages
  update      Update package database
  upgrade     Upgrade packages
  search      Search for packages
  list        List installed packages
  mirror      Manage mirrors
  repo        Manage repositories
''')
        
        self.parser.add_argument('command', help='Command to run')
        
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments (defaults to sys.argv[1:])
            
        Returns:
            int: Exit status (0 for success, non-zero for error)
        """
        # Parse command-line arguments
        if len(sys.argv) == 1:
            self.parser.print_help()
            return 0
            
        # Parse the command
        args = self.parser.parse_args(args or sys.argv[1:2])
        
        # Dispatch to the appropriate handler
        if not hasattr(self, args.command):
            print(f"Unknown command: {args.command}")
            self.parser.print_help()
            return 1
            
        return getattr(self, args.command)()
    
    def install(self) -> int:
        """Handle the 'install' command."""
        parser = argparse.ArgumentParser(description='Install packages')
        parser.add_argument('packages', nargs='+', help='Packages to install')
        parser.add_argument('--nodeps', action='store_true', help='Skip dependency checks')
        args = parser.parse_args(sys.argv[2:])
        
        if not args.packages:
            print("Error: No packages specified")
            return 1
            
        return 0 if self.pkg_manager.install(args.packages, args.nodeps) else 1
    
    def remove(self) -> int:
        """Handle the 'remove' command."""
        parser = argparse.ArgumentParser(description='Remove packages')
        parser.add_argument('packages', nargs='+', help='Packages to remove')
        parser.add_argument('--nodeps', action='store_true', help='Skip dependency checks')
        args = parser.parse_args(sys.argv[2:])
        
        if not args.packages:
            print("Error: No packages specified")
            return 1
            
        return 0 if self.pkg_manager.remove(args.packages, args.nodeps) else 1
    
    def update(self) -> int:
        """Handle the 'update' command."""
        parser = argparse.ArgumentParser(description='Update package database')
        parser.add_argument('--refresh', action='store_true', help='Refresh mirror list')
        args = parser.parse_args(sys.argv[2:])
        
        if args.refresh:
            if not self.mirror_manager.update_mirror_list():
                print("Error: Failed to update mirror list")
                return 1
                
        return 0 if self.pkg_manager.update() else 1
    
    def upgrade(self) -> int:
        """Handle the 'upgrade' command."""
        parser = argparse.ArgumentParser(description='Upgrade packages')
        parser.add_argument('packages', nargs='*', help='Packages to upgrade (default: all)')
        args = parser.parse_args(sys.argv[2:])
        
        return 0 if self.pkg_manager.upgrade(args.packages) else 1
    
    def search(self) -> int:
        """Handle the 'search' command."""
        parser = argparse.ArgumentParser(description='Search for packages')
        parser.add_argument('query', help='Search query')
        args = parser.parse_args(sys.argv[2:])
        
        packages = self.pkg_manager.search(args.query)
        if not packages:
            print("No packages found")
            return 1
            
        for pkg in packages:
            print(f"{pkg.name} ({pkg.version}) - {pkg.description}")
            
        return 0
    
    def list(self) -> int:
        """Handle the 'list' command."""
        parser = argparse.ArgumentParser(description='List installed packages')
        parser.add_argument('--upgradable', action='store_true', help='Show only upgradable packages')
        args = parser.parse_args(sys.argv[2:])
        
        packages = self.pkg_manager.list_installed()
        if not packages:
            print("No packages installed")
            return 0
            
        for pkg in packages:
            print(f"{pkg.name} {pkg.version}")
            
        return 0
    
    def mirror(self) -> int:
        """Handle the 'mirror' command."""
        parser = argparse.ArgumentParser(description='Manage mirrors')
        subparsers = parser.add_subparsers(dest='subcommand', help='Subcommand to run')
        
        # List mirrors
        list_parser = subparsers.add_parser('list', help='List configured mirrors')
        
        # Add mirror
        add_parser = subparsers.add_parser('add', help='Add a mirror')
        add_parser.add_argument('url', help='Mirror URL')
        add_parser.add_argument('--priority', type=int, default=10, help='Mirror priority')
        
        # Remove mirror
        remove_parser = subparsers.add_parser('remove', help='Remove a mirror')
        remove_parser.add_argument('url', help='Mirror URL to remove')
        
        # Update mirrors
        update_parser = subparsers.add_parser('update', help='Update mirror list')
        
        args = parser.parse_args(sys.argv[2:])
        
        if not args.subcommand:
            parser.print_help()
            return 1
            
        if args.subcommand == 'list':
            mirrors = self.mirror_manager.mirrors
            if not mirrors:
                print("No mirrors configured")
                return 0
                
            for i, mirror in enumerate(mirrors, 1):
                print(f"{i}. {mirror}")
                
        elif args.subcommand == 'add':
            if self.mirror_manager.add_mirror(args.url, args.priority):
                print(f"Added mirror: {args.url}")
            else:
                print(f"Failed to add mirror: {args.url}")
                return 1
                
        elif args.subcommand == 'remove':
            if self.mirror_manager.remove_mirror(args.url):
                print(f"Removed mirror: {args.url}")
            else:
                print(f"Failed to remove mirror: {args.url}")
                return 1
                
        elif args.subcommand == 'update':
            if self.mirror_manager.update_mirror_list():
                print("Mirror list updated successfully")
            else:
                print("Failed to update mirror list")
                return 1
                
        return 0
    
    def repo(self) -> int:
        """Handle the 'repo' command."""
        parser = argparse.ArgumentParser(description='Manage repositories')
        subparsers = parser.add_subparsers(dest='subcommand', help='Subcommand to run')
        
        # List repositories
        list_parser = subparsers.add_parser('list', help='List configured repositories')
        
        # Add repository
        add_parser = subparsers.add_parser('add', help='Add a repository')
        add_parser.add_argument('name', help='Repository name')
        add_parser.add_argument('url', help='Repository URL')
        add_parser.add_argument('--sig-level', default='Optional', help='Signature verification level')
        
        # Remove repository
        remove_parser = subparsers.add_parser('remove', help='Remove a repository')
        remove_parser.add_argument('name', help='Repository name to remove')
        
        # Update repositories
        update_parser = subparsers.add_parser('update', help='Update repository databases')
        
        args = parser.parse_args(sys.argv[2:])
        
        if not args.subcommand:
            parser.print_help()
            return 1
            
        if args.subcommand == 'list':
            repos = self.repo_manager.list_repos()
            if not repos:
                print("No repositories configured")
                return 0
                
            for repo in repos:
                print(f"{repo}")
                
        elif args.subcommand == 'add':
            if self.repo_manager.add_repo(args.name, args.url, args.sig_level):
                print(f"Added repository: {args.name}")
            else:
                print(f"Failed to add repository: {args.name}")
                return 1
                
        elif args.subcommand == 'remove':
            if self.repo_manager.remove_repo(args.name):
                print(f"Removed repository: {args.name}")
            else:
                print(f"Failed to remove repository: {args.name}")
                return 1
                
        elif args.subcommand == 'update':
            if self.repo_manager.update_all():
                print("Repository databases updated successfully")
            else:
                print("Failed to update repository databases")
                return 1
                
        return 0


def main():
    """Main entry point for the Syzygia CLI."""
    cli = SyzygiaCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
