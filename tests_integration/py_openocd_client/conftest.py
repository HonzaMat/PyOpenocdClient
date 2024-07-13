# SPDX-License-Identifier: MIT

from pathlib import Path
import pytest
import subprocess
import time


def pytest_addoption(parser):
    parser.addoption("--openocd-path", action="store", required=True)


@pytest.fixture
def openocd_path(pytestconfig):
    return Path(pytestconfig.getoption("openocd_path")).resolve()


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