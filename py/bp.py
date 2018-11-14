#! /usr/bin/python
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import os, sys, occam

from ocutils import ocUtils

#------------- Main script ---------------
# This script sets various options on a ocUtils object, and then
# runs the desired action. ocUtils is a convenience wrapper around
# the basic occam3 objects, and it sets appropriate defaults if you
# don't set every option.

# For settings which require model attribute names,
# the allowed values are:
# h
# t
# df
# ddf
# loops		-- 1=loops, 0=no loops
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
# p2		-- note that the Pearson statistics aren't
# p2		-- computed by default because they are expensive
# p2_alpha
# p2_alpha
# p2_beta
# p2_beta

# To force a particular attribute to be printed as an integer,
# append "$I" to the name (e.g., Level$I)

#-------------------------------------------------

# create an ocUtils object. This is a convenience wrapper which can
# handle Occam2 files and options
# See the source file for other options which can be set

util = ocUtils()
util.initFromCommandLine(sys.argv)

# set desired options which aren't in the data file, or override them
# here.

# set separator between report fields.
# 1=tab, 2=comma, 3=space fill, 4=HTML
util.setReportSeparator(3)

# set report names, from the list above. If omitted, the list is set
# based on whether the ref model is top or bottom. List is separated
# by commas, and provided as a single text string
# for ref=top, this is a good list:
#util.setReportVars("Level$I, h, ddf, lr, alpha, information")
# for ref=bottom, use something like this:
#util.setReportVars("Level$I, h, ddf, lr, alpha, information")
util.setReportVariables("Level$I, bp_t, ddf, h")


# set the model attribute on which sorting is done is done. This
# controls the selection of "best models" during search. It can
# also control reporting (see setReportSortName, below)
util.setSortName("bp_t")

# set the model attribute for sorting the report, if it is different
# from the attribute used during search. Generally this isn't needed.
util.setReportSortName("bp_t")

# set the search direction (up, down)
#util.setSearchDir("up")

# set the search filter (all, loopless, disjoint)
util.setSearchFilter("all")

# set the ref model (bottom, top, default, or a specific model)
util.setRefModel("bottom")

# set the start model for search (top, bottom, default, or a model name)
# skip this to use the model set in the data file
#util.setStartModel("ABC:CD")

# set the sorting direction for pruning and reporting
# ascending means lower values are better
# descending means higher values are better
util.setSortDir("descending")

# set the search width
util.setSearchWidth(5)

# set the number of levels to search
util.setSearchLevels(5)

# set model for fit. Skip this to set it from the data file
#util.setFitModel("ABC:CD")

# set the action (fit, search). Skip this to set it from the data file
#util.setAction("fit")

# leave this in, if you want a full list of program options printed
util.printOptions()

util.setNoIPF(1);

# perform the search or fit, and print report
util.doAction(1)

