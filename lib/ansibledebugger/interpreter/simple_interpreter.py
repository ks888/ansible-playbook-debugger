
import cmd
import copy
import json
import pprint
import re
import readline
import sys

import ansible.utils  # unused, but necessary to avoid circular imports
from ansible.utils import template
from ansible.callbacks import display
from ansible.playbook.task import Task

from ansibledebugger.interpreter import NextAction
from ansibledebugger import utils


class Interpreter(cmd.Cmd):
    prompt = '(Apdb) '  # Ansible Playbook DeBugger
    prompt_continuous = '> '  # used when multiple lines are expected

    def __init__(self, task_info, error_info, next_action, optional_info={}):
        self.intro = "Playbook debugger is invoked (%s)" % error_info.reason
        self.task_info = task_info
        self.error_info = error_info
        self.next_action = next_action
        self.optional_info = optional_info

        cmd.Cmd.__init__(self)

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = " "
            self.cmdloop()

    def input_multiline(self, prompt):
        """repetitively read a line from input until an empty line comes."""
        lines = ''
        while True:
            try:
                line = raw_input(prompt)
            except (EOFError, KeyboardInterrupt):
                return None

            lines += '\n' + line
            if line == '':
                break

        return lines

    do_h = cmd.Cmd.do_help

    def do_error(self, arg):
        """e(rror)
Show an error info.
* 'reason' is the reason the task failed,
* 'data' is the data the module returned.
* 'comm_ok' is the comm_ok flag the playbook runner returned.
* 'excpetion' is the exception from the playbook runner.
"""
        data = None
        comm_ok = None
        if self.error_info.return_data:
            data = str(self.error_info.return_data.result).decode('unicode-escape')
            comm_ok = self.error_info.return_data.comm_ok

        exception = str(self.error_info.exception)

        display('reason: %s' % (self.error_info.reason))
        display('data: %s' % (data))
        display('comm_ok: %s' % (comm_ok))
        display('exception: %s' % (exception))

    do_e = do_error

    def do_list(self, arg):
        """l(ist)
Show the details about this task execution.
* 'module name' is the module name the task executed.
* 'module args' is the key=value style arguments of the module.
* 'complex args' is the key: value style arguments of the module.
* 'keyword' is the list of keywords the task contains.
  Note that the list may not be complete.
* 'hostname' is the target host.
  *delegate_to* keyword is not considered here.
* 'actual host' is the target host. *delegate_to* keyword is considered.
* 'groups' is the host's groups.
"""
        template = '{0:<15} : {1}'
        display(template.format('task name', self.task_info.task.name))
        display(template.format('module name', self.task_info.module_name))
        display(template.format('module args', self.task_info.module_args))
        display(template.format('complex args', self.task_info.complex_args))
        display(template.format('keyword', ', '.join(self.get_keyword_list())))

        display(template.format('hostname', self.task_info.vars.get('inventory_hostname', '')))

        host = ''
        if 'action_plugin_wrapper' in self.optional_info:
            host = self.optional_info['action_plugin_wrapper'].conn.host
        display(template.format('actual host', host))

        groups = self.task_info.vars.get('group_names', [])
        display(template.format('groups', ','.join(groups)))

    do_l = do_list

    def do_print(self, arg, pp=False):
        """p(rint) [arg]
Print variable *arg*.

There are some special cases:
* With no argument, print all variables.
* If *arg* is `module_name`, print the module name.
* If `module_args`, print the key=value style arguments of the module.
* If `complex_args`, print the key: value style arguments of the module.
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
        display('%s' % (self.pformat_if_pp(module_name, pp)))

    def print_module_args(self, arg, pp=False):
        module_args = self.task_info.module_args
        display('%s' % (self.pformat_if_pp(module_args, pp)))

    def print_complex_args(self, arg, pp=False):
        complex_args = self.task_info.complex_args
        display('%s' % (self.pformat_if_pp(complex_args, pp)))

    def print_var(self, arg, pp=False):
        try:
            value = template.template('.', '{{ %s }}' % arg, self.task_info.vars)
            if '{{' in value:
                value = 'Not defined'
        except Exception, ex:
            value = str(ex)

        display('%s' % (self.pformat_if_pp(value, pp)))

    def print_all_vars(self, pp=False):
        for k, v in self.task_info.vars.iteritems():
            display('%s: %s' % (k, self.pformat_if_pp(v, pp)))

    def pformat_if_pp(self, str, pp):
        if pp:
            return pprint.pformat(str)
        return str

    def do_assign(self, arg):
        if arg is None or arg == '':
            display('Invalid option. See help for usage.')
            return

        arg_split = arg.split(None, 1)
        args_type = arg_split[0]
        if len(arg_split) >= 2:
            rest = arg_split[1]
        else:
            rest = ''

        if args_type == 'module_args' or args_type == 'ma':
            self.assign_module_args(rest)
        elif args_type == 'complex_args' or args_type == 'ca':
            self.assign_complex_args(rest)
        else:
            display('Invalid option. See help for usage.')

    def assign_module_args(self, arg):
        self.task_info.module_args = arg
        display('assigned: %s' % (self.task_info.module_args))

    def assign_complex_args(self, arg_first):
        arg_rest = self.input_multiline(self.prompt_continuous)
        if arg_rest is None:
            print 'cancelled'
            return

        arg_yaml = arg_first + arg_rest
        arg = ansible.utils.parse_yaml(arg_yaml)
        if arg is None:
            # arg_yaml is effectively empty
            arg = {}

        if not isinstance(arg, dict):
            display('complex_args has to be dict.')
            return

        self.task_info.complex_args = arg

        display('assigned')

    def do_set(self, arg):
        """set module_args|complex_args key value
