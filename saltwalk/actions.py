# pylint: disable-msg=C0103
"""
Functions related to creating Spacewalk actions from salt jobs
"""
import logging
import json
from spacewalk.server import rhnAction
from spacewalk.server import rhnSQL

from saltwalk.registration import is_minion_registered
from saltwalk.jobs import process_job_result
from saltwalk.transaction import transaction
from pprint import PrettyPrinter

logger = logging.getLogger("saltwalk")
pp = PrettyPrinter(indent=2)


def handle_job(pending_jobs, job_state, event):
    """
    When we get a job related event from salt we
    either process the result from an async
    command that we issued or we update spacewalk
    with information about the job.
    If we're receiving the result from a job we
    created, we remove the job id from pending_jobs
    """
    jid = event['data']['jid']
    logger.info("Processing job: %s", jid)
    if job_state == 'new':
        if jid not in pending_jobs:
            logger.debug("Creating actions for job %s", jid)
            create_actions_for_job(event)
    elif job_state == 'ret':
        if jid in pending_jobs:
            logger.debug("Processing completed job request: %s", jid)
            pending_jobs.remove(jid)
            process_job_result(event)
        else:
            logger.debug("Updating actions for job %s", jid)
            update_actions_for_job(event)
    else:
        logger.warning("Unexpected job_state: %s", job_state)
        logger.debug(pp.pformat(event))
    return pending_jobs


# FIXME: Unkown action type salt.job.
def create_actions_for_job(event):
    """
    For jobs that originated outside of this system
    we create coresponding events in spacewalk
    """
    jid = event['data']['jid']
    minions = event['data']['minions']
    fun = event['data']['fun']

    aid = rhnAction.schedule_action(action_type='salt.job',
                                    action_name='Salt job %s (%s)' %
                                    (jid, fun), org_id=1)

    with transaction(event):
        cursor = rhnSQL.prepare("""
        insert into
        rhnActionSaltJob (action_id, jid, data)
        values (:action_id, :jid, :data)
        """)
        cursor.execute(action_id=aid, jid=jid,
                       data=json.dumps(event['data']))

        for minion in minions:
            sid = is_minion_registered(minion)
            if not sid:
                logger.warn("Skipping reference to unregistered minion: %s",
                            minion)
                continue
            cursor = rhnSQL.prepare("""
            insert into
            rhnServerAction (server_id, action_id, status, pickup_time)
            values (:server_id, :action_id, 0, :pickup_time)
            """)
            cursor.execute(server_id=sid, action_id=aid,
                           pickup_time=event['data']['_stamp'])


# FIXME: I think this also requires a patch to spacewalk.
def update_actions_for_job(event):
    """
    Takes an salt command return event and sets the
    status of the corresponding Spacewalk job.
    """
    jid = event['data']['jid']
    minion = event['data']['id']

    sid = is_minion_registered(minion)
    if not sid:
        logger.error('minion %s is no longer registered', minion)
        # FIXME: cleanup its actions?
        return

    logger.info('Updating job status for sid %s: (%s) jid: %s',
                sid, minion, jid)

    with transaction(event):
        cursor = rhnSQL.prepare("""
        update rhnServerAction set
        status=:status,
        result_msg=:result_msg,
        result_code=:result_code,
        completion_time=:completion_time
        where action_id in
           (select distinct action_id from rhnActionSaltJob where jid=:jid)
        and server_id=:sid""")

        status = 2 if event['data']['success'] else 1
        cursor.execute(sid=sid,
                       status=status,
                       result_code=event['data']['retcode'],
                       result_msg=json.dumps(event['data']['return'])[:1024],
                       completion_time=event['data']['_stamp'],
                       jid=jid)


