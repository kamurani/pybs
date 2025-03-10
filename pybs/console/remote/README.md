### TODO: 


- prevent need for changing user's `~/.ssh/config` by instead changing the default VS code ssh connection command, such as the following:

```
[09:26:12.233] Spawned 63186
[09:26:12.234] Using connect timeout of 62 seconds
[09:26:12.343] > local-server-1> Running ssh connection command: ssh -v -T -D 56023 -o ConnectTimeout=60 katana-k092
[09:26:12.345] > local-server-1> Spawned ssh, pid=63206
[09:26:12.364] stderr> OpenSSH_9.8p1, LibreSSL 3.3.6

```
