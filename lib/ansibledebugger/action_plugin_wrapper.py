
from __future__ import absolute_import
import copy

from ansible.utils import check_conditional, plugins
from ansible import errors

from ansibledebugger.constants import WRAPPED_ACTION_PLUGIN_SUFFIX
from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter


class ActionModule(object):
    """ An action plugin wrapper which invokes a debugger when a task fails """
    def __init__(self, runner):
        plugin_name = self.__module__.split('.')[-1]
        wrapped_plugin_name = plugin_name + WRAPPED_ACTION_PLUGIN_SUFFIX
        wrapped_plugin = plugins.action_loader.get(wrapped_plugin_name, runner)

        self.__class__ = type(wrapped_plugin.__class__.__name__,
                              (self.__class__, wrapped_plugin.__class__), {})
        self.__dict__ = wrapped_plugin.__dict__

        self.wrapped_plugin = wrapped_plugin
        self.runner = runner

    def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        task_info = TaskInfo(conn, tmp_path, module_name, module_args, inject, complex_args)
        return_data, error_info = self._run(task_info, **kwargs)

        while error_info.failed:
            next_action = self._show_interpreter(task_info, return_data, error_info)
            if next_action.result == NextAction.REDO:
                return_data, error_info = self._run(task_info, **kwargs)

            elif next_action.result == NextAction.CONTINUE or next_action.result == NextAction.EXIT:
                # CONTINUE and EXIT are same so far
                if error_info.error is not None:
                    raise error_info.error
                else:
                    break

        return return_data

    def _run(self, task_info, **kwargs_for_run):
        try:
            return_data = self.wrapped_plugin.run(task_info.conn, task_info.tmp_path, task_info.module_name,
                                                  task_info.module_args, task_info.vars,
                                                  task_info.complex_args, **kwargs_for_run)

            ignore_errors = task_info.vars.get('ignore_errors', False)
            failed_when = task_info.vars.get('failed_when', None)
            error_info = self._is_failed(return_data, ignore_errors, failed_when, task_info)

        except errors.AnsibleError, ae:
            return_data = None
            error_info = ErrorInfo(True, errors.AnsibleError.__name__, str(ae), ae)

        return return_data, error_info

    def _is_failed(self, return_data, ignore_errors, failed_when_cond, task_info):
        """Check the result of task execution. """
        failed = False
        reason = None

        result = return_data.result
        failed_flag = result.get('failed', False)
        error_rc = (result.get('rc', 0) != 0)

        if failed_when_cond is not None:
            failed_when_result, reason = self._check_failed_when(failed_when_cond, task_info, result)
        else:
            failed_when_result = False

        if not ignore_errors:
            if failed_flag:
                failed = True
                reason = 'the task returned with a "failed" flag'
            else:
                if failed_when_cond is not None:
                    if failed_when_result:
                        failed = True
                        # reason is already set
                else:
                    if error_rc:
                        failed = True
                        reason = 'return code is not 0'

        return ErrorInfo(failed, reason, str(return_data.result))

    def _check_failed_when(self, failed_when, task_info, return_data):
        """Check whether failed when condition is met."""
        # imitates ansible's Runner class, and should follow the change of the original one.
        register = task_info.vars.get('register')
        if register is not None:
            if 'stdout' in return_data:
                return_data['stdout_lines'] = return_data['stdout'].splitlines()
            task_info.vars[register] = return_data

        failed = False
        reason = None

        # only run the final checks if the async_status has finished,
        # or if we're not running an async_status check at all
        if (task_info.module_name == 'async_status' and "finished" in return_data) \
                or task_info.module_name != 'async_status':
            if failed_when is not None and 'skipped' not in return_data:
                try:
                    failed = check_conditional(failed_when, self.runner.basedir, task_info.vars,
                                               fail_on_undefined=self.runner.error_on_undefined_vars)
                    if failed:
                        reason = 'meet "failed_when" condition'
                except errors.AnsibleError as e:
                    failed = True
                    reason = str(e)

        return failed, reason

    def _show_interpreter(self, task_info, return_data, error_info):
        """ Show an interpreter to debug. """
        next_action = NextAction()

        Interpreter(task_info, return_data, error_info, next_action).cmdloop()
        return next_action
