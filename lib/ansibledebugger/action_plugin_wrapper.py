
from functools import wraps

from ansibledebugger.interpreter import TaskInfo


class ActionPluginWrapper(object):
    """Wraps an action plugin so that necessary debug info is passed to RunnerWrapper"""
    def __init__(self):
        self.reset_data()

    def wrap(self, action_module):
        """Wrap run() method of ActionModule class"""
        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                return self._watch(func, *args, **kwargs)
            return inner

        setattr(action_module, 'run', wrapper(action_module.run))

    def _watch(self, run_inner, self_inner, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        """set Task Info for a debugger"""
        if self.is_reset:
            self.task_info = TaskInfo(module_name, module_args, inject, complex_args,
                                      conn=conn, tmp_path=tmp_path)
            self.is_reset = False

        return run_inner(self_inner, conn, tmp_path, module_name, module_args,
                         inject, complex_args, **kwargs)

    def reset_data(self):
        self.is_reset = True
        self.task_info = None
