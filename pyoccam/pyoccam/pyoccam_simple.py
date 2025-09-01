"""
pyoccam_simple.py - Simple, Clean Interface for OCCAM Python Package
Version 3.4.2-multilevel

Provides a high-level, pandas-compatible interface for OCCAM analysis
"""

import pyoccam
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Union
import re

class Model:
    """High-level OCCAM Model interface for easy use in Jupyter notebooks"""
    
    def __init__(self, data_file: str, debug: bool = False):
        """
        Initialize OCCAM model with data file
        
        Parameters:
        -----------
        data_file : str
            Path to OCCAM data file
        debug : bool
            Enable debug output (default: False)
        """
        self.manager = pyoccam.VBMManager()
        self.manager.set_debug_mode(debug)
        self.data_file = data_file
        self.debug = debug
        
        # Initialize from data file
        if not self.manager.init_from_command_line(['occam', data_file]):
            raise ValueError(f"Failed to load data file: {data_file}")
        
        # Cache for fitted models
        self._model_cache = {}
        self._last_search_results = None
        
    def search(self, 
               levels: int = 7, 
               width: int = 3,
               algorithm: str = "loopless-up",
               as_dataframe: bool = True) -> Union[pd.DataFrame, str]:
        """
        Perform multi-level search for best models
        
        Parameters:
        -----------
        levels : int
            Number of levels to search (default: 7)
        width : int
            Number of models to keep per level (default: 3)
        algorithm : str
            Search algorithm (default: "loopless-up")
            Options: loopless-up, loopless-down, full-up, full-down, etc.
        as_dataframe : bool
            Return results as pandas DataFrame (default: True)
            
        Returns:
        --------
        DataFrame or str : Search results
        """
        # Perform search
        result = self.manager.generate_search_report(algorithm, levels, width)
        
        if not as_dataframe:
            return result
        
        # Parse results into DataFrame
        df = self._parse_search_results(result)
        self._last_search_results = df
        
        return df
    
    def fit(self, model_name: str, return_report: bool = False) -> Union[Dict, str]:
        """
        Fit a specific model and get detailed statistics
        
        Parameters:
        -----------
        model_name : str
            Model specification (e.g., "IV:ApZ:EdZ")
        return_report : bool
            Return full text report instead of dict (default: False)
            
        Returns:
        --------
        dict or str : Model statistics or full report
        """
        # Check cache
        if model_name in self._model_cache and not return_report:
            return self._model_cache[model_name]
        
        # Generate fit report
        report = self.manager.generate_fit_report(model_name)
        
        if return_report:
            return report
        
        # Parse statistics
        stats = self._parse_fit_report(report)
        stats['model'] = model_name
        
        # Cache results
        self._model_cache[model_name] = stats
        
        return stats
    
    def compare_algorithms(self, 
                          levels: int = 3, 
                          width: int = 5) -> pd.DataFrame:
        """
        Compare different search algorithms
        
        Parameters:
        -----------
        levels : int
            Number of levels for comparison (default: 3)
        width : int
            Search width for comparison (default: 5)
            
        Returns:
        --------
        DataFrame : Comparison results
        """
        comparison_text = self.manager.compare_search_algorithms(levels, width)
        
        # Parse comparison into DataFrame
        algorithms = []
        current_algo = {}
        
        for line in comparison_text.split('\n'):
            if 'Algorithm:' in line:
                if current_algo:
                    algorithms.append(current_algo)
                algo_name = line.split('Algorithm:')[1].strip()
                current_algo = {'algorithm': algo_name}
            elif 'Models generated:' in line:
                count = int(line.split(':')[1].strip())
                current_algo['model_count'] = count
            elif 'Best information:' in line:
                info = float(line.split(':')[1].strip())
                current_algo['best_information'] = info
        
        if current_algo:
            algorithms.append(current_algo)
        
        return pd.DataFrame(algorithms)
    
    def get_variables(self) -> List[str]:
        """Get list of variables in the dataset"""
        return self.manager.get_variable_list()
    
    def get_statistics(self) -> Dict:
        """Get basic dataset statistics"""
        return self.manager.get_basic_statistics()
    
    def get_best_model(self, criterion: str = 'bic') -> Optional[str]:
        """
        Get the best model from last search by criterion
        
        Parameters:
        -----------
        criterion : str
            Selection criterion: 'bic', 'aic', or 'information'
            
        Returns:
        --------
        str : Best model name or None if no search performed
        """
        if self._last_search_results is None:
            return None
        
        df = self._last_search_results
        
        if criterion == 'bic':
            # Lower BIC is better
            best_idx = df['BIC'].idxmin()
        elif criterion == 'aic':
            # Lower AIC is better
            best_idx = df['AIC'].idxmin()
        else:  # information
            # Higher information is better
            best_idx = df['Information'].idxmax()
        
        return df.loc[best_idx, 'Model']
    
    def create_report(self) -> 'Report':
        """Create a custom Report object for advanced formatting"""
        return Report(self.manager)
    
    def _parse_search_results(self, text: str) -> pd.DataFrame:
        """Parse search results text into DataFrame"""
        lines = text.split('\n')
        data = []
        
        for line in lines:
            # Look for model lines (contain IV:)
            if 'IV:' in line or 'IV ' in line:
                # Parse model statistics from line
                parts = line.split()
                if len(parts) >= 8:
                    try:
                        model_data = {
                            'Model': self._extract_model_name(line),
                            'Level': self._extract_level(line),
                            'H': self._safe_float(parts, 'H'),
                            'AIC': self._safe_float(parts, 'AIC'),
                            'BIC': self._safe_float(parts, 'BIC'),
                            'Information': self._safe_float(parts, 'Information'),
                            '%C(Data)': self._safe_float(parts, '%C'),
                            'Alpha': self._safe_float(parts, 'Alpha'),
                            'Beta': self._safe_float(parts, 'Beta')
                        }
                        data.append(model_data)
                    except:
                        continue
        
        if not data:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['Model', 'Level', 'H', 'AIC', 'BIC', 
                                        'Information', '%C(Data)', 'Alpha', 'Beta'])
        
        df = pd.DataFrame(data)
        
        # Sort by Information (descending)
        df = df.sort_values('Information', ascending=False).reset_index(drop=True)
        
        return df
    
    def _parse_fit_report(self, text: str) -> Dict:
        """Parse fit report text into dictionary"""
        stats = {}
        
        patterns = {
            'h': r'H.*?:\s*([\d.-]+)',
            'df': r'DF:\s*([\d.-]+)',
            'lr': r'LR:\s*([\d.-]+)',
            'aic': r'AIC:\s*([\d.-]+)',
            'bic': r'BIC:\s*([\d.-]+)',
            'information': r'Information:\s*([\d.-]+)',
            'pct_correct': r'%C\(Data\):\s*([\d.-]+)',
            'coverage': r'%Coverage:\s*([\d.-]+)',
            'alpha': r'Alpha:\s*([\d.-]+)',
            'beta': r'Beta:\s*([\d.-]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    stats[key] = float(match.group(1))
                except:
                    stats[key] = None
        
        return stats
    
    def _extract_model_name(self, line: str) -> str:
        """Extract model name from result line"""
        if 'IV:' in line:
            start = line.find('IV:')
            end = line.find(' ', start) if ' ' in line[start:] else len(line)
            return line[start:end].strip()
        elif 'IV ' in line:
            return 'IV'
        return ''
    
    def _extract_level(self, line: str) -> int:
        """Extract model level from model name"""
        model = self._extract_model_name(line)
        if model:
            return model.count(':')
        return 0
    
    def _safe_float(self, parts: List[str], keyword: str) -> Optional[float]:
        """Safely extract float value from parts"""
        for i, part in enumerate(parts):
            if keyword in part and i + 1 < len(parts):
                try:
                    return float(parts[i + 1])
                except:
                    pass
        return None


class Report:
    """Advanced Report formatting class"""
    
    def __init__(self, manager: pyoccam.VBMManager):
        """Initialize Report with VBMManager"""
        self.report = manager.create_report()
        self.manager = manager
        
    def add_model(self, model_name: str) -> 'Report':
        """Add a model to the report"""
        model = self.manager.get_model(model_name)
        if model:
            self.report.add_model(model)
        return self
    
    def add_models(self, model_names: List[str]) -> 'Report':
        """Add multiple models to the report"""
        for name in model_names:
            self.add_model(name)
        return self
    
    def set_columns(self, columns: List[str]) -> 'Report':
        """
        Set which columns to display
        
        Common columns:
        - Level, H, dDF, dLR, dAIC, dBIC
        - Information, %C(Data), Alpha, Beta, %cover
        """
        col_str = ','.join(columns)
        self.report.set_attributes(col_str)
        return self
    
    def sort_by(self, column: str, ascending: bool = False) -> 'Report':
        """Sort report by column"""
        direction = "ascending" if ascending else "descending"
        self.report.sort(column, direction)
        return self
    
    def set_format(self, format: str = 'text') -> 'Report':
        """
        Set output format
        
        Options:
        - 'text': Plain text (default)
        - 'tab': Tab-separated
        - 'csv': Comma-separated
        - 'html': HTML table
        """
        format_map = {
            'text': 3,  # Space-filled
            'tab': 1,   # Tab-separated
            'csv': 2,   # Comma-separated
            'html': 4   # HTML
        }
        
        if format in format_map:
            self.report.set_separator(format_map[format])
        
        return self
    
    def generate(self) -> str:
        """Generate the formatted report"""
        return self.report.generate_report()
    
    def save(self, filename: str) -> None:
        """Save report to file"""
        with open(filename, 'w') as f:
            f.write(self.generate())


# Convenience functions for quick analysis
def quick_search(data_file: str, levels: int = 5, width: int = 3) -> pd.DataFrame:
    """
    Quick search with default parameters
    
    Example:
    --------
    >>> results = quick_search("dementia05.txt")
    >>> print(results.head())
    """
    model = Model(data_file)
    return model.search(levels=levels, width=width)


def quick_fit(data_file: str, model_name: str) -> Dict:
    """
    Quick model fitting
    
    Example:
    --------
    >>> stats = quick_fit("dementia05.txt", "IV:ApZ:EdZ")
    >>> print(f"BIC: {stats['bic']:.2f}")
    """
    model = Model(data_file)
    return model.fit(model_name)


# Example usage for documentation
if __name__ == "__main__":
    print("OCCAM Python Package - Simple Interface")
    print("Version 3.4.2-multilevel")
    print("=" * 50)
    
    # Example 1: Basic usage
    print("\nExample 1: Basic Search")
    print("-" * 30)
    print("""
    # Import and create model
    from pyoccam_simple import Model
    
    # Load data
    occ = Model("dementia05.txt")
    
    # Perform search
    results = occ.search(levels=7, width=3)
    print(results.head())
    
    # Get best model
    best = occ.get_best_model('bic')
    print(f"Best model by BIC: {best}")
    
    # Fit the best model
    fit = occ.fit(best)
    print(f"BIC: {fit['bic']:.2f}")
    """)
    
    # Example 2: Algorithm comparison
    print("\nExample 2: Algorithm Comparison")
    print("-" * 30)
    print("""
    # Compare algorithms
    comparison = occ.compare_algorithms(levels=3, width=5)
    print(comparison)
    """)
    
    # Example 3: Custom reporting
    print("\nExample 3: Custom Reporting")
    print("-" * 30)
    print("""
    # Create custom report
    report = occ.create_report()
    report.add_models(['IV:Z', 'IV:ApZ', 'IV:EdZ', 'IV:ApZ:EdZ'])
    report.set_columns(['Model', 'BIC', 'AIC', '%C(Data)'])
    report.sort_by('BIC', ascending=True)
    report.set_format('csv')
    
    # Generate and save
    csv_report = report.generate()
    report.save('models.csv')
    """)
    
    print("\n" + "=" * 50)
    print("Ready for use in Jupyter notebooks!")
    print("Import with: from pyoccam_simple import Model")