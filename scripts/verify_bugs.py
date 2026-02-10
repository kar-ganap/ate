"""Verify all 8 primary bugs reproduce against pinned Ruff build."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

RUFF_BINARY = Path(__file__).parent.parent / "data" / "ruff" / "target" / "debug" / "ruff"


@dataclass
class BugRepro:
    bug_id: int
    title: str
    code: str
    rules: list[str]
    check_fn: str  # name of check function
    extra_args: list[str] | None = None
    config: str | None = None  # ruff.toml content
    use_fix: bool = False
    use_format: bool = False  # use `ruff format` instead of `ruff check`
    format_args: list[str] | None = None
    # Extra files to create (path relative to tmpdir -> content)
    extra_files: dict[str, str] = field(default_factory=dict)
    # If set, use this filename instead of "repro.py"
    filename: str = "repro.py"


REPROS: list[BugRepro] = [
    BugRepro(
        bug_id=20945,
        title="FAST001 false positive (None==None)",
        # Key: Foo and Item must NOT be defined so they resolve to None.
        # None==None triggers false positive "redundant response_model".
        code="""\
from __future__ import annotations
from fastapi import FastAPI

app = FastAPI()

@app.post("/items/", response_model=Foo)
async def create_item(item: Item) -> Item:
    return item
""",
        rules=["FAST"],
        check_fn="check_has_diagnostic",
        extra_args=["--preview"],
    ),
    BugRepro(
        bug_id=18654,
        title="ARG001 false positive (@singledispatch)",
        code="""\
from functools import singledispatch

@singledispatch
def extract_step(item, step_name, items, idx):
    raise NotImplementedError

@extract_step.register
def _(item: str, step_name: str, items: list, idx: int):
    return item

@extract_step.register
def _(item: int, step_name: str, items: list, idx: int):
    return None
""",
        rules=["ARG001"],
        check_fn="check_has_diagnostic",
    ),
    BugRepro(
        bug_id=7847,
        title="B023 false positive (immediate invocation)",
        code="""\
def make_squared_list(size: int) -> list[int]:
    result = []
    for i in range(size):
        square = i**2
        def _append_to_result() -> None:
            result.append(square)
        _append_to_result()
    return result
""",
        rules=["B023"],
        check_fn="check_has_diagnostic",
    ),
    BugRepro(
        bug_id=4384,
        title="C901 false positive (closure complexity)",
        code="""\
from functools import wraps

def wrapper(f):
    @wraps(f)
    def wrapped_f(*args, **kwargs):
        if 1 == 1:
            pass
        if 1 == 1:
            pass
        if 1 == 1:
            pass
        return f(*args, **kwargs)
    return wrapped_f
""",
        rules=["C901"],
        check_fn="check_outer_flagged",
        config="[lint.mccabe]\nmax-complexity = 3\n",
    ),
    BugRepro(
        bug_id=19301,
        title="Parser indentation after backslashes",
        code="if True:\n    pass\n    \\\n        print(\"1\")\n",
        rules=[],
        check_fn="check_has_syntax_error",
    ),
    BugRepro(
        bug_id=22221,
        title="F401 fix infinite loop (__all__ duplicates)",
        # This bug needs a package structure: foo/__init__.py importing foo.bar and foo.baz
        filename="foo/__init__.py",
        code="""\
import foo.bar
import foo.baz

__all__ = []
""",
        extra_files={
            "foo/bar/__init__.py": "",
            "foo/baz/__init__.py": "",
        },
        rules=["F401"],
        check_fn="check_convergence_failure",
        use_fix=True,
        extra_args=["--preview"],
    ),
    BugRepro(
        bug_id=22528,
        title="Parser false syntax error (match-like)",
        code="""\
from re import match

match[0]: int
""",
        rules=[],
        check_fn="check_has_syntax_error",
    ),
    BugRepro(
        bug_id=22494,
        title="Formatter range formatting (semicolons)",
        code="""\
class Foo:
    x=1;x=2
