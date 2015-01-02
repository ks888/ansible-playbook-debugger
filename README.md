# ansible-playbook-debugger

A Debugger for Ansible Playbook

## Description

Although `Ansible` is a powerful tool for configuration management, debugging its playbook is often bothersome. One of its reasons is an error message from ansible may not include enough information for debug. For example, variables and task's keywords are not included usually. Another reason is the time it takes to run a playbook. For debug, you may need to run the playbook several times to get more details and to see that the bug is fixed.

`ansible-playbook-debugger` is the debugger to facilitate such a bothersome work. When a task fails, the debugger is invoked automatically. Then you can check the module's arguments, variables, keywords, and so on. Furthermore, you can change the module's arguments to fix a bug, and re-execute the task. If the re-execution is successful, the playbook continues to run as if there was no error.

## Demo

Here is a demo which runs a playbook, invokes the debugger (since ping module's argument is wrong), and prints the module's argument.

![Demo 1](http://i.imgur.com/O6vTvAf.gif)

Here is another demo continued from the first one. It deletes the module's wrong argument, sets the right one, re-executes the task, and continues to run the playbook.

![Demo 2](http://i.imgur.com/2YYH7F9.gif)

## Installation

For the latest release:

```
pip install ansible-playbook-debugger 
```

For the development version:

```
git clone https://github.com/ks888/ansible-playbook-debugger
pip install -e ./ansible-playbook-debugger
```

In this case, any changes to the source code will be reflected immediately.

## Usage

It is easy to use this debugguer: when you call `ansible-playbook` command in a command line, just replace `ansible-playbook` with `ansible-playbook-debugger`. `ansible-playbook-debugger` command setups things so that the debugger is invoked if a task fails, and then calls `ansible-playbook` command.

Options available for `ansible-playbook` are also available for `ansible-playbook-debugger`. `--forks` option is an exception if you setup multiple hosts. In that case, use `--forks=1` to prevent multiple debuggers from invoking.

After the debugger is invoked, you can issue commands for debug. For example, issue `error` command to check an error info, `print` command  to check module's args and variables, `set` command to change the module's args, and `redo` command to re-execute the task.

The terminal logs below are examples to use the debugger. See [Available Commands](https://github.com/ks888/ansible-playbook-debugger#available-commands) to see the list of commands.

### Example 1: a task includes a wrong argument

In this example, an argument to ping module is invalid, and the debugger is invoked. It checks the error message, deletes the wrong argument, set the new argument, then redoes the task.

```bash
~/src/ansible-playbook-debugger-demo% cat demo1.yml
---
- hosts: local
  gather_facts: no
  tasks:
    - name: ping with invalid module arg
      ping: invalid_args=v

    - name: ping again
      ping:

~/src/ansible-playbook-debugger-demo% cat inventory 
[local]
testhost ansible_ssh_host=127.0.0.1 ansible_connection=local

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo1.yml -vv      

PLAY [local] ****************************************************************** 

TASK: [ping with invalid module arg] ****************************************** 
<127.0.0.1> REMOTE_MODULE ping invalid_args=v
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) error
reason: the task returned with a "failed" flag
data: {u'msg': u'unsupported parameter for module: invalid_args', u'failed': True}
comm_ok: True
exception: None
(Apdb) print module_args
module_args: invalid_args=v
(Apdb) del module_args invalid_args
deleted
(Apdb) print module_args
module_args: 
(Apdb) set module_args data v
updated: data=v
(Apdb) print module_args
module_args: data=v
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=v
ok: [testhost] => {"changed": false, "ping": "v"}

TASK: [ping again] ************************************************************ 
<127.0.0.1> REMOTE_MODULE ping
ok: [testhost] => {"changed": false, "ping": "pong"}

PLAY RECAP ******************************************************************** 
testhost                   : ok=2    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

### Example 2: check various info

Some commands print useful info for debug. `list` command prints the details about this task execution, and `print` command (without args) prints module args, variable, keywords, and so on. This example quits from the debugger with Ctrl-d.

```bash
~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo1.yml -vv

PLAY [local] ******************************************************************

TASK: [ping with invalid module arg] ******************************************
<127.0.0.1> REMOTE_MODULE ping invalid_args=v
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) list
module name     : ping
module args     : invalid_args=v
complex args    : {}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     : 127.0.0.1
groups          : local
(Apdb) print
module_name: ping
module_args: invalid_args=v
complex_args: {}
delegate_to: None
failed_when: None
omit: __omit_place_holder__b80c1551ec6b14b0e6e8bede50d8bfaec942cb44
vars: {'delegate_to': None, 'failed_when': None, 'inventory_file': 'inventory', 'playbook_dir': '/home/yagami/src/ansible-playbook-debugger-demo', 'register': None, 'inventory_dir': '/home/yagami/src/ansible-playbook-debugger-demo', 'always_run': False, 'changed_when': None, 'role_names': [], 'play_hosts': ['testhost'], 'ignore_errors': False, 'ansible_version': {'major': 1, 'full': '1.9', 'string': '1.9\n  configured module search path = None', 'minor': 9, 'revision': 0}}
ansible_connection: local
ansible_ssh_host: 127.0.0.1
inventory_hostname: testhost
playbook_dir: /home/yagami/src/ansible-playbook-debugger-demo
environment: {}
hostvars: {'ansible_ssh_host': '127.0.0.1', 'inventory_hostname': 'testhost', 'inventory_hostname_short': 'testhost', 'ansible_connection': 'local', 'group_names': ['local']}
group_names: ['local']
combined_cache: {}
ansible_version: {'major': 1, 'full': '1.9', 'string': '1.9\n  configured module search path = None', 'minor': 9, 'revision': 0}
inventory_file: inventory
always_run: False
groups: {'ungrouped': [], 'all': ['testhost'], 'local': ['testhost']}
ignore_errors: False
changed_when: None
inventory_hostname_short: testhost
register: None
inventory_dir: /home/yagami/src/ansible-playbook-debugger-demo
ansible_ssh_user: yagami
defaults: {}
role_names: []
play_hosts: ['testhost']
(Apdb) error
reason: the task returned with a "failed" flag
data: {u'msg': u'unsupported parameter for module: invalid_args', u'failed': True}
comm_ok: True
exception: None
(Apdb)
failed: [testhost] => {"failed": true}
msg: unsupported parameter for module: invalid_args

FATAL: all hosts have already failed -- aborting

PLAY RECAP ********************************************************************
           to retry, use: --limit @/home/yagami/demo1.retry

testhost                   : ok=0    changed=0    unreachable=0    failed=1

~/src/ansible-playbook-debugger-demo% 
```

### Example 3: a variable inside template is undefined

The playbook below uses template, but the variable is not defined. It replaces the wrong template with the right one, then redoes the task.

```bash
~/src/ansible-playbook-debugger-demo% cat demo3.yml
---
- hosts: local
  gather_facts: no
  vars:
    var1: value1
  tasks:
    - name: ping with wrong template
      ping: data={{ wrong_var }}
      tags:
        - wrong_template
~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo3.yml -vv

PLAY [local] ******************************************************************

TASK: [ping with wrong template] **********************************************
Playbook debugger is invoked (AnsibleUndefinedVariable)
(Apdb) error
reason: AnsibleUndefinedVariable
data: None
comm_ok: None
exception: One or more undefined variables: 'wrong_var' is undefined
(Apdb) print module_args
module_args: data={{ wrong_var }}
(Apdb) set module_args data {{ var1 }}
updated: data={{ var1 }}
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=value1
ok: [testhost] => {"changed": false, "ping": "value1"}

PLAY RECAP ******************************************************************** 
testhost                   : ok=1    changed=0    unreachable=0    failed=0   

~/src/ansible-playbook-debugger-demo% 
```

### Example 4: complex args

A task has two types of arguments: module_args and complex_args. module_args is the simple key=value style arguments, and complex_args is used for representing complex structures like lists and dicts. In this example, complex_args includes an error, and is replaced with new one.

```bash
~/src/ansible-playbook-debugger-demo% cat demo4.yml
---
- hosts: local
  gather_facts: no
  tasks:
    - name: ping with invalid module arg
      ping:
      args:
        k: v

    - name: ping again
      ping:
~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo4.yml -vv

PLAY [local] ******************************************************************

TASK: [ping with invalid module arg] ******************************************
<127.0.0.1> REMOTE_MODULE ping k=v
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) error
reason: the task returned with a "failed" flag
data: {u'msg': u'unsupported parameter for module: k', u'failed': True}
comm_ok: True
exception: None
(Apdb) print complex_args
complex_args: {'k': 'v'}
(Apdb) set complex_args . {"data": "v"}
updated: {'data': 'v'}
(Apdb) print complex_args
complex_args: {'data': 'v'}
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=v
ok: [testhost] => {"changed": false, "ping": "v"}

TASK: [ping again] ************************************************************ 
<127.0.0.1> REMOTE_MODULE ping
ok: [testhost] => {"changed": false, "ping": "pong"}

PLAY RECAP ********************************************************************
testhost                   : ok=2    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

## Available Commands

### h(elp) [*command*]

Print the list of available commands if no argument is given. If a *command* is given, print the help about the command.

### e(rror)

Show an error info.

### l(ist)

Show the details about this task execution.

### p(rint) [*arg*]

Print the value of the variable *arg*.

As the special case, if *arg* is `module_name`, print the module name. Also, if `module_args`, print the simple key=value style args of the module, and if `complex_args`, print the complex args like lists and dicts.

With no argument, print all the variables and its value.

### pp [*arg*]

Same as print command, but output is pretty printed.

### set *module_args*|*complex_args* *key* *value*

Set the argument of the module.

If the first argument is `module_args`, *key*=*value* style argument is added to the module's args. To update the entire module_args, use `.` as *key*.

If the first argument is `complex_args`, *key* and *value* are added to module's complex args. *key* is the path to the location where *value* is added. Use dot notation to specify the child of lists and/or dicts. To update the entire complex_args, use `.` as *key*. *value* accepts JSON format as well as simple string.

### del *module_args*|*complex_args* *key*

Delete the argument of the module. The usage is almost same as set command.

### r(edo)

Re-execute the task, and, if no error, continue to run the playbook.

### c(cont(inue))

Continue without the re-execution of the task.

### q(uit)

Quit from the debugger. The playbook execution is aborted.
