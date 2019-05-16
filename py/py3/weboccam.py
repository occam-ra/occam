#! /usr/bin/env python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.
import cgi
import cgitb
import datetime
import os
import pickle
import sys
import time
import traceback
import zipfile

sys.path.insert(0, os.path.abspath("../occampy3"))
sys.path.insert(0, os.path.abspath("../occampy3/wrappers"))

import distanceFunctions
import ocGraph
from common import *
from jobcontrol import JobControl
from ocutils import OCUtils, Action
from OpagCGI import OpagCGI
from wrappers.report import ReportSortName, SortDirection

cgitb.enable(display=1)
VERSION = "3.4.0"
stdout_save = None

# TODO: check that the 'datadir' directory exists.
# This requires a manual installation step.
# If it does not exist with correct permissions, OCCAM will not run.
datadir = "data"
global_ocInstance = None
csvname = ""


def get_data_file_name(form_fields, trim=False, key='datafilename'):
    """
    Get the original name of the data file.
    * form_fields:   the form data from the user
    * trim:         trim the extension from the filename.
    """
    file_name = os.path.split(form_fields[key])[1]
    return '_'.join(os.path.splitext(file_name)[0] if trim else file_name)


def use_gfx(form_fields):
    return (
        "onlyGfx" in form_fields
        or "gfx" in form_fields
        or "gephi" in form_fields
    )


def print_headers(form_fields, text_format):
    if text_format:
        global csvname
        origcsvname = f"{get_data_file_name(form_fields, True)}.csv"
        csvname = get_unique_filename(f"data/{origcsvname}")
        if use_gfx(form_fields):
            # REDIRECT OUTPUT FOR NOW (it will be printed in output_zipfile())
            print("Content-type: application/octet-stream")
            print(
                f"Content-disposition: attachment; filename={get_data_file_name(form_fields, True)}.zip\n"
            )
            sys.stdout.flush()

            global stdout_save
            stdout_save = os.dup(1)
            csv = os.open(csvname, os.O_WRONLY)
            os.dup2(csv, 1)
            os.close(csv)

        else:
            print("Content-type: application/octet-stream")
            print(f"Content-disposition: attachment; filename={origcsvname}")

    else:
        print("Content-type: text/html")
    print()


def print_top(template, text_format):
    args = {'version': VERSION, 'date': datetime.datetime.now().strftime("%c")}
    file = f"header.{'txt' if text_format else 'html'}"
    template.out(args, file)


def print_time(text_format):
    now = time.time()
    elapsed_t = now - startt
    if elapsed_t > 0:
        if text_format:
            print(f"Run time: {elapsed_t} seconds\n")
        else:
            print(f"<br>Run time: {elapsed_t} seconds</br>")


def attempt_parse_int(string, default, msg, verbose):
    # for now: the fields aren't even displayed...
    verbose = False

    try:
        return int(string)

    except (ValueError, TypeError):
        if verbose:
            print(
                (
                    f'WARNING: expected {msg} to be an integer value, but got: "{string}"; using the default value, "{default}"\n'
                )
            )
            if not text_format:
                print("<br>")

        return default


def graph_width():
    return attempt_parse_int(
        form_fields.get("graph_width"),
        640,
        "hypergraph image width",
        "gfx" in form_fields,
    )


def graph_height():
    return attempt_parse_int(
        form_fields.get("graph_height"),
        480,
        "hypergraph image height",
        "gfx" in form_fields,
    )


def graph_font_size():
    return attempt_parse_int(
        form_fields.get("graph_font_size"),
        12,
        "hypergraph font size",
        "gfx" in form_fields,
    )


def graph_node_size():
    return attempt_parse_int(
        form_fields.get("graph_node_size"),
        24,
        "hypergraph node size",
        "gfx" in form_fields,
    )


# Take the captured standard output,
# and the generated graphs, and roll them into a ZIP file.
def output_to_zip(oc):
    global stdout_save
    global csvname

    # Make an empty zip file
    zipname = f"data/{get_data_file_name(form_fields, True)}.zip"
    z = zipfile.ZipFile(zipname, "w")

    sys.stdout.flush()
    # Write out each graph to a PDF; include a brief note in the CSV.
    for modelname, graph in list(oc.graphs.items()):
        modelname = modelname.replace(":", "_")

        if "gfx" in form_fields:
            filename = f"{modelname}.pdf"
            print(f"Writing graph to {filename}")
            graph_file = ocGraph.print_pdf(
                modelname,
                graph,
                form_fields["layout"],
                graph_width(),
                graph_height(),
                graph_font_size(),
                graph_node_size(),
            )
            z.write(graph_file, filename)
            sys.stdout.flush()

        if "gephi" in form_fields:
            nodename = f"{modelname}.nodes_table.csv"
            print(f"Writing Gephi Node table file to {nodename}")
            nodetext = ocGraph.gephi_nodes(graph)
            nodefile = get_unique_filename(f"data/{nodename}")
            with open(nodefile, "w") as nf:
                nf.write(nodetext)
            z.write(nodefile, nodename)

            edgename = f"{modelname}.edges_table.csv"
            print(f"Writing Gephi Edges table file to {edgename}")
            edgetext = ocGraph.gephi_edges(graph)
            edgefile = get_unique_filename(f"data/{edgename}")
            with open(edgefile, "w") as ef:
                ef.write(edgetext)
            z.write(edgefile, edgename)
            sys.stdout.flush()

    # Restore the STDOUT handle
    sys.stdout = os.fdopen(stdout_save, 'w')

    # Write the CSV to the ZIP
    z.write(csvname, f"{get_data_file_name(form_fields, True)}.csv")
    z.close()

    # print out the zipfile
    with open(zipname) as f:
        contents = f.read()
    print(contents)
    sys.stdout.flush()


