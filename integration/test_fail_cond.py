
import pexpect
import unittest


class FailCondTest(unittest.TestCase):
    base_command = 'ansible-playbook-debugger fail_cond.yml -i inventory -vv'

    def test_unreachable(self):
        command = self.base_command + ' --tags=unreachable'
        self.proc = pexpect.spawn(command)
        self.proc.expect('AnsibleError')
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
        self.proc.expect(pexpect.EOF)

    def test_unreachable_ignore_errors(self):
        command = self.base_command + ' --tags=unreachable_ignore_errors'
        self.proc = pexpect.spawn(command)
        self.proc.expect('AnsibleError')
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
        self.proc.expect(pexpect.EOF)

    def test_failed(self):
        command = self.base_command + ' --tags=failed'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
        self.proc.expect(pexpect.EOF)

    def test_failed_ignore(self):
        command = self.base_command + ' --tags=failed_ignore'
        self.proc = pexpect.spawn(command)
        self.proc.expect('PLAY RECAP')
        self.proc.expect(pexpect.EOF)

    def test_rc_is_not_0(self):
        command = self.base_command + ' --tags=invalid_rc'
        self.proc = pexpect.spawn(command)
        self.proc.expect('(Apdb)')

        self.proc.sendline('quit')
        self.proc.expect('FATAL')
        self.proc.expect(pexpect.EOF)
