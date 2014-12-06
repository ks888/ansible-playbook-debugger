
from mock import patch
from nose_parameterized import parameterized
from StringIO import StringIO
import unittest

from ansible import runner
from ansible import utils

from ansibledebugger.interpreter import ErrorInfo, NextAction, TaskInfo
from ansibledebugger.interpreter.simple_interpreter import Interpreter


def dataset_for_print():
    module_name = 'test module'
    module_args = 'ma_k=ma_v'
    complex_args = {'ca_k': 'ca_v'}
    complex_args_expect = str(complex_args)
    vars = {'v_k': 'v_v'}
    vars_expect = 'v_k: v_v'

    interpreter = Interpreter(TaskInfo('', '', module_name, module_args, vars, complex_args),
                              None, ErrorInfo(), None)
    return interpreter, module_name, module_args, complex_args_expect, vars_expect


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
        module_args = 'ma_k=ma_v'
        complex_args = {'ca_k': 'ca_v'}
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

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_all(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset_for_print()
        interpreter.do_p(None)

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_module_name(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset_for_print()
        interpreter.do_p('module_name')

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_module_args(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset_for_print()
        interpreter.do_p('module_args')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_complex_args(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset_for_print()
        interpreter.do_p('complex_args')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_var(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset_for_print()
        interpreter.do_p('v_k')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_add(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', '', '', module_args, None, None),
                                  None, ErrorInfo(), None)

        key = 'key3'
        value = 'v3'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s %s=%s' % (module_args, key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', '', '', module_args, None, None),
                                  None, ErrorInfo(), None)

        key = 'key1'
        value = 'new_v1'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_quote(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', '', '', module_args, None, None),
                                  None, ErrorInfo(), None)

        key = 'key1'
        value = '"new_v1"'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_sibling(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = 'key2'
        value = 'v2'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': 'v1', 'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_child(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = 'key1.key2'
        value = 'v2'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': {'key2': 'v2'} }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_json_sibling(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = 'key1.key2'
        value = '{"key3": "v3"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': {'key2': {'key3': 'v3'} } }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_list_access(self, mock_stdout):
        complex_args = {'key1': ['v1', 'v2']}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = 'key1[1]'
        value = '{"key2": "v2"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': ['v1', {'key2': 'v2'}] }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_replace_all(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = '.'
        value = '{"key2": "v2"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_module_args(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', '', '', module_args, None, None),
                                  None, ErrorInfo(), None)

        key = 'key1'
        interpreter.do_del('module_args %s' % (key))

        expect = 'key2=v2'
        self.assertEqual(interpreter.task_info.module_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_complex_args_del_str(self, mock_stdout):
        complex_args = {'key1': 'v1', 'key2': 'v2'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = 'key1'
        interpreter.do_del('complex_args %s' % (key))

        expect = {'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_complex_args_del_all(self, mock_stdout):
        complex_args = {'key1': 'v1', 'key2': 'v2'}
        interpreter = Interpreter(TaskInfo('', '', '', '', None, complex_args),
                                  None, ErrorInfo(), None)

        key = '.'
        interpreter.do_del('complex_args %s' % (key))

        expect = {}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_redo(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', '', '', None, None), None, ErrorInfo(), NextAction())
        interpreter.do_r('')

        self.assertEqual(interpreter.next_action.result, NextAction.REDO)

    @patch('sys.stdout', new_callable=StringIO)
    def test_quit(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', '', '', None, None), None, ErrorInfo(), NextAction())
        interpreter.do_q('')

        self.assertEqual(interpreter.next_action.result, NextAction.EXIT)

    @patch('sys.stdout', new_callable=StringIO)
    def test_continue(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', '', '', None, None), None, ErrorInfo(), NextAction())
        interpreter.do_c('')

        self.assertEqual(interpreter.next_action.result, NextAction.CONTINUE)

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
