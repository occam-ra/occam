"""
Pyoccam Examples Package
========================

This package contains demo scripts and Jupyter notebooks to help you get started with pyoccam.

Quick Start
-----------

Copy all examples to your current directory:
    >>> import pyoccam
    >>> pyoccam.examples.copy_examples()

List available examples:
    >>> pyoccam.examples.list_examples()

Get the path to examples:
    >>> pyoccam.examples.get_example_path()
"""

import shutil
from pathlib import Path

__version__ = "0.9.0"

def get_example_path():
    """
    Get the path to the examples directory.
    
    Returns:
        Path: Path to the installed examples directory
        
    Example:
        >>> import pyoccam
        >>> path = pyoccam.examples.get_example_path()
        >>> print(f"Examples are at: {path}")
    """
    return Path(__file__).parent

def list_examples():
    """
    List all available examples.
    
    Shows the scripts and notebooks included with pyoccam.
    
    Example:
        >>> import pyoccam
        >>> pyoccam.list_examples()
    """
    examples_dir = get_example_path()
    
    print("=" * 60)
    print("PYOCCAM EXAMPLES")
    print("=" * 60)
    print(f"\nInstalled at: {examples_dir}")
    
    # List Python scripts
    scripts = sorted(examples_dir.glob("*.py"))
    if scripts:
        print("\n📝 Python Scripts:")
        for script in scripts:
            print(f"  • {script.name}")
    
    # List Jupyter notebooks
    notebooks = sorted(examples_dir.glob("*.ipynb"))
    if notebooks:
        print("\n📓 Jupyter Notebooks:")
        for notebook in notebooks:
            print(f"  • {notebook.name}")
    
    # Show usage
    print("\n" + "=" * 60)
    print("HOW TO USE")
    print("=" * 60)
    print("\n1. Copy examples to current directory:")
    print("   >>> pyoccam.copy_examples()")
    print("\n2. Or run directly from package:")
    print("   >>> from pyoccam.examples import basic_analysis")
    print("   >>> basic_analysis.main()")
    print("\n3. Or use command line:")
    print("   $ pyoccam-examples --copy")
    print("=" * 60)

def copy_examples(destination=None, overwrite=False):
    """
    Copy all examples to a directory.
    
    Args:
        destination (str or Path, optional): Where to copy examples.
            Defaults to './pyoccam_examples' in current directory.
        overwrite (bool): If True, overwrite existing files. Default False.
        
    Returns:
        Path: Path where examples were copied
        
    Example:
        >>> import pyoccam
        >>> # Copy to current directory
        >>> pyoccam.examples.copy_examples()
        >>> 
        >>> # Copy to specific location
        >>> pyoccam.examples.copy_examples("~/my_project/examples")
    """
    examples_dir = get_example_path()
    
    # Set destination
    if destination is None:
        dest = Path.cwd() / "pyoccam_examples"
    else:
        dest = Path(destination).expanduser().resolve()
    
    # Check if destination exists
    if dest.exists() and not overwrite:
        print(f"⚠ Destination already exists: {dest}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Copy cancelled.")
            return None
    
    print(f"📦 Copying examples to: {dest}")
    
    # Create destination directory
    dest.mkdir(parents=True, exist_ok=True)
    
    # Copy Python scripts
    for script in examples_dir.glob("*.py"):
        if script.name != '__init__.py':  # Don't copy __init__.py
            shutil.copy2(script, dest / script.name)
            print(f"  ✓ Copied script: {script.name}")
    
    # Copy Jupyter notebooks
    for notebook in examples_dir.glob("*.ipynb"):
        shutil.copy2(notebook, dest / notebook.name)
        print(f"  ✓ Copied notebook: {notebook.name}")
    
    # Copy README if exists
    readme = examples_dir / "README.md"
    if readme.exists():
        shutil.copy2(readme, dest / "README.md")
        print(f"  ✓ Copied README.md")
    
    print(f"\n✅ Examples copied successfully!")
    print(f"📂 Location: {dest}")
    print(f"\n💡 Next steps:")
    print(f"   1. Edit scripts to use your data")
    print(f"   2. Run: python {dest}/basic_analysis.py")
    print(f"   3. Or open notebooks: jupyter notebook {dest}/basic_analysis.ipynb")
    
    return dest

def cli_main():
    """
    Command-line interface for pyoccam examples.
    
    This is called when user runs: pyoccam-examples
    """
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--copy', '-c']:
            copy_examples()
        elif sys.argv[1] in ['--list', '-l']:
            list_examples()
        elif sys.argv[1] in ['--path', '-p']:
            print(get_example_path())
        elif sys.argv[1] in ['--help', '-h']:
            print(__doc__)
            print("\nCommands:")
            print("  --copy, -c    Copy examples to current directory")
            print("  --list, -l    List all available examples")
            print("  --path, -p    Show path to examples")
            print("  --help, -h    Show this help message")
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Default: show list
        list_examples()

# Make submodules importable
__all__ = [
    'get_example_path',
    'list_examples', 
    'copy_examples',
    'cli_main',
]
