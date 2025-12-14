#!/usr/bin/env python3
"""
Integration Test for UDO Dashboard
Tests backend API endpoints and system integration
"""

import sys
import os
from pathlib import Path
import asyncio
import subprocess
import time
import requests
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text:^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")

class DashboardTester:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_url = "http://localhost:8000"
        self.backend_process = None

    def test_udo_imports(self):
        """Test if UDO system can be imported"""
        print_header("Testing UDO System Imports")

        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from integrated_udo_system import IntegratedUDOSystem
            print_success("IntegratedUDOSystem import successful")

            # Create instance
            udo = IntegratedUDOSystem()
            print_success("IntegratedUDOSystem instantiation successful")

            # Check components
            print_info(f"Orchestrator (UDO v2): {udo.components.get('udo') is not None}")
            print_info(f"Uncertainty Map v3: {udo.components.get('uncertainty') is not None}")
            print_info(f"AI Connector: {udo.components.get('ai_connector') is not None}")
            print_info(f"ML System: {udo.components.get('ml_system') is not None}")
            print_info(f"3-AI Bridge: {udo.components.get('bridge') is not None}")

            return True
        except Exception as e:
            print_error(f"UDO import failed: {e}")
            return False

    def test_backend_startup(self):
        """Test if backend can start"""
        print_header("Testing Backend Startup")

        try:
            # Start backend process
            backend_dir = self.project_root / "backend"
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            print_info("Waiting for backend to start...")
            time.sleep(5)  # Increased wait time for proper startup

            # Check if process is running
            if self.backend_process.poll() is None:
                print_success("Backend process started")
                return True
            else:
                print_error("Backend process failed to start")
                return False

        except Exception as e:
            print_error(f"Backend startup failed: {e}")
            return False

    def test_api_endpoints(self):
        """Test API endpoints"""
        print_header("Testing API Endpoints")

        endpoints = [
            "/api/health",
            "/api/status",
            "/api/metrics"
        ]

        all_passed = True

        for endpoint in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    print_success(f"{endpoint}: {response.status_code}")

                    # Print sample data
                    data = response.json()
                    if isinstance(data, dict):
                        print_info(f"  Response keys: {list(data.keys())[:5]}")
                else:
                    print_error(f"{endpoint}: {response.status_code}")
                    all_passed = False

            except requests.exceptions.ConnectionError:
                print_error(f"{endpoint}: Connection refused (backend not running?)")
                all_passed = False
            except Exception as e:
                print_error(f"{endpoint}: {e}")
                all_passed = False

        return all_passed

    def test_websocket_connection(self):
        """Test WebSocket connection"""
        print_header("Testing WebSocket Connection")

        try:
            import websocket

            ws_url = "ws://localhost:8000/ws"
            print_info(f"Connecting to {ws_url}...")

            ws = websocket.create_connection(ws_url, timeout=5)
            print_success("WebSocket connection established")

            # Wait for initial message
            try:
                message = ws.recv()
                print_success(f"Received message: {message[:100]}...")
            except Exception as e:
                print_info(f"No immediate message (this is OK): {e}")

            ws.close()
            print_success("WebSocket connection closed gracefully")
            return True

        except Exception as e:
            print_error(f"WebSocket test failed: {e}")
            return False

    def test_task_execution(self):
        """Test task execution endpoint"""
        print_header("Testing Task Execution")

        try:
            url = f"{self.backend_url}/api/execute"
            payload = {
                "task": "Test task from integration test",
                "phase": "Testing",
                "auto": True
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print_success("Task execution successful")
                print_info(f"  Decision: {data.get('decision')}")
                print_info(f"  Confidence: {data.get('confidence')}")
                print_info(f"  Quantum State: {data.get('quantum_state')}")
                return True
            else:
                print_error(f"Task execution failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Task execution test failed: {e}")
            return False

    def cleanup(self):
        """Cleanup processes"""
        print_header("Cleanup")

        if self.backend_process:
            print_info("Terminating backend process...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                print_success("Backend process terminated")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print_info("Backend process killed")

    def run_all_tests(self):
        """Run all tests"""
        print_header("UDO Dashboard Integration Tests")

        results = {}

        try:
            # Test 1: UDO imports
            results["UDO Imports"] = self.test_udo_imports()

            # Test 2: Backend startup
            results["Backend Startup"] = self.test_backend_startup()

            if results["Backend Startup"]:
                # Test 3: API endpoints
                results["API Endpoints"] = self.test_api_endpoints()

                # Test 4: WebSocket
                results["WebSocket"] = self.test_websocket_connection()

                # Test 5: Task execution
                results["Task Execution"] = self.test_task_execution()

        finally:
            self.cleanup()

        # Print summary
        print_header("Test Summary")

        total = len(results)
        passed = sum(1 for v in results.values() if v)

        for test_name, passed_flag in results.items():
            if passed_flag:
                print_success(f"{test_name}: PASSED")
            else:
                print_error(f"{test_name}: FAILED")

        print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")

        if passed == total:
            print(f"\n{Fore.GREEN}✓ All tests passed! Dashboard is ready.{Style.RESET_ALL}\n")
            return 0
        else:
            print(f"\n{Fore.RED}✗ Some tests failed. Please review errors above.{Style.RESET_ALL}\n")
            return 1

if __name__ == "__main__":
    tester = DashboardTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
