# Pyoccam Examples

Welcome to the pyoccam examples! This folder contains demo scripts and Jupyter notebooks to help you get started with Reconstructability Analysis using pyoccam.

## 📁 What's Included

### Python Scripts
- **basic_analysis.py** - Basic workflow: Load data → Search → Fit
- **advanced_analysis.py** - Advanced: Extract confusion matrix and calculate metrics

### Jupyter Notebooks
- **basic_analysis.ipynb** - Interactive introduction to pyoccam
- **advanced_analysis.ipynb** - Deep dive into advanced features

## 🚀 Quick Start

### Option 1: Copy Examples to Your Project
```python
import pyoccam
pyoccam.copy_examples()
```

This creates a `pyoccam_examples/` folder in your current directory with all files.

### Option 2: Run From Installed Location
```python
from pyoccam.examples import basic_analysis
basic_analysis.main()
```

### Option 3: Use Command Line
```bash
pyoccam-examples --copy    # Copy to current directory
pyoccam-examples --list    # List all examples
pyoccam-examples --path    # Show installation path
```

## 📝 Using the Scripts

1. **Copy a script to your project folder**
2. **Put your data file in the same folder**
3. **Edit ONE line in the script:**
   ```python
   DATA_FILE = "your_data.txt"  # ← Change this!
   ```
4. **Run it:**
   ```bash
   python basic_analysis.py
   ```

## 📓 Using the Jupyter Notebooks

1. **Copy notebooks to your project:**
   ```python
   import pyoccam
   pyoccam.copy_examples()
   ```

2. **Start Jupyter:**
   ```bash
   cd pyoccam_examples
   jupyter notebook
   ```

3. **Open and run:**
   - Start with `basic_analysis.ipynb`
   - Try `advanced_analysis.ipynb` for more features

## 📊 Sample Data

Pyoccam includes two sample datasets you can use immediately:

```python
import pyoccam

# Dementia dataset (Alzheimer's Disease)
data = pyoccam.load_dementia()

# Landslides dataset (Geological hazards)
data = pyoccam.load_landslides()

# Your own data
data = pyoccam.load_data("your_file.txt")
```

## 📖 Learn More

- **Documentation:** https://github.com/occam-ra/occam
- **Issues/Questions:** https://github.com/occam-ra/occam/issues
- **Original Occam:** http://dmm.sysc.pdx.edu

## 🎯 What's Next?

Coming soon: **CSV to Occam Header** converter script!

This will let you convert your CSV files to Occam format automatically:
```bash
pyoccam-convert mydata.csv --output mydata.txt
```

Stay tuned! 🚀

---

*Pyoccam v0.9.0 - Reconstructability Analysis for Python*
