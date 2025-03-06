# PyBS


## Installation 

`pip install pythonpbs` 

## SSH Configuration 

OpenSSH 

```
Host *
	ControlMaster auto
	ControlPath ~/.ssh/controlmasters/%r@%h:%p
	ControlPersist yes

```
Create directory 
```bash
mkdir -p ~/.ssh/controlmasters
```

## VScode

To use the `launch` command, you will need to have `VS code` added to your `$PATH`. 
#### Using command palette 

In VS code, open the **command palette** (`Cmd+Shift+P`), type "shell command",
and run the `Shell Command: Install 'code' command in PATH` command.
#### Manually configure the path 

##### Zsh 

```zsh
cat << EOF >> ~/.zprofile
# Add Visual Studio Code (code)
export PATH="\$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
EOF
```
##### Bash
```bash
cat << EOF >> ~/.bash_profile
# Add Visual Studio Code (code)
export PATH="\$PATH:/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
EOF
```
Restart your shell to register your changes.  You can check with `which code`.
### Enable tab completion for Bash, Fish, or Zsh


> After modifying `.rc` files for your shell, you may have to restart the shell to enable completions. 
#### Zsh

```zsh
_PYBS_COMPLETE=zsh_source pybs > ~/.zsh/pybs-complete.zsh
```
> NOTE: you may have to add `source ` to your `~/.zshrc` if this does not work.  


#### Oh My Zsh 

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
#### Bash 
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
