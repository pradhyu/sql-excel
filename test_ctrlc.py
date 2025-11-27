#!/usr/bin/env python3
"""Test script to verify Ctrl+C behavior in REPL"""

import subprocess
import time

print("Testing Ctrl+C in multi-line mode...")
print("=" * 50)

# Start the REPL
proc = subprocess.Popen(
    ['.venv/bin/python', 'main.py', 'test_data'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd='/home/pradhyushrestha/git/sql-excel'
)

# Wait for REPL to start
time.sleep(2)

# Send multi-line input
proc.stdin.write("SELECT\n")
proc.stdin.flush()
time.sleep(0.5)

# Send Ctrl+C (ASCII 3)
proc.stdin.write("\x03")
proc.stdin.flush()
time.sleep(0.5)

# Send exit command
proc.stdin.write("exit\n")
proc.stdin.flush()

# Get output
output, _ = proc.communicate(timeout=5)

print("Output:")
print(output)
print("=" * 50)

if "(sql-excel)" in output and "exit" in output.lower():
    print("✓ Ctrl+C successfully exited multi-line mode!")
else:
    print("✗ Ctrl+C did not work as expected")
