"""
Moppi installer tests.

python -m unittest discover -s tests/

python -m build
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps moppi
"""

from pathlib import Path
import sys
import tomllib
import unittest

import tomli_w

from moppi.config import ConfigTOMLW
from moppi.installer import Moppi


class TestMoppi(unittest.TestCase):
    """Moppi tests."""

    # venv_path = Path("test_venv")

    # def setUp(self) -> None:
    #     """."""
    #     import os, venv

    #     venv.create(self.venv_path)
    #     print(111, sys.path)
    #     os.system("source test_venv/bin/activate")
    #     print(222, sys.path)
    #     return super().setUp()

    # def tearDown(self) -> None:
    #     """."""
    #     # Moppi._rmtree(self.venv_path)
    #     return super().tearDown()

    def setUp(self) -> None:
        """Remove the test.toml file."""
        Path("test.toml").unlink(missing_ok=True)

    # def tearDown(self) -> None:
    #     """Remove the test.toml file."""
    #     Path("test.toml").unlink(missing_ok=True)

    def test_add(self):
        """Test adding a package."""
        # install a package
        package = "Werkzeug"
        m = Moppi()
        m.config = ConfigTOMLW()
        m.add(package)

        # check whether the config file was updated
        with open(Path("test.toml"), "rb") as toml_file:
            config = tomllib.load(toml_file)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": ["Werkzeug==2.2.2"]},
                    "tool": {
                        "moppi": {
                            "indirect-dependencies": [["MarkupSafe==2.1.1", "Werkzeug==2.2.2"]]
                        }
                    },
                },
            )

        # check whether the package exists in .env
        venv = Path(sys.path[-1])
        files = list(venv.glob(f"*{package}*"))
        self.assertTrue(files)

        # import the package
        pack = __import__(package.lower())
        self.assertTrue(pack.__file__)

    def test_update(self):
        """Test updating a package."""
        # update
        package = "Werkzeug"
        m = Moppi()
        m.config = ConfigTOMLW()
        m.add(package)
        m.update(package)

        # check whether the config file was updated
        with open(Path("test.toml"), "rb") as toml_file:
            config = tomllib.load(toml_file)
            print(config)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": ["Werkzeug==2.2.2"]},
                    "tool": {
                        "moppi": {
                            "indirect-dependencies": [["MarkupSafe==2.1.1", "Werkzeug==2.2.2"]]
                        }
                    },
                },
            )

    def test_remove(self):
        """Test removing a package."""
        # remove a package
        package = "Werkzeug"
        m = Moppi()
        m.config = ConfigTOMLW()
        m.add(package)
        m.remove(package)

        # check whether the config file was updated
        with open(Path("test.toml"), "rb") as toml_file:
            config = tomllib.load(toml_file)
            print(config)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": []},
                    "tool": {"moppi": {"indirect-dependencies": []}},
                },
            )

    def test_apply(self):
        """Test installing packages from the config file."""
        # create config
        config = {
            "project": {"dependencies": ["Werkzeug==2.2.2"]},
            "tool": {
                "moppi": {"indirect-dependencies": [["MarkupSafe==2.1.1", "Werkzeug==2.2.2"]]}
            },
        }
        with open(Path("test.toml"), "wb") as toml_file:
            tomli_w.dump(config, toml_file)

        # apply
        package = "Werkzeug"
        m = Moppi()
        m.config = ConfigTOMLW()
        m.apply()

        # check whether the package exists in .env
        venv = Path(sys.path[-1])
        files = list(venv.glob(f"*{package}*"))
        self.assertTrue(files)

        # import the package
        pack = __import__(package.lower())
        self.assertTrue(pack.__file__)
