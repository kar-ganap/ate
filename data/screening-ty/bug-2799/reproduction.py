"""ty bug #2799: Constraint solver union heuristic is incorrect for mixed variance.

When calling f(Child(), callback) where f[T](t: T, c: Callable[[T], int]) -> T,
the solver should infer T = Child. Instead it unions Child and Base (from the
Callable's contravariant parameter) and gets T = Base, which is wrong.

The fix requires variance-aware constraint combination (lower/upper bounds)
instead of naive union.
"""

from typing import Callable


class Base: ...


class Child(Base): ...


def f[T](t: T, c: Callable[[T], int]) -> T: ...


def callback(x: Base) -> int:
    return 0


result = f(Child(), callback)
reveal_type(result)  # Should be Child, currently Base
