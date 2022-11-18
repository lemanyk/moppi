"""Dependency."""

from enum import auto, Enum
from typing import Self  # type: ignore


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

    def __repr__(self) -> str:
        """To string."""
        return f"{self.value}"

    __str__ = __repr__


class Dependency:
    """Dataclass representation of a dependency string / tuple / pypi info."""

    name: str
    version: str
    operator: DependencyOperator

    # pyproject.toml data
    category: DependencyCategory
    optional: str | None = None
    needed_by: set[Self]  # set of packages that have this as a direct dependency

    # pypi data
    package_url: str
    filename: str
    requires_dist: list[str]

    def __init__(self, name: str) -> None:
        """."""
        self.name = name
        self.needed_by = set()

    @classmethod
    def from_string(cls, string: str, optional: str | None = None) -> Self:
        """Create a dependency instance from the "package==1.0" like string."""
        string = string.replace(" ", "").replace("(", "").replace(")", "")

        for operator in DependencyOperator:
            if operator.value in string:
                name, version = string.split(operator.value)
                dependency = cls(name)
                dependency.version = version
                dependency.operator = operator
                break
        else:
            # raise Exception(f"Unknown operator in {string}")  # fix when this happens
            dependency = cls(string)

        dependency.optional = optional
        return dependency

    @classmethod
    def from_tuple(cls, array: list[str]) -> Self:
        """Create a dependency instance from a tuple of an indirect dependency."""
        dependency = cls.from_string(array[0])
        dependency.needed_by = set(Dependency.from_string(dep) for dep in array[1:])
        return dependency

    def apply_pypi_info(self, info: dict):
        """Apply a PyPI info to the dependency instance."""
        self.name = info["info"]["name"]
        self.version = info["info"]["version"]
        self.operator = DependencyOperator.equal

        self.package_url = info["urls"][0]["url"]
        self.filename = info["urls"][0]["filename"]
        self.requires_dist = info["info"]["requires_dist"]

    def as_string(self) -> str:
        """Return "package==1.0" like string."""
        return f"{self.name}{self.operator}{self.version}"

    def __repr__(self) -> str:
        """To string."""
        return f"{self.name}{self.operator}{self.version} {self.optional} {self.needed_by}"
