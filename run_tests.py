#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import List


def get_script_dir() -> Path:
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Collect coverage from the unit test run",
    )
    parser.add_argument(
        "--force-pythonpath",
        action="store_true",
        help=(
            "Point PYTHONPATH to the source directory, so that the tests "
            "can run even without having the package installed"
        ),
    )
    parser.add_argument(
        "--openocd-path", help="Path to OpenOCD executable", default=None
    )
    parser.add_argument(
        "--openocd-version", help="OpenOCD version being tested", default=None
    )
    parser.add_argument(
        "test_type", choices=["unit", "integration"], help="Type of the tests"
    )
    return parser.parse_args()


def run_subproc(cmd: List[str]) -> None:
    print("Running command: " + repr(cmd))
    subprocess.check_call(cmd, cwd=get_script_dir())


def run_unittests(enable_coverage: bool) -> None:
    pytest_args = ["-m", "pytest", "tests_unit/", "-vv"]
    if enable_coverage:
        cmd = [sys.executable, "-m", "coverage", "run"] + pytest_args
    else:
        cmd = [sys.executable] + pytest_args
    run_subproc(cmd)


def run_integration_tests(
    openocd_path: Path, openocd_version: str, enable_coverage: bool
) -> None:
    pytest_args = [
        "-m",
        "pytest",
        "tests_integration/",
        "-vv",
        "--openocd-path",
        str(openocd_path),
        "--openocd-version",
        str(openocd_version),
    ]
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
        if importlib.util.find_spec("py_openocd_client") is None:
            print("Error: Package py_openocd_client not found.")
            print("You can:")
            print("- install the package before running the tests, or")
            print(
                "- start the script with --force-pythonpath to modify PYTHONPATH "
                "and use the source code directly, without having it installed"
            )
            return 1

    if args.test_type == "unit":
        if args.openocd_path:
            raise RuntimeError("--openocd-path is irrelevant for unittests")
        if args.openocd_version:
            raise RuntimeError("--openocd-version is irrelevant for unittests")
        run_unittests(args.coverage)

    elif args.test_type == "integration":
        if not args.openocd_path:
            raise RuntimeError("--openocd-path is required for integration tests")
        if not args.openocd_version:
            raise RuntimeError("--openocd-version is required for integration tests")
        openocd_path = Path(args.openocd_path).resolve()
        run_integration_tests(openocd_path, args.openocd_version, args.coverage)

    else:
        assert False

    if args.coverage:
        run_coverage_html_generation()
        run_coverage_xml_generation()

    return 0


if __name__ == "__main__":
    sys.exit(main())
