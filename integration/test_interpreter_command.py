
import pexpect
import unittest


base_command = 'ansible-playbook-debugger command_test.yml -i inventory -vv'


class WrongModuleArgsCaseTest(unittest.TestCase):
    command = base_command + ' --tags=invalid_module_args'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_update_module_args(self):
        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('update module_args data=value')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": "value"')

    def test_assign_module_args(self):
        self.proc.sendline('assign module_args data=value')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": "value"')

    def test_continue(self):
        self.proc.sendline('assign module_args')
        self.proc.expect('(Apdb)')

        self.proc.sendline('continue')
        self.proc.expect('FATAL')

    def test_quit(self):
        self.proc.sendline('quit')
        self.proc.expect('abort')


class WrongComplexArgsCaseTest(unittest.TestCase):
    command = base_command + ' --tags=invalid_complex_args'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_update_complex_args(self):
        self.proc.sendline('del complex_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('update complex_args data: value')
        self.proc.sendline('')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('ok:')

    def test_assign_complex_args(self):
        self.proc.sendline('assign complex_args data: value')
        self.proc.sendline('')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": "value"')


class WrongTemplateCaseTest(unittest.TestCase):
    command = base_command + ' --tags=wrong_template'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_update_module_args(self):
        self.proc.sendline('update module_args data={{ var1 }}')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": "value1"')

    def test_update_complex_args(self):
        self.proc.sendline('assign module_args')
        self.proc.expect('(Apdb)')

        self.proc.sendline('update complex_args data: "{{ var1 }}"')
        self.proc.sendline('')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": "value1"')

    def test_set_dict_var_to_complex_args(self):
        self.proc.sendline('assign module_args')
        self.proc.expect('(Apdb)')

        self.proc.sendline('update complex_args data: "{{ var2 }}"')
        self.proc.sendline('')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('"ping": {"var3": "value3"}')


class MultihostInvalidArgsCaseTest(unittest.TestCase):
    command = base_command + ' --tags=multihost_invalid_args --forks=1'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_assign_module_args(self):
        num_hosts = 2
        for x in xrange(num_hosts):
            self.proc.sendline('assign module_args')
            self.proc.expect('(Apdb)')

            self.proc.sendline('redo')
            self.proc.expect('"ping": "pong"')


class MultihostWrongTemplateCaseTest(unittest.TestCase):
    command = base_command + ' --tags=multihost_wrong_template --forks=1'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_update_module_args(self):
        num_hosts = 2
        for x in xrange(num_hosts):
            self.proc.sendline('update module_args data={{ var1 }}')
            self.proc.expect('(Apdb)')

            self.proc.sendline('redo')
            self.proc.expect('"ping": "value1"')
