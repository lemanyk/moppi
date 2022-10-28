"""Modern Python Package Installer."""

import argparse
from enum import auto, Enum
import io
import json
from pathlib import Path
import sys
import tomllib
import tomli_w
from typing import Self  # type: ignore
import urllib.request
import yaml
from zipfile import ZipFile


class DependencyCategory(Enum):
    """Dependency Category."""

    top_level = auto()  # root
    optional = auto()
    indirect = auto()


class DependencyOperator(Enum):
    """Dependency Operator."""

    equal = "=="
    upper = ">="
    lower = "<="
    space = " "


class Dependency:
    """Dataclass representation of a dependency string / tuple / pypi info."""

    name: str
    version: str
    operator: DependencyOperator

    # pyproject.toml data
    category: DependencyCategory
    optional: str | None = None
    needed_by: list[Self] = []  # list of packages that have this as a direct dependency

    # pypi data
    package_url: str
    filename: str
    requires_dist: list[str]

    @classmethod
    def from_string(cls, string: str, optional: str | None = None) -> Self:
        """Create a dependency instance from the "package==1.0" like string."""
        dependency = cls()
        dependency.optional = optional

        string = string.replace(" ", "").replace("(", "").replace(")", "")

        for operator in DependencyOperator:
            if operator.value in string:
                dependency.name, dependency.version = string.split(operator.value)
                dependency.operator = operator
                break
        else:
            # raise Exception(f"Unknown operator in {string}")  # fix when this happens
            dependency.name = string

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

    CONFIG_FILE: Path = Path("test.toml")

    dependencies: list[Dependency] = []
    optional_dependencies: dict[str, list[Dependency]] = {}
    indirect_dependencies: list[Dependency] = []
    config: dict = {}

    def __init__(self) -> None:
        """Init."""
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, "rb") as toml_file:
                self.config = tomllib.load(toml_file)

        self.dependencies = [
            Dependency.from_string(dep)
            for dep in self.config.get("project", {}).get("dependencies", [])
        ]

        for optional, deps in (
            self.config.get("project", {}).get("optional-dependencies", {}).items()
        ):
            for dep in deps:
                self.optional_dependencies[optional] = [
                    Dependency.from_string(dep, optional=optional)
                ]

        self.indirect_dependencies = [
            Dependency.from_tuple(dep)
            for dep in self.config.get("tool", {}).get("moppi", {}).get("indirect-dependencies", {})
        ]

        print("Currently installed", self.all)

    @property
    def all(self):
        """All installed packages."""
        optional_dependencies = [
            dep for deps in self.optional_dependencies.values() for dep in deps
        ]  # flattening the dict of lists
        return {
            dependency.name.lower()
            for dependency in self.dependencies + optional_dependencies + self.indirect_dependencies
        }

    def save(self):
        """Save the config into pyproject.toml."""
        self.config.setdefault("project", {})["dependencies"] = [
            dep.as_string() for dep in self.dependencies
        ]

        if self.optional_dependencies:
            self.config.setdefault("project", {})["optional-dependencies"] = {
                optional: [dep.as_string() for dep in self.optional_dependencies[optional]]
                for optional in self.optional_dependencies
            }
        else:
            self.config["project"].pop("optional-dependencies", None)

        self.config.setdefault("tool", {}).setdefault("moppi", {})["indirect-dependencies"] = [
            [dep.as_string(), *[depn.as_string() for depn in dep.needed_by]]
            for dep in self.indirect_dependencies
        ]

        with open(self.CONFIG_FILE, "wb") as toml_file:
            tomli_w.dump(self.config, toml_file)

        # >>> re.sub('\ndependencies = \[.*?\]\n\n', 'qwe', f, flags=re.DOTALL)


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
            yaml.dump(config, yaml_file)  # type: ignore


