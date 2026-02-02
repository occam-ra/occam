#!/usr/bin/env python
"""
PyOccam Command Line Interface

Usage:
    python -m pyoccam csv2occam input.csv [options]
    
Examples:
    # Basic conversion (last column = DV, max cardinality = 20)
    python -m pyoccam csv2occam mydata.csv
    
    # Custom cardinality threshold
    python -m pyoccam csv2occam mydata.csv --max-cardinality 30
    
    # Specify DV column and exclusions
    python -m pyoccam csv2occam mydata.csv --dv LS --exclude x,y,Pt_ID,OBJECTID
    
    # Custom output filename
    python -m pyoccam csv2occam mydata.csv -o mydata_occam.txt
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='PyOccam - Reconstructability Analysis Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  csv2occam    Convert CSV file to OCCAM input format
  version      Show version information
  help         Show help for PyOccam functions

Examples:
  python -m pyoccam csv2occam data.csv --max-cardinality 30
  python -m pyoccam csv2occam data.csv --dv target --exclude ID,Name
  python -m pyoccam version
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # csv2occam command
    csv_parser = subparsers.add_parser('csv2occam', 
        help='Convert CSV to OCCAM format',
        description='Convert a standard CSV file to OCCAM input format')
    
    csv_parser.add_argument('input', 
        help='Input CSV file path')
    
    csv_parser.add_argument('-o', '--output',
        help='Output OCCAM file path (default: input with .txt extension)')
    
    csv_parser.add_argument('-c', '--max-cardinality', 
        type=int, default=20,
        help='Maximum cardinality before column is excluded (default: 20)')
    
    csv_parser.add_argument('-d', '--dv', '--dependent-variable',
        dest='dv_column',
        help='Name or index of dependent variable column (default: last column)')
    
    csv_parser.add_argument('-e', '--exclude',
        help='Comma-separated list of column names to exclude (e.g., "ID,Name,Date")')
    
    csv_parser.add_argument('-t', '--test-split',
        type=float, default=None,
        help='Fraction of data for test set (0.0-1.0, e.g., 0.2 for 20%% test)')
    
    csv_parser.add_argument('-r', '--random-state',
        type=int, default=42,
        help='Random seed for train/test split (default: 42)')
    
    csv_parser.add_argument('-q', '--quiet',
        action='store_true',
        help='Suppress progress messages')
    
    csv_parser.add_argument('--no-search',
        action='store_true',
        help='Skip the automatic quick search after conversion')
    
    # version command
    version_parser = subparsers.add_parser('version', help='Show version')
    
    # help command  
    help_parser = subparsers.add_parser('help', help='Show PyOccam help')
    
    args = parser.parse_args()
    
    if args.command == 'csv2occam':
        run_csv2occam(args)
    elif args.command == 'version':
        from . import __version__
        print(f"PyOccam version {__version__}")
    elif args.command == 'help':
        from . import help as pyoccam_help
        pyoccam_help()
    else:
        parser.print_help()
        sys.exit(1)

def run_csv2occam(args):
    """Run the CSV to OCCAM conversion."""
    from . import make_occam_input_from_csv
    
    # Parse exclude columns
    exclude_columns = None
    if args.exclude:
        exclude_columns = [col.strip() for col in args.exclude.split(',')]
    
    # Parse DV column (could be int or string)
    dv_column = args.dv_column
    if dv_column is not None:
        try:
            dv_column = int(dv_column)
        except ValueError:
            pass  # Keep as string (column name)
    
    # Run conversion
    output_file, data = make_occam_input_from_csv(
        csv_filename=args.input,
        output_filename=args.output,
        max_cardinality=args.max_cardinality,
        dv_column=dv_column,
        exclude_columns=exclude_columns,
        test_split=args.test_split,
        random_state=args.random_state,
        verbose=not args.quiet
    )
    
    # Optionally run quick search
    if data and not args.no_search:
        print("\n" + "="*60)
        print("Running quick search...")
        print("="*60)
        best = data.quick_search(search_type="loopless-up", levels=3, width=3)
        
        # Get confusion matrix
        cm = data.manager.get_confusion_matrix(best, target_state="0")
        if cm.get('has_values', False):
            print(f"\nTrain Accuracy: {cm['train_accuracy']:.1%}")
            # Show test accuracy if we have test data
            if data.has_test_data and 'test_accuracy' in cm:
                print(f"Test Accuracy:  {cm['test_accuracy']:.1%}")

if __name__ == '__main__':
    main()
