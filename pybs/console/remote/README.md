### TODO: 


* add support for `code`-specific CLI arguments being provided 
* add support for using a file containing CLI arguments already there (config yaml file?) 
* add support for multiple files / directories being opened on the remote server 

* prevent need for changing user's `~/.ssh/config` by instead changing the default VS code ssh connection command, such as the following:

```
[09:26:12.233] Spawned 63186
[09:26:12.234] Using connect timeout of 62 seconds
[09:26:12.343] > local-server-1> Running ssh connection command: ssh -v -T -D 56023 -o ConnectTimeout=60 katana-k092
[09:26:12.345] > local-server-1> Spawned ssh, pid=63206
[09:26:12.364] stderr> OpenSSH_9.8p1, LibreSSL 3.3.6

```


DONE:
- add tab autocompletion scripts
- add hostname tab completion (use ~/.ssh/config)
- fix logging for qsub wait
- add TUI timer for job submission
- add intelligent remote server expansion of paths example $SCRATCH
to avoid issue where VS code does not evaluate $ variables correctly. 
- add support for local job scripts

TODO:
- change character width on subcommand tab complete suggestions
- automatically close VS code window when Ctrl+C is used to kill job 

- add help to ck args
- add tab complete for remote paths similar to `scp```
- add auto install of ssh config required hostname alias
- add arbitrary command execution for any method (with certain decorator)
from PBSServer class
e.g. write `qsub` and this will call the `qsub` method of the PBSServer class
if a method with that name exists.
- refactoring of PBSServer class to use `ssh_command` decorator
- add `config` command to add config items to a config file
such as turning debug on/off

Future TODO:
- add db for currently running jobs, able to login to
any server and see resources, walltime etc.
- add "autorefresh" or "keepalive" option to remember when the walltime will
expire, and request another GPU node that overlaps so we can keep the session logged
in on the same node.