"""
OCCAM Report Generation and Fit Analysis
High-level Python interface for generating reports and fitting models.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
import pyoccam
from datetime import datetime
import os

class OccamReports:
    """
    High-level interface for OCCAM report generation and fit analysis.
    
    Example usage:
        reports = OccamReports(manager)
        
        # Generate search report
        search_df = reports.create_search_report(models)
        
        # Fit analysis
        fit_stats = reports.fit_model("IV:ApZ:EdZ")
        fit_report = reports.generate_fit_report("IV:ApZ:EdZ")
    """
    
    def __init__(self, manager: 'pyoccam.VBMManager'):
        self.manager = manager
        
    def create_search_report(self, models: List['pyoccam.Model'], 
                           search_type: str = "loopless-up",
                           levels: int = 7, width: int = 3) -> pd.DataFrame:
        """
        Create a comprehensive search report as a DataFrame.
        
        Args:
            models: List of models from search results
            search_type: Search algorithm used
            levels: Search levels
            width: Search width
            
        Returns:
            DataFrame with complete search results
        """
        
        print(f"📊 Generating search report for {len(models)} models...")
        
        # Convert models to structured data
        data = []
        level_best_info = {}  # Track best information score per level
        
        # First pass: find best information score per level
        for model in models:
            level = int(model.getAttribute("level"))
            info = model.getAttribute("information")
            if level not in level_best_info or info > level_best_info[level]:
                level_best_info[level] = info
        
        # Second pass: create data with "best" marking
        for i, model in enumerate(models, 1):
            level = int(model.getAttribute("level"))
            info = model.getAttribute("information")
            is_best = (info == level_best_info[level])
            
            # Get all statistics safely
            try:
                data.append({
                    'id': i,
                    'model': model.getPrintName(),
                    'level': level,
                    'H': model.getAttribute('h'),
                    'dDF': int(model.getAttribute('df')),
                    'dLR': model.getAttribute('lr'),
                    'alpha': model.getAttribute('alpha'),
                    'information': info,
                    '%dH(DV)': model.getAttribute('pct_dh'),
                    'AIC': model.getAttribute('aic'),
                    'BIC': model.getAttribute('bic'),
                    'inc_alpha': model.getAttribute('inc_alpha'),
                    '%C(Data)': model.getAttribute('pct_correct_data'),
                    '%cover': model.getAttribute('pct_cover'),
                    'best': '*' if is_best else ''
                })
            except Exception as e:
                print(f"⚠️  Warning: Error getting statistics for model {i}: {e}")
                # Add minimal data
                data.append({
                    'id': i,
                    'model': model.getPrintName(),
                    'level': level,
                    'information': info,
                    'best': '*' if is_best else ''
                })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add metadata as attributes
        df.attrs = {
            'search_type': search_type,
            'levels': levels,
            'width': width,
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_models': len(models)
        }
        
        print(f"✅ Search report generated with {len(df)} models")
        return df
    
    def generate_search_report_text(self, models: List['pyoccam.Model'],
                                  search_type: str = "loopless-up",
                                  levels: int = 7, width: int = 3) -> str:
        """
        Generate a text-formatted search report (OCCAM server style).
        
        Returns:
            Formatted text report string
        """
        
        try:
            # Use the C++ method for consistent formatting
            report_text = self.manager.generate_search_report(models, search_type, levels, width)
            return report_text
        except Exception as e:
            print(f"⚠️  Error generating C++ report, falling back to Python: {e}")
            
            # Fallback to Python formatting
            df = self.create_search_report(models, search_type, levels, width)
            
            # Format as text
            report = []
            report.append("OCCAM Search Report")
            report.append(f"Search: {search_type}, Levels: {levels}, Width: {width}")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            report.append(df.to_string(index=False))
            
            return "\n".join(report)
    
    def fit_model(self, model_spec: str) -> Dict:
        """
        Fit a specific model and return comprehensive statistics.
        
        Args:
            model_spec: Model specification string (e.g., "IV:ApZ:EdZ")
            
        Returns:
            Dictionary with fit statistics
        """
        
        print(f"🔧 Fitting model: {model_spec}")
        
        try:
            # Use C++ fit method
            model = self.manager.fit_model(model_spec)
            
            if not model:
                raise ValueError(f"Could not fit model: {model_spec}")
            
            # Extract comprehensive statistics
            stats = {
                'model': model.getPrintName(),
                'specification': model_spec,
                'level': self._count_model_level(model_spec),
                'degrees_freedom': model.getAttribute('df'),
                'likelihood_ratio': model.getAttribute('lr'),
                'alpha': model.getAttribute('alpha'),
                'information': model.getAttribute('information'),
                'aic': model.getAttribute('aic'),
                'bic': model.getAttribute('bic'),
                'h_model': model.getAttribute('h'),
                'percent_dh': model.getAttribute('pct_dh'),
                'relation_count': model.getRelationCount()
            }
            
            # Add directed system statistics if applicable
            if self.manager.getVariableList()->isDirected():
                stats.update({
                    'percent_correct_data': model.getAttribute('pct_correct_data'),
                    'percent_correct_test': model.getAttribute('pct_correct_test'),
                    'incremental_alpha': model.getAttribute('inc_alpha'),
                    'percent_cover': model.getAttribute('pct_cover')
                })
            
            print(f"✅ Model fitted successfully: {stats['information']:.6f} information")
            return stats
            
        except Exception as e:
            print(f"❌ Error fitting model {model_spec}: {e}")
            raise
    
    def generate_fit_report(self, model_spec: str) -> str:
        """
        Generate a detailed fit report for a specific model.
        
        Args:
            model_spec: Model specification string
            
        Returns:
            Formatted fit report string
        """
        
        print(f"📋 Generating fit report for: {model_spec}")
        
        try:
            # First fit the model to ensure it's properly computed
            model = self.manager.fit_model(model_spec)
            if not model:
                return f"Error: Could not fit model {model_spec}"
            
            # Generate comprehensive fit report
            report_text = self.manager.generate_fit_report(model)
            
            print(f"✅ Fit report generated for {model_spec}")
            return report_text
            
        except Exception as e:
            error_msg = f"Error generating fit report for {model_spec}: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def save_search_report(self, models: List['pyoccam.Model'], filename: str,
                          search_type: str = "loopless-up", levels: int = 7, width: int = 3,
                          format: str = 'both') -> Dict[str, str]:
        """
        Save search report to file(s).
        
        Args:
            models: Search results
            filename: Base filename (without extension)
            search_type, levels, width: Search parameters
            format: 'csv', 'txt', or 'both'
            
        Returns:
            Dictionary with saved filenames
        """
        
        saved_files = {}
        
        try:
            if format in ['csv', 'both']:
                # Save as CSV
                df = self.create_search_report(models, search_type, levels, width)
                csv_file = f"{filename}.csv"
                df.to_csv(csv_file, index=False)
                saved_files['csv'] = csv_file
                print(f"📁 CSV report saved: {csv_file}")
            
            if format in ['txt', 'both']:
                # Save as text report
                text_report = self.generate_search_report_text(models, search_type, levels, width)
                txt_file = f"{filename}.txt"
                with open(txt_file, 'w') as f:
                    f.write(text_report)
                saved_files['txt'] = txt_file
                print(f"📁 Text report saved: {txt_file}")
                
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            
        return saved_files
    
    def save_fit_report(self, model_spec: str, filename: str) -> str:
        """
        Save fit report to file.
        
        Args:
            model_spec: Model specification
            filename: Output filename
            
        Returns:
            Saved filename
        """
        
        try:
            fit_report = self.generate_fit_report(model_spec)
            
            with open(filename, 'w') as f:
                f.write(f"OCCAM Model Fit Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(fit_report)
            
            print(f"📁 Fit report saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving fit report: {e}")
            raise
    
    def compare_models(self, model_specs: List[str]) -> pd.DataFrame:
        """
        Compare multiple models side by side.
        
        Args:
            model_specs: List of model specification strings
            
        Returns:
            DataFrame with model comparison
        """
        
        print(f"🔍 Comparing {len(model_specs)} models...")
        
        comparison_data = []
        
        for spec in model_specs:
            try:
                stats = self.fit_model(spec)
                comparison_data.append(stats)
            except Exception as e:
                print(f"⚠️  Warning: Could not fit {spec}: {e}")
        
        if not comparison_data:
            raise ValueError("No models could be fitted for comparison")
        
        df = pd.DataFrame(comparison_data)
        
        # Sort by information content (descending)
        df = df.sort_values('information', ascending=False).reset_index(drop=True)
        
        print(f"✅ Model comparison completed")
        return df
    
    def get_best_models(self, models: List['pyoccam.Model'], 
                       criteria: str = 'information', n: int = 5) -> List[Dict]:
        """
        Get the best models according to specified criteria.
        
        Args:
            models: List of models to evaluate
            criteria: 'information', 'aic', 'bic', 'alpha'
            n: Number of best models to return
            
        Returns:
            List of dictionaries with best model information
        """
        
        print(f"🏆 Finding top {n} models by {criteria}...")
        
        model_stats = []
        
        for model in models:
            try:
                stats = {
                    'model': model.getPrintName(),
                    'level': int(model.getAttribute('level')),
                    'information': model.getAttribute('information'),
                    'aic': model.getAttribute('aic'),
                    'bic': model.getAttribute('bic'),
                    'alpha': model.getAttribute('alpha'),
                    'df': model.getAttribute('df'),
                    'lr': model.getAttribute('lr')
                }
                model_stats.append(stats)
            except Exception as e:
                print(f"⚠️  Warning: Could not get stats for model: {e}")
        
        # Sort based on criteria
        if criteria == 'information':
            model_stats.sort(key=lambda x: x['information'], reverse=True)
        elif criteria in ['aic', 'bic']:
            model_stats.sort(key=lambda x: x[criteria], reverse=False)  # Lower is better
        elif criteria == 'alpha':
            model_stats.sort(key=lambda x: x['alpha'], reverse=False)  # Lower is better
        else:
            raise ValueError(f"Unknown criteria: {criteria}")
        
        best_models = model_stats[:n]
        
        print(f"✅ Found top {len(best_models)} models by {criteria}")
        return best_models
    
    def _count_model_level(self, model_spec: str) -> int:
        """Count the complexity level of a model from its specification."""
        if model_spec.startswith("IV:"):
            components = model_spec[3:].split(":")
            return len(components) - 1  # Subtract DV
        return 0


def test_reports_and_fit():
    """
    Test function for report generation and fit analysis.
    """
    print("🧪 Testing OCCAM Reports and Fit Analysis")
    print("=" * 50)
    
    try:
        # Initialize manager
        import pyoccam
        from occam_search import OccamSearchOrchestrator
        
        manager = pyoccam.VBMManager()
        success = manager.init_from_command_line(['occam', 'dementia05.txt'])
        
        if not success:
            print("❌ Failed to initialize manager")
            return False
        
        manager.setSearch("loopless-up")
        
        # Run a small search
        orchestrator = OccamSearchOrchestrator(manager)
        models = orchestrator.search(levels=3, width=3)
        
        # Test report generation
        reports = OccamReports(manager)
        
        print("\n📊 Testing Search Report Generation...")
        search_df = reports.create_search_report(models, "loopless-up", 3, 3)
        print(f"Search report DataFrame shape: {search_df.shape}")
        print(search_df.head())
        
        print("\n📋 Testing Text Report Generation...")
        text_report = reports.generate_search_report_text(models, "loopless-up", 3, 3)
        print("Text report preview:")
        print(text_report[:500] + "..." if len(text_report) > 500 else text_report)
        
        # Test fit analysis
        if len(models) > 0:
            best_model = models[-1]  # Take a complex model
            model_spec = best_model.getPrintName()
            
            print(f"\n🔧 Testing Fit Analysis for: {model_spec}")
            fit_stats = reports.fit_model(model_spec)
            print(f"Fit statistics: {fit_stats}")
            
            print(f"\n📋 Testing Fit Report for: {model_spec}")
            fit_report = reports.generate_fit_report(model_spec)
            print("Fit report preview:")
            print(fit_report[:300] + "..." if len(fit_report) > 300 else fit_report)
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_reports_and_fit()
