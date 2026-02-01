"""
ArcGIS Pro Python Toolbox (.pyt) for Information Theory Analysis
Designed for Reconstructability Analysis preparation and spatial modeling
"""

import arcpy
import pandas as pd
import numpy as np
import math
from pathlib import Path
import json
from itertools import combinations

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Information Theory Toolbox for RA"
        self.alias = "InfoTheoryRA"
        self.tools = [InformationGainTool, OptimalBinningTool, 
                     OccamPreprocessor, ProbabilitySurfaceGenerator]

class InformationGainTool(object):
    def __init__(self):
        """Define the Information Gain Analysis tool."""
        self.label = "Calculate Information Gain"
        self.description = "Calculate information gain for categorical variables"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions."""
        params = []
        
        # Input feature class
        param0 = arcpy.Parameter(
            displayName="Input Feature Class",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        params.append(param0)
        
        # Target field
        param1 = arcpy.Parameter(
            displayName="Target Field (Binary 0/1)",
            name="target_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param1.parameterDependencies = [param0.name]
        params.append(param1)
        
        # Analysis fields
        param2 = arcpy.Parameter(
            displayName="Fields to Analyze",
            name="analysis_fields",
            datatype="Field",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param2.parameterDependencies = [param0.name]
        params.append(param2)
        
        # Encodings folder
        param3 = arcpy.Parameter(
            displayName="Encodings Folder (Optional)",
            name="encodings_folder",
            datatype="DEFolder",
            parameterType="Optional",
            direction="Input")
        params.append(param3)
        
        # Output table
        param4 = arcpy.Parameter(
            displayName="Output Information Gain Table",
            name="out_table",
            datatype="DETable",
            parameterType="Required",
            direction="Output")
        params.append(param4)
        
        # Output report
        param5 = arcpy.Parameter(
            displayName="Output HTML Report",
            name="out_report",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")
        param5.filter.list = ['html']
        params.append(param5)
        
        return params

    def execute(self, parameters, messages):
        """Execute the tool."""
        # Get parameters
        in_features = parameters[0].valueAsText
        target_field = parameters[1].valueAsText
        analysis_fields = parameters[2].valueAsText.split(';')
        encodings_folder = parameters[3].valueAsText
        out_table = parameters[4].valueAsText
        out_report = parameters[5].valueAsText
        
        # Convert to DataFrame
        messages.addMessage("Converting features to DataFrame...")
        field_list = [target_field] + analysis_fields
        data = []
        
        with arcpy.da.SearchCursor(in_features, field_list) as cursor:
            for row in cursor:
                data.append(dict(zip(field_list, row)))
        
        df = pd.DataFrame(data)
        
        # Load encodings if provided
        encodings = {}
        if encodings_folder:
            messages.addMessage(f"Loading encodings from {encodings_folder}")
            encoding_path = Path(encodings_folder)
            for encoding_file in encoding_path.glob('*_encoding.csv'):
                var_name = encoding_file.stem.replace('_encoding', '')
                encodings[var_name] = pd.read_csv(encoding_file)
        
        # Calculate information gains
        results = []
        
        for field in analysis_fields:
            messages.addMessage(f"Analyzing {field}...")
            
            # Calculate entropy metrics
            ig_result = self._calculate_information_gain(df, field, target_field)
            
            # Add encoding descriptions if available
            description = ""
            if field in encodings:
                description = "Encoded variable"
            
            results.append({
                'Variable': field,
                'InformationGain': ig_result['information_gain'],
                'ConditionalEntropy': ig_result['conditional_entropy'],
                'UniqueValues': len(ig_result['class_stats']),
                'Description': description
            })
        
        # Create output table
        messages.addMessage("Creating output table...")
        
        # Create table
        arcpy.management.CreateTable(
            out_path=str(Path(out_table).parent),
            out_name=str(Path(out_table).name)
        )
        
        # Add fields
        arcpy.management.AddField(out_table, "Variable", "TEXT", field_length=50)
        arcpy.management.AddField(out_table, "InformationGain", "DOUBLE")
        arcpy.management.AddField(out_table, "ConditionalEntropy", "DOUBLE")
        arcpy.management.AddField(out_table, "UniqueValues", "LONG")
        arcpy.management.AddField(out_table, "Description", "TEXT", field_length=255)
        
        # Insert rows
        with arcpy.da.InsertCursor(out_table, 
                                  ["Variable", "InformationGain", "ConditionalEntropy", 
                                   "UniqueValues", "Description"]) as cursor:
            for result in sorted(results, key=lambda x: x['InformationGain'], reverse=True):
                cursor.insertRow([
                    result['Variable'],
                    result['InformationGain'],
                    result['ConditionalEntropy'],
                    result['UniqueValues'],
                    result['Description']
                ])
        
        # Generate HTML report if requested
        if out_report:
            self._generate_html_report(results, df, target_field, 
                                      analysis_fields, out_report)
            messages.addMessage(f"HTML report saved to {out_report}")
        
        messages.addMessage("Information gain analysis complete!")
        return

    def _calculate_information_gain(self, df, variable, target):
        """Calculate information gain for a variable."""
        # Calculate target entropy
        target_probs = df[target].value_counts(normalize=True).to_dict()
        target_entropy = -sum(p * math.log2(p) if p > 0 else 0 
                             for p in target_probs.values())
        
        # Calculate conditional entropy
        conditional_entropy = 0
        class_stats = {}
        
        valid_data = df.dropna(subset=[variable, target])
        
        for value in valid_data[variable].unique():
            value_data = valid_data[valid_data[variable] == value]
            value_prob = len(value_data) / len(valid_data)
            
            # Value entropy
            value_target_probs = value_data[target].value_counts(normalize=True).to_dict()
            value_entropy = -sum(p * math.log2(p) if p > 0 else 0 
                                for p in value_target_probs.values())
            
            conditional_entropy += value_prob * value_entropy
            
            # Store statistics
            class_stats[value] = {
                'frequency': len(value_data),
                'probability': value_prob,
                'conditional_prob': value_data[target].mean(),
                'entropy': value_entropy
            }
        
        information_gain = target_entropy - conditional_entropy
        
        return {
            'information_gain': information_gain,
            'target_entropy': target_entropy,
            'conditional_entropy': conditional_entropy,
            'class_stats': class_stats
        }
    
    def _generate_html_report(self, results, df, target_field, 
                             analysis_fields, output_path):
        """Generate HTML report."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Information Gain Analysis - ArcGIS Pro</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
                h1 { color: #2b7bb9; }
                h2 { color: #555; border-bottom: 2px solid #2b7bb9; padding-bottom: 5px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th { background-color: #2b7bb9; color: white; padding: 10px; text-align: left; }
                td { border: 1px solid #ddd; padding: 8px; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .high-ig { background-color: #d4edda; }
                .medium-ig { background-color: #fff3cd; }
                .low-ig { background-color: #f8d7da; }
            </style>
        </head>
        <body>
            <h1>Information Gain Analysis for Reconstructability Analysis</h1>
            <p><strong>Analysis Date:</strong> {}</p>
            <p><strong>Target Variable:</strong> {}</p>
            <p><strong>Number of Records:</strong> {}</p>
        """.format(
            pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            target_field,
            len(df)
        )
        
        # Summary table
        html += """
            <h2>Variable Ranking by Information Gain</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Variable</th>
                    <th>Information Gain (bits)</th>
                    <th>Unique Values</th>
                    <th>Recommendation</th>
                </tr>
        """
        
        sorted_results = sorted(results, key=lambda x: x['InformationGain'], reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            ig = result['InformationGain']
            
            # Determine recommendation
            if ig > 0.15:
                rec = "High importance - Include in model"
                class_str = "high-ig"
            elif ig > 0.05:
                rec = "Medium importance - Consider including"
                class_str = "medium-ig"
            else:
                rec = "Low importance - May exclude"
                class_str = "low-ig"
            
            html += f"""
                <tr class="{class_str}">
                    <td>{i}</td>
                    <td>{result['Variable']}</td>
                    <td>{ig:.4f}</td>
                    <td>{result['UniqueValues']}</td>
                    <td>{rec}</td>
                </tr>
            """
        
        html += """
            </table>
            <h2>Recommendations for Occam Analysis</h2>
            <ul>
                <li>Variables with information gain > 0.15 should be prioritized</li>
                <li>Consider binning variables with > 7 unique values</li>
                <li>Test 2-way and 3-way combinations of top variables</li>
                <li>Use conditional probability method for interpretability</li>
            </ul>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html)


class OptimalBinningTool(object):
    def __init__(self):
        """Define the Optimal Binning tool."""
        self.label = "Optimal Binning for Variables"
        self.description = "Find optimal binning strategy for categorical variables"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions."""
        params = []
        
        # Input feature class
        param0 = arcpy.Parameter(
            displayName="Input Feature Class",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        params.append(param0)
        
        # Target field
        param1 = arcpy.Parameter(
            displayName="Target Field (Binary 0/1)",
            name="target_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param1.parameterDependencies = [param0.name]
        params.append(param1)
        
        # Variable to bin
        param2 = arcpy.Parameter(
            displayName="Variable to Bin",
            name="bin_variable",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.parameterDependencies = [param0.name]
        params.append(param2)
        
        # Maximum bins
        param3 = arcpy.Parameter(
            displayName="Maximum Number of Bins",
            name="max_bins",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param3.value = 3
        params.append(param3)
        
        # Method
        param4 = arcpy.Parameter(
            displayName="Binning Method",
            name="method",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = ["Conditional Probability", "Mutual Information"]
        param4.value = "Conditional Probability"
        params.append(param4)
        
        # Output feature class
        param5 = arcpy.Parameter(
            displayName="Output Feature Class with Binned Field",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        params.append(param5)
        
        # Output binning configuration
        param6 = arcpy.Parameter(
            displayName="Output Binning Configuration (JSON)",
            name="out_config",
            datatype="DEFile",
            parameterType="Optional",
            direction="Output")
        param6.filter.list = ['json']
        params.append(param6)
        
        return params

    def execute(self, parameters, messages):
        """Execute the tool."""
        # Get parameters
        in_features = parameters[0].valueAsText
        target_field = parameters[1].valueAsText
        bin_variable = parameters[2].valueAsText
        max_bins = parameters[3].value
        method = parameters[4].valueAsText
        out_features = parameters[5].valueAsText
        out_config = parameters[6].valueAsText
        
        # Convert method string
        method_str = 'conditional_probability' if 'Conditional' in method else 'mutual_information'
        
        # Read data
        messages.addMessage("Reading input data...")
        field_list = [target_field, bin_variable]
        
        # Also get OID field for joining
        oid_field = arcpy.Describe(in_features).OIDFieldName
        field_list.insert(0, oid_field)
        
        data = []
        with arcpy.da.SearchCursor(in_features, field_list) as cursor:
            for row in cursor:
                data.append(dict(zip(field_list, row)))
        
        df = pd.DataFrame(data)
        
        # Calculate optimal binning
        messages.addMessage(f"Calculating optimal binning using {method}...")
        binning_result = self._calculate_optimal_binning(
            df, bin_variable, target_field, max_bins, method_str
        )
        
        messages.addMessage(f"Optimal number of bins: {binning_result['n_bins']}")
        messages.addMessage(f"Rebinning string: {binning_result['rebinning_string']}")
        
        # Create binned field values
        bin_map = {}
        for bin_num, values in binning_result['bins'].items():
            for val in values:
                bin_map[val] = bin_num
        
        df['binned_value'] = df[bin_variable].map(bin_map)
        
        # Copy features and add binned field
        messages.addMessage("Creating output feature class...")
        arcpy.management.CopyFeatures(in_features, out_features)
        
        # Add binned field
        binned_field_name = f"{bin_variable}_bin"
        arcpy.management.AddField(out_features, binned_field_name, "SHORT")
        
        # Update values
        with arcpy.da.UpdateCursor(out_features, [oid_field, binned_field_name]) as cursor:
            for row in cursor:
                oid = row[0]
                binned_val = df[df[oid_field] == oid]['binned_value'].iloc[0]
                row[1] = binned_val if not pd.isna(binned_val) else None
                cursor.updateRow(row)
        
        # Save configuration if requested
        if out_config:
            config = {
                'variable': bin_variable,
                'method': method_str,
                'n_bins': binning_result['n_bins'],
                'bins': {str(k): v for k, v in binning_result['bins'].items()},
                'bin_probabilities': binning_result['bin_probabilities'],
                'rebinning_string': binning_result['rebinning_string']
            }
            
            with open(out_config, 'w') as f:
                json.dump(config, f, indent=2)
            
            messages.addMessage(f"Binning configuration saved to {out_config}")
        
        messages.addMessage("Optimal binning complete!")
        return

    def _calculate_optimal_binning(self, df, variable, target, max_bins, method):
        """Calculate optimal binning."""
        # Similar implementation as in the core module
        # ... (implementation details)
        pass


class OccamPreprocessor(object):
    """Tool to preprocess data for Occam analysis."""
    # Implementation similar to above tools
    pass


class ProbabilitySurfaceGenerator(object):
    """Tool to generate probability surfaces from Occam output."""
    # Implementation similar to above tools
    pass