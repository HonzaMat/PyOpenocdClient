Quickstart
==========

Configuring OpenOCD for TCL connections
---------------------------------------

OpenOCD by default listens for TCL connections on TCP port `6666`
on the local machine (``127.0.0.1``). This is typically sufficient for
common use cases and no further confguration is necessary.

If needed, OpenOCD command `tcl port`_ can be used to change the port number
(e.g. ``tcl port 1234``).

To make OpenOCD accessible from remote network machines, not just
from the localhost, use OpenOCD command `bindto`_ (e.g. ``bindto 0.0.0.0``).
Note that the TCL connection to OpenOCD is not encrypted nor authenticated, and for that
reason it should only be used within trusted network environments.

.. _tcl port: https://openocd.org/doc/html/Server-Configuration.html#index-tcl-port
.. _bindto: https://openocd.org/doc/html/General-Commands.html#index-bindto

Basic usage of PyOpenocdClient
------------------------------

One instance of class :py:class:`PyOpenocdClient<py_openocd_client.PyOpenocdClient>`
represents one TCL connection to a running OpenOCD program.

:py:class:`PyOpenocdClient<py_openocd_client.PyOpenocdClient>` can be used in two ways:

- Manually: Make an instance of this class and call ``connect()`` and ``disconnect()`` methods
  explicitly.

- As a context manager (in ``with`` block): In this case the connection is established and closed
  automatically.

Both these approaches are shown below.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    # Manual use of PyOpenocdClient:
    # connect() and disconnect() needs to be called.

    ocd = PyOpenocdClient(host="some_hostname", port=1234)  # default is localhost:6666
    ocd.connect()

    # Now interact with OpenOCD. For example:
    ocd.reset_halt()
    ocd.cmd("load_image path/to/program.elf")
    ocd.resume()
    # ...

    ocd.disconnect()

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    # Use PyOpenocdClient as a context manager:
    # The connection is established and closed automatically.

    with PyOpenocdClient(host="some_hostname", port=1234) as ocd:

        # Now interact with OpenOCD. For example:
        ocd.reset_halt()
        ocd.cmd("load_image path/to/program.elf")
        ocd.resume()
        # ...

Executing TCL commands
----------------------

Any TCL command can be sent to OpenOCD via the
:py:meth:`cmd()<py_openocd_client.PyOpenocdClient.cmd>` method.

PyOpenocdClient handles the outcome of the command (success or failure) this way:

- If the command completes successfully, an instance of
  :py:class:`OcdCommandResult<py_openocd_client.OcdCommandResult>` is returned.
- If the command fails, :py:meth:`OcdCommandFailedError<py_openocd_client.OcdCommandFailedError>`
  gets raised.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient, OcdCommandFailedError

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # Execute a single command, don't care about its output:
        ocd.cmd("poll off")

        # Execute a command and obtain its textual output:
        result = ocd.cmd("version")
        print(f"OpenOCD version is: {result.out}")

        # Execute a command and handle its possible failure:
        try:
            result = ocd.cmd("load_image path/to/program.elf")
        except OcdCommandFailedError as e:
            print("Image loading failed. "
                  f"Command error code: {e.result.retcode}. "
                  f"Command message: {e.result.out}.")
        else:
            print(f"Image loading successful. Command message: {result.out}")


Convenience methods for common commands
---------------------------------------

For easier use, PyOpenocdClient provides convenience methods for frequently used
OpenOCD commands. These methods execute the given command and parse the command output
(if applicable) so that the command result is returned in the form of native Python data types.

Therefore it is not necessary to use the :py:meth:`cmd()<py_openocd_client.PyOpenocdClient.cmd>`
and then parse the command output manually.

Some of the convenience methods are shown in the example below. Please refer to the :ref:`api_doc`
for the full list.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # Examples of several of the convenience methods:

        # Read and write processor registers
        pc_value = ocd.get_reg("pc")  # Returns integer value of the register
        print(f"The value of the PC register is: {hex(pc_value)}")

        ocd.set_reg("gp", 0x1234)

        # Read and write memory
        mem_data = ocd.read_memory(0x1000, 32, 8)  # Returns a list of integers
        print(f"Eight 32-bit words starting at memory address 0x1000: {mem_data}")

        ocd.write_memory(0x2000, 16, [0x1234, 0x5678, 0xabcd])

        # Place or remove a breakpoint
        ocd.add_bp(0x2001000, 4, hw=True)
        ocd.remove_bp(0x2001000)

        # Halting, resuming and reset
        ocd.resume()
        ocd.halt()
        ocd.reset_halt()
        ocd.reset_run()

        # Checking target state
        print(f"The target state is {ocd.curstate()}")

        if ocd.is_halted():
            print("The target is halted")

        # Logging
        ocd.echo("A custom message to show in OpenOCD log")

        # Terminating OpenOCD
        ocd.shutdown()

Handling command timeouts
-------------------------

If execution of a command takes too long and a configured timeout is exceeded,
:py:class:`OcdCommandTimeoutError<py_openocd_client.OcdCommandTimeoutError>`
gets raised.

The global default timeout -- applicable to all commands sent by PyOpenocdClient --
can be changed by
:py:meth:`set_default_timeout()<py_openocd_client.PyOpenocdClient.set_default_timeout>`.

It is also possible to specify a timeout for an individual command which then
takes precedence over the global timeout. That is done via the ``timeout`` parameter,
available on certain methods.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # All commands from now on will have a timeout of 10 seconds:
        ocd.set_default_timeout(10.0)

        # ...

        # Override the default timeout for an individual command:
        ocd.cmd("load_image big_program.elf", timeout=30.0)

