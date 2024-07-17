#!/usr/bin/python3

# SPDX-License-Identifier: MIT

import argparse
import subprocess
import sys
from pathlib import Path


def get_script_dir() -> Path:
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run code quality checking tools")
    parser.add_argument(
        "-e",
        "--edit",
        action="store_true",
        help="Edit the files automatically (make changes and overwrite files)",
    )
    return parser.parse_args()


def run_tool(cmd: list[str]) -> None:
    print()
    print("Running tool: " + repr(cmd))
    subprocess.check_call(cmd)
    print("Tool finished OK.")


def run_tool_isort(make_edits: bool, targets: list[Path]) -> None:
    cmd = [sys.executable, "-m", "isort", "--profile", "black"]
    if not make_edits:
        cmd += ["--check-only", "--diff"]
    cmd += map(str, targets)
    run_tool(cmd)


def run_tool_black(make_edits: bool, targets: list[Path]) -> None:
    cmd = [sys.executable, "-m", "black", "-q"]
    if not make_edits:
        cmd += ["--check", "--diff"]
    cmd += map(str, targets)
    run_tool(cmd)


def run_tool_flake8(targets: list[Path]) -> None:
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--max-line-length",
        "88",
        "--extend-ignore",
        "E203",
    ]
    cmd += map(str, targets)
    run_tool(cmd)


def run_tool_mypy(targets: list[Path]) -> None:
    for t in targets:
        cmd = [sys.executable, "-m", "mypy", "--strict", str(t)]
        run_tool(cmd)


def main() -> int:
    args = parse_args()

    srcs = [
        get_script_dir() / "src" / "py_openocd_client",
    ]
    tests = [
        get_script_dir() / "tests_unit" / "py_openocd_client",
        get_script_dir() / "tests_integration" / "py_openocd_client",
    ]
    utils = [
        get_script_dir() / "run_code_quality_check.py",
        get_script_dir() / "run_tests.py",
    ]

    run_tool_isort(args.edit, srcs + tests + utils)
    run_tool_black(args.edit, srcs + tests + utils)
    run_tool_flake8(srcs + tests + utils)
    run_tool_mypy(srcs + utils)

    print()
    print("Code quality check successful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
