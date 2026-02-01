import os
import glob
import subprocess
import getpass
from pathlib import Path

print("=" * 60)
print("PYOCCAM - Upload Wheels to TestPyPI")
print("=" * 60)

# Find all wheel files
wheel_locations = [
    "dist/*.whl",           # Local builds
    "windows-wheels/*.whl", # Windows wheels
    "github_artifacts/*/*.whl",  # If you downloaded manually
]

all_wheels = []
for pattern in wheel_locations:
    wheels = glob.glob(pattern)
    all_wheels.extend(wheels)

if not all_wheels:
    print("\n❌ No wheel files found!")
    print("Looking in:", wheel_locations)
    print("\nOptions:")
    print("1. Download artifacts manually from GitHub Actions")
    print("2. Build wheels locally first")
    exit(1)

print(f"\n📦 Found {len(all_wheels)} wheel(s):")
for wheel in all_wheels:
    size_mb = os.path.getsize(wheel) / (1024 * 1024)
    print(f"  - {os.path.basename(wheel)} ({size_mb:.1f} MB)")

# Get TestPyPI token
print("\n🔑 TestPyPI Authentication")
print("Go to https://test.pypi.org/manage/account/token/ to create a token")
print("The token starts with 'pypi-'")
token = getpass.getpass("\nPaste your TestPyPI token (hidden): ")

# Set environment variables for twine
os.environ["TWINE_USERNAME"] = "__token__"
os.environ["TWINE_PASSWORD"] = token

# Upload with twine
print(f"\n🚀 Uploading {len(all_wheels)} wheels to TestPyPI...")
result = subprocess.run([
    "twine", "upload",
    "--repository", "testpypi",
    "--skip-existing",  # Skip if already uploaded
    *all_wheels
], capture_output=True, text=True)

if result.returncode == 0:
    print("\n✅ Upload successful!")
    print("\n🎉 View your package at: https://test.pypi.org/project/pyoccam/")
    print("\n📦 To install and test:")
    print("  pip install -i https://test.pypi.org/simple/ pyoccam")
else:
    print("\n❌ Upload failed!")
    print(result.stderr)
    if "403" in result.stderr:
        print("\nPossible issues:")
        print("- Invalid token (create a new one)")
        print("- Token doesn't have upload permission")
    elif "already exists" in result.stderr.lower():
        print("\nThis version already exists on TestPyPI.")
        print("To upload a new version, increment version in setup.py")
