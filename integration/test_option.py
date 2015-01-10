
import os
import pexpect
import sys
import unittest

local_module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'lib')
)
sys.path.append(local_module_path)

from ansibledebugger import __version__


class OptionTest(unittest.TestCase):
    """Test a debugger can handle options as expected."""
    def test_version(self):
        command = 'ansible-playbook-debugger --version'
        self.proc = pexpect.spawn(command)
        self.proc.expect(__version__)
        self.proc.expect(pexpect.EOF)

    def test_version_abbrev(self):
        command = 'ansible-playbook-debugger --v'
        self.proc = pexpect.spawn(command)
        self.proc.expect(__version__)
        self.proc.expect(pexpect.EOF)

    def test_help(self):
        command = 'ansible-playbook-debugger --help'
        self.proc = pexpect.spawn(command)
        self.proc.expect('playbook.yml')
        self.proc.expect(pexpect.EOF)
