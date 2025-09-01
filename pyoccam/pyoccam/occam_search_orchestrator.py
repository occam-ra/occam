"""
OCCAM Search Orchestrator
This implements the beam search algorithm that OCCAM expects Python to control.

This is the CRITICAL missing piece - Python must control the level-by-level
search, not C++. The C++ searchOneLevel() method generates children for ONE model only.
"""

import heapq
from typing import List, Optional, Tuple, Dict, Set
import pyoccam

class OccamSearchOrchestrator:
    """
    Orchestrates multi-level search using OCCAM's C++ engine.
    
    This is the CRITICAL missing piece - Python must control the level-by-level
    search, not C++.
    
    How it works:
    1. Start with initial model (usually bottom/independence)
    2. For each level:
       a. Generate children for ALL models at current level using C++ searchOneLevel()
       b. Score all children using C++ statistics computation
       c. Keep best 'width' models for next level
    3. Return all models found across all levels
    """
    
    def __init__(self, manager: 'pyoccam.VBMManager'):
        self.manager = manager
        self.all_models_generated = []
        self.best_models_by_level = {}
        self.seen_model_names = set()  # Track duplicates by name
        
    def search(self, 
               start_model: Optional['pyoccam.Model'] = None,
               levels: int = 7,
               width: int = 3,
               sort_attribute: str = "information",
               direction: str = "descending") -> List['pyoccam.Model']:
        """
        Perform beam search across multiple levels.
        
        This is what ocutils.py does in the original OCCAM:
        1. Start with initial model (usually bottom/independence)
        2. For each level:
           a. Generate children for ALL models at current level
           b. Score all children
           c. Keep best 'width' models for next level
        3. Return all models found
        
        Args:
            start_model: Starting model (if None, uses bottom reference)
            levels: Number of levels to search (default 7)
            width: Beam width - models kept per level (default 3)
            sort_attribute: Attribute to sort by (information, bic, aic, etc.)
            direction: Sort direction (descending or ascending)
            
        Returns:
            List of all models generated across all levels
        """
        
        print(f"\n🔍 Starting OCCAM search: {levels} levels, width {width}")
        print(f"   Sort by: {sort_attribute} ({direction})")
        
        # Initialize tracking
        self.all_models_generated = []
        self.best_models_by_level = {}
        self.seen_model_names = set()
        
        # Get starting model
        if start_model is None:
            start_model = self.manager.getBottomRefModel()
            if start_model is None:
                raise ValueError("Could not get starting model from manager")
        
        # Level 0: starting model
        print(f"📍 Level 0: Starting with {start_model.getPrintName()}")
        self.manager.compute_statistics_for_model(start_model)
        start_model.setLevel(0)
        
        self.all_models_generated = [start_model]
        self.best_models_by_level[0] = [start_model]
        self.seen_model_names.add(start_model.getPrintName())
        current_level_models = [start_model]
        
        # Search levels 1 through N
        for level in range(1, levels + 1):
            print(f"\n🔄 Searching level {level}...")
            print(f"   Parents: {[m.getPrintName() for m in current_level_models]}")
            
            # Generate all children for current level
            next_level_candidates = []
            total_children_generated = 0
            
            for parent_model in current_level_models:
                # CRITICAL: This is the C++ call that generates children
                print(f"   🔍 Generating children for: {parent_model.getPrintName()}")
                
                try:
                    children = self.manager.search_one_level(parent_model)
                    total_children_generated += len(children)
                    print(f"      → Generated {len(children)} children")
                    
                    for child in children:
                        # Check if we've seen this model before (by name)
                        child_name = child.getPrintName()
                        
                        if not self._is_duplicate(child_name):
                            # Compute statistics for sorting
                            self.manager.compute_statistics_for_model(child)
                            child.setLevel(level)
                            
                            # Get sort value
                            sort_value = child.getAttribute(sort_attribute)
                            
                            # Add to candidates (using heap for efficiency)
                            if direction == "descending":
                                heapq.heappush(next_level_candidates, 
                                             (-sort_value, child_name, child))
                            else:
                                heapq.heappush(next_level_candidates, 
                                             (sort_value, child_name, child))
                            
                            # Track that we've seen this model
                            self.seen_model_names.add(child_name)
                        else:
                            print(f"      ⚠️  Skipping duplicate: {child_name}")
                            
                except Exception as e:
                    print(f"      ❌ Error generating children: {e}")
                    continue
            
            print(f"   📊 Total children generated: {total_children_generated}")
            print(f"   📊 Unique candidates: {len(next_level_candidates)}")
            
            # Select best 'width' models for next level
            current_level_models = []
            selected_count = 0
            
            # Extract best models from heap
            selected_models = []
            while next_level_candidates and selected_count < width:
                sort_value, model_name, model = heapq.heappop(next_level_candidates)
                selected_models.append((sort_value, model_name, model))
                selected_count += 1
            
            # Add selected models to tracking
            for sort_value, model_name, model in selected_models:
                current_level_models.append(model)
                self.all_models_generated.append(model)
                
                # Show selection info
                actual_sort_value = -sort_value if direction == "descending" else sort_value
                print(f"   ✅ Selected: {model_name} ({sort_attribute}={actual_sort_value:.6f})")
            
            self.best_models_by_level[level] = current_level_models
            
            print(f"   📈 Level {level} complete: kept {len(current_level_models)} models")
            
            # Stop if no more models
            if not current_level_models:
                print(f"   🛑 No more models at level {level}, stopping search")
                break
        
        print(f"\n✅ Search complete! Generated {len(self.all_models_generated)} total models")
        print(f"   📊 Models by level: {[(l, len(models)) for l, models in self.best_models_by_level.items()]}")
        
        return self.all_models_generated
    
    def search_with_report(self, **kwargs) -> Tuple[List['pyoccam.Model'], str]:
        """
        Perform search and generate report in one step.
        
        Returns:
            Tuple of (models, report_text)
        """
        from occam_reports_fit import OccamReports
        
        # Extract report parameters
        search_type = kwargs.get('search_type', 'loopless-up') 
        levels = kwargs.get('levels', 7)
        width = kwargs.get('width', 3)
        
        # Perform search
        models = self.search(levels=levels, width=width, **kwargs)
        
        # Generate report
        reports = OccamReports(self.manager)
        report_text = reports.generate_search_report_text(models, search_type, levels, width)
        
        return models, report_text
    
    def _is_duplicate(self, model_name: str) -> bool:
        """Check if we've already seen this model structure."""
        return model_name in self.seen_model_names
    
    def get_models_by_level(self, level: int) -> List['pyoccam.Model']:
        """Get all models at a specific level."""
        return self.best_models_by_level.get(level, [])
    
    def get_best_model_at_level(self, level: int) -> Optional['pyoccam.Model']:
        """Get the best (first) model at a specific level."""
        models = self.get_models_by_level(level)
        return models[0] if models else None
    
    def get_all_complex_models(self, min_level: int = 3) -> List['pyoccam.Model']:
        """Get all models at or above a minimum level."""
        complex_models = []
        for model in self.all_models_generated:
            if model.getLevel() >= min_level:
                complex_models.append(model)
        return complex_models
    
    def print_search_summary(self):
        """Print a detailed summary of the search results."""
        print(f"\n📋 OCCAM Search Summary")
        print(f"=" * 50)
        print(f"Total models generated: {len(self.all_models_generated)}")
        print(f"Levels searched: {max(self.best_models_by_level.keys()) if self.best_models_by_level else 0}")
        
        for level in sorted(self.best_models_by_level.keys()):
            models = self.best_models_by_level[level]
            print(f"\nLevel {level}: {len(models)} models")
            for i, model in enumerate(models, 1):
                info_val = model.getAttribute("information")
                alpha_val = model.getAttribute("alpha")
                print(f"  {i}. {model.getPrintName()}")
                print(f"     Info: {info_val:.6f}, Alpha: {alpha_val:.6f}")
    
    def get_search_report_dataframe(self, search_type: str = "loopless-up") -> 'pd.DataFrame':
        """
        Get search results as a pandas DataFrame.
        
        Returns:
            DataFrame with search results and statistics
        """
        try:
            from occam_reports_fit import OccamReports
            reports = OccamReports(self.manager)
            return reports.create_search_report(self.all_models_generated, search_type)
        except ImportError:
            print("⚠️  pandas not available, cannot create DataFrame")
            return None
    
    def validate_expected_models(self, expected_patterns: List[str]) -> Dict[str, List[str]]:
        """
        Validate that expected model patterns appear in results.
        
        Args:
            expected_patterns: List of model name patterns to look for
            
        Returns:
            Dictionary mapping patterns to found model names
        """
        results = {}
        all_model_names = [m.getPrintName() for m in self.all_models_generated]
        
        for pattern in expected_patterns:
            matching = [name for name in all_model_names if pattern in name]
            results[pattern] = matching
            
            if matching:
                print(f"✅ Found {len(matching)} models matching '{pattern}': {matching[:3]}...")
            else:
                print(f"❌ No models found matching '{pattern}'")
        
        return results


