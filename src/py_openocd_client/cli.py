# SPDX-License-Identifier: MIT

import argparse
import sys

from .client import PyOpenocdClient
from .errors import OcdCommandTimeoutError, OcdConnectionError, OcdInvalidResponseError

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 6666
_DEFAULT_TIMEOUT = 10.0

_EXIT_CODE_CONNECTION_ERROR = 91
_EXIT_CODE_INVALID_RESPONSE = 92
_EXIT_CODE_COMMAND_TIMEOUT = 93


def eprint(s: str) -> None:
    print("error: " + s, file=sys.stderr)


def parse_args() -> argparse.Namespace:
    desc = (
        "Command-line utility that sends a single Tcl command to OpenOCD\n"
        "through its Tcl-RPC interface."
    )
    epilog = (
        "If the Tcl command completes successfully, this tool exits with code 0.\n"
        "Connection errors or command execution errors cause it to exit with\n"
        "a non-zero code.\n\n"
        "The output of the Tcl command is written to stdout.\n"
        "Any error messages are written to stderr."
    )
    parser = argparse.ArgumentParser(
        description=desc,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.color = False

    parser.add_argument(
        "--host",
        default=_DEFAULT_HOST,
        help=(
            "Hostname or address of the machine where OpenOCD is running "
            f"(default: {_DEFAULT_HOST})"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_DEFAULT_PORT,
        help=f"OpenOCD's Tcl-RPC server port number (default: {_DEFAULT_PORT})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT,
        help=(
            "Timeout for the command execution in seconds "
            f"(default: {_DEFAULT_TIMEOUT:.1f})"
        ),
    )
    parser.add_argument(
        "command",
        help="The Tcl command to send to OpenOCD",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        with PyOpenocdClient(args.host, args.port) as ocd:
            ocd.set_default_timeout(args.timeout)
            result = ocd.cmd(args.command, throw=False)
            print(result.out)

            if result.retcode != 0:
                eprint(f"The command has failed (return code: {result.retcode}).")
            return result.retcode

    except OcdConnectionError as e:
        eprint(str(e))
        return _EXIT_CODE_CONNECTION_ERROR

    except OcdInvalidResponseError as e:
        eprint("OpenOCD responded unexpectedly: " + str(e))
        return _EXIT_CODE_INVALID_RESPONSE

    except OcdCommandTimeoutError as e:
        eprint(f"Timeout: The command did not complete within {e.timeout:.1f} seconds.")
        return _EXIT_CODE_COMMAND_TIMEOUT


if __name__ == "__main__":
    sys.exit(main())
