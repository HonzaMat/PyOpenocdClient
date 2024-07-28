# SPDX-License-Identifier: MIT

import time

import pytest

from py_openocd_client import (
    OcdCommandFailedError,
    OcdCommandTimeoutError,
    PyOpenocdClient,
)


def test_basic(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("version")
        assert result.retcode == 0
        assert result.cmd == "version"
        assert "Open On-Chip Debugger" in result.out


def test_basic_2(openocd_process):

    with PyOpenocdClient() as ocd:

        if ocd.version_tuple() < (0, 12, 0):
            # OpenOCD below version 0.12.0 seem to ignore the -code ##
            # attribute of "return" command and always use value 2.
            pytest.xfail("Test won't work in OpenOCD older than 0.12.0")

        result = ocd.cmd("return -level 0 -code ok xyz")
        assert result.retcode == 0
        assert result.out == "xyz"


def test_echo(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("echo {some text}")
        assert result.retcode == 0
        assert result.out == ""  # because capture was not set


def test_echo_with_capture(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("echo {some text}", capture=True)
        assert result.retcode == 0
        assert result.out == "some text"


def test_failed_cmd(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("some_nonexistent_cmd some_arg")

        assert e.value.result.retcode != 0
        assert "invalid command" in e.value.result.out
        assert e.value.result.cmd == "some_nonexistent_cmd some_arg"


def test_failed_cmd_2(openocd_process):
    with PyOpenocdClient() as ocd:

        if ocd.version_tuple() < (0, 12, 0):
            # OpenOCD below version 0.12.0 seem to ignore the -code ##
            # attribute of "return" command and always use value 2.
            expected_retcode = 2
        else:
            expected_retcode = 77

        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("return -level 0 -code 77 {some text}")

        assert e.value.result.retcode == expected_retcode
        assert e.value.result.out == "some text"


def test_failed_cmd_negative_retcode(openocd_process):
    with PyOpenocdClient() as ocd:

        if ocd.version_tuple() < (0, 12, 0):
            # OpenOCD below version 0.12.0 seem to ignore the -code ##
            # attribute of "return" command and always use value 2.
            expected_retcode = 2
        else:
            expected_retcode = -200

        with pytest.raises(OcdCommandFailedError) as e:
            ocd.cmd("return -level 0 -code -200 {some text}")

        assert e.value.result.retcode == expected_retcode
        assert e.value.result.out == "some text"


def test_failed_cmd_dont_throw(openocd_process):
    with PyOpenocdClient() as ocd:
        result = ocd.cmd("some_bad_cmd", throw=False)

        assert result.retcode != 0
        assert "invalid command" in result.out


def test_set_and_read_variable(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.cmd("set MY_VARIALBLE 123456")
        result = ocd.cmd("echo $MY_VARIALBLE", capture=True)
        assert result.out == "123456"


def test_version(openocd_process):
    with PyOpenocdClient() as ocd:
        assert "Open On-Chip Debugger" in ocd.version()


def test_version_tuple(openocd_process):
    with PyOpenocdClient() as ocd:
        major, minor, patch = ocd.version_tuple()
        assert (major, minor, patch) >= (0, 10, 0)


def test_timeout_ok(openocd_process):
    with PyOpenocdClient() as ocd:
        ocd.cmd("sleep 2000", timeout=3.0)


def test_timeout_exceeded(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandTimeoutError) as e:
            ocd.cmd("sleep 2000", timeout=1.0)

        assert e.value.timeout == 1.0
        assert e.value.full_cmd == "sleep 2000"

        # Timeout causes disconnection
        assert not ocd.is_connected()

        # After re-connection, commands must again work
        ocd.reconnect()
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
        time.sleep(2.0)
        assert (
            openocd_process.poll() is not None
        ), "OpenOCD process did not terminate after shutdown command"
