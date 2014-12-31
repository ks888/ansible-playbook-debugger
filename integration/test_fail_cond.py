
import pexpect
import unittest


class FailCondTest(unittest.TestCase):
    base_command = 'ansible-playbook-debugger fail_cond.yml -i inventory -vv'

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_unreachable(self):
        command = self.base_command + ' --tags=unreachable'
        self.proc = pexpect.spawn(command)
        self.proc.expect('AnsibleError')
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_unreachable_ignore_errors(self):
        command = self.base_command + ' --tags=unreachable_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('AnsibleError')
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_no_module(self):
        command = self.base_command + ' --tags=no_module'
        self.proc = pexpect.spawn(command)
        self.proc.expect('AnsibleError')
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
        self.proc.expect('AnsibleError')
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_failed(self):
        command = self.base_command + ' --tags=failed'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')

    def test_failed_ignore(self):
        command = self.base_command + ' --tags=failed_ignore'
        self.proc = pexpect.spawn(command)
        self.proc.sendline('ok:')
        self.proc.expect('PLAY RECAP')

    def test_rc_is_not_0(self):
        command = self.base_command + ' --tags=invalid_rc'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
