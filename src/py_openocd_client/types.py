# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class OcdCommandResult:
    """
    This class represets result of an executed and completed TCL command.

    An instance of this class is returned by :meth:`PyOpenocdClient.cmd`.
    """

    retcode: int
    """
    Return code of the command.

    Zero value means successfully completed command. Non-zero value means
    failed command (an error during command execution).
    """

    cmd: str
    """
    The original command that the user requested to exeucte.
    """

    raw_cmd: str
    """
    The actual "raw" command that was sent by PyOpenocdClient to OpenOCD for execution.

    This is typically the user-entered command (`cmd`) wrapped in other TCL commands
    so that PyOpenocdClient is able to obtain both the output and the return code
    of the user-command.
    """

    out: str
    """
    Textual output of the command.
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
