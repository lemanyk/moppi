"""Modern Python Package Installer."""

import argparse
import http.client
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile

from moppi.config import Config
from moppi.dependency import Dependency


class Moppi:
    """Moppi package installer."""

    config: Config
    connection: http.client.HTTPSConnection | None = None

    def __init__(self) -> None:
        """Initialize the Moppi installer."""
        self.config = Config()

    def execute_command(self) -> None:
        """Execute add, update, remove or apply."""
        command, packages, optional = self._parse_args()

        match command:
            case "add":
                for package_name in packages:
                    print(f"Adding {package_name}")
                    self.add(Dependency(package_name, optional))

            case "update":
                for package_name in packages:
                    print(f"Updating {package_name}")
                    self.update(Dependency(package_name))

            case "remove":
                for package_name in packages:
                    print(f"Removing {package_name}")
                    self.remove(Dependency(package_name))

            case "apply":
                print("Applying pyproject.toml")
                self.apply(optional)

    def add(self, dependency: Dependency):
        """Add a package."""
        if dependency in self.config.dependencies:
            print(f"Package {dependency.name} is already installed")
        else:
            self._install(dependency)
            self.config.save()

    def update(self, dependency: Dependency):
        """Update a package."""
        if dependency not in self.config.dependencies:
            print(f"Package {dependency.name} is not installed.")
            return

        self.remove(dependency)
        self._install(dependency)
        self.config.save()

    def remove(self, dependency: Dependency):
        """Remove a package."""
        if dependency not in self.config.dependencies:
            print(f"Package {dependency.name} is not installed.")
            return

        # remove package from main dependencies
        self.config.dependencies = [dep for dep in self.config.dependencies if dep != dependency]

        # remove indirect dependencies
        packages = [dependency.name] + self._cleanup_indirect(dependency)

        print(f"Removing {packages}")

        # delete files
        files = []
        for file in Path(sys.path[-1]).iterdir():
            if file.name.split("-")[0].split(".")[0].lower() in packages:
                files.append(file)

        if files:
            print("Removing files:")
            for file in files:
                print(str(file))
                self._rmtree(file)

        self.config.save()

    def apply(self, optional: str | None = None):
        """Apply the pyproject.toml / moppi.yaml config."""
        dependencies = self.config.dependencies

        if optional:
            dependencies = [dep for dep in dependencies if dep.optional == optional]

        for dependency in dependencies:
            for file in Path(sys.path[-1]).iterdir():
                dependency_name = dependency.name.lower().replace("-", "_")
                if file.name.split("-")[0].split(".")[0].lower() == dependency_name:
                    print(f"Package {dependency.name} is already installed")
                    break
            else:
                info = self._get_package_info(dependency.name)
                dependency.apply_pypi_info(info)
                self._download(dependency)

    def _parse_args(self) -> tuple[str, list[str], str]:
        """Parse the command line args."""
        choices = ("add", "remove", "update", "apply")

        parser = argparse.ArgumentParser("Moppi package installer")
        parser.add_argument("command", type=str, choices=choices, help="Command to execute")
        parser.add_argument("packages", type=str, nargs="*", help="Package name")

        parser.add_argument("--optional", type=str, help="Optional")
        parser.add_argument(
            "-d", dest="optional", action="store_const", const="dev", help="--optional=dev"
        )
        for optional in ["dev", "test", "cicd", "doc", "tools", "all"]:
            parser.add_argument(
                f"--{optional}",
                dest="optional",
                action="store_const",
                const=optional,
                help=f"--optional={optional}",
            )

        args = parser.parse_args()
        command = args.command
        packages = args.packages
        optional = args.optional

        print(f"Command: {command}, package: {packages}, optional: {optional}")

        if command in ["add", "remove"] and not packages:
            print("No packages specified")
            sys.exit(1)

        return command, packages, optional

    def _get_package_info(self, package: str) -> dict:
        """Get a package info from PyPi."""
        url = f"https://pypi.org/pypi/{package}/json"
        print("Getting package info", package)

        if self.connection is None:
            self.connection = http.client.HTTPSConnection("pypi.org")

        self.connection.request("GET", url)
        response = self.connection.getresponse()

        if response.status == 404:
            raise Exception(f"Package {package} not found")

        data = response.read()
        return json.loads(data)

    def _download(self, dependency: Dependency) -> None:
        """Download the dependancy and save it to venv."""
        print("Downloading", dependency.filename)

        if self.connection is None:
            self.connection = http.client.HTTPSConnection("pypi.org")

        self.connection.request("GET", dependency.package_url)
        response = self.connection.getresponse()
        data = response.read()

        file = ZipFile(io.BytesIO(data))
        file.extractall(sys.path[-1])  # need to use sysconfig

    def _install(self, dependency: Dependency) -> None:
        """Install a package."""
        info = self._get_package_info(dependency.name)
        dependency.apply_pypi_info(info)
        self._download(dependency)

        self.config.dependencies.append(dependency)

        if dependency.requires_dist:
            for dependency_string in dependency.requires_dist:
                if ";" in dependency_string:  # or "extra" in dep or "platform" in dep:
                    continue
                # if "jaraco" in dep.lower():
                #     assert 0

                new_dependency = Dependency.from_string(dependency_string)
                new_dependency.needed_by.append(dependency)

                if new_dependency not in self.config.dependencies:
                    print("Dependencies", new_dependency.name, new_dependency.version)
                    self._install(new_dependency)

    def _cleanup_indirect(self, dependency: Dependency) -> list[str]:
        """Cleanup indirect dependencies."""
        packages = []  # packages to remove
        for dep in self.config.dependencies.copy():
            dep.needed_by = [depn for depn in dep.needed_by if depn != dependency]
            if not dep.needed_by:
                # print(333, dependency.name, self.config.indirect_dependencies)
                packages.append(dep.name.lower())
                self.config.dependencies = [d for d in self.config.dependencies if d != dep]
                packages += self._cleanup_indirect(dep)

        return packages

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
