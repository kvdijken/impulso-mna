# Run all the example scripts to ensure they execute without errors.
# This is a smoke test to catch any issues in the examples or
# bugs in the package itself which are not caught by the unit tests.

import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES_DIR = Path("examples")

SCRIPTS = sorted(EXAMPLES_DIR.glob("*.py"))

@pytest.mark.parametrize("script", SCRIPTS)
def test_example_script(script):
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        env={
            "MPLBACKEND": "Agg",
        },
    )

    assert result.returncode == 0, (
        f"\nScript failed: {script}"
        f"\n\nSTDOUT:\n{result.stdout}"
        f"\n\nSTDERR:\n{result.stderr}"
    )
