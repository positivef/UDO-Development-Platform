#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-platform startup script for UDO Dashboard
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Start FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    backend_dir = Path(__file__).parent / "backend"

    # Install requirements
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                   cwd=backend_dir, check=False)

    # Start server
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=backend_dir
    )
    print("✅ Backend started on http://localhost:8000")
    return backend_process

def start_frontend():
    """Start Next.js frontend"""
    print("🎨 Starting Next.js dashboard...")
    frontend_dir = Path(__file__).parent / "web-dashboard"

    # Install dependencies
    subprocess.run(["npm", "install"], cwd=frontend_dir, check=False, shell=True)

    # Start dev server
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )
    print("✅ Dashboard will be available at http://localhost:3000")
    return frontend_process

def main():
    print("=" * 50)
    print("🚀 UDO Development Platform v3.0")
    print("=" * 50)
    print()

    processes = []

    try:
        # Start backend
        backend = start_backend()
        processes.append(backend)

        # Wait for backend to initialize
        print("⏳ Waiting for backend to initialize...")
        time.sleep(3)

        # Start frontend
        frontend = start_frontend()
        processes.append(frontend)

        print()
        print("=" * 50)
        print("✅ All services started successfully!")
        print()
        print("📊 Backend API: http://localhost:8000/docs")
        print("🎯 Dashboard UI: http://localhost:3000")
        print()
        print("Press Ctrl+C to stop all services")
        print("=" * 50)

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⏹️ Shutting down services...")
        for process in processes:
            process.terminate()
        print("✅ All services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
