# PyOpenocdClient

**PyOpenocdClient** is a Python library for controlling [OpenOCD](https://openocd.org)
software tool.

It allows to send any TCL commands from Python programs to OpenOCD and receive results of these commands (for instance commands like halt execution of the program, view data in memory, place breakpoints, single-step, ...).

Main features:

* send any TCL command to OpenOCD and obtain its result;

* shorcuts for frequently used commands;

* command failures are detected (and are reported as Python exceptions by default);

* the code is fully covered via unit tests;

* automatic integration testing against multiple version of OpenOCD;

* the code is multiplatform and portable -- no dependencies except for the Python standard library;

* fully open-source under a permissive license (MIT license).



## Quick instructions

Install PyOpenocdClient package using Pip:

```bash
$ python3 -m pip install PyOpenocdClient
```

Basic usage:

```python
from py_openocd_client import PyOpenocdClient

with PyOpenocdClient(host="localhost", port=6666) as ocd:

    ocd.reset_halt()
    ocd.cmd("load_image path/to/program.elf")
    ocd.resume()
    # ...
```

## Documentation

For full documentation, please visit: https://pyopenocdclient.readthedocs.io/en/latest/

&nbsp;


