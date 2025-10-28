# SPDX-License-Identifier: MIT

import time

import pytest

from py_openocd_client import (
    OcdCommandFailedError,
    OcdCommandTimeoutError,
    PyOpenocdClient,
)


def test_expr(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("expr {1 + 2 + 3}")
        assert result.retcode == 0
        assert result.out == "6"


def test_echo(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("echo {some text}")
        assert result.retcode == 0
        assert result.out == ""  # because capture was not set


def test_echo_with_capture(openocd_process, has_buggy_whitespace_trim):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("echo {some text}", capture=True)
        assert result.retcode == 0

        # "echo" appends \n at the end
        if has_buggy_whitespace_trim:
            assert result.out == "some text"
            pytest.xfail("known OpenOCD whitespace bug")
        else:
            assert result.out == "some text\n"


def test_failed_cmd(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("some_nonexistent_cmd some_arg")

        assert e.value.result.retcode != 0
        assert "invalid command" in e.value.result.out
        assert e.value.result.cmd == "some_nonexistent_cmd some_arg"


def test_failed_cmd_2(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandFailedError) as e:
            # Note:
            # Command `throw <err_code> <message>` is used here as it works reliably
            # across multiple jimtcl versions.
            #
            # The command `return -level 0 -code <err_code> <message>` is not used
            # because older versions of jimtcl seem to have problems with `-code`:
            # they would always return 2 and ignore the <err_code>.
            ocd.cmd("throw 77 {some error message}")

        assert e.value.result.retcode == 77
        assert e.value.result.out == "some error message"


def test_failed_cmd_negative_retcode(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("throw -200 {some error text}")

        assert e.value.result.retcode == -200
        assert e.value.result.out == "some error text"


def test_failed_cmd_dont_throw(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("some_bad_cmd", throw=False)

        assert result.retcode != 0
        assert "invalid command" in result.out


def test_assign_variable_and_read_by_echo(openocd_process, has_buggy_whitespace_trim):
    with PyOpenocdClient() as ocd:
        ocd.cmd("set MY_VARIALBLE 123456")
        result = ocd.cmd("echo $MY_VARIALBLE", capture=True)

        if has_buggy_whitespace_trim:
            assert result.out == "123456"
            pytest.xfail("known OpenOCD whitespace bug")
        else:
            assert result.out == "123456\n"


def test_assign_variable_and_read_by_set(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.cmd("set MY_VARIALBLE 123456")
        # Tcl "set" without just one parameter displays the variable value.
        result = ocd.cmd("set MY_VARIALBLE")
        assert result.out == "123456"


def test_read_nonexistent_variable(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("set NONEXISTENT_VAR")
        assert e.value.result.retcode != 0
        assert "no such variable" in e.value.result.out


def test_version_manual(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("version")
        assert result.retcode == 0
        assert result.cmd == "version"
        assert "Open On-Chip Debugger" in result.out


def test_version(openocd_process):
    with PyOpenocdClient() as ocd:
        assert "Open On-Chip Debugger" in ocd.version()


def test_version_tuple(openocd_process):
    with PyOpenocdClient() as ocd:
        major, minor, patch = ocd.version_tuple()
        assert (major, minor, patch) >= (0, 10, 0)
        # Older OpenOCD versions than 0.10.0 are not tested.


def test_timeout_ok(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.cmd("sleep 1000", timeout=2.0)


def test_timeout_exceeded(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandTimeoutError) as e:
            ocd.cmd("sleep 2000", timeout=1.0)

        expected_raw_cmd = (
            "set CMD_RETCODE [ catch { sleep 2000 } CMD_OUTPUT ] ; "
            'return "$CMD_RETCODE $CMD_OUTPUT" ; '
        )
        assert e.value.raw_cmd == expected_raw_cmd
        assert e.value.timeout == 1.0

        # Timeout causes re-connection, we must remain connected.
        assert ocd.is_connected()

        # Commands must still work
        assert "Open On-Chip Debugger" in ocd.cmd("version").out


def test_exit(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.exit()
        assert not ocd.is_connected()


def test_shutdown(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.shutdown()
        assert not ocd.is_connected()

        # Give OpenOCD time to exit - avoid races
        time.sleep(1.0)
        assert (
            openocd_process.poll() is not None
        ), "OpenOCD process did not terminate after shutdown command"
