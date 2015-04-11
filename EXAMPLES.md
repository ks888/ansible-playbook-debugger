# Examples

### Table of Contents
* [Fix the wrong argument of a module](#example1)
* [Check variables and facts](#example2)
* [Update the entire arguments of a module](#example3)
* [Fix a wrong and complex argument](#example4)
* [Set breakpoints](#example5)
* [Check magic variables (hostvars, groups, etc.)](#example6)

<a name="example1"/>
## Fix the wrong argument of a module

In the example below, the debugger is invoked since a module's argument has undefined variable error. It updates the wrong argument, and then redoes the task.

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

TASK: [wrong variable] ********************************************************
Playbook debugger is invoked (AnsibleUndefinedVariable)
(Apdb) error
reason: AnsibleUndefinedVariable
data: None
comm_ok: None
exception: One or more undefined variables: 'wrong_var' is undefined
(Apdb) list
task name       : wrong variable
module name     : ping
module args     : data={{ wrong_var }}
complex args    : {}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     :
groups          : local
(Apdb) print var1
value1
(Apdb) set module_args data {{ var1 }}
updated: data={{ var1 }}
(Apdb) list
task name       : wrong variable
module name     : ping
module args     : data={{ var1 }}
complex args    : {}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     : 
groups          : local
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=value1
<127.0.0.1> EXEC ['/bin/sh', '-c', 'mkdir -p $HOME/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032 && chmod a+rx $HOME/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032 && echo $HOME/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032']
<127.0.0.1> PUT /tmp/tmpNTv5hy TO /home/yagami/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032/ping
<127.0.0.1> EXEC ['/bin/sh', '-c', u'LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 /usr/bin/python /home/yagami/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032/ping; rm -rf /home/yagami/.ansible/tmp/ansible-tmp-1428721740.66-54689905445032/ >/dev/null 2>&1']
ok: [testhost] => {"changed": false, "ping": "value1"}

PLAY RECAP ********************************************************************
testhost                   : ok=1    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

<a name="example2"/>
## Check variables and facts

In this example, we check the variable defined in a playbook and facts ansible collects.

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
failed: [testhost] => {"failed": true}
msg: Failed as requested from task
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) p var_in_pb
value
(Apdb) p ansible_hostname
yagami-ThinkPad-X230
(Apdb) p ansible_all_ipv4_addresses
[u'192.168.0.6', u'192.168.42.158']
(Apdb) q
aborted

~/src/ansible-playbook-debugger-demo% 
```

<a name="example3"/>
## Update the entire arguments of a module

In this example, an argument to ping module is invalid. So the entire arguments are replaced with new one.

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
failed: [testhost] => {"failed": true}
msg: unsupported parameter for module: invalid_args
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) e
reason: the task returned with a "failed" flag
data: {u'msg': u'unsupported parameter for module: invalid_args', u'failed': True, 'invocation': {'module_name': u'ping', 'module_args': u'invalid_args=v'}}
comm_ok: True
exception: None
(Apdb) l
task name       : ping with invalid module arg
module name     : ping
module args     : invalid_args=v
complex args    : {}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     : 127.0.0.1
groups          : local
(Apdb) set module_args . data=v
updated: data=v
(Apdb) l
task name       : ping with invalid module arg
module name     : ping
module args     : data=v
complex args    : {}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     : 127.0.0.1
groups          : local
(Apdb) r
<127.0.0.1> REMOTE_MODULE ping data=v
ok: [testhost] => {"changed": false, "ping": "v"}

TASK: [ping again] ************************************************************
<127.0.0.1> REMOTE_MODULE ping
ok: [testhost] => {"changed": false, "ping": "pong"}

PLAY RECAP ********************************************************************
testhost                   : ok=2    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

<a name="example4"/>
## Fix a wrong and complex argument

Ansible module has two types of arguments: module_args and complex_args. If you use key=value style to pass arguments, these are module_args. If you use key: value style, these are complex_args. It is used to represent complex structures like lists and dicts.

The playbook below describes this point.

```bash
---
p- hosts: local
  gather_facts: no
  tasks:
    - name: key1 and key2 are module_args
      some_module: key1=value1 key2=value2

    - name: key1 and key2 are complex_args
      some_module:
        key1: value1
        key2: value2

    - name: key1 and key2 are complex_args
      some_module:
      args:
        key1: value1
        key2: value2

    - name: key1 is module_args and key2 is complex_args
      some_module: key1=value1
      args:
        key2: value2

```

This debugger can update complex_args as well as module_args. In the example below, complex_args has an error, and is updated.

```bash
~/src/ansible-playbook-debugger-demo% cat demo4.yml
---
- hosts: local
  gather_facts: no
  vars:
    var1: v
  tasks:
    - name: ping with invalid complex arg
      ping:
        data: "{{ var2 }}"

~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger -i inventory demo4.yml -vv

PLAY [local] ******************************************************************

TASK: [ping with invalid complex arg] *****************************************
Playbook debugger is invoked (AnsibleUndefinedVariable)
(Apdb) e
reason: AnsibleUndefinedVariable
data: None
comm_ok: None
exception: One or more undefined variables: 'var2' is undefined
(Apdb) l
task name       : ping with invalid complex arg
module name     : ping
module args     :
complex args    : {'data': '{{ var2 }}'}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     :
groups          : local
(Apdb) set complex_args data {{ var1 }}
updated: {'data': '{{ var1 }}'}
(Apdb) l
task name       : ping with invalid complex arg
module name     : ping
module args     :
complex args    : {'data': '{{ var1 }}'}
keyword         : register:None, delegate_to:None, ignore_errors:False, environment:{}, changed_when:None, failed_when:None, always_run:False
hostname        : testhost
actual host     :
groups          : local
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=v
ok: [testhost] => {"changed": false, "ping": "v"}

PLAY RECAP ********************************************************************
testhost                   : ok=1    changed=0    unreachable=0    failed=0

~/src/ansible-playbook-debugger-demo% 
```

<a name="example5"/>
## Set breakpoints

You can set breakpoints using the command line option. With this option, the debugger is invoked before running the task you specified. It will be useful when a result is not right even though `ansible-playbook` command ends as successful.

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

<a name="example6"/>
## Check magic variables (hostvars, groups, etc.)

Ansible automatically provides a few variables, as mentioned [here](http://docs.ansible.com/playbooks_variables.html#magic-variables-and-how-to-access-information-about-other-hosts). hostvars, groups, group_names, and inventory_hostname are ones of them and this example checks them. `pp` command here prints same things as `print` command, but pretty printed.

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
failed: [testhost] => {"failed": true}
msg: Failed as requested from task
Playbook debugger is invoked (the task returned with a "failed" flag)
(Apdb) print hostvars['testhost']['ansible_wlan0']['ipv4']
{u'netmask': u'255.255.255.0', u'network': u'192.168.0.0', u'address': u'192.168.0.6'}
(Apdb) pp hostvars['testhost']['ansible_wlan0']['ipv4']
{u'address': u'192.168.0.6',
 u'netmask': u'255.255.255.0',
 u'network': u'192.168.0.0'}
(Apdb) p groups
{'ungrouped': [], 'all': ['testhost'], 'local': ['testhost']}
(Apdb) pp hostvars[groups['all'][0]]['ansible_wlan0']['ipv4']
{u'address': u'192.168.0.6',
 u'netmask': u'255.255.255.0',
 u'network': u'192.168.0.0'}
(Apdb) p group_names
['local']
(Apdb) p inventory_hostname
testhost
(Apdb) q
aborted
~/src/ansible-playbook-debugger-demo% 
```
