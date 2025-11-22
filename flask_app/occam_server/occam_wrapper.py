#!/usr/bin/env python3
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

"""
Compatibility wrapper for OCCAM Python 3 bindings

This module provides a compatibility layer between the old ocutils.py API
and the new pybind11-based _pyoccam module. It allows the Flask web server
to use modern Python 3 bindings while maintaining a familiar interface.
"""

import sys
from pathlib import Path

try:
    from pyoccam import _pyoccam
except ImportError:
    print("ERROR: _pyoccam module not found. Please install pyoccam:")
    print("  pip install pyoccam")
    print("Or build and install from source:")
    print("  meson setup builddir && ninja -C builddir")
    print("  pip install pyoccam/")
    sys.exit(1)

# Import graph generation module
try:
    import ocGraph
    GRAPH_SUPPORT = True
except ImportError:
    GRAPH_SUPPORT = False
    print("Warning: ocGraph module not found. Graph generation will be disabled.")


class OccamManager:
    """
    Wrapper class that provides ocutils.py-compatible API
    using the new pybind11 bindings.
    """

    # Report separators
    TABSEP = 1
    COMMASEP = 2
    SPACESEP = 3
    HTMLFORMAT = 4

    def __init__(self, manager_type="VB"):
        """
        Initialize OCCAM manager

        Args:
            manager_type: "VB" for Variable-Based or "SB" for State-Based
        """
        self.manager_type = manager_type

        if manager_type == "VB":
            self.__manager = _pyoccam.VBMManager()
        elif manager_type == "SB":
            self.__manager = _pyoccam.SBMManager()
        else:
            raise ValueError(f"Invalid manager type: {manager_type}")

        # Configuration
        self.__report_separator = self.SPACESEP
        self.__data_file = ""
        self.__skip_nominal = False
        self.__skip_residuals = True
        self.__skip_ivi_tables = True
        self.__calc_expected_dv = False
        self.__fit_classifier_target = ""
        self.__default_fit_model = ""

        # Graph options
        self.__gfx_enabled = False
        self.__gephi_enabled = False
        self.__graph_layout = "default"
        self.__hide_isolated = True
        self.__hide_dv = False
        self.__full_var_names = False
        self.__graph_width = 640
        self.__graph_height = 480
        self.__graph_font_size = 12
        self.__graph_node_size = 24

        # Graph storage
        self.graphs = {}

    def init_from_file(self, datafile):
        """Initialize from data file"""
        self.__data_file = datafile
        success = self.__manager.init_from_command_line(["occam", datafile])
        if not success:
            raise RuntimeError("Failed to initialize OCCAM from data file")
        return success

    def init_from_command_line(self, argv):
        """Initialize from command line arguments (legacy compatibility)"""
        if len(argv) > 1:
            self.__data_file = argv[1]
        return self.__manager.init_from_command_line(argv)

    # Configuration methods

    def set_report_separator(self, separator):
        """Set report separator format"""
        self.__report_separator = separator
        self.__manager.set_report_separator(separator)

    def set_data_file(self, datafile):
        """Set data file name (for reference only)"""
        self.__data_file = datafile

    def set_skip_nominal(self, skip):
        """Set whether to skip nominal variables"""
        self.__skip_nominal = bool(skip)
        # Note: May need to add to pybind11 if not present

    def set_skip_residuals(self, skip):
        """Set whether to skip residuals table"""
        self.__skip_residuals = bool(skip)
        self.__manager.set_skip_trained_model_table(skip)

    def set_skip_ivi_tables(self, skip):
        """Set whether to skip IVI tables"""
        self.__skip_ivi_tables = bool(skip)
        self.__manager.set_skip_ivi_tables(skip)

    def set_calc_expected_dv(self, calc):
        """Set whether to calculate expected DV"""
        self.__calc_expected_dv = bool(calc)
        self.__manager.set_calc_expected_dv(calc)

    def set_fit_classifier_target(self, target):
        """Set target state for classifier confusion matrix"""
        self.__fit_classifier_target = target
        self.__manager.set_fit_classifier_target(target)

    def set_default_fit_model(self, model):
        """Set default model for comparison"""
        self.__default_fit_model = model
        self.__manager.set_default_fit_model(model)

    def set_ref_model(self, refmodel):
        """Set reference model"""
        self.__manager.set_ref_model(refmodel)

    def set_gfx(self, gfx=False, gephi=False, layout="default",
                hide_isolated=True, hide_dv=False, full_var_names=False,
                width=640, height=480, fontSize=12, nodeSize=24,
                **kwargs):
        """Configure graph generation options"""
        self.__gfx_enabled = gfx
        self.__gephi_enabled = gephi
        self.__graph_layout = layout
        self.__hide_isolated = hide_isolated
        self.__hide_dv = hide_dv
        self.__full_var_names = full_var_names
        self.__graph_width = width
        self.__graph_height = height
        self.__graph_font_size = fontSize
        self.__graph_node_size = nodeSize

    # Core operations

    def do_fit(self, model_name, target_state=""):
        """
        Perform model fitting

        Args:
            model_name: Model specification string
            target_state: Target state for confusion matrix

        Returns:
            str: Formatted fit report
        """
        if target_state:
            self.set_fit_classifier_target(target_state)

        report = self.__manager.generate_fit_report(model_name, target_state)
        return report

    def do_search(self, search_type, levels, width, **kwargs):
        """
        Perform model search

        Args:
            search_type: Search algorithm (e.g., "loopless-up")
            levels: Number of search levels
            width: Beam width

        Returns:
            str: Formatted search report
        """
        report = self.__manager.generate_search_report(search_type, levels, width)
        return report

    def get_best_model_by_bic(self):
        """Get best model by BIC"""
        return self.__manager.get_best_model_by_bic()

    def get_best_model_by_aic(self):
        """Get best model by AIC"""
        return self.__manager.get_best_model_by_aic()

    def get_best_model_by_information(self):
        """Get best model by information"""
        return self.__manager.get_best_model_by_information()

    # Information getters

    def get_variable_list(self):
        """Get list of variable names"""
        return self.__manager.get_variable_list()

    def get_sample_size(self):
        """Get sample size"""
        return self.__manager.get_sample_size()

    def has_test_data(self):
        """Check if test data is available"""
        return self.__manager.has_test_data()

    def is_directed(self):
        """Check if system is directed"""
        # Directed if DV is defined
        try:
            vars = self.get_variable_list()
            # Check for :DV in variable definitions
            return any(':DV' in str(v) for v in vars)
        except:
            return False

    def get_basic_statistics(self):
        """Get basic statistics string"""
        return self.__manager.get_basic_statistics()

    def get_kept_models(self):
        """Get list of models kept from search"""
        return self.__manager.get_kept_models()

    # Legacy compatibility methods (may not all be needed)

    def make_model(self, model_name, make_fit_table=False):
        """Create a model"""
        return self.__manager.make_model(model_name, make_fit_table)

    def get_model_statistics(self, model_name):
        """Get statistics for a model"""
        return self.__manager.get_model_statistics(model_name)

    # Graph generation methods

    def generate_graph(self, model_name):
        """
        Generate graph for a model

        Args:
            model_name: Model specification string

        Returns:
            igraph.Graph: Generated graph object, or None if graph support disabled
        """
        if not GRAPH_SUPPORT:
            return None

        if model_name in self.graphs:
            return self.graphs[model_name]

        # Get variable list
        varlist = self.get_variable_list()

        # Determine if system is directed
        dv_name = ""
        if self.is_directed():
            # Extract DV name from variable list
            for var in varlist:
                if ':DV' in str(var):
                    dv_name = str(var).replace(':DV', '').strip()
                    break

        # Determine if using bipartite layout
        all_higher_order = (self.__graph_layout == "bipartite")

        # Generate graph
        graph = ocGraph.generate(
            model_name,
            varlist,
            self.__hide_isolated,
            self.__hide_dv,
            dv_name,
            self.__full_var_names,
            all_higher_order
        )

        self.graphs[model_name] = graph
        return graph

    def get_graph_svg(self, model_name):
        """
        Get SVG representation of graph

        Args:
            model_name: Model specification string

        Returns:
            str: SVG file path, or None if graph generation disabled
        """
        if not GRAPH_SUPPORT or not self.__gfx_enabled:
            return None

        graph = self.generate_graph(model_name)
        if graph is None:
            return None

        svg_file = ocGraph.printPlot(
            graph,
            self.__graph_layout,
            "svg",
            "graph",
            self.__graph_width,
            self.__graph_height,
            self.__graph_font_size,
            self.__graph_node_size
        )
        return svg_file

    def get_graph_pdf(self, model_name, filename="graph"):
        """
        Get PDF representation of graph

        Args:
            model_name: Model specification string
            filename: Base filename for PDF

        Returns:
            str: PDF file path, or None if graph generation disabled
        """
        if not GRAPH_SUPPORT or not self.__gfx_enabled:
            return None

        graph = self.generate_graph(model_name)
        if graph is None:
            return None

        pdf_file = ocGraph.printPDF(
            filename,
            graph,
            self.__graph_layout,
            self.__graph_width,
            self.__graph_height,
            self.__graph_font_size,
            self.__graph_node_size
        )
        return pdf_file

    def get_gephi_output(self, model_name):
        """
        Get Gephi format output for graph

        Args:
            model_name: Model specification string

        Returns:
            dict: Dictionary with 'nodes' and 'edges' CSV strings, or None
        """
        if not GRAPH_SUPPORT or not self.__gephi_enabled:
            return None

        graph = self.generate_graph(model_name)
        if graph is None:
            return None

        nodes_csv = ocGraph.gephiNodes(graph)
        edges_csv = ocGraph.gephiEdges(graph)

        return {
            'nodes': nodes_csv,
            'edges': edges_csv
        }


# For backwards compatibility, provide module-level constants
TABSEP = OccamManager.TABSEP
COMMASEP = OccamManager.COMMASEP
SPACESEP = OccamManager.SPACESEP
HTMLFORMAT = OccamManager.HTMLFORMAT
