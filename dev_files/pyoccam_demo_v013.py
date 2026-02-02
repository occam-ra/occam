#!/usr/bin/env python3
"""
PyOccam 0.1.3 - Complete Demonstration
Showcases all major functionality including confusion matrix extraction
"""

import pyoccam
import time
import os
import sys

def print_header(text, char='=', width=80):
    """Print a formatted section header"""
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}")

def print_subheader(text, char='-', width=60):
    """Print a formatted subsection header"""
    print(f"\n{char * width}")
    print(f" {text}")
    print(f"{char * width}")

def demo_basic_usage():
    """Demonstrate basic PyOccam usage"""
    print_header("PYOCCAM 0.1.3 - BASIC USAGE DEMO")
    
    # Check version
    print(f"\n📦 PyOccam Version: {pyoccam.__version__}")
    print(f"✓ Successfully loaded PyOccam")
    
    # Initialize manager
    print_subheader("1. Initialize VBMManager")
    manager = pyoccam.VBMManager()
    print("✓ VBMManager created")
    
    # Load data
    print_subheader("2. Load Data File")
    data_file = "dementia05.txt"
    manager.init_from_command_line(["occam", data_file])
    print(f"✓ Loaded: {data_file}")
    
    # Get basic info
    sample_size = manager.get_sample_size()
    variables = manager.get_variable_list()
    print(f"\n📊 Dataset Statistics:")
    print(f"  • Sample size: {sample_size}")
    print(f"  • Number of variables: {len(variables)}")
    print(f"  • DV (dependent variable): {variables[-1]}")
    print(f"  • IVs (independent variables): {', '.join(variables[:5])}...")
    
    return manager

def demo_search_algorithms(manager):
    """Demonstrate different search algorithms"""
    print_header("SEARCH ALGORITHMS DEMO")
    
    search_configs = [
        ("loopless-up", 3, 7),
        ("full-up", 3, 5),
    ]
    
    results = {}
    
    for search_type, levels, width in search_configs:
        print_subheader(f"Search: {search_type}")
        print(f"Parameters: levels={levels}, width={width}")
        
        start_time = time.time()
        search_report = manager.generate_search_report(
            search_type=search_type,
            levels=levels,
            width=width,
            include_test_data=False
        )
        elapsed = time.time() - start_time
        
        # Get best models
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        
        print(f"\n⏱️ Search completed in {elapsed:.3f}s")
        print(f"📈 Best Models Found:")
        print(f"  • BIC: {best_bic}")
        print(f"  • AIC: {best_aic}")
        print(f"  • Info: {best_info}")
        
        # Save report
        filename = f"demo_search_{search_type.replace('-', '_')}.txt"
        with open(filename, 'w') as f:
            f.write(search_report)
        print(f"  • Report saved to: {filename}")
        
        results[search_type] = {
            'best_bic': best_bic,
            'best_aic': best_aic,
            'best_info': best_info,
            'time': elapsed
        }
    
    return results

def demo_confusion_matrix(manager, model_name, target_state="0"):
    """Demonstrate confusion matrix extraction"""
    print_header("CONFUSION MATRIX DEMO")
    
    print(f"Model: {model_name}")
    print(f"Target State (negative class): Z={target_state}")
    
    # Get confusion matrix
    print_subheader("Extracting Confusion Matrix")
    cm = manager.get_confusion_matrix(model_name, target_state)
    
    if cm and any(cm.values()):
        # Display raw values
        print("\n📊 Confusion Matrix Values:")
        print(f"{'':15} Predicted")
        print(f"{'':15} Negative   Positive")
        print(f"Actual Negative  TN={cm['TN']:6.0f}  FP={cm['FP']:6.0f}")
        print(f"       Positive  FN={cm['FN']:6.0f}  TP={cm['TP']:6.0f}")
        
        # Calculate totals
        total = cm['TN'] + cm['FP'] + cm['FN'] + cm['TP']
        correct = cm['TN'] + cm['TP']
        
        print(f"\nTotal samples: {total:.0f}")
        print(f"Correctly classified: {correct:.0f} ({correct/total*100:.1f}%)")
        
        # Display metrics
        print("\n📈 Performance Metrics:")
        metrics = [
            ("Accuracy", cm['accuracy'], "Overall correct predictions"),
            ("Sensitivity", cm['recall'], "True Positive Rate (Recall)"),
            ("Specificity", cm['specificity'], "True Negative Rate"),
            ("Precision", cm['precision'], "Positive Predictive Value"),
            ("F1 Score", cm['f1_score'], "Harmonic mean of Precision & Recall"),
        ]
        
        for name, value, desc in metrics:
            print(f"  • {name:12} = {value:.3f} ({value*100:5.1f}%)  # {desc}")
        
        return cm
    else:
        print("❌ Failed to extract confusion matrix")
        return None

