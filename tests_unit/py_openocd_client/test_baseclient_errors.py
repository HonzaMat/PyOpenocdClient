# SPDX-License-Identifier: MIT

import socket
from typing import List
from unittest import mock

import pytest

from py_openocd_client import OcdCommandTimeoutError, OcdConnectionError
from py_openocd_client.baseclient import _PyOpenocdBaseClient

_COMMAND_DELIMITER = b"\x1a"


@pytest.fixture()
def socket_inst_mock():
    # Prepare a mock that will be returned by socket.socket().
    #
    # This is to allow introspection even after the _PyOpenocdBaseClient
    # class disconnects and discards its reference to the socket object.
    return mock.Mock()


@pytest.fixture(autouse=True)
def socket_mock(socket_inst_mock):
    with mock.patch("socket.socket") as m:
        m.return_value = socket_inst_mock
        yield m


@pytest.fixture(autouse=True)
def select_mock():
    # Mock select.select(). Pretend that there are no data
    # on the socket waiting to be received.
    with mock.patch("select.select") as m:
        m.return_value = [], [], []
        yield m


def test_constructor_wrong_port():
    with pytest.raises(ValueError) as e:
        _PyOpenocdBaseClient("localhost", 123456)

    assert "Incorrect TCP port" in str(e)


def test_double_connect():
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()
    assert ocd_base.is_connected()

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.connect()
    assert "Already connected" in str(e)

    # Disconnected after error
    assert ocd_base.is_connected()


def test_connect_error(socket_inst_mock):
    socket_inst_mock.connect.side_effect = [ConnectionRefusedError("refused")]

    ocd_base = _PyOpenocdBaseClient("localhost", 6666)

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.connect()
    assert "Could not connect to OpenOCD" in str(e)

    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.setsockopt.assert_not_called()
    socket_inst_mock.close.assert_not_called()
    assert not ocd_base.is_connected()


def test_set_tcp_nodelay_error(socket_inst_mock):
    socket_inst_mock.setsockopt.side_effect = [OSError("some error")]

    ocd_base = _PyOpenocdBaseClient("localhost", 6666)

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.connect()
    assert "Could not set TCP_NODELAY" in str(e)

    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.setsockopt.assert_called_once()
    socket_inst_mock.close.assert_called_once()
    assert not ocd_base.is_connected()


def test_recv_extra_bytes_before_sending_command(socket_inst_mock, select_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    # Pretend that some data arrived before the command
    select_mock.return_value = [ocd_base._socket], [], []

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.raw_cmd("some_command")

    assert "Received unexpected bytes from OpenOCD" in str(e)

    socket_inst_mock.send.assert_not_called()
    socket_inst_mock.recv.assert_not_called()

    # Must be disconnected after an error
    socket_inst_mock.close.assert_called_once()
    assert not ocd_base.is_connected()


def test_set_default_timeout_wrong_value():
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)

    with pytest.raises(ValueError):
        ocd_base.set_default_timeout(-8.5)

    with pytest.raises(ValueError):
        ocd_base.set_default_timeout(0)


def test_raw_cmd_timeout_wrong_value():
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    with pytest.raises(ValueError):
        ocd_base.raw_cmd("cmd1", timeout=-5)

    with pytest.raises(ValueError):
        ocd_base.raw_cmd("cmd2", timeout=0)


def test_raw_cmd_not_connected():
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.raw_cmd("dummy_command with args")

    assert "Not connected" in str(e)


