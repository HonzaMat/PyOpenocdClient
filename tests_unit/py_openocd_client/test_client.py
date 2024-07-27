# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from py_openocd_client import (
    OcdCommandError,
    OcdCommandInvalidResponse,
    PyOpenocdClient,
)


@pytest.fixture()
def baseclient_inst_mock():
    """
    Mock of a _PyOpenocdBaseClient instance
    """
    return mock.Mock()


@pytest.fixture(autouse=True)
def baseclient_constr_mock(baseclient_inst_mock):
    """
    Mock of the constructor of _PyOpenocdBaseClient
    """
    with mock.patch("py_openocd_client.client._PyOpenocdBaseClient") as m:
        m.return_value = baseclient_inst_mock
        yield m


def test_constructor_default_addr(baseclient_constr_mock):
    ocd = PyOpenocdClient()
    assert ocd._host == "127.0.0.1"
    assert ocd._port == 6666
    baseclient_constr_mock.assert_called_with("127.0.0.1", 6666)


def test_constructor_custom_addr(baseclient_constr_mock):
    ocd = PyOpenocdClient("192.168.1.20", 12345)
    assert ocd._host == "192.168.1.20"
    assert ocd._port == 12345
    baseclient_constr_mock.assert_called_with("192.168.1.20", 12345)


def test_connect_disconnect(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    ocd.connect()
    baseclient_inst_mock.connect.assert_called_once()
    baseclient_inst_mock.reset_mock()

    ocd.disconnect()
    baseclient_inst_mock.disconnect.assert_called_once()
    baseclient_inst_mock.reset_mock()

    ocd.reconnect()
    baseclient_inst_mock.reconnect.assert_called_once()
    baseclient_inst_mock.reset_mock()

    baseclient_inst_mock.is_connected.return_value = True
    assert ocd.is_connected()

    baseclient_inst_mock.is_connected.return_value = False
    assert not ocd.is_connected()


def test_context_manager(baseclient_constr_mock, baseclient_inst_mock):
    with PyOpenocdClient("some_host", 1234) as ocd:
        baseclient_constr_mock.assert_called_once_with("some_host", 1234)
        assert ocd._host == "some_host"
        assert ocd._port == 1234

        baseclient_inst_mock.connect.assert_called_once()
        baseclient_inst_mock.disconnect.assert_not_called()

    baseclient_inst_mock.disconnect.assert_called_once()


def test_set_default_timeout(baseclient_inst_mock):
    ocd = PyOpenocdClient()
    ocd.set_default_timeout(12.3)
    baseclient_inst_mock.set_default_timeout.assert_called_once_with(12.3)


def test_raw_cmd(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    baseclient_inst_mock.raw_cmd.return_value = "command output"
    assert ocd.raw_cmd("some_cmd") == "command output"
    baseclient_inst_mock.raw_cmd.assert_called_once_with("some_cmd", timeout=None)
    baseclient_inst_mock.reset_mock()

    baseclient_inst_mock.raw_cmd.return_value = "some other output"
    assert ocd.raw_cmd("other_cmd", timeout=4.0) == "some other output"
    baseclient_inst_mock.raw_cmd.assert_called_once_with("other_cmd", timeout=4.0)


def test_cmd(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    cmd = "some_cmd arg"
    expected_full_cmd = (
        "set CMD_RETCODE [ "
        "catch { some_cmd arg } "
        "CMD_OUTPUT ] ; "
        'return "$CMD_RETCODE $CMD_OUTPUT" ; '
    )
    raw_cmd_out = "0 some output\nanother line"

    baseclient_inst_mock.raw_cmd.return_value = raw_cmd_out
    result = ocd.cmd(cmd)

    assert result.retcode == 0
    assert result.cmd == cmd
    assert result.full_cmd == expected_full_cmd
    assert result.out == "some output\nanother line"

    baseclient_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )
    baseclient_inst_mock.reset_mock()

    # Try the same command but this time with explicit timeout
    result2 = ocd.cmd(cmd, timeout=7.5)
    assert result == result2
    baseclient_inst_mock.raw_cmd.assert_called_once_with(expected_full_cmd, timeout=7.5)
    baseclient_inst_mock.reset_mock()


def test_cmd_capture_and_timeout(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    cmd = "dummy_cmd"
    expected_full_cmd = (
        "set CMD_RETCODE [ "
        "catch { capture { dummy_cmd } } "
        "CMD_OUTPUT ] ; "
        'return "$CMD_RETCODE $CMD_OUTPUT" ; '
    )
    raw_cmd_out = "0 dummy output"

    baseclient_inst_mock.raw_cmd.return_value = raw_cmd_out
    # Try capture=True + explicit timeout
    result = ocd.cmd(cmd, capture=True, timeout=3.0)

    assert result.retcode == 0
    assert result.cmd == cmd
    assert result.full_cmd == expected_full_cmd
    assert result.out == "dummy output"

    baseclient_inst_mock.raw_cmd.assert_called_once_with(expected_full_cmd, timeout=3.0)


def test_cmd_exception(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    cmd = "some_cmd_that_fails arg1 arg2"
    expected_full_cmd = (
        "set CMD_RETCODE [ "
        "catch { some_cmd_that_fails arg1 arg2 } "
        "CMD_OUTPUT ] ; "
        'return "$CMD_RETCODE $CMD_OUTPUT" ; '
    )
    raw_cmd_out = "138 some output\nof the command"  # non-zero exit code

    # Try executing the command and getting the exception
    baseclient_inst_mock.raw_cmd.return_value = raw_cmd_out
    with pytest.raises(OcdCommandError) as exc_info:
        ocd.cmd(cmd)

    e = exc_info.value
    assert e.result.retcode == 138
    assert e.result.cmd == cmd
    assert e.result.full_cmd == expected_full_cmd
    assert e.result.out == "some output\nof the command"

    baseclient_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )
    baseclient_inst_mock.reset_mock()

    # Try executing the same command, but with OcdCommandError exception suppressed
    res = ocd.cmd(cmd, throw=False)
    assert res.retcode == 138
    assert res.cmd == cmd
    assert res.full_cmd == expected_full_cmd
    assert res.out == "some output\nof the command"

    baseclient_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )


def _check_cmd_empty_output(baseclient_inst_mock, out):
    ocd = PyOpenocdClient()

    baseclient_inst_mock.raw_cmd.return_value = out
    result = ocd.cmd("some_cmd")
    assert result.retcode == 0
    assert result.cmd == "some_cmd"
    assert result.out == ""


def test_cmd_empty_output(baseclient_inst_mock):
    # Just return code, no textual output.
    _check_cmd_empty_output(baseclient_inst_mock, "0 ")


def test_cmd_empty_output2(baseclient_inst_mock):
    # Just return code, no textual output.
    # No space after return code.
    _check_cmd_empty_output(baseclient_inst_mock, "0")


def test_cmd_negative_retcode(baseclient_inst_mock):
    baseclient_inst_mock.raw_cmd.return_value = "-123 some output"

    ocd = PyOpenocdClient()
    with pytest.raises(OcdCommandError) as e:
        ocd.cmd("some_cmd")

    assert e.value.result.retcode == -123
    assert e.value.result.out == "some output"


def test_cmd_invalid_responses(baseclient_inst_mock):
    ocd = PyOpenocdClient()

    baseclient_inst_mock.raw_cmd.return_value = ""
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    baseclient_inst_mock.raw_cmd.return_value = "a"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    baseclient_inst_mock.raw_cmd.return_value = "abc def"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    baseclient_inst_mock.raw_cmd.return_value = "56a some output"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")
