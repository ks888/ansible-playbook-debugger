
import cmd
import copy
import json
import pprint
import re
import readline
import sys
import yaml

import ansible.utils  # unused, but necessary to avoid circular imports
from ansible import errors
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
        template = '{0:<12} : {1}'
        display(template.format('task name', self.task_info.task.name))
        display(template.format('module name', self.task_info.module_name))
        display(template.format('module args', self.task_info.module_args))

        display(template.format('complex args', ''))
        if self.task_info.complex_args != {}:
            complex_args_yaml = Interpreter.yaml_format(self.task_info.complex_args, 2)
            display('%s' % (complex_args_yaml))

        kws = self.get_keyword_list()
        kws_yaml = Interpreter.yaml_format(kws, 2)
        display(template.format('keyword', ''))
        display('%s' % (kws_yaml))

        display(template.format('hostname', self.task_info.vars.get('inventory_hostname', '')))

        host = ''
        if 'action_plugin_wrapper' in self.optional_info:
            host = self.optional_info['action_plugin_wrapper'].conn.host
        display(template.format('actual host', host))

        groups = self.task_info.vars.get('group_names', [])
        display(template.format('groups', ','.join(groups)))

    do_l = do_list

    def do_print(self, arg):
        """p(rint) [arg]
Print variable *arg*.

There are some special cases:
* With no argument, print all variables.
* If *arg* is `module_name`, print the module name.
* If `module_args` or `ma`, print the key=value style arguments of the module.
* If `complex_args` or `ca`, print the key: value style arguments of the module.
"""
        if arg is None or arg == '':
            self.print_all_vars()
        else:
            if arg == 'module_name':
                self.print_module_name(arg)
            elif arg == 'module_args' or arg == 'ma':
                self.print_module_args(arg)
            elif arg == 'complex_args' or arg == 'ca':
                self.print_complex_args(arg)
            else:
                self.print_var(arg)

    do_p = do_print

    def do_pp(self, arg):
        """pp [arg]
Same as print command, but output is pretty printed.
"""
        # Actually same as p command so far
        self.do_print(arg)

    def print_module_name(self, arg):
        display('%s' % (self.task_info.module_name))

    def print_module_args(self, arg):
        display('%s' % (self.task_info.module_args))

    def print_complex_args(self, arg):
        complex_args_yaml = Interpreter.yaml_format(self.task_info.complex_args)
        display('%s' % (complex_args_yaml))

    def print_var(self, arg):
        try:
            value = self.get_value(arg)
            value_yaml = Interpreter.yaml_format(value)
            display('%s' % (value_yaml))

        except Exception, ex:
            display('%s' % str(ex))

    def print_all_vars(self):
        for key in self.task_info.vars.iterkeys():
            try:
                value = self.get_value(key)
                value_yaml = Interpreter.yaml_format(value, 2)
                display('%s:\n%s' % (key, value_yaml))

            except Exception, ex:
                display('%s' % str(ex))

    def do_assign(self, arg):
        """assign module_args|ma|complex_args|ca ...
Replace module_args or complex_args with new values.

* To see how to replace module_args, call `help assign_module_args|assign_ma`.
* To see how to replace complex_args, call `help assign_complex_args|assign_ca`.
* Use `update` command for partial updates of module_args and/or complex_args.
"""
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

    do_a = do_assign

    def assign_module_args(self, arg):
        """assign module_args|ma [key1=value1 key2=value2 ...]
Replace module_args with new key=value pairs.

* To replace key: value style arguments, use `assign complex_args`.
"""
        self.task_info.module_args = arg
        display('assigned: %s' % (self.task_info.module_args))

    def assign_complex_args(self, arg_first):
        """assign complex_args|ca [args in YAML]
Replace complex_args with new args in YAML.

* *args in YAML* are expected to be multiline. Enter an empty line to show
  the end of input.
* To replace key=value style arguments, use `assign module_args`.
"""
        arg_rest = Interpreter.input_multiline(self.prompt_continuous)
        if arg_rest is None:
            display('cancelled')
            return

        arg_yaml = arg_first + arg_rest
        try:
            arg = ansible.utils.parse_yaml(arg_yaml)
        except errors.AnsibleError as ex:
            display('Failed to parse %s' % (arg_yaml))
            display('%s' % (ex))
            return
        except yaml.YAMLError as ex:
            display('Failed to parse YAML: %s' % ex)
            return

        if arg is None:
            # In ansible, empty complex_args becomes {}
            arg = {}

        if not isinstance(arg, dict):
            display('complex_args has to be dict.')
            return

        self.task_info.complex_args = arg

        display('assigned')

    def help_assign_module_args(self):
        display(self.assign_module_args.__doc__)

    help_assign_ma = help_assign_module_args

    def help_assign_complex_args(self):
        display(self.assign_complex_args.__doc__)

    help_assign_ca = help_assign_complex_args

    def do_update(self, arg):
        """update module_args|ma|complex_args|ca ...
Partially update module_args or complex_args.

* To see how to update module_args, call `help update_module_args|update_ma`.
* To see how to update complex_args, call `help update_complex_args|update_ca`.
* Use `assign` command to totally replace module_args and/or complex_args.
"""
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
            self.update_module_args(rest)
        elif args_type == 'complex_args' or args_type == 'ca':
            self.update_complex_args(rest)
        else:
            display('Invalid option. See help for usage.')

    do_u = do_update

    def update_module_args(self, arg):
        """update module_args|ma [key1=value1 key2=value2 ...]
Partially update module_args.

* To totally replace module_args, use `assign module_args`.
* To update key: value style arguments, use `update complex_args`.
"""
        module_args = self.task_info.module_args
        try:
            module_args_list = utils.split_args(module_args)
            new_args_list = utils.split_args(arg)
        except Exception as ex:
            display('%s' % str(ex))
            return

        for new_arg in new_args_list:
            new_arg_split = new_arg.split('=', 1)
            if len(new_arg_split) <= 1:
                display('skipped non key=value argument (%s)' % new_arg)
                continue

            new_arg_key = new_arg_split[0]
            new_arg_value = new_arg_split[1]

            replaced = False
            for i, module_arg in enumerate(module_args_list):
                module_arg_key = module_arg.split('=', 1)[0]
                quoted = module_arg.startswith('"') and module_arg.endswith('"') or \
                    module_arg.startswith("'") and module_arg.endswith("'")

                if '=' in module_arg and not quoted and module_arg_key == new_arg_key:
                    module_args_list[i] = '%s=%s' % (new_arg_key, new_arg_value)
                    replaced = True
                    break

            if not replaced:
                module_args_list.append('%s=%s' % (new_arg_key, new_arg_value))

        self.task_info.module_args = ' '.join(module_args_list)
        display('updated: %s' % (self.task_info.module_args))

    def update_complex_args(self, arg):
        """update complex_args|ca key: [value in YAML]
Partially update complex_args.

* *value in YAML* is expected to be multiline. Enter an empty line to show
  the end of input.
* complex_args may contain list and/or dict. Use [] and . in a *key* to specify
  the content of these structures.
* To totally replace complex_args, use `assign complex_args`.
"""
        arg_rest = Interpreter.input_multiline(self.prompt_continuous)
        if arg_rest is None:
            display('cancelled')
            return

        arg_split = arg.split(':', 1)
        key = arg_split[0]
        if len(arg_split) >= 2:
            value_yaml = arg_split[1].lstrip() + arg_rest
        else:
            value_yaml = arg_rest

        key_list = Interpreter.dot_str_to_key_list(key)
        if key_list is None or key_list == []:
            display('Failed to interpret the key (%s)' % key)
            return

        try:
            value = ansible.utils.parse_yaml(value_yaml)
        except errors.AnsibleError as ex:
            display('Failed to parse %s' % (value_yaml))
            display('%s' % (ex))
            return
        except yaml.YAMLError as ex:
            display('Failed to parse YAML: %s' % ex)
            return

        curr = self.task_info.complex_args
        for key, expected_type in key_list[:-1]:
            if expected_type == dict and isinstance(curr, dict) and key in curr:
                curr = curr[key]
            elif expected_type == list and isinstance(curr, list) and key < len(curr):
                curr = curr[key]
            else:
                display('Invalid key: %s' % key)
                return

        last_key = key_list[-1]
        last_key_name = last_key[0]
        last_key_type = last_key[1]
        if last_key_type == dict and isinstance(curr, dict):
            curr[last_key_name] = value

        elif last_key_type == list and isinstance(curr, list):
            if last_key_name < len(curr):
                curr[last_key_name] = value
            elif last_key_name == len(curr):
                curr.append(value)
            else:
                display('Invalid key: %s' % key)
                return

        else:
            display('Invalid key: %s' % last_key_name)
            return

        display('updated')

    def help_update_module_args(self):
        display(self.update_module_args.__doc__)

    help_update_ma = help_update_module_args

    def help_update_complex_args(self):
        display(self.update_complex_args.__doc__)

    help_update_ca = help_update_complex_args

    def do_set(self, arg):
        """set module_args|complex_args key value
Add or update the module's argument.

If the first argument is `module_args`, *key* and *value* are added to module_args.

If `complex_args`, *key* and *value* are added to complex_args.

As the special case, if the *key* is `.`, the entire arguments are replaced
with *value*.
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
        display('WARNING: `set module_args` is deprecated. Use `update module_args` instead.')

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
        display('WARNING: `set complex_args` is deprecated. Use `update complex_args` instead.')

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
        """del module_args|ma|complex_args|ca key
