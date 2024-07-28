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
    def __init__(self, host: str = "127.0.0.1", port: int = 6666) -> None:
        self._host = host
        self._port = port
        self._client_base = _PyOpenocdBaseClient(host, port)

    def connect(self) -> None:
        self._client_base.connect()

    def disconnect(self) -> None:
        self._client_base.disconnect()

    def reconnect(self) -> None:
        self._client_base.reconnect()

    def is_connected(self) -> bool:
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

    def set_default_timeout(self, timeout: float) -> None:
        self._client_base.set_default_timeout(timeout)

    def raw_cmd(self, cmd: str, timeout: Optional[float] = None) -> str:
        return self._client_base.raw_cmd(cmd, timeout=timeout)

    def cmd(
        self,
        cmd: str,
        capture: bool = False,
        throw: bool = True,
        timeout: Optional[float] = None,
    ) -> OcdCommandResult:
        if capture:
            raw_cmd = "capture { " + cmd + " }"
        else:
            raw_cmd = cmd

        raw_cmd = "set CMD_RETCODE [ catch { " + raw_cmd + " } CMD_OUTPUT ] ; "
        raw_cmd += 'return "$CMD_RETCODE $CMD_OUTPUT" ; '

        raw_result = self.raw_cmd(raw_cmd, timeout=timeout)

        # Verify the raw output of the has the expected format. It can be:
        #
        # - Command return code (positive or negative decimal number) and that's it.
        #
        # - Or, command return code (positive or negative decimal number) followed by
        #   a space character and optionally the command's textual output.
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

    def halt(self) -> None:
        self.cmd("halt")

    def resume(self, new_pc: Optional[int] = None) -> None:
        cmd = "resume"
        if new_pc is not None:
            cmd += " " + hex(new_pc)
        self.cmd(cmd)

    def step(self, new_pc: Optional[int] = None) -> None:
        cmd = "step"
        if new_pc is not None:
            cmd += " " + hex(new_pc)
        self.cmd(cmd)

    def reset_halt(self) -> None:
        self.cmd("reset halt")

    def reset_init(self) -> None:
        self.cmd("reset init")

    def reset_run(self) -> None:
        self.cmd("reset run")

    def curstate(self) -> str:
        return self.cmd("[target current] curstate").out.strip()

    def is_halted(self) -> bool:
        return self.curstate() == "halted"

    def is_running(self) -> bool:
        return self.curstate() == "running"

    def get_reg(self, reg_name: str, force: bool = False) -> int:
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
        # FIXME: Change the type annotation of "bit_width" to "Literal[8, 16, 32, 64]"
        # once support of Python 3.7 is dropped.

        self._check_memory_access_params(addr, bit_width)
        self._check_memory_write_values(values, bit_width)

        cmd = f"write_memory {hex(addr)} {bit_width} {self._make_tcl_list(values)}"
        if phys:
            cmd += " phys"
        self.cmd(cmd, timeout=timeout).out.strip()

    def list_bp(self) -> List[BpInfo]:
        result = self.cmd("bp")
        bp_lines = result.out.strip().splitlines()
        try:
            return [_BpParser.parse_bp_entry(line) for line in bp_lines]
        except _OcdParsingError as e:
            msg = "Could not parse the output of 'bp' command"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out) from e

    def add_bp(self, addr: int, size: int, hw: bool = False) -> None:
        cmd = "bp " + hex(addr) + " " + str(size)
        if hw:
            cmd += " hw"
        self.cmd(cmd)

    def remove_bp(self, addr: int) -> None:
        self.cmd("rbp " + hex(addr))

    def remove_all_bp(self) -> None:
        self.cmd("rbp all")

    def list_wp(self) -> List[WpInfo]:
        result = self.cmd("wp")
        wp_lines = result.out.splitlines()
        try:
            return [_WpParser().parse_wp_entry(line) for line in wp_lines]
        except _OcdParsingError as e:
            msg = "Could not parse the output of 'wp' command"
            raise OcdInvalidResponseError(msg, result.raw_cmd, result.out) from e

    def add_wp(self, addr: int, size: int, wp_type: WpType = WpType.ACCESS) -> None:
        cmd = "wp " + hex(addr) + " " + str(size) + " " + str(wp_type.value)
        self.cmd(cmd)

    def remove_wp(self, addr: int) -> None:
        self.cmd("rwp " + hex(addr))

    def remove_all_wp(self) -> None:
        self.cmd("rwp all")

    def echo(self, msg: str) -> None:
        self.cmd("echo {" + msg + "}")

    def version(self) -> str:
        return self.cmd("version").out.strip()

    def version_tuple(self) -> Tuple[int, int, int]:
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
        out = self.cmd("target names").out.strip()
        return out.splitlines()

    def select_target(self, target_name: str) -> None:
        self.cmd("targets " + target_name)

    def set_poll(self, enable_polling: bool) -> None:
        self.cmd("poll " + ("on" if enable_polling else "off"))

    def exit(self) -> None:
        self.disconnect()

    def shutdown(self) -> None:
        # OpenOCD's shutdown command returns a non-zero error code (which is expected).
        # For that reason, throw=False is used.
        self.cmd("shutdown", throw=False)
        self.disconnect()
