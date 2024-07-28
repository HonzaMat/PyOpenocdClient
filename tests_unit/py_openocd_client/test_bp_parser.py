# SPDX-License-Identifier: MIT

import pytest

from py_openocd_client import BpType
from py_openocd_client.bp_parser import _BpParser
from py_openocd_client.errors import _OcdParsingError


def test_parse_bp_entry_sw():
    """
    Test that SW breakpoint items from the breakpoint list
    can be parsed (both current and legacy format).
    """

    # current format
    bp_entry_current = (
        "Software breakpoint(IVA): addr=0x00001000, len=0x8, orig_instr=0xabcd1234"
    )
    # legacy format - used by older OpenOCD
    bp_entry_legacy = "IVA breakpoint: 0x00001000, 0x8, 0xabcd1234"

    bp_info = _BpParser.parse_bp_entry(bp_entry_current)
    assert bp_info.bp_type == BpType.SW
    assert bp_info.addr == 0x1000
    assert bp_info.size == 8
    assert bp_info.orig_instr == 0xABCD1234

    bp_info2 = _BpParser.parse_bp_entry(bp_entry_legacy)
    assert bp_info == bp_info2


def test_parse_bp_entry_hw():
    """
    Test that HW breakpoint items from the breakpoint list
    can be parsed (both current and legacy format).
    """

    bp_entry_current = "Hardware breakpoint(IVA): addr=0x00001010, len=0x4, num=0"
    bp_entry_legacy = "Breakpoint(IVA): 0x00001010, 0x4, 0"

    bp_info = _BpParser.parse_bp_entry(bp_entry_current)
    assert bp_info.bp_type == BpType.HW
    assert bp_info.addr == 0x1010
    assert bp_info.size == 4
    assert bp_info.orig_instr is None

    bp_info2 = _BpParser.parse_bp_entry(bp_entry_legacy)
    assert bp_info == bp_info2


def test_parse_bp_entry_context_unsupported():
    """
    Context breakpoints are unsupported. Check that proper exception
    is raised if encountered.
    """

    bp_entry_current = "Context breakpoint: asid=0x00000010, len=0x4, num=0"
    bp_entry_legacy = "Context breakpoint: 0x00000010, 0x4, 0"

    with pytest.raises(NotImplementedError):
        _BpParser.parse_bp_entry(bp_entry_current)

    with pytest.raises(NotImplementedError):
        _BpParser.parse_bp_entry(bp_entry_legacy)


def test_parse_bp_entry_hybrid_unsupported():
    """
    Hybrid breakpoints are unsupported. Check that proper exception
    is raised if encountered.
    """

    bp_entry_current = "Hybrid breakpoint(IVA): addr=0x00001020, len=0x4, num=0"
    bp_entry_legacy = "Hybrid breakpoint(IVA): 0x00001020, 0x4, 0"

    with pytest.raises(NotImplementedError):
        _BpParser.parse_bp_entry(bp_entry_current)

    with pytest.raises(NotImplementedError):
        _BpParser.parse_bp_entry(bp_entry_legacy)


def test_parse_bp_entry_error():
    """
    Test that unrecognized breakpoint items are reported via a proper exception.
    """

    malformed_entry = "Software bre__XYZ__k(IVA): addr=0x0, len=0x8, orig_instr=0x1"
    with pytest.raises(_OcdParsingError) as e:
        _BpParser.parse_bp_entry(malformed_entry)

    assert "Could not parse" in str(e)
