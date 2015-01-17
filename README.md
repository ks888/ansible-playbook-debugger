# ansible-playbook-debugger

A Debugger for Ansible Playbook

## Description

Although `Ansible` is a powerful tool for configuration management, debugging its playbook is often bothersome. One of its reasons is an error message from ansible may not include enough information for debug. For example, variables and task's keywords are not included usually. Another reason is the time it takes to run a playbook. It may take a long time, and you may need to run the playbook several times to get more details and to see that the bug is fixed.

`ansible-playbook-debugger` is the debugger to facilitate such a bothersome work. When a task fails, the debugger is invoked automatically. Then you can check the module's arguments, variables, and so on. Furthermore, you can change the module's arguments to fix a bug, and re-execute the task. If the re-execution is successful, the playbook continues to run as if there was no error.

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

After the debugger is invoked, you can issue commands for debug. For example, issue `error` command to check an error info, `print` command  to check module's args and variables, `set` command to change the module's args, and `redo` command to re-execute the task. See [Available Commands](#available-commands) to see the list of commands.

### Example: check an error, then fix a wrong argument

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

See [EXAMPLES](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md) to get more examples. Here is the table of contents:

* [Fix a wrong argument](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example1)
* [Check variables and facts](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example2)
* [Fix an undefined variable error](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example3)
* [Fix a wrong and complex argument](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4)
* [Check magic variables (hostvars, groups, etc.)](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example5)

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

## Contributing

Contributions are very welcome, including bug reports, feature requests, and English correction of documents.

If you'd like to report a bug, please include the steps to recreate the bug, and the versions of ansible-playbook-debugger, ansible, and python.

If you'd like to send a pull request, please write a test which shows that the new feature works or the bug is fixed. Take the following steps to run tests:

1. Install packages for running tests.

   `pip install -r requirements-dev.txt`

2. Run unit tests.

  `nosetests -d -v --with-coverage --cover-erase --cover-inclusive --cover-package=ansibledebugger`

3. Run integration tests.

  `nosetests -d -v -w integration`
