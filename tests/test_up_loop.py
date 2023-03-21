#!/usr/bin/env python3

import sys
from pathlib import Path
import os
import types

for up_try in ['up', '../up']:
    if os.path.exists(up_try):
        up_found = Path(up_try).resolve()
        break
else:
    raise RuntimeError("Unable to find 'up' module to import")

with open(up_found, 'r') as fp:
    module_bytecode = compile(fp.read(), up_found.parent, 'exec')
module = types.ModuleType('up')
exec(module_bytecode, module.__dict__)
sys.modules['up'] = module

import up

import unittest
from collections import OrderedDict

class TestUnrollLoops(unittest.TestCase):
    def test_no_loop(self):
        input_list = [OrderedDict(a=1, b=2), OrderedDict(c=3, d=4)]
        expected_output = [OrderedDict(a=1, b=2), OrderedDict(c=3, d=4)]
        self.assertEqual(up.unroll_loops(input_list), expected_output)

    def test_loop(self):
        input_list = [OrderedDict(a=1, b=2, loop=[OrderedDict(c=3), OrderedDict(d=4)])]
        expected_output = [OrderedDict(a=1, b=2, c=3), OrderedDict(a=1, b=2, d=4)]
        self.assertEqual(up.unroll_loops(input_list), expected_output)

    def test_loop_override(self):
        input_list = [OrderedDict(a=1, b=2, loop=[OrderedDict(c=3), OrderedDict(b=5, d=4)])]
        expected_output = [OrderedDict(a=1, b=2, c=3), OrderedDict(a=1, b=5, d=4)]
        self.assertEqual(up.unroll_loops(input_list), expected_output)

    def test_empty_input(self):
        input_list = []
        expected_output = []
        self.assertEqual(up.unroll_loops(input_list), expected_output)

if __name__ == "__main__":
    unittest.main()
