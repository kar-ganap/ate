"""ty bug #2732: bool | None not narrowed to bool after == comparison.

After `if bn == b:` where bn: bool | None and b: bool, bn should be
narrowed to bool (since None == bool is always False). Currently it
remains bool | None.
"""


def f(bn: bool | None, b: bool) -> None:
    if bn == b:
        reveal_type(bn)  # Should be bool, currently bool | None
