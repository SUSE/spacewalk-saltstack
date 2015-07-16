# pylint: disable-msg=C0103
"""
Helper for database transactions
"""
import logging
from contextlib import contextmanager
from spacewalk.server import rhnSQL
from spacewalk.common.rhnException import rhnFault

logger = logging.getLogger("saltwalk")


@contextmanager
def transaction(context=None):
    """
    Keeping writes to spacewalk as DRY as possible,
    and making sure that commit or rollback is always
    called as appropriate.
    """
    # TODO: Create proper class.
    #       once you start adding nested functions for
    #       a 'simple' context manager the time has come
    #       to just create that class instead of use the
    #       decorator.
    def log_exception(error):
        if context is not None:
            logger.exception("%s: %s", error, context)
        else:
            logger.exception("Unhandled exception: %s", error)

    def rollback():
        logger.warning("Rolling back rhnSQL transaction.")
        rhnSQL.rollback()

    try:
        yield
        rhnSQL.commit()
    except rhnFault as fault:
        logger.exception("Server fault caught: %s", fault)
        rollback()
    except Exception as error:
        msg = str(error)
        if msg == "Unknown action type salt.job" or \
           msg.find('rhnactionsaltjob') != -1:
            logger.error("Saltstack not fully supported by this system:\n%s.",
                         msg)
        else:
            log_exception(error)
        rollback()

