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

### p *task/vars/host/result*

print values used to execute a module.

```
(debug) p task
TASK: install package
(debug) p task.args
{u'name': u'{{ pkg_name }}'}
(debug) p vars
{u'ansible_all_ipv4_addresses': [u'172.31.6.88'],
 u'ansible_all_ipv6_addresses': [u'fe80::497:a8ff:fe70:d9'],
 u'ansible_architecture': u'x86_64',
 ...
 u'pkg_name': u'not_exist',
 ...
}
(debug) p host
54.249.1.1
(debug) p result
{'_ansible_no_log': False,
 'changed': False,
 u'failed': True,
 ...
 u'msg': u"No package matching 'not_exist' is available"}
```

### q(uit)

Quit from the debugger. The playbook execution is aborted.

## Contributing

Contributions are very welcome, including bug reports, idea sharing, feature requests, and English correction of documents.
