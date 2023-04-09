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
from up import symbolic_to_numeric_permissions


class TestSymbolicToNumericPermissions(unittest.TestCase):
    def test_basic_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r"), 0o754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o="), 0o640)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=,o="), 0o700)
        self.assertEqual(symbolic_to_numeric_permissions("a=r"), 0o444)
        self.assertEqual(symbolic_to_numeric_permissions("a=-,ug+r,u+w"), 0o640)

    def test_add_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug+w"), 0o660)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u+w"), 0o754)

    def test_remove_permissions(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rw,g=r,o=,ug-w"), 0o440)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,u-w"), 0o554)
        self.assertEqual(symbolic_to_numeric_permissions("a=rwxs,u-s"), 0o2777)
        pass

    def test_special_X_permission(self):
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwX", is_directory=False), 0o600
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwX", is_directory=True), 0o700
        )

    def test_special_s_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rws,g=rx,o=r"), 0o4654)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rs,o=r"), 0o2744)

    def test_special_t_permission(self):
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt"), 0o1754)
        self.assertEqual(symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx"), 0o745)

    def test_special_X_permission_with_directory(self):
        # For directories, the "X" permission should behave like the "x" permission
        self.assertEqual(symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", True), 0o555)
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rX,g=rX,o=rX", is_directory=False), 0o444
        )

    def test_sticky_bit_with_directory(self):
        # The sticky bit "t" should be set correctly for directories
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=rt", is_directory=True),
            0o1754,
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rt,o=rx", is_directory=True),
            0o0745,
        )
        self.assertEqual(
            symbolic_to_numeric_permissions("u=rwx,g=rx,o=r,a+t", is_directory=True),
            0o1754,
        )


# Run the unit tests
if __name__ == "__main__":
    unittest.main()
