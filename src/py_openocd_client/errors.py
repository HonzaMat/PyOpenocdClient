# SPDX-License-Identifier: MIT

from .types import OcdCommandResult


class OcdError(RuntimeError):
    """
    Base class for exceptions of PyOpenocdClient.
    """

    pass


class OcdCommandError(OcdError):
    """
    Exception denoting a TCL command that ended unsuccessfully.
    """

    def __init__(self, result: OcdCommandResult):
        assert result.retcode != 0
        msg = f"OpenOCD command failed: '{result.cmd}' (error code: {result.retcode})"
        self._result = result
        super().__init__(msg)

    @property
    def result(self) -> OcdCommandResult:
        return self._result


class OcdConnectionError(OcdError):
    pass


class OcdCommandTimeout(OcdError):
    pass


class OcdCommandInvalidResponse(OcdError):
    pass
