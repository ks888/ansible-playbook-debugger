
from mock import patch
from nose_parameterized import parameterized
from StringIO import StringIO
import unittest

from ansible import runner
from ansible import utils

from ansible.runner.return_data import ReturnData
from ansibledebugger.interpreter import ErrorInfo, NextAction, TaskInfo
from ansibledebugger.interpreter.simple_interpreter import Interpreter


def dataset():
    module_name = 'test module'
    module_args = 'ma_k=ma_v'
    complex_args = {'ca_k': 'ca_v'}
    complex_args_expect = str(complex_args)
    vars = {'v_k': 'v_v'}
    vars_expect = 'v_v'

    interpreter = Interpreter(TaskInfo(module_name, module_args, vars, complex_args),
                              ErrorInfo(), None)
    return interpreter, module_name, module_args, complex_args_expect, vars_expect


class SimpleInterpreterTest(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_help(self, mock_stdout):
        interpreter = Interpreter(None, ErrorInfo(), None)
        interpreter.do_h(None)

        self.assertIn('Documented commands', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_error(self, mock_stdout):
        test_reason = 'test reason'
        test_comm_ok = True
        test_data = ReturnData(host='', result={'msg': 'test data'}, comm_ok=test_comm_ok)
        test_exception = Exception()
        interpreter = Interpreter(None, ErrorInfo(True, test_reason, test_data, test_exception), None)
        interpreter.do_e(None)

        self.assertIn(test_reason, mock_stdout.getvalue())
        self.assertIn(test_data.result['msg'], mock_stdout.getvalue())
        self.assertIn(str(test_comm_ok), mock_stdout.getvalue())
        self.assertIn(str(test_exception), mock_stdout.getvalue())

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

        interpreter = Interpreter(TaskInfo(module_name, module_args, vars, complex_args),
                                  ErrorInfo(), None)
        interpreter.do_l(None)

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(keyword_expect, mock_stdout.getvalue())
        self.assertIn(hostname, mock_stdout.getvalue())
        self.assertIn(groups_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_all(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p(None)

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_module_name(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p('module_name')

        self.assertIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_module_args(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p('module_args')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_complex_args(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p('complex_args')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertIn(complex_args_expect, mock_stdout.getvalue())
        self.assertNotIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_var(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p('v_k')

        self.assertNotIn(module_name, mock_stdout.getvalue())
        self.assertNotIn(module_args, mock_stdout.getvalue())
        self.assertNotIn(complex_args_expect, mock_stdout.getvalue())
        self.assertIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_not_defined_var(self, mock_stdout):
        interpreter, module_name, module_args, complex_args_expect, vars_expect = dataset()
        interpreter.do_p('undefined_var')
        vars_expect = 'Not defined'

        self.assertIn(vars_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_var_in_dict(self, mock_stdout):
        var = {'key': {'key2': 'v'}}
        var_expect = 'v'
        interpreter = Interpreter(TaskInfo(None, None, var, None),
                                  ErrorInfo(), None)
        interpreter.do_p("key['key2']")

        self.assertIn(var_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_var_unknown_key_in_dict(self, mock_stdout):
        var = {'key': {'key2': 'v'}}
        var_expect = 'v'
        interpreter = Interpreter(TaskInfo(None, None, var, None),
                                  ErrorInfo(), None)
        interpreter.do_p("key['unknown_key']")
        var_expect = 'Not defined'

        self.assertIn(var_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_var_in_list(self, mock_stdout):
        var = {'key': ['v1', 'v2']}
        var_expect = 'v2'
        interpreter = Interpreter(TaskInfo(None, None, var, None),
                                  ErrorInfo(), None)
        interpreter.do_p("key[1]")

        self.assertIn(var_expect, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_add(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key3'
        value = 'v3'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s %s=%s' % (module_args, key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        value = 'new_v1'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_quote(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        value = '"new_v1"'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '%s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_nonkv(self, mock_stdout):
        module_args = 'shell_command key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        value = 'new_v1'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = 'shell_command %s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_all(self, mock_stdout):
        module_args = 'shell_command key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        value = 'new_command key1=new_v1'
        interpreter.do_set('module_args . %s' % (value))

        self.assertEqual(value, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_template(self, mock_stdout):
        module_args = '{{ command }} key1={{ var1 }} key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        value = '{{ var2 }}'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = '{{ command }} %s=%s key2=v2' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_module_args_replace_skip_quote(self, mock_stdout):
        module_args = 'shell_command "key1=v1" key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        value = 'v1'
        interpreter.do_set('module_args %s %s' % (key, value))

        expected_kv = 'shell_command "key1=v1" key2=v2 %s=%s' % (key, value)
        self.assertEqual(expected_kv, interpreter.task_info.module_args)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_sibling(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = 'key2'
        value = 'v2'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': 'v1', 'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_child(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = 'key1.key2'
        value = 'v2'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': {'key2': 'v2'} }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_add_json_sibling(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = 'key1.key2'
        value = '{"key3": "v3"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': {'key2': {'key3': 'v3'} } }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_list_access(self, mock_stdout):
        complex_args = {'key1': ['v1', 'v2']}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = 'key1[1]'
        value = '{"key2": "v2"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key1': ['v1', {'key2': 'v2'}] }
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_set_complex_args_replace_all(self, mock_stdout):
        complex_args = {'key1': 'v1'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = '.'
        value = '{"key2": "v2"}'
        interpreter.do_set('complex_args %s %s' % (key, value))

        expect = {'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_module_args(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        interpreter.do_del('module_args %s' % (key))

        expect = 'key2=v2'
        self.assertEqual(interpreter.task_info.module_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_module_args_all(self, mock_stdout):
        module_args = 'key1=v1 key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        interpreter.do_del('module_args  .  ')

        self.assertEqual(interpreter.task_info.module_args, '')

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_module_args_template(self, mock_stdout):
        module_args = 'key1={{ var1 }} key2=v2'
        interpreter = Interpreter(TaskInfo('', module_args, None, None),
                                  ErrorInfo(), None)

        key = 'key1'
        interpreter.do_del('module_args %s' % (key))

        expect = 'key2=v2'
        self.assertEqual(interpreter.task_info.module_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_complex_args_del_str(self, mock_stdout):
        complex_args = {'key1': 'v1', 'key2': 'v2'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = 'key1'
        interpreter.do_del('complex_args %s' % (key))

        expect = {'key2': 'v2'}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_del_complex_args_del_all(self, mock_stdout):
        complex_args = {'key1': 'v1', 'key2': 'v2'}
        interpreter = Interpreter(TaskInfo('', '', None, complex_args),
                                  ErrorInfo(), None)

        key = '.'
        interpreter.do_del('complex_args %s' % (key))

        expect = {}
        self.assertEqual(interpreter.task_info.complex_args, expect)

    @patch('sys.stdout', new_callable=StringIO)
    def test_redo(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', None, None), ErrorInfo(), NextAction())
        result = interpreter.do_r('')

        self.assertEqual(interpreter.next_action.result, NextAction.REDO)
        self.assertTrue(result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_eof(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', None, None), ErrorInfo(), NextAction())
        result = interpreter.do_EOF('')

        self.assertEqual(interpreter.next_action.result, NextAction.EXIT)
        self.assertTrue(result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_quit(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', None, None), ErrorInfo(), NextAction())
        result = interpreter.do_q('')

        self.assertEqual(interpreter.next_action.result, NextAction.EXIT)
        self.assertTrue(result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_continue(self, mock_stdout):
        interpreter = Interpreter(TaskInfo('', '', None, None), ErrorInfo(), NextAction())
        result = interpreter.do_c('')

        self.assertEqual(interpreter.next_action.result, NextAction.CONTINUE)
        self.assertTrue(result)

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
