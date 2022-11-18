"""Modern Python Package Installer."""

import argparse
import io
import json
from pathlib import Path
import sys
import urllib.request
from zipfile import ZipFile

from moppi.config import ConfigTOMLW
from moppi.dependency import Dependency


class Moppi:
    """Moppi package installer."""

    config: ConfigTOMLW

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
            self._install(Dependency(package), optional)
            self.config.save()

    def update(self, package: str):
        """Update a package."""
        package = package.lower()

        if package not in self.config.all:
            print(f"Package {package} is not installed!")
            return

        self.remove(package)
        self._install(Dependency(package))
        self.config.save()

    def remove(self, package: str):
        """Remove a package."""
        package = package.lower()

        if package not in self.config.all:
            print(f"Package {package} is not installed!")
            return

        # remove package from main dependencies
        self.config.dependencies = {
            dep for dep in self.config.dependencies if dep.name.lower() != package
        }

        # remove indirect dependencies
        packages = {package}
        for dependency in self.config.indirect_dependencies.copy():
            dependency.needed_by = {
                dep for dep in dependency.needed_by if dep.name.lower() != package
            }
            if not dependency.needed_by:
                packages.add(dependency.name)
                self.config.indirect_dependencies.remove(dependency)

        # delete files
        files = []
        for file in Path(sys.path[-1]).iterdir():
            if file.name.split("-")[0].split(".")[0].lower() == package:
                files.append(file)

        if files:
            print("Removing files:")
            for file in files:
                print(str(file))
                self._rmtree(file)

        self.config.save()

    def apply(self):
        """Apply the pyproject.toml / moppi.yaml config."""
        for package in self.config.all:
            for file in Path(sys.path[-1]).iterdir():
                if file.name.split("-")[0].split(".")[0].lower() == package:
                    print(f"Package {package} is already installed")
                    break
            else:
                info = self._get_package_info(package)
                dependency = Dependency(package)
                dependency.apply_pypi_info(info)
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

        self.config = ConfigTOMLW()
        # self.config = ConfigYAML() if use_yaml else ConfigTOML()

        return command, packages, optional

    def _get_package_info(self, package: str) -> dict:
        """Get a package info from PyPi."""
        url = f"https://pypi.org/pypi/{package}/json"

        print("Getting package info", package)
        data = urllib.request.urlopen(url).read()
        return json.loads(data)

    def _download(self, dependency: Dependency) -> None:
        """Download the dependancy and save it to venv."""
        print("Downloading", dependency.filename)
        data = urllib.request.urlopen(dependency.package_url).read()
        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])  # need to use sysconfig

    def _install(self, dependency: Dependency, optional: str | None = None) -> None:
        """Install a package."""
        info = self._get_package_info(dependency.name)
        dependency.apply_pypi_info(info)
        self._download(dependency)

        if dependency.needed_by:
            self.config.indirect_dependencies.add(dependency)
        elif optional:
            self.config.optional_dependencies.setdefault(optional, set()).add(dependency)
        else:
            self.config.dependencies.add(dependency)

        if dependency.requires_dist:
            for dep in dependency.requires_dist:
                if ";" in dep:  # or "extra" in dep or "platform" in dep:
                    continue

                new_dependency = Dependency.from_string(dep)
                new_dependency.needed_by.add(dependency)

                if new_dependency.name.lower() not in self.config.all:
                    print("Dependencies", new_dependency.name, new_dependency.version)
                    self._install(new_dependency, optional=optional)

    @classmethod
    def _rmtree(cls, path: Path):
        """Remove files in a path."""
        if path.is_file():
            path.unlink()
        else:
            for child in path.iterdir():
                cls._rmtree(child)
            path.rmdir()


def main():
    """Execute the moppi installer."""
    Moppi().execute_command()


if __name__ == "__main__":
    main()
