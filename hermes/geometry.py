"""Points and the distances between them. Knows nothing about hands."""

import math
from typing import NamedTuple, Protocol


class XY(Protocol):
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...


class XYZ(XY, Protocol):
    @property
    def z(self) -> float: ...


class Point(NamedTuple):
    x: float
    y: float
    z: float = 0.0


def distance_2d(a: XY, b: XY) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def distance_3d(a: XYZ, b: XYZ) -> float:
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))