class Moppi:
    """Moppi package installer."""

    config: ConfigTOML

    def execute_command(self) -> None:
        """Execute add, update, remove or apply."""
        command, packages, optional = self._parse_args()

        if command in ["add", "remove"] and not packages:
            print("No packages specified")
            return

        match command:
            case "add":
                for package in packages:
                    print(f"Adding {package}")
                    self.add(package, optional)

            case "update":
                for package in packages:
                    print(f"Updating {package}")
                    self.update(package)

            case "remove":
                for package in packages:
                    print(f"Removing {package}")
                    self.remove(package)

            case "apply":
                print("Applying moppi.conf")
                self.apply()

    def add(self, package: str, optional: str | None = None):
        """Add a package."""
        if package.lower() in self.config.all:
            print(f"Package {package} is already installed")
        else:
            self._install(package, optional)
            self.config.save()

    def update(self, package: str):
        """Update a package."""
        package = package.lower()

        if package not in self.config.all:
            print(f"Package {package} is not installed!")
            return

        self._install(package)
        self.config.save()

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

            self.config.dependencies = [
                dep for dep in self.config.dependencies if dep.name.lower() != package
            ]
            self.config.save()

    def apply(self):
        """Apply the pyproject.toml / moppi.yaml config."""
        for package in self.config.all:
            for file in Path(sys.path[-1]).iterdir():
                if file.name.split("-")[0].split(".")[0].lower() == package:
                    print(f"Package {package} is already installed")
                    break
            else:
                dependency = self._get_package_info(package)
                self._download(dependency)

    def _parse_args(self) -> tuple[str, list[str], str]:
        """Parse the command line args."""
        choices = ("add", "remove", "update", "apply")

        parser = argparse.ArgumentParser("Moppi package installer")
        parser.add_argument("command", type=str, choices=choices, help="Command to execute")
        parser.add_argument("packages", type=str, nargs="*", help="Package name")

        parser.add_argument("--optional", type=str, help="Optional")

        for optional in ["dev", "test", "ci", "doc", "all"]:
            parser.add_argument(
                f"--{optional}",
                dest="optional",
                action="store_const",
                const=optional,
                help=f"Optional == {optional}",
            )

        parser.add_argument(
            "--yaml", dest="use_yaml", action="store_true", help="Use moppi.yaml file instead"
        )

        args = parser.parse_args()
        command = args.command
        packages = args.packages
        optional = args.optional
        use_yaml = args.use_yaml

        print(f"Command: {command}, package: {packages}, optional: {optional} use_yaml: {use_yaml}")

        self.config = ConfigTOML()
        # self.config = ConfigYAML() if use_yaml else ConfigTOML()

        return command, packages, optional

    def _get_package_info(self, package: str) -> Dependency:
        """Get a package info from PyPi."""
        url = f"https://pypi.org/pypi/{package}/json"

        print("Getting package info", package)
        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        return Dependency.from_pypi(info)

    def _download(self, dependency: Dependency) -> None:
        """Download the dependancy and save it to venv."""
        print("Downloading", dependency.filename)
        data = urllib.request.urlopen(dependency.package_url).read()
        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])  # need to use sysconfig

    def _install(self, package: str, optional: str | None = None) -> None:
        """Install a package."""
        dependency = self._get_package_info(package)
        self._download(dependency)

        if dependency.needed_by:
            self.config.indirect_dependencies.append(dependency)
        elif optional:
            self.config.optional_dependencies.setdefault(optional, []).append(dependency)
        else:
            self.config.dependencies.append(dependency)

        if dependency.requires_dist:
            for dep in dependency.requires_dist:
                if ";" in dep:  # or "extra" in dep or "platform" in dep:
                    continue

                new_dependency = Dependency.from_string(dep)
                new_dependency.needed_by.append(dependency)

                if new_dependency.name.lower() not in self.config.all:
                    print("Dependencies", new_dependency.name, new_dependency.version)
                    self._install(new_dependency.name, optional=optional)

    @classmethod
    def _rmtree(cls, path: Path):
        """Remove files in a path."""
        if path.is_file():
            path.unlink()
        else:
            for child in path.iterdir():
                cls._rmtree(child)
            path.rmdir()


if __name__ == "__main__":
    Moppi().execute_command()
