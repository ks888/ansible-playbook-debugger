
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

    def test_del_module_args_and_redo(self):
        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('ok:')

    def test_set_module_args(self):
        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('set module_args data value')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('REMOTE_MODULE ping data=value')
        self.proc.expect('ok:')

    def test_continue(self):
        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('continue')
        self.proc.expect('FATAL')

    def test_quit(self):
        self.proc.sendline('del module_args invalid_arg')
        self.proc.expect('(Apdb)')

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

    def test_del_complex_args_and_redo(self):
        self.proc.sendline('del complex_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('ok:')

    def test_set_complex_args(self):
        self.proc.sendline('del complex_args invalid_arg')
        self.proc.expect('(Apdb)')

        self.proc.sendline('set complex_args data value')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('REMOTE_MODULE ping data=value')
        self.proc.expect('ok:')


class WrongTemplateCaseTest(unittest.TestCase):
    command = base_command + ' --tags=wrong_template'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_set_module_args_and_redo(self):
        self.proc.sendline('set module_args data {{ var1 }}')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('REMOTE_MODULE ping data=value1')
        self.proc.expect('ok:')

    def test_del_module_args_set_complex_args_and_redo(self):
        self.proc.sendline('del module_args .')
        self.proc.expect('(Apdb)')

        self.proc.sendline('set complex_args data {{ var1 }}')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('REMOTE_MODULE ping data=value1')
        self.proc.expect('ok:')

    def test_set_dict_var_to_complex_args(self):
        self.proc.sendline('del module_args .')
        self.proc.expect('(Apdb)')

        self.proc.sendline('set complex_args . {"data": "{{ var2 }}"}')
        self.proc.expect('(Apdb)')

        self.proc.sendline('redo')
        self.proc.expect('REMOTE_MODULE ping')
        self.proc.expect('ok:')
        self.proc.expect('value3')


class MultihostInvalidArgsCaseTest(unittest.TestCase):
    command = base_command + ' --tags=multihost_invalid_args --forks=1'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_del_module_args(self):
        num_hosts = 2
        for x in xrange(num_hosts):
            self.proc.sendline('del module_args .')
            self.proc.expect('(Apdb)')

            self.proc.sendline('redo')
            self.proc.expect('REMOTE_MODULE ping')

        self.proc.expect('ok:')


class MultihostWrongTemplateCaseTest(unittest.TestCase):
    command = base_command + ' --tags=multihost_wrong_template --forks=1'

    def setUp(self):
        self.proc = pexpect.spawn(self.command)
        #self.proc.logfile_read = sys.stdout  # for debug
        self.proc.expect('(Apdb)')

    def tearDown(self):
        self.proc.expect(pexpect.EOF)

    def test_set_module_args(self):
        num_hosts = 2
        for x in xrange(num_hosts):
            self.proc.sendline('set module_args data {{ var1 }}')
            self.proc.expect('(Apdb)')

            self.proc.sendline('redo')
            self.proc.expect('REMOTE_MODULE ping data=value1')

        self.proc.expect('ok:')
