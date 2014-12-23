# ansible-playbook-debugger

A Debugger for Ansible Playbook

## Description

Although `Ansible` is a powerful tool for configuration management, debugging its playbook is often bothersome. Running a playbook takes time, and if the playbook contains a bug, you may need to rerun it several times. Also, when the playbook fails, you may not get a kind error message.

`ansible-playbook-debugger` is the debugger to facilitate such a bothersome work. When a task fails, the debugger is invoked automatically. Then you can check the module's arguments, variables, keywords, and so on. Furthermore, you can change the module's arguments to fix a bug, and re-execute the task. If the re-execution is successful, the playbook continues to run as if there was no error.

## Demo

Here is a demo which runs a playbook, invokes the debugger (since ping module's argument is wrong), and prints the module's argument.

Here is another demo continued from the first one. It deletes the module's wrong argument, sets the right one, re-executes the task, and continues to run the playbook.

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

It is easy to use this debugguer: when you call `ansible-playbook` command in a command line, just replace `ansible-playbook` with `ansible-playbook-debugger`. Then, the debugger will be invoked if a task fails. Options available for `ansible-playbook` are also available for `ansible-playbook-debugger`.

The terminal logs below are examples to use the debugger for debugging a playbook.

### Example 1: check and change module's args

Doing the same thing as the demo above.

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
The task execution failed.
reason: the task returned with a "failed" flag
result: {u'msg': u'unsupported parameter for module: invalid_args', u'failed': True}

Now a playbook debugger is running...
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

### Example 2: check and change module's complex args

You can change module's complex arguments like lists and dicts.

```bash
~/src/ansible-playbook-debugger-demo% cat demo2.yml 
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

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo2.yml -vv

PLAY [local] ****************************************************************** 

TASK: [ping with invalid module arg] ****************************************** 
<127.0.0.1> REMOTE_MODULE ping k=v
The task execution failed.
reason: the task returned with a "failed" flag
result: {u'msg': u'unsupported parameter for module: k', u'failed': True}

Now a playbook debugger is running...
(Apdb) print module_args
module_args: 
(Apdb) print complex_args
complex_args: {'k': 'v'}
(Apdb) set complex_args k v2
updated: {'k': 'v2'}
(Apdb) print complex_args
complex_args: {'k': 'v2'}
(Apdb) set complex_args new_k v
updated: {'k': 'v2', 'new_k': 'v'}
(Apdb) print complex_args
complex_args: {'k': 'v2', 'new_k': 'v'}
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

### Example 3: check various info

Some commands print useful info for debug, including variables, keywords, host info, and so on.

```bash
~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo2.yml -vv

PLAY [local] ****************************************************************** 

TASK: [ping with invalid module arg] ****************************************** 
<127.0.0.1> REMOTE_MODULE ping k=v
The task execution failed.
reason: the task returned with a "failed" flag
result: {u'msg': u'unsupported parameter for module: k', u'failed': True}

Now a playbook debugger is running...
(Apdb) list
module name     : ping
module args     : 
complex args    : {'k': 'v'}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
groups          : local
connection type : local
(Apdb) print
module_name: ping
module_args: 
complex_args: {'k': 'v'}
delegate_to: None
failed_when: None
vars: {'delegate_to': None, 'failed_when': None, 'changed_when': None, 'playbook_dir': '.', 'register': None, 'inventory_dir': '/home/yagami/src/ansible-playbook-debugger-demo', 'always_run': False, 'role_names': [], 'play_hosts': ['testhost'], 'ignore_errors': False}
ansible_connection: local
environment: {}
inventory_hostname: testhost
playbook_dir: .
ansible_ssh_host: 127.0.0.1
hostvars: {'testhost': {}}
group_names: ['local']
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
result: {u'msg': u'unsupported parameter for module: k', u'failed': True}
(Apdb) 
failed: [testhost] => {"failed": true}
msg: unsupported parameter for module: k

FATAL: all hosts have already failed -- aborting

PLAY RECAP ******************************************************************** 
           to retry, use: --limit @/home/yagami/demo2.retry

testhost                   : ok=0    changed=0    unreachable=0    failed=1   

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

If the first argument is `module_args`, *key*=*value* style argument is added to the module's args. If the key already exists, the key is updated. Use quotes if *value* contains space(s).

If the first argument is `complex_args`, *key* and *value* are added to module's complex args. *key* specifies the location where *value* should be added. *key* accepts dot notation to specify the child of lists and/or dicts. To update the entire complex_args, use `.` as *key*. *value* accepts JSON format as well as simple string.

### del *module_args*|*complex_args* *key*

Delete the argument of the module. The usage of the command's arguments is almost same as set command.

### r(edo)

Re-execute the task, and, if no error, continue to run the playbook.

### c(cont(inue))

Continue without the re-execution of the task.

### q(uit)

Quit from the debugger. The playbook execution is aborted.