#
# ---- print_bottom ---- Print bottom HTML part
#
def print_bottom():
    args = {}
    template.out(args, 'footer.html')


#
# ---- print_form ---- Print the data input form
#
def print_form(form_fields):
    template = OpagCGI()
    action = form_fields.get("action")

    if "formatText" in form_fields:
        form_fields['formatText'] = "checked"
    template.out(form_fields, 'switchform.html')

    if action in ["fit", "search", "SBsearch", "SBfit"]:
        template.out(form_fields, "formheader.html")

        cached = form_fields.get("cached")

        file = f"{'cached_' if cached == 'true' else ''}data.template.html"
        template.out(form_fields, file)
        template.out(form_fields, f"{action}.template.html")
        template.out(form_fields, "output.template.html")
        template.out(form_fields, f"{action}.footer.html")
    elif action in ["compare", "log", "fitbatch"]:
        template.out(form_fields, f"{action}form.html")

    if action == "jobcontrol":
        JobControl().show_jobs(form_fields)


#
# ---- action_form ---- put up the input form
#
def action_form(form, error_text):
    if error_text:
        print(f"<H2>Error: {error_text}</H2><BR>")
    print_form(form)


#
# ---- get_data_file ---- get the posted data and store to temp file
#
def get_data_file_alloc(form_fields, key='datafilename'):
    if get_data_file_name(form_fields, key=key) == "":
        print("ERROR: No data file specified.")
        sys.exit()
    datafile = get_unique_filename(
        os.path.join(datadir, get_data_file_name(form_fields))
    )
    try:
        with open(datafile, "w", 0o660) as f:
            print(form_fields["data"], file=f)
    except Exception:
        if get_data_file_name(form_fields) == "":
            print("ERROR: No data file specified.")
        else:
            print(f"ERROR: Problems reading data file {datafile}.")
        sys.exit()
    return datafile


def get_data_file_alloc_by_name(fn, data):
    if fn == "":
        print("ERROR: No data file specified.")
        sys.exit()
    datafile = get_timestamped_filename(os.path.join(datadir, fn))
    try:
        with open(datafile, "w", 0o660) as f:
            f.write(data)
    except Exception:
        print(f"ERROR: Problems reading data file {datafile}.")
        sys.exit()
    return datafile


def get_data_file(form_fields):
    if form_fields.get("cached") != "true":
        return unzip_data_file(get_data_file_alloc(form_fields))
    else:
        return prepare_cached_data(form_fields)


def prepare_cached_data(form_fields):
    # Get relevant data from the form
    decls_file_name = form_fields.get("declsfilename")
    decls_file = form_fields.get("decls")
    data_file_name = form_fields.get("datafilename")
    data_file = form_fields.get("data")
    test_file_name = form_fields.get("testfilename")
    test_file = form_fields.get("test")
    data_refr_name = form_fields.get("refr")
    test_refr_name = form_fields.get("testrefr")

    # Check that a vars file was submitted
    if decls_file_name == "":
        print("ERROR: No variable declarations file submitted.")
        sys.exit(1)

    # Check that exactly 1 of datafile, refr were chosen
    if (data_file_name == "" and data_refr_name == "") or (
        data_file_name != "" and data_refr_name != ""
    ):
        print(
            "NOTE: Exactly 1 of 'Data File' and 'Cached Data Name' must be filled out."
        )
        sys.exit(1)

    # Check that at most 1 of testfile, testrefr were chosen
    if test_file_name != "" and test_refr_name != "":
        print(
            "ERROR: At most 1 of 'Test File' and 'Cached Test Name' must be filled out."
        )
        sys.exit(1)

    def unpack_to_string(fn, data):
        rn = unzip_data_file(get_data_file_alloc_by_name(fn, data))
        with open(rn) as f:
            data = f.read()
        return data, rn

    decls, decls_rn = unpack_to_string(decls_file_name, decls_file)

    if data_file_name == "":  # Search for the Cached Data Name and combine.
        drn = os.path.join(datadir, data_refr_name)
        try:
            with open(drn) as f:
                data = f.read()
        except FileNotFoundError:
            print(
                "ERROR: Data file corresponding to Cached Data Name, "
                f"'{data_refr_name}', does not exist"
            )
            sys.exit(1)
    else:
        data, data_refr_name = unpack_to_string(data_file_name, data_file)

    test = ""
    if test_file_name == "" and test_refr_name != "":
        trn = os.path.join(datadir, test_refr_name)
        print(trn)
        try:
            with open(trn) as f:
                test = f.read()
        except FileNotFoundError:
            print(
                f"ERROR: Test file corresponding to Cached Test Name, '{test_refr_name}', does not exist"
            )
            sys.exit(1)
    elif test_file_name != "":
        test, test_refr_name = unpack_to_string(test_file_name, test_file)

    data_refr_tag = os.path.split(data_refr_name)[1]
    test_refr_tag = os.path.split(test_refr_name)[1]

    final_data_file = f"{decls}\n{data}\n{test}"

    final_data_file_name = f"{decls_file_name}.{data_refr_tag}.txt"
    final_data_file_name = os.path.join(datadir, final_data_file_name)

    with open(final_data_file_name, "w") as f:
        f.write(final_data_file)

    form_fields['datafilename'] = final_data_file_name

    # Print out the (fresh or reference) cached data name to the report.
    r = ""
    if not text_format:
        r += "<TABLE><TR><TD><B>"
    r += "Cached Data Name:"
    if text_format:
        r += "\t"
    else:
        r += "</B></TD><TD>"
    r += data_refr_tag
    if text_format:
        r += "\n"
    else:
        r += "</TD></TR><TR><TD><B>"
    if test_refr_name != "":
        r += "Cached Test Name: "
    if text_format:
        r += "\t"
    else:
        r += "</B></TD><TD>"
    r += test_refr_tag
    if not text_format:
        r += "</TD></TR></TABLE>"
    print(r)
    # Return the new datafile.
    return final_data_file_name


