# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple, Type

from .baseclient import _PyOpenocdBaseClient
from .bp_parser import _BpParser
from .errors import OcdCommandFailedError, OcdInvalidResponseError, _OcdParsingError
from .types import BpInfo, OcdCommandResult, WpInfo, WpType
from .wp_parser import _WpParser


class PyOpenocdClient:
    """
    PyOpenocdClient is the main class which forms the interface
    of the ``py_openocd_client`` package. One instance of this class
    represents one TCL connection to a running OpenOCD process.

    This class provides:

    - :meth:`cmd` method to send any TCL command to OpenOCD and obtain
      the command result,
    - other convenience methods to issue some of the most common OpenOCD commands
      (:meth:`halt`, :meth:`resume`, :meth:`read_memory`, :meth:`get_reg`, etc.).

    Basic usage:

    .. code-block:: python

        from py_openocd_client import PyOpenocdClient

        ocd = PyOpenocdClient(host="localhost", port=6666)
        ocd.connect()

        # Now use the "ocd" instance to interact with OpenOCD:
        ocd.reset_halt()
        ocd.cmd("load_image path/to/your/program.elf")
        ocd.resume()
        # ...

        # Disconnect when done
        ocd.disconnect()

    Usage through context manager:

    .. code-block:: python

        from py_openocd_client import PyOpenocdClient

        # The context manager automatically establishes the connection.
        # No need to call ocd.connect().
        with PyOpenocdClient(host="localhost", port=6666) as ocd:

            # Now use the "ocd" instance to interact with OpenOCD:
            ocd.reset_halt()
            ocd.cmd("load_image path/to/your/program.elf")
            ocd.resume()
            # ...

            # The instance gets automatically disconnected at the end
            # of the "with" block. No need to call ocd.disconnect().

    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6666) -> None:
        self._host = host
        self._port = port
        self._client_base = _PyOpenocdBaseClient(host, port)

    def connect(self) -> None:
        """
        Establish connection to the OpenOCD instance running on *host* and *port*
        specificed in the class constructor.

        Raises :py:exc:`OcdConnectionError`:

        - if the connection fails,
        - if called on an already connected instance.
        """
        self._client_base.connect()

    def disconnect(self) -> None:
        """
        Terminate the connection to the OpenOCD instance, if connected.

        .. note::
           Calling :py:meth:`disconnect` on a non-connected instance is safe --
           it performs no operation and also does not raise any error.
        """
        self._client_base.disconnect()

    def reconnect(self) -> None:
        """
        Terminate the current connection, if any, and establish a new one.

        This is equivalent to calling :py:meth:`disconnect` and then :py:meth:`connect`.
        """
        self._client_base.reconnect()

    def is_connected(self) -> bool:
        """
        Determine if the instance is connected.
        """
        return self._client_base.is_connected()

    def __enter__(self) -> PyOpenocdClient:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Type[Any]],
    ) -> None:
        # FIXME:
        # Parameter "exc_tb" should probably be annotated as Optional[TracebackType],
        # but then mypy complains this way:
        # Module "typing" does not explicitly export attribute "TracebackType".

        self.disconnect()

    def cmd(
        self,
        cmd: str,
        capture: bool = False,
        throw: bool = True,
        timeout: Optional[float] = None,
    ) -> OcdCommandResult:
        """
        Send a TCL command to OpenOCD, wait for its completion and return the
        command result. The result of the command is represented by
        :py:class:`OcdCommandResult`.

        ``cmd`` is the TCL command to execute, or possibly multiple TCL commands --
        a short TCL script.

        ``capture`` determines whether to also obtain log entries produced by the command
        and return it as part of the command output. (Default: False)

        ``throw`` determines whether to raise :py:class:`OcdCommandFailedError` if
        the command fails. (Default: True)

        ``timeout`` can be used to override the default timeout. If it is not specified,
        the default timeout will apply -- see :py:meth:`set_default_timeout`.

        If the command fails, :py:class:`OcdCommandFailedError` is raised, unless
        suppresed by ``throw=False``.

        If the command timeout is exceeded while waiting for OpenOCD to provide
        the command result, :py:class:`OcdCommandTimeout` is raised and the connection
        is re-established (reconnected).

        If a connection error occurs during the command execution,
        :py:class:`OcdConnectionError` is raised and the connection is terminated.

        In the unlikely event OpenOCD responds unexpectedly (provides its response in
        an unexpected format), :py:class:`OcdCommandInvalidResponse` is raised.

        .. note::
           Other convenience methods of this class (:meth:`halt`, :meth:`resume`, etc.)
           use internally the :py:meth:`cmd` method, and therefore can also raise
           the above errors.

        Basic usage:

        .. code-block:: python

            with PyOpenocdClient("localhost", 6666) as ocd:

                # The simplest usage: Just execute a command and don't care
                # about its output. Should the command fail or not finish within
                # the timeout, an error will be raised.
                ocd.cmd("halt")

                # Second use case: Execute a command and obtain its textual output:
                result = ocd.cmd("version")
                print(f"Output of 'version' command was: {result.out}")

        Command errors can be handled this way:

        .. code-block:: python

            with PyOpenocdClient("localhost", 6666) as ocd:

                try:
                    ocd.cmd("load_image path/to/your/program.elf", timeout=10.0)
                except OcdCommandTimeoutError as e:
                    print(f"Image loading timed out - exceeded {e.timeout} seconds")
                except OcdCommandFailedError as e:
                    print(
                        "Image loading failed. "
                        f"Return code: {e.result.retcode}. "
                        f"OpenOCD's output: {e.result.out}"
                    )
                else:
                    print("Image loading successful.")

        .. note::
           The :py:meth:`cmd` method wraps the user-provided command with additional
           TCL commands (like ``catch`` and ``return``), and the resulting complex
           command is then sent to OpenOCD. This is needed so that both the return
           code and the textual output of the command can be obtained.

        """
        if capture:
            raw_cmd = "capture { " + cmd + " }"
        else:
            raw_cmd = cmd

        raw_cmd = "set CMD_RETCODE [ catch { " + raw_cmd + " } CMD_OUTPUT ] ; "
        raw_cmd += 'return "$CMD_RETCODE $CMD_OUTPUT" ; '

        raw_result = self.raw_cmd(raw_cmd, timeout=timeout)

        # Verify the raw output from OpenOCD the has the expected format. It can be:
        #
        # - Command return code (positive or negative decimal number) and that's it.
        #
        # - Or, command return code (positive or negative decimal number) followed by
        #   a space character and optionally followed by the command's textual output.
        if re.match(r"^-?\d+($| )", raw_result) is None:
            msg = (
                "Received unexpected response from OpenOCD. "
                "It looks like OpenOCD misbehaves. "
            )
            raise OcdInvalidResponseError(msg, raw_cmd, raw_result)

        raw_result_parts = raw_result.split(" ", maxsplit=1)
        assert len(raw_result_parts) in [1, 2]
        retcode = int(raw_result_parts[0], 10)
        out = raw_result_parts[1] if len(raw_result_parts) == 2 else ""

        result = OcdCommandResult(cmd=cmd, raw_cmd=raw_cmd, retcode=retcode, out=out)

        if throw and result.retcode != 0:
            raise OcdCommandFailedError(result)

        return result

    def set_default_timeout(self, timeout: float) -> None:
        """
        Set the default timeout for all commands.

        Note that some methods of this class allow to explicitly override
        the default timeout on per-command basis.
        """
        self._client_base.set_default_timeout(timeout)

    def halt(self) -> None:
        """
        Halt the currently selected target by sending the ``halt`` command.
        """
        self.cmd("halt")

    def resume(self, new_pc: Optional[int] = None) -> None:
        """
        Resume the currently selected target by sending the ``resume`` command.

        Optionally, a differet resume address can be set by the ``new_pc`` argument.
        """
        cmd = "resume"
        if new_pc is not None:
            cmd += " " + hex(new_pc)
        self.cmd(cmd)

    def step(self, new_pc: Optional[int] = None) -> None:
        """
        Perform single-step on the currently selected target by sending
        the ``step`` command.

        Optionally, a differet resume address can be set by the ``new_pc`` argument.
        """
        cmd = "step"
        if new_pc is not None:
            cmd += " " + hex(new_pc)
        self.cmd(cmd)

    def reset_halt(self) -> None:
        """
        Reset and halt all targets by sending the command ``reset halt``.
        """
        self.cmd("reset halt")

    def reset_init(self) -> None:
        """
        Reset and halt all targets by sending the command ``reset init``.
        """
        self.cmd("reset init")

    def reset_run(self) -> None:
        """
        Reset and resume all targets by sending the command ``reset run``.
        """
        self.cmd("reset run")

    def curstate(self) -> str:
        """
        Determinte the state of the currently selected target via the `currstate`
        command. Return the state as a string.
        """
        return self.cmd("[target current] curstate").out.strip()

    def is_halted(self) -> bool:
        """
        Determine if the currently selected target is halted.
        """
        return self.curstate() == "halted"

    def is_running(self) -> bool:
        """
        Determine if the currently selected target is running.
        """
        return self.curstate() == "running"

    def get_reg(self, reg_name: str, force: bool = False) -> int:
        """
        Read the value of a target's register. This is a convenience wrapper
        over the OpenOCD's `get_reg <https://openocd.org/doc-release/html/
        General-Commands.html#index-get_005freg>`_
        command.

        ``reg_name`` is the name of the register to read.

        If ``force`` is set to true, the value of the register is read directly
        from the target, as opposed to reading it from OpenOCD's internal cache.
        """
        force_arg = "-force " if force else ""
        cmd = f"dict get [ get_reg {force_arg}{reg_name} ] {reg_name}"

        result = self.cmd(cmd)
        reg_value = result.out.strip()

        try:
            # Expecting a single hexadecimal number on the output
            return int(reg_value, 16)
        except ValueError as e:
            msg = "Obtained invalid number from get_reg command"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out) from e

    def set_reg(self, reg_name: str, reg_value: int, force: bool = False) -> None:
        """
        Write a new value to a target's register. This is a convenience wraper
        over the OpenOCD's `set_reg <https://openocd.org/doc-release/html/
        General-Commands.html#index-set_005freg>`_
        command.

        ``reg_name`` is the name of the register to which the ``reg_value``
        shall be written.

        If ``force`` is set to true, the new value is written to the register
        immediately (as opposed to keeping it in the OpenOCD's internal cache).
        """
        force_arg = "-force " if force else ""
        cmd = f"set_reg {force_arg}{{ {reg_name} {hex(reg_value)} }}"
        self.cmd(cmd)

    @staticmethod
    def _check_memory_access_params(addr: int, bit_width: int) -> None:
        if addr < 0:
            raise ValueError("Address must be non-negative")
        memory_access_widths = [8, 16, 32, 64]
        if bit_width not in memory_access_widths:
            raise ValueError(
                "Memory access width must be one of: " + repr(memory_access_widths)
            )

    def read_memory(
        self,
        addr: int,
        bit_width: int,
        count: int = 1,
        phys: bool = False,
        timeout: Optional[float] = None,
    ) -> List[int]:
        """
        Read data from memory and return them as a list of integers.
        This is a convenience wrapper over the OpenOCD's ``read_memory`` command.

        ``addr`` is the memory address to read from -- the address of the first
        read data item.

        ``bit_width`` is the size of the data transfer (in bits). Allowed
        values are 8, 16, 32 and 64.

        ``count`` is the number of data items to read. Default is 1.
        If ``count`` is higher than 1, the next values are read
        from the subsequent memory addresses (address incremented by
        ``bit_width / 8``).

        ``phys`` is a boolean flag that makes OpenOCD use physical addressing
        (as opposed to the default virtual addressing). This argument is only
        meaningful for targets that actually use virtual memory.

        ``timeout`` can be optionally used to override the default timeout.
        """

        # FIXME: Change the type annotation of "bit_width" to "Literal[8, 16, 32, 64]"
        # once support of Python 3.7 is dropped.

        self._check_memory_access_params(addr, bit_width)
        if count < 1:
            raise ValueError("Count must be 1 or higher")

        cmd = f"read_memory {hex(addr)} {bit_width} {count}"
        if phys:
            cmd += " phys"
        result = self.cmd(cmd, timeout=timeout)
        out = result.out.strip()

        values_str = out.split(" ")

        # Safety validation of the command output
        if len(values_str) != count:
            msg = (
                "OpenOCD's read_memory command provided different number of values "
                f"than requested (expected {count} but obtained {len(values_str)})."
            )
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out)

        # Safety validation, cont'd
        hex_regex = r"^0x[0-9a-fA-F]+$"
        if any(re.match(hex_regex, v) is None for v in values_str):
            msg = "Found an item that is not a valid hexadecimal number"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out)

        # str -> int
        values = [int(v, 16) for v in values_str]
        return values

    @staticmethod
    def _check_memory_write_values(values: list[int], bit_width: int) -> None:
        if len(values) < 1:
            raise ValueError("At least one value to write must be provided")
        if any(v < 0 for v in values):
            raise ValueError("All values to write must be non-negative integers")
        if any(v.bit_length() > bit_width for v in values):
            raise ValueError(f"Found a value that exceeds {bit_width} bits")

    @staticmethod
    def _make_tcl_list(values: List[int]) -> str:
        return "{" + " ".join(map(hex, values)) + "}"

    def write_memory(
        self,
        addr: int,
        bit_width: int,
        values: List[int],
        phys: bool = False,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Write data to memory. This is a convenience wrapper over the OpenOCD's
        ``write_memory`` command.

        ``addr`` is the memory address to write the data to -- the address of the first
        written data item.

        ``bit_width`` is the size of the data transfer (in bits). Allowed
        values are 8, 16, 32 and 64.

        ``values`` is a list of integers -- list of the values to write. The first
        item is written to the address ``addr`` and the next values are written
        to the next memory words (whose addresses increment by ``bit_width / 8``).

        ``phys`` is a boolean flag that makes OpenOCD use physical addressing
        (as opposed to the default virtual addressing). This argument is only
        meaningful for targets that actually use virtual memory.

        ``timeout`` can optionally be used to override the default timeout.
        """

        # FIXME: Change the type annotation of "bit_width" to "Literal[8, 16, 32, 64]"
        # once support of Python 3.7 is dropped.

        self._check_memory_access_params(addr, bit_width)
        self._check_memory_write_values(values, bit_width)

        cmd = f"write_memory {hex(addr)} {bit_width} {self._make_tcl_list(values)}"
        if phys:
            cmd += " phys"
        self.cmd(cmd, timeout=timeout).out.strip()

    def list_bp(self) -> List[BpInfo]:
        """
        Obtain a list of the currently set breakpoints. Each breakpoint
        is represented by an instance of :py:class:`py_openocd_client.BpInfo`.

        This is a convenience wrapper over the OpenOCD's ``bp`` command.

        .. warning::
           Only HW and SW breakpoints are supported by :py:meth:`list_bp`
           at the moment. Context and hybrid breakpoints are not supported.

           You can still set and use these less common types of breakpoints
           manually (by :py:meth:`cmd`). However, :py:meth:`list_bp` will not
           be able to recognize them.
        """
        result = self.cmd("bp")
        bp_lines = result.out.strip().splitlines()
        try:
            return [_BpParser.parse_bp_entry(line) for line in bp_lines]
        except _OcdParsingError as e:
            msg = "Could not parse the output of 'bp' command"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out) from e

    def add_bp(self, addr: int, size: int, hw: bool = False) -> None:
        """
        Add one breakpoint at address ``addr`` of the given ``size``.

        If ``hw`` is True, hardware breakpoint will be used instead of software
        (default: False).

        This is a convenience wrapper over the OpenOCD's command
        ``bp <addr> <size> [hw]``.
        """
        cmd = "bp " + hex(addr) + " " + str(size)
        if hw:
            cmd += " hw"
        self.cmd(cmd)

    def remove_bp(self, addr: int) -> None:
        """
        Remove breakpoint located at given address ``addr``.

        This is a convenience wrapper over the OpenOCD's command ``rbp <addr>``.
        """
        self.cmd("rbp " + hex(addr))

    def remove_all_bp(self) -> None:
        """
        Remove all breakpoints.

        This is a convenience wrapper over the OpenOCD's command ``rbp all``.
        """
        self.cmd("rbp all")

    def list_wp(self) -> List[WpInfo]:
        """
        Obtain a list of the currently set watchpoints. Each watchpoint
        is represented by an instance of :py:class:`py_openocd_client.WpInfo`.

        This is a convenience wrapper over the OpenOCD's ``wp`` command.
        """
        result = self.cmd("wp")
        wp_lines = result.out.splitlines()
        try:
            return [_WpParser().parse_wp_entry(line) for line in wp_lines]
        except _OcdParsingError as e:
            msg = "Could not parse the output of 'wp' command"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out) from e

    def add_wp(self, addr: int, size: int, wp_type: WpType = WpType.ACCESS) -> None:
        """
        Add a single watchpoint to address ``addr`` of the given ``size``.

        Type of the watchpoint can be set by ``wp_type`` and the default is
        ``WpType.ACCESS``.

        This is a convenience wrapper over the OpenOCD's command
        ``wp <addr> <size> <r|w|a>``.
        """
        cmd = "wp " + hex(addr) + " " + str(size) + " " + str(wp_type.value)
        self.cmd(cmd)

    def remove_wp(self, addr: int) -> None:
        """
        Remove watchpoint located at given address ``addr``.

        This is a convenience wrapper over the OpenOCD's command ``rwp <addr>``.
        """
        self.cmd("rwp " + hex(addr))

    def remove_all_wp(self) -> None:
        """
        Remove all breakpoints.

        This is a convenience wrapper over the OpenOCD's command ``rwp all``.
        """
        self.cmd("rwp all")

    def echo(self, msg: str) -> None:
        """
        Print a text message on the OpenOCD's output.

        This is useful if the user wishses to print extra text to the OpenOCD log,
        for example to aid with subsequent log analysis.
        """
        self.cmd("echo {" + msg + "}")

    def version(self) -> str:
        """
        Return the OpenOCD version string, produced by the ``version`` command.
        """
        return self.cmd("version").out.strip()

    def version_tuple(self) -> Tuple[int, int, int]:
        """
        Return the OpenOCD version as a tuple containing three items -- major,
        minor and patch version.

        This is useful for OpenOCD version checks:

        .. code-block:: python

            if ocd.version_tuple() >= (0, 12, 0):
                # Some code that relies on OpenOCD version at least 0.12.0
                # ...
            else:
                raise RuntimeError("Sorry, OpenOCD 0.12.0 or newer is required.")

        """
        result = self.cmd("version")
        version_str = result.out.strip()
        version_regex = r"Open On\-Chip Debugger (\d+)\.(\d+)\.(\d+)"

        match = re.search(version_regex, version_str)
        if match is None:
            msg = "Unable to parse the version string received from OpenOCD"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out)

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        return major, minor, patch

    def target_names(self) -> List[str]:
        """
        Obtain a list of all target names.

        OpenOCD's command ``target names`` is used.

        This method is useful when there is more than one target
        in the debug session.
        """
        out = self.cmd("target names").out.strip()
        return out.splitlines()

    def select_target(self, target_name: str) -> None:
        """
        Select a specific target, identified by its ``target_name``.

        OpenOCD's command ``targets <target_name>`` is used.

        This method is useful when there is more than one target
        in the debug session.
        """
        self.cmd("targets " + target_name)

    def set_poll(self, enable_polling: bool) -> None:
        """
        Enable or disable periodic OpenOCD's polling of the target state.

        OpenOCD's commands ``poll on`` or ``poll off`` are used.
        """
        self.cmd("poll " + ("on" if enable_polling else "off"))

    def exit(self) -> None:
        """
        Alias for :py:meth:`disconnect`.
        """
        self.disconnect()

    def shutdown(self) -> None:
        """
        Shut down the OpenOCD process by sending the ``shutdown`` command to it.
        Then terminate the connection.
        """
        # OpenOCD's shutdown command returns a non-zero error code (which is expected).
        # For that reason, throw=False is used.
        self.cmd("shutdown", throw=False)
        self.disconnect()

    def raw_cmd(self, raw_cmd: str, timeout: Optional[float] = None) -> str:
        """
        Low-level method that sends a TCL command to OpenOCD in its "raw" form --
        exactly as the user has entered it, without wrapping it into any additional
        TCL commands.

        After the command completes, its textual output is returned as a simple string.
        Return code of the command is **not** obtained.

        .. warning::
           The :py:meth:`raw_cmd` method does not have the ability
           to recognize whether the TCL command succeeded or failed. That's because
           the return code of the command cannot be obtained.

           For that reason, the method :py:meth:`cmd` should always be preferred
           over :py:meth:`raw_cmd`.

        ``raw_cmd`` is the raw TCL command to execute (or possibly multiple TCL
        commands -- a short TCL script).

        ``timeout`` can be used to override the timeout for this command. If not
        specified, the default timeout will apply -- see :py:meth:`set_default_timeout`.

        If the command timeout is exceeded while waiting for OpenOCD to provide
        the command result, :py:class:`OcdCommandTimeoutError` is raised and
        the connection is re-established.

        If connection error occurs during the command execution,
        :py:class:`OcdConnectionError` is raised and the connection is terminated.
        """
        return self._client_base.raw_cmd(raw_cmd, timeout=timeout)
