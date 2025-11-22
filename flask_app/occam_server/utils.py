#!/usr/bin/env python3
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

"""
Utility functions for the OCCAM Flask web application
"""

import os
import tempfile
import zipfile
import datetime
from pathlib import Path


def get_unique_filename(file_path):
    """
    Generate a unique filename using tempfile to avoid collisions
    Similar to common.py getUniqueFilename
    """
    file_path = Path(file_path)
    dirname = file_path.parent
    prefix = file_path.stem.replace(' ', '_')
    suffix = file_path.suffix

    fd, filename = tempfile.mkstemp(suffix=suffix, prefix=f"{prefix}__", dir=dirname)
    os.close(fd)
    os.chmod(filename, 0o660)
    return filename


def get_timestamped_filename(file_path):
    """
    Generate a timestamped filename
    Similar to weboccam.py getTimestampedFilename
    """
    file_path = Path(file_path)
    dirname = file_path.parent
    prefix = file_path.stem.replace(' ', '_')
    suffix = file_path.suffix

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    filename = dirname / f"{prefix}_{timestamp}{suffix}"
    return str(filename)


def unzip_data_file(datafile):
    """
    If the file is a zip, extract it and return the extracted filename
    Similar to weboccam.py unzipDataFile
    """
    datafile = Path(datafile)

    if datafile.suffix != '.zip':
        return str(datafile)

    oldfile = datafile
    try:
        with zipfile.ZipFile(datafile, 'r') as zipdata:
            # Ignore directories and files in subdirectories
            ilist = [item for item in zipdata.infolist()
                    if '/' not in item.filename]

            if len(ilist) != 1:
                raise ValueError(
                    f"Zip file must contain exactly one data file, found {len(ilist)}"
                )

            # Extract the file
            extracted_name = ilist[0].filename
            datafile_new = get_timestamped_filename(
                datafile.parent / extracted_name
            )

            with open(datafile_new, 'w') as outf:
                outf.write(zipdata.read(ilist[0].filename).decode('utf-8'))

            os.remove(oldfile)
            return datafile_new

    except zipfile.BadZipFile:
        raise ValueError("Invalid zip file")
    except Exception as e:
        raise ValueError(f"Error extracting zip file: {str(e)}")


def prepare_cached_data(form_data, data_dir):
    """
    Prepare data file from cached components
    Similar to weboccam.py prepareCachedData
    """
    # Get form fields
    decls_file = form_data.get('decls')
    decls_filename = form_data.get('declsfilename', '')
    data_file = form_data.get('data')
    data_filename = form_data.get('datafilename', '')
    test_file = form_data.get('test')
    test_filename = form_data.get('testfilename', '')
    data_refr = form_data.get('refr', '')
    test_refr = form_data.get('testrefr', '')

    # Validate
    if not decls_filename:
        raise ValueError("No variable declarations file submitted")

    # Check exactly one of datafile or refr
    if (not data_filename and not data_refr) or (data_filename and data_refr):
        raise ValueError(
            "Exactly one of 'Data File' and 'Cached Data Name' must be filled out"
        )

    # Check at most one of testfile or testrefr
    if test_filename and test_refr:
        raise ValueError(
            "At most one of 'Test File' and 'Cached Test Name' must be filled out"
        )

    def unpack_to_string(filename, data):
        """Extract and read a data component"""
        rn = unzip_data_file(
            get_timestamped_filename(data_dir / filename)
        )
        with open(rn) as f:
            content = f.read()
        return content, rn

    # Process declarations
    decls, decls_rn = unpack_to_string(decls_filename, decls_file)

    # Process data
    if data_filename:
        data, data_refr_name = unpack_to_string(data_filename, data_file)
    else:
        # Use cached data
        drn = data_dir / data_refr
        if not drn.exists():
            raise ValueError(
                f"Cached data '{data_refr}' does not exist"
            )
        with open(drn) as f:
            data = f.read()
        data_refr_name = str(drn)

    # Process test data
    test = ""
    test_refr_name = ""
    if test_filename:
        test, test_refr_name = unpack_to_string(test_filename, test_file)
    elif test_refr:
        trn = data_dir / test_refr
        if not trn.exists():
            raise ValueError(
                f"Cached test data '{test_refr}' does not exist"
            )
        with open(trn) as f:
            test = f.read()
        test_refr_name = str(trn)

    # Combine into final data file
    final_data = f"{decls}\n{data}\n{test}\n"

    data_refr_tag = Path(data_refr_name).name
    test_refr_tag = Path(test_refr_name).name if test_refr_name else ""

    final_filename = f"{decls_filename}.{data_refr_tag}.txt"
    final_path = data_dir / final_filename

    with open(final_path, 'w') as f:
        f.write(final_data)

    return str(final_path), data_refr_tag, test_refr_tag


def apply_if(predicate, func, val):
    """Apply function if predicate is true"""
    return func(val) if predicate else val


def get_data_filename(form_data, trim=False, key='datafilename'):
    """Get the original data filename from form"""
    filename = form_data.get(key, '')
    if not filename:
        return ''

    # Get just the filename, not the path
    filename = os.path.basename(filename)

    # Trim extension if requested
    if trim:
        filename = os.path.splitext(filename)[0]

    # Replace spaces with underscores
    filename = '_'.join(filename.split())

    return filename