def test_raw_cmd_connection_closed_by_openocd(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    socket_inst_mock.recv.return_value = b""

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.raw_cmd("some_cmd")

    assert "Connection closed by OpenOCD" in str(e)

    socket_inst_mock.send.assert_called_once()
    socket_inst_mock.recv.assert_called_once()
    assert not ocd_base.is_connected()


def test_raw_cmd_extra_bytes_after_delimiter(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    socket_inst_mock.recv.return_value = (
        b"some_resp" + _COMMAND_DELIMITER + b"extra_bytes"
    )

    with pytest.raises(OcdConnectionError) as e:
        ocd_base.raw_cmd("some_cmd")

    assert "Received extra unexpected byte(s)" in str(e)

    socket_inst_mock.send.assert_called_once()
    socket_inst_mock.recv.assert_called_once()
    assert not ocd_base.is_connected()


def _prepare_big_response(size: int) -> List[bytes]:
    assert size > 0
    resp = b"a" * (size - 1) + _COMMAND_DELIMITER
    # split to chunks of 1 kB maximum
    return list(_chunks(resp, 1024))


def _chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def test_raw_cmd_too_big_response(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    # We are dealing with a large response, so avoid sporadicaly hitting
    # the timeout: pretend that the time does not pass.
    with mock.patch("time.time") as time_mock:
        time_mock.return_value = 1718558082.26  # return constant time value

        # Exceed the maximum message size by 1 byte
        data_to_receive = _prepare_big_response(8 * 1024 * 1024 + 1)
        data_to_receive_size = len(b"".join(data_to_receive))
        assert data_to_receive_size == 8 * 1024 * 1024 + 1

        socket_inst_mock.recv.side_effect = data_to_receive

        with pytest.raises(OcdConnectionError) as e:
            ocd_base.raw_cmd("command")

        assert "Received too big response" in str(e)

        socket_inst_mock.send.assert_called_once()
        assert socket_inst_mock.recv.call_count == 8 * 1024 + 1
        assert not ocd_base.is_connected()


@pytest.mark.parametrize("use_global_timeout", [True, False])
def test_raw_cmd_timeout(socket_inst_mock, use_global_timeout):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()
    assert socket_inst_mock.connect.call_count == 1
    assert socket_inst_mock.close.call_count == 0

    if use_global_timeout:
        ocd_base.set_default_timeout(4.5)

    with mock.patch("time.time") as time_mock:
        # The first time query is the initial; the subsequent ones happen
        # before each recv() call.
        time_mock.side_effect = [10, 11, 12, 13, 14, 15]

        chunks_to_receive = [b"abc", b"def", socket.timeout(), b"ghi"]
        socket_inst_mock.recv.side_effect = chunks_to_receive

        with pytest.raises(OcdCommandTimeoutError) as e:
            if not use_global_timeout:
                ocd_base.raw_cmd("my_command", timeout=4.5)
            else:
                ocd_base.raw_cmd("my_command")

        expected_msg = (
            "Did not receive the complete command response within 4.5 seconds."
        )
        assert expected_msg in str(e)
        assert e.value.raw_cmd == "my_command"
        assert e.value.timeout == 4.5

    # Command timeout shall trigger re-connection
    assert ocd_base.is_connected()
    assert socket_inst_mock.connect.call_count == 2
    assert socket_inst_mock.close.call_count == 1


def test_raw_cmd_reconnection_error_after_timeout(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    # Check that the first socket connection was established
    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.close.assert_not_called()
    assert ocd_base.is_connected()

    ocd_base.set_default_timeout(2.5)

    with mock.patch("time.time") as time_mock:
        time_mock.side_effect = [10, 11, 12, 13]

        chunks_to_receive = [b"abc", b"def", b"ghi"]
        socket_inst_mock.recv.side_effect = chunks_to_receive

        # Prepare a second socket instance that fails on connect()
        with mock.patch("socket.socket") as socket_mock_2:
            socket_inst_mock_2 = mock.Mock()
            socket_inst_mock_2.connect.side_effect = [OSError("connect() failed")]

            socket_mock_2.return_value = socket_inst_mock_2

            # Command timeout must cause re-connection. The reconnection will fail,
            # resulting in OcdConnectionError.
            with pytest.raises(OcdConnectionError) as e:
                ocd_base.raw_cmd("my_command")

            # The first socket connection must have been closed.
            socket_inst_mock.close.assert_called_once()
            # The second socket connection must have been attempted (but failed).
            socket_inst_mock_2.connect.assert_called_once()

        # The overall final state must be "not connected".
        assert not ocd_base.is_connected()


def test_socket_close_errors_suppressed(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("localhost", 6666)
    ocd_base.connect()

    # Set up shutdown() and close() to raise an error
    socket_inst_mock.shutdown.side_effect = [OSError("socket shutdown() failed")]
    socket_inst_mock.close.side_effect = [OSError("socket close() failed")]

    # The error must not be propagated
    ocd_base.disconnect()
