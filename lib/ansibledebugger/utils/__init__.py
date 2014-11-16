
import inspect
import os

from ansible import errors


def read_module_file(module):
    """ Read the content of the file to which *module* object specifies. """
    src_path = inspect.getsourcefile(module)

    if os.path.exists(src_path):
        with open(src_path) as file:
            module_data = file.read()
    else:
        if hasattr(module_obj, '__loader__') and hasattr(module_obj.__loader__, 'get_data'):
            module_data = module_obj.__loader__.get_data('ansibledebugger/action_plugin_wrapper.py')

        else:
            raise errors.AnsibleError("Failed to load %s module's file" % (module_obj.__name__))

    return module_data


def replace_plugin(plugin, plugin_wrapper, replaced_plugin_dir):
    """ Replace *plugin* module to *plugin_wrapper* module in the
    *replaced_plugin_dir* directory.
    In *replaced_plugin_dir*, the file name of *plugin_wrapper* is that of
    *plugin*. Instead, the original *plugin*'s file name has '_internal' suffix
    so that *plugin_wrapper* is able to call *plugin*.
    """
    plugin_name = plugin.__name__.split('.')[-1]
    plugin_data = read_module_file(plugin)
    plugin_file_path = os.path.join(replaced_plugin_dir,
                                    plugin_name + '_internal.py')

    with open(plugin_file_path, 'w') as file:
        file.write(plugin_data)

    wrapper_name = plugin_name
    wrapper_data = read_module_file(plugin_wrapper)
    wrapper_plugin_file_path = os.path.join(replaced_plugin_dir,
                                            wrapper_name + '.py')

    with open(wrapper_plugin_file_path, 'w') as file:
        file.write(wrapper_data)