def unzip_data_file(datafile):
    # If it appears to be a zipfile, unzip it
    if os.path.splitext(datafile)[1] == ".zip":
        oldfile = datafile
        zipdata = zipfile.ZipFile(datafile)
        # ignore any directories, or files in them, such as those OSX likes to make
        ilist = [
            item
            for item in zipdata.infolist()
            if item.filename.find("/") == -1
        ]
        # make sure there is only one file left
        if len(ilist) != 1:
            print(
                f"ERROR: Zip file can only contain one data file. (It appears to contain {len(ilist)}.)"
            )
            sys.exit()
        # try to extract the file
        try:
            datafile = get_timestamped_filename(
                os.path.join(datadir, ilist[0].filename)
            )
            with open(datafile, "w") as f:
                print(zipdata.read(ilist[0].filename), file=f)
            os.remove(oldfile)
        except Exception:
            print("ERROR: Extracting zip file failed.")
            sys.exit()
    return datafile


def process_fit(fn, model, negative_dv_for_confusion, oc, only_gfx):
    global datafile, text_format, print_options

    if text_format:
        oc.set_report_separator(OCUtils.COMMA_SEP)
    else:
        print('<div class="data">')
        oc.set_report_separator(OCUtils.HTML_FORMAT)

    if model != "":
        oc.set_fit_model(model)

    oc.set_fit_classifier_target(negative_dv_for_confusion)
    oc.set_action("fit")
    oc.do_action(print_options, only_gfx)

    if not text_format:
        print("</span>")


#
# ---- process_sb_fit ---- Do state based fit operation
#
def process_sb_fit(fn, model, negative_dv_for_confusion, oc, only_gfx):
    global datafile, text_format, print_options
    if text_format:
        oc.set_report_separator(OCUtils.COMMA_SEP)
    else:
        print('<div class="data">')
        oc.set_report_separator(OCUtils.HTML_FORMAT)

    if model != "":
        oc.set_fit_model(model)

    oc.set_fit_classifier_target(negative_dv_for_confusion)
    oc.set_action("SBfit")
    oc.do_action(print_options, only_gfx)


def maybe_skip_residuals(form_fields, oc):
    skip_residuals_flag = form_fields.get("skipresiduals")
    if skip_residuals_flag:
        oc.set_skip_trained_model_table(1)
    else:
        oc.set_skip_trained_model_table(0)


def maybe_skip_ivis(form_fields, oc):
    skip_residuals_flag = form_fields.get("skipivitables")
    if skip_residuals_flag:
        oc.set_skipIVITables(1)
    else:
        oc.set_skipIVITables(0)


#
# ---- action_fit ---- Report on Fit
#
def handle_graph_options(oc, form_fields):
    if use_gfx(form_fields):
        lo = form_fields["layout"]
        oc.set_gfx(
            "gfx" in form_fields,
            layout=lo,
            gephi="gephi" in form_fields,
            hide_iv="hideIsolated" in form_fields,
            hide_dv="hideDV" in form_fields,
            full_var_names="fullVarNames" in form_fields,
            width=graph_width(),
            height=graph_height(),
            font_size=graph_font_size(),
            node_size=graph_node_size(),
        )


def action_fit(form_fields):
    global text_format

    fn = get_data_file(form_fields)
    oc = OCUtils("VB")
    global global_ocInstance
    global_ocInstance = oc
    if not text_format:
        print('<pre>')
    oc.init_from_command_line(["", fn])
    if not text_format:
        print('</pre>')
    oc.set_data_file(form_fields["datafilename"])
    handle_graph_options(oc, form_fields)

    if "calcExpectedDV" in form_fields:
        oc.set_calc_expected_dv(1)

    oc.set_ddf_method(1)
    skip_nominal_flag = form_fields.get("skipnominal")
    if skip_nominal_flag:
        oc.set_skip_nominal(1)
    if "defaultmodel" in form_fields:
        oc.set_default_fit_model(form_fields["defaultmodel"])
    # function_flag = form_fields.get("functionvalues", "")
    # if function_flag:
    # oc.set_values_are_functions(1)

    target = (
        form_fields["negativeDVforConfusion"]
        if "negativeDVforConfusion" in form_fields
        else ""
    )

    maybe_skip_residuals(form_fields, oc)
    maybe_skip_ivis(form_fields, oc)

    if "data" not in form_fields or "model" not in form_fields:
        action_none(form_fields, "Missing form fields")
        return
    only_gfx = "onlyGfx" in form_fields
    process_fit(fn, form_fields["model"], target, oc, only_gfx)
    os.remove(fn)


#
# ---- action_fit_batch ---- Report on several Fit models
#
def action_fit_batch(form_fields):
    global batch_email
    models = form_fields["model"].split()
    form_fields["model"] = models[0]
    action_fit(form_fields)
    if len(models) > 1:
        form_fields["model"] = "\n".join(models[1:])
        form_fields["batch_output"] = batch_email
        start_batch(form_fields)


