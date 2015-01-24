
import unittest
from nose_parameterized import parameterized
from mock import Mock

from ansible import errors
from ansible import runner
from ansible.runner.return_data import ReturnData

from ansibledebugger import action_plugin_wrapper
from ansibledebugger import runner_wrapper
from ansibledebugger.interpreter import TaskInfo, ErrorInfo, NextAction


class RunnerWrapperTest(unittest.TestCase):
    def setUp(self):
        reload(runner_wrapper)

    def test_func_is_wrapped(self):
        wrapper = runner_wrapper.RunnerWrapper(None)
        wrapper.wrap(runner.Runner)
        dummy_runner = runner.Runner(host_list=[])

        self.assertIsNotNone(dummy_runner._executor_internal_inner.func_closure)
        self.assertTrue(hasattr(dummy_runner._executor_internal_inner.func_closure[0].cell_contents, '__call__'))

    def test_get_action_plugin_wrapper_info(self):
        ap_wrapper = action_plugin_wrapper.ActionPluginWrapper()
        wrapper = runner_wrapper.RunnerWrapper(ap_wrapper)

        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.return_value = ReturnData(host='', result={})
        ap_wrapper._watch(run_inner_mock, None, None, None, None, None, None)

        self.assertIsInstance(wrapper.action_plugin_wrapper.task_info, TaskInfo)
        self.assertFalse(wrapper.action_plugin_wrapper.is_reset)

    def test_watch_is_called(self):
        wrapper = runner_wrapper.RunnerWrapper(None)
        wrapper.wrap(runner.Runner)

        watch_mock = Mock(name="watch_mock")
        runner_wrapper.RunnerWrapper._watch = watch_mock

        dummy_runner = runner.Runner(host_list=[])
        dummy_runner._executor_internal_inner()

        self.assertEqual(runner_wrapper.RunnerWrapper._watch.call_count, 1)

    def test_watch_calls_interpreter_if_failed(self):
        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=True))
        runner_wrapper.RunnerWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock")
        show_interpreter_mock.return_value = NextAction(NextAction.CONTINUE)
        runner_wrapper.RunnerWrapper._show_interpreter = show_interpreter_mock

        wrapper = runner_wrapper.RunnerWrapper(None)
        callbacks_mock = Mock(task=None)
        runner_mock = Mock(callbacks=callbacks_mock)
        wrapper._watch(None, runner_mock, None, None, None, None, None)

        self.assertEqual(runner_wrapper.RunnerWrapper._run.call_count, 1)
        self.assertEqual(runner_wrapper.RunnerWrapper._show_interpreter.call_count, 1)

    def test_watch_redoes_if_failed_and_next_action_is_redo(self):
        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=True))
        runner_wrapper.RunnerWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock",
                                     side_effect=[NextAction(NextAction.REDO), NextAction(NextAction.CONTINUE)])
        runner_wrapper.RunnerWrapper._show_interpreter = show_interpreter_mock

        wrapper = runner_wrapper.RunnerWrapper(None)
        callbacks_mock = Mock(task=None)
        runner_mock = Mock(callbacks=callbacks_mock)
        wrapper._watch(None, runner_mock, None, None, None, None, None)

        self.assertEqual(runner_wrapper.RunnerWrapper._run.call_count, 2)
        self.assertEqual(runner_wrapper.RunnerWrapper._show_interpreter.call_count, 2)

    def test_watch_rethrows_exception_if_internal_run_throws_it(self):
        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (None, ErrorInfo(failed=True, exception=errors.AnsibleError('')))
        runner_wrapper.RunnerWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock")
        show_interpreter_mock.return_value = NextAction(NextAction.CONTINUE)
        runner_wrapper.RunnerWrapper._show_interpreter = show_interpreter_mock

        wrapper = runner_wrapper.RunnerWrapper(None)
        callbacks_mock = Mock(task=None)
        runner_mock = Mock(callbacks=callbacks_mock)
        with self.assertRaises(errors.AnsibleError):
            wrapper._watch(None, runner_mock, None, None, None, None, None)

    def test_watch_calls_exit_if_failed_and_next_action_is_exit(self):
        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=True))
        runner_wrapper.RunnerWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock",
                                     side_effect=[NextAction(NextAction.REDO), NextAction(NextAction.EXIT)])
        runner_wrapper.RunnerWrapper._show_interpreter = show_interpreter_mock

        wrapper = runner_wrapper.RunnerWrapper(None)
        callbacks_mock = Mock(task=None)
        runner_mock = Mock(callbacks=callbacks_mock)
        with self.assertRaises(SystemExit) as ex:
            wrapper._watch(None, runner_mock, None, None, None, None, None)

        self.assertEqual(ex.exception.code, 1)

    def test_watch_calls_interpreter_if_breakpoint(self):
        internal_run_mock = Mock(name="internal_run_mock")
        internal_run_mock.return_value = (ReturnData(host='', result={}), ErrorInfo(failed=False))
        runner_wrapper.RunnerWrapper._run = internal_run_mock

        show_interpreter_mock = Mock(name="show_interpreter_mock",
                                     side_effect=[NextAction(NextAction.CONTINUE)])
        runner_wrapper.RunnerWrapper._show_interpreter = show_interpreter_mock

        wrapper = runner_wrapper.RunnerWrapper(None, ['breakpoint task'])
        task_mock = Mock()  # 'name' is already taken
        task_mock.name = 'breakpoint task'
        callbacks_mock = Mock(task=task_mock)
        runner_mock = Mock(callbacks=callbacks_mock)
        wrapper._watch(None, runner_mock, None, None, None, None, None)

        self.assertEqual(runner_wrapper.RunnerWrapper._run.call_count, 1)
        self.assertEqual(runner_wrapper.RunnerWrapper._show_interpreter.call_count, 1)

    def test_private_run_exec_run_inner(self):
        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.return_value = ReturnData(host='', result={})

        task_info = TaskInfo(None, None, {}, None, host=None, port=None, is_chained=None)
        dummy_runner = runner.Runner(host_list=[])
        wrapper = runner_wrapper.RunnerWrapper(action_plugin_wrapper.ActionPluginWrapper())
        return_data, error_info = wrapper._run(run_inner_mock, dummy_runner, task_info)

        self.assertEqual(run_inner_mock.call_count, 1)
        self.assertEqual(error_info.failed, False)

    def test_private_run_catch_ansible_error(self):
        run_inner_mock = Mock(name="run_inner_mock")
        run_inner_mock.side_effect = errors.AnsibleError("ansible error")

        task_info = TaskInfo(None, None, {}, None, host=None, port=None, is_chained=None)
        dummy_runner = runner.Runner(host_list=[])
        wrapper = runner_wrapper.RunnerWrapper(action_plugin_wrapper.ActionPluginWrapper())
        return_data, error_info = wrapper._run(run_inner_mock, dummy_runner, task_info)

        self.assertEqual(error_info.failed, True)
        self.assertEqual(error_info.reason, 'AnsibleError')
        self.assertEqual(str(error_info.exception), 'ansible error')

    @parameterized.expand([
        # (description, ReturnData, ignore_errors, expected failed flag)
        ("no_error", ReturnData(host='', result={}), False, False),
        ("comm_error", ReturnData(host='', result={}, comm_ok=False), False, True),
        ("failed", ReturnData(host='', result={'failed': True}), False, True),
        ("failed_ignore_error", ReturnData(host='', result={'failed': True}), True, False),
        ("rc_is_1", ReturnData(host='', result={'rc': 1}), False, True),
        ("failed_when_is_True", ReturnData(host='', result={'failed_when_result': True}), False, True),
        ("failed_when_is_False", ReturnData(host='', result={'failed': True, 'failed_when_result': False}), False, False),
    ])
    def test_is_failed(self, _, returnData, ignore_errors, expectedResult):
        wrapper = runner_wrapper.RunnerWrapper(None)
        task_info = TaskInfo(None, None, {'register': 'result'}, None)

        self.assertEqual(wrapper._is_failed(returnData, ignore_errors, task_info).failed,
                         expectedResult)
