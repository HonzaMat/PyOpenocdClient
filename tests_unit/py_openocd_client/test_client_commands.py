# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from py_openocd_client import (
    BpInfo,
    BpType,
    OcdCommandResult,
    PyOpenocdClient,
    WpInfo,
    WpType,
)


@pytest.fixture()
def ocd() -> PyOpenocdClient:
    ocd = PyOpenocdClient()
    ocd.cmd = mock.Mock()  # patch the cmd() method
    return ocd


def _mock_command_result(out) -> OcdCommandResult:
    return OcdCommandResult(
        retcode="0", cmd="don't care", full_cmd="don't care", out=out
    )


def test_halt(ocd):
    ocd.halt()
    ocd.cmd.assert_called_once_with("halt")


def test_resume(ocd):
    ocd.resume()
    ocd.cmd.assert_called_once_with("resume")
    ocd.cmd.reset_mock()

    ocd.resume(new_pc=0x00002000)
    ocd.cmd.assert_called_once_with("resume 0x2000")


def test_step(ocd):
    ocd.step()
    ocd.cmd.assert_called_once_with("step")
    ocd.cmd.reset_mock()

    ocd.step(new_pc=4096)
    ocd.cmd.assert_called_once_with("step 0x1000")


def test_reset_halt(ocd):
    ocd.reset_halt()
    ocd.cmd.assert_called_once_with("reset halt")


def test_reset_init(ocd):
    ocd.reset_init()
    ocd.cmd.assert_called_once_with("reset init")


def test_reset_run(ocd):
    ocd.reset_run()
    ocd.cmd.assert_called_once_with("reset run")


def test_curstate(ocd):
    ocd.cmd.return_value = _mock_command_result("halted")
    assert ocd.curstate() == "halted"
    ocd.cmd.assert_called_once_with("[target current] curstate")


def test_is_halted_is_running(ocd):
    ocd.curstate = mock.Mock()

    ocd.curstate.return_value = "halted"
    assert ocd.is_halted()
    assert not ocd.is_running()

    ocd.curstate.return_value = "running"
    assert not ocd.is_halted()
    assert ocd.is_running()

    ocd.curstate.return_value = "unknown"
    assert not ocd.is_halted()
    assert not ocd.is_running()


def test_get_reg(ocd):
    ocd.cmd.return_value = _mock_command_result("0x1234")
    assert ocd.get_reg("pc") == 0x1234
    ocd.cmd.assert_called_once_with("dict get [ get_reg pc ] pc")
    ocd.cmd.reset_mock()

    ocd.cmd.return_value = _mock_command_result("0xaaaa")
    assert ocd.get_reg("sp", force=True) == 0xAAAA
    ocd.cmd.assert_called_once_with("dict get [ get_reg -force sp ] sp")


def test_set_reg(ocd):
    ocd.set_reg("pc", 0x4321)
    ocd.cmd.assert_called_once_with("set_reg { pc 0x4321 }")
    ocd.cmd.reset_mock()

    ocd.set_reg("ra", 0x11223344, force=True)
    ocd.cmd.assert_called_once_with("set_reg -force { ra 0x11223344 }")


def test_read_memory_8(ocd):
    ocd.cmd.return_value = _mock_command_result("0xab")
    res = ocd.read_memory(0x2000, 8)
    assert res == [0xAB]
    ocd.cmd.assert_called_once_with("read_memory 0x2000 8 1", timeout=None)
    ocd.cmd.reset_mock()


def test_read_memory_16_and_count(ocd):
    ocd.cmd.return_value = _mock_command_result(
        "0x1111 0x2222 0x3333 0x4444 0x5555 0x6666 0x7777 0x8888"
    )
    res = ocd.read_memory(0x3000, 16, count=8)
    assert res == [0x1111, 0x2222, 0x3333, 0x4444, 0x5555, 0x6666, 0x7777, 0x8888]
    ocd.cmd.assert_called_once_with("read_memory 0x3000 16 8", timeout=None)
    ocd.cmd.reset_mock()


def test_read_memory_32_and_phys(ocd):
    ocd.cmd.return_value = _mock_command_result("0x12345678")
    res = ocd.read_memory(0x4000, 32, phys=True)
    assert res == [0x12345678]
    ocd.cmd.assert_called_once_with("read_memory 0x4000 32 1 phys", timeout=None)
    ocd.cmd.reset_mock()


def test_read_memory_64_and_timeout(ocd):
    ocd.cmd.return_value = _mock_command_result(
        "0x1122334455667788 " "0xaaaaaaaaaaaaaaaa " "0xbbbbbbbbbbbbbbbb"
    )
    res = ocd.read_memory(0x5000, 64, count=3, timeout=11.5)
    assert res == [0x1122334455667788, 0xAAAAAAAAAAAAAAAA, 0xBBBBBBBBBBBBBBBB]
    ocd.cmd.assert_called_once_with("read_memory 0x5000 64 3", timeout=11.5)
    ocd.cmd.reset_mock()


