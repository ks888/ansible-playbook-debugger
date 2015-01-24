
import unittest
from mock import Mock

from ansible import runner
from ansible.utils import plugins
from ansible.runner.return_data import ReturnData

from ansibledebugger import action_plugin_wrapper

from testutils import wrapped_action_plugin


class ActionPluginWrapperTest(unittest.TestCase):
    def setUp(self):
        reload(action_plugin_wrapper)

    @wrapped_action_plugin(['normal'])
    def test_func_is_wrapped(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        self.assertIsNotNone(normal_plugin.run.func_closure)
        self.assertTrue(hasattr(normal_plugin.run.func_closure[0].cell_contents, '__call__'))

    def test_watch_is_called(self):
        watch_mock = Mock(name="watch_mock")
        action_plugin_wrapper.ActionPluginWrapper._watch = watch_mock

        dummy_runner = runner.Runner(host_list=[])
        normal_plugin_class = plugins.action_loader.get('normal', dummy_runner).__class__
        wrapper = action_plugin_wrapper.ActionPluginWrapper()
        wrapper.wrap(normal_plugin_class)

        normal_plugin = plugins.action_loader.get('normal', dummy_runner)
        normal_plugin.run()

        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._watch.call_count, 1)

    def test_watch_set_task_info_if_reset(self):
        wrapper = action_plugin_wrapper.ActionPluginWrapper()

        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.return_value = ReturnData(host='', result={})

        wrapper._watch(run_inner_mock, None, None, None, None, None, None)

        self.assertEqual(run_inner_mock.call_count, 1)
        self.assertIsNotNone(wrapper.task_info)
        self.assertFalse(wrapper.is_reset)
