#! python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import resource
import sys

sys.path.insert(0, "./wrappers")

# sys.path.append("/www")
import time

from ocutils import OCUtils, Action
from wrappers.report import SortDirection, SeparatorType

resource.setrlimit(resource.RLIMIT_CORE, [360000, 360000])

# This section of the script allows you to specify the most frequently changed options from the command line.
# The width, levels and filter are determined here, to be used by the rest of the script below.
if len(sys.argv) < 2:
    print('No data file specified.')
    print(
        f'Usage: {sys.argv[0]} datafile [width levels] ["all"|"loopless"|"disjoint"|"chain"]'
    )
    sys.exit()

if len(sys.argv) >= 4:
    swidth = sys.argv[2]
    slevels = sys.argv[3]
else:
    swidth = 3
    slevels = 7

if len(sys.argv) >= 5:
    filter_ = sys.argv[4]
else:
    filter_ = "loopless"


util = OCUtils("SB")  # create a variable-based manager
t1 = time.time()
util.init_from_command_line(sys.argv[0:2])  # initialize with the data file

# ------------- Main script ---------------
# This script sets various options on a OCUtils object, and then runs the desired action.
# OCUtils is a convenience wrapper around the basic occam3 objects, and it sets appropriate
# defaults if you don't set every option.

# For settings which require model attribute names, the allowed values include:
# h, t, df, ddf, loops [1=loops, 0=no loops]
# information, unexplained, ipf_iterations, lr, alpha, beta, level, aic, bic
# cond_h, cond_dh, cond_pct_dh, cond_df, cond_ddf, p2, p2_alpha, p2_beta
# (Note that the Pearson statistics aren't computed by default because they are expensive.)
# To force a particular attribute to be printed as an integer, append "$I" to the name (e.g., Level$I)

# Set separator between report fields.  [1=tab, 2=comma, 3=space fill, 4=HTML]
util.set_report_separator(SeparatorType.SPACE)

# Set the sorting direction for reporting.
util.set_sort_dir(SortDirection.DESCENDING)

# Set the search width & number of levels.
util.set_search_width(swidth)
util.set_search_levels(slevels)

util.set_use_inverse_notation(0)

# Set the start model for search [top, bottom, default, a specific model].
# Skip this to use the model set in the data file.
util.set_start_model("bottom")
# util.set_start_model("IV:A38Z")

# Set the ref model [top, bottom, default, a specific model].
util.set_ref_model("bottom")

# Set the sorting direction for the search. ["ascending" prefers lower values, "descending" prefers higher]
util.set_search_sort_dir("descending")
# Set the search filter [all, loopless, disjoint, chain] and search direction [up, down].
# util.set_search_dir("up")
util.set_search_filter(filter_)

# Set the action [fit, search].  Skip this to set it from the data file.
util.set_action(Action.SBSEARCH)

# Set the model attribute for sorting the report, if it is different from the attribute used during search.
# Generally this isn't needed.
util.set_report_sort_name("information")

# Set the model attribute on which sorting is done is done.  This controls the selection
# of "best models" during search. It can also control reporting (see set_report_sort_name, below).
util.set_report_sort_name("information")

# util.set_ddf_method(0)

# Set report names, from the list above. If omitted, the list is set based on whether the ref model
# is top or bottom.  List is separated by commas, and provided as a single text string.
# For ref=top, this is a good list:
# util.set_report_variables("Level$I, h, ddf, lr, alpha, information, pct_correct_data, aic, bic")
# util.set_no_ipf(1)
# For ref=bottom, use something like this:
# util.set_report_variables("Level$i, h, ddf, lr, alpha, information, cond_pct_dh, aic, bic, incr_alpha, prog_id")
util.set_report_variables(
    "level$I, h, ddf, lr, alpha, information, aic, bic, incr_alpha, prog_id, pct_correct_data"
)

# Perform the search or fit. Pass 1 as argument to print options, 0 not to.
t2 = time.time()
util.do_action(1)
t3 = time.time()

print(f"start:  {(t2 - t1):8f}")
print(f"search: {(t3 - t2):8f}")
