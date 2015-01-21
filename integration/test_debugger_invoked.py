
from nose_parameterized import parameterized
import pexpect
import unittest


class DebuggerInvokedTest(unittest.TestCase):
    """Test a debugger is (not) invoked as expected."""
    base_command = 'ansible-playbook-debugger fail_cond.yml -i inventory -vv'

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    @parameterized.expand([
        ('invalid_rc'),
        ('no_module'),
        ('env_is_not_dict'),
        ('action_plugin_throws_error'),
        ('undefined_var_in_template'),
        ('wrong_filter_in_template'),
        ('when_keyword_has_error'),
        ('duplicate_arguments'),
        ('failed_when'),
        ('unreachable'),
        ('unreachable_ignore_errors'),
        ('wrong_port'),
        ('wrong_port_ignore_errors'),
        ('unreachable_paramiko'),
        ('unreachable_paramiko_ignore_errors'),
        ('failed_retries'),
    ])
    def test_debugger_invoked(self, tag_name):
        command = self.base_command + ' --tags=' + tag_name
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    @parameterized.expand([
        ('failed_ignore'),
        ('failed_retries_ignore_errors'),
        ('invalid_rc_ignore_errors'),
        ('failed_when_ignore_errors'),
    ])
    def test_debugger_not_invoked_by_ignoring(self, tag_name):
        command = self.base_command + ' --tags=' + tag_name
        self.proc = pexpect.spawn(command)
        self.proc.expect('ignoring')
        self.proc.expect('PLAY RECAP')

    @parameterized.expand([
        ('failed_when_failed'),
        ('failed_when_invalid_rc'),
    ])
    def test_debugger_not_invoked(self, tag_name):
        command = self.base_command + ' --tags=' + tag_name
        self.proc = pexpect.spawn(command)
        self.proc.expect('PLAY RECAP')

    def test_failed(self):
        command = self.base_command + ' --tags=failed'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

        # unreachable=1 if return_data is not returned as expected
        self.proc.expect('unreachable=0')
