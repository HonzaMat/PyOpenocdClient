# SPDX-License-Identifier: MIT

import re

from .errors import _OcdParsingError
from .types import WpInfo, WpType


class _WpParser:
    """
    Internal helper class to parse items from the watchpoint list;
    that is, lines produced by the OpenOCD's "wp" command.

    .. warning::
        This class is not intended for direct use.
        Its API is not guaranteed to remain stable between releases.
    """

    @staticmethod
    def parse_wp_entry(line: str) -> WpInfo:
        """
        Parse one item from the OpenOCD's watchpoint list.
        """
        new_format = (
            r"^address: (0x[a-fA-F0-9]+), "
            r"len: (0x[a-fA-F0-9]+), "
            r"r/w/a: ([rwa012]), "
            r"value: (0x[a-fA-F0-9]+), "
            r"mask: (0x[a-fA-F0-9]+)"
        )

        match = re.match(new_format, line)
        if match is None:
            raise _OcdParsingError(
                "Could not parse this entry from the 'wp' command output: " + line
            )

        addr = int(match[1], 16)
        size = int(match[2], 16)
        # Older OpenOCD (prior to https://review.openocd.org/c/openocd/+/7909)
        # printed watchpoint type as 0, 1, 2 instead of r, w, a.
        wp_type = {
            "r": WpType.READ,
            "0": WpType.READ,
            "w": WpType.WRITE,
            "1": WpType.WRITE,
            "a": WpType.ACCESS,
            "2": WpType.ACCESS,
        }[match[3]]
        value = int(match[4], 16)
        mask = int(match[5], 16)

        return WpInfo(addr=addr, size=size, wp_type=wp_type, value=value, mask=mask)