Delete the argument of the module. The usage is almost same
as set command.
"""
        if arg is None or arg == '' or len(arg.split()) != 2:
            display('Invalid option. See help for usage.')
            return

        arg_split = arg.split()
        target = arg_split[0]
        key = arg_split[1]

        if target == 'module_args' or target == 'ma':
            self.del_module_args(key)
        elif target == 'complex_args' or target == 'ca':
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
        kws = {}

        if not hasattr(Task, '__slots__'):
            return kws

        for slot in Task.__slots__:
            if slot in self.task_info.vars:
                try:
                    value = self.get_value(slot)
                    kws[slot] = value

                except Exception:
                    pass

        return kws

    def get_value(self, varname):
        """Get a variable's value by applying a template.
        If the value is dict or list, *varname* may include '.' or '[]'
        to get the content of dict or list.
        * For example, if the value of variable "var" is {"k": "v"},
          get_value("var.k") will return "v".
        """
        value = template.template('.', '{{ %s }}' % varname, self.task_info.vars)
        if '{{' in value:
            value = 'Not defined'
        return value

    @classmethod
    def input_multiline(cls, prompt):
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

    @classmethod
    def yaml_format(cls, data, head_indent=0):
        """format *data* as yaml. *head_indent* indicates the number of
        spaces at the head of each line.
        """
        data_yaml = yaml.safe_dump(data, default_flow_style=False)
        # remove confusing ... line, and the last line break
        data_yaml = data_yaml.replace('...\n', '')[:-1]

        indent = ' ' * head_indent
        data_yaml = indent + data_yaml.replace('\n', '\n' + indent)

        return data_yaml

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