Add or update the module's argument.

If the first argument is `module_args`, *key* and *value* are added to module_args.

If `complex_args`, *key* and *value* are added to complex_args.

As the special case, if the *key* is `.`, the entire arguments are replaced with *value*.
"""
        if arg is None or arg == '' or len(arg.split()) < 2:
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
        print 'WARNING: `set module_args` is deprecated. Use `update module_args` instead.'

        if key == '.':
            self.task_info.module_args = value
        else:
            module_args = self.task_info.module_args
            try:
                module_args_list = utils.split_args(module_args)
                _ = utils.split_args(value)
            except Exception as ex:
                display('%s' % str(ex))
                return

            replaced = False
            for i, arg in enumerate(module_args_list):
                quoted = arg.startswith('"') and arg.endswith('"') or arg.startswith("'") and arg.endswith("'")
                if '=' in arg and not quoted and arg.split('=', 1)[0] == key:
                    module_args_list[i] = '%s=%s' % (key, value)
                    replaced = True
                    break

            if not replaced:
                module_args_list.append('%s=%s' % (key, value))

            self.task_info.module_args = ' '.join(module_args_list)

        display('updated: %s' % (self.task_info.module_args))

    def set_complex_args(self, key, value):
        print 'WARNING: `set complex_args` is deprecated. Use `update complex_args` instead.'

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
Delete the argument of the module. The usage is almost same
as set command.
"""
        if arg is None or arg == '' or len(arg.split()) != 2:
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
        if key == '.':
            self.task_info.module_args = ''
            display('deleted')
        else:
            module_args = self.task_info.module_args
            try:
                module_args_list = utils.split_args(module_args)
            except Exception as ex:
                display('%s' % str(ex))
                return

            deleted = False
            for i, arg in enumerate(module_args_list):
                quoted = arg.startswith('"') and arg.endswith('"') or arg.startswith("'") and arg.endswith("'")
                if '=' in arg and not quoted and arg.split('=', 1)[0] == key:
                    del module_args_list[i]
                    display('deleted')
                    deleted = True
                    break

            if not deleted:
                display('module_args does not contain the key %s' % (key))
                return

            self.task_info.module_args = ' '.join(module_args_list)

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
        display('aborted')
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
