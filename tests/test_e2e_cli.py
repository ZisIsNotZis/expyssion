"""End-to-end: .expy program files through the expy CLI."""
import subprocess
import sys
from pathlib import Path

from expyssion.api import run_file

PROGRAMS = Path(__file__).parent / "programs"


def test_litmus_febonacci_expy():
    assert run_file(PROGRAMS / "febonacci.expy") is None  # prints 55


def test_litmus_pipeline_expy():
    out = run_file(PROGRAMS / "pipeline.expy")
    assert out[:4] == [0, 9, 36, 81]
    assert len(out) == 34  # multiples of 3 below 100


def test_litmus_guard_expy(capsys):
    run_file(PROGRAMS / "guard.expy")
    assert capsys.readouterr().out == "0\n6\n"


def test_cli_subprocess():
    r = subprocess.run(
        [sys.executable, "-m", "expyssion.cli", "run", str(PROGRAMS / "febonacci.expy")],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "55"


def test_cli_error_is_loud(tmp_path):
    bad = tmp_path / "bad.expy"
    bad.write_text("gen= : yield 1\ngen ()\n")
    r = subprocess.run(
        [sys.executable, "-m", "expyssion.cli", "run", str(bad)],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 1
    assert "unhandled yield" in r.stderr
