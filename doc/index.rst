
PyOpenocdClient documentation
=============================

**PyOpenocdClient** is a Python library for controlling `OpenOCD`_ software tool.

This library allows Python programs to send commands to OpenOCD through its
Tcl-RPC interface.

The PyOpenocdClient package also provides a command-line utility that can be used
to send commands to OpenOCD from non-Python programs, such as from shell scripts.

Using Tcl commands, you can perform various actions with OpenOCD, such as halting
the execution of the debugged target, reading data from memory,
reading processor register values, and more. A complete list of Tcl commands
supported by OpenOCD can be found in the `OpenOCD documentation`_.

.. _OpenOCD: https://openocd.org
.. _OpenOCD documentation: https://openocd.org/pages/documentation.html

🏠 Homepage of PyOpenocdClient: https://github.com/HonzaMat/PyOpenocdClient


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installing
   quickstart
   apidocs
   console_utility
   Changelog<changelog>
