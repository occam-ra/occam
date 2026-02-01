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

__version__ = '0.9.2'  # Fixed get_best_model_by_information() to match OCCAM manual

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
    Container for OCCAM dataset information, similar to sklearn's Bunch.
    
    This class provides a sklearn-compatible interface for OCCAM datasets,
    wrapping the VBMManager with convenient attributes and methods.
    
    KEY DESIGN DECISIONS:
    - Automatic initialization: Creates and configures VBMManager on construction
    - Lazy computation: Metadata extracted after successful data load
    - Convenience methods: Provides quick_search() for rapid exploration
    - Test data support: Automatically detects and flags test data presence
    
    Attributes:
        data_file: Path to the loaded data file
        n_samples: Number of samples in training data
        n_features: Number of independent variables (excluding dependent variable)
        feature_names: List of independent variable names
        target_name: Name of the dependent variable (last column)
        manager: VBMManager instance for running analyses
        has_test_data: Boolean flag indicating test data presence
        DESCR: Optional description of the dataset (set by load functions)
    
    Usage Examples:
        # Load and explore dataset:
        >>> data = pyoccam.load_dementia()
        >>> print(f"{data.n_samples} samples, {data.n_features} features")
        >>> print(f"Target variable: {data.target_name}")
        
        # Access manager for analysis:
        >>> report = data.manager.generate_search_report("loopless-up", 3, 3)
        >>> best = data.manager.get_best_model_by_bic()
        
        # Convenience method:
        >>> best = data.quick_search()  # Shortcut for above
    """
    def __init__(self, data_file, manager=None):
        self.data_file = str(data_file)
        
        # Initialize manager if not provided
        if manager is None:
            manager = VBMManager()
            if not manager.init_from_command_line(["occam", self.data_file]):
                raise RuntimeError(f"Failed to load {data_file}")
            # Set sensible defaults for report formatting
            manager.set_report_separator(SPACESEP)
            manager.set_ref_model("bottom")
        
        self.manager = manager
        
        # Extract metadata from loaded data
        variables = manager.get_variable_list()
        self.n_samples = manager.get_sample_size()
        self.n_features = len(variables) - 1  # Exclude DV
        self.feature_names = variables[:-1]   # All but last
        self.target_name = variables[-1] if variables else None
        self.has_test_data = manager.has_test_data()
        
    def __repr__(self):
        return (f"OccamData(n_samples={self.n_samples}, "
                f"n_features={self.n_features}, "
                f"target='{self.target_name}')")
    
    def quick_search(self, search_type="loopless-up", levels=3, width=3):
        """
        Run a quick exploratory search on this dataset.
        
        Convenience method that runs beam search and returns the best model
        by BIC criterion. Equivalent to:
            report = self.manager.generate_search_report(...)
            best = self.manager.get_best_model_by_bic()
        
        Args:
            search_type: Search algorithm (default: "loopless-up")
            levels: Number of levels to search (default: 3)
            width: Beam width (default: 3)
        
        Returns:
            String name of best model (e.g., "IV:ApZ:EdZ")
        """
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
    
    print(f"âœ“ Loaded dementia: {data.n_samples} samples, {data.n_features} features")
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
    
    print(f"âœ“ Loaded landslides: {data.n_samples} samples, {data.n_features} features")
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
    print(f"âœ“ Loaded {os.path.basename(filename)}: {data.n_samples} samples")
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
        print(f"âœ“ Copied demo script to: {dest.absolute()}")
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
        print(f"âœ“ Copied notebook to: {dest.absolute()}")
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
  
  # 5. Get best model (choose criterion)
  best = manager.get_best_model_by_bic()           # Most parsimonious
  best = manager.get_best_model_by_information()   # Highest info with ALL steps Inc.Alpha < 0.05
  best = manager.get_best_model_by_aic()           # Intermediate
  # WARNING: Avoid get_best_model_by_raw_information() - may return overfitted models!

DEMOS:
  pyoccam.run_demo()                      # Run demo
  pyoccam.get_demo_script(copy_to_current=True)   # Copy demo locally
  pyoccam.get_demo_notebook(copy_to_current=True) # Copy notebook

Type pyoccam.help() to see this again.
""")

# Welcome message
print(f"PyOccam {__version__} loaded. Type pyoccam.help() for usage.")