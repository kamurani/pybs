# PyBS

## Installation 

#### 1. Install `pybs` 
`pip install pythonpbs` 

#### 2. SSH Configuration 

You will need to add the following to your `~/.ssh/config` file:  

```
# the host details of your login node:
Host YOUR_LOGIN_SERVER_ALIAS
  Hostname YOUR_LOGIN_SERVER_HOSTNAME
  User YOUR_USERNAME
```


For better ssh performance, you can optionally add the following: 
```
Host *
	ControlMaster auto
	ControlPath ~/.ssh/controlmasters/%r@%h:%p
	ControlPersist yes

```
Then, create directory: 
```bash
mkdir -p ~/.ssh/controlmasters
```
To prevent disconnecting from timeouts, you can also add: 
```
# Send keepalive packets to prevent SSH disconnecting...
Host *
  ServerAliveInterval 60
```


#### 3. VS code setup

To use the `code` command, you will need to have `VS code` added to your `$PATH`. 
##### Using command palette 

In VS code, open the **command palette** (`Cmd+Shift+P`), type "shell command",
and run the `Shell Command: Install 'code' command in PATH` command.
##### Manually configure the path 

###### Zsh 

```zsh
cat << EOF >> ~/.zprofile
# Add Visual Studio Code (code)
export PATH="\$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
EOF
```
###### Bash
```bash
cat << EOF >> ~/.bash_profile
# Add Visual Studio Code (code)
export PATH="\$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
EOF
```
Restart your shell to register your changes.  You can check with `which code`.


#### 4. Enable tab completions

You can enable CLI tab completion for Bash, Fish, or Zsh. 


> After modifying `.rc` files for your shell, you may have to restart the shell to enable completions. 
##### Zsh

```zsh
_PYBS_COMPLETE=zsh_source pybs > ~/.zsh/pybs-complete.zsh
```
> NOTE: you may have to add `source ` to your `~/.zshrc` if this does not work.  


##### Oh My Zsh 

```zsh
mkdir $ZSH_CUSTOM/plugins/pybs
pybs completions zsh > $ZSH_CUSTOM/plugins/pybs/_pybs
```
You must then add `pybs` to your plugins array in `~/.zshrc`:

```zsh
plugins(
	pybs
	...
)
```
##### Bash 
```bash
_PYBS_COMPLETE=bash_source pybs > ~/.pybs-complete.bash
```
Add the following to your `~/.bashrc`:
```bash
. ~/.pybs-complete.bash
```
#### Fish 
```fish
_PYBS_COMPLETE=fish_source pybs > ~/.config/fish/completions/pybs.fish
```
#### 5. Create job script 

To use the `code` command to launch a VS code instance on a compute node, you will need to create a
PBS-compatible job script with a `sleep infinity` command or similar to prevent early exiting of the
job script.  

##### Example job script 

```bash
#! /usr/bin/env bash

#PBS -I 
#PBS -l select=1:ncpus=6:ngpus=1:mem=46gb
#PBS -l walltime=4:00:00
#PBS -M YOUR_EMAIL_ADDRESS
#PBS -m ae
#PBS -j oe

sleep infinity
```


Then, you can run `code` as follows: 

```bash
pybs code YOUR_SERVER_NAME '$HOME/path/to/notebook.ipynb' path/to/job_script.pbs 
```

