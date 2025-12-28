#!/usr/bin/env python3
"""
Dynamic port finder for backend API server.
Finds an available port if the default is in use.
"""
import os
import socket
from typing import Optional


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> Optional[int]:
    """
    Find an available port starting from start_port.
    
    Args:
        start_port: Port to start searching from
        max_attempts: Maximum number of ports to try
        
    Returns:
        Available port number or None if not found
    """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('localhost', port))
                return port
            except OSError:
                continue
    return None


def get_backend_port() -> int:
    """
    Get backend port from environment or find available port.
    
    Returns:
        Port number to use
    """
    # Try environment variable first
    env_port = os.getenv('API_PORT', os.getenv('BACKEND_PORT'))
    if env_port:
        try:
            port = int(env_port)
            # Check if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(('localhost', port))
                    return port
                except OSError:
                    print(f"⚠️  Port {port} from environment is in use")
        except ValueError:
            print(f"⚠️  Invalid port in environment: {env_port}")
    
    # Find available port
    default_port = 8001
    port = find_available_port(default_port)
    
    if port is None:
        raise RuntimeError(f"Could not find available port in range {default_port}-{default_port + 10}")
    
    if port != default_port:
        print(f"ℹ️  Using port {port} (default {default_port} was in use)")
    
    return port


if __name__ == "__main__":
    port = get_backend_port()
    print(port)