def test_write_memory_8(ocd):
    ocd.write_memory(0x4000, 8, [0x12])
    ocd.cmd.assert_called_once_with("write_memory 0x4000 8 {0x12}", timeout=None)


def test_write_memory_16_and_multiple(ocd):
    ocd.write_memory(0x5000, 16, [0x1234, 0x5678, 0xABCD])
    ocd.cmd.assert_called_once_with(
        "write_memory 0x5000 16 {0x1234 0x5678 0xabcd}", timeout=None
    )


def test_write_memory_32_and_phys(ocd):
    ocd.write_memory(0x6000, 32, [0x11223344, 0xFFFFFFFF], phys=True)
    ocd.cmd.assert_called_once_with(
        "write_memory 0x6000 32 {0x11223344 0xffffffff} phys", timeout=None
    )


def test_write_memory_64_and_timeout(ocd):
    ocd.write_memory(0x7000, 64, [0x1122334455667788], timeout=4.56)
    ocd.cmd.assert_called_once_with(
        "write_memory 0x7000 64 {0x1122334455667788}", timeout=4.56
    )


def test_read_memory_argument_errors(ocd):
    # Address can't be negative
    with pytest.raises(ValueError):
        ocd.read_memory(-4096, 8)

    # Bit width must be one of: 8, 16, 32, 64
    with pytest.raises(ValueError):
        ocd.read_memory(0x1000, 12)

    # Count must be greater than zero
    with pytest.raises(ValueError):
        ocd.read_memory(0x1000, 8, count=0)
    with pytest.raises(ValueError):
        ocd.read_memory(0x1000, 8, count=-4)


def test_write_memory_argument_errors(ocd):
    # Address can't be negative
    with pytest.raises(ValueError):
        ocd.write_memory(-4096, 8, [0xABCD, 0x1234])

    # Bit width must be one of: 8, 16, 32, 64
    with pytest.raises(ValueError):
        ocd.write_memory(4096, 10, [0xABCD, 0x1234])

    # Items to write must be non-empty
    with pytest.raises(ValueError):
        ocd.write_memory(0x1000, 8, [])

    # Items to write must be non-negative
    with pytest.raises(ValueError):
        ocd.write_memory(0x1000, 8, [-10])

    # Bit width of the items to write must not be exceeded
    with pytest.raises(ValueError):
        ocd.write_memory(0x1000, 8, [0x100])
    with pytest.raises(ValueError):
        ocd.write_memory(0x1000, 16, [0x12, 0x12345])


def test_read_memory_response_errors(ocd):
    # Pretend that only 3 values were returned instead of requested 8
    ocd.cmd.return_value = _mock_command_result("0x1111 0x2222 0x3333")
    with pytest.raises(ValueError) as e:
        ocd.read_memory(0x1234, 16, count=8)
    assert "different number of values than requested" in str(e)

    # Pretend that we received an invalid number
    ocd.cmd.return_value = _mock_command_result("0x1111 0xKLM")
    with pytest.raises(ValueError) as e:
        ocd.read_memory(0x5678, 16, count=2)
    assert "not a valid hexadecimal number" in str(e)


def test_list_bp_empty(ocd):
    ocd.cmd.return_value = _mock_command_result("")
    assert ocd.list_bp() == []
    ocd.cmd.assert_called_once_with("bp")


def test_list_bp_not_empty(ocd):
    bp_command_output = (
        "Hardware breakpoint(IVA): addr=0x10110000, len=0x4, num=0\n"
        "Software breakpoint(IVA): addr=0x10110ff0, len=0x2, orig_instr=0xabcd"
    )
    ocd.cmd.return_value = _mock_command_result(bp_command_output)
    bps = ocd.list_bp()
    assert len(bps) == 2
    assert bps[0] == BpInfo(addr=0x10110000, size=4, bp_type=BpType.HW, orig_instr=None)
    assert bps[1] == BpInfo(
        addr=0x10110FF0, size=2, bp_type=BpType.SW, orig_instr=0xABCD
    )
    ocd.cmd.assert_called_once_with("bp")


def test_add_bp(ocd):
    ocd.add_bp(0x10001800, 2)
    ocd.cmd.assert_called_once_with("bp 0x10001800 2")
    ocd.cmd.reset_mock()

    ocd.add_bp(0x10002200, 4, hw=True)
    ocd.cmd.assert_called_once_with("bp 0x10002200 4 hw")


def test_remove_bp(ocd):
    ocd.remove_bp(0x10001500)
    ocd.cmd.assert_called_once_with("rbp 0x10001500")


def test_remove_all_bp(ocd):
    ocd.remove_all_bp()
    ocd.cmd.assert_called_once_with("rbp all")