""",
        rules=[],
        check_fn="check_range_format_bug",
        use_format=True,
        format_args=["--range=2:9-2:12"],
    ),
]


def run_ruff(
    file_path: Path,
    rules: list[str],
    extra_args: list[str] | None = None,
    config_path: Path | None = None,
    use_fix: bool = False,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(RUFF_BINARY), "check", str(file_path)]
    if rules:
        cmd.extend(["--select", ",".join(rules)])
    if config_path:
        cmd.extend(["--config", str(config_path)])
    if use_fix:
        cmd.append("--fix")
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def run_ruff_format(
    file_path: Path,
    format_args: list[str] | None = None,
    config_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(RUFF_BINARY), "format", str(file_path)]
    if config_path:
        cmd.extend(["--config", str(config_path)])
    if format_args:
        cmd.extend(format_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def check_has_diagnostic(result: subprocess.CompletedProcess[str], _repro: BugRepro) -> bool:
    """Bug reproduces if ruff reports a diagnostic (false positive)."""
    return result.returncode != 0 and len(result.stdout.strip()) > 0


def check_outer_flagged(result: subprocess.CompletedProcess[str], _repro: BugRepro) -> bool:
    """Bug reproduces if 'wrapper' (outer fn) is flagged for complexity."""
    return "wrapper" in result.stdout and "C901" in result.stdout


def check_has_syntax_error(result: subprocess.CompletedProcess[str], _repro: BugRepro) -> bool:
    """Bug reproduces if ruff reports a syntax error for valid Python."""
    output = result.stdout + result.stderr
    return "SyntaxError" in output or "syntax" in output.lower()


def check_convergence_failure(
    result: subprocess.CompletedProcess[str], _repro: BugRepro
) -> bool:
    """Bug reproduces if --fix hits convergence limit (infinite loop)."""
    output = result.stdout + result.stderr
    return "converge" in output.lower() or "100 iterations" in output.lower()


def check_range_format_bug(
    result: subprocess.CompletedProcess[str],
    _repro: BugRepro,
    file_path: Path | None = None,
) -> bool:
    """Bug reproduces if range formatting doesn't split semicolons properly."""
    if file_path is None:
        return False
    content = file_path.read_text()
    # Bug: semicolons remain on the same line instead of being split
    return ";" in content


CHECK_FNS: dict[str, object] = {
    "check_has_diagnostic": check_has_diagnostic,
    "check_outer_flagged": check_outer_flagged,
    "check_has_syntax_error": check_has_syntax_error,
    "check_convergence_failure": check_convergence_failure,
    "check_range_format_bug": check_range_format_bug,
}


def verify_bug(repro: BugRepro) -> tuple[bool, str]:
    """Verify a single bug reproduces. Returns (reproduced, details)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        file_path = tmpdir_path / repro.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(repro.code)

        # Create any extra files needed (e.g., package structure)
        for rel_path, content in repro.extra_files.items():
            extra = tmpdir_path / rel_path
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text(content)

        config_path = None
        if repro.config:
            config_path = tmpdir_path / "ruff.toml"
            config_path.write_text(repro.config)

        try:
            if repro.use_format:
                result = run_ruff_format(
                    file_path,
                    format_args=repro.format_args,
                    config_path=config_path,
                )
            else:
                result = run_ruff(
                    file_path,
                    repro.rules,
                    extra_args=repro.extra_args,
                    config_path=config_path,
                    use_fix=repro.use_fix,
                )
        except subprocess.TimeoutExpired:
            return True, "TIMEOUT (likely infinite loop — bug reproduces)"

        check_fn = CHECK_FNS[repro.check_fn]

        # Some checks need the file path (e.g., to read file after modification)
        if repro.check_fn == "check_range_format_bug":
            reproduced = check_range_format_bug(result, repro, file_path=file_path)
        else:
            reproduced = check_fn(result, repro)  # type: ignore[operator]

        details = f"exit={result.returncode}"
        if result.stdout.strip():
            details += f" stdout={result.stdout.strip()[:200]}"
        if result.stderr.strip():
            details += f" stderr={result.stderr.strip()[:200]}"
        if repro.use_format:
            content = file_path.read_text().strip()
            details += f" file={content[:100]}"

        return reproduced, details


def main() -> None:
    if not RUFF_BINARY.exists():
        print(f"ERROR: Ruff binary not found at {RUFF_BINARY}")
        print("Run 'ate ruff pin' and 'ate ruff build' first.")
        sys.exit(1)

    print(f"Verifying 8 bugs against {RUFF_BINARY}")
    print("=" * 70)

    passed = 0
    failed = 0
    for repro in REPROS:
        reproduced, details = verify_bug(repro)
        status = "REPRODUCED" if reproduced else "NOT REPRODUCED"
        icon = "+" if reproduced else "-"
        print(f"  [{icon}] #{repro.bug_id} {repro.title}")
        print(f"      {status}: {details}")
        if reproduced:
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"Reproduced: {passed}/8  |  Not reproduced: {failed}/8")

    if failed > 0:
        print("\nWARN: Some bugs did not reproduce. Check if they were fixed")
        print("before v0.14.14, or swap from backup list.")
        sys.exit(1)


if __name__ == "__main__":
    main()
