#!/usr/bin/env python3
"""API Performance Benchmark"""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("API Performance Benchmark")
print("=" * 60)

# Test 1: Import time
print("\n1. Import Performance:")
start = time.time()
from integrated_udo_system import IntegratedUDOSystem  # noqa: E402

import_time = time.time() - start
print(f"   Import time: {import_time:.3f}s")

# Test 2: Initialization time
print("\n2. UDO System Initialization:")
start = time.time()
udo_system = IntegratedUDOSystem(project_name="Benchmark-Test")
init_time = time.time() - start
print(f"   Init time: {init_time:.3f}s")

# Test 3: get_system_report() time
print("\n3. get_system_report() Performance:")
for i in range(5):
    start = time.time()
    report = udo_system.get_system_report()
    report_time = time.time() - start
    print(f"   Attempt {i + 1}: {report_time:.3f}s")

# Test 4: Individual component reports
print("\n4. Component Report Performance:")
if udo_system.components.get("ai_connector"):
    start = time.time()
    ai_report = udo_system.components["ai_connector"].get_status_report()
    ai_time = time.time() - start
    print(f"   AI Connector report: {ai_time:.3f}s")

if udo_system.components.get("ml_system"):
    start = time.time()
    ml_report = udo_system.components["ml_system"].get_model_report()
    ml_time = time.time() - start
    print(f"   ML System report: {ml_time:.3f}s")

# Summary
print("\n" + "=" * 60)
print("Summary:")
print(f"  Total startup: {import_time + init_time:.3f}s")
print("  First report: needs to be measured above")
print("=" * 60)
