"""Modern Python Package Installer."""

import argparse
from enum import auto, Enum  # , StrEnum
import io
import json
import sys
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

    category: DependencyCategory
    optional: str | None = None
    needed_by: list = []

    package_url: str
    filename: str

    @classmethod
    def from_string(cls, string: str, optional: str = None):
        """Create a dependency instance from the "package==1.0" like string."""
        dependency = cls()
        dependency.optional = optional

        for operator in DependencyOperator:
            if operator.value in string:
                dependency.name, dependency.version = string.split(operator)
                dependency.operator = operator
                break
        else:
            raise Exception(f"Unknown operator in {string}")  # fix when this happens

        return dependency

    @classmethod
    def from_list(cls, array: list[str]):
        """Create a dependency instance from the list of an indirect dependency."""
        dependency = cls.from_string(array[0])
        dependency.needed_by = [Dependency.from_string(dep) for dep in array[1:]]
        return dependency

    @classmethod
    def from_pypi(cls, info: dict):
        """Create a dependency instance from the pypi info."""
        dependency = cls()

        dependency.name = info["info"]["name"]
        dependency.version = info["info"]["version"]
        dependency.operator = DependencyOperator.equal

        dependency.package_url = info["urls"][0]["url"]
        dependency.filename = info["urls"][0]["filename"]

        return dependency

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
            Dependency(dep) for dep in config.get("project", {}).get("dependencies", [])
        ]
        self.dev_dependencies = [
            Dependency(dep, optional="dev")
            for dep in config.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        ]
        self.indirect_dependencies = [
            Dependency(dep)
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
                "dependencies": self.dependencies,
                "optional-dependencies": {
                    "dev": self.dev_dependencies,
                },
            },
            "tool": {
                "moppi": {
                    "indirect-dependencies": self.indirect_dependencies,
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

    def _parse_args(self) -> tuple[str]:
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

    def _run(self) -> None:
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

    def _get_package_info(self, package):
        """Info."""
        url = f"https://pypi.org/pypi/{package}/json"

        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        return Dependency.from_pypi(info)

    def _download(self, package: str) -> dict:
        """Download a package and save it to venv. Returns a package info."""
        url = f"https://pypi.org/pypi/{package}/json"

        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        package = info["info"]["name"]
        version = info["info"]["version"]
        package_url = info["urls"][0]["url"]
        filename = info["urls"][0]["filename"]

        print("Downloading", filename)
        data = urllib.request.urlopen(package_url).read()

        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])

        return {
            "name": package,
            "sha256": info["urls"][0]["digests"]["sha256"],
            "version": version,
        }

    def add(
        self,
        package: str,
        needed_by: None | list = None,
        is_dev: bool = False,
        force=False,
    ) -> None:
        """Install a package."""
        url = f"https://pypi.org/pypi/{package}/json"

        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        package = info["info"]["name"]
        version = info["info"]["version"]
        package_url = info["urls"][0]["url"]
        filename = info["urls"][0]["filename"]

        if not force and package.lower() in self.config.all:
            print(f"Package {package}=={version} is already installed")
            return

        print("Downloading", filename)

        data = urllib.request.urlopen(package_url).read()
        # open(filename, 'wb').write(data)

        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])

        package_info = {
            "name": package,
            "sha256": info["urls"][0]["digests"]["sha256"],
            "version": version,
        }

        if needed_by:
            package_info["needed_by"] = [needed_by]
            self.config.indirect_dependencies[package] = package_info
        elif is_dev:
            self.config.dev_dependencies[package] = package_info
        else:
            self.config.dependencies[package] = package_info

        if info["info"]["requires_dist"]:
            for dependecy in info["info"]["requires_dist"]:
                if "extra" in dependecy or "platform" in dependecy:
                    continue

                if " " in dependecy:
                    dep_package, versions = dependecy.split(" ", 1)
                elif "==" in dependecy:
                    dep_package, versions = dependecy.split("==", 1)
                elif ">=" in dependecy:
                    dep_package, versions = dependecy.split(">=", 1)
                else:
                    dep_package, versions = dependecy, ""

                if dep_package not in self.config.all:
                    print("Dependencies", dep_package, versions)
                    self.add(dep_package, package, is_dev)

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

        self.add(package, force=True)


if __name__ == "__main__":
    Moppi()._run()
