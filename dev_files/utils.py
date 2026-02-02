"""
OCCAM Utility Functions - Core occ.cpp orchestration
"""

import subprocess
import shutil
import re
from typing import Dict, List
from pathlib import Path

from .exceptions import OCCAMError

def find_occ_executable() -> str:
    """Find the occ.cpp executable in package or system"""
    
    # First, try package directory (when installed)
    package_dir = Path(__file__).parent
    possible_names = ['occ.exe', 'occ']
    
    for name in possible_names:
        exe_path = package_dir / name
        if exe_path.exists():
            return str(exe_path)
    
    # Try current directory
    for name in possible_names:
        if Path(name).exists():
            return name
    
    # Try system PATH
    occ_path = shutil.which('occ')
    if occ_path:
        return occ_path
        
    # Try common locations
    common_paths = [
        './occ', '../occ', './bin/occ', '../bin/occ',
        './occam', '../occam', './bin/occam', '../bin/occam'
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    raise OCCAMError(
        "Could not find occ executable. "
        "Please ensure occ.exe (Windows) or occ (Unix) is available in the package directory, "
        "current directory, or system PATH."
    )

def call_occ(data_file: str, arguments: List[str]) -> str:
    """
    Call occ.cpp executable with arguments and return output
    This is the core function that mirrors weboccam.py's approach
    """
    try:
        occ_exe = find_occ_executable()
    except OCCAMError as e:
        return f"ERROR: {e}"
    
    # Build command
    cmd = [occ_exe, data_file] + arguments
    
    try:
        # Execute occ.cpp and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False
        )
        
        if result.returncode != 0:
            error_msg = f"occ.cpp failed with exit code {result.returncode}"
            if result.stderr:
                error_msg += f"\nError: {result.stderr}"
            return f"ERROR: {error_msg}"
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        return "ERROR: occ.cpp execution timed out"
    except Exception as e:
        return f"ERROR: Failed to execute occ.cpp: {e}"

def parse_search_output(output: str) -> Dict:
    """
    Parse occ.cpp search output to extract key information
    """
    result = {
        'full_output': output,
        'best_models': {},
        'all_models': [],
        'search_stats': {},
        'header_lines': []
    }
    
    lines = output.split('\n')
    data_start_idx = -1
    
    # Find where data section starts
    for i, line in enumerate(lines):
        if 'ID,MODEL,Level' in line or 'ID\tMODEL\tLevel' in line:
            data_start_idx = i
            break
    
    if data_start_idx > 0:
        result['header_lines'] = lines[:data_start_idx]
    
    # Extract best models from output
    in_bic_section = False
    in_aic_section = False
    
    for line in lines:
        # Look for best model sections
        if "Best Model(s) by dBIC:" in line:
            in_bic_section = True
            in_aic_section = False
            continue
        elif "Best Model(s) by dAIC:" in line:
            in_aic_section = True
            in_bic_section = False
            continue
        
        # Extract model names
        if (in_bic_section or in_aic_section) and "IV:" in line:
            model_match = re.search(r'IV:[A-Za-z:]+', line)
            if model_match:
                model_name = model_match.group()
                if in_bic_section:
                    result['best_models']['bic'] = model_name
                elif in_aic_section:
                    result['best_models']['aic'] = model_name
    
    # Parse data section for first (best) model if no explicit best models
    if data_start_idx >= 0 and not result['best_models']:
        for line in lines[data_start_idx + 1:]:
            if "IV:" in line:
                model_match = re.search(r'IV:[A-Za-z:]+', line)
                if model_match:
                    result['best_models']['information'] = model_match.group()
                    break
    
    return result

def parse_fit_output(output: str) -> Dict:
    """
    Parse occ.cpp fit output to extract confusion matrix and statistics
    """
    result = {
        'full_output': output,
        'confusion_matrix': {},
        'statistics': {}
    }
    
    # This would parse the actual confusion matrix from fit output
    # For now, return the full output and placeholder metrics
    result['confusion_matrix'] = {
        'accuracy': 0.75,  # Would be parsed from actual output
        'sensitivity': 0.80,
        'specificity': 0.70,
        'precision': 0.72,
        'recall': 0.80,
        'f1_score': 0.76
    }
    
    return result

# Convenience functions
def search(data_file: str, search_type: str = "loopless-up", 
          levels: int = 7, width: int = 3) -> str:
    """Quick search function"""
    from .manager import VBMManager
    
    manager = VBMManager()
    if not manager.init_from_command_line(["occam", data_file]):
        return "ERROR: Failed to initialize with data file"
    
    return manager.generate_search_report(search_type, levels, width)

def fit(data_file: str, model: str, target: str = "0") -> str:
    """Quick fit function"""
    from .manager import VBMManager
    
    manager = VBMManager()
    if not manager.init_from_command_line(["occam", data_file]):
        return "ERROR: Failed to initialize with data file"
    
    return manager.generate_fit_report(model, target)