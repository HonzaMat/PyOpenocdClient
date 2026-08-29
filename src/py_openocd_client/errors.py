# SPDX-License-Identifier: MIT

import warnings

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
            except OcdCommandFailedError as e:
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
    - re-issue the command with a larger timeout.

    .. note::
        If this exception occurs, then reconnection is automatically performed:
        the current connection to OpenOCD is closed and a new one established.

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

    def __init__(self, msg: str, raw_cmd: str, raw_out: str):
        self._raw_cmd = raw_cmd
        self._raw_out = raw_out
        super().__init__(msg)

    @property
    def raw_cmd(self) -> str:
        """
        Raw command that produced the invalid response.
        """
        return self._raw_cmd

    @property
    def raw_out(self) -> str:
        """
        The actual raw command's output that was unexpected
        (that could not be understood or parsed).

        .. versionadded:: 0.2.0
           Added in version 0.2.0.
        """
        return self._raw_out

    @property
    def out(self) -> str:
        """
        Deprecated alias for `raw_out`, kept just for compatibility.

        .. deprecated:: 0.2.0
           Please use `raw_out` instead.
        """
        warnings.warn(
            "OcdInvalidResponseError.out is deprecated. "
            "Please use OcdInvalidResponseError.raw_out instead.",
            DeprecationWarning,
        )
        return self._raw_out


class OcdEmptyResponseError(OcdInvalidResponseError):
    """
    Exception which denotes that a TCL command produced an empty response.
    It is a sub-class of :py:class:`py_openocd_client.OcdInvalidResponseError`.

    Empty responses occur for commands ``exit`` and ``shutdown``, that is, commands
    that immediately terminate the TCL session. For other commands, empty responses are
    unexpected and would mean that OpenOCD mis-behaves.

    .. versionadded:: 0.2.0
       Added in version 0.2.0.
    """

    pass


class OcdConnectionError(OcdBaseException):
    """
    Exception that denotes connection errors, for instance:

    - connection to OpenOCD could be established
    - OpenOCD closed the connection
    - OpenOCD responded unexpectedly (protocol broken)

    .. note::
        If this exception is raised, the connection is automatically
        terminated.

        If the user wishes to continue issuing more commands, new
        connection needs to be established manually (by calling ``connect()`` or
        ``reconnect()``).

    """

    pass


class _OcdParsingError(OcdBaseException):
    """
    Internal exception that denotes a parsing error.

    .. warning::
        This exception is not part of the public API of PyOpenocdClient.
        It may change between releases.
    """

    pass
