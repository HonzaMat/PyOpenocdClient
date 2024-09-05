#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

import subprocess
import sys
from pathlib import Path
from typing import List


def get_script_dir() -> Path:
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def run_subproc(cmd: List[str], cwd: Path) -> None:
    print("Running command: " + repr(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def main() -> int:
    work_dir = get_script_dir() / "doc"
    run_subproc(
        [
            sys.executable,
            "-m",
            "sphinx",
            "--fail-on-warning",
            "--keep-going",
            ".",
            "_build/html",
        ],
        cwd=work_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