#
# ---- action_sb_fit ---- Report on SB Fit model
#
def action_sb_fit(form_fields):
    global text_format

    fn = get_data_file(form_fields)
    oc = OCUtils("SB")
    global global_ocInstance
    global_ocInstance = oc
    if not text_format:
        print('<pre>')
    oc.init_from_command_line(["", fn])
    if not text_format:
        print('</pre>')
    oc.set_data_file(form_fields["datafilename"])
    handle_graph_options(oc, form_fields)
    # function_flag = form_fields.get("functionvalues")
    # if function_flag:
    #     oc.set_values_are_functions(1)
    if "data" not in form_fields or "model" not in form_fields:
        action_none(form_fields, "Missing form fields")
        os.remove(fn)
        return
    skip_nominal_flag = form_fields.get("skipnominal")
    if skip_nominal_flag:
        oc.set_skip_nominal(1)

    maybe_skip_residuals(form_fields, oc)
    maybe_skip_ivis(form_fields, oc)

    target = (
        form_fields["negativeDVforConfusion"]
        if "negativeDVforConfusion" in form_fields
        else ""
    )

    only_gfx = "onlyGfx" in form_fields
    process_sb_fit(fn, form_fields["model"], target, oc, only_gfx)
    os.remove(fn)


#
# ---- process_search ---- Do search operation
#
def action_search(form_fields):
    global text_format
    fn = get_data_file(form_fields)
    man = "VB"
    oc = OCUtils(man)
    global global_ocInstance
    global_ocInstance = oc
    if not text_format:
        print('<pre>')
    oc.init_from_command_line(["", fn])
    if not text_format:
        print('</pre>')
    oc.set_data_file(form_fields["datafilename"])
    # unused error? this should get caught by get_data_file() above
    if "data" not in form_fields:
        action_form(form_fields, "Missing form fields")
        print("missing data")
        return
    # text_format = form_fields.get("format")
    if text_format:
        oc.set_report_separator(OCUtils.COMMA_SEP)
    else:
        oc.set_report_separator(OCUtils.HTML_FORMAT)

    oc.set_sort_dir(form_fields.get("sortdir", ""))
    levels = form_fields.get("searchlevels")
    if levels and levels > 0:
        oc.set_search_levels(levels)
    width = form_fields.get("searchwidth")
    if width and width > 0:
        oc.set_search_width(width)
    report_sort = form_fields.get("sortreportby", "")
    search_sort = form_fields.get("sortby", "")
    inverse_flag = form_fields.get("inversenotation")
    if inverse_flag:
        oc.set_use_inverse_notation(1)
    skip_nominal_flag = form_fields.get("skipnominal")
    if skip_nominal_flag:
        oc.set_skip_nominal(1)
    function_flag = form_fields.get("functionvalues")
    if function_flag:
        oc.set_values_are_functions(1)
    oc.set_start_model(form_fields.get("model", "default"))
    ref_model = form_fields.get("refmodel", "default")
    # specific_ref_model = ""
    # if ref_model == "specific" and "specificrefmodel" in form_fields:
    #    ref_model = form_fields["specificrefmodel"]
    # specific_ref_model = ref_model
    if ref_model == "starting":
        ref_model = oc.start_model
    oc.set_ref_model(ref_model)
    oc.search_dir = form_fields.get("searchdir", "default")
    oc.set_search_sort_dir(form_fields.get("searchsortdir", ""))
    oc.set_search_filter(form_fields.get("searchtype", "all"))
    oc.set_alpha_threshold(form_fields.get("alpha-threshold", "0.05"))
    oc.set_action("search")

    # INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
    # This code handles the backpropagation-based evaluation,
    # but it is not currently used (and the HTML forms do not define "evalmode"
    # so it will crash!!)
    disabled_bp_code = """
    if form_fields["evalmode"] == "bp":
        reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
        oc.set_noIPF(true)
        if report_sort == ReportSortName.INFORMATION: report_sort = ReportSortName.BP_INFORMATION
        elif report_sort == ReportSortName.ALPHA: report_sort = ReportSortName.BP_ALPHA
        if search_sort == "information": search_sort = "bp_information"
        elif search_sort == "alpha": search_sort = "bp_alpha"
        if oc.is_directed:
            reportvars += ", bp_cond_pct_dh"
        reportvars += ", bp_aic, bp_bic"
    """
    reportvars = "Level$I"
    if form_fields.get("show_h"):
        reportvars += ", h"
    reportvars += ", ddf"
    if form_fields.get("show_dlr"):
        reportvars += ", lr"
    if (
        form_fields.get("show_alpha")
        or search_sort == ReportSortName.ALPHA
        or report_sort == ReportSortName.ALPHA
    ):
        reportvars += ", alpha"
    reportvars += ", information"
    if oc.is_directed and form_fields.get("show_pct_dh"):
        reportvars += ", cond_pct_dh"
    if (
        form_fields.get("show_aic")
        or search_sort == ReportSortName.AIC
        or report_sort == ReportSortName.AIC
    ):
        reportvars += ", aic"
    if (
        form_fields.get("show_bic")
        or search_sort == ReportSortName.BIC
        or report_sort == ReportSortName.BIC
    ):
        reportvars += ", bic"

    if form_fields.get("show_incr_a"):
        reportvars += ", incr_alpha, prog_id"

    # INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
    # This code handles the backpropagation-based evaluation,
    # but it is not currently used (and the HTML forms do not define "evalmode"
    # so it will crash!!)
    disabled_bp_code = """
        if form_fields.get("show_bp") and form_fields["evalmode"] != "bp":
            reportvars += ", bp_t"
        """

    if oc.is_directed and (
        form_fields.get("show_pct")
        or form_fields.get("show_pct_cover")
        or search_sort == ReportSortName.PCT_CORRECT_DATA
        or report_sort == ReportSortName.PCT_CORRECT_DATA
    ):
        reportvars += ", pct_correct_data"
        if form_fields.get("show_pct_cover"):
            reportvars += ", pct_coverage"
        if oc.has_test_data():
            reportvars += ", pct_correct_test"
            if form_fields.get("show_pct_miss"):
                reportvars += ", pct_missed_test"
    oc.set_report_sort_name(report_sort)
    oc.sort_name = search_sort
    oc.set_report_variables(reportvars)
    if text_format:
        oc.do_action(print_options)
    else:
        print("<hr><p>")
        print('<div class="data">')
        oc.do_action(print_options)
        print("</div>")
    os.remove(fn)


