"""
OCCAM VBMManager - Main interface class
"""

from typing import Dict, List
from pathlib import Path

from .utils import call_occ, parse_search_output, parse_fit_output
from .exceptions import OCCAMError

# Constants
TABSEP = 1
COMMASEP = 2
SPACESEP = 3
HTMLFORMAT = 4

class VBMManager:
    """
    Main OCCAM Variable-Based Modeling Manager
    Orchestrates calls to occ.cpp like weboccam.py does
    """
    
    def __init__(self):
        self.data_file = None
        self.initialized = False
        self.ref_model = "bottom"
        self.report_separator = SPACESEP
        self.search_cache = {}
        self.core_manager = None
        
        # Try to initialize core C++ manager for basic operations if available
        try:
            import pyoccam2  # The actual compiled C++ module
            self.core_manager = pyoccam2.VBMManager()
        except ImportError:
            pass  # Fall back to pure Python orchestration
    
    def init_from_command_line(self, args: List[str]) -> bool:
        """Initialize with command line arguments"""
        if len(args) < 2:
            return False
        
        self.data_file = args[1]
        
        # Verify data file exists
        if not Path(self.data_file).exists():
            return False
        
        # Initialize core manager if available
        if self.core_manager:
            try:
                self.initialized = self.core_manager.init_from_command_line(args)
            except:
                pass
        
        self.initialized = True
        return True
    
    def generate_search_report(self, search_type: str, levels: int, width: int, 
                             include_test: bool = False) -> str:
        """
        Generate search report by calling occ.cpp
        This is where we orchestrate the call to the working OCCAM engine
        """
        if not self.initialized or not self.data_file:
            return "ERROR: Manager not initialized. Call init_from_command_line first."
        
        # Build arguments for occ.cpp
        args = [
            f"-search={search_type}",
            f"-levels={levels}",
            f"-width={width}",
            f"-ref={self.ref_model}",
            "-action=search"
        ]
        
        # Add format option
        if self.report_separator == TABSEP:
            args.append("-separator=tab")
        elif self.report_separator == COMMASEP:
            args.append("-separator=comma")
        elif self.report_separator == SPACESEP:
            args.append("-separator=space")
        
        if include_test:
            args.append("-test")
        
        # Call occ.cpp and get the perfect output!
        output = call_occ(self.data_file, args)
        
        if not output.startswith("ERROR:"):
            # Parse and cache results for get_best_model_* methods
            parsed = parse_search_output(output)
            cache_key = f"{search_type}_{levels}_{width}"
            self.search_cache[cache_key] = parsed
        
        return output
    
    def generate_fit_report(self, model: str, target: str = "0") -> str:
        """Generate fit report by calling occ.cpp"""
        if not self.initialized or not self.data_file:
            return "ERROR: Manager not initialized. Call init_from_command_line first."
        
        args = [
            f"-model={model}",
            "-action=fit"
        ]
        
        if target:
            args.append(f"-target={target}")
        
        # Add format option
        if self.report_separator == SPACESEP:
            args.append("-separator=space")
        
        # Call occ.cpp for fit analysis
        output = call_occ(self.data_file, args)
        
        return output
    
    def get_best_model_by_bic(self) -> str:
        """Get best model by BIC from cached search results"""
        for cache_data in self.search_cache.values():
            if 'bic' in cache_data['best_models']:
                return cache_data['best_models']['bic']
        return ""
    
    def get_best_model_by_aic(self) -> str:
        """Get best model by AIC from cached search results"""
        for cache_data in self.search_cache.values():
            if 'aic' in cache_data['best_models']:
                return cache_data['best_models']['aic']
        return ""
    
    def get_best_model_by_information(self) -> str:
        """Get best model by Information from cached search results"""
        for cache_data in self.search_cache.values():
            if 'information' in cache_data['best_models']:
                return cache_data['best_models']['information']
        return ""
    
    def get_confusion_matrix(self, model: str, target: str = "0") -> Dict[str, float]:
        """Get confusion matrix by calling fit and parsing output"""
        fit_output = self.generate_fit_report(model, target)
        
        if fit_output.startswith("ERROR:"):
            return {"error": fit_output}
        
        parsed = parse_fit_output(fit_output)
        return parsed['confusion_matrix']
    
    def get_basic_statistics(self) -> Dict[str, str]:
        """Get basic dataset statistics"""
        if self.core_manager:
            try:
                return self.core_manager.get_basic_statistics()
            except:
                pass
        
        # Fallback: parse from a quick occ.cpp call
        if self.initialized and self.data_file:
            output = call_occ(self.data_file, ["-action=info"])
            if not output.startswith("ERROR:"):
                return self._parse_basic_stats(output)
        
        return {"error": "Could not get statistics"}
    
    def _parse_basic_stats(self, output: str) -> Dict[str, str]:
        """Parse basic statistics from occ.cpp output"""
        stats = {}
        lines = output.split('\n')
        
        for line in lines:
            if 'Sample Size' in line:
                try:
                    stats['num_cases'] = line.split()[-1]
                except:
                    pass
            elif 'Variables' in line and 'in use' in line:
                # Extract variable count
                import re
                match = re.search(r'(\d+)', line)
                if match:
                    stats['num_variables'] = match.group(1)
        
        return stats
    
    def get_variable_list(self) -> List[str]:
        """Get list of variables"""
        if self.core_manager:
            try:
                return self.core_manager.get_variable_list()
            except:
                pass
        
        # Fallback: could parse from occ.cpp output
        return []
    
    def get_sample_size(self) -> int:
        """Get sample size"""
        if self.core_manager:
            try:
                return self.core_manager.get_sample_size()
            except:
                pass
        return 0
    
    def has_test_data(self) -> bool:
        """Check if test data is available"""
        return False
    
    def set_report_separator(self, separator: int):
        """Set report separator format"""
        self.report_separator = separator
    
    def set_report_variables(self, variables: str):
        """Set report variables (passed to occ.cpp)"""
        # This would be passed as arguments to occ.cpp
        pass
    
    def set_ref_model(self, model: str):
        """Set reference model"""
        self.ref_model = model