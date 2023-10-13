__all__ = ["Version"]

import re
from functools import total_ordering
from typing import Sequence, Union, Optional, Any

PreRelease = Sequence[Union[str, int]]
BuildMetaData = Sequence[Union[str, int]]

REGEX_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(-(?P<pre_release>[-\da-zA-Z]+(\.[-\da-zA-Z]+)*)+)?"
    r"(\+(?P<build_metadata>[-\da-zA-Z]*))?"
)


@total_ordering
class Version:
    __slots__ = (
        "_major",
        "_minor",
        "_patch",
        "_pre_release",
        "_build_metadata",
    )

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        pre_release: Optional[PreRelease] = None,
        build_metadata: Optional[BuildMetaData] = None,
    ) -> None:
        if major < 0:
            raise ValueError("The major version must be non-negative integer")
        if minor < 0:
            raise ValueError("The minor version must be non-negative integer")
        if patch < 0:
            raise ValueError("The minor version must be non-negative integer")
        if pre_release is not None:
            validate_pre_release(pre_release)
        if build_metadata is not None:
            validate_build_metadata(build_metadata)

        self._major = major
        self._minor = minor
        self._patch = patch
        self._pre_release = pre_release
        self._build_metadata = build_metadata

    @property
    def major(self) -> int:
        return self._major

    @property
    def minor(self) -> int:
        return self._minor

    @property
    def patch(self) -> int:
        return self._patch

    @property
    def pre_release(self) -> Optional[PreRelease]:
        return self._pre_release

    @property
    def build_metadata(self) -> Optional[BuildMetaData]:
        return self._build_metadata

    @classmethod
    def parse(cls, value: str, /) -> "Version":
        match = REGEX_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(
                f"'{value}' is not a valid semantic version number"
            )
        groups = match.groupdict()
        major = int(groups["major"])
        minor = int(groups["minor"])
        patch = int(groups["patch"])
        pre_release = parse_pre_release(groups["pre_release"])
        build_metadata = parse_build_metadata(groups["build_metadata"])
        return cls(major, minor, patch, pre_release, build_metadata)

    def to_string(
        self,
        *,
        with_pre_release: bool = True,
        with_build_metadata: bool = True,
    ) -> str:
        value = f"{self._major}.{self._minor}.{self._patch}"
        if with_pre_release and self._pre_release is not None:
            value += "-" + ".".join(map(str, self._pre_release))
        if with_build_metadata and self._build_metadata is not None:
            value += "+" + ".".join(map(str, self._build_metadata))
        return value

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.({self})"

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self._major,
                self._minor,
                self._patch,
                self._pre_release,
                self._build_metadata,
            )
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Version):
            return (
                self._major == other._major
                and self._minor == other._minor
                and self._patch == other._patch
                and self._pre_release == other._pre_release
                and self._build_metadata == other._build_metadata
            )
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Version):
            if (
                self._major < other._major
                or self._minor < other._minor
                or self._patch < other._patch
            ):
                return True
            if not self._pre_release or not other._pre_release:
                return bool(not other._pre_release and self._pre_release)
            for self_value, other_value in zip(
                self._pre_release, other._pre_release
            ):
                if self_value != other_value:
                    return (
                        (
                            isinstance(self_value, int)
                            and isinstance(other_value, str)
                        )
                        or (
                            isinstance(self_value, int)
                            and isinstance(other_value, int)
                            and self_value < other_value
                        )
                        or (
                            isinstance(self_value, str)
                            and isinstance(other_value, str)
                            and self_value < other_value
                        )
                    )
            return len(self._pre_release) < len(other._pre_release)
        return NotImplemented


def parse_pre_release(value: str) -> PreRelease:
    pre_release: list[Union[str, int]] = []
    for identifier in value.split("."):
        if not identifier.isdigit():
            pre_release.append(identifier)
        elif identifier.startswith("0"):
            raise ValueError(
                "Pre-release's numeric identifier has leading zero: %s"
                % identifier
            )
        else:
            pre_release.append(int(identifier))
    return tuple(pre_release)


def parse_build_metadata(value: str) -> BuildMetaData:
    return tuple(
        identifier if not identifier.isdigit() else int(identifier)
        for identifier in value.split(".")
    )


def validate_pre_release(value: PreRelease) -> None:
    if len(value) == 0:
        raise ValueError("Cannot be empty")
    for identifier in value:
        if isinstance(identifier, int) and identifier < 0:
            raise ValueError(
                f"Negative numeric identifier is not allowed: {identifier}"
            )
        if isinstance(identifier, str) and identifier.isdigit():
            raise ValueError(
                f"Alphanumeric identifier should be numeric: '{identifier}'"
            )


def validate_build_metadata(value: BuildMetaData) -> None:
    if not value:
        raise ValueError("Build metadata cannot be empty")
    for identifier in value:
        if isinstance(identifier, int) and identifier < 0:
            raise ValueError("Build metadata has negative numeric identifier")
        if isinstance(identifier, str) and identifier.isdigit():
            raise ValueError(
                "Build metadata numeric identifier should not be a string"
            )
