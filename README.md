
# Salt Spacewalk integration reactor

This process allows you to integrate a Saltstack environment in Spacewalk.

## Features

* Automatic registration of (accepted) minions in Spacewalk
* (WIP) Integration of a (minimal) part of the minion hardware inventory in Spacewalk
* (WIP) Integration of the software inventory of the minion in Spacewalk
* Integration of Salt jobs into the event history and synchronization of the action
  status and results

## Limitations

* Events happening when the reactor is down will not be recorded
* Initiating actions from the Spacewalk user interface require additional
  changes in Spacewalk, which are also being done as part of the concept, but
  are not part of the reactor.
  (incl. a Java library to interact with salt-api)

## Requirements

* Run the salt-master on the Spacewalk server

* Setup pillar data so set the default admin user and activation key for
  salt minions. Put the following data in /srv/pillar

top.sls
'''yaml
base:
  '*':
    - data
'''

data.sls
'''yamp
spacewalk-activation-key: 1-salt-testing
spacewalk-admin-user: admin
'''

This gives the same admin user and key for all minions. You can change top.sls to match different minion names or grains.

* Some patches to Spacewalk to introduce a SaltJob Action type
* Run salt-api locally in the Spacewalk so that the webapp can interact with it

* 

## Inner workings

The reactor reads events from the master in a loop. It reacts to the following
events.

* minon_start

When a minion starts, it will be registered with Spacwalk if it is not already
registered.
A refresh of the software inventory and hardware will be done

* tag salt/job/$jobid/new

If the job was not created by the reactor itself (like hardware refresh), an
action will be created, of type SaltJob

* tag salt/job/$jobid/ret/$minion

When an action is returned, if it was not created by the reactor itself,
the status will be updated.

## TODO

See https://github.com/SUSE/spacewalk-saltstack/issues

## Authors

The Spacewalk Salt reactor was developed by the SUSE Manager team during Hackweek 11
https://hackweek.suse.com/11/projects/514

## License

MIT