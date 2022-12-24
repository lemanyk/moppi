"""Config."""

from pathlib import Path

import tomli_w
import tomllib

from moppi.dependency import Dependency


class Config:
    """Config in pyproject.toml file, using tomli_w."""

    # CONFIG_FILE = Path("test.toml")
    CONFIG_FILE = Path("pyproject.toml")

    config_data: dict
    dependencies: list[Dependency]

    def __init__(self) -> None:
        """Load the config file."""
        self.config_data = {}
        self.dependencies = []

        # Read the config file
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, "rb") as toml_file:
                self.config_data = tomllib.load(toml_file)

        # Load the main dependencies
        for dependency_string in self.config_data.get("project", {}).get("dependencies", []):
            dependency = Dependency.from_string(dependency_string)
            if dependency not in self.dependencies:
                self.dependencies.append(dependency)

        # Load the optional dependencies
        optional_deps = self.config_data.get("project", {}).get("optional-dependencies", {})
        for optional, dependency_strings in optional_deps.items():
            for dependency_string in dependency_strings:
                dependency = Dependency.from_string(dependency_string, optional)
                if dependency not in self.dependencies:
                    self.dependencies.append(dependency)

        # Load the indirect dependencies
        for dependency_string in (
            self.config_data.get("tool", {}).get("moppi", {}).get("indirect-dependencies", [])
        ):
            dependency = Dependency.from_composite_string(dependency_string)
            if dependency not in self.dependencies:
                self.dependencies.append(dependency)

        # Load the dependency lock
        for dependency_string in (
            self.config_data.get("tool", {}).get("moppi", {}).get("dependency-lock", [])
        ):
            dependency = Dependency.from_lock_string(dependency_string)
            if dependency not in self.dependencies:
                self.dependencies.append(dependency)

        print("Currently installed", self.dependencies)

    def save(self):
        """Save the config into pyproject.toml."""
        # Clear the config
        self.config_data.setdefault("project", {})["dependencies"] = []
        self.config_data.get("project", {}).pop("optional-dependencies", None)
        self.config_data.get("tool", {}).get("moppi", {}).pop("indirect-dependencies", None)
        self.config_data.get("tool", {}).get("moppi", {}).pop("dependency-lock", None)

        if not self.config_data.get("tool", {}).get("moppi", None):
            self.config_data.get("tool", {}).pop("moppi", None)
        if not self.config_data.get("tool", None):
            self.config_data.pop("tool", None)

        # Dump the dependencies
        for dependency in self.dependencies:
            if dependency.needed_by:
                # Dump the indirect dependencies
                needed_by = " :: ".join(depn.as_string() for depn in dependency.needed_by)
                self.config_data.setdefault("tool", {}).setdefault("moppi", {}).setdefault(
                    "indirect-dependencies", []
                ).append(f"{dependency.as_string()} :: {needed_by}")

            elif dependency.optional:
                # Dump the optional dependencies
                self.config_data.setdefault("project", {}).setdefault(
                    "optional-dependencies", {}
                ).setdefault(dependency.optional, []).append(dependency.as_string())

            else:
                # Dump the main dependencies
                self.config_data.setdefault("project", {}).setdefault("dependencies", []).append(
                    dependency.as_string()
                )

            # Dump the dependency lock
            needed_by = " :: ".join(depn.as_string() for depn in dependency.needed_by)
            if needed_by:
                needed_by = f" :: {needed_by}"
            self.config_data.setdefault("tool", {}).setdefault("moppi", {}).setdefault(
                "dependency-lock", []
            ).append(f"{dependency.as_string()}{needed_by} :: {dependency.sha256}")

        with open(self.CONFIG_FILE, "wb") as toml_file:
            tomli_w.dump(self.config_data, toml_file)
            # re.sub('\ndependencies = \[.*?\]\n\n', 'qwe', f, flags=re.DOTALL)
