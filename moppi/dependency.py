"""Dependency."""

import re
from enum import Enum
from typing import Self


class DependencyOperator(Enum):
    """Dependency Operator."""

    equal = "=="
    upper = ">="
    lower = "<="
    # space = " "
    # not_equal = "!="

    def __repr__(self) -> str:
        """To string."""
        return f"{self.value}"

    __str__ = __repr__


class Dependency:
    """Dataclass representation of a dependency string / tuple / pypi info."""

    name: str
    version: str = ""
    operator: DependencyOperator = DependencyOperator.equal

    # pyproject.toml data
    optional: str | None = None
    needed_by: list[Self]  # list of packages that have this as a direct dependency

    # pypi data
    package_url: str
    filename: str
    requires_dist: list[str]
    sha256: str = "hashqwe"

    def __init__(self, name: str, optional: str | None = None) -> None:
        """."""
        self.name = name
        self.optional = optional
        self.needed_by = []

    @classmethod
    def from_string(cls, string: str, optional: str | None = None) -> Self:
        """Create a dependency instance from the "package==1.0" like string."""
        # print(f"Dependency.from_string: {string}")
        string = string.replace(" ", "").replace("(", "").replace(")", "")

        # match the package name at the start of the string
        match = re.match(r"^([\w\.-]+)([^\w\.-].*)?$", string)
        if not match:
            raise Exception(f"Unknown dependency string: {string}")
        package_name = match.group(1)
        constraints_string = match.group(2) or ""

        # find all version constraints
        constraints = re.split(r",", constraints_string)
        constraints = [c.strip() for c in constraints if c.strip()]

        # create the dependency
        dependency = cls(package_name, optional)

        for operator in DependencyOperator:
            if operator.value in string:
                operator_constraints = [c for c in constraints if c.startswith(operator.value)]
                dependency.version = operator_constraints[0].split(operator.value)[1]
                dependency.operator = operator
                break
        # else:
        #     raise Exception(f"Unknown operator in {string}")  # fix when this happens

        return dependency

    @classmethod
    def from_tuple(cls, array: list[str]) -> Self:
        """Create a dependency instance from a tuple of an indirect dependency."""
        dependency = cls.from_string(array[0])
        dependency.needed_by = [Dependency.from_string(dep) for dep in array[1:]]
        return dependency

    @classmethod
    def from_composite_string(cls, string: str) -> Self:
        """Create a dependency instance from a composite string of an indirect dependency."""
        dependency = cls.from_string(string.split(" :: ")[0])
        dependency.needed_by = [Dependency.from_string(dep) for dep in string.split(" :: ")[1:]]
        return dependency

    @classmethod
    def from_lock_string(cls, string: str) -> Self:
        """Create a dependency instance from a lock string."""
        parts = string.split(" :: ")

        dependency = cls.from_string(parts[0])
        dependency.needed_by = [Dependency.from_string(dep) for dep in parts[1:-1]]
        dependency.sha256 = parts[-1]

        return dependency

    def apply_pypi_info(self, info: dict) -> None:
        """Apply a PyPI info to the dependency instance."""
        self.name = info["info"]["name"]
        self.version = info["info"]["version"]
        self.operator = DependencyOperator.equal

        self.package_url = info["urls"][0]["url"]
        self.filename = info["urls"][0]["filename"]
        self.requires_dist = info["info"]["requires_dist"]
        self.sha256 = info["urls"][0]["digests"]["sha256"]

    def as_string(self) -> str:
        """Return "package==1.0" like string."""
        return f"{self.name}{self.operator}{self.version}"

    def __repr__(self) -> str:
        """To string."""
        return f"{self.name}{self.operator}{self.version} {self.optional} {self.needed_by}"

    def __eq__(self, other: Self) -> bool:
        return self.name.lower() == other.name.lower()