def action_batch_compare(form_fields):
    # Get data from the form

    # Get Occam search parameters
    search_fields = [
        "type",
        "direction",
        "levels",
        "width",
        "sort by",
        "selection function",
    ]
    search = {key: form_fields.get(key) for key in search_fields}

    # Get Occam report parameters
    report_1 = []
    report_2 = []
    report_fields_1 = [
        "DF(data)",
        "H(data)",
        "dBIC(model)",
        "dAIC(model)",
        "DF(model)",
        "H(model)",
    ]
    report_fields_2 = [
        "Absolute dist",
        "Information dist",
        "Kullback-Leibler dist",
        "Euclidean dist",
        "Maximum dist",
        "Hellinger dist",
    ]

    d = {
        "max(DF)": "DF(model)",
        "min(H)": "H(model)",
        "min(dAIC)": "dAIC(model)",
        "min(dBIC)": "dBIC(model)",
    }

    for r, rf in [(report_1, report_fields_1), (report_2, report_fields_2)]:
        for key in sorted(rf):
            if (
                form_fields.get(key) == "yes"
                or d[search["selection function"]] == key
            ):
                r.append(key)

    # Check if the datafile field has a file in it.
    fn = get_data_file_alloc(form_fields)

    # Validate the datafile as a zip file containing the proper named pairs.
    if not zipfile.is_zipfile(fn):
        print(f"ERROR: {fn} is not a zipped archive.")
        sys.exit()

    def make_pairs(zip_data):
        pairs = []
        sorted_data = sorted(zip_data, key=lambda s: s.filename)

        if len(sorted_data) == 0:
            print("ERROR: Empty zip archive.")
            sys.exit()

        if len(sorted_data) % 2 != 0:
            print(
                "ERROR: Expected an even number of datafiles inside the zip archive."
            )
            sys.exit()
        for ix in range(len(sorted_data) / 2):
            g = lambda i: os.path.splitext(sorted_data[i].filename)[0]
            a = g(2 * ix)
            b = g(2 * ix + 1)
            if not (a[:-1] == b[:-1]):
                print("ERROR: Expected matching paired data, but got<br></br>")
                print(
                    f"&emsp;&emsp;'{sorted_data[2 * ix].filename}',<br></br>"
                )
                print(
                    f"&emsp;&emsp;'{sorted_data[2 * ix + 1].filename}'.<br></br>"
                )
                print(
                    "For each pair in the zipfile, the 2 filenames must be the same"
                )
                print(
                    "except for exactly 1 character immediately before the extension which differs<br></br>"
                )
                print("&emsp;&emsp;(e.g. 'fileA.txt', 'fileB.txt').")
                sys.exit()
            pairs.append(
                (a[:-1], sorted_data[2 * ix], sorted_data[2 * ix + 1])
            )
        return pairs

    zip_data = zipfile.ZipFile(fn)
    pairs = make_pairs(
        [i for i in zip_data.infolist() if i.filename.find("/") == -1]
    )

    # Define the analysis.
    # Steps:
    # * Read out one pair at a time into the directory, and analyze it:
    #   * Search to find the best model for each file
    #   * Compare the two best models
    #   * Save a data row

    def extract(x):
        try:
            d = get_unique_filename(os.path.join(datadir, x.filename))
            with open(d, "w") as f:
                print(zip_data.read(x.filename), file=f)
            return d
        except Exception:
            print("ERROR: Extracting zip file failed.")
            sys.exit()

    # Figure out what statistics to include (and in what reporting order)
    def get_stat_headers():
        headers = []
        candidate = [
            "H(data)",
            "H(model)",
            "DF(data)",
            "DF(model)",
            "dAIC(model)",
            "dBIC(model)",
        ]
        for i in report_1 + report_2:
            if i in candidate:
                headers.append(f"{i[:-1]}(A))")
                headers.append(f"{i[:-1]}(B))")
            if i in report_fields_2:
                headers.append(f"{i}(model(A) : model(B))")
        return headers

    global text_format, print_options

    # Definitions used in the report
    def bracket(s, hl, hr, tl, tr):
        if text_format:
            return tl + s + tr
        else:
            return hl + s + hr

    tab_row = lambda s: bracket(s, "<tr>", "</tr>", "", "")
    tab_col = lambda s: bracket(s, "<td>", "</td>", " ", ",")
    tab_head = lambda s: bracket(s, "<th align=left>", "</th>", " ", ",")

    table_start = "<br><table border=0 cellpadding=0 cellspacing=0>"
    table_end = "</table>"

    def compute_best_model(filename):
        oc = OCUtils("VB")
        global global_ocInstance
        global_ocInstance = oc
        oc.init_from_command_line(["occam", filename])
        oc.set_data_file(filename)
        oc.set_action("search")

        # Hardcoded settings (for now):
        oc.set_sort_dir(SortDirection.DESCENDING)
        oc.set_search_sort_dir("descending")  # try to maximize dBIC or dAIC.
        oc.set_ref_model("bottom")  # Always uses bottom as reference.

        # Parameters from the web form
        oc.sort_name = search["sort by"]
        oc.set_search_levels(int(search["levels"]))
        oc.set_search_width(int(search["width"]))
        oc.set_search_filter(search["type"])

        [i, d] = search["direction"].split(" ")
        oc.search_dir = d
        oc.set_start_model(i)

        return oc.find_best_model()

    def select_best(stats):
        sel = search["selection function"]
        d = 0
        s = ""
        if sel == "min(H)":
            d = -1
            s = "H(model)"
        elif sel == "max(DF)":
            d = 1
            s = "DF(model)"
        elif sel == "min(dBIC)":
            d = -1
            s = "dBIC(model)"
        elif sel == "min(dAIC)":
            d = -1
            s = "dAIC(model)"
        return d, s

    def compute_binary_statistics(report_items, comp_order):
        stats = {
            k: distanceFunctions.compute_distance_metric(k, comp_order)
            for k in report_items
        }
        return stats

    def compute_model_stats(model_a, model_b):
        stats_1 = {k: [model_a[k], model_b[k]] for k in report_1}

        # Find the best model based on the single-model stats
        best_d, best_s = select_best(stats_1)
        a, b = stats_1[best_s]
        best = ""
        if best_d == -1:
            best = "A" if a <= b else "B"
        elif best_d == 1:
            best = "A" if a >= b else "B"
        comp_order = [model_a, model_b] if best == "A" else [model_b, model_a]
        stats_2 = compute_binary_statistics(report_2, comp_order)

        return best, stats_1, stats_2

    def run_analysis(pair_name, file_a, file_b):
        model_a = compute_best_model(file_a)
        model_b = compute_best_model(file_b)
        model_a["filename"] = f"{pair_name}A.txt"
        model_b["filename"] = f"{pair_name}B.txt"

        best, stats_1, stats_2 = compute_model_stats(model_a, model_b)
        return (
            [pair_name, model_a["name"], model_b["name"], best],
            stats_1,
            stats_2,
        )

    # Print out the report
    # * Print out options if requested
    # * Print out the file name
    # * Print out the header
    # * For each data row, pretty print it
    # * Print out the header again as a footer

    def pp_options():
        for (k, v) in list(search.items()):
            if v != '':
                print(tab_row(tab_col(f"{k}: ") + tab_col(v)))

    def pp_column_list():
        print(
            tab_row(
                tab_col("columns in report: ")
                + tab_col(", ".join(report_1 + report_2))
            )
        )

    def pp_analysis(row):
        return "".join(map(tab_col, row))

    def pp_stats(stats_1, stats_2):
        s = ""
        for (k, v) in sorted(stats_1.items()):
            for i in [0, 1]:
                if k[:2] == "DF":
                    s += tab_col(f"{v[i]:.0f}")
                else:
                    s += tab_col(f"{v[i]:.6g}")
        for (k, v) in sorted(stats_2.items()):
            s += tab_col(f"{v:.6g}")
        return s

    def pp_header():
        col_headers = [
            "pair name",
            "model(A)",
            "model(B)",
            search["selection function"],
        ] + get_stat_headers()
        return "".join(map(tab_head, col_headers))

    # Layout the document
    if not text_format:
        print("<hr><p>")
        print('<div class="data">')
    if not text_format:
        print(table_start)
    print(
        tab_row(
            tab_head("Input archive: ")
            + tab_col(get_data_file_name(form_fields))
        )
    )
    if print_options:
        print(tab_row(tab_head("Options:")))
        pp_options()
        pp_column_list()
    if not text_format:
        print(table_end)

    # Perform and print the analysis on each pair in the zip file.
    sys.stdout.write("Running searches")
    results = []
    for pair_name, A, B in pairs:
        file_a = extract(A)
        file_b = extract(B)
        l, s1, s2 = run_analysis(pair_name, file_a, file_b)
        results.append([l, s1, s2])
        os.remove(file_a)
        os.remove(file_b)
    print("\nSearches completed. ")

    if not text_format:
        print(table_start)
    print(tab_row(tab_head("Comparison Results:")))
    print(tab_row(pp_header()))

    for res in results:
        print(tab_row(pp_analysis(res[0]) + pp_stats(res[1], res[2])))

    # If there was more than one pair, print a footer
    if len(pairs) > 1:
        print(tab_row(pp_header()))
        if not text_format:
            print(table_end)
            print("</div>")

    # Remove the zip file
    os.remove(fn)


