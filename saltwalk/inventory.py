# pylint: disable-msg=C0103
"""
Functions related to inventory data from minions
"""
import logging

from spacewalk.server import rhnServer
from saltwalk.registration import is_minion_registered
from pprint import PrettyPrinter

NETWORK_IFACES_CMD = 'network.interfaces'
LIST_PKGS_CMD = 'pkg.list_pkgs'

logger = logging.getLogger("saltwalk")
pp = PrettyPrinter(indent=2)


def request_minion_inventory(pending_jobs, client, minion):
    """
    When a minion starts up this function will
    grab it's current list of network interfaces, and
    installed packages, then update it's spacewalk
    registration.
    If the calls are successful we add the job ids
    to pending_jobs.
    """
    package_list_job_id = request_package_list(client, minion)
    if package_list_job_id:
        pending_jobs.add(package_list_job_id)
    network_ifaces_job_id = request_network_ifaces(client, minion)
    if network_ifaces_job_id:
        pending_jobs.add(network_ifaces_job_id)
    return pending_jobs


def request_minion_info_async(client, minion, cmd, desc):
    """
    Returns jobid for async cmd that was dispatched, False otherwise
    """
    jobid = client.cmd_async(minion, cmd)
    if jobid != 0:
        logger.info("'%s' request for %s (jid %s)",
                    desc, minion, jobid)
        return jobid
    else:
        logger.warn("'%s' request failed for %s",
                    desc, minion)
        return False


def request_package_list(client, minion):
    """
    Returns the jobid for an async request for the minions
    package list, False otherwise
    """
    return request_minion_info_async(client, minion, LIST_PKGS_CMD,
                                     'package list')


def request_network_ifaces(client, minion):
    """
    Returns the jobid for an async request for the minions
    network interface information, False otherwise
    """
    return request_minion_info_async(client, minion, NETWORK_IFACES_CMD,
                                     'network interfaces')


def process_network_ifaces_result(minion, event):
    """
    Updates the spacewalk registration for a minion
    with it's currently reported network interface list.
    """
    sid = is_minion_registered(minion)
    if not sid:
        logger.warning("%s is no longer registered. Interfaces ignored.",
                       minion)
        return

    profile = dict()
    interfaces = event.get('data', {}).get('return', {})
    logger.info('Got network interfaces for %s', sid)
    logger.debug(pp.pformat(interfaces))

    profile['class'] = 'NETINTERFACES'
    for iface, details in interfaces.iteritems():
        profile[iface] = dict()
        profile[iface]['ipv6'] = list()
        profile[iface]['hwaddr'] = details['hwaddr']
        # FIXME: how to get the iface module with Salt?
        profile[iface]['module'] = 'Unknown'

        # only one ipv4 addr supported
        for ipv4net in details['inet']:
            profile[iface]['ipaddr'] = ipv4net['address']
            profile[iface]['netmask'] = ipv4net['netmask']
            profile[iface]['broadcast'] = ipv4net['broadcast']
            break

        for ipv6net in details['inet6']:
            ipv6net['scope'] = 'Unknown'
            ipv6net['addr'] = ipv6net['address']
            ipv6net['netmask'] = ipv6net['prefixlen']
            profile[iface]['ipv6'].append(ipv6net)

        server = rhnServer.search(int(sid))

        # No need to delete the hardware as the class seems to ovewrite
        # the previous value
        server.add_hardware(profile)
        server.save_hardware()


def format_package_list(packages):
    """
    Take the package list provided by salt and
    format it as spacewalk expects it.
    """
    # FIXME: Fake data needs to be sourced correctly
    def frmt_pkg(name, version):
        return {'name': name, 'version': version,
                'epoch': '', 'release': 'unknown',
                'arch': 'x86_64', 'installtime': 1413297811}
    return [frmt_pkg(name, version) for name, version in packages.items()]


def process_package_list_result(minion, event):
    """
    Updates the server registration of the minion with
    the list of packages reported by salt.
    """
    sid = is_minion_registered(minion)
    if not sid:
        logger.warning("%s is no longer registered. Ignoring package list",
                       minion)
        return

    package_list = format_package_list(event.get('data', {}).get('return', {}))

    if not package_list:
        logger.error("Failed to retrieve a current package list for %s",
                     minion)
    else:
        logger.info('Updating package list for Spacewalk sid=%s', sid)
        server = rhnServer.search(int(sid))
        server.dispose_packages()
        for package in package_list:
            server.add_package(package)
        server.save_packages()
