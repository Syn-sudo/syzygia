"""Download utilities for Syzygia."""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Union, Dict, Any

import requests
from tqdm import tqdm

def download_file(url: str, destination: Union[str, Path], chunk_size: int = 8192) -> bool:
    """Download a file from a URL to a local destination with progress bar.
    
    Args:
        url: The URL of the file to download
        destination: Local path where the file should be saved
        chunk_size: Size of chunks to download at a time (in bytes)
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        # Ensure the destination directory exists
        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Stream the download to handle large files
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            
            # Get the total file size from headers
            total_size = int(response.headers.get('content-length', 0))
            
            # Initialize progress bar
            progress_bar = tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=f"Downloading {url.split('/')[-1]}",
                ncols=80
            )
            
            # Write the file in chunks
            with open(dest_path, 'wb') as file_obj:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        file_obj.write(chunk)
                        progress_bar.update(len(chunk))
            
            progress_bar.close()
            
            # Verify the file was downloaded completely if size is known
            if total_size != 0 and os.path.getsize(dest_path) != total_size:
                print(f"Error: File size mismatch for {url}")
                os.remove(dest_path)
                return False
                
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {str(e)}")
        # Clean up partially downloaded file if it exists
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False
    except Exception as e:
        print(f"Unexpected error while downloading {url}: {str(e)}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def verify_checksum(file_path: Union[str, Path], checksum: str, algorithm: str = 'sha256') -> bool:
    """Verify the checksum of a file.
    
    Args:
        file_path: Path to the file to verify
        checksum: Expected checksum value
        algorithm: Hash algorithm to use (default: 'sha256')
        
    Returns:
        bool: True if the checksum matches, False otherwise
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return False
            
        # Get the appropriate hash function
        hash_func = getattr(hashlib, algorithm.lower(), None)
        if not hash_func:
            print(f"Error: Unsupported hash algorithm: {algorithm}")
            return False
        
        # Calculate the file's checksum
        file_hash = hash_func()
        with open(file_path, 'rb') as file_obj:
            while True:
                chunk = file_obj.read(8192)
                if not chunk:
                    break
                file_hash.update(chunk)
        
        # Compare with the expected checksum (case-insensitive)
        return file_hash.hexdigest().lower() == checksum.lower()
        
    except (IOError, OSError) as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error while verifying checksum: {str(e)}")
        return False

def download_with_retry(
    url: str,
    destination: Union[str, Path],
    max_retries: int = 3,
    checksum: Optional[str] = None,
    checksum_algorithm: str = 'sha256',
    chunk_size: int = 8192
) -> bool:
    """Download a file with retry mechanism and optional checksum verification.
    
    Args:
        url: The URL of the file to download
        destination: Local path where the file should be saved
        max_retries: Maximum number of retry attempts
        checksum: Expected checksum of the file (optional)
        checksum_algorithm: Hash algorithm to use for checksum verification
        chunk_size: Size of chunks to download at a time (in bytes)
        
    Returns:
        bool: True if download and verification were successful, False otherwise
    """
    dest_path = Path(destination)
    
    for attempt in range(max_retries):
        print(f"Download attempt {attempt + 1} of {max_retries} for {url}")
        
        # Try to download the file
        if download_file(url, dest_path, chunk_size):
            # If checksum is provided, verify it
            if checksum:
                print("Verifying checksum...")
                if verify_checksum(dest_path, checksum, checksum_algorithm):
                    print("Checksum verification successful.")
                    return True
                
                print(f"Checksum verification failed for {url} (attempt {attempt + 1}/{max_retries})")
                try:
                    os.remove(dest_path)
                except OSError as e:
                    print(f"Warning: Could not remove corrupted file {dest_path}: {e}")
            else:
                return True
        
        # If we get here, download or verification failed
        if attempt < max_retries - 1:
            retry_delay = 2 ** attempt  # Exponential backoff
            print(f"Waiting {retry_delay} seconds before retry...")
            import time
            time.sleep(retry_delay)
    
    print(f"Failed to download {url} after {max_retries} attempts")
    return False
