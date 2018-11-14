# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import os, cgi, sys, occam, time, string, pickle, zipfile, datetime, tempfile, cgitb, urllib2, platform, traceback


def getUniqueFilename(file_name):
    dirname, filename = os.path.split(file_name)
    prefix, suffix = os.path.splitext(filename)
    prefix = '_'.join(prefix.split())
    fd, filename = tempfile.mkstemp(suffix, prefix+"__", dirname)
    os.chmod(filename, 0660)
    return filename


