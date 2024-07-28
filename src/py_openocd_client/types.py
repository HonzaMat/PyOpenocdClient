# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class OcdCommandResult:
    """
    Class representing result of an executed and finished TCL command.
    """

    retcode: int
    cmd: str
    raw_cmd: str
    out: str


class BpType(Enum):
    """
    Breakpoint type.
    """

    HW = "hw"
    SW = "sw"
    CONTEXT = "context"
    HYBRID = "hybrid"


class WpType(Enum):
    """
    Watchpoint type.
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
    size: int
    bp_type: BpType
    orig_instr: Optional[int]  # only relevant for SW breakpoints


@dataclass
class WpInfo:
    """
    Information about a single watchpoint.
    """

    addr: int
    size: int
    wp_type: WpType
    value: int
    mask: int
