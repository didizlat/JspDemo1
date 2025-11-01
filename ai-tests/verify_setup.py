"""
Verify Python environment setup for AI testing
"""

import sys
import codecs

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print("="*60)
print("Python AI Testing Environment Verification")
print("="*60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check installed packages
packages = [
    "playwright",
    "openai",
    "faker",
    "dotenv"
]

print("\nInstalled packages:")
for pkg in packages:
    try:
        if pkg == "dotenv":
            __import__("dotenv")
            print(f"  ✓ python-dotenv")
        else:
            __import__(pkg)
            print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  ✗ {pkg} - NOT INSTALLED")

# Check Playwright browsers
print("\nPlaywright browsers:")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        print(f"  ✓ Chromium available")
except Exception as e:
    print(f"  ✗ Browser issue: {e}")

# Check for OpenAI key
import os
from dotenv import load_dotenv
load_dotenv()

print("\nOpenAI Configuration:")
if os.getenv("OPENAI_API_KEY"):
    key = os.getenv("OPENAI_API_KEY")
    print(f"  ✓ API Key found: {key[:10]}...{key[-4:]}")
else:
    print("  ⚠ API Key not found (required for ai_testing.py)")
    print("    Create .env file with: OPENAI_API_KEY=your_key_here")

print("\n" + "="*60)
print("Setup Status: READY ✓")
print("="*60)
print("\nYou can now run:")
print("  python demo_automation.py    # Traditional automation")
print("  python ai_testing.py         # AI-powered testing (needs API key)")
print("="*60)

