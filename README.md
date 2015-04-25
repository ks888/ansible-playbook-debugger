# ansible-playbook-debugger

`ansible-playbook-debugger` is the tool to debug a playbook. This debugger is invoked when the task in the playbook fails, and enables you to check actually used module's args, variables, facts, and so on. Also, you can fix module's args in the debugger, and re-run the failed task (and if it is successful, the remaining part of the playbook runs).

For example, the task in the playbook below executes ping module, but *wrong_var* variable is undefined.

```bash
~/src/ansible-playbook-debugger-demo% cat demo3.yml 
---
- hosts: local
  gather_facts: no
  vars:
    var1: value1
  tasks:
    - name: wrong variable
      ping: data={{ wrong_var }}
```

The debugger is invoked when the task runs. You can check the error and variables, replace *wrong_var* with *var1*, and redo the task.

```bash
~/src/ansible-playbook-debugger-demo% ansible-playbook-debugger demo3.yml -i inventory -vv

PLAY [local] ****************************************************************** 

TASK: [wrong variable] ******************************************************** 
Playbook debugger is invoked (AnsibleUndefinedVariable)
(Apdb) error
reason: AnsibleUndefinedVariable
data: None
comm_ok: None
exception: One or more undefined variables: 'wrong_var' is undefined
(Apdb) print module_args
data={{ wrong_var }}
(Apdb) print wrong_var
Not defined
(Apdb) print var1
value1
(Apdb) assign module_args data={{ var1 }}
assigned: data={{ var1 }}
(Apdb) print module_args
data={{ var1 }}
(Apdb) redo
<127.0.0.1> REMOTE_MODULE ping data=value1
ok: [testhost] => {"changed": false, "ping": "value1"}

PLAY RECAP ******************************************************************** 
testhost                   : ok=1    changed=0    unreachable=0    failed=0   
~/src/ansible-playbook-debugger-demo% 
```

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

1. Replace `ansible-playbook` command with `ansible-playbook-debugger` command when you call `ansible-playbook` command in a command line.
  * Although `ansible-playbook` options are still available, `--forks` option is an exception if you setup multiple hosts. In that case, use `--forks=1` to prevent multiple debuggers from invoking.
  * As of v0.2.2, `--breakpoint TASK_NAME` option is supported. With this option, the debugger is invoked before running the task matching this name. See [EXAMPLES page](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example5) for details.

2. When the debugger is invoked, issue commands for debug. Frequently used commands are:
  * `error` or `e` command to check an error.
  * `list` or `l` command to check the details of a failed task, including a module's arguments.
  * `print variable` or `p variable` command to print a variable.
  * `assign` command to replace a module's arguments.
  * `update` command to partially update a module's arguments.
  * `redo` or `r` command to re-execute a task.
  * `quit` or `q` command to quit from the debugger.

  See [Available Commands](#available-commands) to check the list of commands.

[EXAMPLES](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md) page has actual examples to use this debugger. Here is the table of contents:

* [Fix the wrong argument of a module](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example1)
* [Check variables and facts](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example2)
* [Update the entire arguments of a module](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example3)
* [Fix a wrong and complex argument](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4)
* [Set breakpoints](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example5)
* [Check magic variables (hostvars, groups, etc.)](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example6)

If you have trouble with this debugger, ask on [the mailing list](https://groups.google.com/d/forum/ansible-playbook-debugger).

## Available Commands

### h(elp) [*command*]

Print the list of available commands if no argument is given. If a *command* is given, print the help about the command.

### e(rror)

Show an error info.

### l(ist)

Show the details about this task execution.

### p(rint) [*arg*]

Print variable *arg*.

There are some special cases:
* With no argument, print all variables.
* If *arg* is `module_name`, print the module name.
* If `module_args` or `ma`, print the key=value style arguments (module_args) of the module.
* If `complex_args` or `ca`, print the key: value style arguments (complex_args) of the module.

See [this example](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4) to know the difference between module_args and complex_args.

### pp [*arg*]

Same as print command, but output is pretty printed.

### a(ssign) *module_args|ma [key1=value1 key2=value2 ...]*

Replace module_args with new key=value pairs.

### a(ssign) *complex_args|ca [args in YAML]*

Replace complex_args with new args.

* *args in YAML* are expected to be multiline. Enter an empty line to show the end of input.
* See [this example](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4) to know the difference between module_args and complex_args.

### u(pdate) *module_args|ma [key1=value1 key2=value2 ...]*

Partially update module_args.

### u(pdate) *complex_args|ca key: [value in YAML]*

Partially update complex_args.

* *value in YAML* is expected to be multiline. Enter an empty line to show the end of input.
* complex_args may contain list or dict. If you want to update the content of these structures, use [ ] and . in a *key*. For example, `update complex_args k1.k2[0]: v2` replaces v1 in the complex_args below with v2.
```yaml
  k1:
    k2:
    - v1
```
* See [this example](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4) to know the difference between module_args and complex_args.

### set *module_args*|*complex_args* *key* *value*

*Deprecated. Use assign or update commands instead. With these commands, you can update a module's arguments using formats such as key=value and key: value (just like you do in a playbook).*

Add or update a module's argument.

If the first argument is `module_args`, *key* and *value* are added to module_args.
If `complex_args`, *key* and *value* are added to complex_args.
See [this example](https://github.com/ks888/ansible-playbook-debugger/blob/master/EXAMPLES.md#example4) to know the difference between module_args and complex_args.

As the special case, if the *key* is `.`, the entire arguments are replaced with *value*.

### del *module_args|ma|complex_args|ca key*

Delete the *key* (and its value) of *module_args* or *complex_args*.

### r(edo)

Re-execute the task, and, if no error, run the remaining part of the playbook.

If the debugger is invoked due to a breakpoint, it simply does the first-run of the task.

### c(ont(inue))

Continue without the re-execution of the task.

If the debugger is invoked due to a breakpoint, it simply does the first-run of the task.

### q(uit)

Quit from the debugger. The playbook execution is aborted.

## Contributing

Contributions are very welcome, including bug reports, idea sharing, feature requests, and English correction of documents.

If you'd like to send a pull request, it is excellent if there is a test which shows that the new feature works or the bug is fixed. Take the following steps to run tests:

1. Install packages for running tests.

  `pip install -r requirements-dev.txt`

2. Run unit tests.

  `nosetests -d -v --with-coverage --cover-erase --cover-inclusive --cover-package=ansibledebugger`

3. Run integration tests.

  `nosetests -d -v -w integration`

All tests do not make a destructive change to your system.
