
import pexpect
import unittest


class DebuggerInvokedTest(unittest.TestCase):
    """Test a debugger is (not) invoked as expected."""
    base_command = 'ansible-playbook-debugger fail_cond.yml -i inventory -vv'

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_failed(self):
        command = self.base_command + ' --tags=failed'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

        # unreachable=1 if return_data is not returned as expected
        self.proc.expect('unreachable=0')

    def test_failed_ignore(self):
        command = self.base_command + ' --tags=failed_ignore'
        self.proc = pexpect.spawn(command)
        self.proc.expect('ignoring')
        self.proc.expect('PLAY RECAP')

    def test_failed_retries(self):
        command = self.base_command + ' --tags=failed_retries'
        self.proc = pexpect.spawn(command)
        num_tries = 3
        for x in xrange(num_tries):
            self.proc.expect('(Apdb)')
            self.proc.sendline('quit')

        self.proc.expect('FATAL')

    def test_failed_retries_ignore_errors(self):
        command = self.base_command + ' --tags=failed_retries_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('ignoring')
        self.proc.expect('PLAY RECAP')

    def test_rc_is_not_0(self):
        command = self.base_command + ' --tags=invalid_rc'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_rc_is_not_0_ignore_errors(self):
        command = self.base_command + ' --tags=invalid_rc_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('ignoring')
        self.proc.expect('PLAY RECAP')

    def test_no_module(self):
        command = self.base_command + ' --tags=no_module'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_env_is_not_dict(self):
        command = self.base_command + ' --tags=env_is_not_dict'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_action_plugin_throws_error(self):
        command = self.base_command + ' --tags=action_plugin_throws_error'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_undefined_var_in_template(self):
        command = self.base_command + ' --tags=undefined_var_in_template'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_wrong_filter_in_template(self):
        command = self.base_command + ' --tags=wrong_filter_in_template'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_when_keyword_has_error(self):
        command = self.base_command + ' --tags=when_keyword_has_error'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_duplicate_arguments(self):
        command = self.base_command + ' --tags=duplicate_arguments'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_failed_when(self):
        command = self.base_command + ' --tags=failed_when'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_failed_when_ignore_errors(self):
        command = self.base_command + ' --tags=failed_when_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('ignoring')
        self.proc.expect('PLAY RECAP')

    def test_unreachable(self):
        command = self.base_command + ' --tags=unreachable'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_unreachable_ignore_errors(self):
        command = self.base_command + ' --tags=unreachable_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_wrong_port(self):
        command = self.base_command + ' --tags=wrong_port'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_wrong_port_ignore_errors(self):
        command = self.base_command + ' --tags=wrong_port_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_unreachable_paramiko(self):
        command = self.base_command + ' --tags=unreachable_paramiko'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_unreachable_paramiko_ignore_errors(self):
        command = self.base_command + ' --tags=unreachable_paramiko_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
