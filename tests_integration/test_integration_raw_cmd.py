# SPDX-License-Identifier: MIT

import pytest

from py_openocd_client import OcdCommandTimeoutError, PyOpenocdClient


def test_no_output(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("puts some_text")

        # The text is printed to stdout but the actual TCL command
        # does not produce any output.
        assert out == ""


def test_return(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return abcdef")
        assert out == "abcdef"


def test_return_with_whitespace(openocd_process, has_buggy_whitespace_trim):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return {  abc 4567 }")

        if has_buggy_whitespace_trim:
            assert out == "abc 4567"
            pytest.xfail("known OpenOCD whitespace bug")
        else:
            assert out == "  abc 4567 "


def test_nonexistent_cmd(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("nonexistent_cmd")
        assert out == 'invalid command name "nonexistent_cmd"'


def test_echo_capture(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("capture { echo {abcdef} }")
        # "echo" appends \n at the end
        assert out == "abcdef\n"


def test_echo_capture_whitespace(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("capture { echo { 123 456 } }")
        assert out == " 123 456 \n"


def test_catch_success(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return [ catch { version } ]")
        assert int(out) == 0  # success code


def test_catch_error(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("return [ catch { nonexistent_cmd } ]")
        assert int(out) != 0  # error code


def test_catch_throw(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd('return [ catch { throw 22 "Error message" } ]')
        assert int(out) == 22  # error code


def _parse_out(out):
    # "5 some text" -> (5, "some text")
    parts = out.split(" ", maxsplit=1)
    retcode = int(parts[0])
    out = parts[1]
    return int(parts[0]), parts[1]


def test_catch_output_and_success(openocd_process):
    with PyOpenocdClient() as ocd:
        cmd = 'set RETCODE [ catch { version } OUT ]; return "$RETCODE $OUT" '
        out = ocd.raw_cmd(cmd)
        retcode, text = _parse_out(out)

        assert retcode == 0  # success code
        assert "Open On-Chip Debugger" in text


def test_catch_output_and_success_whitespace(openocd_process, has_buggy_whitespace_trim):
    with PyOpenocdClient() as ocd:
        cmd = 'set RETCODE [ catch { string repeat { a } 4 } OUT ]; return "$RETCODE $OUT" '
        out = ocd.raw_cmd(cmd)
        retcode, text = _parse_out(out)

        assert retcode == 0  # success code

        if has_buggy_whitespace_trim:
            assert text == " a  a  a  a"
            pytest.xfail("known OpenOCD whitespace bug")
        else:
            assert text == " a  a  a  a "


def test_catch_output_and_error(openocd_process):
    with PyOpenocdClient() as ocd:
        cmd = 'set RETCODE [ catch { nonexistent_cmd } OUT; ]; return "$RETCODE $OUT" '
        out = ocd.raw_cmd(cmd)
        retcode, text = _parse_out(out)

        assert retcode != 0  # error code
        assert "invalid command" in text


def test_catch_output_and_throw(openocd_process):
    with PyOpenocdClient() as ocd:
        cmd = 'set RETCODE [catch { throw 25 {my msg} } OUT;]; return "$RETCODE $OUT"'
        out = ocd.raw_cmd(cmd)
        retcode, text = _parse_out(out)

        assert retcode == 25  # error code
        assert text == "my msg"


def test_catch_output_and_throw_whitespace(openocd_process, has_buggy_whitespace_trim):
    with PyOpenocdClient() as ocd:
        cmd = 'set RETCODE [catch { throw 25 { my msg  } } OUT;]; return "$RETCODE $OUT"'
        out = ocd.raw_cmd(cmd)
        retcode, text = _parse_out(out)

        assert retcode == 25  # error code
        if has_buggy_whitespace_trim:
            assert text == " my msg"
            pytest.xfail("known OpenOCD whitespace bug")
        else:
            assert text == " my msg  "


def test_raw_cmd_timeout_ok(openocd_process):
    with PyOpenocdClient() as ocd:
        out = ocd.raw_cmd("sleep 1000", timeout=2.0)
        assert out == ""


def test_raw_cmd_timeout_exceeded(openocd_process):
    with PyOpenocdClient() as ocd:
        with pytest.raises(OcdCommandTimeoutError) as e:
            ocd.raw_cmd("sleep 2000", timeout=1.0)

        assert e.value.raw_cmd == "sleep 2000"
        assert e.value.timeout == 1.0
