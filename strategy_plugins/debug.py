
import cmd
import pprint
import sys

from ansible.plugins.strategy import linear
from ansible.plugins.strategy import StrategyBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class StrategyModule(linear.StrategyModule, StrategyBase):
    # Usually inheriting linear.StrategyModule is enough. However, StrategyBase class must be
    # direct ancestor to be considered as strategy plugin, and so we inherit the class here.

    def _queue_task(self, host, task, task_vars, play_context):
        self.curr_host = host
        self.curr_task = task
        self.curr_task_vars = task_vars
        self.curr_play_context = play_context

        StrategyBase._queue_task(self, host, task, task_vars, play_context)

    def _process_pending_results(self, iterator, one_pass=False):
        results = super(StrategyModule, self)._process_pending_results(iterator, one_pass)
        if self._need_debug(results):
            dbg = Debugger(self, results)
            dbg.cmdloop()
        return results

    def _need_debug(self, results):
        return reduce(lambda total, res : res.is_failed() or res.is_unreachable() or total, results, False)

class Debugger(cmd.Cmd):
    prompt = '(debug) '  # debugger
    prompt_continuous = '> '  # multiple lines

    def __init__(self, strategy_module, results):
        # cmd.Cmd is old-style class
        cmd.Cmd.__init__(self)

        self.intro = "Debugger invoked"
        self.scope = {}
        self.scope['task'] = strategy_module.curr_task
        self.scope['vars'] = strategy_module.curr_task_vars['vars']
        self.scope['host'] = strategy_module.curr_host
        self.scope['result'] = results[0]._result
        self.scope['results'] = results  # for debug of this debugger

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            pass

    def do_EOF(self, args):
        return self.do_quit(args)

    def do_quit(self, args):
        display.display('aborted')
        return True

    do_q = do_quit

    def evaluate(self, args):
        try:
            return eval(args, globals(), self.scope)
        except:
            t, v = sys.exc_info()[:2]
            if isinstance(t, str):
                exc_type_name = t
            else:
                exc_type_name = t.__name__
            display.display('***%s:%s' % (exc_type_name, repr(v)))
            raise

    def do_p(self, args):
        try:
            result = self.evaluate(args)
            display.display(pprint.pformat(result))
        except:
            pass

    def default(self, line):
        self.do_p(line)
