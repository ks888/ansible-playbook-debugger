
import unittest
from nose_parameterized import parameterized
from mock import Mock

from ansible import runner
from ansible.utils import plugins
from ansible.runner.action_plugins import normal, synchronize, template
from ansible.runner.return_data import ReturnData

from testutils import replaced_action_plugin


class ActionPluginWrapperTest(unittest.TestCase):
    @replaced_action_plugin([normal])
    def test_wrapper_can_load_internal_plugin(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        parent_classes = normal_plugin.__class__.__bases__
        parent_class_modules = [cls.__module__.split('.')[-1] for cls in parent_classes]
        self.assertIn('normal', parent_class_modules)
        self.assertIn('normal_internal', parent_class_modules)
        self.assertIn('runner', normal_plugin.__dict__)

    @replaced_action_plugin([synchronize, template])
    def test_wrapper_can_delegate_attr_if_not_defined(self):
        dummy_runner = runner.Runner(host_list=[])
        sync_plugin = plugins.action_loader.get('synchronize', dummy_runner)
        template_plugin = plugins.action_loader.get('template', dummy_runner)

        self.assertTrue(hasattr(sync_plugin, 'setup'), 'sync plugin has setup attr')
        self.assertTrue(hasattr(template_plugin, 'TRANSFERS_FILES'),
                        'template plugin has TRANSFERS_FILES attr')

    @replaced_action_plugin([normal])
    def test_run_exec_wrapped_plugin(self):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        run_mock = Mock(name="run_mock")
        run_mock.return_value = ReturnData(host='', result={})

        # __dict__ is shared between wrapper and wrapped class, so avoid to touch it
        normal_plugin.wrapped_plugin.__class__.run = run_mock
        normal_plugin.run(None, None, None, None, {})

        self.assertEqual(len(normal_plugin.wrapped_plugin.run.mock_calls), 1)

    @parameterized.expand([
        # (description, ReturnData, ignore_errors, expected result)
        ("no_error", ReturnData(host='', result={}), False, False),
        ("unreachable", ReturnData(host='', result={}, comm_ok=False), False, True),
        ("unreachable_ignore_error", ReturnData(host='', result={}, comm_ok=False), True, True),
        ("failed", ReturnData(host='', result={'failed': True}), False, True),
        ("failed_ignore_error", ReturnData(host='', result={'failed': True}), True, False),
        ("rc_is_1", ReturnData(host='', result={'rc': 1}), False, True),
        ("failed_when_result", ReturnData(host='', result={'failed_when_result': True}), False, True),
    ])
    @replaced_action_plugin([normal])
    def test_is_fail(self, _, returnData, ignore_errors, expectedResult):
        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        self.assertEqual(normal_plugin._is_fail(returnData, ignore_errors),
                         expectedResult)
