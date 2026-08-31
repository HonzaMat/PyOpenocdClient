Console utility ``openocd_cmd``
===============================

The PyOpenocdClient package includes a console utility called ``openocd_cmd``.

This console program can be used to send Tcl commands to OpenOCD from command-line,
shell scripts or other non-Python programs.


Synopsis
--------

.. code-block:: text

   usage: openocd_cmd [-h] [--host HOST] [--port PORT] [--timeout TIMEOUT] command

   Command-line utility that sends a single Tcl command to OpenOCD
   through its Tcl-RPC interface.

   positional arguments:
     command            The Tcl command to send to OpenOCD

   options:
     -h, --help         show this help message and exit
     --host HOST        Hostname or address of the machine where OpenOCD is running (default: 127.0.0.1)
     --port PORT        OpenOCD's Tcl-RPC server port number (default: 6666)
     --timeout TIMEOUT  Timeout for the command execution in seconds (default: 5.0)


Examples of use
---------------

.. code-block:: bash

   $ openocd_cmd --host 127.0.0.1 --port 6666 version
   Open On-Chip Debugger 0.12.0+dev-02634-g390b9d731 (2026-08-29-14:15)

   $ openocd_cmd --host 127.0.0.1 --port 6666 "reset halt ; reg pc"
   pc (/32): 0x08001234


Exit code of openocd_cmd
------------------------

If the Tcl command is executed successfully, the ``openocd_cmd`` utility exits with code 0.

If an error occurs, the utility exits with a non-zero code, as shown in the
table below.

+-----------------------------------------+-----------------------------------------------------------+
| Situation                               | Exit code of ``openocd_cmd``                              |
+=========================================+===========================================================+
| Tcl command was executed and succeeded. | 0                                                         |
+-----------------------------------------+-----------------------------------------------------------+
| Tcl command was executed and failed.    | Non-zero exit code, equal to the Tcl command return code. |
+-----------------------------------------+-----------------------------------------------------------+
| Connection failure                      | 91                                                        |
+-----------------------------------------+-----------------------------------------------------------+
| Invalid response from OpenOCD           | 92                                                        |
+-----------------------------------------+-----------------------------------------------------------+
| Command timeout                         | 93                                                        |
+-----------------------------------------+-----------------------------------------------------------+


Output of openocd_cmd
---------------------

All textual output of the Tcl command is written to stdout.

Any error messages coming from the ``openocd_cmd`` tool itself are written to stderr.
This keeps them separate from the command output.


Alternative invocation
----------------------

The ``openocd_cmd`` utility can be invoked also via ``python3 -m py_openocd_client.cli``
command, which serves as an alias.

The following two commands are therefore equivalent:

.. code-block:: bash

   $ openocd_cmd --host 127.0.0.1 --port 6666 "reset halt"

   $ python3 -m py_openocd_client.cli --host 127.0.0.1 --port 6666 "reset halt"

