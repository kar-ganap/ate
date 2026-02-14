"""Bug reproduction cases and check functions.

Extracted from scripts/verify_bugs.py to make reproduction logic importable
for Tier 1 scoring. The original script imports from this module.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BugReproCase:
    """A single bug reproduction case."""

    bug_id: int
    title: str
    code: str
    rules: list[str]
    check_fn: str
    extra_args: list[str] | None = None
    config: str | None = None
    use_fix: bool = False
    use_format: bool = False
    format_args: list[str] | None = None
    extra_files: dict[str, str] = field(default_factory=dict)
    filename: str = "repro.py"


REPRO_CASES: dict[int, BugReproCase] = {
    20945: BugReproCase(
        bug_id=20945,
        title="FAST001 false positive (None==None)",
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
    18654: BugReproCase(
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
    7847: BugReproCase(
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
    4384: BugReproCase(
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
    19301: BugReproCase(
        bug_id=19301,
        title="Parser indentation after backslashes",
        code="if True:\n    pass\n    \\\n        print(\"1\")\n",
        rules=[],
        check_fn="check_has_syntax_error",
    ),
    22221: BugReproCase(
        bug_id=22221,
        title="F401 fix infinite loop (__all__ duplicates)",
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
    22528: BugReproCase(
        bug_id=22528,
        title="Parser false syntax error (match-like)",
        code="""\
from re import match

match[0]: int
""",
        rules=[],
        check_fn="check_has_syntax_error",
    ),
    22494: BugReproCase(
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
}


# --- Check Functions ---


def check_has_diagnostic(
    result: subprocess.CompletedProcess[str], _case: BugReproCase
) -> bool:
    """Bug reproduces if ruff reports a diagnostic (false positive)."""
    return result.returncode != 0 and len(result.stdout.strip()) > 0


def check_outer_flagged(
    result: subprocess.CompletedProcess[str], _case: BugReproCase
) -> bool:
    """Bug reproduces if 'wrapper' (outer fn) is flagged for complexity."""
    return "wrapper" in result.stdout and "C901" in result.stdout


def check_has_syntax_error(
    result: subprocess.CompletedProcess[str], _case: BugReproCase
) -> bool:
    """Bug reproduces if ruff reports a syntax error for valid Python."""
    output = result.stdout + result.stderr
    return "SyntaxError" in output or "syntax" in output.lower()


def check_convergence_failure(
    result: subprocess.CompletedProcess[str], _case: BugReproCase
) -> bool:
    """Bug reproduces if --fix hits convergence limit (infinite loop)."""
    output = result.stdout + result.stderr
    return "converge" in output.lower() or "100 iterations" in output.lower()


def check_range_format_bug(
    result: subprocess.CompletedProcess[str],
    _case: BugReproCase,
    file_path: Path | None = None,
) -> bool:
    """Bug reproduces if range formatting doesn't split semicolons properly."""
    if file_path is None:
        return False
    content = file_path.read_text()
    return ";" in content


CHECK_FNS: dict[str, Callable[..., bool]] = {
    "check_has_diagnostic": check_has_diagnostic,
    "check_outer_flagged": check_outer_flagged,
    "check_has_syntax_error": check_has_syntax_error,
    "check_convergence_failure": check_convergence_failure,
    "check_range_format_bug": check_range_format_bug,
}


# --- Repro Execution ---


def setup_repro(case: BugReproCase, work_dir: Path) -> Path:
    """Write reproduction files to work_dir. Returns target file path."""
    target = work_dir / case.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(case.code)

    for rel_path, content in case.extra_files.items():
        extra = work_dir / rel_path
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text(content)

    if case.config:
        config_path = work_dir / "ruff.toml"
        config_path.write_text(case.config)

    return target


def _run_ruff_check(
    ruff_binary: Path,
    file_path: Path,
    rules: list[str],
    extra_args: list[str] | None = None,
    config_path: Path | None = None,
    use_fix: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ruff check on a file."""
    cmd = [str(ruff_binary), "check", str(file_path)]
    if rules:
        cmd.extend(["--select", ",".join(rules)])
    if config_path:
        cmd.extend(["--config", str(config_path)])
    if use_fix:
        cmd.append("--fix")
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _run_ruff_format(
    ruff_binary: Path,
    file_path: Path,
    format_args: list[str] | None = None,
    config_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ruff format on a file."""
    cmd = [str(ruff_binary), "format", str(file_path)]
    if config_path:
        cmd.extend(["--config", str(config_path)])
    if format_args:
        cmd.extend(format_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def run_repro(bug_id: int, ruff_dir: Path) -> tuple[bool, str]:
    """Run reproduction case. Returns (reproduced, details)."""
    case = REPRO_CASES[bug_id]
    ruff_binary = ruff_dir / "target" / "debug" / "ruff"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        file_path = setup_repro(case, tmpdir_path)

        config_path = None
        if case.config:
            config_path = tmpdir_path / "ruff.toml"

        try:
            if case.use_format:
                result = _run_ruff_format(
                    ruff_binary,
                    file_path,
                    format_args=case.format_args,
                    config_path=config_path,
                )
            else:
                result = _run_ruff_check(
                    ruff_binary,
                    file_path,
                    case.rules,
                    extra_args=case.extra_args,
                    config_path=config_path,
                    use_fix=case.use_fix,
                )
        except subprocess.TimeoutExpired:
            return True, "TIMEOUT (likely infinite loop — bug reproduces)"

        check_fn = CHECK_FNS[case.check_fn]

        if case.check_fn == "check_range_format_bug":
            reproduced = check_range_format_bug(result, case, file_path=file_path)
        else:
            reproduced = check_fn(result, case)

        details = f"exit={result.returncode}"
        if result.stdout.strip():
            details += f" stdout={result.stdout.strip()[:200]}"
        if result.stderr.strip():
            details += f" stderr={result.stderr.strip()[:200]}"
        if case.use_format:
            content = file_path.read_text().strip()
            details += f" file={content[:100]}"

        return reproduced, details


def is_fixed(bug_id: int, ruff_dir: Path) -> bool:
    """Returns True if bug no longer reproduces (for Tier 1 scoring)."""
    reproduced, _details = run_repro(bug_id, ruff_dir)
    return not reproduced
