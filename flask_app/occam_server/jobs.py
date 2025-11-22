#!/usr/bin/env python3
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

"""
Job management for OCCAM batch processing
"""

import os
import uuid
from datetime import datetime
from redis import Redis
from rq import Queue
from rq.job import Job

from worker import process_occam_job, send_job_notification


class JobManager:
    """Manages OCCAM batch jobs using Redis Queue"""

    def __init__(self, redis_url=None):
        """
        Initialize job manager

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
        """
        if redis_url is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

        self.redis_conn = Redis.from_url(redis_url)
        self.queue = Queue('occam', connection=self.redis_conn)

    def submit_job(self, action, data_file, model_str='', email='', **options):
        """
        Submit a new OCCAM analysis job to the queue

        Args:
            action: OCCAM action (fit, search, SBfit, SBsearch)
            data_file: Path to uploaded data file
            model_str: Model specification string
            email: Email for notification when job completes
            **options: Additional OCCAM options

        Returns:
            str: Job ID
        """
        job_id = str(uuid.uuid4())

        # Enqueue the job
        job = self.queue.enqueue(
            process_occam_job,
            job_id=job_id,
            action=action,
            data_file=data_file,
            model_str=model_str,
            email=email,
            **options,
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400
        )

        # Store job metadata
        self._store_job_metadata(job_id, {
            'action': action,
            'email': email,
            'submitted_at': datetime.now().isoformat(),
            'rq_job_id': job.id
        })

        # If email provided, register callback for notification
        if email:
            job.meta['email'] = email
            job.save_meta()

        return job_id

    def get_job_status(self, job_id):
        """
        Get current status of a job

        Args:
            job_id: Job ID

        Returns:
            dict: Job status information
        """
        metadata = self._get_job_metadata(job_id)
        if not metadata:
            return None

        rq_job_id = metadata.get('rq_job_id')
        job = Job.fetch(rq_job_id, connection=self.redis_conn)

        status = {
            'job_id': job_id,
            'action': metadata.get('action'),
            'submitted_at': metadata.get('submitted_at'),
            'status': job.get_status(),
            'is_finished': job.is_finished,
            'is_failed': job.is_failed,
        }

        if job.is_finished:
            result = job.result
            if result:
                status['completed_at'] = result.get('end_time')
                status['output'] = result.get('output')
                status['error'] = result.get('error')

                # Send email notification if not already sent
                email = metadata.get('email')
                if email and not self._was_notification_sent(job_id):
                    send_job_notification(email, result)
                    self._mark_notification_sent(job_id)

        elif job.is_failed:
            status['error'] = str(job.exc_info) if job.exc_info else 'Job failed'

        return status

    def list_jobs(self, limit=50):
        """
        List recent jobs

        Args:
            limit: Maximum number of jobs to return

        Returns:
            list: List of job status dictionaries
        """
        job_keys = self.redis_conn.keys('job:*:metadata')
        jobs = []

        for key in job_keys[:limit]:
            job_id = key.decode().split(':')[1]
            status = self.get_job_status(job_id)
            if status:
                jobs.append(status)

        # Sort by submission time (newest first)
        jobs.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
        return jobs

    def get_job_result(self, job_id):
        """
        Get the result output for a completed job

        Args:
            job_id: Job ID

        Returns:
            str: Job output or None if not available
        """
        status = self.get_job_status(job_id)
        if status and status.get('is_finished'):
            return status.get('output')
        return None

    def cancel_job(self, job_id):
        """
        Cancel a pending or running job

        Args:
            job_id: Job ID

        Returns:
            bool: True if cancelled, False otherwise
        """
        metadata = self._get_job_metadata(job_id)
        if not metadata:
            return False

        rq_job_id = metadata.get('rq_job_id')
        try:
            job = Job.fetch(rq_job_id, connection=self.redis_conn)
            job.cancel()
            return True
        except:
            return False

    def _store_job_metadata(self, job_id, metadata):
        """Store job metadata in Redis"""
        key = f'job:{job_id}:metadata'
        self.redis_conn.hset(key, mapping=metadata)
        self.redis_conn.expire(key, 86400)  # Expire after 24 hours

    def _get_job_metadata(self, job_id):
        """Retrieve job metadata from Redis"""
        key = f'job:{job_id}:metadata'
        data = self.redis_conn.hgetall(key)
        if not data:
            return None
        return {k.decode(): v.decode() for k, v in data.items()}

    def _was_notification_sent(self, job_id):
        """Check if notification was already sent for this job"""
        key = f'job:{job_id}:notified'
        return self.redis_conn.exists(key)

    def _mark_notification_sent(self, job_id):
        """Mark that notification was sent for this job"""
        key = f'job:{job_id}:notified'
        self.redis_conn.setex(key, 86400, '1')
