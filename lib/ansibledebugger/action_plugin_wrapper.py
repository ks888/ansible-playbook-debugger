
from __future__ import absolute_import
import copy

from ansible.utils import plugins
from ansible import errors

from ansibledebugger.constants import WRAPPED_ACTION_PLUGIN_SUFFIX
from ansibledebugger.interpreter import Interpreter, ErrorInfo, NextAction


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

    def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        return_data, error_info = self._run(conn, tmp_path, module_name, module_args,
                                            inject, complex_args, **kwargs)
        while error_info.failed:
            next_action = self._show_interpreter(return_data, error_info)
            if next_action.result == NextAction.REDO:
                # update vars
                return_data, error_info = self._run(conn, tmp_path, module_name, module_args,
                                                    inject, complex_args, **kwargs)
            elif next_action.result == NextAction.CONTINUE or next_action.result == NextAction.EXIT:
                # CONTINUE and EXIT are same so far
                if error_info.error is not None:
                    raise error_info.error
                else:
                    break

        return return_data

    def _run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        try:
            return_data = self.wrapped_plugin.run(conn, tmp_path, module_name, module_args,
                                                  inject, complex_args=None, **kwargs)

            ignore_errors = inject.get('ignore_errors', False)
            error_info = self._is_failed(return_data, ignore_errors)

        except errors.AnsibleError, ae:
            return_data = None
            error_info = ErrorInfo(True, errors.AnsibleError.__name__, str(ae), ae)

        return return_data, error_info

    def _is_failed(self, return_data, ignore_errors):
        """ Check the result of task execution. If the result is *failed*,
        returns True. Note that it is unknown whether 'failed_when_result'
        is True or not, since it is evaluated after the plugin execution, so
        the value is always False here.
        """
        error_info = ErrorInfo()

        result = return_data.result
        failed = result.get('failed', False)
        failed_when_result = ('failed_when_result' in result and result['failed_when_result'])
        error_rc = (result.get('rc', 0) != 0)

        if not ignore_errors and (failed or failed_when_result or error_rc):
            if failed:
                reason = 'the task returned with a "failed" flag'
            elif failed_when_result:
                reason = '"failed_when_result" condition is met'
            elif error_rc:
                reason = 'return code is not 0'
            error_info = ErrorInfo(True, reason, str(return_data.result))

        return error_info

    def _show_interpreter(self, return_data, error_info):
        """ Show an interpreter to debug. """
        return_data_cp = copy.deepcopy(return_data)
        next_action = NextAction()

        Interpreter(return_data_cp, error_info, next_action).cmdloop()
        return next_action
