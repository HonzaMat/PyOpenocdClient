# SPDX-License-Identifier: MIT

import subprocess
import time
from pathlib import Path
from openocd_version_info import OPENOCD_VERSION_NAMES

import pytest


def pytest_addoption(parser):
    parser.addoption("--openocd-path", action="store", required=True)
    parser.addoption("--openocd-version", action="store", required=True, choices=OPENOCD_VERSION_NAMES)


@pytest.fixture
def openocd_path(pytestconfig):
    return Path(pytestconfig.getoption("openocd_path")).resolve()


@pytest.fixture
def openocd_version(pytestconfig):
    version = pytestconfig.getoption("openocd_version")
    assert version in OPENOCD_VERSION_NAMES
    return version


@pytest.fixture
def has_buggy_whitespace_trim(openocd_version):
    """
    Detect if the OpenOCD version being tested has a known buggy whitespace handling.

    In OpenOCD prior to version 0.13.0, the "return" command performed extra
    whitespace trimming on the command output. This was fixed in commit "93f16eed4,
    https://review.openocd.org/c/openocd/+/9084.
    """
    return openocd_version in [
        "vanilla-0.10.0",
        "vanilla-0.11.0",
        "vanilla-0.12.0",
        "riscv-master-libjim-from-apt",
    ]


@pytest.fixture
def openocd_process(openocd_path):
    # Start OpenOCD without any target, just so that TCL command interface
    # becomes available.
    proc = subprocess.Popen([openocd_path, "-c", "noinit", "-c", "tcl_port 6666"])
    # Safety: Give OpenOCD time to start up, avoid races
    time.sleep(1.0)

    yield proc

    # Kill if still running
    if proc.poll() is None:
        proc.kill()