def test_search_orchestrator():
    """
    Test function to verify the orchestrator works correctly.
    """
    print("🧪 Testing OCCAM Search Orchestrator")
    print("=" * 50)
    
    try:
        # Initialize manager
        manager = pyoccam.VBMManager()
        success = manager.init_from_command_line(['occam', 'dementia05.txt'])
        
        if not success:
            print("❌ Failed to initialize manager with data file")
            return False
        
        manager.setSearch("loopless-up")
        manager.setRefModel("bottom")
        
        # Create orchestrator
        orchestrator = OccamSearchOrchestrator(manager)
        
        # Run search
        models = orchestrator.search(levels=5, width=3, sort_attribute="information")
        
        # Validate results
        if len(models) < 5:
            print(f"❌ Only generated {len(models)} models (expected at least 5)")
            return False
        
        # Check we have multiple levels
        levels = set(m.getLevel() for m in models)
        if len(levels) < 3:
            print(f"❌ Only reached {len(levels)} levels (expected at least 3)")
            return False
        
        # Check for complex models
        complex_models = orchestrator.get_all_complex_models(min_level=3)
        if len(complex_models) == 0:
            print("❌ No complex models (level 3+) generated")
            return False
        
        # Print summary
        orchestrator.print_search_summary()
        
        # Test expected patterns (from handoff document)
        expected_patterns = ["ApZ", "EdZ", "ApSxZ"]
        found_patterns = orchestrator.validate_expected_models(expected_patterns)
        
        print(f"\n✅ Test passed!")
        print(f"   Generated {len(models)} models across {len(levels)} levels")
        print(f"   Found {len(complex_models)} complex models")
        
        # Test report generation
        try:
            from occam_reports_fit import OccamReports
            reports = OccamReports(manager)
            report_text = reports.generate_search_report_text(models, "loopless-up", 5, 3)
            print(f"\n📊 Generated {len(report_text)} character report")
        except ImportError:
            print("⚠️  Report functionality not tested (occam_reports_fit not available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the test if script is executed directly
    test_search_orchestrator()
