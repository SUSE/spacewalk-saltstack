# pylint: disable-msg=C0103
"""
Functions related to Salt jobs from minions
"""
import logging

from saltwalk.inventory import LIST_PKGS_CMD
from saltwalk.inventory import NETWORK_IFACES_CMD
from saltwalk.inventory import process_network_ifaces_result
from saltwalk.inventory import process_package_list_result

logger = logging.getLogger("saltwalk")


def process_job_result(event):
    """
    Dispatch to the specific return handler for a command
    issued to a minion.
    Current commands supported/expected:
      - pkg.list_pkgs
      - network.interfaces
    """
    try:
        data = event['data']
        tag = event['tag']
        minion = data['id']
        fun = data['fun']
    except KeyError as error:
        logger.exception('Unexpected event format for %s. %s', tag, error)
        return

    try:
        if data['success']:
            if fun == LIST_PKGS_CMD:
                process_package_list_result(minion, event)
            elif fun == NETWORK_IFACES_CMD:
                process_network_ifaces_result(minion, event)
            else:
                logger.warning("No handler for: %s -> %s", tag, fun)
        else:
            logger.error("Event reports that the command failed: %s -> %s",
                         minion, fun)
    except Exception as error:
        logger.exception('Unable to process event %s. %s', tag, error)
