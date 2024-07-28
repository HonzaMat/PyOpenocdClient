# SPDX-License-Identifier: MIT

import pytest

from py_openocd_client import OcdCommandTimeoutError, PyOpenocdClient


def test_no_output(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("puts some_text")

        # The text is printed to stdout but the actual TCL command
        # does not produce any output.
        assert out == ""


def test_with_output(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return abcdef")
        assert out == "abcdef"


def test_whitespace_trimmed(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return {  abc 4567 }")
        # OpenOCD trims leading and trailing whitespace
        assert out == "abc 4567"


def test_nonexistent_cmd(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("nonexistent_cmd")
        assert out == 'invalid command name "nonexistent_cmd"'


def test_capture(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("capture { echo {abcdef} }")
        assert out == "abcdef\n"


def test_catch_success(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return [ catch { version } ]")
        assert int(out) == 0  # success code


def test_catch_error(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return [ catch { nonexistent_cmd } ]")
        assert int(out) != 0  # error code


def test_catch_output_and_success(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd(
            'set RETCODE [ catch { version } OUT ]; return "$RETCODE $OUT" '
        )

        parts = out.split(" ", maxsplit=1)
        retcode = int(parts[0])
        out = parts[1]

        assert retcode == 0  # success code
        assert "Open On-Chip Debugger" in out


def test_catch_output_and_error(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd(
            'set RETCODE [ catch { nonexistent_cmd } OUT; ]; return "$RETCODE $OUT" '
        )

        parts = out.split(" ", maxsplit=1)
        retcode = int(parts[0])
        out = parts[1]

        assert retcode != 0  # error code
        assert "invalid command" in out


def test_raw_cmd_timeout_ok(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("sleep 1000", timeout=2.0)
        assert out == ""


def test_raw_cmd_timeout_exceeded(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandTimeoutError) as e:
            ocd.raw_cmd("sleep 2000", timeout=1.0)

        assert e.value.full_cmd == "sleep 2000"
        assert e.value.timeout == 1.0
