
from functools import wraps

from ansible import runner
from ansible.utils import plugins

from ansibledebugger import action_plugin_wrapper


def wrapped_action_plugin(plugin_list=[]):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            reload(plugins)  # flush past wrappers

            dummy_runner = runner.Runner(host_list=[])
            for plugin in plugin_list:
                action_module = plugins.action_loader.get(plugin, dummy_runner)

                wrapper = action_plugin_wrapper.ActionPluginWrapper()
                wrapper.wrap(action_module.__class__)
                action_module.__class__

            func(*args, **kwargs)

        return inner
    return wrapper