def test_list_wp_empty(ocd):
    ocd.cmd.return_value = _mock_command_result("")
    assert ocd.list_wp() == []
    ocd.cmd.assert_called_once_with("wp")


def test_list_wp_non_empty(ocd):
    wp_command_output = (
        "address: 0x10002000, len: 0x00000004, r/w/a: r, value: 0x00000000, mask: 0xffffffffffffffff\n"  # noqa: E501
        "address: 0x10002800, len: 0x00000002, r/w/a: w, value: 0x00000000, mask: 0xffffffffffffffff\n"  # noqa: E501
        "address: 0x10003000, len: 0x00000008, r/w/a: a, value: 0x00001122, mask: 0xffffffffffff0000\n"  # noqa: E501
    )
    ocd.cmd.return_value = _mock_command_result(wp_command_output)
    wps = ocd.list_wp()
    ocd.cmd.assert_called_once_with("wp")

    assert len(wps) == 3
    assert wps[0] == WpInfo(
        addr=0x10002000, size=4, wp_type=WpType.READ, value=0x0, mask=(2**64 - 1)
    )
    assert wps[1] == WpInfo(
        addr=0x10002800, size=2, wp_type=WpType.WRITE, value=0x0, mask=(2**64 - 1)
    )
    assert wps[2] == WpInfo(
        addr=0x10003000,
        size=8,
        wp_type=WpType.ACCESS,
        value=0x1122,
        mask=0xFFFFFFFFFFFF0000,
    )


def test_add_wp(ocd):
    ocd.add_wp(0x2001000, 2)
    ocd.cmd.assert_called_once_with("wp 0x2001000 2 a")
    ocd.cmd.reset_mock()

    ocd.add_wp(0x2002000, 4, WpType.READ)
    ocd.cmd.assert_called_once_with("wp 0x2002000 4 r")
    ocd.cmd.reset_mock()

    ocd.add_wp(0x2003000, 8, WpType.WRITE)
    ocd.cmd.assert_called_once_with("wp 0x2003000 8 w")
    ocd.cmd.reset_mock()

    ocd.add_wp(0x2004000, 16, WpType.ACCESS)
    ocd.cmd.assert_called_once_with("wp 0x2004000 16 a")


def test_remove_wp(ocd):
    ocd.remove_wp(0x10003F00)
    ocd.cmd.assert_called_once_with("rwp 0x10003f00")


def test_remove_all_wp(ocd):
    ocd.remove_all_wp()
    ocd.cmd.assert_called_once_with("rwp all")


def test_echo(ocd):
    ocd.echo("Some text to print")
    ocd.cmd.assert_called_once_with("echo {Some text to print}")


def test_version(ocd):
    ocd.cmd.return_value = _mock_command_result("openocd version string")
    assert ocd.version() == "openocd version string"
    ocd.cmd.assert_called_once_with("version")


def test_version_tuple(ocd):
    ocd.version = mock.Mock()
    ocd.version.return_value = "Open On-Chip Debugger 11.12.13 blah blah"
    assert ocd.version_tuple() == (11, 12, 13)


def test_version_tuple_2(ocd):
    ocd.version = mock.Mock()
    ocd.version.return_value = "My Little Open On-Chip Debugger 2.3.4 blah blah"
    assert ocd.version_tuple() == (2, 3, 4)


def test_version_tuple_3(ocd):
    ocd.version = mock.Mock()
    ocd.version.return_value = "xPack Open On-Chip Debugger 0.12.0+dev-01557-gdd1758272-dirty (2024-04-02-07:27)"
    assert ocd.version_tuple() == (0, 12, 0)


def test_version_tuple_error(ocd):
    ocd.version = mock.Mock()
    ocd.version.return_value = "Open On-Chip Debugger 9a.10b.11 blah blah"
    with pytest.raises(ValueError) as e:
        ocd.version_tuple()
    assert "Unable to parse the version string received from OpenOCD" in str(e)


def test_target_names(ocd):
    dummy_target_names = "target_1\n" "target_2\n" "target_3\n"
    ocd.cmd.return_value = _mock_command_result(dummy_target_names)
    assert ocd.target_names() == ["target_1", "target_2", "target_3"]


def test_select_target(ocd):
    ocd.select_target("name_of_target")
    ocd.cmd.assert_called_once_with("targets name_of_target")


def test_set_poll(ocd):
    ocd.set_poll(True)
    ocd.cmd.assert_called_once_with("poll on")
    ocd.cmd.reset_mock()

    ocd.set_poll(False)
    ocd.cmd.assert_called_once_with("poll off")


def test_exit(ocd):
    ocd.disconnect = mock.Mock()
    ocd.exit()
    ocd.disconnect.assert_called_once()
    ocd.cmd.assert_not_called()


def test_shutdown(ocd):
    ocd.disconnect = mock.Mock()
    ocd.shutdown()
    ocd.cmd.assert_called_once_with("shutdown", throw=False)
    ocd.disconnect.assert_called_once()
