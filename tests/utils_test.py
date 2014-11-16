
import inspect
import os
import tempfile
import unittest

from ansible import runner
from ansible.utils import plugins
import ansible.runner.action_plugins.normal as normal

from ansibledebugger import action_plugin_wrapper
from ansibledebugger import utils


class UtilsTest(unittest.TestCase):
    def test_read_std_module_file(self):
        module_data = utils.read_module_file(os)
        self.assertNotEqual(module_data, '')

    def test_read_ansible_module_file(self):
        module_data = utils.read_module_file(normal)
        self.assertNotEqual(module_data, '')

    def test_read_ansibledebugger_module_file(self):
        module_data = utils.read_module_file(action_plugin_wrapper)
        self.assertNotEqual(module_data, '')

    def test_replace_plugin_can_setup_dir(self):
        tempdir = tempfile.mkdtemp()
        utils.replace_plugin(normal, action_plugin_wrapper, tempdir)

        self.assertIn('normal.py', os.listdir(tempdir))
        self.assertIn('normal_internal.py', os.listdir(tempdir))

    def test_replace_plugin_can_replace(self):
        tempdir = tempfile.mkdtemp()
        utils.replace_plugin(normal, action_plugin_wrapper, tempdir)
        plugins.action_loader.add_directory(tempdir)

        dummy_runner = runner.Runner(host_list=[])
        normal_plugin = plugins.action_loader.get('normal', dummy_runner)

        self.assertEqual(inspect.getsourcefile(normal_plugin.__class__),
                         os.path.join(tempdir, 'normal.py'))
