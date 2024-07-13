#!/usr/bin/python3

# SPDX-License-Identifier: MIT

import argparse
from pathlib import Path
import os
import subprocess
import sys
from typing import List


def get_script_dir() -> Path:
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", action="store_true",
                        help="Collect coverage from the unit test run")
    parser.add_argument("--force-pythonpath", action="store_true",
                        help=("Point PYTHONPATH to the source directory, so that the tests "
                              "can run even without having the package installed"))
    return parser.parse_args()


def run_subproc(cmd: List[str]) -> None:
    print("Running command: " + repr(cmd))
    subprocess.check_call(cmd, cwd=get_script_dir())


def run_pytest(enable_coverage: bool) -> None:
    pytest_args = ["-m", "pytest", "tests_unit/", "-vv"]
    if enable_coverage:
        cmd = [sys.executable, "-m", "coverage", "run"] + pytest_args
    else:
        cmd = [sys.executable] + pytest_args
    run_subproc(cmd)


def run_coverage_html_generation() -> None:
    cmd = [sys.executable, "-m", "coverage", "html"]
    run_subproc(cmd)


def run_coverage_xml_generation() -> None:
    cmd = [sys.executable, "-m", "coverage", "xml"]
    run_subproc(cmd)


def main() -> int:
    args = parse_args()

    if args.force_pythonpath:
        # Allow running the unit tests even without having the package installed
        os.environ["PYTHONPATH"] = str(get_script_dir() / "src")
    else:
        try:
            import py_openocd_client
        except ModuleNotFoundError:
            print("Error: Package py_openocd_client not found.")
            print("You can:")
            print("- install the package before running the tests, or")
            print("- start the script with --force-pythonpath to modify PYTHONPATH "
                  "and use the source code directly, without having it installed")
            return 1

    run_pytest(args.coverage)
    if args.coverage:
        run_coverage_html_generation()
        run_coverage_xml_generation()

    return 0


if __name__ == "__main__":
    sys.exit(main())



