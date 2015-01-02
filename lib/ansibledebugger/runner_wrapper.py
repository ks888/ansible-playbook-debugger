
from functools import wraps

from ansible import errors

from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter
from ansibledebugger.return_data import ReturnDataWithoutSlots


# Since this class is similar to ActionPluginWrapper, it is possible to
# create BaseWrapper class, but it may be over-engineering.
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
        """execute *watched_func*, then check its result"""
        task_info = TaskInfo(module_name, module_args, inject, complex_args, host=host, port=port, is_chained=is_chained)
        return_data, error_info = self._run(watched_func, runner, task_info)

        while error_info.failed and not getattr(return_data, 'debugger_pass_through', False):
            next_action = self._show_interpreter(task_info, return_data, error_info)
            if next_action.result == NextAction.REDO:
                return_data, error_info = self._run(watched_func, runner, task_info)

            elif next_action.result == NextAction.CONTINUE or next_action.result == NextAction.EXIT:
                if error_info.exception is not None:
                    error_info.exception.debugger_pass_through = True
                    raise error_info.exception
                else:
                    return_data = ReturnDataWithoutSlots(return_data)
                    return_data.debugger_pass_through = True
                    break

        # outermost wrapper has to replace ReturnDataWithoutSlots with ReturnData
        if hasattr(return_data, 'original_return_data'):
            return_data = return_data.original_return_data
        return return_data

    def _run(self, run_inner, self_inner, task_info):
        try:
            return_data = run_inner(self_inner, task_info.host, task_info.module_name,
                                    task_info.module_args, task_info.vars, task_info.port,
                                    task_info.is_chained, task_info.complex_args)

            ignore_errors = task_info.vars.get('ignore_errors', False)
            error_info = self._is_failed(return_data, ignore_errors, task_info)

        except Exception, ex:
            if hasattr(ex, 'debugger_pass_through') and ex.debugger_pass_through:
                # pass through since the debugger was already invoked.
                raise ex
            return_data = None
            error_info = ErrorInfo(True, ex.__class__.__name__, None, ex)

        return return_data, error_info

    def _is_failed(self, return_data, ignore_errors, task_info):
        """Check the result of task execution. """
        failed = False
        reason = None

        result = return_data.result

        if result.get('failed', False):
            if not return_data.comm_ok:
                failed = True
                reason = '"comm_ok" flag is False'
            elif result.get('failed_when_result', False):
                if not ignore_errors:
                    failed = True
                    reason = '"failed_when_result" flag is True'
            else:
                # out of scope of this wrapper
                pass

        return ErrorInfo(failed, reason, return_data)

    def _show_interpreter(self, task_info, return_data, error_info):
        """ Show an interpreter to debug. """
        next_action = NextAction()

        Interpreter(task_info, error_info, next_action).cmdloop()
        return next_action
