
import cmd
import readline
import sys


class Interpreter(cmd.Cmd):

    def __init__(self):
        self.intro = "The task failed... Now, the playbook debugger is running."
        cmd.Cmd.__init__(self)

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            self.intro = " "
            self.cmdloop()

    def do_EOF(self, line):
        sys.stdout.write('\n')
        return True

    def do_exit(self, args):
        return True
