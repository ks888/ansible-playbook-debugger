
from functools import wraps

from ansible import runner
from ansible.utils import plugins

from ansibledebugger.action_plugin_wrapper import ActionPluginWrapper
from ansibledebugger.runner_wrapper import RunnerWrapper


def wrapped_action_plugin(plugin_list=[]):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            reload(plugins)  # flush past wrappers

            dummy_runner = runner.Runner(host_list=[])
            wrapper = ActionPluginWrapper()
            for plugin in plugin_list:
                action_module = plugins.action_loader.get(plugin, dummy_runner)
                wrapper.wrap(action_module.__class__)

            func(*args, **kwargs)

        return inner
    return wrapper
