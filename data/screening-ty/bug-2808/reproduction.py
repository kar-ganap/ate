"""ty bug #2808: Hang when analyzing loop with recursive self-reference.

ty hangs (infinite loop in fixpoint computation) on this code.
The recursive `b = [b]` creates types that cause widening to not converge.
Regression introduced by PR #22794 — ty 0.0.16 did not hang.
"""

for i in range(1):
    if a:
        b = [b]
    else:
        b = -[b]
