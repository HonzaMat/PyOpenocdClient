# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from py_openocd_client import (
    OcdCommandError,
    OcdCommandInvalidResponse,
    PyOpenocdClient,
)

# TODO: Rename _PyOpenocdClientBase to _PyOpenocdBaseClient

# TODO: Rename to client_base_mock
@pytest.fixture()
def socket_base_inst_mock():
    return mock.Mock()


@pytest.fixture(autouse=True)
def socket_base_mock(socket_base_inst_mock):
    with mock.patch("py_openocd_client.client._PyOpenocdClientBase") as m:
        m.return_value = socket_base_inst_mock
        yield m


def test_constructor_default_addr(socket_base_mock):
    ocd = PyOpenocdClient()
    assert ocd._host == "127.0.0.1"
    assert ocd._port == 6666
    socket_base_mock.assert_called_with("127.0.0.1", 6666)


def test_constructor_custom_addr(socket_base_mock):
    ocd = PyOpenocdClient("192.168.1.20", 12345)
    assert ocd._host == "192.168.1.20"
    assert ocd._port == 12345
    socket_base_mock.assert_called_with("192.168.1.20", 12345)


def test_connect_disconnect(socket_base_inst_mock):
    ocd = PyOpenocdClient()

    ocd.connect()
    socket_base_inst_mock.connect.assert_called_once()
    socket_base_inst_mock.reset_mock()

    ocd.disconnect()
    socket_base_inst_mock.disconnect.assert_called_once()
    socket_base_inst_mock.reset_mock()

    ocd.reconnect()
    socket_base_inst_mock.reconnect.assert_called_once()
    socket_base_inst_mock.reset_mock()

    socket_base_inst_mock.is_connected.return_value = True
    assert ocd.is_connected()

    socket_base_inst_mock.is_connected.return_value = False
    assert not ocd.is_connected()


def test_context_manager(socket_base_mock, socket_base_inst_mock):
    with PyOpenocdClient("some_host", 1234) as ocd:
        socket_base_mock.assert_called_once_with("some_host", 1234)
        assert ocd._host == "some_host"
        assert ocd._port == 1234

        socket_base_inst_mock.connect.assert_called_once()
        socket_base_inst_mock.disconnect.assert_not_called()

    socket_base_inst_mock.disconnect.assert_called_once()


def test_set_default_timeout(socket_base_inst_mock):
    ocd = PyOpenocdClient()
    ocd.set_default_timeout(12.3)
    socket_base_inst_mock.set_default_timeout.assert_called_once_with(12.3)


def test_raw_cmd(socket_base_inst_mock):
    ocd = PyOpenocdClient()

    socket_base_inst_mock.raw_cmd.return_value = "command output"
    assert ocd.raw_cmd("some_cmd") == "command output"
    socket_base_inst_mock.raw_cmd.assert_called_once_with("some_cmd", timeout=None)
    socket_base_inst_mock.reset_mock()

    socket_base_inst_mock.raw_cmd.return_value = "some other output"
    assert ocd.raw_cmd("other_cmd", timeout=4.0) == "some other output"
    socket_base_inst_mock.raw_cmd.assert_called_once_with("other_cmd", timeout=4.0)


def test_cmd(socket_base_inst_mock):
    ocd = PyOpenocdClient()

    cmd = "some_cmd arg"
    expected_full_cmd = (
        "set CMD_RETCODE [ "
        "catch { some_cmd arg } "
        "CMD_OUTPUT ] ; "
        'return "$CMD_RETCODE $CMD_OUTPUT" ; '
    )
    raw_cmd_out = "0 some output\nanother line"

    socket_base_inst_mock.raw_cmd.return_value = raw_cmd_out
    result = ocd.cmd(cmd)

    assert result.retcode == 0
    assert result.cmd == cmd
    assert result.full_cmd == expected_full_cmd
    assert result.out == "some output\nanother line"

    socket_base_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )
    socket_base_inst_mock.reset_mock()

    # Try the same command but this time with explicit timeout
    result2 = ocd.cmd(cmd, timeout=7.5)
    assert result == result2
    socket_base_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=7.5
    )
    socket_base_inst_mock.reset_mock()


def test_cmd_capture_and_timeout(socket_base_inst_mock):
    ocd = PyOpenocdClient()

    cmd = "dummy_cmd"
    expected_full_cmd = (
        "set CMD_RETCODE [ "
        "catch { capture { dummy_cmd } } "
        "CMD_OUTPUT ] ; "
        'return "$CMD_RETCODE $CMD_OUTPUT" ; '
    )
    raw_cmd_out = "0 dummy output"

    socket_base_inst_mock.raw_cmd.return_value = raw_cmd_out
    # Try capture=True + explicit timeout
    result = ocd.cmd(cmd, capture=True, timeout=3.0)

    assert result.retcode == 0
    assert result.cmd == cmd
    assert result.full_cmd == expected_full_cmd
    assert result.out == "dummy output"

    socket_base_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=3.0
    )


def test_cmd_exception(socket_base_inst_mock):
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
    socket_base_inst_mock.raw_cmd.return_value = raw_cmd_out
    with pytest.raises(OcdCommandError) as exc_info:
        ocd.cmd(cmd)

    e = exc_info.value
    assert e.result.retcode == 138
    assert e.result.cmd == cmd
    assert e.result.full_cmd == expected_full_cmd
    assert e.result.out == "some output\nof the command"

    socket_base_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )
    socket_base_inst_mock.reset_mock()

    # Try executing the same command with exceptions suppressed
    res = ocd.cmd(cmd, throw=False)
    assert res.retcode == 138
    assert res.cmd == cmd
    assert res.full_cmd == expected_full_cmd
    assert res.out == "some output\nof the command"

    socket_base_inst_mock.raw_cmd.assert_called_once_with(
        expected_full_cmd, timeout=None
    )


def _check_cmd_empty_output(socket_base_inst_mock, out):
    ocd = PyOpenocdClient()

    socket_base_inst_mock.raw_cmd.return_value = out
    result = ocd.cmd("some_cmd")
    assert result.retcode == 0
    assert result.cmd == "some_cmd"
    assert result.out == ""


def test_cmd_empty_output(socket_base_inst_mock):
    # Just return code, no textual output.
    _check_cmd_empty_output(socket_base_inst_mock, "0 ")


def test_cmd_empty_output2(socket_base_inst_mock):
    # Just return code, no textual output.
    # No space after return code,
    _check_cmd_empty_output(socket_base_inst_mock, "0")


def test_cmd_negative_retcode(socket_base_inst_mock):
    socket_base_inst_mock.raw_cmd.return_value = "-123 some output"

    ocd = PyOpenocdClient()
    with pytest.raises(OcdCommandError) as e:
        ocd.cmd("some_cmd")

    assert e.value.result.retcode == -123
    assert e.value.result.out == "some output"





def test_cmd_invalid_responses(socket_base_inst_mock):
    ocd = PyOpenocdClient()

    socket_base_inst_mock.raw_cmd.return_value = ""
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    socket_base_inst_mock.raw_cmd.return_value = "a"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    socket_base_inst_mock.raw_cmd.return_value = "abc def"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")

    socket_base_inst_mock.raw_cmd.return_value = "56a some output"
    with pytest.raises(OcdCommandInvalidResponse):
        ocd.cmd("cmd")
