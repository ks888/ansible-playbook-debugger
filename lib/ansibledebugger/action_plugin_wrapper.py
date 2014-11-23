
from ansible.utils import plugins

from ansibledebugger.constants import WRAPPED_ACTION_PLUGIN_SUFFIX

class ActionModule(object):
    """ An action plugin wrapper which invokes a debugger when a task fails """
    def __init__(self, runner):
        plugin_name = self.__module__.split('.')[-1]
        wrapped_plugin_name = plugin_name + WRAPPED_ACTION_PLUGIN_SUFFIX
        wrapped_plugin = plugins.action_loader.get(wrapped_plugin_name, runner)

        self.__class__ = type(wrapped_plugin.__class__.__name__,
                              (self.__class__, wrapped_plugin.__class__), {})
        self.__dict__ = wrapped_plugin.__dict__

    def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        pass
