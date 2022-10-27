"""Modern Python Package Installer."""

import argparse
from enum import auto, Enum
import io
import json
import sys
from typing import Self
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import tomlkit
import yaml


class DependencyCategory(Enum):
    """Dependency Category."""

    top_level = auto()
    optional = auto()
    indirect = auto()


class DependencyOperator(Enum):
    """Dependency Operator."""

    equal = "=="
    upper = ">="
    lower = "<="


class Dependency:
    """Dataclass representation of dependency string / tuple."""

    name: str
    version: str
    operator: DependencyOperator

    # pyproject.toml data
    category: DependencyCategory
    optional: str | None = None
    needed_by: list[Self] = []

    # pypi data
    package_url: str
    filename: str
    requires_dist: list[str]

    @classmethod
    def from_string(cls, string: str, optional: str | None = None) -> Self:
        """Create a dependency instance from the "package==1.0" like string."""
        dependency = cls()
        dependency.optional = optional

        for operator in DependencyOperator:
            if operator.value in string:
                dependency.name, dependency.version = string.split(operator.value)
                dependency.operator = operator
                break
        else:
            raise Exception(f"Unknown operator in {string}")  # fix when this happens

        return dependency

    @classmethod
    def from_tuple(cls, array: list[str]) -> Self:
        """Create a dependency instance from a tuple of an indirect dependency."""
        dependency = cls.from_string(array[0])
        dependency.needed_by = [Dependency.from_string(dep) for dep in array[1:]]
        return dependency

    @classmethod
    def from_pypi(cls, info: dict) -> Self:
        """Create a dependency instance from a pypi info."""
        dependency = cls()

        dependency.name = info["info"]["name"]
        dependency.version = info["info"]["version"]
        dependency.operator = DependencyOperator.equal

        dependency.package_url = info["urls"][0]["url"]
        dependency.filename = info["urls"][0]["filename"]
        dependency.requires_dist = info["info"]["requires_dist"]

        return dependency

    def as_string(self) -> str:
        """Return "package==1.0" like string."""
        return f"{self.name}=={self.version}"

    def __repr__(self) -> str:
        """To string."""
        return f"{self.name}{self.operator}{self.version} {self.optional} {self.needed_by}"


class ConfigTOML:
    """Config in pyproject.toml file."""

    CONFIG_FILE = "test.toml"

    def __init__(self) -> None:
        """Init."""
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf8") as toml_file:
                config = tomlkit.load(toml_file)
        except FileNotFoundError:
            config = {}

        self.dependencies = [
            Dependency.from_string(dep) for dep in config.get("project", {}).get("dependencies", [])
        ]
        self.dev_dependencies = [
            Dependency.from_string(dep, optional="dev")
            for dep in config.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        ]
        self.indirect_dependencies = [
            Dependency.from_tuple(dep)
            for dep in config.get("tool", {}).get("moppi", {}).get("indirect-dependencies", {})
        ]
        print("Currently installed", self.all)

    @property
    def all(self):
        """All installed packages."""
        return {
            dependency.name.lower()
            for dependency in self.dependencies + self.dev_dependencies + self.indirect_dependencies
        }

    def save(self):
        """Save the config into moppi.yaml."""
        config = {
            "project": {
                "dependencies": [dep.as_string() for dep in self.dependencies],
                "optional-dependencies": {
                    "dev": [dep.as_string() for dep in self.dev_dependencies],
                },
            },
            "tool": {
                "moppi": {
                    "indirect-dependencies": [
                        [dep.as_string(), *[depn.as_string() for depn in dep.needed_by]]
                        for dep in self.indirect_dependencies
                    ],
                }
            },
        }

        with open(self.CONFIG_FILE, "w", encoding="utf8") as toml_file:
            tomlkit.dump(config, toml_file)


class ConfigYAML:
    """Config in moppy.yaml file."""

    CONFIG_FILE = "moppi.yaml"

    def __init__(self) -> None:
        """Init."""
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf8") as yaml_file:
                config = yaml.load(yaml_file, yaml.Loader)
        except FileNotFoundError:
            config = {}

        self.dependencies = config.get("dependencies", {})
        self.dev_dependencies = config.get("dev_dependencies", {})
        self.indirect_dependencies = config.get("indirect_dependencies", {})
        print("Currently installed", self.all)

    @property
    def all(self):
        """All installed packages."""
        return {
            package.lower()
            for package in self.dependencies.keys()
            | self.dev_dependencies.keys()
            | self.indirect_dependencies.keys()
        }

    def save(self):
        """Save the config into moppi.yaml."""
        config = {
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            "indirect_dependencies": self.indirect_dependencies,
        }

        with open(self.CONFIG_FILE, "w", encoding="utf8") as yaml_file:
            yaml.dump(config, yaml_file)


