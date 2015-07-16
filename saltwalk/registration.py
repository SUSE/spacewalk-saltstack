# pylint: disable-msg=C0103
"""
Functions related to registration of minions into Spacewalk
"""
import logging

from spacewalk.common import rhnFlags
from spacewalk.server import rhnUser, rhnServer, rhnSQL
from pprint import PrettyPrinter

logger = logging.getLogger("saltwalk")
pp = PrettyPrinter(indent=2)

PILLAR_GET_CMD = 'pillar.get'
GRAINS_ITEMS_CMD = 'grains.items'
ACTIVATION_KEY_PILLAR_KEY = 'spacewalk-activation-key'
ADMIN_USER_PILLAR_KEY = 'spacewalk-admin-user'


def register_system(client, minion):
    """
    Adds a spacewalk registration for a minion.
    """
    # ask for the minion data to get its id that tell us
    # if it is registered, and data to register it
    ret = client.cmd_iter(minion, GRAINS_ITEMS_CMD)

    for grains in ret:
        logger.info("Registering new minion: %s", minion)

        if minion in grains:
            values = grains[minion]['ret']
            logger.debug("%s grains:\n%s", minion, pp.pformat(values))

            username = client.cmd(minion, PILLAR_GET_CMD, [ADMIN_USER_PILLAR_KEY])
            if not username[minion]:
                logger.error("Can't get admin user from pillar key '%s'", ADMIN_USER_PILLAR_KEY)
                continue

            user = rhnUser.search(username[minion])

            rhnSQL.clear_log_id()
            newserv = rhnServer.Server(user, values['osarch'])

            token = client.cmd(minion, PILLAR_GET_CMD, [ACTIVATION_KEY_PILLAR_KEY])

            if not token[minion]:
                tokens_obj = rhnServer.search_org_token(user.contact["org_id"])
                rhnFlags.set("universal_registration_token", tokens_obj)
            else:
                tokens_obj = rhnServer.search_token(token[minion])
                rhnFlags.set("registration_token", tokens_obj)

            # reserve the id
            newserv.getid()
            # overrite the digital id
            # FIXME: None of these values appear in the systems properties
            newserv.server['digital_server_id'] = 'SALT-ID-%s' % minion
            newserv.server['release'] = values['osrelease']
            newserv.server['os'] = values['osfullname']
            newserv.server['name'] = minion
            newserv.server['running_kernel'] = values['kernelrelease']
            newserv.virt_uuid = None
            newserv.save()

            rhnSQL.commit()

            logger.info("%s registered as %s", minion, newserv.getid())
        else:
            logger.error("Registration failed: Can't get grains for %s",
                         minion)


def is_minion_registered(minion):
    """
    Returns sid if a minion is registered, False otherwise
    """
    result = False
    cursor = rhnSQL.prepare("""
    SELECT id from rhnServer
    WHERE digital_server_id=:did
    """)
    if cursor.execute(did=('SALT-ID-%s' % minion)):
        result = cursor.fetchone_dict()['id']
    return result

