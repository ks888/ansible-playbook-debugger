# ansible-playbook-debugger

`ansible-playbook-debugger` is the tool to debug a playbook. This debugger is invoked when the task in the playbook fails, and enables you to check actually used module's args, variables, facts, and so on.

NOTE: the debugger in this branch does not support ansible v1.

## Installation

Make a `strategy_plugins` directory in your playbook directory, and put `debug.py` inside of it.

```
mkdir strategy_plugins
cd strategy_plugins
wget https://raw.githubusercontent.com/ks888/ansible-playbook-debugger/support-ansible-v2/strategy_plugins/debug.py
```

### Setup

Open your playbook, and change its strategy like this:

```
- hosts: all
  strategy: debug
  tasks:
```

## Usage

### Run

Run `ansible-playbook` command as usual. This debugger is invoked when the task in the playbook fails. See [Available Commands](#available-commands) to check the debugger's commands.

## Available Commands

### p *task/args/vars/host/result*

print the several values used to execute a module. The example below shows the module's arguments:

```
(debug) p args
{u'name': u'test'}
```

### pp *task/args/vars/host/result*

Same as print command, but output is pretty printed.

### q(uit)

Quit from the debugger. The playbook execution is aborted.

## Contributing

Contributions are very welcome, including bug reports, idea sharing, feature requests, and English correction of documents.
