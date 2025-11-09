""
Validation utilities for Syzygia
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

def validate_package_name(name: str) -> Tuple[bool, str]:
    """
    Validate a package name according to Arch Linux package naming conventions.
    
    Args:
        name: The package name to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not name:
        return False, "Package name cannot be empty"
    
    # Package name must only contain alphanumeric characters, @, ., _ , +, -
    if not re.match(r'^[a-zA-Z0-9@._+-]+$', name):
        return False, "Package name contains invalid characters. Only alphanumeric, @, ., _, +, - are allowed."
    
    # Package name must start with an alphanumeric character
    if not name[0].isalnum():
        return False, "Package name must start with an alphanumeric character"
    
    # Package name must end with an alphanumeric character or an underscore
    if not (name[-1].isalnum() or name[-1] == '_'):
        return False, "Package name must end with an alphanumeric character or underscore"
    
    return True, ""

def validate_package_version(version: str) -> Tuple[bool, str]:
    """
    Validate a package version string.
    
    Args:
        version: The version string to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not version:
        return False, "Version cannot be empty"
    
    # Version must start with a digit
    if not version[0].isdigit():
        return False, "Version must start with a digit"
    
    # Version can contain alphanumeric characters, ., _, +, :, ~
    if not re.match(r'^[a-zA-Z0-9._+:~-]+$', version):
        return False, "Version contains invalid characters"
    
    return True, ""

def validate_package_architecture(arch: str) -> Tuple[bool, str]:
    """
    Validate a package architecture.
    
    Args:
        arch: The architecture string to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    valid_archs = {
        'x86_64', 'i686', 'i586', 'i486', 'i386',
        'armv7h', 'aarch64', 'armv6h', 'armv5tel',
        'ppc64le', 'ppc64', 'ppc', 'riscv64',
        's390x', 'any'
    }
    
    if not arch:
        return False, "Architecture cannot be empty"
    
    if arch not in valid_archs:
        return False, f"Invalid architecture. Must be one of: {', '.join(sorted(valid_archs))}"
    
    return True, ""

def validate_package_dependencies(deps: List[str]) -> Tuple[bool, str]:
    """
    Validate package dependencies.
    
    Args:
        deps: List of dependency strings to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not isinstance(deps, list):
        return False, "Dependencies must be a list"
    
    for dep in deps:
        if not isinstance(dep, str):
            return False, f"Dependency must be a string, got {type(dep).__name__}"
        
        # Check for valid dependency format: name[=><~!]*[0-9.:]*
        if not re.match(r'^[a-zA-Z0-9@._+-]+([=><~!]?=|[><]=?|~=)[0-9a-zA-Z.:+~-]*$', dep):
            # Check if it's just a package name without version constraints
            if not re.match(r'^[a-zA-Z0-9@._+-]+$', dep):
                return False, f"Invalid dependency format: {dep}"
    
    return True, ""

def validate_package_metadata(metadata: Dict) -> Tuple[bool, str]:
    """
    Validate package metadata.
    
    Args:
        metadata: Dictionary containing package metadata
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ['name', 'version', 'description', 'arch', 'license', 'depends']
    
    for field in required_fields:
        if field not in metadata:
            return False, f"Missing required field: {field}"
    
    # Validate name
    is_valid, error = validate_package_name(metadata['name'])
    if not is_valid:
        return False, f"Invalid package name: {error}"
    
    # Validate version
    is_valid, error = validate_package_version(metadata['version'])
    if not is_valid:
        return False, f"Invalid version: {error}"
    
    # Validate architecture
    is_valid, error = validate_package_architecture(metadata['arch'])
    if not is_valid:
        return False, f"Invalid architecture: {error}"
    
    # Validate dependencies
    is_valid, error = validate_package_dependencies(metadata.get('depends', []))
    if not is_valid:
        return False, f"Invalid dependencies: {error}"
    
    # Validate optional fields if present
    if 'optdepends' in metadata:
        is_valid, error = validate_package_dependencies(metadata['optdepends'])
        if not is_valid:
            return False, f"Invalid optional dependencies: {error}"
    
    # Validate package size if present
    if 'size' in metadata and not isinstance(metadata['size'], int):
        return False, "Package size must be an integer"
    
    return True, ""

def validate_package_file(file_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate a package file.
    
    Args:
        file_path: Path to the package file
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    
    # Check file extension
    if file_path.suffix not in ('.pkg.tar.zst', '.pkg.tar.xz', '.pkg.tar.gz', '.pkg.tar.bz2'):
        return False, f"Invalid package file extension: {file_path.suffix}"
    
    # Check file size
    if file_path.stat().st_size == 0:
        return False, "Package file is empty"
    
    # TODO: Add more comprehensive validation, e.g., check package content
    
    return True, ""

def validate_repository(path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate a repository directory.
    
    Args:
        path: Path to the repository directory
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    path = Path(path)
    
    # Check if path exists and is a directory
    if not path.exists():
        return False, f"Repository directory does not exist: {path}"
    if not path.is_dir():
        return False, f"Repository path is not a directory: {path}"
    
    # Check for required files
    required_files = ['syzygia.db', 'syzygia.db.sig', 'syzygia.files', 'syzygia.files.sig']
    for file in required_files:
        if not (path / file).exists():
            return False, f"Missing required repository file: {file}"
    
    # TODO: Add more comprehensive validation, e.g., check database integrity
    
    return True, ""

def validate_mirror_url(url: str) -> Tuple[bool, str]:
    """
    Validate a mirror URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Check for valid URL scheme
    if not (url.startswith('http://') or url.startswith('https://') or url.startswith('file://') or url.startswith('ftp://')):
        return False, "URL must start with http://, https://, file://, or ftp://"
    
    # For file URLs, check if the path exists
    if url.startswith('file://'):
        path = url[7:]
        if not os.path.exists(path):
            return False, f"Local path does not exist: {path}"
    
    return True, ""

# Alias for backward compatibility
validate_package = validate_package_metadata
