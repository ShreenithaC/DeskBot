#!/usr/bin/env python3
"""Simple test script for USB speakers."""

import subprocess

print("Speaking: Hello, my name is Debo!")
subprocess.run(['espeak', '-v', 'en-us+f3', '-s', '150', '-p', '65', 'Hello, my name is Debo!'])
print("Done!")
