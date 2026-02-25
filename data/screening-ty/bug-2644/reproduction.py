"""ty bug #2644: getattr narrowing with string literal.

ty should narrow `x` after `getattr(x, "flag")` since it knows the
attribute name is a string literal, but it currently does not.
"""


class C:
    flag: bool


def f(x: C | None) -> None:
    if getattr(x, "flag"):
        reveal_type(x)  # Should narrow to C, currently doesn't
