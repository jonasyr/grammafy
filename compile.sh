#!/bin/bash
#
# Grammafy Build Script
# Creates a standalone executable using PyInstaller

set -e  # Exit on error

echo "Grammafy Build Script"
echo "===================="
echo

# Check for required packages
installed_packages=$(pip list 2>/dev/null)

if ! echo "$installed_packages" | grep -q "Uni-Curses"; then
    echo "Error: uni-curses is not installed"
    echo "Install with: pip install uni-curses"
    exit 1
fi

if ! echo "$installed_packages" | grep -q "pyinstaller"; then
    echo "Error: pyinstaller is not installed"
    echo "Install with: pip install pyinstaller"
    exit 1
fi

echo "All dependencies found. Building..."
echo

# Clean old builds
rm -rf build dist *.spec

# Build standalone executable
pyinstaller --onefile --name grammafy scr/grammafy.py

echo
echo "Build complete! Executable is in: dist/grammafy"
echo

exit 0
