# SPDX-FileCopyrightText: 2026 Jan Matyas <info@janmatyas.net>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class OcdCommandResult:
    """
    This class represents the result of an executed and completed Tcl command.

    An instance of this class is returned by :meth:`PyOpenocdClient.cmd`.

    Here, "original Tcl command" refers to the command provided by the caller
    to :meth:`PyOpenocdClient.cmd`, before PyOpenocdClient wraps or otherwise
    modifies that command..
    """

    retcode: int
    """
    Return code of the original Tcl command.

    A value of zero means successfully completed command. A non-zero value indicates
    that the command failed.
    """

    cmd: str
    """
    The original Tcl command -- as provided by the caller
    to :meth:`PyOpenocdClient.cmd`.
    """

    raw_cmd: str
    """
    The "raw" Tcl script that was actually sent by PyOpenocdClient to OpenOCD
    for execution.

    This is typically the original Tcl command wrapped in additional Tcl code,
    so that PyOpenocdClient is able to retrieve *both* the textual output and
    the return code of the original Tcl command.
    """

    out: str
    """
    Textual output of the original Tcl command.
    """


class BpType(Enum):
    """
    Breakpoint type (enum).
    """

    HW = "hw"
    SW = "sw"
    CONTEXT = "context"
    HYBRID = "hybrid"


class WpType(Enum):
    """
    Watchpoint type (enum).
    """

    READ = "r"
    WRITE = "w"
    ACCESS = "a"


@dataclass
class BpInfo:
    """
    Information about a single breakpoint.
    """

    addr: int
    """
    Address of the breakpoint.
    """

    size: int
    """
    Size of the breakpoint.
    """

    bp_type: BpType
    """
    Breakpoint type.
    """

    orig_instr: Optional[int]
    """
    Original instruction. Only relevant to SW breakpoints.
    """


@dataclass
class WpInfo:
    """
    Information about a single watchpoint.
    """

    addr: int
    """
    Address of the watchpoint.
    """

    size: int
    """
    Size of the watchpoint.
    """

    wp_type: WpType
    """
    Watchpoint type.
    """

    value: int
    """
    Data value to compare.
    """

    mask: int
    """
    Mask for data value comparison.

    Only the data bits whose corresponding mask bit is ``0`` are compared
    against the :py:attr:`value`.

    Watchpoint whose mask is "all ones" does not perform any data comparison.
    """
