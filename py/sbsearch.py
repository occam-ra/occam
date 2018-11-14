#! python
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

#import pdb
import os, sys
#sys.path.append("/www")
import occam
import time

import resource
resource.setrlimit(resource.RLIMIT_CORE, [360000, 360000])

from ocutils import ocUtils


# This section of the script allows you to specify the most frequently changed options from the command line.
# The width, levels and filter are determined here, to be used by the rest of the script below.
if len(sys.argv) < 2:
	print 'No data file specified.'
	print 'Usage: %s datafile [width levels] ["all"|"loopless"|"disjoint"|"chain"]' % sys.argv[0]
	sys.exit()

if len(sys.argv) >= 4:
	swidth = sys.argv[2]
	slevels = sys.argv[3]
else:
	swidth = 3;
	slevels = 7;

if len(sys.argv) >= 5:
	filter = sys.argv[4]
else:
	filter = "loopless"


util = ocUtils("SB")			# create a variable-based manager
t1 = time.time()
util.initFromCommandLine(sys.argv[0:2])	# initialize with the data file

#------------- Main script ---------------
# This script sets various options on a ocUtils object, and then runs the desired action.
# ocUtils is a convenience wrapper around the basic occam3 objects, and it sets appropriate
# defaults if you don't set every option.

# For settings which require model attribute names, the allowed values include:
# h, t, df, ddf, loops [1=loops, 0=no loops]
# information, unexplained, ipf_iterations, lr, alpha, beta, level, aic, bic
# cond_h, cond_dh, cond_pct_dh, cond_df, cond_ddf, p2, p2_alpha, p2_beta
# (Note that the Pearson statistics aren't computed by default because they are expensive.)
# To force a particular attribute to be printed as an integer, append "$I" to the name (e.g., Level$I)

# Set separator between report fields.  [1=tab, 2=comma, 3=space fill, 4=HTML]
util.setReportSeparator(3)

# Set the sorting direction for reporting.
util.setSortDir("descending")

# Set the search width & number of levels.
util.setSearchWidth(swidth)
util.setSearchLevels(slevels)

util.setUseInverseNotation(0)

# Set the start model for search [top, bottom, default, a specific model].
# Skip this to use the model set in the data file.
util.setStartModel("bottom")
#util.setStartModel("IV:A38Z")

# Set the ref model [top, bottom, default, a specific model].
util.setRefModel("bottom")

# Set the sorting direction for the search. ["ascending" prefers lower values, "descending" prefers higher]
util.setSearchSortDir("descending")
# Set the search filter [all, loopless, disjoint, chain] and search direction [up, down].
util.setSearchDir("up")
util.setSearchFilter(filter)

# Set the action [fit, search].  Skip this to set it from the data file.
util.setAction("SBsearch")

# Set the model attribute for sorting the report, if it is different from the attribute used during search.
# Generally this isn't needed.
util.setReportSortName("information")

# Set the model attribute on which sorting is done is done.  This controls the selection
# of "best models" during search. It can also control reporting (see setReportSortName, below).
util.setSortName("information")

#######util.setDDFMethod(0)

# Set report names, from the list above. If omitted, the list is set based on whether the ref model
# is top or bottom.  List is separated by commas, and provided as a single text string.
# For ref=top, this is a good list:
#util.setReportVariables("Level$I, h, ddf, lr, alpha, information, pct_correct_data, aic, bic")
#util.setNoIPF(1)
# For ref=bottom, use something like this:
#util.setReportVariables("Level$i, h, ddf, lr, alpha, information, cond_pct_dh, aic, bic, incr_alpha, prog_id")
util.setReportVariables("level$I, h, ddf, lr, alpha, information, aic, bic, incr_alpha, prog_id, pct_correct_data")

# Perform the search or fit. Pass 1 as argument to print options, 0 not to.
t2 = time.time()
util.doAction(1)
t3 = time.time()

print "start:  %8f" % (t2 - t1)
print "search: %8f" % (t3 - t2)





