
import unittest
from nose_parameterized import parameterized
from mock import Mock

from ansible import errors
from ansible import runner
from ansible.utils import plugins
from ansible.runner.return_data import ReturnData

from ansibledebugger import action_plugin_wrapper
from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction

from testutils import wrapped_action_plugin


class ActionPluginWrapperTest(unittest.TestCase):
    @wrapped_action_plugin(['normal'])
    def test_wrap_run_is_wrapped(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        self.assertIsNotNone(normal_plugin.run.func_closure)
        self.assertTrue(hasattr(normal_plugin.run.func_closure[0].cell_contents, '__call__'))

    @wrapped_action_plugin(['normal'])
    def test_wrap_watch_is_called(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        watch_mock = Mock(name="watch_mock")
        action_plugin_wrapper.ActionPluginWrapper._watch = watch_mock

        return_data = normal_plugin.run()

        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._watch.call_count, 1)
        self.assertTrue(getattr(return_data, 'debugger_pass_through', False))

    @wrapped_action_plugin(['normal'])
    def test_watch_call_interpreter_if_failed(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=True))
        action_plugin_wrapper.ActionPluginWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock")
        show_interpreter_mock.return_value = NextAction(NextAction.EXIT)
        action_plugin_wrapper.ActionPluginWrapper._show_interpreter = show_interpreter_mock

        normal_plugin.run(None, None, None, None, {})

        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._run.call_count, 1)
        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._show_interpreter.call_count, 1)

    @wrapped_action_plugin(['normal'])
    def test_watch_redo_if_failed_and_next_action_is_redo(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=True))
        action_plugin_wrapper.ActionPluginWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock",
                                     side_effect=[NextAction(NextAction.REDO), NextAction(NextAction.EXIT)])
        action_plugin_wrapper.ActionPluginWrapper._show_interpreter = show_interpreter_mock

        normal_plugin.run(None, None, None, None, {})

        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._run.call_count, 2)
        self.assertEqual(action_plugin_wrapper.ActionPluginWrapper._show_interpreter.call_count, 2)

    @wrapped_action_plugin(['normal'])
    def test_watch_rethrow_exception_if_internal_run_throws_it(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (None, ErrorInfo(failed=True, exception=errors.AnsibleError('')))
        action_plugin_wrapper.ActionPluginWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock")
        show_interpreter_mock.return_value = NextAction(NextAction.EXIT)
        action_plugin_wrapper.ActionPluginWrapper._show_interpreter = show_interpreter_mock

        with self.assertRaises(errors.AnsibleError) as ex:
            normal_plugin.run(None, None, None, None, {})

        self.assertTrue(hasattr(ex.exception, 'debugger_pass_through'))
        self.assertTrue(ex.exception.debugger_pass_through)

    @wrapped_action_plugin(['normal'])
    def test_private_run_exec_run_inner(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)
        wrapper = action_plugin_wrapper.ActionPluginWrapper()

        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.return_value = ReturnData(host='', result={})

        task_info = TaskInfo(None, None, {}, None, conn=None, tmp_path=None)
        return_data, error_info = wrapper._run(run_inner_mock, normal_plugin, task_info)

        self.assertEqual(run_inner_mock.call_count, 1)
        self.assertEqual(error_info.failed, False)

    @wrapped_action_plugin(['normal'])
    def test_private_run_catch_ansible_error(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)
        wrapper = action_plugin_wrapper.ActionPluginWrapper()

        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.side_effect = errors.AnsibleError("ansible error")

        task_info = TaskInfo(None, None, None, None, conn=None, tmp_path=None)
        return_data, error_info = wrapper._run(run_inner_mock, normal_plugin, task_info)

        self.assertEqual(error_info.failed, True)
        self.assertEqual(error_info.reason, 'AnsibleError')
        self.assertEqual(str(error_info.exception), 'ansible error')

    @parameterized.expand([
        # (description, ReturnData, ignore_errors, expected failed flag)
        ("no_error", ReturnData(host='', result={}), False, False),
        ("failed", ReturnData(host='', result={'failed': True}), False, True),
        ("failed_ignore_error", ReturnData(host='', result={'failed': True}), True, False),
        ("rc_is_1", ReturnData(host='', result={'rc': 1}), False, True),
    ])
    def test_is_failed(self, _, returnData, ignore_errors, expectedResult):
        wrapper = action_plugin_wrapper.ActionPluginWrapper()
        task_info = TaskInfo(None, None, {'register': 'result'}, None)

        self.assertEqual(wrapper._is_failed(returnData, ignore_errors, task_info).failed,
                         expectedResult)
