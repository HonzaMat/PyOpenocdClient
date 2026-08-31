# SPDX-License-Identifier: MIT

import subprocess
import sys


def _run_openocd_cmd(args):
    safety_timeout = 10.0
    return subprocess.run(
        args, capture_output=True, encoding="utf8", check=False, timeout=safety_timeout
    )


def test_help():
    res = _run_openocd_cmd(["openocd_cmd", "--help"])
    assert res.returncode == 0
    assert "Command-line utility that sends a single Tcl command" in res.stdout


def test_cmd_success(openocd_process):
    res = _run_openocd_cmd(["openocd_cmd", "version"])
    assert res.returncode == 0
    assert "Open On-Chip Debugger" in res.stdout
    assert res.stderr == ""


def test_cmd_success_alternate_invocation(openocd_process):
    python = sys.executable
    res = _run_openocd_cmd([python, "-m", "py_openocd_client.cli", "version"])
    assert res.returncode == 0
    assert "Open On-Chip Debugger" in res.stdout
    assert res.stderr == ""


def test_cmd_success_explicit_args(openocd_process):
    res = _run_openocd_cmd(
        [
            "openocd_cmd",
            "--host",
            "localhost",
            "--port",
            "6666",
            "--timeout",
            "2.5",
            "version",
        ]
    )
    assert res.returncode == 0
    assert "Open On-Chip Debugger" in res.stdout
    assert res.stderr == ""


def test_cmd_nonexistent(openocd_process):
    res = _run_openocd_cmd(["openocd_cmd", "nonexistent_cmd"])
    assert res.returncode != 0
    assert "invalid command" in res.stdout
    assert "The command has failed" in res.stderr


def test_cmd_throw(openocd_process):
    res = _run_openocd_cmd(["openocd_cmd", "throw 77 {some error message}"])
    assert res.returncode != 0
    assert res.stdout == "some error message\n"
    assert res.stderr == "error: The command has failed (return code: 77).\n"


def test_cmd_timeout(openocd_process):
    res = _run_openocd_cmd(["openocd_cmd", "--timeout", "1.5", "sleep 3000"])
    assert res.returncode == 93
    assert res.stdout == ""
    assert res.stderr == (
        "error: Timeout: The command did not complete within 1.5 seconds.\n"
    )


def test_connect_error(openocd_process):
    res = _run_openocd_cmd(["openocd_cmd", "--port", "56789", "version"])
    assert res.returncode == 91
    assert res.stdout == ""
    assert res.stderr == (
        "error: Could not connect to OpenOCD at 127.0.0.1, port 56789\n"
    )
