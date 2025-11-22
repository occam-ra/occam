#!/usr/bin/env python3
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

"""
Background worker for processing OCCAM batch jobs using Redis Queue (RQ)
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from redis import Redis
from rq import Queue, Worker

# Import OCCAM manager
from occam_wrapper import OccamManager


def process_occam_job(job_id, action, data_file, model_str, email, **options):
    """
    Process an OCCAM analysis job in the background

    Args:
        job_id: Unique job identifier
        action: OCCAM action (fit, search, SBfit, SBsearch)
        data_file: Path to uploaded data file
        model_str: Model specification string
        email: Email address for notification
        **options: Additional OCCAM options (separator, alpha, etc.)

    Returns:
        dict: Job results including status, output, and any errors
    """
    result = {
        'job_id': job_id,
        'action': action,
        'status': 'running',
        'start_time': datetime.now().isoformat(),
        'output': None,
        'error': None
    }

    try:
        # Determine model type from action
        model_type = 'SB' if action.startswith('SB') else 'VB'
        manager = OccamManager(model_type)

        # Build command line arguments
        args = [
            f'action:{action}',
            f'data:{data_file}',
        ]

        if model_str:
            args.append(f'model:{model_str}')

        # Add optional parameters
        if 'separator' in options:
            args.append(f'separator:{options["separator"]}')
        if 'alpha' in options:
            args.append(f'alpha:{options["alpha"]}')
        if 'search_levels' in options:
            args.append(f'searchLevels:{options["search_levels"]}')
        if 'search_width' in options:
            args.append(f'searchWidth:{options["search_width"]}')
        if 'ref_model' in options:
            args.append(f'refModel:{options["ref_model"]}')

        # Initialize and run analysis
        manager.init_from_command_line(args)

        if action in ['fit', 'SBfit']:
            manager.do_fit()
        elif action in ['search', 'SBsearch']:
            manager.do_search()
        else:
            raise ValueError(f"Unknown action: {action}")

        # Get results
        output = manager.get_report()

        result['status'] = 'completed'
        result['output'] = output
        result['end_time'] = datetime.now().isoformat()

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        result['end_time'] = datetime.now().isoformat()

    return result


def send_job_notification(email, result):
    """
    Send email notification when job completes

    Args:
        email: Recipient email address
        result: Job result dictionary
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Get email configuration from environment
    smtp_host = os.environ.get('SMTP_HOST', 'localhost')
    smtp_port = int(os.environ.get('SMTP_PORT', '25'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    from_email = os.environ.get('SMTP_FROM', 'noreply@occam.local')

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"OCCAM Job {result['job_id']} - {result['status'].upper()}"
    msg['From'] = from_email
    msg['To'] = email

    # Create email body
    if result['status'] == 'completed':
        text = f"""
Your OCCAM analysis job has completed successfully.

Job ID: {result['job_id']}
Action: {result['action']}
Started: {result['start_time']}
Completed: {result['end_time']}

Results are available at the OCCAM web interface.
Use Job ID {result['job_id']} to retrieve your results.
"""
    else:
        text = f"""
Your OCCAM analysis job has failed.

Job ID: {result['job_id']}
Action: {result['action']}
Started: {result['start_time']}
Failed: {result['end_time']}

Error: {result.get('error', 'Unknown error')}

Please check your input data and try again.
"""

    msg.attach(MIMEText(text, 'plain'))

    # Send email
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Email sent to {email} for job {result['job_id']}")
    except Exception as e:
        print(f"Failed to send email: {e}", file=sys.stderr)


def run_worker():
    """Run RQ worker to process jobs from the queue"""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_conn = Redis.from_url(redis_url)

    worker = Worker(['occam'], connection=redis_conn)
    worker.work()


if __name__ == '__main__':
    run_worker()
