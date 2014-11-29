
import cmd
import readline
import sys


class TaskInfo(object):
    """ Class to describe a target task """
    def __init__(self, module_name, module_args, vars, complex_args):
        self.module_name = module_name
        self.module_args = module_args
        self.vars = vars
        self.complex_args = complex_args


class ErrorInfo(object):
    """ Class to describe the error on a task execution. """
    def __init__(self, failed=False, reason='', result='', error=None):
        self.failed = failed
        self.reason = reason
        self.result = result
        self.error = error


class NextAction(object):
    """ The next action after an interpreter's exit. """
    REDO = 1
    CONTINUE = 2
    EXIT = 3

    def __init__(self, result=EXIT):
        self.result = result

    def set(self, result):
        self.result = result


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

    def do_show_args(self, arg):
        """Show a module name and its args.

        *module_args* shows key=value style arguments passed to the module.
        *complex_args* shows more complex arguments like lists and associative
        arrays. If *args* keyword is used in your task, arguments the *args*
        keyword contains are assigned to *complex_args*. """

        print 'module_name: %s' % (self.task_info.module_name)
        print 'module_args: %s' % (self.task_info.module_args)
        print 'complex_args: %s' % (str(self.task_info.complex_args))

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
