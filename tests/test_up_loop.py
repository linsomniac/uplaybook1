#!/usr/bin/env python3

from typing import List
from types import ModuleType


def import_script_as_module(module_name: str, paths_to_try: List[str]) -> ModuleType:
    """
    Imports a Python script as a module, whether it ends in ".py" or not.
    Given the name of a module to import, and a list of absolute or relative path names
    (including the filename), import the module.  The module is set up so that it can
    later be imported, but a reference to the module is also returned.

    Args:
        module_name (str): The name of the module to import.
                This doesn't have to match the filename.
        paths_to_try (List[str]): A list of file paths to look for the file to load.
                This can be absolute or relative paths to the file, the first file that
                exists is used.

    Returns:
        Module: A reference to the imported module.

    Raises:
        FileNotFoundError: If the module file is not found in any of the specified directory paths.
        ImportError: If there are issues importing the module, such as invalid Python syntax in the module file.

    Example:
        my_module = import_script_as_module("my_module", ["my_module", "../my_module"])

        # Now you can either directly use "my_module"
        my_module.function()

        # Or you can later import it:
        import my_module
    """
    from pathlib import Path
    import os

    for try_filename in paths_to_try:
        if os.path.exists(try_filename):
            module_filename = Path(try_filename).resolve()
            break
    else:
        raise FileNotFoundError(f"Unable to find '{module_name}' module to import")

    from importlib.util import spec_from_loader, module_from_spec
    from importlib.machinery import SourceFileLoader
    import sys

    spec = spec_from_loader(
        module_name, SourceFileLoader(module_name, str(module_filename))
    )
    if spec is None:
        raise ImportError("Unable to spec_from_loader() the module, no error returned.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["up"] = module

    return module


up = import_script_as_module("up", ["./up", "../up"])

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
        input_list = [
            OrderedDict(a=1, b=2, loop=[OrderedDict(c=3), OrderedDict(b=5, d=4)])
        ]
        expected_output = [OrderedDict(a=1, b=2, c=3), OrderedDict(a=1, b=5, d=4)]
        self.assertEqual(up.unroll_loops(input_list), expected_output)

    def test_empty_input(self):
        input_list = []
        expected_output = []
        self.assertEqual(up.unroll_loops(input_list), expected_output)


if __name__ == "__main__":
    unittest.main()
