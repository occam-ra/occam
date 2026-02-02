# pyoccam/__init__.py
"""
PyOccam - Python bindings for OCCAM Reconstructability Analysis
"""

# CRITICAL: Import from the compiled extension module 'pyoccam.pyd'
# which is built as a simple module, not nested
try:
    # The extension is built as 'pyoccam.pyd' in this folder
    # We import its contents here
    from ._pyoccam import *
except ImportError:
    # Try alternative import for development
    try:
        import _pyoccam
        from _pyoccam import *
    except ImportError as e:
        print(f"ERROR: Could not import pyoccam extension: {e}")
        print("Make sure the extension is built with: python setup.py build_ext --compiler=mingw32 --inplace")
        raise

import os
from pathlib import Path

__version__ = '0.1.2'

# Get the package directory
PACKAGE_DIR = Path(__file__).parent

# Verify the extension loaded properly
try:
    _ = VBMManager
    print(f"PyOccam {__version__} loaded successfully")
except NameError:
    print(f"ERROR: VBMManager not loaded from extension")
    print("Available names:", dir())
    raise

# ==================================
# DATA CONTAINER CLASS
# ==================================

class OccamData:
    """
    Container for OCCAM dataset information, similar to sklearn Bunch.
    
    Attributes:
        data_file: Path to the data file
        n_samples: Number of samples
        n_features: Number of features (excluding target)
        feature_names: List of feature variable names
        target_name: Name of dependent variable
        manager: VBMManager instance for analysis
        DESCR: Description of the dataset
    """
    def __init__(self, data_file, manager=None):
        self.data_file = str(data_file)
        
        # Initialize manager if not provided
        if manager is None:
            manager = VBMManager()
            if not manager.init_from_command_line(["occam", self.data_file]):
                raise RuntimeError(f"Failed to load {data_file}")
            manager.set_report_separator(SPACESEP)
            manager.set_ref_model("bottom")
        
        self.manager = manager
        
        # Extract metadata
        variables = manager.get_variable_list()
        self.n_samples = manager.get_sample_size()
        self.n_features = len(variables) - 1  # Exclude DV
        self.feature_names = variables[:-1]
        self.target_name = variables[-1] if variables else None
        self.has_test_data = manager.has_test_data()
        
    def __repr__(self):
        return (f"OccamData(n_samples={self.n_samples}, "
                f"n_features={self.n_features}, "
                f"target='{self.target_name}')")
    
    def quick_search(self, search_type="loopless-up", levels=3, width=3):
        """Run a quick search on this data."""
        report = self.manager.generate_search_report(search_type, levels, width)
        best = self.manager.get_best_model_by_bic()
        print(f"Best model: {best}")
        return best

# ==================================
# DATA LOADING FUNCTIONS
# ==================================

def load_dementia():
    """
    Load the dementia dataset.
    
    Returns:
        OccamData object with:
            - .n_samples: number of samples
            - .n_features: number of features
            - .feature_names: list of feature names
            - .target_name: name of dependent variable
            - .manager: VBMManager for analysis
            
    Example:
        >>> dementia = pyoccam.load_dementia()
        >>> print(f"{dementia.n_samples} samples, {dementia.n_features} features")
        >>> dementia.manager.generate_search_report("loopless-up", 3, 3)
        
        # Or use the convenience method:
        >>> best = dementia.quick_search()
    """
    data_file = PACKAGE_DIR / "dementia05.txt"
    if not data_file.exists():
        raise FileNotFoundError(f"Dementia data not found at {data_file}")
    
    data = OccamData(data_file)
    data.DESCR = """Dementia (Alzheimer's Disease) Dataset
Sample size: 424 subjects
Features: APOE, Gender, Education, Age, and genetic markers
Target: CaseControl (0=control, 1=case)"""
    
    print(f"✓ Loaded dementia: {data.n_samples} samples, {data.n_features} features")
    return data

def load_landslides():
    """
    Load the landslides dataset.
    
    Returns:
        OccamData object (same structure as load_dementia)
        
    Example:
        >>> landslides = pyoccam.load_landslides()
        >>> print(landslides)
        >>> landslides.manager.generate_search_report("loopless-up", 3, 3)
    """
    # Try different possible filenames
    possible_files = [
        "landslides.txt",
        "SY_sample_pts_to_occam3_shuffle_split42_hdr.txt"
    ]
    
    data_file = None
    for fname in possible_files:
        candidate = PACKAGE_DIR / fname
        if candidate.exists():
            data_file = candidate
            break
    
    if not data_file:
        available = [f.name for f in PACKAGE_DIR.glob("*.txt")]
        raise FileNotFoundError(
            f"Landslides data not found. Available: {', '.join(available[:5])}"
        )
    
    data = OccamData(data_file)
    data.DESCR = "Landslides/Geological hazard dataset"
    
    print(f"✓ Loaded landslides: {data.n_samples} samples, {data.n_features} features")
    return data

