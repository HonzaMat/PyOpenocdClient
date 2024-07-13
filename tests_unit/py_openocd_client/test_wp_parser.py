# SPDX-License-Identifier: MIT

import pytest

from py_openocd_client import WpType
from py_openocd_client.wp_parser import _WpParser


def test_parse_wp_entry():
    wp_entry = (
        "address: 0x00002000, len: 0x00000004, r/w/a: a, "
        "value: 0x00000000, mask: 0xffffffffffffffff"
    )

    wp_info = _WpParser.parse_wp_entry(wp_entry)
    assert wp_info.addr == 0x2000
    assert wp_info.size == 4
    assert wp_info.wp_type == WpType.ACCESS
    assert wp_info.value == 0x0
    assert wp_info.mask == 0xFFFFFFFFFFFFFFFF


def test_parse_wp_entry_2():
    wp_entry = (
        "address: 0x00001234, len: 0x00000008, r/w/a: 0, "
        "value: 0x0000abcd, mask: 0x0000ffff"
    )

    wp_info = _WpParser.parse_wp_entry(wp_entry)
    assert wp_info.addr == 0x1234
    assert wp_info.size == 8
    assert wp_info.wp_type == WpType.READ
    assert wp_info.value == 0xABCD
    assert wp_info.mask == 0xFFFF


def test_parse_wp_entry_error():
    with pytest.raises(ValueError) as e:
        _WpParser.parse_wp_entry("malformed wp entry")
    assert "Could not parse" in str(e)
