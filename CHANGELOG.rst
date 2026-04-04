
Changelog for PyOpenocdClient
=============================

Unreleased
----------

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