def action_sb_search(form_fields):
    global text_format
    fn = get_data_file(form_fields)
    man = "SB"
    oc = OCUtils(man)
    global global_ocInstance
    global_ocInstance = oc
    if not text_format:
        print('<pre>')
    oc.init_from_command_line(["", fn])
    if not text_format:
        print('</pre>')
    oc.set_data_file(form_fields["datafilename"])
    # unused error? this should get caught by get_data_file() above
    if "data" not in form_fields:
        action_form(form_fields, "Missing form fields")
        print("missing data")
        return
    # text_format = form_fields.get("format")
    if text_format:
        oc.set_report_separator(OCUtils.COMMA_SEP)
    else:
        oc.set_report_separator(OCUtils.HTML_FORMAT)
    oc.set_sort_dir(form_fields.get("sortdir", ""))
    levels = form_fields.get("searchlevels")
    if levels and levels > 0:
        oc.set_search_levels(levels)
    width = form_fields.get("searchwidth")
    if width and width > 0:
        oc.set_search_width(width)
    report_sort = form_fields.get("sortreportby", "")
    search_sort = form_fields.get("sortby", "")
    inverse_flag = form_fields.get("inversenotation")
    if inverse_flag:
        oc.set_use_inverse_notation(1)
    skip_nominal_flag = form_fields.get("skipnominal")
    if skip_nominal_flag:
        oc.set_skip_nominal(1)
    function_flag = form_fields.get("functionvalues")
    if function_flag:
        oc.set_values_are_functions(1)
    oc.set_start_model(form_fields.get("model", "default"))
    ref_model = form_fields.get("refmodel", "default")
    # specific_ref_model = ""
    if ref_model == "specific" and "specificrefmodel" in form_fields:
        ref_model = form_fields["specificrefmodel"]
        # specific_ref_model = ref_model
    elif ref_model == "starting":
        ref_model = oc.start_model
    oc.set_ref_model(ref_model)
    oc.search_dir = form_fields.get("searchdir", "default")
    oc.set_search_sort_dir(form_fields.get("searchsortdir", ""))
    oc.set_search_filter(form_fields.get("searchtype", "all"))
    oc.set_action("SBsearch")

    # INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
    # This code handles the backpropagation-based evaluation,
    # but it is not currently used (and the HTML forms do not define "evalmode"
    # so it will crash!!)
    disabled_bp_code = """
    if form_fields["evalmode"] == "bp":
        reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
        oc.set_noIPF(true)
        if report_sort == "information": report_sort = ReportSortName.BP_INFORMATION
        elif report_sort == ReportSortName.ALPHA: report_sort = ReportSortName.BP_ALPHA
        if search_sort == "information": search_sort = "bp_information"
        elif search_sort == "alpha": search_sort = "bp_alpha"
        if oc.is_directed:
            reportvars += ", bp_cond_pct_dh"
        reportvars += ", bp_aic, bp_bic"
    """
    reportvars = "Level$I"
    if form_fields.get("show_h"):
        reportvars += ", h"
    reportvars += ", ddf"
    if form_fields.get("show_dlr"):
        reportvars += ", lr"
    if (
        form_fields.get("show_alpha")
        or search_sort == ReportSortName.ALPHA
        or report_sort == ReportSortName.ALPHA
    ):
        reportvars += ", alpha"
    reportvars += ", information"
    if oc.is_directed and form_fields.get("show_pct_dh"):
        reportvars += ", cond_pct_dh"
    if (
        form_fields.get("show_aic")
        or search_sort == ReportSortName.AIC
        or report_sort == ReportSortName.AIC
    ):
        reportvars += ", aic"
    if (
        form_fields.get("show_bic")
        or search_sort == ReportSortName.BIC
        or report_sort == ReportSortName.BIC
    ):
        reportvars += ", bic"

    if form_fields.get("show_incr_a"):
        reportvars += ", incr_alpha, prog_id"

    # INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
    # This code handles the backpropagation-based evaluation,
    # but it is not currently used (and the HTML forms do not define "evalmode"
    # so it will crash!!)
    disabled_bp_code = """
        if form_fields.get("show_bp") and form_fields["evalmode"] != "bp":
            reportvars += ", bp_t"
        """

    if oc.is_directed and (
        form_fields.get("show_pct")
        or form_fields.get("show_pct_cover")
        or search_sort == ReportSortName.PCT_CORRECT_DATA
        or report_sort == ReportSortName.PCT_CORRECT_DATA
    ):
        reportvars += ", pct_correct_data"
        if form_fields.get("show_pct_cover"):
            reportvars += ", pct_coverage"
        if oc.has_test_data():
            reportvars += ", pct_correct_test"
            if form_fields.get("show_pct_miss"):
                reportvars += ", pct_missed_test"
    oc.set_report_sort_name(report_sort)
    oc.sort_name = search_sort
    oc.set_report_variables(reportvars)
    if text_format:
        oc.do_action(print_options)
    else:
        print("<hr><p>")
        print('<div class="data">')
        oc.do_action(print_options)
        print("</div>")
    os.remove(fn)


