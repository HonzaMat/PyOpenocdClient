# SPDX-License-Identifier: MIT

import socket
from unittest import mock

import pytest

from py_openocd_client.baseclient import _PyOpenocdBaseClient

_COMMAND_DELIMITER = b"\x1a"


@pytest.fixture()
def socket_inst_mock():
    # Prepare a mock that will be returned by socket.socket().
    #
    # This is to make introspection possible even after
    # the class discards its reference to the socket object
    # upon disconnection.
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


def test_connect_disconnect(socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("192.168.1.1", 6666)

    assert not ocd_base.is_connected()
    assert ocd_base._socket is None

    ocd_base.connect()
    assert ocd_base.is_connected()
    assert ocd_base._socket is not None
    socket_inst_mock.connect.assert_called_with(("192.168.1.1", 6666))
    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.setsockopt.assert_called_with(
        socket.IPPROTO_TCP, socket.TCP_NODELAY, True
    )
    socket_inst_mock.setsockopt.assert_called_once()
    socket_inst_mock.reset_mock()

    ocd_base.disconnect()
    assert not ocd_base.is_connected()
    socket_inst_mock.shutdown.assert_called_once()
    socket_inst_mock.close.assert_called_once()
    socket_inst_mock.reset_mock()

    # double disconnect is no-op, no error is thrown
    ocd_base.disconnect()
    assert not ocd_base.is_connected()

    # reconnecting when disconnected
    ocd_base.reconnect()
    assert ocd_base.is_connected()
    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.reset_mock()

    # reconnecting when already connected
    ocd_base.reconnect()
    assert ocd_base.is_connected()
    socket_inst_mock.shutdown.assert_called_once()
    socket_inst_mock.close.assert_called_once()
    socket_inst_mock.connect.assert_called_once()
    socket_inst_mock.reset_mock()

    ocd_base.disconnect()
    assert not ocd_base.is_connected()


def test_raw_cmd(select_mock):
    ocd_base = _PyOpenocdBaseClient("192.168.2.1", 6666)
    ocd_base.connect()
    assert ocd_base.is_connected()

    ocd_base._socket.recv.side_effect = [
        b"result_line1\nresult_line2" + _COMMAND_DELIMITER
    ]

    result = ocd_base.raw_cmd("some_command")
    assert result == "result_line1\nresult_line2"

    select_mock.assert_called_once()
    select_mock.assert_called_with([ocd_base._socket], [], [], 0)

    ocd_base._socket.send.assert_called_once()
    ocd_base._socket.send.assert_called_with(b"some_command" + _COMMAND_DELIMITER)

    ocd_base._socket.recv.assert_called_once()


def test_raw_cmd_multiple_pieces(select_mock, socket_inst_mock):
    ocd_base = _PyOpenocdBaseClient("192.168.2.1", 7777)
    ocd_base.connect()
    assert ocd_base.is_connected()

    ocd_base._socket.recv.side_effect = [
        b"Lorem ip",
        socket.timeout(),
        b"sum dolor s",
        socket.timeout(),
        b"il amet" + _COMMAND_DELIMITER,
    ]

    result = ocd_base.raw_cmd("my_command")

    assert result == "Lorem ipsum dolor sil amet"

    select_mock.assert_called_once()
    select_mock.assert_called_with([ocd_base._socket], [], [], 0)

    socket_inst_mock.send.assert_called_once()
    socket_inst_mock.send.assert_called_with(b"my_command" + _COMMAND_DELIMITER)

    assert ocd_base._socket.recv.call_count == 5
