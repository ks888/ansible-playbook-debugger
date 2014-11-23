
import tempfile
from functools import wraps

from ansible.utils import plugins

from ansibledebugger import action_plugin_wrapper
from ansibledebugger import utils


def replaced_action_plugin(replace_plugin_list=[]):
    def replace(func):
        @wraps(func)
        def inner(*args, **kwargs):
            tempdir = tempfile.mkdtemp()
            for plugin in replace_plugin_list:
                utils.replace_plugin(plugin, action_plugin_wrapper, tempdir)
            plugins.action_loader.add_directory(tempdir)

            try:
                func(*args, **kwargs)
            finally:
                reload(plugins)
                for plugin in replace_plugin_list:
                    reload(plugin)

        return inner
    return replace
