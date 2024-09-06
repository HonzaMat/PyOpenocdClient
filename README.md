# PyOpenocdClient

**PyOpenocdClient** is a Python library for controlling [OpenOCD](https://openocd.org)
software tool.

It allows to send any TCL commands from Python programs to OpenOCD and receive results of these commands (for instance commands like halt execution of the program, view data in memory, place breakpoints, single-step, ...).

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


