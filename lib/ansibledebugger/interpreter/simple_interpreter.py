
import cmd
import re
import readline
import sys

from ansibledebugger.interpreter import NextAction


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

    def do_show_module_args(self, arg):
        """Show a module name and its args. If *args* keyword is used in your task, use *show_complex_args* to see the keyword's arguments. """
        print 'module_name: %s' % (self.task_info.module_name)
        print 'module_args: %s' % (self.task_info.module_args)

    def do_set_module_args(self, arg):
        """Set args to a module. If the arg already exists, it is replaced.
        Usage: set_module_args <key=value>
        """
        if arg is None or '=' not in arg[1:-1]:
            print 'Invalid option. See help for usage.'
        else:
            split_arg = arg.split('=')
            key = split_arg[0]
            value = split_arg[1]

            module_args = self.task_info.module_args
            match = re.search(r'(\A| )%s=[^ ](\Z| )' % (key), module_args)
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

            print 'module_args is updated: %s' % (self.task_info.module_args)

    def do_show_complex_args(self, arg):
        """Show the complex args of a module. Typically complex_args shows more complex arguments like lists and associative arrays."""
        print 'complex_args: %s' % (str(self.task_info.complex_args))

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
