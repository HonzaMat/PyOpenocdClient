# SPDX-License-Identifier: MIT

from py_openocd_client import OcdCommandFailedError, OcdCommandResult


def test_ocd_command_error_to_string():
    cmd_result = OcdCommandResult(
        retcode=8, cmd="my_cmd", full_cmd="my_full_cmd", out="abc\ndef\n"
    )
    cmd_error = OcdCommandFailedError(cmd_result)

    assert str(cmd_error) == "OpenOCD command failed: 'my_cmd' (error code: 8)"