def load_data(filename):
    """
    Load any data file.
    
    Args:
        filename: Path to data file or name of packaged file
        
    Returns:
        OccamData object
        
    Example:
        >>> data = pyoccam.load_data("mydata.txt")
        >>> print(data)
    """
    # Check if it's a packaged file
    if not os.path.isabs(filename) and not os.path.exists(filename):
        packaged = PACKAGE_DIR / filename
        if packaged.exists():
            filename = str(packaged)
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Data file not found: {filename}")
    
    data = OccamData(filename)
    print(f"✓ Loaded {os.path.basename(filename)}: {data.n_samples} samples")
    return data

# ==================================
# DEMO ACCESS FUNCTIONS
# ==================================

def get_demo_script(copy_to_current=False):
    """Get or copy the demo script."""
    demo_file = PACKAGE_DIR / "pyoccam_demo.py"
    
    if not demo_file.exists():
        raise FileNotFoundError(f"Demo script not found at {demo_file}")
    
    if copy_to_current:
        import shutil
        dest = Path("pyoccam_demo.py")
        shutil.copy2(demo_file, dest)
        print(f"✓ Copied demo script to: {dest.absolute()}")
        return str(dest.absolute())
    else:
        return str(demo_file)

def get_demo_notebook(copy_to_current=False):
    """Get or copy the demo notebook."""
    notebook_file = PACKAGE_DIR / "pyoccam_demo.ipynb"
    
    if not notebook_file.exists():
        notebooks = list(PACKAGE_DIR.glob("*.ipynb"))
        if notebooks:
            notebook_file = notebooks[0]
        else:
            raise FileNotFoundError("No notebook files found in package")
    
    if copy_to_current:
        import shutil
        dest = Path(notebook_file.name)
        shutil.copy2(notebook_file, dest)
        print(f"✓ Copied notebook to: {dest.absolute()}")
        return str(dest.absolute())
    else:
        return str(notebook_file)

def run_demo():
    """Run the demo script."""
    demo_file = PACKAGE_DIR / "pyoccam_demo.py"
    if demo_file.exists():
        import subprocess
        import sys
        original_dir = os.getcwd()
        try:
            os.chdir(PACKAGE_DIR)
            subprocess.run([sys.executable, str(demo_file)])
        finally:
            os.chdir(original_dir)
    else:
        print("Demo not found. Try: pyoccam.get_demo_script(copy_to_current=True)")

# ==================================
# CONVENIENCE FUNCTIONS
# ==================================

def quick_search(data_or_file="dementia05.txt", search_type="loopless-up", levels=3, width=3):
    """
    Quick one-line search.
    
    Args:
        data_or_file: OccamData object, filename, or "dementia05.txt" (default)
        
    Returns:
        tuple of (data_object, best_model_name)
        
    Example:
        >>> data, best = pyoccam.quick_search()
        >>> print(f"Best: {best}")
    """
    if isinstance(data_or_file, OccamData):
        data = data_or_file
    elif data_or_file == "dementia05.txt":
        data = load_dementia()
    else:
        data = load_data(data_or_file)
    
    report = data.manager.generate_search_report(search_type, levels, width)
    best = data.manager.get_best_model_by_bic()
    
    print(f"Search complete. Best model: {best}")
    return data, best

def help():
    """Show help."""
    print(f"""
PyOccam {__version__} - Quick Help
{'='*60}

LOADING DATA (returns data object with .manager attribute):
  dementia = pyoccam.load_dementia()      # Load dementia dataset
  landslides = pyoccam.load_landslides()  # Load landslides dataset
  data = pyoccam.load_data("file.txt")    # Load any file

USING DATA OBJECTS:
  print(dementia.n_samples)               # Number of samples
  print(dementia.feature_names)           # Feature variable names
  print(dementia.target_name)             # Dependent variable name
  manager = dementia.manager              # Access the VBMManager
  
  # Convenience method on data object:
  best = dementia.quick_search()          # Run search on this data

STANDARD WORKFLOW:
  # 1. Load data
  data = pyoccam.load_dementia()
  
  # 2. Get the manager
  manager = data.manager
  
  # 3. Configure (Don't include ID or Model!)
  manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC")
  
  # 4. Run search
  report = manager.generate_search_report("loopless-up", 7, 3)
  
  # 5. Get best model
  best = manager.get_best_model_by_bic()

DEMOS:
  pyoccam.run_demo()                      # Run demo
  pyoccam.get_demo_script(copy_to_current=True)   # Copy demo locally
  pyoccam.get_demo_notebook(copy_to_current=True) # Copy notebook

Type pyoccam.help() to see this again.
""")

# Welcome message
print(f"PyOccam {__version__} loaded. Type pyoccam.help() for usage.")