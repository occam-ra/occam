"""
Cleanup script to move test/debug files out of the pyoccam package folder.
This ensures only essential files are shipped with pip install.
"""
import os
import shutil
from pathlib import Path

# Source and destination
PYOCCAM_DIR = Path(r"D:\projects\occam\pyoccam")
DEV_FILES_DIR = Path(r"D:\projects\occam\dev_files")

# Files to KEEP in pyoccam/ (essential for package)
KEEP_FILES = {
    '__init__.py',
    '__main__.py',
    'pyoccam_pybind11.cpp',
    'README.md',
    'dementia05.txt',
    'landslides.txt',
    'pyoccam_demo.py',
    'pyoccam_demo.ipynb',
    # DLLs
    'libgcc_s_seh-1.dll',
    'libstdc++-6.dll', 
    'libwinpthread-1.dll',
}

# Directories to KEEP
KEEP_DIRS = {
    '__pycache__',
    'examples',  # if it exists and is needed
}

# File patterns to ALWAYS move (even if not matching other rules)
MOVE_PATTERNS = [
    'test_',
    'debug_',
    'diagnose_',
    'verify_',
    'check_',
    'minimal_',
    'isolate_',
    'examine_',
    'temp_',
    'unified_ra_ml_',
    'fullup_cv_',
    'sklearn_baseline_',
    'python_cm_',
    'python_usage_',
    'simple_confusion_',
    'final_test_',
    'find_source_',
    'cm_debug_',
    'cm_verification',
    'cm_verify_',
    'hang_diagnostic',
    'pyoccam2_',
    'pyoccam_csv_',
    'pyoccam_diagnostic',
    'PyOccam_Vizzies',
]

# Extensions that indicate output/temp files (move these)
MOVE_EXTENSIONS = {
    '.bak', '.bak2', '.oldCM',
}

# Create destination directory
DEV_FILES_DIR.mkdir(exist_ok=True)

# Track what we move
moved_files = []
moved_dirs = []
kept_files = []

# Process files
for item in PYOCCAM_DIR.iterdir():
    name = item.name
    
    # Skip __pycache__
    if name == '__pycache__':
        continue
        
    # Check if it's a .pyd file (keep these - compiled extensions)
    if item.suffix == '.pyd':
        kept_files.append(name)
        continue
    
    # Check if explicitly kept
    if name in KEEP_FILES:
        kept_files.append(name)
        continue
    
    # Check if it's a directory we want to move
    if item.is_dir():
        if name not in KEEP_DIRS:
            dest = DEV_FILES_DIR / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(item), str(dest))
            moved_dirs.append(name)
        continue
    
    # Check move patterns
    should_move = False
    for pattern in MOVE_PATTERNS:
        if name.startswith(pattern) or pattern in name.lower():
            should_move = True
            break
    
    # Check extensions
    if item.suffix.lower() in MOVE_EXTENSIONS:
        should_move = True
    
    # Check for backup/copy indicators in name
    if 'Copy' in name or 'original' in name or 'bak' in name.lower():
        should_move = True
    
    # Check for output txt files (but keep dementia05.txt and landslides.txt)
    if item.suffix == '.txt' and name not in KEEP_FILES:
        should_move = True
    
    # Check for non-essential .py files
    if item.suffix == '.py' and name not in KEEP_FILES:
        should_move = True
    
    # Check for non-essential .ipynb files
    if item.suffix == '.ipynb' and name not in KEEP_FILES:
        should_move = True
    
    # Check for .csv files
    if item.suffix == '.csv':
        should_move = True
    
    # Check for .md files (except README.md)
    if item.suffix == '.md' and name != 'README.md':
        should_move = True
    
    if should_move:
        dest = DEV_FILES_DIR / name
        shutil.move(str(item), str(dest))
        moved_files.append(name)
    else:
        kept_files.append(name)

# Report
print("="*70)
print("CLEANUP COMPLETE")
print("="*70)
print(f"\nFiles KEPT in pyoccam/ ({len(kept_files)}):")
for f in sorted(kept_files):
    print(f"  {f}")

print(f"\nFiles MOVED to dev_files/ ({len(moved_files)}):")
for f in sorted(moved_files)[:20]:
    print(f"  {f}")
if len(moved_files) > 20:
    print(f"  ... and {len(moved_files) - 20} more")

print(f"\nDirectories MOVED to dev_files/ ({len(moved_dirs)}):")
for d in sorted(moved_dirs):
    print(f"  {d}/")

print(f"\nTotal: {len(kept_files)} kept, {len(moved_files)} files moved, {len(moved_dirs)} dirs moved")
