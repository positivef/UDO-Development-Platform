#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Restart Script
Purpose: Forcefully kill all backend processes and restart with fixed code
Created: 2025-12-23
"""

import subprocess
import time
import sys
import os
from pathlib import Path

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def find_port_processes(port=8000):
    """Find all processes using the specified port"""
    try:
        # Windows: netstat -ano | findstr :8000
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"',
            shell=True,
            capture_output=True,
            text=True
        )

        pids = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                if pid.isdigit():
                    pids.add(int(pid))

        return list(pids)
    except Exception as e:
        print(f"⚠️  Error finding port processes: {e}")
        return []

def kill_process(pid):
    """Kill a process by PID (Windows)"""
    try:
        subprocess.run(
            f'taskkill /F /PID {pid}',
            shell=True,
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def kill_all_backend_processes():
    """Kill all backend processes on port 8000"""
    print("🔍 Finding backend processes on port 8000...")

    pids = find_port_processes(8000)

    if not pids:
        print("✅ No processes found on port 8000")
        return True

    print(f"📋 Found {len(pids)} process(es): {pids}")

    # Kill each process
    killed = 0
    for pid in pids:
        print(f"🔫 Killing PID {pid}...", end=" ")
        if kill_process(pid):
            print("✅")
            killed += 1
        else:
            print("❌")

    print(f"\n✅ Killed {killed}/{len(pids)} processes")

    # Wait and verify
    time.sleep(2)

    remaining = find_port_processes(8000)
    if remaining:
        print(f"⚠️  Warning: {len(remaining)} process(es) still running: {remaining}")
        return False
    else:
        print("✅ Port 8000 is now free")
        return True

def start_backend():
    """Start backend with uvicorn"""
    repo_root = Path(__file__).parent.parent
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        print(f"❌ Virtual environment not found: {venv_python}")
        return False

    print("\n🚀 Starting backend server...")
    print(f"   Python: {venv_python}")
    print(f"   Working dir: {repo_root}")

    # Change to repo root
    os.chdir(repo_root)

    # Start uvicorn
    cmd = [
        str(venv_python),
        "-m", "uvicorn",
        "backend.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]

    print(f"   Command: {' '.join(cmd)}\n")

    try:
        # Start in background (don't wait for completion)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"✅ Backend started (PID: {process.pid})")

        # Wait a bit for server to start
        print("⏳ Waiting for server to initialize...")
        time.sleep(5)

        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend is running")
            print(f"\n📍 API: http://localhost:8000")
            print(f"📍 Docs: http://localhost:8000/docs")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False

def verify_backend():
    """Verify backend is responding"""
    import urllib.request
    import json

    print("\n🔍 Verifying backend health...")

    try:
        # Try to fetch from health endpoint (or any endpoint)
        req = urllib.request.Request("http://localhost:8000/docs")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("✅ Backend is responding (HTTP 200)")
                return True
            else:
                print(f"⚠️  Backend returned HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ Backend verification failed: {e}")
        return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("🔄 Backend Restart Script")
    print("=" * 60)
    print()

    # Step 1: Kill all existing processes
    print("📍 Step 1: Killing existing backend processes")
    print("-" * 60)
    if not kill_all_backend_processes():
        print("\n⚠️  Warning: Some processes couldn't be killed")
        print("   Backend will still attempt to start...")

    # Step 2: Start new backend
    print("\n📍 Step 2: Starting backend with fixed code")
    print("-" * 60)
    if not start_backend():
        print("\n❌ Failed to start backend")
        sys.exit(1)

    # Step 3: Verify backend is responding
    print("\n📍 Step 3: Verifying backend health")
    print("-" * 60)
    if verify_backend():
        print("\n" + "=" * 60)
        print("✅ Backend restart complete!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("   1. Go to http://localhost:3000/kanban")
        print("   2. Test drag & drop")
        print("   3. Verify no errors in browser console")
        print()
    else:
        print("\n⚠️  Backend started but not responding yet")
        print("   Wait a few more seconds and check http://localhost:8000/docs")

if __name__ == '__main__':
    main()