class Moppi:
    """Moppi package installer."""

    def _parse_args(self) -> tuple[str, list[str]]:
        """Parse the command line args."""
        choices = ("add", "remove", "update", "apply")

        parser = argparse.ArgumentParser("Moppi package installer")
        parser.add_argument("command", type=str, choices=choices, help="Command to execute")
        parser.add_argument("packages", type=str, nargs="*", help="Package name")
        parser.add_argument(
            "--yaml",
            action="store_true",
            dest="use_yaml",
            help="Use moppi.yaml file instead",
        )

        args = parser.parse_args()
        command = args.command
        packages = args.packages
        use_yaml = args.use_yaml

        print(f"Command: {command}, package: {packages}, use_yaml: {use_yaml}")

        self.config = ConfigYAML() if use_yaml else ConfigTOML()

        return command, packages

    def execute_command(self) -> None:
        """Execute add, remove, apply or update."""
        command, packages = self._parse_args()

        if command in ["add", "remove"] and not packages:
            print("No packages specified")
            return

        match command:
            case "add":
                for package in packages:
                    print(f"Adding {package}")
                    self.add(package)

            case "remove":
                for package in packages:
                    print(f"Removing {package}")
                    self.remove(package)

            case "apply":
                print("Applying moppi.conf")
                self.apply()

            case "update":
                for package in packages:
                    print(f"Updating {package}")
                    self.update(package)

    def _get_package_info(self, package: str) -> Dependency:
        """Get a package info from PyPi."""
        url = f"https://pypi.org/pypi/{package}/json"

        print("Getting package info", package)
        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        return Dependency.from_pypi(info)

    def _download(self, dependecy: Dependency) -> None:
        """Download the dependancy and save it to venv."""
        print("Downloading", dependecy.filename)
        data = urllib.request.urlopen(dependecy.package_url).read()
        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])  # need to use sysconfig

    def _install(
        self,
        package: str,
        needed_by: None | list = None,
        optional: str | None = None,
    ) -> None:
        """Install a package."""
        dependecy = self._get_package_info(package)
        self._download(dependecy)

        if needed_by:
            dependecy.needed_by = [needed_by]
            self.config.indirect_dependencies.append(dependecy)
        elif optional:
            self.config.dev_dependencies.append(dependecy)
        else:
            self.config.dependencies.append(dependecy)

        if dependecy.requires_dist:
            for dep in dependecy.requires_dist:
                if "extra" in dep or "platform" in dep:
                    continue

                if " " in dep:
                    dep_package, versions = dep.split(" ", 1)
                elif "==" in dep:
                    dep_package, versions = dep.split("==", 1)
                elif ">=" in dep:
                    dep_package, versions = dep.split(">=", 1)
                else:
                    dep_package, versions = dep, ""

                if dep_package not in self.config.all:
                    print("Dependencies", dep_package, versions)
                    self._install(dep_package, dependecy, optional)

        if needed_by is None:
            self.config.save()

    @classmethod
    def _rmtree(cls, path: Path):
        """Remove files in a path."""
        if path.is_file():
            path.unlink()
        else:
            for child in path.iterdir():
                cls._rmtree(child)
            path.rmdir()

    def add(self, package: str):
        """Add a package."""
        if package.lower() in self.config.all:
            print(f"Package {package} is already installed")
        else:
            self._install(package)

    def remove(self, package: str):
        """Remove a package."""
        package = package.lower()

        if package not in self.config.all:
            print(f"Package {package} is not installed!")
            return

        files = []
        for file in Path(sys.path[-1]).iterdir():
            if file.name.split("-")[0].split(".")[0].lower() == package:
                files.append(file)

        if files:
            print("Removing files:")
            for file in files:
                print(str(file))
                self._rmtree(file)

            self.config.dependencies.pop(package)
            self.config.save()

    def apply(self):
        """Apply the moppi.yaml config."""
        for package in self.config.all:
            for file in Path(sys.path[-1]).iterdir():
                if file.name.split("-")[0].split(".")[0].lower() == package:
                    print(f"Package {package} is already installed")
                    break
            else:
                self._download(package)

    def update(self, package: str):
        """Update a package."""
        package = package.lower()

        if package not in self.config.all:
            print(f"Package {package} is not installed!")
            return

        self._install(package)


if __name__ == "__main__":
    Moppi().execute_command()
