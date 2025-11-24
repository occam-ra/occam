#!/usr/bin/env python3
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

"""
OCCAM Flask Web Application

Modern Python 3 Flask replacement for the legacy Python 2 CGI web server.
Provides the same user interface and functionality using the pyoccam Python 3 bindings.
"""

import os
import sys
import time
import tempfile
import zipfile
import datetime
import traceback
from pathlib import Path

from flask import Flask, render_template, request, send_file, redirect, url_for, Response
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from occam_wrapper import OccamManager
from jobs import JobManager
from utils import (
    get_unique_filename,
    get_timestamped_filename,
    unzip_data_file,
    prepare_cached_data
)

app = Flask(__name__)

# Configure Flask to trust proxy headers (X-Forwarded-*)
# This is essential when running behind Apache/Nginx reverse proxy with HTTPS
# x_for=1: trust X-Forwarded-For (client IP)
# x_proto=1: trust X-Forwarded-Proto (http/https)
# x_host=1: trust X-Forwarded-Host (original host)
# x_prefix=1: trust X-Forwarded-Prefix (URL prefix)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['DATA_DIR'] = Path(__file__).parent / 'data'
app.config['DATA_DIR'].mkdir(exist_ok=True)

VERSION = "3.5.0-flask"

# Initialize batch job manager
job_manager = JobManager()

# Valid actions (security allowlist)
COMMON_ACTIONS = {'fit', 'search', 'SBsearch', 'SBfit', ''}
FORM_ACTIONS = {'compare', 'log', 'fitbatch'}
JOBCONTROL_ACTIONS = {'jobcontrol'}
VALID_ACTIONS = COMMON_ACTIONS | FORM_ACTIONS | JOBCONTROL_ACTIONS


@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html', version=VERSION)


@app.route('/occam', methods=['GET', 'POST'])
def occam_main():
    """Main OCCAM interface - handles all actions"""
    start_time = time.time()

    if request.method == 'GET':
        # Show the input form
        action = request.args.get('action', '')
        if action not in VALID_ACTIONS:
            action = ''
        return render_form(action)

    # POST request - process the action
    try:
        action = request.form.get('action', '')

        # Validate action
        if action not in VALID_ACTIONS:
            return render_template('error.html',
                                 error="Invalid action specified"), 400

        # Route to appropriate handler
        if action == 'fit':
            return handle_fit(request.form, start_time)
        elif action == 'search':
            return handle_search(request.form, start_time)
        elif action == 'SBfit':
            return handle_sb_fit(request.form, start_time)
        elif action == 'SBsearch':
            return handle_sb_search(request.form, start_time)
        elif action == 'fitbatch':
            return handle_fit_batch(request.form, start_time)
        elif action == 'compare':
            return handle_batch_compare(request.form, start_time)
        elif action == 'log':
            return handle_show_log(request.form, start_time)
        elif action == 'jobcontrol':
            return handle_job_control(request.form, start_time)
        else:
            return render_form(action)

    except Exception as e:
        traceback.print_exc()
        return render_template('error.html',
                             error=str(e),
                             traceback=traceback.format_exc()), 500


def render_form(action=''):
    """Render the appropriate input form"""
    context = {
        'version': VERSION,
        'date': datetime.datetime.now().strftime("%c"),
        'action': action
    }

    if action in COMMON_ACTIONS:
        return render_template('main_form.html', **context)
    elif action == 'compare':
        return render_template('compare_form.html', **context)
    elif action == 'log':
        return render_template('log_form.html', **context)
    elif action == 'fitbatch':
        return render_template('fitbatch_form.html', **context)
    elif action == 'jobcontrol':
        return handle_job_control({}, 0)
    else:
        return render_template('main_form.html', **context)


def handle_fit(form_data, start_time):
    """Handle model fitting request"""
    # Get data file
    datafile = get_data_file(form_data)

    # Check for text format output
    text_format = 'format' in form_data

    if text_format:
        # CSV/text output
        return handle_fit_text(form_data, datafile, start_time)
    else:
        # HTML output
        return handle_fit_html(form_data, datafile, start_time)