#
# ---- action_show_log ---- show job log given email
def action_show_log(form_fields):
    email = form_fields.get("email")
    if email:
        print_batch_log(email.lower())


# ---- action_error ---- print error on unknown action
#
def action_error():
    if text_format:
        print("Error: unknown action")
    else:
        print("<H1>Error: unknown action</H1>")


def action_none(*args, **kwargs):
    pass


# ---- get_form_fields ----
def get_form_fields(form):
    form_fields = {}
    keys = list(form.keys())
    for key in keys:
        if key in ['data', 'decls', 'test']:
            form_fields[key + 'filename'] = form[key].filename
            form_fields[key] = form[key].value
        else:
            form_fields[key] = form.getfirst(key)
    return form_fields


def get_timestamped_filename(file_name):
    dirname, filename = os.path.split(file_name)
    prefix, suffix = os.path.splitext(filename)
    prefix = '_'.join(prefix.split())
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    filename = os.path.join(dirname, f"{prefix}_{timestamp}{suffix}")
    return filename


#
# ---- start_batch ----
#
# Output all the form arguments to a file, and then run the
# script as a command line job
#
def start_batch(form_fields):
    if get_data_file_name(form_fields) == "":
        print("ERROR: No data file specified.")
        sys.exit()
    ctlfilename = os.path.join(
        datadir, get_data_file_name(form_fields, true) + '.ctl'
    )
    ctlfilename = get_unique_filename(ctlfilename)
    csvname = get_data_file_name(form_fields, True) + '.csv'
    datafilename = get_data_file_name(form_fields)
    toaddress = form_fields["batch_output"].lower()
    email_subject = form_fields["email_subject"]
    with open(ctlfilename, 'w', 0o660) as f:
        pickle.dump(form_fields, f)
    appname = os.path.dirname(sys.argv[0])
    if not appname:
        appname = "."
    appname = os.path.join(appname, "occambatch")

    print("Process ID:", os.getpid(), "<p>")

    cmd = f'nohup {appname} {sys.argv[0]} {ctlfilename} {toaddress} {csvname} {email_subject.encode("hex")}'
    os.system(cmd)

    print(
        f"<hr>Batch job started for data file '{datafilename}'.<br>Results will be sent to '{toaddress}'"
    )

    if len(email_subject) > 0:
        print(f" with email subject line including '{email_subject}'.")


