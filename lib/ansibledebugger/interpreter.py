
import cmd
import readline
import sys


class ErrorInfo(object):
    """ Class to describe the error on a task execution. """
    def __init__(self, failed=False, reason='', msg='', error=None):
        """ *failed* is the result of a task execution.
        *reason* is the reason the task failed.
        *msg* is the hint message for debugging.
        *error* is the exception object (if exists).
        """
        self.failed = failed
        self.reason = reason
        self.msg = msg
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
    def __init__(self, return_data, error_info, next_action):
        self.intro = "The task execution failed because %s. See the message below to get more details.\n%s\nNow the playbook debugger is running..." % (error_info.reason, error_info.msg)
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

    def do_show_result(self, arg):
        """ Show the result of a task execution. """
        print self.return_data.result

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
