
from ansible.utils import plugins

from ansibledebugger.constants import WRAPPED_ACTION_PLUGIN_SUFFIX
from ansibledebugger.interpreter import Interpreter


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
        returnData = self.wrapped_plugin.run(conn, tmp_path, module_name, module_args,
                                             inject, complex_args, **kwargs)
        ignore_errors = inject.get('ignore_errors', False)

        while self._is_fail(returnData, ignore_errors):
            Interpreter().cmdloop()
            # update vars

            returnData = self.wrapped_plugin.run(conn, tmp_path, module_name, module_args,
                                                 inject, complex_args, **kwargs)
            ignore_errors = inject.get('ignore_errors', False)
            ignore_errors = True

        return returnData

    def _is_fail(self, returnData, ignore_errors):
        """ Check the result of task execution. If the result is *unreachable* or
        *failed*, it returns True. Note that it is unknown whether 'failed_when_result'
        is True or not, since it is evaluated after the plugin execution, so
        the value is always False here.
        """
        result = returnData.result
        failed = result.get('failed', False)
        failed_when_result = ('failed_when_result' in result and result['failed_when_result'])
        error_rc = [result.get('rc', 0) != 0][0]

        if not ignore_errors and (failed or failed_when_result or error_rc):
            return True

        if not returnData.comm_ok:
            return True

        return False
