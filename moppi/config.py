"""Configs."""

from pathlib import Path
import tomllib
import tomli_w
import yaml

from moppi.dependency import Dependency


class Config:
    """Config interface."""

    CONFIG_FILE: Path

    def all(self):
        """All installed packages."""

    def save(self):
        """Save the config into a config file."""


class ConfigTOML(Config):
    """Config in pyproject.toml file, using regex."""

    # >>> re.sub('\ndependencies = \[.*?\]\n\n', 'qwe', f, flags=re.DOTALL)


class ConfigTOMLW(Config):
    """Config in pyproject.toml file, using tomli_w."""

    # CONFIG_FILE = Path("test.toml")
    CONFIG_FILE = Path("pyproject.toml")

    dependencies: set[Dependency] = set()
    optional_dependencies: dict[str, set[Dependency]] = {}
    indirect_dependencies: set[Dependency] = set()
    config: dict = {}

    def __init__(self) -> None:
        """Init."""
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, "rb") as toml_file:
                self.config = tomllib.load(toml_file)

        self.dependencies = {
            Dependency.from_string(dep)
            for dep in self.config.get("project", {}).get("dependencies", [])
        }

        for optional, deps in (
            self.config.get("project", {}).get("optional-dependencies", {}).items()
        ):
            for dep in deps:
                self.optional_dependencies.setdefault(optional, set()).add(
                    Dependency.from_string(dep, optional=optional)
                )

        self.indirect_dependencies = {
            Dependency.from_tuple(dep)
            for dep in self.config.get("tool", {}).get("moppi", {}).get("indirect-dependencies", [])
        }

        print("Currently installed", self.all)

    @property
    def all(self):
        """All installed packages."""
        optional_dependencies = {
            dep for deps in self.optional_dependencies.values() for dep in deps
        }  # flattening the dict of sets
        return {
            dependency.name.lower()
            for dependency in self.dependencies | optional_dependencies | self.indirect_dependencies
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
            [dep.as_string(), *set(depn.as_string() for depn in dep.needed_by)]
            for dep in self.indirect_dependencies
        ]

        with open(self.CONFIG_FILE, "wb") as toml_file:
            tomli_w.dump(self.config, toml_file)


class ConfigYAML(Config):
    """Config in moppy.yaml file."""

    CONFIG_FILE = Path("moppi.yaml")

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
