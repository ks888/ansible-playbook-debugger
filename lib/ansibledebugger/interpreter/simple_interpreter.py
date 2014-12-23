
import cmd
import copy
import json
import pprint
import re
import readline
import shlex
import sys

from ansible.callbacks import display
from ansible.playbook.task import Task

from ansibledebugger.interpreter import NextAction
from ansibledebugger import utils


class Interpreter(cmd.Cmd):
    prompt = '(Apdb) '  # Ansible Playbook DeBugger

    def __init__(self, task_info, return_data, error_info, next_action):
        result_decoded = str(error_info.result).decode('unicode-escape')
        self.intro = "The task execution failed.\nreason: %s\nresult: %s\n\nNow a playbook debugger is running..." % (error_info.reason, result_decoded)

        self.task_info = task_info
        self.return_data = return_data
        self.error_info = error_info
        self.next_action = next_action
        cmd.Cmd.__init__(self)

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = " "
            self.cmdloop()

    do_h = cmd.Cmd.do_help

    def do_error(self, arg):
        """e(rror)
Show an error info.
* 'reason' is the reason the task failed,
* 'result' is the result the module returned. If the module
  throws an expception, 'result' shows the exception.
"""
        result_decoded = str(self.error_info.result).decode('unicode-escape')

        display('reason: %s' % (self.error_info.reason))
        display('result: %s' % (result_decoded))

    do_e = do_error

    def do_list(self, arg):
        """l(ist)
Show the details about this task execution.
* 'module name' is the module name the task executed.
* 'module args' is the simple key=value style args of the module.
* 'complex args' is the module's complex arguments like lists and dicts.
* 'keyword' is the list of keywords the task contains.
  Note that the list may not be complete.
* 'hostname' is the name of a host associated with the task.
  *delegate_to* keyword is not considered here.
* 'groups' is the host's groups.
* 'connection type' is the type of a connection to the host.
* 'ssh host' is the host to ssh. *delegate_to* keyword is
  considered.
* 'ssh options' is the options given to ssh command. Note that
  the options here may not be complete. Run ansible with -vvvv
  option to see the full ssh command.
"""
        template = '{0:<15} : {1}'
        display(template.format('module name', self.task_info.module_name))
        display(template.format('module args', self.task_info.module_args))
        display(template.format('complex args', self.task_info.complex_args))
        display(template.format('keyword', ', '.join(self.get_keyword_list())))

        display(template.format('hostname', self.task_info.vars.get('inventory_hostname', '')))
        groups = self.task_info.vars.get('group_names', [])
        display(template.format('groups', ','.join(groups)))

        connection_type = self.task_info.conn.__module__.split('.')[-1]
        display(template.format('connection type', connection_type))
        if connection_type == 'ssh':
            display(template.format('ssh host', self.task_info.conn.host))
            display(template.format('ssh options', self.task_info.conn.common_args))

    do_l = do_list

    def do_print(self, arg, pp=False):
        """p(rint) [arg]
Print the value of the variable *arg*.

As the special case, if *arg* is `module_name`, print the
module name. Also, if `module_args`, print the simple
key=value style args of the module, and if `complex_args`,
print the complex args like lists and dicts.

With no argument, print all the variables and its value.
"""
        if arg is None or arg == '':
            self.print_module_name(arg, pp)
            self.print_module_args(arg, pp)
            self.print_complex_args(arg, pp)
            self.print_all_vars(pp)
        else:
            if arg == 'module_name':
                self.print_module_name(arg, pp)
            elif arg == 'module_args':
                self.print_module_args(arg, pp)
            elif arg == 'complex_args':
                self.print_complex_args(arg, pp)
            else:
                self.print_var(arg, pp)

    do_p = do_print

    def do_pp(self, arg):
        """pp [arg]
Same as print command, but output is pretty printed.
"""
        self.do_print(arg, pp=True)

    def print_module_name(self, arg, pp=False):
        module_name = self.task_info.module_name
        display('module_name: %s' % (self.pformat_if_pp(module_name, pp)))

    def print_module_args(self, arg, pp=False):
        module_args = self.task_info.module_args
        display('module_args: %s' % (self.pformat_if_pp(module_args, pp)))

    def print_complex_args(self, arg, pp=False):
        complex_args = self.task_info.complex_args
        display('complex_args: %s' % (self.pformat_if_pp(complex_args, pp)))

    def print_var(self, arg, pp=False):
        value = self.task_info.vars.get(arg, 'Not defined')
        display('%s: %s' % (arg, self.pformat_if_pp(value, pp)))

    def print_all_vars(self, pp=False):
        for k, v in self.task_info.vars.iteritems():
            display('%s: %s' % (k, self.pformat_if_pp(v, pp)))

    def pformat_if_pp(self, str, pp):
        if pp:
            return pprint.pformat(str)
        return str

    def do_set(self, arg):
        """set module_args|complex_args key value
Set the argument of the module.

If the first argument is `module_args`, *key*=*value* style
argument is added to the module's args. If the key already
exists, the key is updated. Use quotes if *value* contains
space(s).

If the first argument is `complex_args`, *key* and *value*
are added to module's complex args. *key* specifies the
location where *value* should be added. *key* accepts dot
notation to specify the child of lists and/or dicts.
To update the entire complex_args, use `.` as *key*. *value*
accepts JSON format as well as simple string.
"""
        if arg is None or arg == '':
            display('Invalid option. See help for usage.')
            return

        arg_split = arg.split()
        target = arg_split[0]
        key = arg_split[1]
        index_after_target = arg.find(target) + len(target)
        index_after_key = arg.find(key, index_after_target) + len(key)
        value = arg[index_after_key:].strip()

        if target == 'module_args':
            self.set_module_args(key, value)
        elif target == 'complex_args':
            self.set_complex_args(key, value)
        else:
            display('Invalid option. See help for usage.')

    def set_module_args(self, key, value):
        module_args = self.task_info.module_args
        module_arg_list = shlex.split(module_args)

        replaced = False
        for i, arg in enumerate(module_arg_list):
            if '=' in arg and arg.split('=', 1)[0] == key:
                module_arg_list[i] = '%s=%s' % (key, value)
                replaced = True
                break

        if not replaced:
            module_arg_list.append('%s=%s' % (key, value))

        self.task_info.module_args = ' '.join(module_arg_list)

        display('updated: %s' % (self.task_info.module_args))

    def set_complex_args(self, key, value):
        if key == '.':
            key_list = []
        else:
            key_list = Interpreter.dot_str_to_key_list(key)
            if key_list is None:
                display('Failed to interpret the key')
                return

        try:
            value = json.loads(value)
            value = utils.json_dict_unicode_to_bytes(value)
        except ValueError:
            pass

        if not isinstance(value, dict) and key == '.':
            display('complex_args has to be dict.')
            return

        new_complex_args = copy.deepcopy(self.task_info.complex_args)
        parent = None
        curr = new_complex_args
        last_key = None
        for key, expected_type in key_list:
            if isinstance(curr, dict):
                parent = curr
                last_key = key
                try:
                    curr = curr[key]
                except KeyError:
                    curr = curr[key] = {}

            elif isinstance(curr, list) or isinstance(curr, str):
                try:
                    curr = curr[key]
                except TypeError:
                    curr = parent[last_key] = {}
                    curr = curr[key] = {}
                except IndexError:
                    display('Invalid Index: %s' % str(key))
                    return

                parent = parent[last_key]
                last_key = key

        if parent is None:
            new_complex_args = value
        else:
            parent[last_key] = value
        self.task_info.complex_args = new_complex_args

        display('updated: %s' % (str(self.task_info.complex_args)))

    def do_del(self, arg):
        """del module_args|complex_args key
Delete the argument of the module. The usage of the command's
arguments is almost same as set command.
"""
        if arg is None or arg == '':
            display('Invalid option. See help for usage.')
            return

        arg_split = arg.split()
        target = arg_split[0]
        key = arg_split[1]

        if target == 'module_args':
            self.del_module_args(key)
        elif target == 'complex_args':
            self.del_complex_args(key)
        else:
            display('Invalid option. See help for usage.')

    def del_module_args(self, key):
        module_args = self.task_info.module_args
        module_arg_list = shlex.split(module_args)

        deleted = False
        for i, arg in enumerate(module_arg_list):
            if '=' in arg and arg.split('=', 1)[0] == key:
                del module_arg_list[i]
                display('deleted')
                deleted = True
                break

        if not deleted:
            display('module_args does not contain the key %s' % (key))

        self.task_info.module_args = ' '.join(module_arg_list)

    def del_complex_args(self, key):
        if key == '.':
            key_list = []
        else:
            key_list = Interpreter.dot_str_to_key_list(key)
            if key_list is None:
                display('Failed to interpret the key')
                return

        new_complex_args = copy.deepcopy(self.task_info.complex_args)
        parent = None
        curr = new_complex_args
        last_key = None
        for key, expected_type in key_list:
            parent = curr
            last_key = key
            try:
                curr = curr[key]
            except (KeyError, TypeError, IndexError):
                display('Cannot access the specified element of complex_args. Invalid key: %s' % (key))
                return

        if parent is None:
            new_complex_args = {}
        else:
            del parent[last_key]
        display('deleted')

        self.task_info.complex_args = new_complex_args

    def do_redo(self, args):
        """Re-execute the task, and, if no error, continue to run the playbook.
"""
        self.next_action.set(NextAction.REDO)
        return True

    do_r = do_redo

    def do_EOF(self, line):
        display('')
        return self.do_quit(line)

    def do_quit(self, args):
        """Quit from the debugger. The playbook execution is aborted."""
        self.next_action.set(NextAction.EXIT)
        return True

    do_q = do_quit

    def do_continue(self, arg):
        """Continue without the re-execution of the task."""
        self.next_action.set(NextAction.CONTINUE)
        return True

    do_c = do_cont = do_continue

    def get_keyword_list(self):
        kw_list = []

        if not hasattr(Task, '__slots__'):
            return kw_list

        for slot in Task.__slots__:
            if slot in self.task_info.vars:
                kw = '%s:%s' % (slot, self.task_info.vars[slot])
                kw_list.append(kw)

        return kw_list

    @classmethod
    def dot_str_to_key_list(cls, dot_str):
        """Convert json accessor string in the dot notation to the list of keys.
        Each key in the the returned list includes an expected type.
        """
        pattern = re.compile(r'\A\.?(\w+)|\A\[(\d+)\]')

        key_list = []
        match = pattern.search(dot_str)
        while match is not None:
            if match.group(1) is not None:
                # dict key
                key_list.append((match.group(1), dict))
            elif match.group(2) is not None:
                # list key
                key_list.append((int(match.group(2)), list))
            else:
                break

            dot_str = dot_str[match.end():]
            match = pattern.search(dot_str)

        if dot_str == '':
            return key_list
        else:
            return None
