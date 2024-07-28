# SPDX-License-Identifier: MIT

from .types import OcdCommandResult


class OcdBaseException(Exception):
    """
    Base class for exceptions of PyOpenocdClient.
    """

    pass


class OcdCommandFailedError(OcdBaseException):
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


class OcdCommandTimeoutError(OcdBaseException):
    def __init__(self, msg: str, full_cmd: str, timeout: float):
        self._full_cmd = full_cmd
        self._timeout = timeout
        super().__init__(msg)

    @property
    def full_cmd(self) -> str:
        return self._full_cmd

    @property
    def timeout(self) -> float:
        return self._timeout


class OcdInvalidResponseError(OcdBaseException):
    """
    Exception which means that a TCL command produced unexpected output. That is,
    PyOpenocdClient could not understand the output form OpenOCD and parse it.
    """

    def __init__(self, msg: str, full_cmd: str, out: str):
        self._full_cmd = full_cmd
        self._out = out
        super().__init__(msg)

    @property
    def full_cmd(self) -> str:
        return self._full_cmd

    @property
    def out(self) -> str:
        return self._out


class OcdConnectionError(OcdBaseException):
    pass


class _OcdParsingError(OcdBaseException):
    """
    Internal exception that denotes parsing error.

    Not part of the public API. May change between versions.
    """

    pass
