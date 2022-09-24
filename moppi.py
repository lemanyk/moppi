"""
Modern Python Package Installer
"""

import argparse
import io
import json
import sys
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import yaml


def _rmtree(file: Path):
    if file.is_file():
        file.unlink()
    else:
        for child in file.iterdir():
            _rmtree(child)
        file.rmdir()


class Config:
    """Config"""

    CONFIG_FILE = "moppi.yaml"

    def __init__(self) -> None:
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
        """All installed packages"""
        return {
            package.lower()
            for package in self.dependencies.keys()
            | self.dev_dependencies.keys()
            | self.indirect_dependencies.keys()
        }

    def save(self):
        """Save the config into moppi.yaml"""
        config = {
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            "indirect_dependencies": self.indirect_dependencies,
        }

        with open("moppi.yaml", "w", encoding="utf8") as yaml_file:
            yaml.dump(config, yaml_file)


class Moppi:
    """Moppi package installer"""

    def __init__(self) -> None:
        self.config = Config()

    def _parse_args(self) -> tuple[str]:
        """Parse the command line args"""
        choices = ("add", "remove", "update", "apply")

        parser = argparse.ArgumentParser("Moppi package installer")
        parser.add_argument("command", type=str, choices=choices, help="command to execute")
        parser.add_argument("package", type=str, help="package name")

        args = parser.parse_args()
        command = args.command
        package = args.package

        return command, package

    def run(self) -> None:
        """Execute install, remove, update or apply"""
        command, package = self._parse_args()
        match command:
            case "add":
                print(f"Installing {package}")
                self.add(package)
            case "remove":
                print(f"Removing {package}")
                self.remove(package)
            case "update":
                print(f"Updating {package}")
                self.update(package)
            case "apply":
                print("Appliyng moppi.conf")
                self.apply()

    def add(self, package: str, needed_by: None | list = None, is_dev: bool = False) -> None:
        """Install a package"""
        url = f"https://pypi.org/pypi/{package}/json"

        data = urllib.request.urlopen(url).read()
        info = json.loads(data)

        package = info["info"]["name"]
        version = info["info"]["version"]
        package_url = info["urls"][0]["url"]
        filename = info["urls"][0]["filename"]

        if package.lower() in self.config.all:
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

    def remove(self, package: str):
        """Remove a package"""
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
                _rmtree(file)

            self.config.dependencies.pop(package)
            self.config.save()

    def update(self, package: str):
        """Update a package"""

    def apply(self):
        """Apply the moppi.yaml config"""


if __name__ == "__main__":
    # Moppi().install('Werkzeug')
    Moppi().run()
