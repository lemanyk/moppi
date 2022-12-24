"""
Moppi installer tests.

python -m unittest discover -s tests/

python -m build
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps moppi
"""

import sys
import unittest
from pathlib import Path

import tomli_w
import tomllib

from moppi.config import Config
from moppi.dependency import Dependency
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
        Config.CONFIG_FILE = Path("test1.toml")
        Config.CONFIG_FILE.unlink(missing_ok=True)

    # def tearDown(self) -> None:
    #     """Remove the test.toml file."""
    #     Path("test.toml").unlink(missing_ok=True)

    def test_add(self):
        """Test adding a package."""
        # install a package
        dependency = Dependency("Werkzeug")
        m = Moppi()
        m.add(dependency)

        # check whether the config file was updated
        with open(Config.CONFIG_FILE, "rb") as toml_file:
            config = tomllib.load(toml_file)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": ["Werkzeug==2.2.2"]},
                    "tool": {
                        "moppi": {
                            "dependency-lock": [
                                "Werkzeug==2.2.2 :: f979ab81f58d7318e064e99c4506445d60135ac5cd2e177a2de0089bfd4c9bd5",
                                "MarkupSafe==2.1.1 :: Werkzeug==2.2.2 :: 86b1f75c4e7c2ac2ccdaec2b9022845dbb81880ca318bb7a0a01fbf7813e3812",
                            ],
                            "indirect-dependencies": ["MarkupSafe==2.1.1 :: Werkzeug==2.2.2"],
                        }
                    },
                },
            )

        # check whether the package exists in .env
        venv = Path(sys.path[-1])
        files = list(venv.glob(f"*{dependency.name}*"))
        self.assertTrue(files)

        # import the package
        pack = __import__(dependency.name.lower())
        self.assertTrue(pack.__file__)

    def test_update(self):
        """Test updating a package."""
        # update
        dependency = Dependency("Werkzeug")
        m = Moppi()
        m.add(dependency)
        m.update(dependency)

        # check whether the config file was updated
        with open(Config.CONFIG_FILE, "rb") as toml_file:
            config = tomllib.load(toml_file)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": ["Werkzeug==2.2.2"]},
                    "tool": {
                        "moppi": {
                            "dependency-lock": [
                                "Werkzeug==2.2.2 :: f979ab81f58d7318e064e99c4506445d60135ac5cd2e177a2de0089bfd4c9bd5",
                                "MarkupSafe==2.1.1 :: Werkzeug==2.2.2 :: 86b1f75c4e7c2ac2ccdaec2b9022845dbb81880ca318bb7a0a01fbf7813e3812",
                            ],
                            "indirect-dependencies": ["MarkupSafe==2.1.1 :: Werkzeug==2.2.2"],
                        }
                    },
                },
            )

    def test_remove(self):
        """Test removing a package."""
        # remove a package
        dependency = Dependency("Werkzeug")
        m = Moppi()
        m.add(dependency)
        m.remove(dependency)

        # check whether the config file was updated
        with open(Config.CONFIG_FILE, "rb") as toml_file:
            config = tomllib.load(toml_file)
            self.assertEqual(
                config,
                {
                    "project": {"dependencies": []},
                },
            )

    def test_apply(self):
        """Test installing packages from the config file."""
        # create config
        config = {
            "project": {"dependencies": ["Werkzeug==2.2.2"]},
            "tool": {"moppi": {"indirect-dependencies": ["MarkupSafe==2.1.1 :: Werkzeug==2.2.2"]}},
        }
        with open(Config.CONFIG_FILE, "wb") as toml_file:
            tomli_w.dump(config, toml_file)

        # apply
        dependency = Dependency("Werkzeug")
        m = Moppi()
        m.apply()

        # check whether the package exists in .env
        venv = Path(sys.path[-1])
        files = list(venv.glob(f"*{dependency.name}*"))
        self.assertTrue(files)

        # import the package
        pack = __import__(dependency.name.lower())
        self.assertTrue(pack.__file__)
