# SPDX-License-Identifier: MIT

import select
import socket
import time
from typing import Optional

from .errors import OcdCommandTimeout, OcdConnectionError


class _PyOpenocdBaseClient:
    """
    Internal class that implements the TCL command exchange with OpenOCD.

    The base layer of the communication is implemented in this class:
    - Sending of commands
    - Receiving of responses
    - Handling of network sockets
    - Detection of communication errors
    - Detection of command timeouts

    This class is not intended for direct use. The derived class
    "PyOpenocdClient", built on top of this, should be used instead.
    """

    # Character that delimits commands and responses
    COMMAND_DELIMITER = b"\x1a"

    # Maximum response size (in bytes) - safety limit
    MAX_RESPONSE_SIZE = 8 * 1024 * 1024

    # Timeout for sending commands
    SEND_TIMEOUT = 3.0

    # Default timeout for receiving responses. Can be overriden by the user.
    DEFAULT_RECV_TIMEOUT = 5.0

    # Maximum wait time for one poll of the network socket while waiting
    # for command response.
    RECV_POLL_TIMEOUT = 1.0

    # Maximum number of bytes to receive in one go (in one recv() operation)
    RECV_BLOCK_SIZE = 2048

    # Character set used for decoding of responses from OpenOCD
    CHARSET = "utf-8"

    def __init__(self, host: str, port: int) -> None:
        if not (1 <= port <= 65535):
            raise ValueError("Incorrect TCP port. Expecting number in range 1 - 65535.")

        self._host: str = host
        self._port: int = port
        self._socket: Optional[socket.socket] = None
        self._default_recv_timeout: float = self.DEFAULT_RECV_TIMEOUT

    def connect(self) -> None:
        if self.is_connected():
            raise OcdConnectionError("Already connected")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self._host, self._port))
        except OSError as e:
            raise OcdConnectionError(
                f"Could not connect to OpenOCD at {self._host}, port {self._port}"
            ) from e

        # Connection established
        self._socket = s

        try:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        except OSError as e:
            # Good manners: Try close the socket but don't care if that fails.
            self._close_socket()
            raise OcdConnectionError("Could not set TCP_NODELAY for the socket") from e

    def disconnect(self) -> None:
        if not self.is_connected():
            # Already disconnected, nothing to do.
            # Don't consider this to be an error.
            return

        self._close_socket(disconnect_nicely=True)

    def reconnect(self) -> None:
        self.disconnect()
        self.connect()

    def is_connected(self) -> bool:
        return self._socket is not None

    def set_default_timeout(self, timeout: float) -> None:
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero")
        self._default_recv_timeout = timeout

    def _check_no_premature_recvd_bytes(self) -> None:
        assert self._socket is not None
        rd, _, _ = select.select([self._socket], [], [], 0)  # Don't block, just poll
        if len(rd) > 0:
            raise OcdConnectionError(
                "Received unexpected bytes from OpenOCD before "
                "the command was even sent."
            )

    def _do_send_cmd(self, cmd: str) -> None:
        assert self.is_connected()
        assert self._socket is not None

        # Safety:
        self._check_no_premature_recvd_bytes()

        data = cmd.encode(self.CHARSET) + self.COMMAND_DELIMITER
        self._socket.settimeout(self.SEND_TIMEOUT)
        self._socket.send(data)

    def _do_recv_response(self, timeout: Optional[float] = None) -> str:
        assert self.is_connected()
        assert self._socket is not None

        recv_data = b""
        curr_timeout = timeout if timeout is not None else self._default_recv_timeout

        self._socket.settimeout(self.RECV_POLL_TIMEOUT)

        time_start = time.time()
        while time.time() < (time_start + curr_timeout):
            try:
                d = self._socket.recv(self.RECV_BLOCK_SIZE)
            except socket.timeout:
                continue

            if d == b"":
                raise OcdConnectionError("Connection closed by OpenOCD")

            recv_data += d
            if len(recv_data) > self.MAX_RESPONSE_SIZE:
                raise OcdConnectionError(
                    "Received too big response "
                    f"(exceeding {self.MAX_RESPONSE_SIZE} bytes)"
                )

            if self.COMMAND_DELIMITER in recv_data:
                # Safety check: the command delimiter must be the last received byte
                if recv_data.find(self.COMMAND_DELIMITER) != len(recv_data) - 1:
                    raise OcdConnectionError(
                        "Received extra unexpected byte(s) after the command "
                        "response delimiter!"
                    )

                # We have received all bytes of the response.
                # Drop the delimiter & decode the rest of the bytes into a string.
                recv_data = recv_data[:-1]
                return recv_data.decode(self.CHARSET)

        # Timed out
        raise OcdCommandTimeout(
            "Did not receive the complete command response "
            f"within {curr_timeout} seconds."
        )

    def raw_cmd(self, cmd: str, timeout: Optional[float] = None) -> str:
        if (timeout is not None) and (timeout <= 0):
            raise ValueError(
                "Timeout must be positive float number "
                "(or None to use the default timeout)"
            )

        if not self.is_connected():
            raise OcdConnectionError("Not connected")

        try:
            self._do_send_cmd(cmd)
            return self._do_recv_response(timeout=timeout)
        except (OcdCommandTimeout, OcdConnectionError):
            # Connection error -> disconnect.
            # Timeout -> disconnect too. This is essential to avoid any
            # late-arriving data to be interpreted as response to
            # the next command.
            self._close_socket()
            raise

    def _close_socket(self, disconnect_nicely: bool = False) -> None:
        """
        Disconnect and close the socket.

        Ignore any errors in the process because there is not much we can do.
        """

        assert self._socket is not None

        if disconnect_nicely:
            # shutdown() causes "nice" TCP disconnection via TCP FIN flags
            # as opposed to TCP RST.
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        try:
            self._socket.close()
        except OSError:
            pass

        self._socket = None
