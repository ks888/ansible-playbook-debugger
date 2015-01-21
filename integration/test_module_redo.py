
from nose_parameterized import parameterized
import pexpect
import unittest


class WrongModuleArgsCaseTest(unittest.TestCase):
    base_command = 'ansible-playbook-debugger module_redo_test.yml -i inventory -vv'

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    @parameterized.expand([
        ('template'),
    ])
    def test_del_module_args_and_redo(self, tag_name):
        command = self.base_command + ' --tags=' + tag_name
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('PLAY RECAP')
