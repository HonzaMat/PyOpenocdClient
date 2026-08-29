# SPDX-License-Identifier: MIT

import pytest

from py_openocd_client import (
    OcdCommandFailedError,
    OcdCommandResult,
    OcdInvalidResponseError,
)


def test_ocd_command_error_to_string():
    cmd_result = OcdCommandResult(
        retcode=8, cmd="my_cmd", raw_cmd="my_raw_cmd", out="abc\ndef\n"
    )
    cmd_error = OcdCommandFailedError(cmd_result)

    assert str(cmd_error) == "OpenOCD command failed: 'my_cmd' (error code: 8)"


def test_invalid_response_deprecated_property_out():
    exc = OcdInvalidResponseError("Exception message", "raw_cmd", "Raw output")

    # "out" is deprecated in favor of "raw_out"
    with pytest.warns(DeprecationWarning):
        out = exc.out
    raw_out = exc.raw_out
    assert raw_out == out
