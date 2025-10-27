# SPDX-License-Identifier: MIT

import socket
import subprocess
import time
from pathlib import Path

import pytest
from openocd_version_info import OPENOCD_VERSION_NAMES


def pytest_addoption(parser):
    parser.addoption("--openocd-path", action="store", required=True)
    parser.addoption(
        "--openocd-version",
        action="store",
        required=True,
        choices=OPENOCD_VERSION_NAMES,
    )


def _wait_until_port_open(port: int, timeout: float = 5.0):
    """Wait until OpenOCD opens given TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.1)

    time_start = time.time()
    while True:
        try:
            s.connect(("127.0.0.1", port))
        except socket.error as e:
            print(str(e))
            time_elapsed = time.time() - time_start
            if time_elapsed > timeout:
                raise RuntimeError(
                    "It looks like OpenOCD did not start up (did not open "
                    f"port {port}) within {timeout} sec"
                )
            time.sleep(0.1)
            continue
        finally:
            s.close()
            return


@pytest.fixture
def openocd_path(pytestconfig):
    return Path(pytestconfig.getoption("openocd_path")).resolve()


TCL_PORT_NUM = 6666


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
    proc = subprocess.Popen(
        [openocd_path, "-c", "noinit", "-c", f"tcl_port {TCL_PORT_NUM}"]
    )

    try:
        # Start OpenOCD without any target, just so that TCL command interface
        # becomes available.
        _wait_until_port_open(TCL_PORT_NUM)

        yield proc

    finally:

        # Kill if still running
        if proc.poll() is None:
            proc.kill()

        # Safety
        proc.wait(timeout=1.0)
        assert proc.poll() is not None
        time.sleep(0.2)  # just in case
