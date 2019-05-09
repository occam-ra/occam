#! /usr/bin/python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import sys

sys.path.insert(0, "./wrappers")


from ocutils import OCUtils
from wrappers.manager import SearchFilter
from wrappers.model import ModelType
from wrappers.report import SortDirection, ReportSortName

# ------------- Main script ---------------
# This script sets various options on a OCUtils object, and then
# runs the desired action. OCUtils is a convenience wrapper around
# the basic occam3 objects, and it sets appropriate defaults if you
# don't set every option.

# For settings which require model attribute names,
# the allowed values are:
# h
# t
# df
# ddf
# loops     -- 1=loops, 0=no loops
# information
# unexplained
# ipf_iterations
# cond_h
# cond_dh
# cond_pct_dh
# cond_df
# cond_ddf
# lr
# alpha
# beta
# level
# p2        -- note that the Pearson statistics aren't
# p2        -- computed by default because they are expensive
# p2_alpha
# p2_alpha
# p2_beta
# p2_beta

# To force a particular attribute to be printed as an integer,
# append "$I" to the name (e.g., Level$I)

# -------------------------------------------------

# create an OCUtils object. This is a convenience wrapper which can
# handle Occam2 files and options
# See the source file for other options which can be set

util = OCUtils()
util.init_from_command_line(sys.argv)

# set desired options which aren't in the data file, or override them
# here.

# set separator between report fields.
# 1=tab, 2=comma, 3=space fill, 4=HTML
util.set_report_separator(3)

# set report names, from the list above. If omitted, the list is set
# based on whether the ref model is top or bottom. List is separated
# by commas, and provided as a single text string
# for ref=top, this is a good list:
# util.set_report_vars("Level$I, h, ddf, lr, alpha, information")
# for ref=bottom, use something like this:
# util.set_report_vars("Level$I, h, ddf, lr, alpha, information")
util.set_report_variables("Level$I, bp_t, ddf, h")


# set the model attribute on which sorting is done is done. This
# controls the selection of "best models" during search. It can
# also control reporting (see set_report_sort_name, below)
util.set_report_sort_name(ReportSortName.BPT)

# set the model attribute for sorting the report, if it is different
# from the attribute used during search. Generally this isn't needed.
util.set_report_sort_name(ReportSortName.BPT)

# set the search direction (up, down)
# util.set_search_dir("up")

# set the search filter (all, loopless, disjoint)
util.set_search_filter(SearchFilter.ALL)

# set the ref model (bottom, top, default, or a specific model)
util.set_ref_model(ModelType.BOTTOM)

# set the start model for search (top, bottom, default, or a model name)
# skip this to use the model set in the data file
# util.set_start_model("ABC:CD")

# set the sorting direction for pruning and reporting
# ascending means lower values are better
# descending means higher values are better
util.set_sort_dir(SortDirection.DESCENDING)

# set the search width
util.set_search_width(5)

# set the number of levels to search
util.set_search_levels(5)

# set model for fit. Skip this to set it from the data file
# util.set_fit_model("ABC:CD")

# set the action (fit, search). Skip this to set it from the data file
# util.set_action("fit")

# leave this in, if you want a full list of program options printed
util.print_options(1)

util.set_no_ipf(1)

# perform the search or fit, and print report
util.do_action(1)
