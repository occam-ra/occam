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

__version__ = '0.9.3'  # Added make_occam_input_from_csv() converter function

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
    
    Attributes:
        data_file: Path to the loaded data file
        n_samples: Number of samples in training data
        n_features: Number of independent variables (excluding dependent variable)
        feature_names: List of independent variable names
        target_name: Name of the dependent variable (last column)
        manager: VBMManager instance for running analyses
        has_test_data: Boolean flag indicating test data presence
        DESCR: Optional description of the dataset (set by load functions)
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
        OccamData object with .manager attribute for analysis
    """
    data_file = PACKAGE_DIR / "dementia05.txt"
    if not data_file.exists():
        raise FileNotFoundError(f"Dementia data not found at {data_file}")
    
    data = OccamData(data_file)
    data.DESCR = """Dementia (Alzheimer's Disease) Dataset
Sample size: 424 subjects
Features: APOE, Gender, Education, Age, and genetic markers
Target: CaseControl (0=control, 1=case)"""
    
    print(f"[OK] Loaded dementia: {data.n_samples} samples, {data.n_features} features")
    return data

def load_landslides():
    """
    Load the landslides dataset.
    
    Returns:
        OccamData object (same structure as load_dementia)
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
    
    print(f"[OK] Loaded landslides: {data.n_samples} samples, {data.n_features} features")
    return data

def load_data(filename):
    """
    Load any data file.
    
    Args:
        filename: Path to data file or name of packaged file
        
    Returns:
        OccamData object
    """
    # Check if it's a packaged file
    if not os.path.isabs(filename) and not os.path.exists(filename):
        packaged = PACKAGE_DIR / filename
        if packaged.exists():
            filename = str(packaged)
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Data file not found: {filename}")
    
    data = OccamData(filename)
    print(f"[OK] Loaded {os.path.basename(filename)}: {data.n_samples} samples")
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
        print(f"[OK] Copied demo script to: {dest.absolute()}")
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
        print(f"[OK] Copied notebook to: {dest.absolute()}")
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
  
  # 3. Run search
  report = manager.generate_search_report("loopless-up", 7, 3)
  
  # 4. Get best model (choose criterion)
  best = manager.get_best_model_by_bic()           # Most parsimonious
  best = manager.get_best_model_by_information()   # Highest info (alpha < 0.05)
  best = manager.get_best_model_by_aic()           # Intermediate

CSV CONVERSION:
  # Convert CSV to OCCAM format (last column = DV, auto-exclude high cardinality)
  output_file, data = pyoccam.make_occam_input_from_csv("mydata.csv")
  
  # With options:
  output_file, data = pyoccam.make_occam_input_from_csv(
      "mydata.csv",
      max_cardinality=20,           # Exclude columns with >20 unique values
      dv_column="target",           # Specify DV column by name
      exclude_columns=["ID", "Name"] # Always exclude these columns
  )
  
  # Then analyze:
  best = data.quick_search()

DEMOS:
  pyoccam.run_demo()                      # Run demo
  pyoccam.get_demo_script(copy_to_current=True)   # Copy demo locally
  pyoccam.get_demo_notebook(copy_to_current=True) # Copy notebook

Type pyoccam.help() to see this again.
""")

# ==================================
# CSV TO OCCAM CONVERTER
# ==================================

def make_occam_input_from_csv(csv_filename, output_filename=None, max_cardinality=20, 
                               dv_column=None, exclude_columns=None, verbose=True):
    """
    Convert a standard CSV file to OCCAM input format.
    
    Automatically detects categorical vs numeric columns, computes cardinality,
    and generates appropriate variable definitions. Columns with cardinality > max_cardinality
    are automatically excluded (set to role=0).
    
    Args:
        csv_filename: Path to input CSV file
        output_filename: Path for output OCCAM file (default: same name with .txt extension)
        max_cardinality: Maximum unique values before column is excluded (default: 20)
        dv_column: Name or index of dependent variable column (default: last column)
        exclude_columns: List of column names to always exclude (e.g., ['ID', 'Pt_ID'])
        verbose: Print progress messages (default: True)
        
    Returns:
        tuple: (output_path, OccamData object) - ready for analysis
        
    Example:
        >>> output_file, data = pyoccam.make_occam_input_from_csv("mydata.csv")
        >>> best = data.quick_search()
    """
    import csv
    from collections import Counter
    from pathlib import Path
    
    csv_path = Path(csv_filename)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    # Default output filename
    if output_filename is None:
        output_filename = csv_path.with_suffix('.txt')
    output_path = Path(output_filename)
    
    exclude_columns = set(exclude_columns or [])
    
    if verbose:
        print(f"Reading CSV: {csv_path}")
    
    # Read CSV and analyze columns
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Initialize column data structures
        n_cols = len(headers)
        column_values = [[] for _ in range(n_cols)]
        
        # Read all data rows
        rows = []
        for row in reader:
            if len(row) == n_cols:  # Skip malformed rows
                rows.append(row)
                for i, val in enumerate(row):
                    column_values[i].append(val)
    
    n_samples = len(rows)
    if verbose:
        print(f"  Found {n_samples} samples, {n_cols} columns")
    
    # Determine DV column
    if dv_column is None:
        dv_idx = n_cols - 1  # Last column
    elif isinstance(dv_column, int):
        dv_idx = dv_column
    else:
        try:
            dv_idx = headers.index(dv_column)
        except ValueError:
            raise ValueError(f"DV column '{dv_column}' not found in headers")
    
    if verbose:
        print(f"  Dependent variable: {headers[dv_idx]} (column {dv_idx})")
    
    # Analyze each column
    column_info = []
    used_abbrevs = set()
    
    def make_abbreviation(name, used):
        """Generate a unique 2-letter abbreviation from column name."""
        # Clean the name
        clean = ''.join(c for c in name if c.isalnum())
        
        # Try first two letters (lowercase)
        if len(clean) >= 2:
            abbr = clean[:2].lower()
            if abbr not in used:
                used.add(abbr)
                return abbr
        
        # Try first letter + consonants
        consonants = ''.join(c for c in clean[1:] if c.lower() not in 'aeiou')
        if consonants:
            abbr = (clean[0] + consonants[0]).lower()
            if abbr not in used:
                used.add(abbr)
                return abbr
        
        # Try first letter + number
        for i in range(1, 100):
            abbr = f"{clean[0].lower()}{i}"
            if abbr not in used:
                used.add(abbr)
                return abbr
        
        return clean[:2].lower()  # Fallback
    
    for i, (name, values) in enumerate(zip(headers, column_values)):
        unique_values = sorted(set(values))
        cardinality = len(unique_values)
        
        # Create value-to-index mapping
        value_map = {v: idx for idx, v in enumerate(unique_values)}
        
        # Determine role: 0=exclude, 1=IV, 2=DV
        if i == dv_idx:
            role = 2  # Dependent variable
            include = True
            reason = "DV"
        elif name in exclude_columns:
            role = 0  # Excluded by user
            include = False
            reason = "user excluded"
        elif cardinality > max_cardinality:
            role = 0  # Excluded due to high cardinality
            include = False
            reason = f"cardinality {cardinality} > {max_cardinality}"
        elif cardinality < 2:
            role = 0  # Constant column
            include = False
            reason = "constant (cardinality < 2)"
        else:
            role = 1  # Independent variable
            include = True
            reason = "IV"
        
        abbrev = make_abbreviation(name, used_abbrevs)
        
        column_info.append({
            'name': name,
            'cardinality': cardinality,
            'role': role,
            'abbrev': abbrev,
            'include': include,
            'reason': reason,
            'value_map': value_map,
            'unique_values': unique_values
        })
    
    # Report column decisions
    included = [c for c in column_info if c['include']]
    excluded = [c for c in column_info if not c['include']]
    
    if verbose:
        print(f"\n  Included columns ({len(included)}):")
        for c in included:
            print(f"    {c['abbrev']:4s} {c['name'][:30]:30s} card={c['cardinality']:3d} ({c['reason']})")
        
        if excluded:
            print(f"\n  Excluded columns ({len(excluded)}):")
            for c in excluded:
                print(f"    {c['abbrev']:4s} {c['name'][:30]:30s} card={c['cardinality']:3d} ({c['reason']})")
    
    # Write OCCAM format file
    if verbose:
        print(f"\nWriting OCCAM file: {output_path}")
    
    with open(output_path, 'w') as f:
        # Header
        f.write(":nominal\n")
        
        # Variable definitions
        for col in column_info:
            # Format: name, cardinality, role, abbreviation
            f.write(f"{col['name']}, {col['cardinality']}, {col['role']}, {col['abbrev']}\n")
        
        # Data section
        f.write(":no-frequency\n")
        f.write(":data\n")
        
        # Data rows (convert values to indices)
        for row in rows:
            converted = []
            for i, val in enumerate(row):
                idx = column_info[i]['value_map'].get(val, 0)
                converted.append(str(idx))
            f.write(','.join(converted) + '\n')
    
    if verbose:
        print(f"[OK] Created OCCAM input file: {output_path}")
        print(f"  {n_samples} samples, {len(included)} active variables")
    
    # Load and return the data object
    try:
        data = OccamData(output_path)
        return str(output_path), data
    except Exception as e:
        print(f"[!] Warning: Could not load generated file: {e}")
        return str(output_path), None


# Alias for convenience
csv_to_occam = make_occam_input_from_csv


# Welcome message
print(f"PyOccam {__version__} loaded. Type pyoccam.help() for usage.")
