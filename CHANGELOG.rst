
Changelog for PyOpenocdClient
=============================

Unreleased
----------

* Drop support for Python 3.9 and older (`#46`_)
* Create new exception ``OcdEmptyResponseError``. (`#49`_)
* Improve ``shutdown()`` method to better check the OpenOCD's "shutdown" command result. (`#49`_)
* Deprecate property ``OcdInvalidResponseError.out``. (`#49`_)
* Add new argument ``exit_code`` to the ``shutdown()`` method. (`#51`_)
* Add ``openocd_cmd`` command-line utility that can be used from non-Python
  programs (shell scripts or similar). (`#53`_)

.. _#46: https://github.com/HonzaMat/PyOpenocdClient/pull/46
.. _#49: https://github.com/HonzaMat/PyOpenocdClient/pull/49
.. _#51: https://github.com/HonzaMat/PyOpenocdClient/pull/51
.. _#53: https://github.com/HonzaMat/PyOpenocdClient/pull/53

Release 0.1.2 (Apr 04, 2026)
----------------------------

* Fix: Proper exception if OpenOCD closes the connection (`#37`_)
* Diligent handling of socket exceptions (`#38`_)
* Workaround for excessive whitespace trimming in 'return' in older OpenOCD versions (`#42`_)

.. _#37: https://github.com/HonzaMat/PyOpenocdClient/pull/37
.. _#38: https://github.com/HonzaMat/PyOpenocdClient/pull/38
.. _#42: https://github.com/HonzaMat/PyOpenocdClient/pull/42

Release 0.1.1 (Oct 06, 2025)
----------------------------

* Fix PyOpenocdClient.shutdown() call (`#32`_)
* Fix integration tests related to whitespace (`#33`_)

.. _#32: https://github.com/HonzaMat/PyOpenocdClient/pull/32
.. _#33: https://github.com/HonzaMat/PyOpenocdClient/pull/33

Release 0.1.0 (Sep 06, 2024)
----------------------------

* Initial release.
