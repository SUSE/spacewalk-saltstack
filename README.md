
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
* Some patches to Spacewalk to introduce a SaltJob Action type
* Run salt-api locally in the Spacewalk so that the webapp can interact with it

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

* The reactor is using a hardcoded '1-SALT' registration key
* The reactor is using a hardcoded 'admin' user to create the new registered server
* The reactor is writing a fake package inventory list. EVR spliting needs to be
  done from the Salt stack data we receive (not done yet).

* Cleanup all actions for jobs that completed in salt-master at reactor startup
  (for all jobs that completed when the reactor was down). Beware of race conditions.

* Figure out how to refresh the hardware inventory after rpm db changes

## Authors

The Spacewalk Salt reactor was developed by the SUSE Manager team during Hackweek 11
https://hackweek.suse.com/11/projects/514

## License

MIT