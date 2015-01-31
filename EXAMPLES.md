# Examples

### Table of Contents
* [Fix a wrong argument](#example1)
* [Check variables and facts](#example2)
* [Fix an undefined variable error](#example3)
* [Fix a wrong and complex argument](#example4)
* [Check magic variables (hostvars, groups, etc.)](#example5)

<a name="example1"/>
## Fix a wrong argument

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

<a name="example2"/>
## Check variables and facts

In this example, we check the variable defined in a playbook and facts ansible collects. This example quits from the debugger with Ctrl-d.

```bash
~/src/ansible-playbook-debugger-demo% cat demo2.yml                  
---
- hosts: local
  vars:
    var_in_pb: value
  tasks:
    - name: somehow fail here
      fail:

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger demo2.yml -i inventory -vv

PLAY [local] ****************************************************************** 

GATHERING FACTS *************************************************************** 
<127.0.0.1> REMOTE_MODULE setup
ok: [testhost]

TASK: [somehow fail here] ***************************************************** 
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) print var_in_pb
var_in_pb: value
(Apdb) print ansible_hostname
ansible_hostname: yagami-ThinkPad-X230
(Apdb) print ansible_all_ipv4_addresses
ansible_all_ipv4_addresses: [u'192.168.0.4', u'192.168.42.170']
(Apdb) 
failed: [testhost] => {"failed": true}
msg: Failed as requested from task

FATAL: all hosts have already failed -- aborting

PLAY RECAP ******************************************************************** 
           to retry, use: --limit @/home/yagami/demo2.retry

testhost                   : ok=1    changed=0    unreachable=0    failed=1

~/src/ansible-playbook-debugger-demo% 
```

<a name="example3"/>
## Fix an undefined variable error

The playbook below uses template, but the variable is undefined. It replaces the wrong template with the right one, then redoes the task.

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

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger demo3.yml -i inventory -vv

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
(Apdb) print var1
var1: value1
(Apdb) set module_args data {{ var1 }}
updated: data={{ var1 }}
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=value1
ok: [testhost] => {"changed": false, "ping": "value1"}

PLAY RECAP ********************************************************************
testhost                   : ok=1    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

If the debugger is invoked because a template file used in the template module has an undefined variable error, fix a template file and then issue `redo` command.

<a name="example4"/>
## Fix a wrong and complex argument

A module has two types of arguments: module_args and complex_args. module_args is the simple key=value style arguments, and complex_args is used for representing complex structures like lists and dicts. In this example, complex_args includes an error, and is replaced with new one.

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

<a name="example5"/>
## Check magic variables (hostvars, groups, etc.)

Ansible automatically provides a few variables, as mentioned [here](http://docs.ansible.com/playbooks_variables.html#magic-variables-and-how-to-access-information-about-other-hosts). hostvars, groups, group_names, and inventory_hostname are ones of them and this example checks their value. `pp` command here prints same things as `print` command, but pretty printed.

```bash
~/src/ansible-playbook-debugger-demo% cat demo2.yml
---
- hosts: local
  vars:
    var_in_pb: value
  tasks:
    - name: somehow fail here
      fail:

~/src/ansible-playbook-debugger-demo% cat inventory
[local]
testhost ansible_ssh_host=127.0.0.1 ansible_connection=local

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger demo2.yml -i inventory -vv

PLAY [local] ******************************************************************

GATHERING FACTS ***************************************************************
<127.0.0.1> REMOTE_MODULE setup
ok: [testhost]

TASK: [somehow fail here] *****************************************************
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) print hostvars['testhost']['ansible_wlan0']['ipv4']
{u'netmask': u'255.255.255.0', u'network': u'192.168.0.0', u'address': u'192.168.0.4'}
(Apdb) pp hostvars['testhost']['ansible_wlan0']['ipv4']
{u'address': u'192.168.0.4',
 u'netmask': u'255.255.255.0',
 u'network': u'192.168.0.0'}
(Apdb) p groups
{'ungrouped': [], 'all': ['testhost'], 'local': ['testhost']}
(Apdb) pp hostvars[groups['all'][0]]['ansible_wlan0']['ipv4']
{u'address': u'192.168.0.4',
 u'netmask': u'255.255.255.0',
 u'network': u'192.168.0.0'}
(Apdb) p group_names
['local']
(Apdb) p inventory_hostname
testhost
(Apdb) 
failed: [testhost] => {"failed": true}
msg: Failed as requested from task

FATAL: all hosts have already failed -- aborting

PLAY RECAP ******************************************************************** 
           to retry, use: --limit @/home/yagami/demo2.retry

testhost                   : ok=1    changed=0    unreachable=0    failed=1   

~/src/ansible-playbook-debugger-demo% 
```

<a name="example6"/>
## Set breakpoints

You can set breakpoints using the command line option. With this option, the debugger is invoked before running the task you specified. It will be useful when configuration results are not right even though `ansible-playbook` command ends as successful.

The example below checks the variable in the breakpoint task.

```bash
~/src/ansible-playbook-debugger-demo% cat demo6.yml
---
- hosts: local
  gather_facts: no
  vars:
    var1: defined_in_pb
  tasks:
    - name: register new var
      set_fact:
        var1: defined_dynamically

    - name: any module
      ping:

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger demo6.yml -i inventory -vv \
% -e var1=defined_external --breakpoint="any module"

PLAY [local] ****************************************************************** 

TASK: [register new var] ****************************************************** 
ok: [testhost] => {"ansible_facts": {"var1": "defined_dynamically"}}

TASK: [any module] ************************************************************ 
Playbook debugger is invoked (breakpoint)
(Apdb) print var1
defined_external
(Apdb) continue
<127.0.0.1> REMOTE_MODULE ping
ok: [testhost] => {"changed": false, "ping": "pong"}

PLAY RECAP ******************************************************************** 
testhost                   : ok=2    changed=0    unreachable=0    failed=0   

~/src/ansible-playbook-debugger-demo% 
```