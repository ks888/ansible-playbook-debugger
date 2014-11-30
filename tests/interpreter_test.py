
import unittest
from nose_parameterized import parameterized

from ansibledebugger.interpreter import ErrorInfo, NextAction
from ansibledebugger.interpreter.simple_interpreter import Interpreter


class SimpleInterpreterTest(unittest.TestCase):
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
