
import unittest

from ansible import runner
from ansible.utils import plugins
from ansible.runner.action_plugins import normal, synchronize, template

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
