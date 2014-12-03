
import cmd
import copy
import json
import re
import readline
import sys

from ansible.playbook.task import Task

from ansibledebugger.interpreter import NextAction
from ansibledebugger import utils


class Interpreter(cmd.Cmd):
    def __init__(self, task_info, return_data, error_info, next_action):
        self.intro = "The task execution failed.\nreason: %s\nresult: %s\n\nNow a playbook debugger is running..." % (error_info.reason, error_info.result)
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
        """e(error)
Show an error info.
* 'reason' is the reason the task failed,
* 'result' is the result the module returned. If the module
  throws an expception, 'result' shows the exception.
"""
        print 'reason: %s' % (self.error_info.reason)
        print 'result: %s' % (self.error_info.result)

    do_e = do_error

    def do_list(self, arg):
        """l(ist)
Show the info about this task execution.
* 'module name' is the module name the task executed.
* 'module args' is the key=value style args of the module.
* 'complex args' is the arguments *args* keyword contains.
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
        print template.format('module name', self.task_info.module_name)
        print template.format('module args', self.task_info.module_args)
        print template.format('complex args', self.task_info.complex_args)
        print template.format('keyword', ', '.join(self.get_keyword_list()))

        print template.format('hostname', self.task_info.vars.get('inventory_hostname', ''))
        groups = self.task_info.vars.get('group_names', [])
        print template.format('groups', ','.join(groups))

        connection_type = self.task_info.conn.__module__.split('.')[-1]
        print template.format('connection type', connection_type)
        if connection_type == 'ssh':
            print template.format('ssh host', self.task_info.conn.host)
            print template.format('ssh options', self.task_info.conn.common_args)

    do_l = do_list

    def do_show_module_args(self, arg):
        """Show a module name and its args. If *args* keyword is used in your task, use *show_complex_args* to see the keyword's arguments. """
        print 'module_name: %s' % (self.task_info.module_name)
        print 'module_args: %s' % (self.task_info.module_args)

    def do_set_module_args(self, arg):
        """Set a module's args. If the arg already exists, it is replaced.
        Usage: set_module_args <key=value>
        """
        if arg is None or '=' not in arg[1:-1]:
            print 'Invalid option. See help for usage.'
        else:
            split_arg = arg.split('=')
            key = split_arg[0]
            value = split_arg[1]

            module_args = self.task_info.module_args
            match = re.search(r'(\A| )%s=[^ ]+(\Z| )' % (key), module_args)
            if match is not None:
                index_value_start = match.start()
                index_value_end = match.end()

                new_module_args = module_args[0:index_value_start]
                # multiple spaces are better than no space
                new_module_args += ' %s=%s ' % (key, value)
                new_module_args += module_args[index_value_end:]

                self.task_info.module_args = new_module_args
            else:
                self.task_info.module_args += ' %s=%s' % (key, value)

            print 'updated: %s' % (self.task_info.module_args)

    def do_show_complex_args(self, arg):
        """Show the complex args of a module.

        complex_args is the arguments *args* keyword contains, and can express more complex
        data like lists and dicts."""
        print 'complex_args: %s' % (str(self.task_info.complex_args))
        if arg is not None and arg == 'p':
            print '...and pretty print'
            print json.dumps(self.task_info.complex_args, sort_keys=True, indent=4)

    def do_set_complex_args(self, arg):
        """Set a module's complex args.

        Usage: set_complex_args <key in dot notation> <value>

        *key* expects dot notation, which is useful to set nested element.
        As the special case, use . as *key* to update the entire complex_args.

        *value* accepts JSON format to set lists and/or dicts as well as simple string.
        """
        if arg is None or len(arg.split(' ')) < 2:
            print 'Invalid option. See help for usage.'
            return

        split_arg = arg.split(' ')
        key = split_arg[0]
        if key == '.':
            key_list = []
        else:
            key_list = Interpreter.dot_str_to_key_list(key)
            if key_list is None:
                print 'Failed to interpret the key'
                return

        try:
            raw_value = arg[len(key) + 1:]
            value = json.loads(raw_value)
            value = utils.json_dict_unicode_to_bytes(value)
        except ValueError:
            value = raw_value

        if not isinstance(value, dict) and key == '.':
            print 'complex_args has to be dict.'
            return

        new_complex_args = copy.deepcopy(self.task_info.complex_args)
        parent = None
        curr = new_complex_args
        last_key = None
        for key, expected_type in key_list:
            if not isinstance(curr, expected_type):
                print 'Can not access the specified element of complex_args. Invalid key: %s' % str(key)
                return

            try:
                parent = curr
                last_key = key
                curr = parent[key]
            except (TypeError, IndexError):
                print 'Can not access the specified element of complex_args. Invalid key: %s' % str(key)
                return
            except KeyError:
                curr = parent[key] = {}

        if parent is None:
            new_complex_args = value
        else:
            parent[last_key] = value
        self.task_info.complex_args = new_complex_args

        print 'updated: %s' % (str(self.task_info.complex_args))

    def do_show_var(self, arg):
        """Show a variable.

        usage: show_var *variable*
        """
        if arg is None or arg == '':
            print 'Invalid option. See help for usage.'
        else:
            value = self.task_info.vars.get(arg, 'Not defined')
            print '%s: %s' % (arg, value)

    def do_show_all_vars(self, arg):
        """Show all variables. """
        for k, v in self.task_info.vars.iteritems():
            print '%s: %s' % (k, v)

    def do_show_host(self, arg):
        """Show a host info. """
        print 'hostname: %s' % (self.task_info.vars.get('inventory_hostname', ''))

        groups = self.task_info.vars.get('group_names', [])
        print 'host\'s groups: %s' % (','.join(groups))

    def do_show_ssh_option(self, arg):
        """Show options given to ssh command. Not available if a connection type is not ssh.
        """
        connection_type = self.task_info.conn.__module__.split('.')[-1]
        if connection_type == 'ssh':
            print 'ssh host: %s' % (self.task_info.conn.host)
            print 'ssh options: %s' % (self.task_info.conn.common_args)
            print '\nHint: to see the complete ssh command, run ansible with -vvvv option.'
        else:
            print 'Not available since the connection type is not ssh'

    def do_show_error(self, arg):
        """Show an error info. """
        print 'reason: %s' % (self.error_info.reason)
        print 'result: %s' % (self.error_info.result)

    def do_redo(self, args):
        self.next_action.set(NextAction.REDO)
        return True

    def do_EOF(self, line):
        sys.stdout.write('\n')
        self.next_action.set(NextAction.EXIT)
        return True

    def do_exit(self, args):
        self.next_action.set(NextAction.EXIT)
        return True

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
