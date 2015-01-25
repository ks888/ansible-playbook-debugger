
from functools import wraps

from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter


class RunnerWrapper(object):
    """Wraps a part of Runner class so that a debugger is invoked when a task fails"""

    def __init__(self, action_plugin_wrapper, breakpoint_task_list=[]):
        self.action_plugin_wrapper = action_plugin_wrapper
        self.breakpoint_task_list = breakpoint_task_list

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
        task_info = TaskInfo(module_name, module_args, inject, complex_args, host=host, port=port, is_chained=is_chained, task=runner.callbacks.task)

        if task_info.task is not None and self._is_breakpoint_task(task_info.task):
            return_data = None
            error_info = ErrorInfo(False, 'breakpoint', None, None)
            next_action = self._show_interpreter(task_info, return_data, error_info)
            if next_action.result == NextAction.EXIT:
                exit(1)

        return_data, error_info = self._run(watched_func, runner, task_info)

        while error_info.failed:
            next_action = self._show_interpreter(task_info, return_data, error_info)
            if next_action.result == NextAction.REDO:
                return_data, error_info = self._run(watched_func, runner, task_info)

            elif next_action.result == NextAction.CONTINUE:
                if error_info.exception is not None:
                    raise error_info.exception
                else:
                    break
            elif next_action.result == NextAction.EXIT:
                exit(1)

        return return_data

    def _is_breakpoint_task(self, curr_task):
        for breakpoint_taskname in self.breakpoint_task_list:
            if breakpoint_taskname == curr_task.name:
                return True

        return False

    def _run(self, run_inner, self_inner, task_info):
        self.action_plugin_wrapper.reset_data()
        try:
            return_data = run_inner(self_inner, task_info.host, task_info.module_name,
                                    task_info.module_args, task_info.vars, task_info.port,
                                    task_info.is_chained, task_info.complex_args)

            ignore_errors = task_info.vars.get('ignore_errors', False)
            error_info = self._is_failed(return_data, ignore_errors, task_info)

        except Exception, ex:
            return_data = None
            error_info = ErrorInfo(True, ex.__class__.__name__, None, ex)

        return return_data, error_info

    def _is_failed(self, return_data, ignore_errors, task_info):
        """Check the result of task execution. """
        failed = False
        reason = None

        result = return_data.result

        if not return_data.comm_ok:
            failed = True
            reason = '"comm_ok" flag is False'
            return ErrorInfo(failed, reason, return_data)

        if not ignore_errors:
            if 'failed_when_result' in result:
                if result.get('failed_when_result'):
                    failed = True
                    reason = '"failed_when_result" flag is True'

            else:
                if result.get('rc', 0) != 0:
                    failed = True
                    reason = 'return code is not 0'

                elif result.get('failed', False):
                    failed = True
                    reason = 'the task returned with a "failed" flag'

        return ErrorInfo(failed, reason, return_data)

    def _show_interpreter(self, task_info, return_data, error_info):
        """ Show an interpreter to debug. """
        next_action = NextAction()

        optional_info = {}
        if self.action_plugin_wrapper.task_info is not None:
            optional_info['action_plugin_wrapper'] = self.action_plugin_wrapper.task_info
        Interpreter(task_info, error_info, next_action, optional_info=optional_info).cmdloop()
        return next_action
