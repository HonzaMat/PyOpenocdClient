# PyOpenocdClient

[![Build documentation](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/build_doc.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/build_doc.yml)
[![Code quality checks](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/code_quality.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/code_quality.yml)
[![Unit tests](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/unit_tests.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/unit_tests.yml)
[![Integration tests](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/integration_tests.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/integration_tests.yml)

**PyOpenocdClient** is a Python library for controlling [OpenOCD](https://openocd.org)
software tool.

It allows to send TCL commands from Python programs to OpenOCD &mdash; for instance commands like halt execution of the program, view data in memory, place breakpoints, single-step, ...

Main features of PyOpenocdClient:

* allow to send any TCL command to OpenOCD and obtain its result;

* shorcuts for quick use of most common OpenOCD commands are provided;

* command failures are detected (and reported as Python exceptions by default);

* the code is fully covered via unit tests;

* automatic integration testing against multiple versions of OpenOCD;

* the code is multiplatform and portable &mdash; it does not have any dependencies except for the Python's standard library;

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