#
# ---- get_web_controls ----
#
def get_web_controls():
    form_fields = get_form_fields(cgi.FieldStorage())
    return form_fields


#
# ---- get_batch_controls ----
#
def get_batch_controls():
    ctlfile = sys.argv[1]
    with open(ctlfile) as f:
        form_fields = pickle.load(f)
    os.remove(ctlfile)
    # set text mode
    form_fields["format"] = "text"
    return form_fields


#
# ---- print_batch_log ----
#
def print_batch_log(email):
    email = email.lower()
    print("<P>")
    # perhaps we should do some check that this directory exists?
    file_ = os.path.join("batchlogs", email.lower())
    try:
        with open(file_) as f:
            logcontents = f.readlines()
        log = '<BR>'.join(logcontents)
        print(log)
    except Exception:
        print(f"no log file found for {email}<br>")


def start_normal(form_fields):
    # if any subject line was supplied, print it
    if form_fields.get("emailSubject"):
        print(f"Subject line:,{form_fields['emailSubject']}")

    try:
        if form_fields["action"] == "fit":
            action_fit(form_fields)
        elif form_fields["action"] == "SBsearch":
            action_sb_search(form_fields)
        elif form_fields["action"] == "SBfit":
            action_sb_fit(form_fields)
        elif form_fields["action"] == "fitbatch":
            action_fit_batch(form_fields)
        elif (
            form_fields["action"] == "search"
            or form_fields["action"] == "advanced"
        ):
            action_search(form_fields)
        elif form_fields["action"] == "log":
            action_show_log(form_fields)
        elif form_fields["action"] == "compare":
            action_batch_compare(form_fields)
        elif form_fields["action"] == "jobcontrol":
            pass
        else:
            action_error()

        print_time(text_format)
    except Exception as e:
        if isinstance(e, KeyError) and str(e) == "'datafilename'":
            pass
        else:
            if not text_format:
                print("<br><hr>")
            print(f"FATAL ERROR: {str(e)}")
            if not text_format:
                print("<br>")
            print("This error was not expected by the programmer. ")
            print(
                "For help, please contact h.forrest.alexander@gmail.com, and include the output so far "
            )
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)
            print("(end error message).")


def finalize_gfx():
    global global_ocInstance
    if use_gfx(form_fields) and text_format:
        output_to_zip(global_ocInstance)
        sys.stdout.flush()


# ---- main script ----
#

template = OpagCGI()
datafile = ""
text_format = ""
print_options = ""
# thispage = os.getenv('SCRIPT_NAME', '')
startt = time.time()

# See if this is a batch run or a web server run
argc = len(sys.argv)
if argc > 1:
    form_fields = get_batch_controls()
    batch_email = form_fields["batch_output"]
    form_fields["batch_output"] = ""
else:
    form_fields = get_web_controls()

text_format = form_fields.get("format", "") != ""
if form_fields.get("batchOutput"):
    text_format = 0

print_headers(form_fields, text_format)

if "printoptions" in form_fields:
    print_options = "true"

print_top(template, text_format)

if form_fields.get("batchOutput"):
    text_format = 0

    r1 = form_fields.pop('gfx', None)
    r2 = form_fields.pop('gephi', None)
    t = (r1 is not None) or (r2 is not None)
    if t:
        print(
            "Note: Occam's email server interacts with graph output in a way that currently results in an error; graph functionality is temporarily disabled. The programmer is working on a fix...<br><hr>"
        )

sys.stdout.flush()

# print(f"{sys.executable}<br>{platform.python_version()}<br>"

# If this is not an output page, or reporting a batch job, then print the header form
if "data" not in form_fields and "email" not in form_fields:
    action_form(form_fields, None)

# If there is an action, and either data or an email address, proceed
if "action" in form_fields:

    # If this is running from web server, and batch mode requested, then start a background task
    if form_fields.get("batchOutput"):
        start_batch(form_fields)
    else:
        start_normal(form_fields)

finalize_gfx()

if not text_format:
    print_bottom()
    sys.stdout.flush()
    sys.stdout.close()
