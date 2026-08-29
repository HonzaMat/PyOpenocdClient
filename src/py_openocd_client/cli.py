# SPDX-License-Identifier: MIT

import sys
import argparse

from .client import PyOpenocdClient
from .errors import OcdConnectionError, OcdInvalidResponseError, OcdCommandTimeoutError


def eprint(s: str) -> None:
    print("error: " + s, file=sys.stderr)


def parse_args():
    desc = "Command-line utility that sends a single Tcl command to OpenOCD through its Tcl-RPC interface."
    epilog = (
        "If the Tcl command completes successfully, this tool exits with code 0. "
        "Connection errors or command execution errors cause it to exit with a non-zero code. "
        "The output of the Tcl command is written to stdout. "
        "Any error messages are written to stderr."
    )
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname or address of the machine where OpenOCD runs (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6666,
        help="OpenOCD's Tcl-RPC server port number (default: 6666)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout for the command execution in seconds (default: 10.0)",
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
                eprint(f"The command has failed (return code {result.retcode}).")
            return result.retcode

    except OcdConnectionError as e:
        eprint(str(e))
        return 91

    except OcdInvalidResponseError as e:
        eprint("OpenOCD responded unexpectedly: " + str(e))
        return 92

    except OcdCommandTimeoutError as e:
        eprint(f"Timeout: The command did not complete within {e.timeout} seconds.")
        return 93


if __name__ == "__main__":
    sys.exit(main())
