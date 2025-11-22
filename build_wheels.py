#!/usr/bin/env python3
"""
Build pyoccam wheels for multiple Python versions.

This script automates building wheels for Python 3.9, 3.10, 3.11, 3.12, and 3.13.
It detects available Python installations and builds wheels for each version found.

Usage:
    python build_wheels.py              # Build for all found Python versions
    python build_wheels.py 3.11 3.12    # Build only for specific versions
    python build_wheels.py --clean      # Clean build directories first
"""

import subprocess
import sys
import argparse
from pathlib import Path
import shutil
import platform

# Python versions to build for
DEFAULT_VERSIONS = ['3.9', '3.10', '3.11', '3.12', '3.13']


def find_python(version):
    """
    Find Python executable for given version.

    Tries multiple common patterns:
    - python3.X (Linux/macOS)
    - pythonX.Y (Linux/macOS)
    - py -3.X (Windows py launcher)
    - python (check if it's the right version)
    """
    candidates = []

    if platform.system() == 'Windows':
        # Windows: try py launcher first, then direct python commands
        candidates = [
            f'py -{version}',
            f'python{version}',
            f'python{version.replace(".", "")}',
        ]
    else:
        # Linux/macOS: try direct python commands
        candidates = [
            f'python{version}',
            f'python{version.replace(".", "")}',
        ]

    # Also try generic python/python3
    candidates.extend(['python3', 'python'])

    for cmd in candidates:
        try:
            # Run version check
            result = subprocess.run(
                cmd.split() + ['--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Check if version matches
            if result.returncode == 0 and version in result.stdout:
                print(f"  Found Python {version}: {cmd}")
                return cmd.split()[0] if ' ' not in cmd else cmd

        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def clean_build_dirs(pyoccam_dir):
    """Remove build artifacts."""
    dirs_to_clean = [
        pyoccam_dir / 'build',
        pyoccam_dir / 'builddir',
        pyoccam_dir / '.mesonpy-*',
    ]

    for pattern in dirs_to_clean:
        if '*' in str(pattern):
            # Handle glob patterns
            for path in pyoccam_dir.glob(pattern.name):
                if path.is_dir():
                    print(f"  Removing {path}")
                    shutil.rmtree(path, ignore_errors=True)
        elif pattern.exists():
            print(f"  Removing {pattern}")
            shutil.rmtree(pattern, ignore_errors=True)


def build_wheel(python_cmd, pyoccam_dir, output_dir):
    """Build wheel for specific Python version."""
    print(f"\nBuilding wheel with {python_cmd}...")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if build module is available
    try:
        subprocess.run(
            [python_cmd, '-m', 'build', '--version'],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"  Installing 'build' module...")
        subprocess.run(
            [python_cmd, '-m', 'pip', 'install', 'build'],
            check=True
        )

    # Build wheel using python -m build
    try:
        subprocess.run([
            python_cmd, '-m', 'build',
            '--wheel',
            '--outdir', str(output_dir),
            str(pyoccam_dir)
        ], check=True, cwd=str(pyoccam_dir))

        print(f"  ✓ Wheel built successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error building wheel: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Build pyoccam wheels for multiple Python versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'versions',
        nargs='*',
        default=DEFAULT_VERSIONS,
        help=f'Python versions to build for (default: {", ".join(DEFAULT_VERSIONS)})'
    )
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Clean build directories before building'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('dist'),
        help='Output directory for wheels (default: dist/)'
    )

    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent.resolve()
    pyoccam_dir = script_dir / 'pyoccam'

    if not pyoccam_dir.exists():
        print(f"Error: pyoccam directory not found at {pyoccam_dir}")
        sys.exit(1)

    print("=" * 70)
    print("OCCAM Wheel Builder")
    print("=" * 70)
    print(f"Project directory: {script_dir}")
    print(f"PyOCCAM directory: {pyoccam_dir}")
    print(f"Output directory: {args.output}")
    print(f"Target Python versions: {', '.join(args.versions)}")
    print()

    # Clean if requested
    if args.clean:
        print("Cleaning build directories...")
        clean_build_dirs(pyoccam_dir)
        print()

    # Find Python installations
    print("Searching for Python installations...")
    found_pythons = {}
    for version in args.versions:
        python_cmd = find_python(version)
        if python_cmd:
            found_pythons[version] = python_cmd
        else:
            print(f"  Python {version} not found, skipping...")

    if not found_pythons:
        print("\nError: No compatible Python installations found!")
        print(f"Searched for versions: {', '.join(args.versions)}")
        sys.exit(1)

    print(f"\nFound {len(found_pythons)} Python installation(s)")
    print()

    # Build wheels
    print("=" * 70)
    print("Building wheels...")
    print("=" * 70)

    successful_builds = []
    failed_builds = []

    for version, python_cmd in found_pythons.items():
        success = build_wheel(python_cmd, pyoccam_dir, args.output)
        if success:
            successful_builds.append(version)
        else:
            failed_builds.append(version)

    # Summary
    print()
    print("=" * 70)
    print("Build Summary")
    print("=" * 70)
    print(f"Successful: {len(successful_builds)}/{len(found_pythons)}")
    if successful_builds:
        for version in successful_builds:
            print(f"  ✓ Python {version}")

    if failed_builds:
        print(f"\nFailed: {len(failed_builds)}")
        for version in failed_builds:
            print(f"  ✗ Python {version}")

    print()
    print(f"Wheels saved to: {args.output.resolve()}")

    # List generated wheels
    wheels = sorted(args.output.glob('*.whl'))
    if wheels:
        print(f"\nGenerated {len(wheels)} wheel(s):")
        for wheel in wheels:
            size_mb = wheel.stat().st_size / (1024 * 1024)
            print(f"  {wheel.name} ({size_mb:.2f} MB)")

    sys.exit(0 if not failed_builds else 1)


if __name__ == '__main__':
    main()
