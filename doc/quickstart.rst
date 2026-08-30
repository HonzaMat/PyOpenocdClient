Quickstart for Python
=====================

Configuring OpenOCD for Tcl connections
---------------------------------------

By default, OpenOCD listens for Tcl-RPC connections on TCP port 6666
on the local machine (127.0.0.1). This is sufficient for common use cases,
so no further configuration is usually necessary.

If you need to change the Tcl-RPC server port, use the OpenOCD' `tcl port`_ command.

To make the Tcl-RPC server accessible from remote machines, not just from
the local machine, use OpenOCD's bindto_ command (for example, `bindto 0.0.0.0`).

.. warning::

   The Tcl-RPC connection to OpenOCD is not encrypted nor authenticated. For that
   reason, it should only be used within trusted network environments.

.. _tcl port: https://openocd.org/doc/html/Server-Configuration.html#index-tcl-port
.. _bindto: https://openocd.org/doc/html/General-Commands.html#index-bindto

Basic usage of PyOpenocdClient
------------------------------

One instance of the class :py:class:`PyOpenocdClient<py_openocd_client.PyOpenocdClient>`
represents one Tcl connection to a running OpenOCD program.

``PyOpenocdClient`` can be used in two ways:

- **Manual use:** Create an instance of this class and explicitly call methods
  ``connect()`` and ``disconnect()`` to establish and close the connection.

- **As a context manager:** Use ``PyOpenocdClient`` in a ``with`` block. The connection
  gets established automatically when entering the block and closed when leaving it.

Both these approaches are shown below.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    # Connect to OpenOCD:
    ocd = PyOpenocdClient(host="localhost", port=6666)
    ocd.connect()

    # Now you can interact with OpenOCD:
    ocd.reset_halt()
    ocd.cmd("load_image path/to/program.elf")
    ocd.resume()
    # ...

    # Close the connection when done:
    ocd.disconnect()

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    # Using PyOpenocdClient in a "with" block:
    # The connection is automatically established at the beginning
    # of the "with" block and closed when leaving it.

    with PyOpenocdClient(host="some_hostname", port=1234) as ocd:

        # Now you can interact with OpenOCD:
        ocd.reset_halt()
        ocd.cmd("load_image path/to/program.elf")
        ocd.resume()
        # ...

Executing Tcl commands
----------------------

The method :py:meth:`PyOpenocdClient.cmd()<py_openocd_client.PyOpenocdClient.cmd>`
is used to send Tcl commands to OpenOCD and retrieve their results.

``PyOpenocdClient`` handles the command results as follows:

- If the command completes successfully, the method returns an instance of
  :py:class:`OcdCommandResult<py_openocd_client.OcdCommandResult>`.
- If the command fails, the method raises
  :py:exc:`OcdCommandFailedError<py_openocd_client.OcdCommandFailedError>`.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient, OcdCommandFailedError

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # Execute a command and ignore its textual output:
        ocd.cmd("poll off")

        # Execute a command and retrieve its textual output:
        result = ocd.cmd("version")
        print(f"OpenOCD version is: {result.out}")

        # Execute a command and handle a possible failure:
        try:
            result = ocd.cmd("load_image path/to/program.elf")
        except OcdCommandFailedError as e:
            print("Image loading failed. "
                  f"Command error code: {e.result.retcode}. "
                  f"Command message: {e.result.out}.")
        else:
            print(f"Image loading successful. Command message: {result.out}")


Convenience methods for common OpenOCD commands
-----------------------------------------------

For easier use, PyOpenocdClient provides convenience methods (shortcuts) for frequently
used OpenOCD commands. These methods execute the corresponding command, parse its output
and return it in the form of native Python data types.

This eliminates the need to call
:py:meth:`cmd()<py_openocd_client.PyOpenocdClient.cmd>` and parse the
command output manually.

Some of the available convenience methods are shown below. Please refer to the :ref:`api_doc`
for the complete list.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # Examples of several of the convenience methods:

        # Read and write processor registers
        pc_value = ocd.get_reg("pc")
        print(f"The value of the PC register is: {hex(pc_value)}")

        ocd.set_reg("gp", 0x1234)

        # Read and write memory
        mem_data = ocd.read_memory(0x1000, 32, 8)
        print(f"Eight 32-bit words starting at memory address 0x1000: {mem_data}")

        ocd.write_memory(0x2000, 16, [0x1234, 0x5678, 0xabcd])

        # Place or remove a breakpoint
        ocd.add_bp(0x2001000, 4, hw=True)
        ocd.remove_bp(0x2001000)

        # Halt, resume and reset
        ocd.resume()
        ocd.halt()
        ocd.reset_halt()
        ocd.reset_run()

        # Check target state
        print(f"The target state is {ocd.curstate()}")

        if ocd.is_halted():
            print("The target is halted")

        # Put a message into OpenOCD's log
        ocd.echo("A custom message to show in OpenOCD log")

        # Terminate OpenOCD and disconnect the Tcl-RPC session
        ocd.shutdown()


Handling command timeouts
-------------------------

If execution of a command takes longer than a configured timeout,
:py:class:`OcdCommandTimeoutError<py_openocd_client.OcdCommandTimeoutError>`
is raised.

The global default timeout, which applies to all commands sent through PyOpenocdClient,
can be changed by
:py:meth:`set_default_timeout()<py_openocd_client.PyOpenocdClient.set_default_timeout>`.

Some of the methods of PyOpenocdClient allow you to specify a timeout for an individual
command through the optional ``timeout`` parameter. If this parameter is set, it takes
precedence over the global timeout.

.. code-block:: python

    from py_openocd_client import PyOpenocdClient

    with PyOpenocdClient(host="localhost", port=6666) as ocd:

        # All commands from now on will have a timeout of 10 seconds:
        ocd.set_default_timeout(10.0)

        # ...

        # Override the default timeout for an individual command:
        ocd.cmd("load_image big_program.elf", timeout=30.0)

