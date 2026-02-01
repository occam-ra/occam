# PyOccam Demo Scripts and Notebooks

This directory contains demonstration scripts and notebooks for PyOccam analysis.

## Files Overview

### Basic Analysis
- **`basic_analysis.py`** - Python script for simple workflow
- **`basic_analysis.ipynb`** - Jupyter notebook for simple workflow

**Use basic analysis when:**
- You're new to OCCAM or PyOccam
- You want a straightforward single-model analysis
- You need quick results with minimal configuration
- You're doing exploratory analysis

**Features:**
- Single search algorithm
- Automatic best model selection (BIC, AIC, or Information)
- Confusion matrix extraction
- Clean, easy-to-understand output
- ~150 lines of code

### Advanced Analysis
- **`advanced_analysis.py`** - Python script for comprehensive workflow
- **`advanced_analysis.ipynb`** - Jupyter notebook for comprehensive workflow

**Use advanced analysis when:**
- You need to compare multiple search algorithms
- You want to analyze multiple top models
- You're doing research or publication-quality analysis
- You need detailed model comparison tables

**Features:**
- Multiple search algorithm comparison
- Top N model fitting and comparison
- Comprehensive confusion matrix analysis
- Model comparison tables with performance metrics
- Detailed statistical output
- ~300 lines of code

## Quick Start

### Option 1: Python Scripts

**Basic Analysis:**
```bash
# Edit configuration at the top of the file
python basic_analysis.py
```

**Advanced Analysis:**
```bash
# Edit configuration at the top of the file
python advanced_analysis.py
```

### Option 2: Jupyter Notebooks

**Basic Analysis:**
```bash
jupyter notebook basic_analysis.ipynb
```

**Advanced Analysis:**
```bash
jupyter notebook advanced_analysis.ipynb
```

## Configuration

All scripts and notebooks have a **CONFIGURATION** section at the top where you can modify:

### Data Selection
```python
DATASET = "dementia"  # Options: "dementia", "landslides", or path to your file
```

### Search Settings
```python
SEARCH_TYPE = "loopless-up"  # or "full-up", "disjoint-up", "chain-up"
SEARCH_LEVELS = 7            # Depth to search (1-10)
SEARCH_WIDTH = 3             # Models to keep per level (1-10)
```

### Model Selection
```python
MODEL_SELECTION = "BIC"  # Options: "BIC", "AIC", "INFO"
```

Choose which criterion to use for selecting the best model:
- **BIC** - Bayesian Information Criterion (penalizes complexity more)
- **AIC** - Akaike Information Criterion (less penalty for complexity)
- **INFO** - Pure information-theoretic approach

### Output Options
```python
OUTPUT_FORMAT = "space"           # "space", "tab", or "comma"
SHOW_CONFUSION_MATRIX = True      # Display confusion matrix?
SAVE_REPORTS = True               # Save reports to files?
```

## Typical Workflow

1. **Edit configuration** at the top of the script/notebook
2. **Run the analysis**
   - Scripts: `python basic_analysis.py` or `python advanced_analysis.py`
   - Notebooks: Run cells in order
3. **Review output** printed to console/displayed in notebook
4. **Examine saved reports** in generated `.txt` files

## Output Files

Both scripts/notebooks generate timestamped output files:

- `search_{algorithm}_{timestamp}.txt` - Search results
- `fit_{model}_{timestamp}.txt` - Fit results for each model
- `analysis_summary_{timestamp}.txt` - Overall summary (advanced only)

## Example Configurations

### Quick Exploratory Analysis
```python
DATASET = "dementia"
SEARCH_TYPE = "loopless-up"
SEARCH_LEVELS = 3
SEARCH_WIDTH = 3
MODEL_SELECTION = "BIC"
```

### Comprehensive Research Analysis
```python
DATASET = "your_data.txt"
SEARCH_TYPES = ["loopless-up", "full-up", "disjoint-up"]
SEARCH_LEVELS = 7
SEARCH_WIDTH = 5
MODEL_SELECTION = "BIC"
ANALYZE_TOP_N = 5
COMPARE_ALL_CRITERIA = True
```

### Publication-Quality Analysis
```python
DATASET = "your_data.txt"
SEARCH_TYPES = ["loopless-up", "full-up"]
SEARCH_LEVELS = 7
SEARCH_WIDTH = 7
MODEL_SELECTION = "BIC"
ANALYZE_TOP_N = 3
EXTRACT_CONFUSION_MATRICES = True
DETAILED_OUTPUT = True
```

## Search Algorithm Descriptions

- **loopless-up** - Bottom-up without loops (fast, good for most cases)
- **full-up** - Full bottom-up search (comprehensive, slower)
- **disjoint-up** - Disjoint component search
- **chain-up** - Chain decomposition search

## Model Selection Criteria

### BIC (Bayesian Information Criterion)
- Penalizes model complexity more strongly
- Preferred for prediction
- Formula: BIC = -2*log(L) + k*log(n)

### AIC (Akaike Information Criterion)  
- Less penalty for complexity than BIC
- Preferred for explanation
- Formula: AIC = -2*log(L) + 2*k

### INFO (Information-theoretic)
- Pure information approach
- Uses transmission information (H)
- No explicit complexity penalty

## Tips

1. **Start with basic_analysis** to understand the workflow
2. **Use loopless-up** for initial exploration (fastest)
3. **Increase SEARCH_LEVELS** for more thorough search (up to 7-10)
4. **Compare search algorithms** using advanced_analysis
5. **Check confusion matrices** to evaluate predictive performance
6. **Save your reports** for documentation and reproducibility

## Troubleshooting

**Problem:** No models found  
**Solution:** Check that SEARCH_TYPE includes "-up" suffix (e.g., "loopless-up" not "loopless")

**Problem:** Search takes too long  
**Solution:** Reduce SEARCH_LEVELS or SEARCH_WIDTH, or use "loopless-up"

**Problem:** Best model is empty string  
**Solution:** Verify search completed successfully and generated models

**Problem:** Confusion matrix shows error  
**Solution:** Check that TARGET_STATE matches a valid DV state in your data

## Resources

- PyOccam documentation: Type `pyoccam.help()` in Python
- OCCAM manual: See included PDF documentation
- Example datasets: Use `pyoccam.load_dementia()` or `pyoccam.load_landslides()`

## Getting Help

```python
import pyoccam
pyoccam.help()  # Display usage guide
```

For more examples and detailed API documentation, see the project repository.
