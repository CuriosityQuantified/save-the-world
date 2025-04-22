"""
Main Application Entry Point

This module serves as the entry point for the Interactive Simulation system.
It starts the FastAPI application with uvicorn.
"""

import uvicorn
import os
import sys
import socket
import time
from dotenv import load_dotenv

def find_available_port(start_port=8000, max_port=8100):
    """Find an available port to use if the default is occupied."""
    port = start_port
    while port <= max_port:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Set SO_REUSEADDR to allow reusing the socket immediately
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"Could not find an available port in range {start_port}-{max_port}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("PORT", 8000))
    
    # Add a small delay to ensure any previous socket is fully released
    time.sleep(1)
    
    try:
        # Try to find an available port if the default is in use
        port = find_available_port(default_port)
        if port != default_port:
            print(f"Port {default_port} is in use. Using port {port} instead.")
        
        # Log startup message
        print(f"Starting Interactive Simulation API on {host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Start the FastAPI application with proper socket handling
        uvicorn.run(
            "api.app:app", 
            host=host, 
            port=port, 
            reload=True,
            # Add configuration to better handle socket reuse
            log_level="info",
            timeout_keep_alive=65
        )
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1) 