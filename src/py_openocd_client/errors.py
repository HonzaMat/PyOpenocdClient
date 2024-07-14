# SPDX-License-Identifier: MIT

from .types import OcdCommandResult


class OcdBaseException(Exception):
    """
    Base exception class for all exceptions of PyOpenocdClient.
    """

    pass


class OcdCommandFailedError(OcdBaseException):
    """
    Exception which denotes that a TCL command failed;
    that is, the command ended with a non-zero return code.
    """

    def __init__(self, result: OcdCommandResult):
        assert result.retcode != 0
        msg = f"OpenOCD command failed: '{result.cmd}' (error code: {result.retcode})"
        self._result = result
        super().__init__(msg)

    @property
    def result(self) -> OcdCommandResult:
        """
        Result of the command -- an instance of
        :py:class:`py_openocd_client.OcdCommandResult`. It allows to access
        the error code and the command output.

        Example of use:

        .. code-block:: python

            try:
                res = ocd.cmd("some command")
                print(f"Command succeeded. Output: {res.out}")
            except OcdCommandError as e:
                print(f"Command failed with error code {e.result.retcode}. "
                      f"Output: {e.result.out}")

        """
        return self._result


class OcdCommandTimeoutError(OcdBaseException):
    """
    Exception that is raised whenever a TCL command does not complete
    within the configured timeout.

    If this exception occurs, it is advisable to:

    - investigate why the command execution takes long time, and/or
    - re-connect and re-issue the command with a larger timeout.

    .. note::
        If this exception is raised, then the connection is automatically
        terminated.

        If the user wishes to continue issuing more commands, new
        connection needs to be established (by calling ``connect()`` or
        ``reconnect()``).

    """

    def __init__(self, msg: str, raw_cmd: str, timeout: float):
        self._raw_cmd = raw_cmd
        self._timeout = timeout
        super().__init__(msg)

    @property
    def raw_cmd(self) -> str:
        """
        Raw command which did not complete within the timeout.
        """
        return self._raw_cmd

    @property
    def timeout(self) -> float:
        """
        Timeout value that got exceeded.
        """
        return self._timeout


class OcdInvalidResponseError(OcdBaseException):
    """
    Exception which means that a TCL command produced invalid (unexpected) output.
    That is, PyOpenocdClient could not parse and/or interpret that command output.
    """

    def __init__(self, msg: str, raw_cmd: str, out: str):
        self._raw_cmd = raw_cmd
        self._out = out
        super().__init__(msg)

    @property
    def raw_cmd(self) -> str:
        """
        Raw command that produced the invalid response.
        """
        return self._raw_cmd

    @property
    def out(self) -> str:
        """
        The actual invalid response of the command.
        """
        return self._out


class OcdConnectionError(OcdBaseException):
    """
    Exception that denotes connection errors, for instance:

    - connection to OpenOCD could be established
    - OpenOCD closed the connection
    - OpenOCD responded unexpectedly (protocol broken)

    .. note::
        If this exception is raised, then the connection is automatically
        terminated.

        If the user wishes to continue issuing more commands, new
        connection needs to be established (by calling ``connect()`` or
        ``reconnect()``).

    """

    pass


class _OcdParsingError(OcdBaseException):
    """
    Internal exception that denotes a parsing error.

    Not part of the public API of PyOpenocdClient. May change between releases.
    """

    pass