def handle_fit_html(form_data, datafile, start_time):
    """Generate HTML fit report"""
    try:
        # Initialize OCCAM manager
        oc = OccamManager("VB")
        oc.init_from_file(datafile)

        # Configure options
        configure_manager(oc, form_data)

        # Set HTML output format
        oc.set_report_separator(OccamManager.HTMLFORMAT)

        # Perform fit
        model_name = form_data.get('model', '')
        target = form_data.get('negativeDVforConfusion', '')

        output = oc.do_fit(model_name, target)

        # Generate graphs if requested
        svg_file = None
        gephi_data = None

        if 'gfx' in form_data:
            svg_file = oc.get_graph_svg(model_name)
            if svg_file and os.path.exists(svg_file):
                with open(svg_file, 'r') as f:
                    svg_content = f.read()
                os.remove(svg_file)
            else:
                svg_content = None
        else:
            svg_content = None

        if 'gephi' in form_data:
            gephi_data = oc.get_gephi_output(model_name)

        # Clean up
        os.remove(datafile)

        elapsed = time.time() - start_time

        return render_template('fit_result.html',
                             output=output,
                             model=model_name,
                             elapsed=elapsed,
                             svg_content=svg_content,
                             gephi_data=gephi_data,
                             version=VERSION)
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_fit_text(form_data, datafile, start_time):
    """Generate CSV/text fit report"""
    try:
        oc = OccamManager("VB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)

        # Set CSV separator
        oc.set_report_separator(OccamManager.COMMASEP)

        model_name = form_data.get('model', '')
        target = form_data.get('negativeDVforConfusion', '')

        output = oc.do_fit(model_name, target)

        os.remove(datafile)

        # Return as CSV download
        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=fit_results.csv'
        return response
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_search(form_data, start_time):
    """Handle model search request"""
    datafile = get_data_file(form_data)
    text_format = 'format' in form_data

    if text_format:
        return handle_search_text(form_data, datafile, start_time)
    else:
        return handle_search_html(form_data, datafile, start_time)


def handle_search_html(form_data, datafile, start_time):
    """Generate HTML search report"""
    try:
        oc = OccamManager("VB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)

        # Set HTML output format
        oc.set_report_separator(OccamManager.HTMLFORMAT)

        # Get search parameters
        search_type = form_data.get('searchType', 'loopless-up')
        levels = int(form_data.get('searchLevels', 3))
        width = int(form_data.get('searchWidth', 3))

        # Set reference model
        ref_model = form_data.get('refModel', 'bottom')
        oc.set_ref_model(ref_model)

        output = oc.do_search(search_type, levels, width)

        # Generate graphs for best model if requested
        svg_content = None
        gephi_data = None
        best_model = None

        if 'gfx' in form_data or 'gephi' in form_data:
            # Get best model from search results
            try:
                best_model = oc.get_best_model_by_bic()
                if best_model and 'gfx' in form_data:
                    svg_file = oc.get_graph_svg(best_model)
                    if svg_file and os.path.exists(svg_file):
                        with open(svg_file, 'r') as f:
                            svg_content = f.read()
                        os.remove(svg_file)

                if best_model and 'gephi' in form_data:
                    gephi_data = oc.get_gephi_output(best_model)
            except:
                pass

        os.remove(datafile)

        elapsed = time.time() - start_time

        return render_template('search_result.html',
                             output=output,
                             search_type=search_type,
                             levels=levels,
                             width=width,
                             elapsed=elapsed,
                             svg_content=svg_content,
                             gephi_data=gephi_data,
                             best_model=best_model,
                             version=VERSION)
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_search_text(form_data, datafile, start_time):
    """Generate CSV search report"""
    try:
        oc = OccamManager("VB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)
        oc.set_report_separator(OccamManager.COMMASEP)

        search_type = form_data.get('searchType', 'loopless-up')
        levels = int(form_data.get('searchLevels', 3))
        width = int(form_data.get('searchWidth', 3))
        ref_model = form_data.get('refModel', 'bottom')
        oc.set_ref_model(ref_model)

        output = oc.do_search(search_type, levels, width)

        os.remove(datafile)

        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=search_results.csv'
        return response
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_sb_fit(form_data, start_time):
    """Handle state-based model fitting"""
    datafile = get_data_file(form_data)
    text_format = 'format' in form_data

    if text_format:
        return handle_sb_fit_text(form_data, datafile, start_time)
    else:
        return handle_sb_fit_html(form_data, datafile, start_time)


def handle_sb_fit_html(form_data, datafile, start_time):
    """Generate HTML state-based fit report"""
    try:
        oc = OccamManager("SB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)

        # Set HTML output format
        oc.set_report_separator(OccamManager.HTMLFORMAT)

        model_name = form_data.get('model', '')
        target = form_data.get('negativeDVforConfusion', '')

        output = oc.do_fit(model_name, target)

        # Generate graphs if requested
        svg_content = None
        gephi_data = None

        if 'gfx' in form_data:
            svg_file = oc.get_graph_svg(model_name)
            if svg_file and os.path.exists(svg_file):
                with open(svg_file, 'r') as f:
                    svg_content = f.read()
                os.remove(svg_file)

        if 'gephi' in form_data:
            gephi_data = oc.get_gephi_output(model_name)

        os.remove(datafile)

        elapsed = time.time() - start_time

        return render_template('sbfit_result.html',
                             output=output,
                             model=model_name,
                             elapsed=elapsed,
                             svg_content=svg_content,
                             gephi_data=gephi_data,
                             version=VERSION)
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_sb_fit_text(form_data, datafile, start_time):
    """Generate CSV state-based fit report"""
    try:
        oc = OccamManager("SB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)
        oc.set_report_separator(OccamManager.COMMASEP)

        model_name = form_data.get('model', '')
        target = form_data.get('negativeDVforConfusion', '')

        output = oc.do_fit(model_name, target)

        os.remove(datafile)

        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=sbfit_results.csv'
        return response
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_sb_search(form_data, start_time):
    """Handle state-based model search"""
    datafile = get_data_file(form_data)
    text_format = 'format' in form_data

    if text_format:
        return handle_sb_search_text(form_data, datafile, start_time)
    else:
        return handle_sb_search_html(form_data, datafile, start_time)


def handle_sb_search_html(form_data, datafile, start_time):
    """Generate HTML state-based search report"""
    try:
        oc = OccamManager("SB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)

        # Set HTML output format
        oc.set_report_separator(OccamManager.HTMLFORMAT)

        search_type = form_data.get('searchType', 'sb-loopless-up')
        levels = int(form_data.get('searchLevels', 3))
        width = int(form_data.get('searchWidth', 3))
        ref_model = form_data.get('refModel', 'bottom')
        oc.set_ref_model(ref_model)

        output = oc.do_search(search_type, levels, width)

        # Generate graphs for best model if requested
        svg_content = None
        gephi_data = None
        best_model = None

        if 'gfx' in form_data or 'gephi' in form_data:
            try:
                best_model = oc.get_best_model_by_bic()
                if best_model and 'gfx' in form_data:
                    svg_file = oc.get_graph_svg(best_model)
                    if svg_file and os.path.exists(svg_file):
                        with open(svg_file, 'r') as f:
                            svg_content = f.read()
                        os.remove(svg_file)

                if best_model and 'gephi' in form_data:
                    gephi_data = oc.get_gephi_output(best_model)
            except:
                pass

        os.remove(datafile)

        elapsed = time.time() - start_time

        return render_template('sbsearch_result.html',
                             output=output,
                             search_type=search_type,
                             levels=levels,
                             width=width,
                             elapsed=elapsed,
                             svg_content=svg_content,
                             gephi_data=gephi_data,
                             best_model=best_model,
                             version=VERSION)
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_sb_search_text(form_data, datafile, start_time):
    """Generate CSV state-based search report"""
    try:
        oc = OccamManager("SB")
        oc.init_from_file(datafile)

        configure_manager(oc, form_data)
        oc.set_report_separator(OccamManager.COMMASEP)

        search_type = form_data.get('searchType', 'sb-loopless-up')
        levels = int(form_data.get('searchLevels', 3))
        width = int(form_data.get('searchWidth', 3))
        ref_model = form_data.get('refModel', 'bottom')
        oc.set_ref_model(ref_model)

        output = oc.do_search(search_type, levels, width)

        os.remove(datafile)

        response = Response(output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=sbsearch_results.csv'
        return response
    except Exception as e:
        if os.path.exists(datafile):
            os.remove(datafile)
        raise


def handle_fit_batch(form_data, start_time):
    """Handle batch fitting with email results"""
    # TODO: Implement full batch processing with background jobs and email
    # For now, return a message
    return render_template('error.html',
                         error="Batch processing not yet implemented in Flask version. "
                               "This feature requires background job queue and email integration.",
                         version=VERSION)


def handle_batch_compare(form_data, start_time):
    """Handle batch model comparison"""
    # TODO: Implement batch comparison
    # For now, return a message
    return render_template('error.html',
                         error="Batch comparison not yet implemented in Flask version. "
                               "This feature requires background job queue integration.",
                         version=VERSION)


def handle_show_log(form_data, start_time):
    """Show batch job log"""
    # TODO: Implement log viewing
    # For now, return a message
    return render_template('error.html',
                         error="Log viewing not yet implemented in Flask version.",
                         version=VERSION)


def handle_job_control(form_data, start_time):
    """Handle job control operations (list/kill jobs)"""
    import subprocess
    import re

    # Kill job if requested
    pid = form_data.get('pid', '')
    if pid:
        try:
            pid_int = int(pid)
            # Verify it's an occam process before killing
            result = subprocess.run(['ps', '-o', 'pid,command'],
                                  capture_output=True, text=True)
            lines = result.stdout.split('\n')
            killed = False
            for line in lines:
                if 'occam' in line and str(pid_int) in line:
                    try:
                        os.kill(pid_int, 9)
                        killed = True
                        break
                    except ProcessLookupError:
                        pass

            if killed:
                message = f"Job {pid} killed successfully."
            else:
                message = f"Could not kill job {pid}. Process not found or not an OCCAM process."
        except (ValueError, PermissionError) as e:
            message = f"Error killing job {pid}: {str(e)}"
    else:
        message = ""

    # List active jobs
    try:
        result = subprocess.run(['ps', '-o', 'pid,lstart,etime,pcpu,pmem,command'],
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')[1:]  # Skip header

        jobs = []
        for line in lines:
            if 'occam' in line and line.strip():
                # Parse the line
                parts = re.split(r'\s+', line.strip(), maxsplit=9)
                if len(parts) >= 10:
                    command = parts[9]
                    # Filter out web server processes
                    if 'weboccam' not in command and 'app.py' not in command:
                        jobs.append({
                            'pid': parts[0],
                            'start': ' '.join(parts[1:4]) + ' ' + parts[5],
                            'year': parts[4],
                            'elapsed': parts[6],
                            'cpu': parts[7],
                            'mem': parts[8],
                            'command': command
                        })
    except Exception as e:
        jobs = []
        message += f" Error listing jobs: {str(e)}"

    return render_template('job_control.html',
                         jobs=jobs,
                         message=message,
                         version=VERSION)


@app.route('/batch', methods=['GET'])
def batch_form():
    """Display batch job submission form"""
    return render_template('batch_form.html', version=VERSION)


@app.route('/batch', methods=['POST'])
def submit_batch_job():
    """Handle batch job submission"""
    try:
        # Get form data
        action = request.form.get('action')
        model_str = request.form.get('model', '')
        email = request.form.get('email')

        # Validate required fields
        if not action:
            return render_template('error.html',
                                 error="Action is required"), 400
        if not email:
            return render_template('error.html',
                                 error="Email address is required for batch jobs"), 400

        # Get uploaded data file
        if 'data' not in request.files:
            return render_template('error.html',
                                 error="No data file uploaded"), 400

        file = request.files['data']
        if file.filename == '':
            return render_template('error.html',
                                 error="No data file selected"), 400

        # Save uploaded file to data directory
        filename = secure_filename(file.filename)
        datafile = get_timestamped_filename(
            app.config['DATA_DIR'] / filename
        )
        file.save(datafile)

        # Unzip if necessary
        datafile = unzip_data_file(datafile)

        # Collect optional parameters
        options = {}
        if request.form.get('separator'):
            options['separator'] = request.form.get('separator')
        if request.form.get('alpha'):
            options['alpha'] = float(request.form.get('alpha'))
        if request.form.get('search_levels'):
            options['search_levels'] = int(request.form.get('search_levels'))
        if request.form.get('search_width'):
            options['search_width'] = int(request.form.get('search_width'))

        # Submit job to queue
        job_id = job_manager.submit_job(
            action=action,
            data_file=datafile,
            model_str=model_str,
            email=email,
            **options
        )

        # Redirect to job status page
        return redirect(url_for('view_batch_job', job_id=job_id))

    except Exception as e:
        traceback.print_exc()
        return render_template('error.html',
                             error=str(e),
                             traceback=traceback.format_exc()), 500


@app.route('/batch/jobs')
def batch_jobs_list():
    """List all batch jobs"""
    try:
        jobs = job_manager.list_jobs()
        return render_template('batch_jobs.html',
                             jobs=jobs,
                             version=VERSION)
    except Exception as e:
        traceback.print_exc()
        return render_template('error.html',
                             error=str(e),
                             traceback=traceback.format_exc()), 500


@app.route('/batch/job/<job_id>')
def view_batch_job(job_id):
    """View individual batch job status and results"""
    try:
        status = job_manager.get_job_status(job_id)
        if not status:
            return render_template('error.html',
                                 error=f"Job {job_id} not found"), 404

        return render_template('batch_result.html',
                             job_id=status['job_id'],
                             action=status.get('action'),
                             submitted_at=status.get('submitted_at'),
                             completed_at=status.get('completed_at'),
                             status=status.get('status'),
                             output=status.get('output'),
                             error=status.get('error'),
                             version=VERSION)
    except Exception as e:
        traceback.print_exc()
        return render_template('error.html',
                             error=str(e),
                             traceback=traceback.format_exc()), 500


@app.route('/batch/job/<job_id>/cancel', methods=['POST'])
def cancel_batch_job(job_id):
    """Cancel a batch job"""
    try:
        success = job_manager.cancel_job(job_id)
        if success:
            # Redirect back to jobs list
            return redirect(url_for('batch_jobs_list'))
        else:
            return render_template('error.html',
                                 error=f"Could not cancel job {job_id}"), 400
    except Exception as e:
        traceback.print_exc()
        return render_template('error.html',
                             error=str(e),
                             traceback=traceback.format_exc()), 500


def get_data_file(form_data):
    """Process uploaded data file"""
    if 'data' not in request.files:
        raise ValueError("No data file uploaded")

    file = request.files['data']
    if file.filename == '':
        raise ValueError("No data file selected")

    # Save uploaded file
    filename = secure_filename(file.filename)
    datafile = get_timestamped_filename(
        app.config['DATA_DIR'] / filename
    )
    file.save(datafile)

    # Unzip if necessary
    datafile = unzip_data_file(datafile)

    return datafile


def configure_manager(oc, form_data):
    """Configure OCCAM manager from form data"""
    # Set various options based on form fields
    if 'skipnominal' in form_data:
        oc.set_skip_nominal(True)

    if 'skipresiduals' in form_data:
        oc.set_skip_residuals(True)

    if 'skipivitables' in form_data:
        oc.set_skip_ivi_tables(True)

    if 'calcExpectedDV' in form_data:
        oc.set_calc_expected_dv(True)

    # Graph options
    if 'gfx' in form_data or 'gephi' in form_data:
        # Parse graph dimensions
        width = int(form_data.get('graphWidth', 640))
        height = int(form_data.get('graphHeight', 480))
        font_size = int(form_data.get('graphFontSize', 12))
        node_size = int(form_data.get('graphNodeSize', 24))

        oc.set_gfx(
            gfx='gfx' in form_data,
            gephi='gephi' in form_data,
            layout=form_data.get('layout', 'default'),
            hide_isolated='hideIsolated' in form_data,
            hide_dv='hideDV' in form_data,
            full_var_names='fullVarNames' in form_data,
            width=width,
            height=height,
            fontSize=font_size,
            nodeSize=node_size
        )


if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)
