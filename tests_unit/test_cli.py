# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import py_openocd_client.cli as cli
from py_openocd_client import (
    OcdCommandResult,
    OcdCommandTimeoutError,
    OcdConnectionError,
    OcdInvalidResponseError,
)

_EXIT_CODE_CONNECTION_ERROR = 91
_EXIT_CODE_INVALID_RESPONSE = 92
_EXIT_CODE_COMMAND_TIMEOUT = 93


def _mock_pyopenocdclient(monkeypatch, command_result):
    # Mock of the connected instance of PyOpenocdClient
    ocd_mock = MagicMock()
    ocd_mock.cmd.side_effect = [command_result]

    # Context manager mock
    class_mock = MagicMock()
    class_mock.return_value.__enter__.return_value = ocd_mock

    monkeypatch.setattr(cli, "PyOpenocdClient", class_mock)

    return class_mock, ocd_mock


def _execute_one_cli_unit_test(
    monkeypatch,
    capsys,
    argv,
    command_result,
    expected_host,
    expected_port,
    expected_timeout,
    expected_command,
    expected_exit_code,
    expected_stdout,
    expected_stderr,
):

    monkeypatch.setattr("sys.argv", argv)
    class_mock, ocd_mock = _mock_pyopenocdclient(monkeypatch, command_result)

    assert cli.main() == expected_exit_code

    class_mock.assert_called_once_with(expected_host, expected_port)
    ocd_mock.set_default_timeout.assert_called_once_with(expected_timeout)
    ocd_mock.cmd.assert_called_once_with(expected_command, throw=False)

    captured = capsys.readouterr()
    assert captured.out == expected_stdout
    assert captured.err == expected_stderr


def test_command_success(monkeypatch, capsys):
    _execute_one_cli_unit_test(
        monkeypatch,
        capsys,
        ["openocd_cmd", "some_command arg"],
        OcdCommandResult(0, "some_command arg", "...", "Command output\nAnother line"),
        expected_host="127.0.0.1",
        expected_port=6666,
        expected_timeout=10.0,
        expected_command="some_command arg",
        expected_exit_code=0,
        expected_stdout="Command output\nAnother line\n",
        expected_stderr="",
    )


def test_command_success_non_default_args(monkeypatch, capsys):
    _execute_one_cli_unit_test(
        monkeypatch,
        capsys,
        [
            "openocd_cmd",
            "--host",
            "some_hostname",
            "--port",
            "12345",
            "--timeout",
            "2.0",
            "my_command",
        ],
        OcdCommandResult(0, "my_command", "...", "Dummy command output"),
        expected_host="some_hostname",
        expected_port=12345,
        expected_timeout=2.0,
        expected_command="my_command",
        expected_exit_code=0,
        expected_stdout="Dummy command output\n",
        expected_stderr="",
    )


def test_command_failure(monkeypatch, capsys):
    _execute_one_cli_unit_test(
        monkeypatch,
        capsys,
        ["openocd_cmd", "command_which_fails"],
        OcdCommandResult(4, "command_which_fails", "...", "Command failed blah blah"),
        expected_host="127.0.0.1",
        expected_port=6666,
        expected_timeout=10.0,
        expected_command="command_which_fails",
        expected_exit_code=4,
        expected_stdout="Command failed blah blah\n",
        expected_stderr="error: The command has failed (return code: 4).\n",
    )


def test_command_invalid_response(monkeypatch, capsys):
    _execute_one_cli_unit_test(
        monkeypatch,
        capsys,
        ["openocd_cmd", "some_command"],
        OcdInvalidResponseError("Received bogus data.", "...", "raw_out"),
        expected_host="127.0.0.1",
        expected_port=6666,
        expected_timeout=10.0,
        expected_command="some_command",
        expected_exit_code=_EXIT_CODE_INVALID_RESPONSE,
        expected_stdout="",
        expected_stderr="error: OpenOCD responded unexpectedly: Received bogus data.\n",
    )


def test_command_timeout(monkeypatch, capsys):
    _execute_one_cli_unit_test(
        monkeypatch,
        capsys,
        ["openocd_cmd", "long_cmd"],
        OcdCommandTimeoutError("Command timed out", "long_cmd", 10.0),
        expected_host="127.0.0.1",
        expected_port=6666,
        expected_timeout=10.0,
        expected_command="long_cmd",
        expected_exit_code=_EXIT_CODE_COMMAND_TIMEOUT,
        expected_stdout="",
        expected_stderr=(
            "error: Timeout: The command did not complete within 10.0 seconds.\n"
        ),
    )


def test_connection_error(monkeypatch, capsys):

    mock_connect = MagicMock()
    mock_connect.side_effect = OcdConnectionError("Failed to connect.")

    monkeypatch.setattr(cli.PyOpenocdClient, "connect", mock_connect)
    monkeypatch.setattr("sys.argv", ["openocd_cmd", "some_command"])

    assert cli.main() == _EXIT_CODE_CONNECTION_ERROR

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: Failed to connect.\n"
