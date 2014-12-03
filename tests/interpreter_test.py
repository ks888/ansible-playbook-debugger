
from StringIO import StringIO
from mock import patch
import unittest
from nose_parameterized import parameterized

from ansible import runner
from ansible import utils

from ansibledebugger.interpreter import ErrorInfo, NextAction, TaskInfo
from ansibledebugger.interpreter.simple_interpreter import Interpreter


class SimpleInterpreterTest(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_help(self, mock_stdout):
        interpreter = Interpreter(None, None, ErrorInfo(), None)
        interpreter.do_h(None)

        self.assertIn('Documented commands', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_error(self, mock_stdout):
        test_reason = 'test reason'
        test_result = 'test result'
        interpreter = Interpreter(None, None, ErrorInfo(failed=True, reason=test_reason,
                                                        result=test_result), None)
        interpreter.do_e(None)

        self.assertIn(test_reason, mock_stdout.getvalue())
        self.assertIn(test_result, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_list(self, mock_stdout):
        module_name = 'test module'
        module_args = 'a=b'
        complex_args = {'a': 'b'}
        complex_args_expect = str(complex_args)
        keyword = {'ignore_errors': False}
        keyword_expect = 'ignore_errors:False'
        hostname = 'test_host'
        groups = ['a', 'b']
        groups_expect = 'a,b'
        vars = {'inventory_hostname': hostname, 'group_names': groups}
        vars.update(keyword)
        dummy_runner = runner.Runner(host_list=[])
        connection_type = 'ssh'
        ssh_host = 'another_test_host'
        ssh_port = 22
        ssh_port_expect = 'Port=22'
        conn = utils.plugins.connection_loader.get(connection_type, dummy_runner, ssh_host, ssh_port, '', '', '')
        conn.connect()

        interpreter = Interpreter(TaskInfo(conn, '', module_name, module_args, vars, complex_args),
                                  None, ErrorInfo(), None)
        interpreter.do_l(None)

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(keyword_expect, mock_stdout.getvalue())
        self.assertIn(hostname, mock_stdout.getvalue())
        self.assertIn(groups_expect, mock_stdout.getvalue())
        self.assertIn(connection_type, mock_stdout.getvalue())
        self.assertIn(ssh_host, mock_stdout.getvalue())
        self.assertIn(ssh_port_expect, mock_stdout.getvalue())

    @parameterized.expand([
        # string in dot notation, expected key list
        ('dict', 'ab', [('ab', dict)]),
        ('dot_dict', '.ab', [('ab', dict)]),
        ('list', '[10]', [(10, list)]),
        ('dict_list', 'ab[10]', [('ab', dict), (10, list)]),
        ('dict_dict', 'ab.cd', [('ab', dict), ('cd', dict)]),
        ('list_list', '[0][10]', [(0, list), (10, list)]),
        ('dict_list_dict', 'ab[10].cd', [('ab', dict), (10, list), ('cd', dict)]),
    ])
    def test_doc_str_to_key_list(self, _, doc_str, expected_key_list):
        self.assertEqual(Interpreter.dot_str_to_key_list(doc_str),
                         expected_key_list)
