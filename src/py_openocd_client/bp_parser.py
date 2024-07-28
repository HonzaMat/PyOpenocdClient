# SPDX-License-Identifier: MIT

import re
from typing import Optional

from .errors import _OcdParsingError
from .types import BpInfo, BpType


class _BpParser:
    """
    Helper class to parse items from the breakpoint list, that is
    lines produced by the "bp" command.

    The class serves as a helper for PyOpenocdClient class and is not intended
    for direct use.

    Note: Context and hybrid breakpoints are currently unsupported.
    """

    @staticmethod
    def parse_bp_entry(line: str) -> BpInfo:
        """
        Parse one item from OpenOCD's breakpoint list.

        Raise ValueError if the line cannot be parsed.
        """
        parsers = [
            _BpParser._parse_bp_entry_sw,
            _BpParser._parse_bp_entry_hw,
            _BpParser._parse_bp_entry_context,
            _BpParser._parse_bp_entry_hybrid,
        ]

        for parser in parsers:
            bp_info = parser(line)
            if bp_info is not None:
                # Successfully parsed item
                return bp_info

        raise _OcdParsingError(
            "Could not parse this entry from the 'bp' command output: " + line
        )

    @staticmethod
    def _parse_bp_entry_sw(line: str) -> Optional[BpInfo]:
        # New format:
        # Software breakpoint(IVA): addr=0x00001000, len=0x8, orig_instr=0x00

        # Old format (prior to https://review.openocd.org/c/openocd/+/7861):
        # IVA breakpoint: 0x00001000, 0x8, 0x00

        new_format = (
            r"^Software breakpoint\(IVA\): "
            r"addr=(0x[a-fA-F0-9]+), "
            r"len=(0x[a-fA-F0-9]+), "
            r"orig_instr=(0x[a-fA-F0-9]+)$"
        )
        old_format = (
            r"^IVA breakpoint: (0x[a-fA-F0-9]+), "
            r"(0x[a-fA-F0-9]+), "
            r"(0x[a-fA-F0-9]+)$"
        )

        # Try the "new" format
        match = re.match(new_format, line)
        if match is None:
            # Try the "old" format
            match = re.match(old_format, line)
        if match is None:
            # Not a software breakpoint entry.
            return None

        return BpInfo(
            bp_type=BpType.SW,
            addr=int(match[1], 16),
            size=int(match[2], 16),
            orig_instr=int(match[3], 16),
        )

    @staticmethod
    def _parse_bp_entry_hw(line: str) -> Optional[BpInfo]:
        # New format:
        # Hardware breakpoint(IVA): addr=0x00001010, len=0x4, num=0

        # Old format (prior to https://review.openocd.org/c/openocd/+/7861):
        # Breakpoint(IVA): 0x00001010, 0x4, 0

        new_format = (
            r"^Hardware breakpoint\(IVA\): "
            r"addr=(0x[a-fA-F0-9]+), "
            r"len=(0x[a-fA-F0-9]+), "
            r"num=\d+$"
        )
        old_format = r"^Breakpoint\(IVA\): (0x[a-fA-F0-9]+), (0x[a-fA-F0-9]+), \d+$"

        # Try the "new" format
        match = re.match(new_format, line)
        if match is None:
            # Try the "old" format
            match = re.match(old_format, line)
        if match is None:
            # Not a HW breakpoint entry.
            return None

        return BpInfo(
            bp_type=BpType.HW,
            addr=int(match[1], 16),
            size=int(match[2], 16),
            orig_instr=None,
        )

    @staticmethod
    def _parse_bp_entry_context(line: str) -> Optional[BpInfo]:
        # FIXME: Context breakpoints are currently unsupported.
        if "Context" in line:
            raise NotImplementedError(
                "'Context breakpoint was found but is "
                "unsupported by PyOpenocdClient at the moment."
            )

        # Not a context breakpoint.
        return None

    @staticmethod
    def _parse_bp_entry_hybrid(line: str) -> Optional[BpInfo]:
        # FIXME: Hybrid breakpoints are currently unsupported.
        if "Hybrid" in line:
            raise NotImplementedError(
                "Hybrid breakpoint was found but is "
                "unsupported by PyOpenocdClient at the moment."
            )

        # Not a hybrid breakpoint.
        return None
