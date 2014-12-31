
from functools import wraps

from ansible import errors

from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter


class RunnerWrapper(object):
    """Wraps a part of Runner class so that a debugger is invoked when a task fails"""
    def __init__(self):
        pass

    def wrap(self, runner):
        """Wrap some methods of Runner class"""
        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                return self._watch(func, *args, **kwargs)
            return inner

        setattr(runner, '_executor_internal_inner', wrapper(runner._executor_internal_inner))

    def _watch(self, watched_func, runner, host, module_name, module_args, inject, port, is_chained=False, complex_args=None):
        """execute run() method, then check its result"""
        pass
