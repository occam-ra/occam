# PyOccam Demo Quick Reference Card

## 📁 Files

```
basic_analysis.py         - Simple Python script
basic_analysis.ipynb      - Simple Jupyter notebook
advanced_analysis.py      - Comprehensive Python script  
advanced_analysis.ipynb   - Comprehensive Jupyter notebook
DEMOS_README.md           - Complete documentation
```

## 🎯 Which Demo Should I Use?

| Use This | If You Want |
|----------|-------------|
| **basic_analysis** | Quick single-model analysis |
| **advanced_analysis** | Compare algorithms & multiple models |

## ⚙️ Configuration (At Top of Each File)

```python
# DATA
DATASET = "dementia"              # "dementia", "landslides", or file path

# SEARCH
SEARCH_TYPE = "loopless-up"       # Algorithm to use
SEARCH_LEVELS = 7                 # How deep (1-10)
SEARCH_WIDTH = 3                  # Models per level (1-10)

# MODEL SELECTION - CHOOSE ONE:
MODEL_SELECTION = "BIC"           # "BIC", "AIC", or "INFO"

# OUTPUT
OUTPUT_FORMAT = "space"           # "space", "tab", or "comma"
SHOW_CONFUSION_MATRIX = True      # True or False
```

## 🔍 Search Algorithms

| Algorithm | Speed | Use When |
|-----------|-------|----------|
| **loopless-up** | ⚡ Fast | Most cases (default) |
| **full-up** | 🐌 Slow | Comprehensive search |
| **disjoint-up** | ⚡ Fast | Disjoint components |
| **chain-up** | ⚡ Fast | Chain decompositions |

## 📊 Model Selection Criteria

| Criterion | Best For | Penalty for Complexity |
|-----------|----------|------------------------|
| **BIC** | Prediction | 🔴 Strong |
| **AIC** | Explanation | 🟡 Moderate |
| **INFO** | Theory | 🟢 None |

**Just change `MODEL_SELECTION = "BIC"` to "AIC" or "INFO"**

## 🚀 Quick Start

### Python Script
```bash
python basic_analysis.py
```

### Jupyter Notebook
```bash
jupyter notebook basic_analysis.ipynb
```

## 📈 Typical Settings

### Beginner / Quick
```python
SEARCH_TYPE = "loopless-up"
SEARCH_LEVELS = 3
SEARCH_WIDTH = 3
MODEL_SELECTION = "BIC"
```

### Standard Analysis
```python
SEARCH_TYPE = "loopless-up"
SEARCH_LEVELS = 7
SEARCH_WIDTH = 3
MODEL_SELECTION = "BIC"
```

### Research / Publication
```python
SEARCH_TYPES = ["loopless-up", "full-up"]  # advanced only
SEARCH_LEVELS = 7
SEARCH_WIDTH = 5
MODEL_SELECTION = "BIC"
ANALYZE_TOP_N = 3                          # advanced only
```

## 📤 Output Files

All files are timestamped automatically:
- `search_{algorithm}_{timestamp}.txt`
- `fit_{model}_{timestamp}.txt`
- `analysis_summary_{timestamp}.txt` (advanced only)

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| No models found | Add "-up" to SEARCH_TYPE |
| Too slow | Reduce SEARCH_LEVELS or use "loopless-up" |
| Empty best_model | Check search completed successfully |
| CM error | Verify TARGET_STATE matches your data |

## 💡 Tips

1. **Start simple** - Use basic_analysis first
2. **Use loopless-up** - Fastest algorithm for initial exploration  
3. **Try all criteria** - Set COMPARE_ALL_CRITERIA = True (advanced)
4. **Save reports** - Set SAVE_REPORTS = True
5. **Check accuracy** - Set SHOW_CONFUSION_MATRIX = True

## 📚 Help

```python
import pyoccam
pyoccam.help()           # Show usage guide
pyoccam.load_dementia()  # Load example dataset
```

## 🔗 More Info

See **DEMOS_README.md** for complete documentation including:
- Detailed configuration options
- Example workflows
- Search algorithm descriptions
- Model selection formulas
- Troubleshooting guide
- Example configurations

---

**Keep this card handy for quick reference!**