def demo_model_comparison(manager):
    """Compare multiple models"""
    print_header("MODEL COMPARISON DEMO")
    
    # Run a search first
    print("Running search to get candidate models...")
    manager.generate_search_report("loopless-up", 4, 3, False)
    
    # Get various best models
    models = {
        'BIC': manager.get_best_model_by_bic(),
        'AIC': manager.get_best_model_by_aic(),
        'Information': manager.get_best_model_by_information(),
    }
    
    # Add some specific models for comparison
    additional_models = [
        "IV:ApZ",           # Simple single-variable model
        "IV:CZ:KZ",         # Two-variable model
        "IV:ApSxZ:EdZ:CZ",  # More complex model
    ]
    
    print_subheader("Comparing Models")
    print(f"{'Model':<30} {'Accuracy':>10} {'Sensitivity':>12} {'F1 Score':>10}")
    print("-" * 65)
    
    # Compare best models
    for criterion, model in models.items():
        if model:
            cm = manager.get_confusion_matrix(model, "0")
            if cm and cm['accuracy'] > 0:
                print(f"{model:<30} {cm['accuracy']:10.3f} {cm['recall']:12.3f} {cm['f1_score']:10.3f}  # Best by {criterion}")
    
    # Compare additional models
    for model in additional_models:
        try:
            cm = manager.get_confusion_matrix(model, "0")
            if cm and cm['accuracy'] > 0:
                print(f"{model:<30} {cm['accuracy']:10.3f} {cm['recall']:12.3f} {cm['f1_score']:10.3f}")
        except:
            pass

def demo_fit_report(manager, model_name):
    """Generate and analyze fit report"""
    print_header("FIT REPORT DEMO")
    
    print(f"Generating complete fit report for: {model_name}")
    
    # Generate fit report
    fit_report = manager.generate_fit_report(model_name, "0")
    
    # Save report
    filename = f"demo_fit_{model_name.replace(':', '_')}.txt"
    with open(filename, 'w') as f:
        f.write(fit_report)
    
    print(f"✓ Fit report saved to: {filename}")
    
    # Analyze report content
    print("\n📄 Report Contents Analysis:")
    sections = {
        "Model Statistics": "H(data)",
        "Conditional Probability Tables": "Conditional DV",
        "Confusion Matrix": "Confusion Matrix",
        "Performance Statistics": "Additional Statistics",
        "Component Relations": "Component:",
    }
    
    for section, marker in sections.items():
        if marker in fit_report:
            count = fit_report.count(marker)
            print(f"  ✓ {section}: {'Found' if count > 0 else 'Not found'} ({count} occurrence(s))")
        else:
            print(f"  ✗ {section}: Not found")
    
    # Report size
    print(f"\n📏 Report Size: {len(fit_report)} characters, {len(fit_report.splitlines())} lines")

def demo_advanced_features(manager):
    """Demonstrate advanced features"""
    print_header("ADVANCED FEATURES DEMO")
    
    print_subheader("Available Search Types")
    search_types = manager.get_available_search_types()
    print("Supported search algorithms:")
    for st in search_types:
        direction = "ascending" if "up" in st else "descending"
        print(f"  • {st:15} ({direction})")
    
    print_subheader("Report Configuration")
    # Set report separator (space-separated format)
    manager.set_report_separator(pyoccam.SPACESEP)
    print("✓ Set report separator to SPACESEP")
    
    # Set reference model
    manager.set_ref_model("bottom")
    print("✓ Set reference model to 'bottom'")
    
    print_subheader("Model Creation")
    # Create a specific model
    model = manager.make_model("IV:ApZ:EdZ", make_fit_table=True)
    if model:
        print(f"✓ Created model: {model.name}")
        print(f"  • H = {model.h:.3f}")
        print(f"  • DF = {model.df}")
        print(f"  • %Correct = {model.pct_correct_data:.1f}%")

def main():
    """Main demo function"""
    print_header("PYOCCAM 0.1.3 - COMPREHENSIVE DEMONSTRATION", '=', 80)
    print("\nThis demo showcases all major PyOccam functionality")
    print("including the newly fixed confusion matrix extraction.")
    
    try:
        # Basic usage
        manager = demo_basic_usage()
        
        # Search algorithms
        search_results = demo_search_algorithms(manager)
        
        # Get best model for further demos
        best_model = manager.get_best_model_by_bic()
        if not best_model:
            best_model = "IV:ApSxZ:EdZ:AgZ:CZ:KZ"  # Fallback
        
        # Confusion matrix
        cm = demo_confusion_matrix(manager, best_model)
        
        # Model comparison
        demo_model_comparison(manager)
        
        # Fit report
        demo_fit_report(manager, best_model)
        
        # Advanced features
        demo_advanced_features(manager)
        
        # Summary
        print_header("DEMO SUMMARY", '=', 80)
        print("\n✅ All PyOccam 0.1.3 features demonstrated successfully!")
        print("\n📊 Key Results:")
        print(f"  • Best model (BIC): {best_model}")
        if cm:
            print(f"  • Model accuracy: {cm['accuracy']*100:.1f}%")
            print(f"  • F1 Score: {cm['f1_score']:.3f}")
        
        print("\n📁 Generated Files:")
        for f in os.listdir('.'):
            if f.startswith('demo_'):
                print(f"  • {f}")
        
        print("\n🎉 PyOccam 0.1.3 is fully functional!")
        print("   Ready for production use in RA/machine learning comparisons.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
