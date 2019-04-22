# coding=utf-8
# Copyright (C) Ottawa Python Author's Group
# Example of use:
# cgi = OpagCGI('template.html')
# rdict = {'email': 'msoulier@storm.ca'}
# print cgi.parse(rdict)

# (kwillett, 031303) make template a required arg to OPagCGI constructor;
# make replacement delimiters {} instead of %%; allow change to template
# so object is reusable; added out convenience method to print result

import os
import re

TRUE = 1
FALSE = 0

# The replacement dictionary for parsing the template.
replacement_dict = {}


class Replacer:
    """This class is a utility class used to provide a bound method to the
    re.sub() function."""

    def __init__(self, dict_):
        """The constructor. It's only duty is to populate itself with the
        replacement dictionary passed."""
        self.dict = dict_

    def replace(self, matchobj):
        """The replacement method. This is passed a match object by re.sub(),
        which it uses to index the replacement dictionary and find the
        replacement string."""
        match = matchobj.group(1)
        matchobj = re.search('(.*)=(.*)', match)
        if matchobj:
            key = matchobj.group(1)
            qual = matchobj.group(2)
        else:
            key = match
            qual = ''
        if key in self.dict:
            if qual == 'checked':
                return 'checked'
            elif qual == self.dict[key]:
                return 'checked'
            else:
                return self.dict[key]
        else:
            return ''


class OpagCGI:
    """This class represents a running instance of a CGI on the OPAG website.
    It provides methods to give output from a CGI to a user's browser while
    maintaining the site's look and feel. It does this via template parsing of
    a standard template, permitting parsing of other templates as well."""

    def __init__(self, template=''):
        """OpagCGI(template) -> OpagCGI object
        The class constructor, taking the path to the template to use
        """
        if template:
            self.set_template(template)

    def set_template(self, template):
        self.template = template
        self.template_file = None
        if not os.path.exists(self.template):
            raise OpagMissingPrecondition("%s does not exist" % self.template)

    def parse(self, dict_, header=FALSE):
        """parse(dict) -> string
        This method parses the open file object passed, replacing any keys
        found using the replacement dictionary passed."""
        if not isinstance(dict_, dict):
            raise TypeError("Second argument must be a dictionary")
        if not self.template:
            raise OpagMissingPrecondition("template path is not set")
        # Open the file if its not already open. If it is, seek to the
        # beginning of the file.
        self.template_file = open(self.template, "r")
        # Instantiate a new bound method to do the replacement.
        replacer = Replacer(dict_).replace
        # Read in the entire template into memory. I guess we'd better keep
        # the templates a reasonable size if we're going to keep doing this.
        buffer_ = self.template_file.read()
        replaced = ""
        if header:
            replaced = "Content-Type: text/html\n\n"
        replaced = replaced + re.sub("{(.+)}", replacer, buffer_)
        self.template_file.close()
        return replaced

    def out(self, dict_, header=FALSE):
        print self.parse(dict_, header)


class OpagRuntimeError(RuntimeError):
    """The purpose of this class is to act as the base class for all runtime
    errors in OPAG CGI code. More specific Exceptions should subclass this if
    they happen at runtime. We might want to get more specific than this in
    the future, and introduce subclasses for IO errors, type errors and such,
    but this will do for now."""


class OpagMissingPrecondition(OpagRuntimeError):
    """The purpose of this class is to represent all problems with missing
    preconditions in OPAG code, such as a file that is supposed to exist, but
    does not."""
