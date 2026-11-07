<!--
SPDX-FileCopyrightText: 2026 Jan Matyas <info@janmatyas.net>
SPDX-License-Identifier: MIT
-->

# PyOpenocdClient

[![Build documentation](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/build_doc.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/build_doc.yml)
[![Code quality checks](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/code_quality.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/code_quality.yml)
[![Unit tests](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/unit_tests.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/unit_tests.yml)
[![Integration tests](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/integration_tests.yml/badge.svg?event=schedule)](https://github.com/HonzaMat/PyOpenocdClient/actions/workflows/integration_tests.yml)
[![Python 3.10 and newer](https://img.shields.io/badge/Python-3.10_and_newer-blue?logo=python&logoColor=yellow)](https://pypi.org/project/PyOpenocdClient/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/HonzaMat/PyOpenocdClient/blob/main/LICENSE)

**PyOpenocdClient** is a Python library for controlling the [OpenOCD](https://openocd.org)
software tool.

It allows you to send Tcl commands from Python programs to OpenOCD &mdash; for instance commands like halt execution of the program, view data in memory, set breakpoints, perform single-stepping, and others.

Main features of PyOpenocdClient:

* You can send any Tcl command to OpenOCD and obtain its result.

* Shortcuts for quick use of the most common OpenOCD commands are provided.

* Command failures are detected (and reported as Python exceptions by default).

* The code of the library is fully covered by unit tests.

* Integration tests are regularly run against multiple versions of OpenOCD.

* The code is multiplatform and portable &mdash; it does not have any dependencies except for the Python's standard library.

* The library is fully open-source under a permissive license (MIT license).

In addition to the main Python library, a command-line utility is included, which allows users
to send Tcl commands to OpenOCD from non-Python software, such as shell scripts.

## Quick instructions

Install PyOpenocdClient package using Pip:

```bash
$ python3 -m pip install PyOpenocdClient
```

Basic usage from Python:

```python
from py_openocd_client import PyOpenocdClient

with PyOpenocdClient(host="localhost", port=6666) as ocd:

    ocd.reset_halt()
    ocd.cmd("load_image path/to/program.elf")
    ocd.resume()
    # ...
```

Basic usage from a command-line or shell scripts:

```bash

$ openocd_cmd --host 127.0.0.1 --port 6666 version
Open On-Chip Debugger 0.12.0+dev-02634-g390b9d731 (2026-08-29-14:15)

$ openocd_cmd --host 127.0.0.1 --port 6666 "reset halt ; reg pc"
pc (/32): 0x08001234

```

## Documentation

For full documentation, please visit: https://pyopenocdclient.readthedocs.io/en/latest/

&nbsp;


