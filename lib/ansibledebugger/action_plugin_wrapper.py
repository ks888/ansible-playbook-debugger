
from functools import wraps

from ansible import errors

from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter
from ansibledebugger.return_data import ReturnDataWithoutSlots


class ActionPluginWrapper(object):
    """Wraps an action plugin so that a debugger is invoked when a task fails"""
    def __init__(self):
        pass

    def wrap(self, action_module):
        """Wrap run() method of ActionModule class"""
        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                return self._watch(func, *args, **kwargs)
            return inner

        setattr(action_module, 'run', wrapper(action_module.run))

    def _watch(self, run_inner, self_inner, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        """execute run() method, then check its result"""
        task_info = TaskInfo(module_name, module_args, inject, complex_args, conn=conn, tmp_path=tmp_path)
        return_data, error_info = self._run(run_inner, self_inner, task_info, **kwargs)

        while error_info.failed and not getattr(return_data, 'debugger_pass_through', False):
            next_action = self._show_interpreter(task_info, return_data, error_info)
            if next_action.result == NextAction.REDO:
                return_data, error_info = self._run(run_inner, self_inner, task_info, **kwargs)

            elif next_action.result == NextAction.CONTINUE or next_action.result == NextAction.EXIT:
                # CONTINUE and EXIT are same so far
                if error_info.exception is not None:
                    error_info.exception.debugger_pass_through = True
                    raise error_info.exception
                else:
                    return_data = ReturnDataWithoutSlots(return_data)
                    return_data.debugger_pass_through = True
                    break

        return return_data

    def _run(self, run_inner, self_inner, task_info, **kwargs_for_run):
        try:
            return_data = run_inner(self_inner, task_info.conn, task_info.tmp_path, task_info.module_name,
                                    task_info.module_args, task_info.vars,
                                    task_info.complex_args, **kwargs_for_run)

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
        if not ignore_errors:
            if result.get('failed', False):
                failed = True
                reason = 'the task returned with a "failed" flag'
            elif task_info.vars.get('failed_when', None) is None and result.get('rc', 0) != 0:
                failed = True
                reason = 'return code is not 0'

        return ErrorInfo(failed, reason, return_data)

    def _show_interpreter(self, task_info, return_data, error_info):
        """ Show an interpreter to debug. """
        next_action = NextAction()

        Interpreter(task_info, error_info, next_action).cmdloop()
        return next_action
