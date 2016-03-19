# ansible-playbook-debugger

*ansible-playbook-debugger* is the tool to debug a playbook. This debugger is invoked when the task in the playbook fails, and enables you to check useful debug info such as module's args, and variables. Also, you can change module's args in the debugger, and run the failed task again to make sure a bug is fixed.

NOTE: the debugger in v0.3.0 or later does not support ansible v1. If you use ansible v1, the debugger's version should be [v0.2.4 or earlier](https://github.com/ks888/ansible-playbook-debugger/tree/v0.2.4).

For example, let's run the playbook below:

```bash
- hosts: test
  strategy: debug
  gather_facts: no
  vars:
    var1: value1
  tasks:
    - name: wrong variable
      ping: data={{ wrong_var }}
```

The debugger is invoked since *wrong_var* variable is undefined. Let's change the module's args, and run the task again.

```bash
$ ansible-playbook example1.yml -i inventory

PLAY ***************************************************************************

TASK [wrong variable] **********************************************************
fatal: [54.249.1.1]: FAILED! => {"failed": true, "msg": "ERROR! 'wrong_var' is undefined"}
Debugger invoked
(debug) p result
{'msg': u"ERROR! 'wrong_var' is undefined", 'failed': True}
(debug) p task.args
{u'data': u'{{ wrong_var }}'}
(debug) task.args['data'] = '{{ var1 }}'
(debug) p task.args
{u'data': '{{ var1 }}'}
(debug) redo
ok: [54.249.1.1]

PLAY RECAP *********************************************************************
54.249.1.1               : ok=1    changed=0    unreachable=0    failed=0
```

This time, the task runs successfully!

## Installation

Make a `strategy_plugins` directory in your playbook directory, and put `debug.py` inside of it.

```
mkdir strategy_plugins
cd strategy_plugins
wget https://raw.githubusercontent.com/ks888/ansible-playbook-debugger/master/strategy_plugins/debug.py
```

### Setup

Open your playbook, and add `strategy: debug` line like this:

```
- hosts: all
  strategy: debug
  ...
```

## Usage

### Run

Run `ansible-playbook` command as usual. This debugger is invoked when the task in a playbook fails, and show `(debug)` prompt. See [Available Commands](#available-commands) to check the debugger's commands.

## Available Commands

### p *task/vars/host/result*

Print values used to execute a module.

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
}
(debug) p vars['pkg_name']
u'bash'
(debug) p host
54.249.1.1
(debug) p result
{'_ansible_no_log': False,
 'changed': False,
 u'failed': True,
 ...
 u'msg': u"No package matching 'not_exist' is available"}
```

### task.args[*key*] = *value*

Update module's argument.

If you run a playbook like this:

```
- hosts: test
  strategy: debug
  gather_facts: yes
  vars:
    pkg_name: not_exist
  tasks:
    - name: install package
      apt: name={{ pkg_name }}
```

Debugger is invoked due to wrong package name, so let's fix the module's args:

```
(debug) p task.args
{u'name': u'{{ pkg_name }}'}
(debug) task.args['name'] = 'bash'
(debug) p task.args
{u'name': 'bash'}
(debug) redo
```

Then the task runs again with new args.

### vars[*key*] = *value*

Update vars.

Let's use the same playbook above, but fix vars instead of args:

```
(debug) p vars['pkg_name']
u'not_exist'
(debug) vars['pkg_name'] = 'bash'
(debug) p vars['pkg_name']
'bash'
(debug) redo
```

Then the task runs again with new vars.

### r(edo)

Run the task again.

### c(ontinue)

Just continue.

### q(uit)

Quit from the debugger. The playbook execution is aborted.

## Contributing

Contributions are very welcome. Feel free to open an issue or create a pull request.
